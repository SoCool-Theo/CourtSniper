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
    def _browser_dependencies(self):
        page = MagicMock()
        browser = MagicMock()
        browser.new_page.return_value = page

        chromium = MagicMock()
        chromium.launch_persistent_context.return_value = browser
        playwright = SimpleNamespace(chromium=chromium)

        playwright_context = MagicMock()
        playwright_context.__enter__.return_value = playwright
        playwright_factory = Mock(return_value=playwright_context)
        sleep_fn = Mock()
        return page, browser, chromium, playwright_factory, sleep_fn

    def test_opens_the_injected_configured_target_without_logging_it(self):
        configured_target = (
            "https://www.facebook.com/messages/t/private-conversation?secret=value"
        )
        configuration_loader = Mock(return_value=configured_target)
        page, browser, chromium, playwright_factory, sleep_fn = (
            self._browser_dependencies()
        )
        output = StringIO()

        with redirect_stdout(output):
            setup_session.create_persistent_session(
                configuration_loader=configuration_loader,
                playwright_factory=playwright_factory,
                sleep_fn=sleep_fn,
            )

        configuration_loader.assert_called_once_with()
        page.goto.assert_called_once_with(configured_target)
        self.assertNotIn(configured_target, output.getvalue())
        self.assertNotIn("private-conversation", output.getvalue())
        sleep_fn.assert_called_once_with(300)
        browser.close.assert_called_once_with()

        chromium.launch_persistent_context.assert_called_once()
        launch_kwargs = chromium.launch_persistent_context.call_args.kwargs
        self.assertEqual(Path(launch_kwargs["user_data_dir"]).name, "user_data")
        self.assertEqual(launch_kwargs["channel"], "chrome")
        self.assertFalse(launch_kwargs["headless"])
        self.assertEqual(launch_kwargs["viewport"], {"width": 1280, "height": 720})

    def test_opens_the_messenger_inbox_when_configuration_is_invalid(self):
        configuration_loader = Mock(
            return_value="https://user:password@example.org/private-conversation"
        )
        page, browser, _, playwright_factory, sleep_fn = self._browser_dependencies()
        output = StringIO()

        with redirect_stdout(output):
            setup_session.create_persistent_session(
                configuration_loader=configuration_loader,
                playwright_factory=playwright_factory,
                sleep_fn=sleep_fn,
            )

        page.goto.assert_called_once_with(setup_session.MESSENGER_INBOX_URL)
        self.assertIn("opening the Messenger inbox", output.getvalue())
        self.assertNotIn("password", output.getvalue())
        self.assertNotIn("private-conversation", output.getvalue())
        browser.close.assert_called_once_with()

    def test_closes_the_persistent_context_when_navigation_fails(self):
        page, browser, _, playwright_factory, sleep_fn = self._browser_dependencies()
        private_failure = "mock navigation failure for private-conversation"
        page.goto.side_effect = RuntimeError(private_failure)
        output = StringIO()

        with redirect_stdout(output):
            with self.assertRaisesRegex(RuntimeError, "Unable to open") as context:
                setup_session.create_persistent_session(
                    configuration_loader=Mock(
                        return_value="https://www.messenger.com/t/private-conversation"
                    ),
                    playwright_factory=playwright_factory,
                    sleep_fn=sleep_fn,
                )

        self.assertIsNone(context.exception.__cause__)
        self.assertNotIn("private-conversation", str(context.exception))
        self.assertNotIn(private_failure, output.getvalue())
        sleep_fn.assert_not_called()
        browser.close.assert_called_once_with()
