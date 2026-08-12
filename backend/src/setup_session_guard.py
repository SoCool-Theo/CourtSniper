"""Compatibility exports for :mod:`backend.src.session.guard`."""

try:
    from .session.guard import (
        ERROR_ALREADY_EXISTS,
        MUTEX_NAME_PREFIX,
        SetupSessionGuardError,
        WindowsNamedMutex,
        _load_kernel32,
        create_setup_session_guard,
        setup_session_mutex_name,
    )
except ImportError:
    from session.guard import (
        ERROR_ALREADY_EXISTS,
        MUTEX_NAME_PREFIX,
        SetupSessionGuardError,
        WindowsNamedMutex,
        _load_kernel32,
        create_setup_session_guard,
        setup_session_mutex_name,
    )
