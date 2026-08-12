"""Compatibility exports for :mod:`backend.src.booking.process`."""

try:
    from .booking.process import (
        ManagedProcess,
        ProcessFactory,
        SniperAlreadyRunningError,
        SniperLaunchError,
        SniperNotRunningError,
        SniperProcessError,
        SniperProcessManager,
        SniperRunStatus,
        SniperScriptNotFoundError,
        SniperStopError,
        StopAction,
        _force_stop_process_group,
        _process_group_launch_options,
        _request_process_group_stop,
    )
except ImportError:
    from booking.process import (
        ManagedProcess,
        ProcessFactory,
        SniperAlreadyRunningError,
        SniperLaunchError,
        SniperNotRunningError,
        SniperProcessError,
        SniperProcessManager,
        SniperRunStatus,
        SniperScriptNotFoundError,
        SniperStopError,
        StopAction,
        _force_stop_process_group,
        _process_group_launch_options,
        _request_process_group_stop,
    )
