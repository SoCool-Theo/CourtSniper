"""Validated scheduler configuration and local next-run calculation."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


MAX_WARMUP_MINUTES = 24 * 60
_CALCULATION_HORIZON_DAYS = 14


class Weekday(str, Enum):
    """Canonical weekday values used by the scheduler API and adapter."""

    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"

    @property
    def index(self) -> int:
        return _WEEKDAYS.index(self)

    @classmethod
    def from_index(cls, index: int) -> "Weekday":
        return _WEEKDAYS[index % len(_WEEKDAYS)]


_WEEKDAYS = tuple(Weekday)


class ScheduleConfig(BaseModel):
    """User-selectable weekly schedule settings."""

    model_config = ConfigDict(extra="forbid")

    weekdays: list[Weekday]
    warmup_minutes: int = Field(
        default=5,
        ge=0,
        le=MAX_WARMUP_MINUTES,
        strict=True,
    )

    @field_validator("weekdays", mode="before")
    @classmethod
    def normalize_weekdays(cls, value: object) -> object:
        if not isinstance(value, list):
            return value

        normalized: list[object] = []
        for weekday in value:
            if isinstance(weekday, Weekday):
                normalized.append(weekday)
            elif isinstance(weekday, str):
                normalized.append(weekday.strip().upper())
            else:
                normalized.append(weekday)
        return normalized

    @field_validator("weekdays")
    @classmethod
    def validate_weekdays(cls, value: list[Weekday]) -> list[Weekday]:
        if not value:
            raise ValueError("Select at least one weekday.")
        if len(set(value)) != len(value):
            raise ValueError("Weekdays must not contain duplicates.")
        return sorted(value, key=lambda weekday: weekday.index)


class BookingTargetTime(BaseModel):
    """The existing booking target time, supplied internally by the backend."""

    model_config = ConfigDict(extra="forbid")

    hour: int = Field(ge=0, le=23, strict=True)
    minute: int = Field(ge=0, le=59, strict=True)
    second: int = Field(ge=0, le=59, strict=True)

    def as_time(self) -> time:
        return time(self.hour, self.minute, self.second)


class SchedulePlan(BaseModel):
    """Calculated values needed to configure and report a weekly schedule."""

    model_config = ConfigDict(extra="forbid")

    weekdays: list[Weekday]
    warmup_minutes: int
    target_time: time
    trigger_weekdays: list[Weekday]
    trigger_time: time
    next_run_time: datetime


def calculate_schedule(
    config: ScheduleConfig,
    target: BookingTargetTime,
    *,
    now: datetime | None = None,
) -> SchedulePlan:
    """Calculate the weekly trigger and earliest future run in local time.

    The selected weekdays belong to the booking target. Subtracting the warm-up
    can therefore move the actual trigger to the preceding calendar day.
    """

    current = now or datetime.now().astimezone()
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("The current time must include local timezone information.")

    target_time = target.as_time()
    trigger_time = _trigger_time(target_time, config.warmup_minutes)
    trigger_weekdays = _trigger_weekdays(
        config.weekdays,
        target_time,
        config.warmup_minutes,
    )
    selected_weekdays = set(config.weekdays)
    next_run_time: datetime | None = None

    for day_offset in range(_CALCULATION_HORIZON_DAYS + 1):
        target_date = current.date() + timedelta(days=day_offset)
        if Weekday.from_index(target_date.weekday()) not in selected_weekdays:
            continue

        target_datetime = datetime.combine(
            target_date,
            target_time,
            tzinfo=current.tzinfo,
        )
        candidate = target_datetime - timedelta(minutes=config.warmup_minutes)
        if candidate <= current:
            continue
        if next_run_time is None or candidate < next_run_time:
            next_run_time = candidate

    if next_run_time is None:
        raise RuntimeError("Unable to calculate the next scheduled run.")

    return SchedulePlan(
        weekdays=config.weekdays,
        warmup_minutes=config.warmup_minutes,
        target_time=target_time,
        trigger_weekdays=trigger_weekdays,
        trigger_time=trigger_time,
        next_run_time=next_run_time,
    )


def _trigger_time(target_time: time, warmup_minutes: int) -> time:
    anchor = datetime(2024, 1, 1).replace(
        hour=target_time.hour,
        minute=target_time.minute,
        second=target_time.second,
    )
    return (anchor - timedelta(minutes=warmup_minutes)).time()


def _trigger_weekdays(
    weekdays: list[Weekday],
    target_time: time,
    warmup_minutes: int,
) -> list[Weekday]:
    monday = datetime(2024, 1, 1).replace(
        hour=target_time.hour,
        minute=target_time.minute,
        second=target_time.second,
    )
    trigger_days = {
        Weekday.from_index(
            (
                monday
                + timedelta(days=weekday.index)
                - timedelta(minutes=warmup_minutes)
            ).weekday()
        )
        for weekday in weekdays
    }
    return sorted(trigger_days, key=lambda weekday: weekday.index)
