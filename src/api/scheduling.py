"""Validation and next-run calculation for recurring task schedules."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from croniter import croniter


def next_run_at(
    schedule_type: str,
    *,
    now: datetime | None = None,
    interval_seconds: int | None = None,
    cron_expression: str | None = None,
    timezone_name: str = "UTC",
) -> datetime:
    current = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo(timezone_name))
    if schedule_type == "interval":
        if interval_seconds is None or interval_seconds < 1:
            raise ValueError("interval_seconds must be greater than zero")
        return (current + timedelta(seconds=interval_seconds)).astimezone(timezone.utc)
    if schedule_type == "cron":
        if not cron_expression or not croniter.is_valid(cron_expression):
            raise ValueError("cron_expression is invalid")
        return croniter(cron_expression, current).get_next(datetime).astimezone(timezone.utc)
    raise ValueError("schedule_type must be interval or cron")
