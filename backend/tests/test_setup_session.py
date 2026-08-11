from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, Mock

from backend.src import setup_session


class SetupSessionUrlTests(TestCase):
    def test_allows_https_facebook_and_messenger_hosts(self):
        valid_urls = (
            "https://facebook.com/messages/t/123",
            "https://www.facebook.com/messages/t/123?ref=bookmark",
            "https://m.facebook.com/messages/t/123",
            "https://messenger.com/t/123",
            "https://www.messenger.com/t/123",
        )

        for target_url in valid_urls:
            with self.subTest(target_url=target_url):
                resolved_url, uses_configured_target = setup_session.resolve_login_url(
                    target_url
                )

                self.assertEqual(resolved_url, target_url)
                self.assertTrue(uses_configured_target)

    def test_falls_back_for_missing_or_unsafe_targets(self):
        unsafe_urls = (
            None,
            "",
            "   ",
            " https://www.facebook.com/messages/t/123",
            "http://www.facebook.com/messages/t/123",
            "ftp://www.messenger.com/t/123",
            "//www.facebook.com/messages/t/123",
            "https:///messages/t/123",
            "https://example.com/messages/t/123",
            "https://notfacebook.com/messages/t/123",
            "https://facebook.com.example.org/messages/t/123",
            "https://www.messenger.com.example.org/t/123",
            "https://user@facebook.com/messages/t/123",
            "https://user:password@messenger.com/t/123",
            "https://facebook.com:invalid/messages/t/123",
            "https://facebook.com/messages/t/123\n",
        )

        for target_url in unsafe_urls:
            with self.subTest(target_url=target_url):
                resolved_url, uses_configured_target = setup_session.resolve_login_url(
                    target_url
                )

                self.assertEqual(resolved_url, setup_session.MESSENGER_INBOX_URL)
                self.assertFalse(uses_configured_target)


class SetupSessionBrowserTests(TestCase):
    def _dependencies(self):
        page = MagicMock()
        page.is_closed.return_value = False
        browser = MagicMock()
        browser.new_page.return_value = page

        chromium = MagicMock()
        chromium.launch_persistent_context.return_value = browser
        playwright = SimpleNamespace(chromium=chromium)

        playwright_context = MagicMock()
        playwright_context.__enter__.return_value = playwright
        playwright_factory = Mock(return_value=playwright_context)

        guard = MagicMock()
        guard.acquire.return_value = True
        guard_factory = Mock(return_value=guard)

        return SimpleNamespace(
            page=page,
            browser=browser,
            chromium=chromium,
            playwright_factory=playwright_factory,
            guard=guard,
            guard_factory=guard_factory,
        )

    def _create_session(self, dependencies, configuration_loader=None):
        if configuration_loader is None:
            configuration_loader = Mock(
                return_value="https://www.facebook.com/messages/t/123"
            )
        return setup_session.create_persistent_session(
            configuration_loader=configuration_loader,
            playwright_factory=dependencies.playwright_factory,
            guard_factory=dependencies.guard_factory,
        )

    def test_opens_the_injected_target_and_releases_guard_after_timeout(self):
        dependencies = self._dependencies()
        configured_target = (
            "https://www.facebook.com/messages/t/private-conversation?secret=value"
        )
        configuration_loader = Mock(return_value=configured_target)
        output = StringIO()

        with redirect_stdout(output):
            completed = self._create_session(dependencies, configuration_loader)

        self.assertTrue(completed)
        configuration_loader.assert_called_once_with()
        dependencies.page.goto.assert_called_once_with(configured_target)
        dependencies.page.wait_for_timeout.assert_called_once_with(
            setup_session.LOGIN_WINDOW_TIMEOUT_MS
        )
        self.assertNotIn(configured_target, output.getvalue())
        self.assertNotIn("private-conversation", output.getvalue())
        dependencies.browser.close.assert_called_once_with()
        dependencies.guard.acquire.assert_called_once_with()
        dependencies.guard.release.assert_called_once_with()

        dependencies.chromium.launch_persistent_context.assert_called_once()
        launch_kwargs = (
            dependencies.chromium.launch_persistent_context.call_args.kwargs
        )
        self.assertEqual(Path(launch_kwargs["user_data_dir"]).name, "user_data")
        self.assertEqual(launch_kwargs["channel"], "chrome")
        self.assertFalse(launch_kwargs["headless"])
        self.assertEqual(launch_kwargs["viewport"], {"width": 1280, "height": 720})

    def test_browser_close_completes_early_and_releases_guard(self):
        dependencies = self._dependencies()
        dependencies.page.wait_for_timeout.side_effect = RuntimeError(
            "mock target closed"
        )
        dependencies.page.is_closed.return_value = True
        dependencies.browser.close.side_effect = RuntimeError(
            "mock context already closed"
        )

        completed = self._create_session(dependencies)

        self.assertTrue(completed)
        dependencies.browser.close.assert_called_once_with()
        dependencies.guard.release.assert_called_once_with()

    def test_duplicate_process_does_not_read_config_or_load_playwright(self):
        dependencies = self._dependencies()
        dependencies.guard.acquire.return_value = False
        configuration_loader = Mock()
        output = StringIO()

        with redirect_stdout(output):
            completed = self._create_session(dependencies, configuration_loader)

        self.assertFalse(completed)
        self.assertIn("already open", output.getvalue())
        configuration_loader.assert_not_called()
        dependencies.playwright_factory.assert_not_called()
        dependencies.guard.release.assert_not_called()

    def test_opens_the_messenger_inbox_when_configuration_is_invalid(self):
        dependencies = self._dependencies()
        configuration_loader = Mock(
            return_value="https://user:password@example.org/private-conversation"
        )
        output = StringIO()

        with redirect_stdout(output):
            self._create_session(dependencies, configuration_loader)

        dependencies.page.goto.assert_called_once_with(
            setup_session.MESSENGER_INBOX_URL
        )
        self.assertIn("opening the Messenger inbox", output.getvalue())
        self.assertNotIn("password", output.getvalue())
        self.assertNotIn("private-conversation", output.getvalue())
        dependencies.guard.release.assert_called_once_with()

    def test_navigation_failure_is_sanitized_and_releases_guard(self):
        dependencies = self._dependencies()
        private_failure = "mock navigation failure for private-conversation"
        dependencies.page.goto.side_effect = RuntimeError(private_failure)
        output = StringIO()

        with redirect_stdout(output):
            with self.assertRaisesRegex(RuntimeError, "Unable to open") as context:
                self._create_session(dependencies)

        self.assertIsNone(context.exception.__cause__)
        self.assertNotIn("private-conversation", str(context.exception))
        self.assertNotIn(private_failure, output.getvalue())
        dependencies.page.wait_for_timeout.assert_not_called()
        dependencies.browser.close.assert_called_once_with()
        dependencies.guard.release.assert_called_once_with()

    def test_wait_failure_is_sanitized_and_releases_guard(self):
        dependencies = self._dependencies()
        private_failure = "mock wait failure for private-conversation"
        dependencies.page.wait_for_timeout.side_effect = RuntimeError(private_failure)

        with self.assertRaisesRegex(RuntimeError, "did not complete") as context:
            self._create_session(dependencies)

        self.assertIsNone(context.exception.__cause__)
        self.assertNotIn("private-conversation", str(context.exception))
        dependencies.browser.close.assert_called_once_with()
        dependencies.guard.release.assert_called_once_with()

    def test_interruption_closes_browser_and_releases_guard(self):
        dependencies = self._dependencies()
        dependencies.page.wait_for_timeout.side_effect = KeyboardInterrupt()

        with self.assertRaises(KeyboardInterrupt):
            self._create_session(dependencies)

        dependencies.browser.close.assert_called_once_with()
        dependencies.guard.release.assert_called_once_with()
