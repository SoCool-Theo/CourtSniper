"""Compatibility entry point for :mod:`backend.src.session.setup`."""

try:
    from .session.setup import (
        ALLOWED_TARGET_DOMAINS,
        LOGIN_WINDOW_TIMEOUT_MS,
        MESSENGER_INBOX_URL,
        SETUP_ALREADY_RUNNING_EXIT_CODE,
        _close_browser_context,
        _create_playwright_context,
        _is_allowed_target_url,
        _load_configured_target_url,
        _wait_for_browser_completion,
        create_persistent_session,
        create_setup_session_guard,
        resolve_login_url,
    )
except ImportError:
    from session.setup import (
        ALLOWED_TARGET_DOMAINS,
        LOGIN_WINDOW_TIMEOUT_MS,
        MESSENGER_INBOX_URL,
        SETUP_ALREADY_RUNNING_EXIT_CODE,
        _close_browser_context,
        _create_playwright_context,
        _is_allowed_target_url,
        _load_configured_target_url,
        _wait_for_browser_completion,
        create_persistent_session,
        create_setup_session_guard,
        resolve_login_url,
    )


def main():
    """Run the stable login-setup entry point and return its exit code."""
    setup_completed = create_persistent_session()
    return 0 if setup_completed else SETUP_ALREADY_RUNNING_EXIT_CODE


if __name__ == "__main__":
    raise SystemExit(main())
