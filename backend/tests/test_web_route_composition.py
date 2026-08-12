import importlib
from pathlib import Path
import sys
from unittest import TestCase
from unittest.mock import patch

from fastapi.middleware.cors import CORSMiddleware

from backend.src import api
from backend.src.setup_session_process import SetupSessionProcessManager
from backend.src.sniper_process import SniperProcessManager
from backend.src.windows_scheduler import WindowsTaskSchedulerAdapter


class WebRouteCompositionTests(TestCase):
    def test_api_composition_root_remains_stable(self):
        self.assertEqual(api.app.title, "CourtSniper Web UI")
        self.assertIsInstance(
            api.setup_session_process_manager,
            SetupSessionProcessManager,
        )
        self.assertIsInstance(api.sniper_process_manager, SniperProcessManager)
        self.assertIsInstance(api.scheduler_adapter, WindowsTaskSchedulerAdapter)

    def test_scheduled_runner_import_target_still_exports_the_app(self):
        backend_dir = Path(__file__).resolve().parents[1]

        with patch.object(sys, "path", [str(backend_dir), *sys.path]):
            scheduled_api = importlib.import_module("src.api")

        self.assertIsNotNone(scheduled_api.app)
        self.assertEqual(scheduled_api.app.title, "CourtSniper Web UI")

    def test_cors_contract_is_unchanged(self):
        middleware = next(
            item
            for item in api.app.user_middleware
            if item.cls is CORSMiddleware
        )

        self.assertEqual(middleware.kwargs["allow_origins"], ["*"])
        self.assertTrue(middleware.kwargs["allow_credentials"])
        self.assertEqual(middleware.kwargs["allow_methods"], ["*"])
        self.assertEqual(middleware.kwargs["allow_headers"], ["*"])

    def test_complete_api_route_contract_is_unchanged(self):
        route_contracts = {
            (route.path, tuple(sorted(route.methods)), route.status_code)
            for route in api.app.routes
            if route.path.startswith("/api/")
        }

        self.assertEqual(
            route_contracts,
            {
                ("/api/status", ("GET",), None),
                ("/api/config", ("GET",), None),
                ("/api/config", ("POST",), None),
                ("/api/run-setup", ("POST",), None),
                ("/api/run-sniper", ("POST",), 202),
                ("/api/run-sniper/status", ("GET",), 200),
                ("/api/run-sniper/stop", ("POST",), 200),
                ("/api/scheduler", ("GET",), 200),
                ("/api/scheduler/config", ("POST",), 200),
                ("/api/scheduler/enable", ("POST",), 200),
                ("/api/scheduler/disable", ("POST",), 200),
            },
        )

    def test_route_handlers_are_owned_by_the_feature_modules(self):
        expected_modules = {
            "/api/status": "backend.src.web.config_routes",
            "/api/config": "backend.src.web.config_routes",
            "/api/run-setup": "backend.src.web.session_routes",
            "/api/run-sniper": "backend.src.web.sniper_routes",
            "/api/run-sniper/status": "backend.src.web.sniper_routes",
            "/api/run-sniper/stop": "backend.src.web.sniper_routes",
            "/api/scheduler": "backend.src.web.scheduler_routes",
            "/api/scheduler/config": "backend.src.web.scheduler_routes",
            "/api/scheduler/enable": "backend.src.web.scheduler_routes",
            "/api/scheduler/disable": "backend.src.web.scheduler_routes",
        }

        for route in api.app.routes:
            expected_module = expected_modules.get(route.path)
            if expected_module is not None:
                with self.subTest(path=route.path, methods=route.methods):
                    self.assertEqual(route.endpoint.__module__, expected_module)

    def test_api_exports_the_registered_handler_objects(self):
        exported_handlers = (
            api.get_status,
            api.get_config,
            api.update_config,
            api.trigger_setup,
            api.trigger_sniper,
            api.get_sniper_run_status,
            api.stop_sniper,
            api.get_scheduler_status,
            api.configure_scheduler,
            api.enable_scheduler,
            api.disable_scheduler,
        )
        registered_endpoints = {route.endpoint for route in api.app.routes}

        for handler in exported_handlers:
            with self.subTest(handler=handler.__name__):
                self.assertIn(handler, registered_endpoints)
