"""Windows scheduler routes and response mapping."""

from typing import Callable


def register_scheduler_routes(
    app,
    *,
    schedule_config_type,
    get_scheduler_adapter: Callable[[], object],
    get_booking_target_time: Callable[[], object],
    scheduler_payload: Callable[[object], dict[str, object]],
    scheduler_http_exception: Callable[[Exception], Exception],
    scheduler_error: type[Exception],
    booking_target_error: type[Exception],
    not_configured_error: type[Exception],
):
    @app.get("/api/scheduler", status_code=200)
    def get_scheduler_status():
        """Return a sanitized snapshot of the fixed Windows scheduled task."""
        try:
            snapshot = get_scheduler_adapter().get_status()
        except scheduler_error as error:
            raise scheduler_http_exception(error) from error
        return scheduler_payload(snapshot)

    @app.post("/api/scheduler/config", status_code=200)
    def configure_scheduler(config: schedule_config_type):
        """Install or update the fixed task using the existing booking target."""
        try:
            target = get_booking_target_time()
            snapshot = get_scheduler_adapter().configure(config, target)
        except (scheduler_error, booking_target_error) as error:
            raise scheduler_http_exception(error) from error
        return {
            "message": "CourtSniper schedule configured.",
            "scheduler": scheduler_payload(snapshot),
        }

    @app.post("/api/scheduler/enable", status_code=200)
    def enable_scheduler():
        """Enable future runs after confirming the target time is current."""
        try:
            adapter = get_scheduler_adapter()
            current = adapter.get_status()
            if current.configuration is not None:
                target = get_booking_target_time()
                if current.configuration.target_time != target.as_time():
                    raise not_configured_error(
                        "Save the scheduler configuration for the current booking target before enabling it."
                    )
            snapshot = adapter.enable()
        except (scheduler_error, booking_target_error) as error:
            raise scheduler_http_exception(error) from error
        return {
            "message": "CourtSniper schedule enabled.",
            "scheduler": scheduler_payload(snapshot),
        }

    @app.post("/api/scheduler/disable", status_code=200)
    def disable_scheduler():
        """Disable future triggers without stopping an active sniper run."""
        try:
            snapshot = get_scheduler_adapter().disable()
        except scheduler_error as error:
            raise scheduler_http_exception(error) from error
        return {
            "message": "CourtSniper schedule disabled.",
            "scheduler": scheduler_payload(snapshot),
        }

    return (
        get_scheduler_status,
        configure_scheduler,
        enable_scheduler,
        disable_scheduler,
    )
