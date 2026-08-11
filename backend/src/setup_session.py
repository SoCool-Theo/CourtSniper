import os
import time
from urllib.parse import urlsplit


MESSENGER_INBOX_URL = "https://www.facebook.com/messages/"
ALLOWED_TARGET_DOMAINS = ("facebook.com", "messenger.com")


def _load_configured_target_url():
    """Read the booking target from the backend's internal configuration."""
    try:
        from . import config
    except ImportError:
        import config

    return getattr(config, "TARGET_URL", None)


def _create_playwright_context():
    """Load Playwright only when the real login workflow is launched."""
    from playwright.sync_api import sync_playwright

    return sync_playwright()


def _is_allowed_target_url(target_url):
    if not isinstance(target_url, str) or not target_url:
        return False
    if target_url != target_url.strip():
        return False
    if any(ord(character) < 32 or ord(character) == 127 for character in target_url):
        return False

    try:
        parsed = urlsplit(target_url)
        hostname = parsed.hostname
        parsed.port
    except (TypeError, ValueError):
        return False

    if parsed.scheme.lower() != "https" or not parsed.netloc or not hostname:
        return False
    if parsed.username is not None or parsed.password is not None:
        return False

    normalized_hostname = hostname.rstrip(".").lower()
    return any(
        normalized_hostname == domain
        or normalized_hostname.endswith(f".{domain}")
        for domain in ALLOWED_TARGET_DOMAINS
    )


def resolve_login_url(target_url):
    """Return a safe configured destination or the fixed Messenger inbox."""
    if _is_allowed_target_url(target_url):
        return target_url, True
    return MESSENGER_INBOX_URL, False


def create_persistent_session(
    configuration_loader=_load_configured_target_url,
    playwright_factory=_create_playwright_context,
    sleep_fn=time.sleep,
):
    print("Launching Google Chrome to save your Facebook login...")
    login_url, uses_configured_target = resolve_login_url(configuration_loader())
    if uses_configured_target:
        print("Opening the configured Facebook or Messenger conversation.")
    else:
        print(
            "Configured conversation unavailable or invalid; "
            "opening the Messenger inbox."
        )

    with playwright_factory() as p:

        script_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(script_dir)
        user_data_path = os.path.join(backend_dir, "user_data")

        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_path,
            channel="chrome",
            headless=False,
            viewport={"width": 1280, "height": 720}
        )

        try:
            page = browser.new_page()
            try:
                page.goto(login_url)
            except Exception:
                raise RuntimeError("Unable to open the login destination.") from None

            print("\n--- ACTION REQUIRED ---")
            print("1. Log into your Facebook account in the browser window.")
            print("2. Handle any Two-Factor Authentication (2FA) prompts.")
            print(
                "3. Once the configured conversation or Messenger inbox is visible, "
                "return to this terminal and press Ctrl+C, or simply close the browser window."
            )

            # Keep the script open for 5 minutes to give you plenty of time to log in
            sleep_fn(300)
        finally:
            browser.close()


if __name__ == "__main__":
    create_persistent_session()
