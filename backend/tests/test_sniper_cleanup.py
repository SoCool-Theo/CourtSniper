from datetime import datetime
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from unittest import TestCase
from unittest.mock import patch


SNIPER_PATH = Path(__file__).resolve().parents[1] / "src" / "sniper.py"


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

    sync_api_module = ModuleType("playwright.sync_api")
    sync_api_module.sync_playwright = lambda: FakePlaywrightContext(chromium, events)
    playwright_module = ModuleType("playwright")

    now = datetime.now()
    config_module = ModuleType("config")
    config_module.TARGET_URL = "https://example.invalid/messages/test"
    config_module.BOOKING_MESSAGE = "test booking message"
    config_module.TARGET_HOUR = now.hour
    config_module.TARGET_MINUTE = now.minute
    config_module.TARGET_SECOND = 0

    dotenv_module = ModuleType("dotenv")
    dotenv_module.load_dotenv = lambda **kwargs: None

    module_name = f"sniper_under_test_{id(browser)}"
    spec = importlib.util.spec_from_file_location(module_name, SNIPER_PATH)
    module = importlib.util.module_from_spec(spec)

    fake_modules = {
        "playwright": playwright_module,
        "playwright.sync_api": sync_api_module,
        "config": config_module,
        "dotenv": dotenv_module,
    }
    with patch.dict(sys.modules, fake_modules), patch("os.getenv", return_value="ARMED"):
        spec.loader.exec_module(module)

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
    def test_successful_run_closes_browser_after_dispatch(self):
        module, browser, page, input_box, chromium, events = load_sniper_module()

        module.run_sniper()

        self.assertEqual(page.keyboard.pressed_keys, ["Enter"])
        self.assertTrue(input_box.focused)
        self.assertEqual(input_box.filled_message, "test booking message")
        self.assertEqual(browser.close_calls, 1)
        self.assertLess(events.index("browser_closed"), events.index("playwright_exited"))

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
