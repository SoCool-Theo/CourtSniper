from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
from unittest import TestCase

from backend.src.scheduler_models import BookingTargetTime, ScheduleConfig, calculate_schedule
from backend.src.windows_scheduler import (
    POWERSHELL_EXECUTABLE,
    TASK_DESCRIPTION_PREFIX,
    TASK_NAME,
    SchedulerTaskNotConfiguredError,
    SchedulerTaskNotInstalledError,
    SchedulerTaskOwnershipError,
    Weekday,
    WindowsSchedulerOperationError,
    WindowsSchedulerPermissionError,
    WindowsSchedulerTimeoutError,
    WindowsSchedulerUnavailableError,
    WindowsSchedulerUnsupportedError,
    WindowsTaskSchedulerAdapter,
    _encode_configuration,
)


BANGKOK = timezone(timedelta(hours=7))


def completed(stdout="", returncode=0, stderr=""):
    return subprocess.CompletedProcess(
        args=[],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def missing_task_result():
    return completed(json.dumps({"installed": False}))


def managed_task_result(
    *,
    enabled=False,
    description=None,
    state=None,
    next_run_time="2026-08-12T07:55:00+07:00",
    last_run_time="2026-08-10T07:55:00+07:00",
    last_run_result=0,
):
    if description is None:
        plan = calculate_schedule(
            ScheduleConfig(weekdays=["MONDAY", "WEDNESDAY"]),
            BookingTargetTime(hour=8, minute=0, second=0),
            now=datetime(2026, 8, 10, 7, 0, tzinfo=BANGKOK),
        )
        description = _encode_configuration(plan)
    return completed(
        json.dumps(
            {
                "installed": True,
                "description": description,
                "enabled": enabled,
                "state": state or ("Ready" if enabled else "Disabled"),
                "next_run_time": next_run_time,
                "last_run_time": last_run_time,
                "last_run_result": last_run_result,
            }
        )
    )


class FakeRunner:
    def __init__(self, *results):
        self.results = list(results)
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append((command, kwargs))
        if not self.results:
            raise AssertionError("No mocked scheduler result remains.")
        result = self.results.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result


class WindowsSchedulerStatusTests(TestCase):
    def test_missing_task_reports_only_safe_empty_status(self):
        runner = FakeRunner(missing_task_result())
        status = WindowsTaskSchedulerAdapter(
            runner=runner,
            platform_name="nt",
        ).get_status()

        self.assertEqual(status.task_name, TASK_NAME)
        self.assertFalse(status.installed)
        self.assertFalse(status.managed)
        self.assertIsNone(status.enabled)
        self.assertIsNone(status.configuration)
        self.assertNotIn("Register-ScheduledTask", runner.calls[0][0][-1])

    def test_owned_task_reports_configuration_and_runtime_information(self):
        runner = FakeRunner(managed_task_result(enabled=True, state="Running"))
        status = WindowsTaskSchedulerAdapter(
            runner=runner,
            platform_name="nt",
        ).get_status()

        self.assertTrue(status.installed)
        self.assertTrue(status.managed)
        self.assertTrue(status.enabled)
        self.assertEqual(status.state, "running")
        self.assertEqual(status.configuration.weekdays, [Weekday.MONDAY, Weekday.WEDNESDAY])
        self.assertEqual(status.configuration.warmup_minutes, 5)
        self.assertEqual(status.configuration.target_time.isoformat(), "08:00:00")
        self.assertEqual(status.configuration.trigger_time.isoformat(), "07:55:00")
        self.assertEqual(status.next_run_time.isoformat(), "2026-08-12T07:55:00+07:00")
        self.assertEqual(status.last_run_result, 0)

    def test_never_run_task_has_no_last_result(self):
        runner = FakeRunner(
            managed_task_result(last_run_time=None, last_run_result=267011)
        )
        status = WindowsTaskSchedulerAdapter(
            runner=runner,
            platform_name="nt",
        ).get_status()

        self.assertIsNone(status.last_run_time)
        self.assertIsNone(status.last_run_result)

    def test_unowned_name_collision_does_not_expose_task_details(self):
        runner = FakeRunner(
            managed_task_result(
                enabled=True,
                description="Someone else's task",
                state="Running",
            )
        )
        status = WindowsTaskSchedulerAdapter(
            runner=runner,
            platform_name="nt",
        ).get_status()

        self.assertTrue(status.installed)
        self.assertFalse(status.managed)
        self.assertIsNone(status.enabled)
        self.assertIsNone(status.state)
        self.assertIsNone(status.next_run_time)
        self.assertIsNone(status.last_run_result)

    def test_owned_task_with_invalid_metadata_is_not_configured(self):
        runner = FakeRunner(
            managed_task_result(description=f"{TASK_DESCRIPTION_PREFIX}not-base64")
        )
        status = WindowsTaskSchedulerAdapter(
            runner=runner,
            platform_name="nt",
        ).get_status()

        self.assertTrue(status.managed)
        self.assertIsNone(status.configuration)

    def test_unknown_windows_state_is_sanitized(self):
        runner = FakeRunner(managed_task_result(state="private machine detail"))
        status = WindowsTaskSchedulerAdapter(
            runner=runner,
            platform_name="nt",
        ).get_status()

        self.assertEqual(status.state, "unknown")


class WindowsSchedulerMutationTests(TestCase):
    def setUp(self):
        self.config = ScheduleConfig(weekdays=["MONDAY", "WEDNESDAY"])
        self.target = BookingTargetTime(hour=8, minute=0, second=30)

    def test_new_configuration_registers_fixed_task_disabled(self):
        runner = FakeRunner(
            missing_task_result(),
            completed(),
            managed_task_result(enabled=False),
        )
        status = WindowsTaskSchedulerAdapter(
            runner=runner,
            platform_name="nt",
        ).configure(self.config, self.target)

        registration_script = runner.calls[1][0][-1]
        self.assertFalse(status.enabled)
        self.assertIn(f"-TaskName '{TASK_NAME}'", registration_script)
        self.assertIn("New-ScheduledTaskSettingsSet", registration_script)
        self.assertIn("-WakeToRun", registration_script)
        self.assertIn("-Disable", registration_script)
        self.assertIn("-LogonType Interactive", registration_script)
        self.assertIn("-RunLevel Highest", registration_script)
        self.assertIn("@('Monday', 'Wednesday')", registration_script)
        self.assertIn("AddHours(7).AddMinutes(55).AddSeconds(30)", registration_script)
        self.assertIn("$existing = Get-ScheduledTask", registration_script)
        self.assertIn(f"StartsWith('{TASK_DESCRIPTION_PREFIX}')", registration_script)

    def test_updating_enabled_owned_task_preserves_enabled_state(self):
        runner = FakeRunner(
            managed_task_result(enabled=True),
            completed(),
            managed_task_result(enabled=True),
        )
        WindowsTaskSchedulerAdapter(
            runner=runner,
            platform_name="nt",
        ).configure(self.config, self.target)

        settings_line = next(
            line for line in runner.calls[1][0][-1].splitlines()
            if "New-ScheduledTaskSettingsSet" in line
        )
        self.assertNotIn("-Disable", settings_line)

    def test_configuration_refuses_unowned_name_collision(self):
        runner = FakeRunner(
            managed_task_result(description="unrecognized existing task")
        )
        adapter = WindowsTaskSchedulerAdapter(runner=runner, platform_name="nt")

        with self.assertRaises(SchedulerTaskOwnershipError):
            adapter.configure(self.config, self.target)

        self.assertEqual(len(runner.calls), 1)

    def test_configuration_handles_an_ownership_race_safely(self):
        runner = FakeRunner(missing_task_result(), completed(returncode=6))
        adapter = WindowsTaskSchedulerAdapter(runner=runner, platform_name="nt")

        with self.assertRaises(SchedulerTaskOwnershipError):
            adapter.configure(self.config, self.target)

        self.assertEqual(len(runner.calls), 2)

    def test_enable_uses_only_fixed_task_name(self):
        runner = FakeRunner(
            managed_task_result(enabled=False),
            completed(),
            managed_task_result(enabled=True),
        )
        status = WindowsTaskSchedulerAdapter(
            runner=runner,
            platform_name="nt",
        ).enable()

        mutation_script = runner.calls[1][0][-1]
        self.assertTrue(status.enabled)
        self.assertIn("Enable-ScheduledTask", mutation_script)
        self.assertIn(f"-TaskName '{TASK_NAME}'", mutation_script)
        self.assertIn(f"StartsWith('{TASK_DESCRIPTION_PREFIX}')", mutation_script)
        self.assertNotIn("Disable-ScheduledTask", mutation_script)

    def test_disable_only_disables_future_fixed_task_runs(self):
        runner = FakeRunner(
            managed_task_result(enabled=True),
            completed(),
            managed_task_result(enabled=False),
        )
        status = WindowsTaskSchedulerAdapter(
            runner=runner,
            platform_name="nt",
        ).disable()

        mutation_script = runner.calls[1][0][-1]
        self.assertFalse(status.enabled)
        self.assertIn("Disable-ScheduledTask", mutation_script)
        self.assertNotIn("Stop-ScheduledTask", mutation_script)
        self.assertNotIn("run-sniper/stop", mutation_script)
        self.assertNotIn("taskkill", mutation_script.lower())

    def test_enable_rejects_missing_task(self):
        runner = FakeRunner(missing_task_result())
        adapter = WindowsTaskSchedulerAdapter(runner=runner, platform_name="nt")

        with self.assertRaises(SchedulerTaskNotInstalledError):
            adapter.enable()

        self.assertEqual(len(runner.calls), 1)

    def test_enable_rejects_owned_task_without_valid_configuration(self):
        runner = FakeRunner(
            managed_task_result(description=f"{TASK_DESCRIPTION_PREFIX}invalid")
        )
        adapter = WindowsTaskSchedulerAdapter(runner=runner, platform_name="nt")

        with self.assertRaises(SchedulerTaskNotConfiguredError):
            adapter.enable()

        self.assertEqual(len(runner.calls), 1)

    def test_disable_rejects_unowned_task(self):
        runner = FakeRunner(managed_task_result(description="not ours"))
        adapter = WindowsTaskSchedulerAdapter(runner=runner, platform_name="nt")

        with self.assertRaises(SchedulerTaskOwnershipError):
            adapter.disable()

        self.assertEqual(len(runner.calls), 1)

    def test_state_change_handles_a_missing_task_race_safely(self):
        runner = FakeRunner(
            managed_task_result(enabled=True),
            completed(returncode=7),
        )
        adapter = WindowsTaskSchedulerAdapter(runner=runner, platform_name="nt")

        with self.assertRaises(SchedulerTaskNotInstalledError):
            adapter.disable()

        self.assertEqual(len(runner.calls), 2)

    def test_fixed_action_launches_only_the_scheduled_runner(self):
        runner = FakeRunner(
            missing_task_result(),
            completed(),
            managed_task_result(enabled=False),
        )
        WindowsTaskSchedulerAdapter(
            runner=runner,
            platform_name="nt",
            python_executable="C:\\CourtSniper\\python.exe",
            scheduled_runner_path=Path(
                "C:\\CourtSniper\\backend\\src\\scheduled_runner.py"
            ),
        ).configure(self.config, self.target)

        registration_script = runner.calls[1][0][-1]
        action_line = next(
            line for line in registration_script.splitlines()
            if "New-ScheduledTaskAction" in line
        )
        self.assertIn("-Execute 'C:\\CourtSniper\\python.exe'", action_line)
        self.assertIn(
            "-Argument '\"C:\\CourtSniper\\backend\\src\\scheduled_runner.py\"'",
            action_line,
        )
        self.assertIn(
            "-WorkingDirectory 'C:\\CourtSniper\\backend'",
            action_line,
        )
        self.assertNotIn("sniper.py", action_line)
        self.assertNotIn("Invoke-RestMethod", action_line)
        self.assertNotIn("run-sniper", action_line)

    def test_action_paths_escape_powershell_literals(self):
        runner = FakeRunner(
            missing_task_result(),
            completed(),
            managed_task_result(enabled=False),
        )
        WindowsTaskSchedulerAdapter(
            runner=runner,
            platform_name="nt",
            python_executable="C:\\Court'Sniper\\python.exe",
            scheduled_runner_path=Path(
                "C:\\Court'Sniper\\backend\\src\\scheduled_runner.py"
            ),
        ).configure(self.config, self.target)

        registration_script = runner.calls[1][0][-1]
        self.assertIn("Court''Sniper", registration_script)


class WindowsSchedulerCommandSafetyTests(TestCase):
    def test_runner_is_always_non_shell_with_fixed_powershell_prefix(self):
        runner = FakeRunner(missing_task_result())
        WindowsTaskSchedulerAdapter(
            runner=runner,
            platform_name="nt",
        ).get_status()

        command, options = runner.calls[0]
        self.assertEqual(command[:5], [
            POWERSHELL_EXECUTABLE,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
        ])
        self.assertFalse(options["shell"])
        self.assertFalse(options["check"])
        self.assertTrue(options["capture_output"])

    def test_non_windows_platform_is_rejected_before_runner_call(self):
        runner = FakeRunner()
        adapter = WindowsTaskSchedulerAdapter(runner=runner, platform_name="posix")

        with self.assertRaises(WindowsSchedulerUnsupportedError):
            adapter.get_status()

        self.assertEqual(runner.calls, [])

    def test_timeout_is_wrapped_without_command_details(self):
        private_command = "C:\\private\\secret.ps1"
        runner = FakeRunner(
            subprocess.TimeoutExpired(private_command, timeout=10)
        )
        adapter = WindowsTaskSchedulerAdapter(runner=runner, platform_name="nt")

        with self.assertRaises(WindowsSchedulerTimeoutError) as context:
            adapter.get_status()

        self.assertNotIn("private", str(context.exception).lower())

    def test_missing_powershell_is_reported_safely(self):
        runner = FakeRunner(OSError("C:\\private\\powershell.exe was not found"))
        adapter = WindowsTaskSchedulerAdapter(runner=runner, platform_name="nt")

        with self.assertRaises(WindowsSchedulerUnavailableError) as context:
            adapter.get_status()

        self.assertNotIn("private", str(context.exception).lower())

    def test_permission_failure_uses_only_safe_message(self):
        runner = FakeRunner(completed(returncode=5, stderr="secret local detail"))
        adapter = WindowsTaskSchedulerAdapter(runner=runner, platform_name="nt")

        with self.assertRaises(WindowsSchedulerPermissionError) as context:
            adapter.get_status()

        self.assertNotIn("secret", str(context.exception).lower())

    def test_generic_command_failure_does_not_expose_output(self):
        runner = FakeRunner(completed(returncode=1, stderr="credential=secret"))
        adapter = WindowsTaskSchedulerAdapter(runner=runner, platform_name="nt")

        with self.assertRaises(WindowsSchedulerOperationError) as context:
            adapter.get_status()

        self.assertNotIn("credential", str(context.exception).lower())

    def test_invalid_json_is_reported_safely(self):
        runner = FakeRunner(completed(stdout="not scheduler json"))
        adapter = WindowsTaskSchedulerAdapter(runner=runner, platform_name="nt")

        with self.assertRaises(WindowsSchedulerOperationError):
            adapter.get_status()
