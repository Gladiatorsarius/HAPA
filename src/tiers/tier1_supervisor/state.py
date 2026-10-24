"""State contract shared by the supervisor graph and tier subgraphs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TypedDict
from uuid import UUID

from src.core.schemas import (
    ExecutionLineage,
    ExecutionSummary,
    TaskHandOff,
    TaskLifecycle,
    TaskMetadata,
    TaskStatus,
    Tier,
)


class GlobalSupervisorState(TypedDict):
    metadata: TaskMetadata
    lineage: ExecutionLineage
    status: TaskStatus
    current_tier: Tier
    current_handoff: TaskHandOff | None
    handoff_history: list[TaskHandOff]
    iteration_count: int
    max_iterations: int
    retry_count: int
    max_retries: int
    approval_required: bool
    approval_granted: bool
    provider_name: str
    strong_model: str
    tier3_model: str | None
    plan: str
    summary: ExecutionSummary | None
    error: str | None


def create_initial_state(
    *,
    title: str,
    description: str,
    requested_by: str,
    provider_name: str = "anthropic",
    strong_model: str = "",
    max_iterations: int = 3,
    max_retries: int = 2,
) -> GlobalSupervisorState:
    if max_iterations < 1:
        raise ValueError("max_iterations must be greater than zero")
    if max_retries < 0:
        raise ValueError("max_retries cannot be negative")
    now = datetime.now(timezone.utc)
    metadata = TaskMetadata(title=title, description=description, created_at=now)
    return {
        "metadata": metadata,
        "lineage": ExecutionLineage(root_task_id=metadata.task_id, requested_by=requested_by),
        "status": TaskStatus(updated_at=now, max_retries=max_retries),
        "current_tier": Tier.TIER_1,
        "current_handoff": None,
        "handoff_history": [],
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "retry_count": 0,
        "max_retries": max_retries,
        "approval_required": False,
        "approval_granted": False,
        "provider_name": provider_name,
        "strong_model": strong_model,
        "tier3_model": None,
        "plan": "",
        "summary": None,
        "error": None,
    }


def record_handoff(
    state: GlobalSupervisorState,
    *,
    destination_tier: Tier,
    payload: dict[str, object] | None = None,
) -> TaskHandOff:
    """Create and record a validated hand-off, advancing lineage exactly once."""

    if destination_tier == Tier.TIER_1:
        raise ValueError("A hand-off destination must be Tier 2 or Tier 3")
    previous = state["current_handoff"]
    origin_tier = state["current_tier"]
    if previous is not None and previous.destination_tier != origin_tier:
        raise ValueError("Current tier does not match the previous hand-off destination")
    lineage = state["lineage"].model_copy(
        update={
            "hop_number": state["lineage"].hop_number + 1,
            "preceding_handoff_id": previous.handoff_id if previous else None,
        }
    )
    handoff = TaskHandOff(
        metadata=state["metadata"],
        lineage=lineage,
        origin_tier=origin_tier,
        destination_tier=destination_tier,
        status=state["status"].model_copy(
            update={"state": TaskLifecycle.RUNNING, "updated_at": datetime.now(timezone.utc)}
        ),
        payload=payload or {},
        created_at=datetime.now(timezone.utc),
    )
    state["lineage"] = lineage
    state["current_tier"] = destination_tier
    state["current_handoff"] = handoff
    state["handoff_history"].append(handoff)
    return handoff


def state_task_id(state: GlobalSupervisorState) -> UUID:
    """Expose the root task identifier without allowing arbitrary state access."""

    return state["lineage"].root_task_id


__all__ = ["GlobalSupervisorState", "create_initial_state", "record_handoff", "state_task_id"]
