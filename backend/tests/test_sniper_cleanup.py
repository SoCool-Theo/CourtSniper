from datetime import datetime
import importlib.util
from pathlib import Path
from types import ModuleType
from unittest import TestCase
from unittest.mock import Mock


SNIPER_PATH = (
    Path(__file__).resolve().parents[1] / "src" / "booking" / "sniper.py"
)


class FakeInputBox:
    def __init__(self, cancel_on_wait=False):
        self.first = self
        self.cancel_on_wait = cancel_on_wait
        self.focused = False
        self.filled_message = None

    def wait_for(self, **kwargs):
        if self.cancel_on_wait:
            raise KeyboardInterrupt()

    def focus(self):
        self.focused = True

    def fill(self, message):
        self.filled_message = message


class FakeKeyboard:
    def __init__(self):
        self.pressed_keys = []

    def press(self, key):
        self.pressed_keys.append(key)


class FakePage:
    def __init__(self, input_box):
        self.input_box = input_box
        self.keyboard = FakeKeyboard()
        self.visited_urls = []

    def goto(self, url):
        self.visited_urls.append(url)

    def get_by_role(self, role):
        return self.input_box


class FakeBrowser:
    def __init__(self, page, events):
        self.page = page
        self.events = events
        self.close_calls = 0

    def new_page(self):
        return self.page

    def close(self):
        self.close_calls += 1
        self.events.append("browser_closed")


class FakeChromium:
    def __init__(self, browser):
        self.browser = browser
        self.launch_options = None

    def launch_persistent_context(self, **options):
        self.launch_options = options
        return self.browser


class FakePlaywrightContext:
    def __init__(self, chromium, events):
        self.playwright = type("FakePlaywright", (), {"chromium": chromium})()
        self.events = events

    def __enter__(self):
        return self.playwright

    def __exit__(self, exc_type, exc_value, traceback):
        self.events.append("playwright_exited")


def load_sniper_module(cancel_on_wait=False, cancel_after_dispatch=False):
    events = []
    input_box = FakeInputBox(cancel_on_wait=cancel_on_wait)
    page = FakePage(input_box)
    browser = FakeBrowser(page, events)
    chromium = FakeChromium(browser)

    now = datetime.now()
    config_module = ModuleType("config")
    config_module.TARGET_URL = "https://example.invalid/messages/test"
    config_module.BOOKING_MESSAGE = "test booking message"
    config_module.TARGET_HOUR = now.hour
    config_module.TARGET_MINUTE = now.minute
    config_module.TARGET_SECOND = 0

    module_name = f"sniper_under_test_{id(browser)}"
    spec = importlib.util.spec_from_file_location(module_name, SNIPER_PATH)
    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    module._load_environment = lambda: None
    module._get_configured_status = lambda: "ARMED"
    module._load_booking_config = lambda: config_module
    module._create_playwright_context = lambda: FakePlaywrightContext(
        chromium,
        events,
    )

    class FixedDateTime:
        @classmethod
        def now(cls):
            return now

    def fake_sleep(seconds):
        if cancel_after_dispatch and seconds == 15:
            raise KeyboardInterrupt()

    module.datetime = FixedDateTime
    module.time.sleep = fake_sleep
    return module, browser, page, input_box, chromium, events


class SniperCleanupTests(TestCase):
    def test_disarmed_run_exits_before_loading_config_or_playwright(self):
        module, browser, page, input_box, chromium, events = load_sniper_module()
        configuration_loader = Mock()
        playwright_factory = Mock()
        module._get_configured_status = lambda: "DISARMED"
        module._load_booking_config = configuration_loader
        module._create_playwright_context = playwright_factory

        with self.assertRaises(SystemExit) as context:
            module.run_sniper()

        self.assertEqual(context.exception.code, 0)
        configuration_loader.assert_not_called()
        playwright_factory.assert_not_called()
        self.assertEqual(browser.close_calls, 0)
        self.assertEqual(page.keyboard.pressed_keys, [])
        self.assertEqual(events, [])

    def test_successful_run_closes_browser_after_dispatch(self):
        module, browser, page, input_box, chromium, events = load_sniper_module()

        module.run_sniper()

        self.assertEqual(page.keyboard.pressed_keys, ["Enter"])
        self.assertTrue(input_box.focused)
        self.assertEqual(input_box.filled_message, "test booking message")
        self.assertEqual(browser.close_calls, 1)
        self.assertLess(events.index("browser_closed"), events.index("playwright_exited"))
        self.assertEqual(
            Path(chromium.launch_options["user_data_dir"]),
            Path(__file__).resolve().parents[1] / "user_data",
        )

    def test_cancellation_after_dispatch_still_closes_browser(self):
        module, browser, page, input_box, chromium, events = load_sniper_module(
            cancel_after_dispatch=True
        )

        with self.assertRaises(SystemExit) as context:
            module.run_sniper()

        self.assertEqual(context.exception.code, 130)
        self.assertEqual(page.keyboard.pressed_keys, ["Enter"])
        self.assertEqual(browser.close_calls, 1)
        self.assertLess(events.index("browser_closed"), events.index("playwright_exited"))
        self.assertEqual(chromium.launch_options["channel"], "chrome")

    def test_cancellation_closes_browser_without_dispatching(self):
        module, browser, page, input_box, chromium, events = load_sniper_module(
            cancel_on_wait=True
        )

        with self.assertRaises(SystemExit) as context:
            module.run_sniper()

        self.assertEqual(context.exception.code, 130)
        self.assertEqual(page.keyboard.pressed_keys, [])
        self.assertFalse(input_box.focused)
        self.assertIsNone(input_box.filled_message)
        self.assertEqual(browser.close_calls, 1)
        self.assertLess(events.index("browser_closed"), events.index("playwright_exited"))
