from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from backend.src import setup_session as legacy_setup
from backend.src import setup_session_guard as legacy_guard
from backend.src import setup_session_process as legacy_process
from backend.src.session import guard, process, setup


class SessionImportCompatibilityTests(TestCase):
    def test_setup_symbols_are_reexported_from_the_legacy_module(self):
        symbol_names = (
            "ALLOWED_TARGET_DOMAINS",
            "LOGIN_WINDOW_TIMEOUT_MS",
            "MESSENGER_INBOX_URL",
            "SETUP_ALREADY_RUNNING_EXIT_CODE",
            "_close_browser_context",
            "_create_playwright_context",
            "_is_allowed_target_url",
            "_load_configured_target_url",
            "_wait_for_browser_completion",
            "create_persistent_session",
            "create_setup_session_guard",
            "resolve_login_url",
        )

        for symbol_name in symbol_names:
            with self.subTest(symbol=symbol_name):
                self.assertIs(
                    getattr(legacy_setup, symbol_name),
                    getattr(setup, symbol_name),
                )

    def test_guard_symbols_are_reexported_from_the_legacy_module(self):
        symbol_names = (
            "ERROR_ALREADY_EXISTS",
            "MUTEX_NAME_PREFIX",
            "SetupSessionGuardError",
            "WindowsNamedMutex",
            "_load_kernel32",
            "create_setup_session_guard",
            "setup_session_mutex_name",
        )

        for symbol_name in symbol_names:
            with self.subTest(symbol=symbol_name):
                self.assertIs(
                    getattr(legacy_guard, symbol_name),
                    getattr(guard, symbol_name),
                )

    def test_process_symbols_are_reexported_from_the_legacy_module(self):
        symbol_names = (
            "SETUP_SCRIPT_FILENAME",
            "SETUP_ALREADY_RUNNING_EXIT_CODE",
            "STARTUP_PROBE_SECONDS",
            "SetupSessionGuardError",
            "SetupSessionLaunchError",
            "SetupSessionProcessError",
            "SetupSessionProcessManager",
            "SetupSessionScriptNotFoundError",
            "SetupSessionStartResult",
            "create_setup_session_guard",
        )

        for symbol_name in symbol_names:
            with self.subTest(symbol=symbol_name):
                self.assertIs(
                    getattr(legacy_process, symbol_name),
                    getattr(process, symbol_name),
                )

    def test_legacy_entrypoint_preserves_success_and_duplicate_exit_codes(self):
        with patch.object(legacy_setup, "create_persistent_session", return_value=True):
            self.assertEqual(legacy_setup.main(), 0)

        with patch.object(legacy_setup, "create_persistent_session", return_value=False):
            self.assertEqual(
                legacy_setup.main(),
                legacy_setup.SETUP_ALREADY_RUNNING_EXIT_CODE,
            )

    def test_default_process_paths_still_target_the_legacy_entrypoint(self):
        manager = process.SetupSessionProcessManager()
        backend_dir = Path(__file__).resolve().parents[1]

        self.assertEqual(manager._root_dir, backend_dir)
        self.assertEqual(
            manager._script_path,
            backend_dir / "src" / "setup_session.py",
        )
