"""Manual session-setup route."""

from typing import Callable

from fastapi import HTTPException


def register_session_routes(
    app,
    *,
    get_process_manager: Callable[[], object],
    launch_errors: tuple[type[Exception], ...],
):
    @app.post("/api/run-setup")
    def trigger_setup():
        """Start the fixed login setup process or reuse its existing window."""
        try:
            result = get_process_manager().start()
        except launch_errors as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

        if result.already_running:
            return {
                "message": (
                    "Login browser is already open. "
                    "Continue setup in the existing window."
                ),
                "already_running": True,
            }

        return {
            "message": "Setup session launched! Check your laptop screen.",
            "already_running": False,
        }

    return trigger_setup
