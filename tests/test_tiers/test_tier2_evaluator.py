from datetime import datetime, timezone
from unittest import TestCase

from src.core.schemas import TaskLifecycle, TestOutcome, TestReport
from src.tiers.tier1_supervisor.state import create_initial_state
from src.tiers.tier2_subparent.evaluator import (
    EvaluationDecision,
    apply_evaluation,
    evaluate_report,
)


def report(outcome: TestOutcome, failed: int = 0) -> TestReport:
    return TestReport(
        suite_name="quality",
        outcome=outcome,
        total_tests=1,
        passed_tests=1 - failed,
        failed_tests=failed,
        generated_at=datetime.now(timezone.utc),
    )


class Tier2EvaluatorTests(TestCase):
    def test_passed_report_succeeds(self) -> None:
        result = evaluate_report(report(TestOutcome.PASSED), retry_count=0, max_retries=2)

        self.assertEqual(result.decision, EvaluationDecision.SUCCESS)

    def test_failed_report_self_corrects_while_retries_remain(self) -> None:
        result = evaluate_report(report(TestOutcome.FAILED, 1), retry_count=0, max_retries=2)

        self.assertEqual(result.decision, EvaluationDecision.SELF_CORRECT)
        self.assertEqual(result.retry_count, 1)

    def test_failed_report_escalates_at_retry_limit(self) -> None:
        result = evaluate_report(report(TestOutcome.FAILED, 1), retry_count=2, max_retries=2)
        state = create_initial_state(title="Task", description="Work", requested_by="test")

        apply_evaluation(state, result)

        self.assertEqual(result.decision, EvaluationDecision.ESCALATE)
        self.assertEqual(state["status"].state, TaskLifecycle.BLOCKED_AT_HUMAN_GATE)
        self.assertTrue(state["approval_required"])
