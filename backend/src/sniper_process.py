"""Safe lifecycle management for the CourtSniper automation process."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
from threading import Lock
from typing import Callable, Protocol


class ManagedProcess(Protocol):
    """The subprocess operations needed by ``SniperProcessManager``."""

    pid: int

    def poll(self) -> int | None:
        """Return ``None`` while running, otherwise the process exit code."""


ProcessFactory = Callable[..., ManagedProcess]


class SniperProcessError(RuntimeError):
    """Base error for controlled sniper process failures."""


class SniperAlreadyRunningError(SniperProcessError):
    """Raised when a second sniper run is requested."""


class SniperScriptNotFoundError(SniperProcessError):
    """Raised when the fixed sniper entry point is unavailable."""


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
    ) -> None:
        source_dir = Path(__file__).resolve().parent
        self._script_path = (script_path or source_dir / "sniper.py").resolve()
        self._backend_dir = self._script_path.parent.parent
        self._process_factory = process_factory
        self._python_executable = python_executable
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

            process = self._process_factory(
                [self._python_executable, str(self._script_path)],
                cwd=str(self._backend_dir),
            )
            self._process = process
            self._status = SniperRunStatus(
                state="running",
                pid=process.pid,
                started_at=self._timestamp(),
            )
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

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
