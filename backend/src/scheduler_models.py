"""Compatibility exports for :mod:`backend.src.scheduler.models`."""

try:
    from .scheduler.models import (
        MAX_WARMUP_MINUTES,
        BookingTargetTime,
        ScheduleConfig,
        SchedulePlan,
        Weekday,
        _CALCULATION_HORIZON_DAYS,
        _WEEKDAYS,
        _trigger_time,
        _trigger_weekdays,
        calculate_schedule,
    )
except ImportError:
    from scheduler.models import (
        MAX_WARMUP_MINUTES,
        BookingTargetTime,
        ScheduleConfig,
        SchedulePlan,
        Weekday,
        _CALCULATION_HORIZON_DAYS,
        _WEEKDAYS,
        _trigger_time,
        _trigger_weekdays,
        calculate_schedule,
    )
