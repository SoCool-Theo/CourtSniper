from pathlib import Path
import sys
from types import ModuleType
from unittest import TestCase
from unittest.mock import Mock, patch

from backend.src import sniper as legacy_sniper
from backend.src import sniper_process as legacy_process
from backend.src.booking import process, sniper


class BookingImportCompatibilityTests(TestCase):
    def test_sniper_symbols_are_reexported_from_the_legacy_module(self):
        symbol_names = (
            "CURRENT_DIR",
            "ROOT_DIR",
            "ENV_PATH",
            "_create_playwright_context",
            "_get_configured_status",
            "_load_booking_config",
            "_load_environment",
            "_require_armed_status",
            "run_sniper",
        )

        for symbol_name in symbol_names:
            with self.subTest(symbol=symbol_name):
                self.assertIs(
                    getattr(legacy_sniper, symbol_name),
                    getattr(sniper, symbol_name),
                )

    def test_process_symbols_are_reexported_from_the_legacy_module(self):
        symbol_names = (
            "ManagedProcess",
            "ProcessFactory",
            "SniperAlreadyRunningError",
            "SniperLaunchError",
            "SniperNotRunningError",
            "SniperProcessError",
            "SniperProcessManager",
            "SniperRunStatus",
            "SniperScriptNotFoundError",
            "SniperStopError",
            "StopAction",
            "_force_stop_process_group",
            "_process_group_launch_options",
            "_request_process_group_stop",
        )

        for symbol_name in symbol_names:
            with self.subTest(symbol=symbol_name):
                self.assertIs(
                    getattr(legacy_process, symbol_name),
                    getattr(process, symbol_name),
                )

    def test_legacy_entrypoint_delegates_to_the_booking_implementation(self):
        with patch.object(legacy_sniper, "run_sniper", return_value=None) as run:
            self.assertIsNone(legacy_sniper.main())

        run.assert_called_once_with()

    def test_default_process_path_still_targets_the_legacy_entrypoint(self):
        manager = process.SniperProcessManager()
        backend_dir = Path(__file__).resolve().parents[1]

        self.assertEqual(
            manager._script_path,
            (backend_dir / "src" / "sniper.py").resolve(),
        )
        self.assertEqual(manager._backend_dir, backend_dir)

    def test_automation_paths_still_target_the_backend_root(self):
        backend_dir = Path(__file__).resolve().parents[1]

        self.assertEqual(Path(sniper.CURRENT_DIR), backend_dir / "src")
        self.assertEqual(Path(sniper.ROOT_DIR), backend_dir)
        self.assertEqual(Path(sniper.ENV_PATH), backend_dir / ".env")

    def test_environment_loader_uses_only_the_fixed_backend_path(self):
        dotenv_module = ModuleType("dotenv")
        dotenv_module.load_dotenv = Mock()

        with patch.dict(sys.modules, {"dotenv": dotenv_module}):
            sniper._load_environment()

        dotenv_module.load_dotenv.assert_called_once_with(
            dotenv_path=sniper.ENV_PATH,
        )
