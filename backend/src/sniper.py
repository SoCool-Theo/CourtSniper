"""Compatibility entry point for :mod:`backend.src.booking.sniper`."""

try:
    from .booking.sniper import (
        CURRENT_DIR,
        ENV_PATH,
        ROOT_DIR,
        _create_playwright_context,
        _get_configured_status,
        _load_booking_config,
        _load_environment,
        _require_armed_status,
        run_sniper,
    )
except ImportError:
    from booking.sniper import (
        CURRENT_DIR,
        ENV_PATH,
        ROOT_DIR,
        _create_playwright_context,
        _get_configured_status,
        _load_booking_config,
        _load_environment,
        _require_armed_status,
        run_sniper,
    )


def main():
    """Run the stable CourtSniper automation entry point."""
    return run_sniper()


if __name__ == "__main__":
    main()
