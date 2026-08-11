import sys
from inspect import signature
from types import ModuleType, SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

try:
    from fastapi import HTTPException
except ModuleNotFoundError:
    fastapi_module = ModuleType("fastapi")
    middleware_module = ModuleType("fastapi.middleware")
    cors_module = ModuleType("fastapi.middleware.cors")

    class HTTPException(Exception):
        def __init__(self, status_code, detail):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    class FakeRoute:
        def __init__(self, path, method, status_code):
            self.path = path
            self.methods = {method}
            self.status_code = status_code

    class FastAPI:
        def __init__(self, **kwargs):
            self.routes = []

        def add_middleware(self, middleware_class, **kwargs):
            return None

        def _route(self, method, path, status_code=200):
            def decorator(function):
                self.routes.append(FakeRoute(path, method, status_code))
                return function

            return decorator

        def get(self, path, status_code=200):
            return self._route("GET", path, status_code)

        def post(self, path, status_code=200):
            return self._route("POST", path, status_code)

    class CORSMiddleware:
        pass

    fastapi_module.FastAPI = FastAPI
    fastapi_module.HTTPException = HTTPException
    fastapi_module.status = SimpleNamespace(
        HTTP_202_ACCEPTED=202,
        HTTP_409_CONFLICT=409,
        HTTP_500_INTERNAL_SERVER_ERROR=500,
    )
    cors_module.CORSMiddleware = CORSMiddleware
    sys.modules["fastapi"] = fastapi_module
    sys.modules["fastapi.middleware"] = middleware_module
    sys.modules["fastapi.middleware.cors"] = cors_module

from backend.src import api
from backend.src.sniper_process import (
    SniperAlreadyRunningError,
    SniperLaunchError,
    SniperNotRunningError,
    SniperRunStatus,
    SniperScriptNotFoundError,
    SniperStopError,
)


class FakeSniperProcessManager:
    def __init__(self):
        self.start_calls = 0
        self.start_error = None
        self.stop_calls = 0
        self.stop_error = None
        self.status = SniperRunStatus()

    def start(self):
        self.start_calls += 1
        if self.start_error:
            raise self.start_error
        self.status = SniperRunStatus(
            state="running",
            pid=4321,
            started_at="2026-08-10T00:00:00+00:00",
        )
        return self.status

    def get_status(self):
        return self.status

    def stop(self):
        self.stop_calls += 1
        if self.stop_error:
            raise self.stop_error
        self.status = SniperRunStatus(
            state="stopped",
            pid=4321,
            started_at="2026-08-10T00:00:00+00:00",
            finished_at="2026-08-10T00:00:30+00:00",
            exit_code=130,
        )
        return self.status


class SniperApiTests(TestCase):
    def setUp(self):
        self.manager = FakeSniperProcessManager()
        self.original_manager = api.sniper_process_manager
        api.sniper_process_manager = self.manager

    def tearDown(self):
        api.sniper_process_manager = self.original_manager

    @patch.object(api, "_get_configured_status", return_value="ARMED")
    def test_status_reports_an_armed_backend(self, configured_status):
        response = api.get_status()

        configured_status.assert_called_once_with()
        self.assertEqual(
            response,
            {
                "service": "CourtSniper",
                "status": "online",
                "execution_status": "ARMED",
                "armed": True,
            },
        )

    @patch.object(api, "_get_configured_status", return_value="DISARMED")
    def test_status_reports_a_disarmed_backend(self, configured_status):
        response = api.get_status()

        configured_status.assert_called_once_with()
        self.assertEqual(
            response,
            {
                "service": "CourtSniper",
                "status": "online",
                "execution_status": "DISARMED",
                "armed": False,
            },
        )

    @patch.object(api, "_get_configured_status", return_value=None)
    def test_status_reports_an_unknown_execution_status(self, configured_status):
        response = api.get_status()

        configured_status.assert_called_once_with()
        self.assertEqual(
            response,
            {
                "service": "CourtSniper",
                "status": "online",
                "execution_status": "UNKNOWN",
                "armed": False,
            },
        )

    @patch.object(api, "_get_configured_status", return_value="ARMED")
    def test_trigger_sniper_starts_an_armed_run(self, configured_status):
        response = api.trigger_sniper()

        configured_status.assert_called_once_with()
        self.assertEqual(self.manager.start_calls, 1)
        self.assertEqual(response["message"], "CourtSniper run started.")
        self.assertEqual(response["run"]["state"], "running")
        self.assertEqual(response["run"]["pid"], 4321)

    @patch.object(api, "_get_configured_status", return_value="DISARMED")
    def test_trigger_sniper_rejects_a_disarmed_run(self, configured_status):
        with self.assertRaises(HTTPException) as context:
            api.trigger_sniper()

        configured_status.assert_called_once_with()
        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(self.manager.start_calls, 0)

    @patch.object(api, "_get_configured_status", return_value=None)
    def test_trigger_sniper_rejects_a_missing_status(self, configured_status):
        with self.assertRaises(HTTPException) as context:
            api.trigger_sniper()

        configured_status.assert_called_once_with()
        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(self.manager.start_calls, 0)

    @patch.object(api, "_get_configured_status", return_value="ARMED")
    def test_trigger_sniper_rejects_a_concurrent_run(self, configured_status):
        self.manager.start_error = SniperAlreadyRunningError(
            "A sniper run is already active."
        )

        with self.assertRaises(HTTPException) as context:
            api.trigger_sniper()

        configured_status.assert_called_once_with()
        self.assertEqual(context.exception.status_code, 409)

    @patch.object(api, "_get_configured_status", return_value="ARMED")
    def test_trigger_sniper_reports_a_missing_entry_point(self, configured_status):
        self.manager.start_error = SniperScriptNotFoundError(
            "The sniper entry point is unavailable."
        )

        with self.assertRaises(HTTPException) as context:
            api.trigger_sniper()

        configured_status.assert_called_once_with()
        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(
            context.exception.detail,
            "The sniper entry point is unavailable.",
        )

    @patch.object(api, "_get_configured_status", return_value="ARMED")
    def test_trigger_sniper_reports_a_safe_launch_error(self, configured_status):
        self.manager.start_error = SniperLaunchError(
            "The sniper process could not be started."
        )

        with self.assertRaises(HTTPException) as context:
            api.trigger_sniper()

        configured_status.assert_called_once_with()
        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(
            context.exception.detail,
            "The sniper process could not be started.",
        )

    def test_get_sniper_run_status_returns_only_the_snapshot(self):
        self.manager.status = SniperRunStatus(
            state="succeeded",
            pid=4321,
            started_at="2026-08-10T00:00:00+00:00",
            finished_at="2026-08-10T00:01:00+00:00",
            exit_code=0,
        )

        response = api.get_sniper_run_status()

        self.assertEqual(
            response,
            {
                "run": {
                    "state": "succeeded",
                    "pid": 4321,
                    "started_at": "2026-08-10T00:00:00+00:00",
                    "finished_at": "2026-08-10T00:01:00+00:00",
                    "exit_code": 0,
                }
            },
        )

    def test_stop_sniper_returns_the_stopped_run(self):
        response = api.stop_sniper()

        self.assertEqual(self.manager.stop_calls, 1)
        self.assertEqual(response["message"], "CourtSniper run stopped.")
        self.assertEqual(response["run"]["state"], "stopped")
        self.assertEqual(response["run"]["pid"], 4321)
        self.assertEqual(response["run"]["exit_code"], 130)

    def test_stop_sniper_rejects_a_request_without_an_active_run(self):
        self.manager.stop_error = SniperNotRunningError(
            "No sniper run is currently active."
        )

        with self.assertRaises(HTTPException) as context:
            api.stop_sniper()

        self.assertEqual(self.manager.stop_calls, 1)
        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(
            context.exception.detail,
            "No sniper run is currently active.",
        )

    def test_stop_sniper_reports_a_safe_termination_error(self):
        self.manager.stop_error = SniperStopError(
            "The sniper process could not be stopped."
        )

        with self.assertRaises(HTTPException) as context:
            api.stop_sniper()

        self.assertEqual(self.manager.stop_calls, 1)
        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(
            context.exception.detail,
            "The sniper process could not be stopped.",
        )


class SniperApiRouteContractTests(TestCase):
    def test_run_sniper_routes_are_registered(self):
        route_contracts = {
            (route.path, tuple(sorted(route.methods)), route.status_code)
            for route in api.app.routes
            if route.path.startswith("/api/run-sniper")
        }

        self.assertIn(
            ("/api/run-sniper", ("POST",), 202),
            route_contracts,
        )
        self.assertIn(
            ("/api/run-sniper/status", ("GET",), 200),
            route_contracts,
        )
        self.assertIn(
            ("/api/run-sniper/stop", ("POST",), 200),
            route_contracts,
        )


class SetupSessionApiSecurityTests(TestCase):
    def setUp(self):
        self.manager = Mock()
        self.manager.start.return_value = SimpleNamespace(already_running=False)
        self.original_manager = api.setup_session_process_manager
        api.setup_session_process_manager = self.manager

    def tearDown(self):
        api.setup_session_process_manager = self.original_manager

    def test_run_setup_accepts_no_client_configuration(self):
        self.assertEqual(tuple(signature(api.trigger_setup).parameters), ())

    def test_run_setup_starts_the_internal_process_manager(self):
        response = api.trigger_setup()

        self.manager.start.assert_called_once_with()
        self.assertEqual(
            response,
            {
                "message": "Setup session launched! Check your laptop screen.",
                "already_running": False,
            },
        )

    def test_run_setup_reuses_an_active_login_window(self):
        self.manager.start.return_value = SimpleNamespace(already_running=True)

        response = api.trigger_setup()

        self.manager.start.assert_called_once_with()
        self.assertEqual(
            response,
            {
                "message": (
                    "Login browser is already open. "
                    "Continue setup in the existing window."
                ),
                "already_running": True,
            },
        )

    def test_run_setup_reports_only_sanitized_launch_failures(self):
        self.manager.start.side_effect = api.SetupSessionLaunchError(
            "The login setup process could not be started."
        )

        with self.assertRaises(HTTPException) as context:
            api.trigger_setup()

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(
            context.exception.detail,
            "The login setup process could not be started.",
        )

    def test_run_setup_route_is_registered_as_bodyless_post(self):
        routes = [
            route
            for route in api.app.routes
            if route.path == "/api/run-setup" and "POST" in route.methods
        ]

        self.assertEqual(len(routes), 1)
        self.assertEqual(tuple(signature(api.trigger_setup).parameters), ())
