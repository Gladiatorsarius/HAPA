from datetime import datetime, timezone
from unittest import TestCase
from uuid import UUID

from pydantic import ValidationError

from src.core.schemas import (
    ExecutionLineage,
    ProvenanceMetadata,
    ReviewFinding,
    ReviewPersona,
    TaskHandOff,
    TaskLifecycle,
    TaskMetadata,
    TaskStatus,
    TestOutcome,
    TestReport,
    Tier,
)


def make_handoff() -> TaskHandOff:
    now = datetime.now(timezone.utc)
    return TaskHandOff(
        metadata=TaskMetadata(title="Implement schemas", created_at=now),
        lineage=ExecutionLineage(
            root_task_id=UUID("00000000-0000-0000-0000-000000000001"),
            requested_by="tier-1",
        ),
        origin_tier=Tier.TIER_1,
        destination_tier=Tier.TIER_2,
        status=TaskStatus(updated_at=now),
        created_at=now,
    )


class SchemaTests(TestCase):
    def test_task_metadata_carries_provenance(self) -> None:
        now = datetime.now(timezone.utc)
        metadata = TaskMetadata(
            title="Implement schemas",
            created_at=now,
            provenance=ProvenanceMetadata(source="discord", actor="discord:alice"),
        )

        self.assertEqual(metadata.provenance.source, "discord")
        self.assertEqual(metadata.provenance.actor, "discord:alice")

    def test_handoff_round_trips_through_json(self) -> None:
        handoff = make_handoff()

        self.assertEqual(TaskHandOff.model_validate_json(handoff.model_dump_json()), handoff)

    def test_failed_status_requires_failure_reason(self) -> None:
        with self.assertRaisesRegex(ValidationError, "failure_reason is required"):
            TaskStatus(state=TaskLifecycle.FAILED, updated_at=datetime.now(timezone.utc))

    def test_handoff_rejects_invalid_tier_and_extra_fields(self) -> None:
        payload = make_handoff().model_dump(mode="json")
        payload["origin_tier"] = 4
        payload["unexpected"] = True

        with self.assertRaises(ValidationError):
            TaskHandOff.model_validate(payload)

    def test_test_report_preserves_multi_persona_findings(self) -> None:
        report = TestReport(
            suite_name="quality gates",
            outcome=TestOutcome.PASSED,
            total_tests=2,
            passed_tests=2,
            generated_at=datetime.now(timezone.utc),
            review_findings=[
                ReviewFinding(
                    persona=ReviewPersona.SECURITY_AUDITOR,
                    title="No injection issue",
                    description="Inputs are parameterized.",
                    severity=1,
                ),
                ReviewFinding(
                    persona=ReviewPersona.PERFORMANCE_OPTIMIZER,
                    title="No hot path regression",
                    description="No measurable regression found.",
                    severity=1,
                ),
            ],
        )

        self.assertEqual(
            {finding.persona for finding in report.review_findings},
            {ReviewPersona.SECURITY_AUDITOR, ReviewPersona.PERFORMANCE_OPTIMIZER},
        )
