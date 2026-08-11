from datetime import datetime, timedelta, timezone
from unittest import TestCase

from pydantic import ValidationError

from backend.src.scheduler_models import (
    BookingTargetTime,
    ScheduleConfig,
    Weekday,
    calculate_schedule,
)


BANGKOK = timezone(timedelta(hours=7))


class ScheduleConfigTests(TestCase):
    def test_warmup_defaults_to_five_minutes(self):
        config = ScheduleConfig(weekdays=["MONDAY"])

        self.assertEqual(config.warmup_minutes, 5)

    def test_weekdays_are_normalized_and_sorted(self):
        config = ScheduleConfig(weekdays=[" friday ", "monday", "WEDNESDAY"])

        self.assertEqual(
            config.weekdays,
            [Weekday.MONDAY, Weekday.WEDNESDAY, Weekday.FRIDAY],
        )

    def test_at_least_one_weekday_is_required(self):
        with self.assertRaisesRegex(ValidationError, "Select at least one weekday"):
            ScheduleConfig(weekdays=[])

    def test_duplicate_weekdays_are_rejected_after_normalization(self):
        with self.assertRaisesRegex(ValidationError, "must not contain duplicates"):
            ScheduleConfig(weekdays=["monday", "MONDAY"])

    def test_unknown_weekday_is_rejected(self):
        with self.assertRaises(ValidationError):
            ScheduleConfig(weekdays=["FUNDAY"])

    def test_warmup_must_be_a_strict_integer(self):
        with self.assertRaises(ValidationError):
            ScheduleConfig(weekdays=["MONDAY"], warmup_minutes="5")

    def test_warmup_accepts_zero_and_one_day(self):
        zero = ScheduleConfig(weekdays=["MONDAY"], warmup_minutes=0)
        one_day = ScheduleConfig(weekdays=["MONDAY"], warmup_minutes=1440)

        self.assertEqual(zero.warmup_minutes, 0)
        self.assertEqual(one_day.warmup_minutes, 1440)

    def test_warmup_outside_v1_range_is_rejected(self):
        for value in (-1, 1441):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                ScheduleConfig(weekdays=["MONDAY"], warmup_minutes=value)

    def test_extra_configuration_fields_are_rejected(self):
        with self.assertRaises(ValidationError):
            ScheduleConfig(
                weekdays=["MONDAY"],
                task_name="NotCourtSniper",
            )


class BookingTargetTimeTests(TestCase):
    def test_target_time_preserves_seconds(self):
        target = BookingTargetTime(hour=8, minute=15, second=42)

        self.assertEqual(target.as_time().isoformat(), "08:15:42")

    def test_target_time_fields_are_strict_and_bounded(self):
        invalid_values = (
            {"hour": 24, "minute": 0, "second": 0},
            {"hour": 8, "minute": 60, "second": 0},
            {"hour": 8, "minute": 0, "second": 60},
            {"hour": "8", "minute": 0, "second": 0},
        )

        for values in invalid_values:
            with self.subTest(values=values), self.assertRaises(ValidationError):
                BookingTargetTime(**values)


class ScheduleCalculationTests(TestCase):
    def test_same_day_trigger_uses_target_minus_warmup(self):
        plan = calculate_schedule(
            ScheduleConfig(weekdays=["MONDAY"]),
            BookingTargetTime(hour=8, minute=0, second=30),
            now=datetime(2026, 8, 10, 7, 0, tzinfo=BANGKOK),
        )

        self.assertEqual(plan.trigger_time.isoformat(), "07:55:30")
        self.assertEqual(plan.trigger_weekdays, [Weekday.MONDAY])
        self.assertEqual(
            plan.next_run_time,
            datetime(2026, 8, 10, 7, 55, 30, tzinfo=BANGKOK),
        )

    def test_midnight_crossing_moves_trigger_to_previous_weekday(self):
        plan = calculate_schedule(
            ScheduleConfig(weekdays=["MONDAY"], warmup_minutes=5),
            BookingTargetTime(hour=0, minute=2, second=0),
            now=datetime(2026, 8, 9, 20, 0, tzinfo=BANGKOK),
        )

        self.assertEqual(plan.trigger_time.isoformat(), "23:57:00")
        self.assertEqual(plan.trigger_weekdays, [Weekday.SUNDAY])
        self.assertEqual(
            plan.next_run_time,
            datetime(2026, 8, 9, 23, 57, tzinfo=BANGKOK),
        )

    def test_elapsed_cross_midnight_trigger_advances_to_next_week(self):
        plan = calculate_schedule(
            ScheduleConfig(weekdays=["MONDAY"], warmup_minutes=5),
            BookingTargetTime(hour=0, minute=2, second=0),
            now=datetime(2026, 8, 9, 23, 58, tzinfo=BANGKOK),
        )

        self.assertEqual(
            plan.next_run_time,
            datetime(2026, 8, 16, 23, 57, tzinfo=BANGKOK),
        )

    def test_exact_current_time_is_not_returned_again(self):
        plan = calculate_schedule(
            ScheduleConfig(weekdays=["MONDAY"], warmup_minutes=5),
            BookingTargetTime(hour=8, minute=0, second=0),
            now=datetime(2026, 8, 10, 7, 55, tzinfo=BANGKOK),
        )

        self.assertEqual(
            plan.next_run_time,
            datetime(2026, 8, 17, 7, 55, tzinfo=BANGKOK),
        )

    def test_earliest_selected_weekday_is_returned(self):
        plan = calculate_schedule(
            ScheduleConfig(weekdays=["FRIDAY", "WEDNESDAY"]),
            BookingTargetTime(hour=9, minute=0, second=0),
            now=datetime(2026, 8, 11, 12, 0, tzinfo=BANGKOK),
        )

        self.assertEqual(
            plan.next_run_time,
            datetime(2026, 8, 12, 8, 55, tzinfo=BANGKOK),
        )

    def test_one_day_warmup_shifts_each_trigger_weekday(self):
        plan = calculate_schedule(
            ScheduleConfig(
                weekdays=["MONDAY", "SUNDAY"],
                warmup_minutes=1440,
            ),
            BookingTargetTime(hour=8, minute=0, second=0),
            now=datetime(2026, 8, 10, 9, 0, tzinfo=BANGKOK),
        )

        self.assertEqual(
            plan.trigger_weekdays,
            [Weekday.SATURDAY, Weekday.SUNDAY],
        )
        self.assertEqual(plan.trigger_time.isoformat(), "08:00:00")
        self.assertEqual(
            plan.next_run_time,
            datetime(2026, 8, 15, 8, 0, tzinfo=BANGKOK),
        )

    def test_naive_current_time_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            calculate_schedule(
                ScheduleConfig(weekdays=["MONDAY"]),
                BookingTargetTime(hour=8, minute=0, second=0),
                now=datetime(2026, 8, 10, 7, 0),
            )
