"""Retry and iteration limits shared by all orchestration transitions."""

from __future__ import annotations

from datetime import datetime, timezone

from src.core.schemas import TaskLifecycle

from .state import GlobalSupervisorState


class TransitionLimitError(RuntimeError):
    """Raised when a transition would exceed a configured execution limit."""


def begin_iteration(state: GlobalSupervisorState) -> None:
    if state["iteration_count"] >= state["max_iterations"]:
        now = datetime.now(timezone.utc)
        state["status"] = state["status"].model_copy(
            update={
                "state": TaskLifecycle.BLOCKED_AT_HUMAN_GATE,
                "updated_at": now,
                "failure_reason": "Maximum orchestration iterations exceeded",
            }
        )
        state["approval_required"] = True
        state["error"] = "Maximum orchestration iterations exceeded"
        raise TransitionLimitError(state["error"])
    state["iteration_count"] += 1


def begin_retry(state: GlobalSupervisorState) -> None:
    if state["retry_count"] >= state["max_retries"]:
        now = datetime.now(timezone.utc)
        state["status"] = state["status"].model_copy(
            update={
                "state": TaskLifecycle.BLOCKED_AT_HUMAN_GATE,
                "updated_at": now,
                "failure_reason": "Maximum orchestration retries exceeded",
            }
        )
        state["approval_required"] = True
        state["error"] = "Maximum orchestration retries exceeded"
        raise TransitionLimitError(state["error"])
    state["retry_count"] += 1


__all__ = ["TransitionLimitError", "begin_iteration", "begin_retry"]
