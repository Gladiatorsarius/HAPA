"""Tier 2 coordination graph with an explicit no-execution boundary."""

from __future__ import annotations

from enum import StrEnum
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.core.schemas import Tier
from src.tiers.tier1_supervisor.state import GlobalSupervisorState


class Tier2Action(StrEnum):
    PLAN = "plan"
    DELEGATE = "delegate"
    EVALUATE = "evaluate"
    EXECUTE = "execute"
    TERMINAL = "terminal"
    BROWSER = "browser"


class Tier2BoundaryError(ValueError):
    """Raised when Tier 2 is asked to perform Tier 3 work."""


_FORBIDDEN_ACTIONS = {Tier2Action.EXECUTE, Tier2Action.TERMINAL, Tier2Action.BROWSER}


def validate_tier2_action(action: Tier2Action | str) -> Tier2Action:
    normalized = Tier2Action(action)
    if normalized in _FORBIDDEN_ACTIONS:
        raise Tier2BoundaryError(
            f"Tier 2 cannot perform {normalized.value} work; delegate it to Tier 3"
        )
    return normalized


class Tier2GraphState(TypedDict, total=False):
    supervisor: GlobalSupervisorState
    actions: list[str]
    delegated: bool
    plan: str
    error: str | None


def _coordinate(state: Tier2GraphState) -> Tier2GraphState:
    supervisor = state["supervisor"]
    if supervisor["current_tier"] != Tier.TIER_2:
        raise Tier2BoundaryError("Tier 2 graph requires a Tier 2 current state")
    return {
        "actions": [Tier2Action.PLAN.value, Tier2Action.DELEGATE.value],
        "delegated": True,
        "plan": supervisor["plan"] or supervisor["metadata"].description,
    }


def build_tier2_graph():
    """Compile the Tier 2 coordinator graph."""

    graph = StateGraph(Tier2GraphState)
    graph.add_node("coordinate", _coordinate)
    graph.add_edge(START, "coordinate")
    graph.add_edge("coordinate", END)
    return graph.compile()


__all__ = [
    "Tier2Action",
    "Tier2BoundaryError",
    "build_tier2_graph",
    "validate_tier2_action",
]
