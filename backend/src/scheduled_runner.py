"""Compatibility entry point for :mod:`backend.src.scheduler.runner`."""

try:
    from .scheduler.runner import (
        ACTIVE_RUN_STATES,
        API_BASE_URL,
        API_HOST,
        API_PORT,
        API_SERVICE_ID,
        EXIT_AUTOMATION_FAILED,
        EXIT_AUTOMATION_STOPPED,
        EXIT_RUNNER_ERROR,
        EXIT_RUN_REJECTED,
        EXIT_SUCCESS,
        KNOWN_RUN_STATES,
        TERMINAL_RUN_STATES,
        ApiClient,
        ApiHttpError,
        ApiUnavailableError,
        CourtSniperApiClient,
        ManagedApiProcess,
        ProcessFactory,
        ScheduledRunner,
        ScheduledRunnerError,
        UnexpectedApiError,
        _api_launch_options,
        main,
    )
except ImportError:
    from scheduler.runner import (
        ACTIVE_RUN_STATES,
        API_BASE_URL,
        API_HOST,
        API_PORT,
        API_SERVICE_ID,
        EXIT_AUTOMATION_FAILED,
        EXIT_AUTOMATION_STOPPED,
        EXIT_RUNNER_ERROR,
        EXIT_RUN_REJECTED,
        EXIT_SUCCESS,
        KNOWN_RUN_STATES,
        TERMINAL_RUN_STATES,
        ApiClient,
        ApiHttpError,
        ApiUnavailableError,
        CourtSniperApiClient,
        ManagedApiProcess,
        ProcessFactory,
        ScheduledRunner,
        ScheduledRunnerError,
        UnexpectedApiError,
        _api_launch_options,
        main,
    )


if __name__ == "__main__":
    raise SystemExit(main())
