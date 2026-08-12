"""Stable FastAPI composition root for CourtSniper."""

import os
from typing import Dict

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

try:
    from .scheduler_models import BookingTargetTime, ScheduleConfig
    from .setup_session_process import (
        SetupSessionLaunchError,
        SetupSessionProcessManager,
        SetupSessionScriptNotFoundError,
    )
    from .sniper_process import (
        SniperAlreadyRunningError,
        SniperLaunchError,
        SniperNotRunningError,
        SniperProcessManager,
        SniperScriptNotFoundError,
        SniperStopError,
    )
    from .web import config_routes, scheduler_routes, session_routes, sniper_routes
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
    from setup_session_process import (
        SetupSessionLaunchError,
        SetupSessionProcessManager,
        SetupSessionScriptNotFoundError,
    )
    from sniper_process import (
        SniperAlreadyRunningError,
        SniperLaunchError,
        SniperNotRunningError,
        SniperProcessManager,
        SniperScriptNotFoundError,
        SniperStopError,
    )
    from web import config_routes, scheduler_routes, session_routes, sniper_routes
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
setup_session_process_manager = SetupSessionProcessManager()
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
    return config_routes.read_config_values(ENV_FILE_PATH, allowed_keys)


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


get_status, get_config, update_config = config_routes.register_config_routes(
    app,
    get_configured_status=lambda: _get_configured_status(),
    read_public_config=lambda: _read_config_values(PUBLIC_CONFIG_KEYS),
    update_configuration=lambda updates: config_routes.update_config_file(
        updates,
        env_file_path=ENV_FILE_PATH,
        editable_keys=EDITABLE_CONFIG_KEYS,
    ),
)

trigger_setup = session_routes.register_session_routes(
    app,
    get_process_manager=lambda: setup_session_process_manager,
    launch_errors=(SetupSessionScriptNotFoundError, SetupSessionLaunchError),
)

(
    trigger_sniper,
    get_sniper_run_status,
    stop_sniper,
) = sniper_routes.register_sniper_routes(
    app,
    get_configured_status=lambda: _get_configured_status(),
    get_process_manager=lambda: sniper_process_manager,
    already_running_error=SniperAlreadyRunningError,
    launch_errors=(SniperScriptNotFoundError, SniperLaunchError),
    not_running_error=SniperNotRunningError,
    stop_error=SniperStopError,
)

(
    get_scheduler_status,
    configure_scheduler,
    enable_scheduler,
    disable_scheduler,
) = scheduler_routes.register_scheduler_routes(
    app,
    schedule_config_type=ScheduleConfig,
    get_scheduler_adapter=lambda: scheduler_adapter,
    get_booking_target_time=lambda: _get_booking_target_time(),
    scheduler_payload=lambda snapshot: _scheduler_payload(snapshot),
    scheduler_http_exception=lambda error: _scheduler_http_exception(error),
    scheduler_error=WindowsSchedulerError,
    booking_target_error=BookingTargetConfigurationError,
    not_configured_error=SchedulerTaskNotConfiguredError,
)
