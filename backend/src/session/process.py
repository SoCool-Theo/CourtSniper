from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
import threading

from .guard import SetupSessionGuardError, create_setup_session_guard
from .setup import SETUP_ALREADY_RUNNING_EXIT_CODE


SETUP_SCRIPT_FILENAME = "setup_session.py"
STARTUP_PROBE_SECONDS = 1.0


class SetupSessionProcessError(RuntimeError):
    """Base error for safe setup-session process failures."""


class SetupSessionScriptNotFoundError(SetupSessionProcessError):
    """Raised when the fixed setup script is unavailable."""


class SetupSessionLaunchError(SetupSessionProcessError):
    """Raised when the fixed setup process cannot be started safely."""


@dataclass(frozen=True)
class SetupSessionStartResult:
    launched: bool

    @property
    def already_running(self):
        return not self.launched


class SetupSessionProcessManager:
    """Start at most one fixed login setup process across threads and servers."""

    def __init__(
        self,
        *,
        root_dir=None,
        script_path=None,
        python_executable=None,
        process_factory=None,
        guard_factory=None,
        startup_probe_seconds=STARTUP_PROBE_SECONDS,
    ):
        source_dir = Path(__file__).resolve().parent.parent
        self._root_dir = Path(root_dir) if root_dir else source_dir.parent
        self._script_path = (
            Path(script_path)
            if script_path
            else source_dir / SETUP_SCRIPT_FILENAME
        )
        self._python_executable = python_executable or sys.executable
        self._process_factory = process_factory or subprocess.Popen
        self._guard_factory = guard_factory or create_setup_session_guard
        self._startup_probe_seconds = startup_probe_seconds
        self._lock = threading.Lock()
        self._process = None

    def _tracked_process_is_running(self):
        if self._process is None:
            return False
        try:
            exit_code = self._process.poll()
        except Exception as error:
            self._process = None
            raise SetupSessionLaunchError(
                "Unable to check the login setup process."
            ) from error
        if exit_code is None:
            return True
        self._process = None
        return False

    def _cross_process_guard_is_active(self):
        guard = self._guard_factory(str(self._root_dir))
        acquired = False
        try:
            acquired = guard.acquire()
            return not acquired
        except SetupSessionGuardError as error:
            raise SetupSessionLaunchError(
                "Unable to check the login setup state."
            ) from error
        finally:
            if acquired:
                try:
                    guard.release()
                except SetupSessionGuardError as error:
                    raise SetupSessionLaunchError(
                        "Unable to check the login setup state."
                    ) from error

    def _probe_started_process(self, process):
        try:
            exit_code = process.wait(timeout=self._startup_probe_seconds)
        except subprocess.TimeoutExpired:
            return SetupSessionStartResult(launched=True)
        except Exception as error:
            self._process = None
            raise SetupSessionLaunchError(
                "Unable to check the login setup process."
            ) from error

        self._process = None
        if exit_code == SETUP_ALREADY_RUNNING_EXIT_CODE:
            return SetupSessionStartResult(launched=False)
        if exit_code != 0:
            raise SetupSessionLaunchError(
                "The login setup process could not be started."
            )
        return SetupSessionStartResult(launched=True)

    def start(self):
        """Start the fixed setup script or reuse the active login window."""
        with self._lock:
            if self._tracked_process_is_running():
                return SetupSessionStartResult(launched=False)

            if self._cross_process_guard_is_active():
                return SetupSessionStartResult(launched=False)

            if not self._script_path.is_file():
                raise SetupSessionScriptNotFoundError(
                    "The login setup entry point is unavailable."
                )

            command = [self._python_executable, str(self._script_path)]
            try:
                process = self._process_factory(
                    command,
                    cwd=str(self._root_dir),
                )
            except Exception as error:
                raise SetupSessionLaunchError(
                    "The login setup process could not be started."
                ) from error

            self._process = process
            return self._probe_started_process(process)
