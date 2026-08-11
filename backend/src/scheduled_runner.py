"""Fixed scheduled entry point that safely invokes the CourtSniper API."""

from __future__ import annotations

from collections.abc import Callable
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_BASE_URL = "http://127.0.0.1:8000/api"
API_HOST = "127.0.0.1"
API_PORT = "8000"
API_SERVICE_ID = "CourtSniper"

EXIT_SUCCESS = 0
EXIT_RUNNER_ERROR = 1
EXIT_RUN_REJECTED = 2
EXIT_AUTOMATION_FAILED = 3
EXIT_AUTOMATION_STOPPED = 4

ACTIVE_RUN_STATES = {"running", "stopping"}
TERMINAL_RUN_STATES = {"idle", "stopped", "succeeded", "failed"}
KNOWN_RUN_STATES = ACTIVE_RUN_STATES | TERMINAL_RUN_STATES


class ScheduledRunnerError(RuntimeError):
    """Base error for sanitized scheduled-runner failures."""


class ApiUnavailableError(ScheduledRunnerError):
    """Raised when the fixed local API cannot be reached."""


class UnexpectedApiError(ScheduledRunnerError):
    """Raised when port 8000 does not expose the expected CourtSniper API."""


class ApiHttpError(ScheduledRunnerError):
    """A sanitized non-success response from the fixed local API."""

    def __init__(self, status_code: int) -> None:
        super().__init__("The CourtSniper API rejected the scheduled request.")
        self.status_code = status_code


class ApiClient(Protocol):
    def check_health(self) -> None:
        """Confirm that the fixed local endpoint is the CourtSniper API."""

    def start_run(self) -> None:
        """Request a run through the existing guarded endpoint."""

    def get_run_state(self) -> str:
        """Return a validated process-manager state."""


class ManagedApiProcess(Protocol):
    def poll(self) -> int | None:
        """Return None while the temporary API is running."""

    def terminate(self) -> None:
        """Request graceful API termination."""

    def wait(self, timeout: float | None = None) -> int:
        """Wait for API termination."""

    def kill(self) -> None:
        """Force API termination after a graceful timeout."""


ProcessFactory = Callable[..., ManagedApiProcess]


class CourtSniperApiClient:
    """HTTP client with no configurable host, route, command, or path."""

    def __init__(
        self,
        *,
        opener: Callable[..., object] = urlopen,
        timeout_seconds: float = 3.0,
    ) -> None:
        self._opener = opener
        self._timeout_seconds = timeout_seconds

    def check_health(self) -> None:
        payload = self._request("GET", "/status")
        if (
            payload.get("service") != API_SERVICE_ID
            or payload.get("status") != "online"
            or not isinstance(payload.get("armed"), bool)
            or not isinstance(payload.get("execution_status"), str)
        ):
            raise UnexpectedApiError("The expected CourtSniper API is unavailable.")

    def start_run(self) -> None:
        payload = self._request("POST", "/run-sniper")
        run = payload.get("run")
        if not isinstance(run, dict) or run.get("state") != "running":
            raise UnexpectedApiError("The CourtSniper API returned an invalid response.")

    def get_run_state(self) -> str:
        payload = self._request("GET", "/run-sniper/status")
        run = payload.get("run")
        state = run.get("state") if isinstance(run, dict) else None
        if not isinstance(state, str) or state not in KNOWN_RUN_STATES:
            raise UnexpectedApiError("The CourtSniper API returned an invalid response.")
        return state

    def _request(self, method: str, path: str) -> dict[str, object]:
        request = Request(
            f"{API_BASE_URL}{path}",
            data=b"" if method == "POST" else None,
            method=method,
            headers={"Accept": "application/json"},
        )
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                raw_payload = response.read(65_536)
        except HTTPError as error:
            raise ApiHttpError(error.code) from None
        except (URLError, TimeoutError, OSError):
            raise ApiUnavailableError("The CourtSniper API is unavailable.") from None

        try:
            payload = json.loads(raw_payload)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
            raise UnexpectedApiError(
                "The CourtSniper API returned an invalid response."
            ) from None
        if not isinstance(payload, dict):
            raise UnexpectedApiError("The CourtSniper API returned an invalid response.")
        return payload


def _api_launch_options() -> dict[str, int | bool]:
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


class ScheduledRunner:
    """Start/reuse the local API, invoke one run, and monitor it safely."""

    def __init__(
        self,
        *,
        api_client: ApiClient | None = None,
        process_factory: ProcessFactory = subprocess.Popen,
        python_executable: str = sys.executable,
        backend_dir: Path | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        startup_timeout_seconds: float = 30.0,
        run_timeout_seconds: float = 7_200.0,
        poll_interval_seconds: float = 0.5,
        shutdown_timeout_seconds: float = 5.0,
    ) -> None:
        self._api = api_client or CourtSniperApiClient()
        self._process_factory = process_factory
        self._python_executable = python_executable
        self._backend_dir = (
            backend_dir or Path(__file__).resolve().parent.parent
        ).resolve()
        self._monotonic = monotonic
        self._sleep = sleep
        self._startup_timeout_seconds = startup_timeout_seconds
        self._run_timeout_seconds = run_timeout_seconds
        self._poll_interval_seconds = poll_interval_seconds
        self._shutdown_timeout_seconds = shutdown_timeout_seconds

    def run(self) -> int:
        owned_api: ManagedApiProcess | None = None
        run_may_be_active = False

        try:
            try:
                self._api.check_health()
            except ApiUnavailableError:
                owned_api = self._start_api()
                self._wait_for_api(owned_api)

            try:
                self._api.start_run()
                run_may_be_active = True
            except ApiHttpError as error:
                if error.status_code != 409:
                    raise
                if owned_api is not None:
                    # A 409 can mean another run won a race. Until status proves
                    # otherwise, preserve the API that may be controlling it.
                    run_may_be_active = True
                    state = self._api.get_run_state()
                    run_may_be_active = state in ACTIVE_RUN_STATES
                    if run_may_be_active:
                        self._wait_for_terminal_run()
                        run_may_be_active = False
                    self._stop_owned_api(owned_api)
                return EXIT_RUN_REJECTED

            final_state = self._wait_for_terminal_run()
            run_may_be_active = False
            if owned_api is not None:
                self._stop_owned_api(owned_api)

            if final_state in {"idle", "succeeded"}:
                return EXIT_SUCCESS
            if final_state == "stopped":
                return EXIT_AUTOMATION_STOPPED
            return EXIT_AUTOMATION_FAILED
        except Exception:
            if owned_api is not None and not run_may_be_active:
                self._stop_owned_api(owned_api)
            return EXIT_RUNNER_ERROR

    def _start_api(self) -> ManagedApiProcess:
        command = [
            self._python_executable,
            "-m",
            "uvicorn",
            "src.api:app",
            "--host",
            API_HOST,
            "--port",
            API_PORT,
        ]
        try:
            return self._process_factory(
                command,
                cwd=str(self._backend_dir),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                **_api_launch_options(),
            )
        except OSError:
            raise ScheduledRunnerError("The temporary CourtSniper API could not start.") from None

    def _wait_for_api(self, process: ManagedApiProcess) -> None:
        deadline = self._monotonic() + self._startup_timeout_seconds
        while self._monotonic() < deadline:
            if process.poll() is not None:
                raise ScheduledRunnerError("The temporary CourtSniper API stopped early.")
            try:
                self._api.check_health()
                return
            except ApiUnavailableError:
                self._sleep(self._poll_interval_seconds)
        raise ScheduledRunnerError("The temporary CourtSniper API did not become ready.")

    def _wait_for_terminal_run(self) -> str:
        deadline = self._monotonic() + self._run_timeout_seconds
        while self._monotonic() < deadline:
            state = self._api.get_run_state()
            if state in TERMINAL_RUN_STATES:
                return state
            self._sleep(self._poll_interval_seconds)
        raise ScheduledRunnerError("The scheduled CourtSniper run timed out.")

    def _stop_owned_api(self, process: ManagedApiProcess) -> None:
        if process.poll() is not None:
            return
        try:
            process.terminate()
            process.wait(timeout=self._shutdown_timeout_seconds)
        except (OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
                process.wait(timeout=self._shutdown_timeout_seconds)
            except (OSError, subprocess.TimeoutExpired):
                return


def main() -> int:
    """Run the fixed scheduled workflow and return a Windows task result code."""
    return ScheduledRunner().run()


if __name__ == "__main__":
    raise SystemExit(main())
