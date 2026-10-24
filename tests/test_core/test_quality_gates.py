from datetime import datetime, timezone
from unittest import TestCase

from pydantic import ValidationError

from src.core.quality_gates import validate_test_report
from src.core.schemas import TestOutcome, TestReport


class QualityGateTests(TestCase):
    def test_test_report_is_json_round_trippable(self) -> None:
        report = TestReport(
            suite_name="quality",
            outcome=TestOutcome.PASSED,
            total_tests=1,
            passed_tests=1,
            generated_at=datetime.now(timezone.utc),
        )

        validated = validate_test_report(report.model_dump(mode="json"))

        self.assertEqual(validated, report)

    def test_test_report_gate_rejects_unstructured_input(self) -> None:
        with self.assertRaises(ValidationError):
            validate_test_report({"suite_name": "quality", "outcome": "PASSED"})
