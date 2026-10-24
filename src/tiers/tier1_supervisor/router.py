"""Deterministic Tier 1 routing and approval classification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from src.core.schemas import Tier

from .state import GlobalSupervisorState


class RouteTarget(StrEnum):
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"
    HUMAN_APPROVAL = "human_approval"


@dataclass(frozen=True)
class RouteDecision:
    target: RouteTarget
    destination_tier: Tier | None
    reason: str
    requires_approval: bool = False


_APPROVAL_TERMS = (
    "deploy",
    "publish",
    "release",
    "delete",
    "destroy",
    "payment",
    "production",
    "send email",
)


def route_task(state: GlobalSupervisorState) -> RouteDecision:
    """Choose the next tier without executing task content."""

    text = f"{state['metadata'].title} {state['metadata'].description}".lower()
    labels = {label.lower() for label in state["metadata"].labels}
    if any(term in text for term in _APPROVAL_TERMS) or "requires-approval" in labels:
        state["approval_required"] = True
        return RouteDecision(
            RouteTarget.HUMAN_APPROVAL,
            None,
            "Task contains an irreversible or production-affecting action",
            requires_approval=True,
        )
    if "fast-path" in labels or "simple" in labels:
        return RouteDecision(
            RouteTarget.TIER_3,
            Tier.TIER_3,
            "Task explicitly opted into the Tier 1 fast path",
        )
    return RouteDecision(
        RouteTarget.TIER_2,
        Tier.TIER_2,
        "Task requires planning and quality coordination",
    )


__all__ = ["RouteDecision", "RouteTarget", "route_task"]
