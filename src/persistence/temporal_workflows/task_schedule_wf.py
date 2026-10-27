"""Temporal workflow contract for durable recurring task firings."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

from temporalio import activity, workflow


SCHEDULE_ACTIVITY_TIMEOUT: Final[timedelta] = timedelta(minutes=5)


@activity.defn
async def fire_scheduled_task(payload: dict[str, object]) -> dict[str, object]:
    """Activity boundary used by the API worker to create one task execution."""

    return payload


@workflow.defn
class RecurringTaskWorkflow:
    """Fire a recurring task at a fixed interval until cancelled."""

    @workflow.run
    async def run(self, payload: dict[str, object], interval_seconds: int) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero")
        while True:
            await workflow.execute_activity(
                fire_scheduled_task,
                args=[payload],
                start_to_close_timeout=SCHEDULE_ACTIVITY_TIMEOUT,
            )
            await workflow.sleep(timedelta(seconds=interval_seconds))


__all__ = [
    "RecurringTaskWorkflow",
    "SCHEDULE_ACTIVITY_TIMEOUT",
    "fire_scheduled_task",
]
