from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import os
import subprocess
import sys

from pydantic import ValidationError

try:
    from .sniper_process import (
        SniperAlreadyRunningError,
        SniperLaunchError,
        SniperNotRunningError,
        SniperProcessManager,
        SniperScriptNotFoundError,
        SniperStopError,
    )
except ImportError:
    from sniper_process import (
        SniperAlreadyRunningError,
        SniperLaunchError,
        SniperNotRunningError,
        SniperProcessManager,
        SniperScriptNotFoundError,
        SniperStopError,
    )

try:
    from .scheduler_models import BookingTargetTime, ScheduleConfig
    from .windows_scheduler import (
        SchedulerTaskNotConfiguredError,
        SchedulerTaskNotInstalledError,
        SchedulerTaskOwnershipError,
        WindowsSchedulerError,
        WindowsSchedulerOperationError,
        WindowsSchedulerPermissionError,
        WindowsSchedulerStatus,
        WindowsSchedulerTimeoutError,
        WindowsSchedulerUnavailableError,
        WindowsSchedulerUnsupportedError,
        WindowsTaskSchedulerAdapter,
    )
except ImportError:
    from scheduler_models import BookingTargetTime, ScheduleConfig
    from windows_scheduler import (
        SchedulerTaskNotConfiguredError,
        SchedulerTaskNotInstalledError,
        SchedulerTaskOwnershipError,
        WindowsSchedulerError,
        WindowsSchedulerOperationError,
        WindowsSchedulerPermissionError,
        WindowsSchedulerStatus,
        WindowsSchedulerTimeoutError,
        WindowsSchedulerUnavailableError,
        WindowsSchedulerUnsupportedError,
        WindowsTaskSchedulerAdapter,
    )

# Initialize the FastAPI application
app = FastAPI(title="CourtSniper Web UI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

ROOT_DIR = os.path.dirname(CURRENT_DIR)

ENV_FILE_PATH = os.path.join(ROOT_DIR, ".env")

sniper_process_manager = SniperProcessManager()
scheduler_adapter = WindowsTaskSchedulerAdapter()

PUBLIC_CONFIG_KEYS = {
    "TARGET_URL",
    "BOOKING_MESSAGE",
    "TARGET_HOUR",
    "TARGET_MINUTE",
    "TARGET_SECOND",
    "STATUS",
}
EDITABLE_CONFIG_KEYS = PUBLIC_CONFIG_KEYS
TARGET_TIME_KEYS = {"TARGET_HOUR", "TARGET_MINUTE", "TARGET_SECOND"}


class BookingTargetConfigurationError(ValueError):
    """Raised when the scheduler cannot use the existing booking target time."""


def _read_config_values(allowed_keys: set[str]) -> dict[str, str]:
    values = {}
    if not os.path.exists(ENV_FILE_PATH):
        return values

    with open(ENV_FILE_PATH, "r", encoding="utf-8") as file:
        for line in file:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith("#") or "=" not in stripped_line:
                continue

            key, value = stripped_line.split("=", 1)
            key = key.strip()
            if key in allowed_keys:
                values[key] = value.strip().strip("\"'")
    return values


def _get_configured_status():
    """Read only the kill-switch value required to authorize a run."""
    status_value = _read_config_values({"STATUS"}).get("STATUS")
    return status_value.upper() if status_value else None


def _get_booking_target_time() -> BookingTargetTime:
    """Read and validate only the existing target-time fields."""
    values = _read_config_values(TARGET_TIME_KEYS)
    if any(key not in values for key in TARGET_TIME_KEYS):
        raise BookingTargetConfigurationError(
            "Configure a valid booking target time before scheduling CourtSniper."
        )

    try:
        return BookingTargetTime(
            hour=int(values["TARGET_HOUR"]),
            minute=int(values["TARGET_MINUTE"]),
            second=int(values["TARGET_SECOND"]),
        )
    except (ValueError, ValidationError) as error:
        raise BookingTargetConfigurationError(
            "Configure a valid booking target time before scheduling CourtSniper."
        ) from error


def _try_get_booking_target_time() -> BookingTargetTime | None:
    try:
        return _get_booking_target_time()
    except BookingTargetConfigurationError:
        return None


def _scheduler_payload(snapshot: WindowsSchedulerStatus) -> dict[str, object]:
    payload = snapshot.model_dump(mode="json")
    configuration = snapshot.configuration
    payload["configured"] = configuration is not None

    if configuration is None:
        payload["configuration_in_sync"] = None
    else:
        target = _try_get_booking_target_time()
        payload["configuration_in_sync"] = (
            target is not None and configuration.target_time == target.as_time()
        )
    return payload


def _scheduler_http_exception(error: Exception) -> HTTPException:
    if isinstance(error, WindowsSchedulerPermissionError):
        return HTTPException(status_code=403, detail=str(error))
    if isinstance(error, WindowsSchedulerTimeoutError):
        return HTTPException(status_code=504, detail=str(error))
    if isinstance(
        error,
        (WindowsSchedulerUnsupportedError, WindowsSchedulerUnavailableError),
    ):
        return HTTPException(status_code=503, detail=str(error))
    if isinstance(
        error,
        (
            SchedulerTaskOwnershipError,
            SchedulerTaskNotInstalledError,
            SchedulerTaskNotConfiguredError,
            BookingTargetConfigurationError,
        ),
    ):
        return HTTPException(status_code=409, detail=str(error))
    if isinstance(error, (WindowsSchedulerOperationError, WindowsSchedulerError)):
        return HTTPException(
            status_code=500,
            detail="Windows Task Scheduler operation failed.",
        )
    return HTTPException(
        status_code=500,
        detail="Windows Task Scheduler operation failed.",
    )

@app.get("/api/status")
def get_status():
    execution_status = _get_configured_status() or "UNKNOWN"
    return {
        "status": "online",
        "execution_status": execution_status,
        "armed": execution_status == "ARMED",
    }

@app.get("/api/config")
def get_config():
    """Return only the configuration fields required by the dashboard."""
    return _read_config_values(PUBLIC_CONFIG_KEYS)

@app.post("/api/config")
def update_config(updates: Dict[str, str]):
    """Receives JSON from the frontend and overwrites the .env file."""
    if any(key not in EDITABLE_CONFIG_KEYS for key in updates):
        raise HTTPException(
            status_code=422,
            detail="The request contains an unsupported configuration field.",
        )

    if not os.path.exists(ENV_FILE_PATH):
        return {"error": ".env file missing!"}

    # Read the current file line by line
    with open(ENV_FILE_PATH, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # Rewrite the file, swapping out updated values
    with open(ENV_FILE_PATH, "w", encoding="utf-8") as file:
        for line in lines:
            written = False
            for key, new_value in updates.items():
                if line.startswith(f"{key}="):
                    # Write the new value, wrapped safely in quotes
                    file.write(f'{key}="{new_value}"\n')
                    written = True
                    break
            # If the line wasn't updated, keep it exactly as it was
            if not written:
                file.write(line)

    return {"message": "Configuration successfully updated on the server!"}


@app.post("/api/run-setup")
def trigger_setup():
    """Triggers the manual Facebook login script in the background."""

    # 1. Build the absolute path to setup_session.py (it lives in the same folder as this api.py)
    setup_script_path = os.path.join(CURRENT_DIR, "setup_session.py")

    if not os.path.exists(setup_script_path):
        return {"error": "Could not find setup_session.py!"}

    try:
        # 2. Launch the script as a separate background process.
        subprocess.Popen([sys.executable, setup_script_path], cwd=ROOT_DIR)

        return {"message": "Setup session launched! Check your laptop screen."}

    except Exception as e:
        return {"error": f"Failed to launch script: {str(e)}"}


@app.post("/api/run-sniper", status_code=status.HTTP_202_ACCEPTED)
def trigger_sniper():
    """Start the predefined sniper automation when the kill switch is armed."""
    if _get_configured_status() != "ARMED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CourtSniper must be armed before starting a run.",
        )

    try:
        run_status = sniper_process_manager.start()
    except SniperAlreadyRunningError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except (SniperScriptNotFoundError, SniperLaunchError) as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    return {
        "message": "CourtSniper run started.",
        "run": run_status.to_dict(),
    }


@app.get("/api/run-sniper/status", status_code=200)
def get_sniper_run_status():
    """Return the current non-sensitive sniper process state."""
    return {"run": sniper_process_manager.get_status().to_dict()}


@app.post("/api/run-sniper/stop", status_code=200)
def stop_sniper():
    """Stop the currently tracked sniper process group."""
    try:
        run_status = sniper_process_manager.stop()
    except SniperNotRunningError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except SniperStopError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    return {
        "message": "CourtSniper run stopped.",
        "run": run_status.to_dict(),
    }


@app.get("/api/scheduler", status_code=200)
def get_scheduler_status():
    """Return a sanitized snapshot of the fixed Windows scheduled task."""
    try:
        snapshot = scheduler_adapter.get_status()
    except WindowsSchedulerError as error:
        raise _scheduler_http_exception(error) from error
    return _scheduler_payload(snapshot)


@app.post("/api/scheduler/config", status_code=200)
def configure_scheduler(config: ScheduleConfig):
    """Install or update the fixed task using the existing booking target."""
    try:
        target = _get_booking_target_time()
        snapshot = scheduler_adapter.configure(config, target)
    except (WindowsSchedulerError, BookingTargetConfigurationError) as error:
        raise _scheduler_http_exception(error) from error
    return {
        "message": "CourtSniper schedule configured.",
        "scheduler": _scheduler_payload(snapshot),
    }


@app.post("/api/scheduler/enable", status_code=200)
def enable_scheduler():
    """Enable future runs after confirming the target time is current."""
    try:
        current = scheduler_adapter.get_status()
        if current.configuration is not None:
            target = _get_booking_target_time()
            if current.configuration.target_time != target.as_time():
                raise SchedulerTaskNotConfiguredError(
                    "Save the scheduler configuration for the current booking target before enabling it."
                )
        snapshot = scheduler_adapter.enable()
    except (WindowsSchedulerError, BookingTargetConfigurationError) as error:
        raise _scheduler_http_exception(error) from error
    return {
        "message": "CourtSniper schedule enabled.",
        "scheduler": _scheduler_payload(snapshot),
    }


@app.post("/api/scheduler/disable", status_code=200)
def disable_scheduler():
    """Disable future triggers without stopping an active sniper run."""
    try:
        snapshot = scheduler_adapter.disable()
    except WindowsSchedulerError as error:
        raise _scheduler_http_exception(error) from error
    return {
        "message": "CourtSniper schedule disabled.",
        "scheduler": _scheduler_payload(snapshot),
    }
