"""Compatibility exports for :mod:`backend.src.session.process`."""

try:
    from .session.process import (
        SETUP_SCRIPT_FILENAME,
        SETUP_ALREADY_RUNNING_EXIT_CODE,
        STARTUP_PROBE_SECONDS,
        SetupSessionGuardError,
        SetupSessionLaunchError,
        SetupSessionProcessError,
        SetupSessionProcessManager,
        SetupSessionScriptNotFoundError,
        SetupSessionStartResult,
        create_setup_session_guard,
    )
except ImportError:
    from session.process import (
        SETUP_SCRIPT_FILENAME,
        SETUP_ALREADY_RUNNING_EXIT_CODE,
        STARTUP_PROBE_SECONDS,
        SetupSessionGuardError,
        SetupSessionLaunchError,
        SetupSessionProcessError,
        SetupSessionProcessManager,
        SetupSessionScriptNotFoundError,
        SetupSessionStartResult,
        create_setup_session_guard,
    )
