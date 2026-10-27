from datetime import datetime, timezone
from tempfile import TemporaryDirectory
from unittest import TestCase

from pydantic import ValidationError

from src.api.models import ScheduleRequest, ScheduleResponse
from src.api.scheduling import next_run_at
from src.api.store import ApiStore


class SchedulingTests(TestCase):
    def test_interval_schedule_requires_interval_and_calculates_next_run(self) -> None:
        request = ScheduleRequest(
            title="Daily scan",
            requested_by="website",
            schedule_type="interval",
            interval_seconds=86400,
        )
        current = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(
            next_run_at("interval", now=current, interval_seconds=request.interval_seconds),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
        )

    def test_cron_schedule_requires_cron_expression(self) -> None:
        with self.assertRaises(ValidationError):
            ScheduleRequest(
                title="Hourly scan",
                requested_by="website",
                schedule_type="cron",
            )

    def test_schedule_store_round_trips_lifecycle(self) -> None:
        with TemporaryDirectory() as directory:
            store = ApiStore(f"sqlite:///{directory}/hapa.db")
            next_run = datetime(2026, 1, 2, tzinfo=timezone.utc)
            schedule = store.create_schedule(
                {
                    "title": "Daily scan",
                    "description": "",
                    "requested_by": "website",
                    "schedule_type": "interval",
                    "interval_seconds": 86400,
                    "cron_expression": None,
                    "timezone": "UTC",
                    "callback_url": None,
                },
                next_run,
            )
            self.assertEqual(ScheduleResponse.model_validate(schedule).state, "ACTIVE")
            paused = store.update_schedule(
                schedule["schedule_id"], state="PAUSED"
            )
            self.assertEqual(paused["state"], "PAUSED")
