from datetime import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from fastapi import HTTPException

from backend.src import api
from backend.src.scheduler_models import BookingTargetTime, ScheduleConfig, Weekday
from backend.src.windows_scheduler import (
    SchedulerTaskConfiguration,
    SchedulerTaskNotConfiguredError,
    SchedulerTaskNotInstalledError,
    SchedulerTaskOwnershipError,
    WindowsSchedulerOperationError,
    WindowsSchedulerPermissionError,
    WindowsSchedulerStatus,
    WindowsSchedulerTimeoutError,
    WindowsSchedulerUnavailableError,
    WindowsSchedulerUnsupportedError,
)


def scheduler_configuration(target_time=time(8, 0, 0)):
    return SchedulerTaskConfiguration(
        weekdays=[Weekday.MONDAY, Weekday.WEDNESDAY],
        warmup_minutes=5,
        target_time=target_time,
        trigger_weekdays=[Weekday.MONDAY, Weekday.WEDNESDAY],
        trigger_time=time(7, 55, 0),
    )


def scheduler_status(*, installed=True, managed=True, enabled=False, configuration=None):
    if configuration is None and installed and managed:
        configuration = scheduler_configuration()
    return WindowsSchedulerStatus(
        installed=installed,
        managed=managed,
        enabled=enabled if managed else None,
        state="ready" if enabled else "disabled" if managed else None,
        next_run_time="2026-08-12T00:55:00+00:00" if enabled else None,
        last_run_time="2026-08-10T00:55:00+00:00" if managed else None,
        last_run_result=0 if managed else None,
        configuration=configuration,
    )


class FakeSchedulerAdapter:
    def __init__(self, status=None):
        self.status = status or scheduler_status()
        self.status_error = None
        self.configure_error = None
        self.enable_error = None
        self.disable_error = None
        self.status_calls = 0
        self.configure_calls = []
        self.enable_calls = 0
        self.disable_calls = 0

    def get_status(self):
        self.status_calls += 1
        if self.status_error:
            raise self.status_error
        return self.status

    def configure(self, config, target):
        self.configure_calls.append((config, target))
        if self.configure_error:
            raise self.configure_error
        self.status = scheduler_status(enabled=False)
        return self.status

    def enable(self):
        self.enable_calls += 1
        if self.enable_error:
            raise self.enable_error
        self.status = scheduler_status(enabled=True)
        return self.status

    def disable(self):
        self.disable_calls += 1
        if self.disable_error:
            raise self.disable_error
        self.status = scheduler_status(enabled=False)
        return self.status


class SchedulerApiTests(TestCase):
    def setUp(self):
        self.adapter = FakeSchedulerAdapter()
        self.original_adapter = api.scheduler_adapter
        api.scheduler_adapter = self.adapter
        self.target_patch = patch.object(
            api,
            "_get_booking_target_time",
            return_value=BookingTargetTime(hour=8, minute=0, second=0),
        )
        self.target_reader = self.target_patch.start()

    def tearDown(self):
        self.target_patch.stop()
        api.scheduler_adapter = self.original_adapter

    def test_get_scheduler_reports_safe_status_and_sync(self):
        response = api.get_scheduler_status()

        self.assertEqual(response["task_name"], "CourtSniper")
        self.assertTrue(response["installed"])
        self.assertTrue(response["managed"])
        self.assertFalse(response["enabled"])
        self.assertTrue(response["configured"])
        self.assertTrue(response["configuration_in_sync"])
        self.assertNotIn("command", response)
        self.assertNotIn("path", response)

    def test_get_scheduler_reports_missing_task_without_reading_target(self):
        self.adapter.status = scheduler_status(
            installed=False,
            managed=False,
            configuration=None,
        )

        response = api.get_scheduler_status()

        self.assertFalse(response["installed"])
        self.assertFalse(response["configured"])
        self.assertIsNone(response["configuration_in_sync"])
        self.target_reader.assert_not_called()

    def test_get_scheduler_reports_stale_target(self):
        self.target_reader.return_value = BookingTargetTime(hour=9, minute=0, second=0)

        response = api.get_scheduler_status()

        self.assertFalse(response["configuration_in_sync"])

    def test_configure_uses_existing_booking_target(self):
        config = ScheduleConfig(weekdays=["FRIDAY"], warmup_minutes=10)

        response = api.configure_scheduler(config)

        called_config, called_target = self.adapter.configure_calls[0]
        self.assertEqual(called_config, config)
        self.assertEqual(called_target.as_time(), time(8, 0, 0))
        self.assertEqual(response["message"], "CourtSniper schedule configured.")
        self.assertFalse(response["scheduler"]["enabled"])

    def test_configure_rejects_missing_booking_target(self):
        self.target_reader.side_effect = api.BookingTargetConfigurationError(
            "Configure a valid booking target time before scheduling CourtSniper."
        )

        with self.assertRaises(HTTPException) as context:
            api.configure_scheduler(ScheduleConfig(weekdays=["MONDAY"]))

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(self.adapter.configure_calls, [])

    def test_enable_rejects_stale_target_before_mutation(self):
        self.target_reader.return_value = BookingTargetTime(hour=9, minute=0, second=0)

        with self.assertRaises(HTTPException) as context:
            api.enable_scheduler()

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(self.adapter.enable_calls, 0)

    @patch.object(api, "_get_configured_status", return_value="DISARMED")
    def test_enable_remains_independent_from_armed_state(self, configured_status):
        response = api.enable_scheduler()

        self.assertEqual(response["message"], "CourtSniper schedule enabled.")
        self.assertEqual(self.adapter.enable_calls, 1)
        configured_status.assert_not_called()

    def test_disable_does_not_stop_an_active_sniper_run(self):
        process_manager = api.sniper_process_manager
        with patch.object(process_manager, "stop") as stop:
            response = api.disable_scheduler()

        self.assertEqual(response["message"], "CourtSniper schedule disabled.")
        self.assertEqual(self.adapter.disable_calls, 1)
        stop.assert_not_called()

    def test_scheduler_errors_map_to_sanitized_http_statuses(self):
        cases = (
            (WindowsSchedulerPermissionError("permission denied"), 403),
            (WindowsSchedulerTimeoutError("timed out"), 504),
            (WindowsSchedulerUnavailableError("unavailable"), 503),
            (WindowsSchedulerUnsupportedError("unsupported"), 503),
            (SchedulerTaskOwnershipError("name collision"), 409),
            (SchedulerTaskNotInstalledError("not installed"), 409),
            (SchedulerTaskNotConfiguredError("not configured"), 409),
            (WindowsSchedulerOperationError("private local detail"), 500),
        )

        for error, expected_status in cases:
            with self.subTest(error=type(error).__name__):
                self.adapter.status_error = error
                with self.assertRaises(HTTPException) as context:
                    api.get_scheduler_status()
                self.assertEqual(context.exception.status_code, expected_status)
                if expected_status == 500:
                    self.assertNotIn("private", context.exception.detail)
        self.adapter.status_error = None


class SchedulerApiRouteContractTests(TestCase):
    def test_scheduler_routes_are_registered(self):
        route_contracts = {
            (route.path, tuple(sorted(route.methods)), route.status_code)
            for route in api.app.routes
            if route.path.startswith("/api/scheduler")
        }

        self.assertEqual(
            route_contracts,
            {
                ("/api/scheduler", ("GET",), 200),
                ("/api/scheduler/config", ("POST",), 200),
                ("/api/scheduler/enable", ("POST",), 200),
                ("/api/scheduler/disable", ("POST",), 200),
            },
        )


class ConfigurationApiSafetyTests(TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.env_path = Path(self.temporary_directory.name) / "test.env"
        self.env_path.write_text(
            'TARGET_URL="https://example.invalid/messages/test"\n'
            'TARGET_HOUR="8"\n'
            'TARGET_MINUTE="0"\n'
            'TARGET_SECOND="0"\n'
            'STATUS="ARMED"\n'
            'PRIVATE_CREDENTIAL="do-not-expose"\n',
            encoding="utf-8",
        )
        self.path_patch = patch.object(api, "ENV_FILE_PATH", str(self.env_path))
        self.path_patch.start()

    def tearDown(self):
        self.path_patch.stop()
        self.temporary_directory.cleanup()

    def test_get_config_does_not_expose_unrecognized_env_fields(self):
        response = api.get_config()

        self.assertEqual(response["TARGET_HOUR"], "8")
        self.assertNotIn("PRIVATE_CREDENTIAL", response)
        self.assertNotIn("do-not-expose", response.values())

    def test_update_config_rejects_unrecognized_fields_without_writing(self):
        original = self.env_path.read_text(encoding="utf-8")

        with self.assertRaises(HTTPException) as context:
            api.update_config({"PRIVATE_CREDENTIAL": "changed"})

        self.assertEqual(context.exception.status_code, 422)
        self.assertEqual(self.env_path.read_text(encoding="utf-8"), original)

    def test_update_config_preserves_private_fields_while_editing_allowed_field(self):
        api.update_config({"TARGET_HOUR": "9"})

        updated = self.env_path.read_text(encoding="utf-8")
        self.assertIn('TARGET_HOUR="9"', updated)
        self.assertIn('PRIVATE_CREDENTIAL="do-not-expose"', updated)
