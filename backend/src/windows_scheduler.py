"""Safe adapter for the single CourtSniper Windows scheduled task."""

from __future__ import annotations

import base64
from collections.abc import Callable
from datetime import datetime, time, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

try:
    from .scheduler_models import (
        BookingTargetTime,
        ScheduleConfig,
        SchedulePlan,
        Weekday,
        calculate_schedule,
    )
except ImportError:
    from scheduler_models import (
        BookingTargetTime,
        ScheduleConfig,
        SchedulePlan,
        Weekday,
        calculate_schedule,
    )


TASK_NAME = "CourtSniper"
TASK_PATH = "\\"
TASK_DESCRIPTION_PREFIX = "CourtSniper Scheduler v1:"
POWERSHELL_EXECUTABLE = "powershell.exe"
_POWERSHELL_PREFIX = [
    POWERSHELL_EXECUTABLE,
    "-NoLogo",
    "-NoProfile",
    "-NonInteractive",
    "-Command",
]
_WINDOWS_WEEKDAYS = {
    Weekday.MONDAY: "Monday",
    Weekday.TUESDAY: "Tuesday",
    Weekday.WEDNESDAY: "Wednesday",
    Weekday.THURSDAY: "Thursday",
    Weekday.FRIDAY: "Friday",
    Weekday.SATURDAY: "Saturday",
    Weekday.SUNDAY: "Sunday",
}
_KNOWN_STATES = {"disabled", "queued", "ready", "running"}


class WindowsSchedulerError(RuntimeError):
    """Base error for safe Windows Task Scheduler failures."""


class WindowsSchedulerUnsupportedError(WindowsSchedulerError):
    """Raised when the adapter is used outside Windows."""


class WindowsSchedulerUnavailableError(WindowsSchedulerError):
    """Raised when PowerShell or the ScheduledTasks module is unavailable."""


class WindowsSchedulerPermissionError(WindowsSchedulerError):
    """Raised when Windows denies a scheduler operation."""


class WindowsSchedulerTimeoutError(WindowsSchedulerError):
    """Raised when a scheduler command exceeds its fixed timeout."""


class WindowsSchedulerOperationError(WindowsSchedulerError):
    """Raised when Windows returns an invalid or unsuccessful result."""


class SchedulerTaskOwnershipError(WindowsSchedulerError):
    """Raised when the fixed name belongs to an unrecognized task."""


class SchedulerTaskNotInstalledError(WindowsSchedulerError):
    """Raised when enable or disable is requested before installation."""


class SchedulerTaskNotConfiguredError(WindowsSchedulerError):
    """Raised when an owned task has invalid scheduler metadata."""


class SchedulerTaskConfiguration(BaseModel):
    """Non-sensitive configuration recovered from an owned task."""

    model_config = ConfigDict(extra="forbid")

    weekdays: list[Weekday]
    warmup_minutes: int
    target_time: time
    trigger_weekdays: list[Weekday]
    trigger_time: time

    @classmethod
    def from_plan(cls, plan: SchedulePlan) -> "SchedulerTaskConfiguration":
        return cls(
            weekdays=plan.weekdays,
            warmup_minutes=plan.warmup_minutes,
            target_time=plan.target_time,
            trigger_weekdays=plan.trigger_weekdays,
            trigger_time=plan.trigger_time,
        )


class WindowsSchedulerStatus(BaseModel):
    """Public scheduler snapshot without commands, users, or local paths."""

    model_config = ConfigDict(extra="forbid")

    task_name: Literal["CourtSniper"] = TASK_NAME
    installed: bool
    managed: bool
    enabled: bool | None = None
    state: str | None = None
    next_run_time: datetime | None = None
    last_run_time: datetime | None = None
    last_run_result: int | None = None
    configuration: SchedulerTaskConfiguration | None = None


class _TaskMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    weekdays: list[Weekday]
    warmup_minutes: int = Field(ge=0, le=1440, strict=True)
    target_time: time


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


class WindowsTaskSchedulerAdapter:
    """Manage only the fixed, adapter-owned ``CourtSniper`` task."""

    def __init__(
        self,
        *,
        runner: CommandRunner = subprocess.run,
        platform_name: str = os.name,
        timeout_seconds: float = 10.0,
        python_executable: str = sys.executable,
        scheduled_runner_path: Path | None = None,
    ) -> None:
        self._runner = runner
        self._platform_name = platform_name
        self._timeout_seconds = timeout_seconds
        self._python_executable = str(Path(python_executable).resolve())
        self._scheduled_runner_path = (
            scheduled_runner_path
            or Path(__file__).resolve().parent / "scheduled_runner.py"
        ).resolve()
        self._backend_dir = self._scheduled_runner_path.parent.parent

    def get_status(self) -> WindowsSchedulerStatus:
        payload = self._run_json(_status_script())
        installed = payload.get("installed")
        if not isinstance(installed, bool):
            raise WindowsSchedulerOperationError(
                "Windows Task Scheduler returned an invalid response."
            )
        if not installed:
            return WindowsSchedulerStatus(installed=False, managed=False)

        description = payload.get("description")
        if not isinstance(description, str) or not description.startswith(
            TASK_DESCRIPTION_PREFIX
        ):
            return WindowsSchedulerStatus(installed=True, managed=False)

        configuration = _decode_configuration(description)
        enabled = payload.get("enabled")
        if not isinstance(enabled, bool):
            raise WindowsSchedulerOperationError(
                "Windows Task Scheduler returned an invalid response."
            )

        last_run_time = _parse_optional_datetime(payload.get("last_run_time"))
        last_run_result = payload.get("last_run_result")
        if last_run_time is None:
            last_run_result = None
        elif isinstance(last_run_result, bool) or not isinstance(last_run_result, int):
            raise WindowsSchedulerOperationError(
                "Windows Task Scheduler returned an invalid response."
            )

        raw_state = payload.get("state")
        state = raw_state.lower() if isinstance(raw_state, str) else "unknown"
        if state not in _KNOWN_STATES:
            state = "unknown"

        return WindowsSchedulerStatus(
            installed=True,
            managed=True,
            enabled=enabled,
            state=state,
            next_run_time=_parse_optional_datetime(payload.get("next_run_time")),
            last_run_time=last_run_time,
            last_run_result=last_run_result,
            configuration=configuration,
        )

    def configure(
        self,
        config: ScheduleConfig,
        target: BookingTargetTime,
    ) -> WindowsSchedulerStatus:
        current = self.get_status()
        if current.installed and not current.managed:
            raise SchedulerTaskOwnershipError(
                "A different task already uses the CourtSniper task name."
            )

        plan = calculate_schedule(config, target)
        description = _encode_configuration(plan)
        preserve_enabled = current.enabled is True
        self._run(
            _configure_script(
                plan,
                description,
                preserve_enabled,
                python_executable=self._python_executable,
                scheduled_runner_path=self._scheduled_runner_path,
                backend_dir=self._backend_dir,
            )
        )
        return self.get_status()

    def enable(self) -> WindowsSchedulerStatus:
        current = self._require_managed_task(require_configuration=True)
        if current.enabled is not True:
            self._run(_state_change_script(enable=True))
        return self.get_status()

    def disable(self) -> WindowsSchedulerStatus:
        current = self._require_managed_task(require_configuration=False)
        if current.enabled is not False:
            self._run(_state_change_script(enable=False))
        return self.get_status()

    def _require_managed_task(
        self,
        *,
        require_configuration: bool,
    ) -> WindowsSchedulerStatus:
        current = self.get_status()
        if not current.installed:
            raise SchedulerTaskNotInstalledError(
                "The CourtSniper scheduled task is not installed."
            )
        if not current.managed:
            raise SchedulerTaskOwnershipError(
                "A different task already uses the CourtSniper task name."
            )
        if require_configuration and current.configuration is None:
            raise SchedulerTaskNotConfiguredError(
                "The CourtSniper scheduled task is not configured."
            )
        return current

    def _run_json(self, script: str) -> dict[str, object]:
        result = self._run(script)
        try:
            payload = json.loads(result.stdout)
        except (json.JSONDecodeError, TypeError) as error:
            raise WindowsSchedulerOperationError(
                "Windows Task Scheduler returned an invalid response."
            ) from error
        if not isinstance(payload, dict):
            raise WindowsSchedulerOperationError(
                "Windows Task Scheduler returned an invalid response."
            )
        return payload

    def _run(self, script: str) -> subprocess.CompletedProcess[str]:
        if self._platform_name != "nt":
            raise WindowsSchedulerUnsupportedError(
                "Windows Task Scheduler is available only on Windows."
            )

        command = [*_POWERSHELL_PREFIX, script]
        try:
            result = self._runner(
                command,
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as error:
            raise WindowsSchedulerTimeoutError(
                "Windows Task Scheduler did not respond in time."
            ) from error
        except OSError as error:
            raise WindowsSchedulerUnavailableError(
                "Windows Task Scheduler is unavailable."
            ) from error

        if result.returncode == 5:
            raise WindowsSchedulerPermissionError(
                "Windows denied permission to manage the CourtSniper task."
            )
        if result.returncode == 6:
            raise SchedulerTaskOwnershipError(
                "A different task already uses the CourtSniper task name."
            )
        if result.returncode == 7:
            raise SchedulerTaskNotInstalledError(
                "The CourtSniper scheduled task is not installed."
            )
        if result.returncode != 0:
            raise WindowsSchedulerOperationError(
                "Windows Task Scheduler operation failed."
            )
        return result


def _status_script() -> str:
    return f"""
$ErrorActionPreference = 'Stop'
try {{
    $task = Get-ScheduledTask -TaskName '{TASK_NAME}' -TaskPath '{TASK_PATH}' -ErrorAction SilentlyContinue
    if ($null -eq $task) {{
        @{{ installed = $false }} | ConvertTo-Json -Compress
        exit 0
    }}
    $info = $task | Get-ScheduledTaskInfo -ErrorAction Stop
    $nextRun = if ($info.NextRunTime -gt [datetime]::MinValue) {{ $info.NextRunTime.ToUniversalTime().ToString('o') }} else {{ $null }}
    $lastRun = if ($info.LastRunTime -gt [datetime]::MinValue) {{ $info.LastRunTime.ToUniversalTime().ToString('o') }} else {{ $null }}
    @{{
        installed = $true
        description = [string]$task.Description
        enabled = [bool]$task.Settings.Enabled
        state = [string]$task.State
        next_run_time = $nextRun
        last_run_time = $lastRun
        last_run_result = if ($null -eq $lastRun) {{ $null }} else {{ [int64]$info.LastTaskResult }}
    }} | ConvertTo-Json -Compress
}} catch [System.UnauthorizedAccessException] {{
    exit 5
}} catch {{
    if ($_.FullyQualifiedErrorId -match 'Unauthorized|AccessDenied') {{ exit 5 }}
    exit 1
}}
""".strip()


def _configure_script(
    plan: SchedulePlan,
    description: str,
    preserve_enabled: bool,
    *,
    python_executable: str,
    scheduled_runner_path: Path,
    backend_dir: Path,
) -> str:
    days = ", ".join(
        f"'{_WINDOWS_WEEKDAYS[weekday]}'" for weekday in plan.trigger_weekdays
    )
    disable_setting = "" if preserve_enabled else " -Disable"
    trigger_time = plan.trigger_time
    action_executable = _powershell_literal(python_executable)
    action_arguments = _powershell_literal(f'"{scheduled_runner_path}"')
    action_working_directory = _powershell_literal(str(backend_dir))
    return f"""
$ErrorActionPreference = 'Stop'
try {{
    $existing = Get-ScheduledTask -TaskName '{TASK_NAME}' -TaskPath '{TASK_PATH}' -ErrorAction SilentlyContinue
    if ($null -ne $existing -and -not ([string]$existing.Description).StartsWith('{TASK_DESCRIPTION_PREFIX}')) {{ exit 6 }}
    $action = New-ScheduledTaskAction -Execute '{action_executable}' -Argument '{action_arguments}' -WorkingDirectory '{action_working_directory}'
    $at = [datetime]::Today.AddHours({trigger_time.hour}).AddMinutes({trigger_time.minute}).AddSeconds({trigger_time.second})
    $trigger = New-ScheduledTaskTrigger -Weekly -WeeksInterval 1 -DaysOfWeek @({days}) -At $at
    $settings = New-ScheduledTaskSettingsSet -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew{disable_setting}
    $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Highest
    Register-ScheduledTask -TaskName '{TASK_NAME}' -TaskPath '{TASK_PATH}' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description '{description}' -Force | Out-Null
}} catch [System.UnauthorizedAccessException] {{
    exit 5
}} catch {{
    if ($_.FullyQualifiedErrorId -match 'Unauthorized|AccessDenied') {{ exit 5 }}
    exit 1
}}
""".strip()


def _powershell_literal(value: str) -> str:
    """Escape an internally derived value for a single-quoted PowerShell literal."""
    return value.replace("'", "''")


def _state_change_script(*, enable: bool) -> str:
    command = "Enable-ScheduledTask" if enable else "Disable-ScheduledTask"
    return f"""
$ErrorActionPreference = 'Stop'
try {{
    $task = Get-ScheduledTask -TaskName '{TASK_NAME}' -TaskPath '{TASK_PATH}' -ErrorAction SilentlyContinue
    if ($null -eq $task) {{ exit 7 }}
    if (-not ([string]$task.Description).StartsWith('{TASK_DESCRIPTION_PREFIX}')) {{ exit 6 }}
    {command} -TaskName '{TASK_NAME}' -TaskPath '{TASK_PATH}' | Out-Null
}} catch [System.UnauthorizedAccessException] {{
    exit 5
}} catch {{
    if ($_.FullyQualifiedErrorId -match 'Unauthorized|AccessDenied') {{ exit 5 }}
    exit 1
}}
""".strip()


def _encode_configuration(plan: SchedulePlan) -> str:
    payload = {
        "schema_version": 1,
        "weekdays": [weekday.value for weekday in plan.weekdays],
        "warmup_minutes": plan.warmup_minutes,
        "target_time": plan.target_time.isoformat(),
    }
    encoded = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).decode("ascii")
    return f"{TASK_DESCRIPTION_PREFIX}{encoded}"


def _decode_configuration(description: str) -> SchedulerTaskConfiguration | None:
    encoded = description.removeprefix(TASK_DESCRIPTION_PREFIX)
    try:
        payload = json.loads(base64.b64decode(encoded, altchars=b"-_", validate=True))
        metadata = _TaskMetadata.model_validate(payload)
        config = ScheduleConfig(
            weekdays=metadata.weekdays,
            warmup_minutes=metadata.warmup_minutes,
        )
        target = BookingTargetTime(
            hour=metadata.target_time.hour,
            minute=metadata.target_time.minute,
            second=metadata.target_time.second,
        )
        plan = calculate_schedule(
            config,
            target,
            now=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
    except (ValueError, ValidationError, json.JSONDecodeError, RuntimeError):
        return None
    return SchedulerTaskConfiguration.from_plan(plan)


def _parse_optional_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise WindowsSchedulerOperationError(
            "Windows Task Scheduler returned an invalid response."
        )
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise WindowsSchedulerOperationError(
            "Windows Task Scheduler returned an invalid response."
        ) from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise WindowsSchedulerOperationError(
            "Windows Task Scheduler returned an invalid response."
        )
    return parsed
