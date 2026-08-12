"""Sniper process lifecycle routes."""

from typing import Callable

from fastapi import HTTPException, status


def register_sniper_routes(
    app,
    *,
    get_configured_status: Callable[[], str | None],
    get_process_manager: Callable[[], object],
    already_running_error: type[Exception],
    launch_errors: tuple[type[Exception], ...],
    not_running_error: type[Exception],
    stop_error: type[Exception],
):
    @app.post("/api/run-sniper", status_code=status.HTTP_202_ACCEPTED)
    def trigger_sniper():
        """Start the predefined sniper automation when the kill switch is armed."""
        if get_configured_status() != "ARMED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="CourtSniper must be armed before starting a run.",
            )

        try:
            run_status = get_process_manager().start()
        except already_running_error as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            ) from error
        except launch_errors as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(error),
            ) from error

        return {
            "message": "CourtSniper run started.",
            "run": run_status.to_dict(),
        }

    @app.get("/api/run-sniper/status", status_code=200)
    def get_sniper_run_status():
        """Return the current non-sensitive sniper process state."""
        return {"run": get_process_manager().get_status().to_dict()}

    @app.post("/api/run-sniper/stop", status_code=200)
    def stop_sniper():
        """Stop the currently tracked sniper process group."""
        try:
            run_status = get_process_manager().stop()
        except not_running_error as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            ) from error
        except stop_error as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(error),
            ) from error

        return {
            "message": "CourtSniper run stopped.",
            "run": run_status.to_dict(),
        }

    return trigger_sniper, get_sniper_run_status, stop_sniper
