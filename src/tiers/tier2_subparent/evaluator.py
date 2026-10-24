"""Tier 2 quality gates and bounded self-correction decisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from src.core.quality_gates import validate_test_report
from src.core.schemas import TaskLifecycle, TestOutcome, TestReport
from src.tiers.tier1_supervisor.state import GlobalSupervisorState


class EvaluationDecision(StrEnum):
    SUCCESS = "success"
    SELF_CORRECT = "self_correct"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class EvaluationResult:
    decision: EvaluationDecision
    reason: str
    retry_count: int


def evaluate_report(
    report: TestReport,
    *,
    retry_count: int,
    max_retries: int,
) -> EvaluationResult:
    report = validate_test_report(report)
    if retry_count < 0 or max_retries < 0:
        raise ValueError("retry counts cannot be negative")
    if retry_count > max_retries:
        raise ValueError("retry_count cannot exceed max_retries")
    if report.outcome == TestOutcome.PASSED and not report.failed_tests:
        return EvaluationResult(
            EvaluationDecision.SUCCESS,
            "All automated quality gates passed",
            retry_count,
        )
    if retry_count < max_retries:
        return EvaluationResult(
            EvaluationDecision.SELF_CORRECT,
            "Quality gates failed; a bounded correction iteration is available",
            retry_count + 1,
        )
    return EvaluationResult(
        EvaluationDecision.ESCALATE,
        "Quality gates remain unsuccessful after the retry limit",
        retry_count,
    )


def apply_evaluation(
    state: GlobalSupervisorState,
    result: EvaluationResult,
) -> None:
    """Apply a quality decision to the shared lifecycle state."""

    state["retry_count"] = result.retry_count
    state["status"] = state["status"].model_copy(
        update={
            "state": (
                TaskLifecycle.SUCCESS
                if result.decision == EvaluationDecision.SUCCESS
                else TaskLifecycle.BLOCKED_AT_HUMAN_GATE
                if result.decision == EvaluationDecision.ESCALATE
                else TaskLifecycle.RUNNING
            ),
            "retry_count": result.retry_count,
            "updated_at": state["status"].updated_at,
        }
    )
    if result.decision == EvaluationDecision.ESCALATE:
        state["approval_required"] = True
        state["error"] = result.reason


__all__ = ["EvaluationDecision", "EvaluationResult", "apply_evaluation", "evaluate_report"]
