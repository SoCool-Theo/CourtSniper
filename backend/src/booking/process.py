"""Safe lifecycle management for the CourtSniper automation process."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import signal
import subprocess
import sys
from threading import Lock
from typing import Callable, Protocol


class ManagedProcess(Protocol):
    """The subprocess operations needed by ``SniperProcessManager``."""

    pid: int

    def poll(self) -> int | None:
        """Return ``None`` while running, otherwise the process exit code."""

    def send_signal(self, signal_number: int) -> None:
        """Send a graceful stop signal to the managed process."""

    def wait(self, timeout: float | None = None) -> int:
        """Wait for the managed process and return its exit code."""


ProcessFactory = Callable[..., ManagedProcess]
StopAction = Callable[[ManagedProcess], None]


def _process_group_launch_options() -> dict[str, int | bool]:
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def _request_process_group_stop(process: ManagedProcess) -> None:
    if os.name == "nt":
        process.send_signal(signal.CTRL_BREAK_EVENT)
        return
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)


def _force_stop_process_group(process: ManagedProcess) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return
    os.killpg(os.getpgid(process.pid), signal.SIGKILL)


class SniperProcessError(RuntimeError):
    """Base error for controlled sniper process failures."""


class SniperAlreadyRunningError(SniperProcessError):
    """Raised when a second sniper run is requested."""


class SniperScriptNotFoundError(SniperProcessError):
    """Raised when the fixed sniper entry point is unavailable."""


class SniperLaunchError(SniperProcessError):
    """Raised when the operating system cannot launch the sniper process."""


class SniperNotRunningError(SniperProcessError):
    """Raised when cancellation is requested without an active run."""


class SniperStopError(SniperProcessError):
    """Raised when the active sniper process cannot be stopped."""


@dataclass(frozen=True)
class SniperRunStatus:
    """Public, non-sensitive snapshot of the current run."""

    state: str = "idle"
    pid: int | None = None
    started_at: str | None = None
    finished_at: str | None = None
    exit_code: int | None = None

    def to_dict(self) -> dict[str, str | int | None]:
        return asdict(self)


class SniperProcessManager:
    """Launch and monitor the single allowed ``sniper.py`` process."""

    def __init__(
        self,
        script_path: Path | None = None,
        process_factory: ProcessFactory = subprocess.Popen,
        python_executable: str = sys.executable,
        graceful_stop: StopAction = _request_process_group_stop,
        force_stop: StopAction = _force_stop_process_group,
        stop_timeout: float = 5.0,
    ) -> None:
        source_dir = Path(__file__).resolve().parent.parent
        self._script_path = (script_path or source_dir / "sniper.py").resolve()
        self._backend_dir = self._script_path.parent.parent
        self._process_factory = process_factory
        self._python_executable = python_executable
        self._graceful_stop = graceful_stop
        self._force_stop = force_stop
        self._stop_timeout = stop_timeout
        self._process: ManagedProcess | None = None
        self._status = SniperRunStatus()
        self._lock = Lock()

    def start(self) -> SniperRunStatus:
        """Start the fixed sniper script, rejecting concurrent execution."""
        with self._lock:
            self._refresh_locked()

            if self._status.state == "running":
                raise SniperAlreadyRunningError("A sniper run is already active.")

            if not self._script_path.is_file():
                raise SniperScriptNotFoundError("The sniper entry point is unavailable.")

            try:
                process = self._process_factory(
                    [self._python_executable, str(self._script_path)],
                    cwd=str(self._backend_dir),
                    **_process_group_launch_options(),
                )
            except OSError as error:
                raise SniperLaunchError("The sniper process could not be started.") from error
            self._process = process
            self._status = SniperRunStatus(
                state="running",
                pid=process.pid,
                started_at=self._timestamp(),
            )
            return self._status

    def stop(self) -> SniperRunStatus:
        """Stop the active sniper process group and record a stopped state."""
        with self._lock:
            self._refresh_locked()

            if self._process is None or self._status.state != "running":
                raise SniperNotRunningError("No sniper run is currently active.")

            process = self._process
            running_status = self._status
            self._status = SniperRunStatus(
                state="stopping",
                pid=running_status.pid,
                started_at=running_status.started_at,
            )

            try:
                try:
                    self._graceful_stop(process)
                    exit_code = process.wait(timeout=self._stop_timeout)
                except (OSError, subprocess.TimeoutExpired):
                    self._force_stop(process)
                    exit_code = process.wait(timeout=self._stop_timeout)
            except (OSError, subprocess.TimeoutExpired) as error:
                if process.poll() is None:
                    self._status = running_status
                else:
                    self._complete_stop_locked(process.poll())
                raise SniperStopError("The sniper process could not be stopped.") from error

            self._complete_stop_locked(exit_code)
            return self._status

    def get_status(self) -> SniperRunStatus:
        """Return the latest process state without exposing process output."""
        with self._lock:
            self._refresh_locked()
            return self._status

    def _refresh_locked(self) -> None:
        if self._process is None or self._status.state != "running":
            return

        exit_code = self._process.poll()
        if exit_code is None:
            return

        self._status = SniperRunStatus(
            state="succeeded" if exit_code == 0 else "failed",
            pid=self._status.pid,
            started_at=self._status.started_at,
            finished_at=self._timestamp(),
            exit_code=exit_code,
        )
        self._process = None

    def _complete_stop_locked(self, exit_code: int | None) -> None:
        self._status = SniperRunStatus(
            state="stopped",
            pid=self._status.pid,
            started_at=self._status.started_at,
            finished_at=self._timestamp(),
            exit_code=exit_code,
        )
        self._process = None

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
