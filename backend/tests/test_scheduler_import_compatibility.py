from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from backend.src import scheduled_runner as legacy_runner
from backend.src import scheduler_models as legacy_models
from backend.src import windows_scheduler as legacy_windows
from backend.src.scheduler import models, runner, windows


class SchedulerImportCompatibilityTests(TestCase):
    def test_model_symbols_are_reexported_from_the_legacy_module(self):
        symbol_names = (
            "MAX_WARMUP_MINUTES",
            "BookingTargetTime",
            "ScheduleConfig",
            "SchedulePlan",
            "Weekday",
            "_CALCULATION_HORIZON_DAYS",
            "_WEEKDAYS",
            "_trigger_time",
            "_trigger_weekdays",
            "calculate_schedule",
        )

        for symbol_name in symbol_names:
            with self.subTest(symbol=symbol_name):
                self.assertIs(
                    getattr(legacy_models, symbol_name),
                    getattr(models, symbol_name),
                )

    def test_runner_symbols_are_reexported_from_the_legacy_module(self):
        symbol_names = (
            "ACTIVE_RUN_STATES",
            "API_BASE_URL",
            "API_HOST",
            "API_PORT",
            "API_SERVICE_ID",
            "EXIT_AUTOMATION_FAILED",
            "EXIT_AUTOMATION_STOPPED",
            "EXIT_RUNNER_ERROR",
            "EXIT_RUN_REJECTED",
            "EXIT_SUCCESS",
            "KNOWN_RUN_STATES",
            "TERMINAL_RUN_STATES",
            "ApiClient",
            "ApiHttpError",
            "ApiUnavailableError",
            "CourtSniperApiClient",
            "ManagedApiProcess",
            "ProcessFactory",
            "ScheduledRunner",
            "ScheduledRunnerError",
            "UnexpectedApiError",
            "_api_launch_options",
            "main",
        )

        for symbol_name in symbol_names:
            with self.subTest(symbol=symbol_name):
                self.assertIs(
                    getattr(legacy_runner, symbol_name),
                    getattr(runner, symbol_name),
                )

    def test_windows_symbols_are_reexported_from_the_legacy_module(self):
        symbol_names = (
            "POWERSHELL_EXECUTABLE",
            "TASK_DESCRIPTION_PREFIX",
            "TASK_NAME",
            "TASK_PATH",
            "BookingTargetTime",
            "CommandRunner",
            "ScheduleConfig",
            "SchedulePlan",
            "SchedulerTaskConfiguration",
            "SchedulerTaskNotConfiguredError",
            "SchedulerTaskNotInstalledError",
            "SchedulerTaskOwnershipError",
            "Weekday",
            "WindowsSchedulerError",
            "WindowsSchedulerOperationError",
            "WindowsSchedulerPermissionError",
            "WindowsSchedulerStatus",
            "WindowsSchedulerTimeoutError",
            "WindowsSchedulerUnavailableError",
            "WindowsSchedulerUnsupportedError",
            "WindowsTaskSchedulerAdapter",
            "_KNOWN_STATES",
            "_POWERSHELL_PREFIX",
            "_TaskMetadata",
            "_WINDOWS_WEEKDAYS",
            "_configure_script",
            "_decode_configuration",
            "_encode_configuration",
            "_parse_optional_datetime",
            "_powershell_literal",
            "_state_change_script",
            "_status_script",
            "calculate_schedule",
        )

        for symbol_name in symbol_names:
            with self.subTest(symbol=symbol_name):
                self.assertIs(
                    getattr(legacy_windows, symbol_name),
                    getattr(windows, symbol_name),
                )

    def test_legacy_runner_main_preserves_the_result_code(self):
        scheduled_runner = Mock()
        scheduled_runner.run.return_value = runner.EXIT_AUTOMATION_STOPPED

        with patch.object(runner, "ScheduledRunner", return_value=scheduled_runner):
            result = legacy_runner.main()

        self.assertEqual(result, runner.EXIT_AUTOMATION_STOPPED)
        scheduled_runner.run.assert_called_once_with()

    def test_runner_default_working_directory_remains_the_backend_root(self):
        scheduled_runner = runner.ScheduledRunner(api_client=Mock())
        backend_dir = Path(__file__).resolve().parents[1]

        self.assertEqual(scheduled_runner._backend_dir, backend_dir)

    def test_adapter_default_action_remains_the_legacy_runner(self):
        adapter = windows.WindowsTaskSchedulerAdapter(
            runner=Mock(),
            platform_name="test",
            python_executable="test-python",
        )
        backend_dir = Path(__file__).resolve().parents[1]

        self.assertEqual(
            adapter._scheduled_runner_path,
            (backend_dir / "src" / "scheduled_runner.py").resolve(),
        )
        self.assertEqual(adapter._backend_dir, backend_dir)
        adapter._runner.assert_not_called()
