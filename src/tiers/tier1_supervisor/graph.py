"""Compiled Tier 1 supervisor graph."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from langgraph.graph import END, START, StateGraph

from src.core.schemas import TaskLifecycle, Tier
from src.llm.providers import LLMMessage, LLMProvider
from src.tiers.tier2_subparent.subgraphs import build_tier2_graph

from .router import RouteTarget, route_task
from .safeguards import begin_iteration
from .state import GlobalSupervisorState, record_handoff


def _route(state: GlobalSupervisorState) -> GlobalSupervisorState:
    begin_iteration(state)
    route_task(state)
    return state


def _route_key(state: GlobalSupervisorState) -> Literal["approval", "tier2", "tier3"]:
    decision = route_task(state)
    if decision.target == RouteTarget.HUMAN_APPROVAL:
        return "approval"
    return "tier3" if decision.target == RouteTarget.TIER_3 else "tier2"


def _plan_with_provider(state: GlobalSupervisorState, provider: LLMProvider | None) -> str:
    if provider is None:
        return state["metadata"].description
    response = provider.complete(
        [
            LLMMessage("system", "Create a concise implementation plan. Return plain text."),
            LLMMessage("user", state["metadata"].description),
        ]
    )
    return response.content


def _tier2(state: GlobalSupervisorState) -> GlobalSupervisorState:
    record_handoff(state, destination_tier=Tier.TIER_2, payload={"description": state["metadata"].description})
    return state


def _tier3(state: GlobalSupervisorState) -> GlobalSupervisorState:
    record_handoff(state, destination_tier=Tier.TIER_3, payload={"description": state["metadata"].description})
    return state


def _approval(state: GlobalSupervisorState) -> GlobalSupervisorState:
    now = datetime.now(timezone.utc)
    state["status"] = state["status"].model_copy(
        update={"state": TaskLifecycle.BLOCKED_AT_HUMAN_GATE, "updated_at": now}
    )
    return state


def build_supervisor_graph(provider: LLMProvider | None = None):
    """Compile the supervisor graph with an optional configured planner."""

    def plan(state: GlobalSupervisorState) -> GlobalSupervisorState:
        state["plan"] = _plan_with_provider(state, provider)
        return state

    graph = StateGraph(GlobalSupervisorState)
    graph.add_node("route", _route)
    graph.add_node("plan", plan)
    graph.add_node("tier2", _tier2)
    graph.add_node("tier3", _tier3)
    graph.add_node("approval", _approval)
    graph.add_edge(START, "route")
    graph.add_conditional_edges(
        "route",
        _route_key,
        {"approval": "approval", "tier2": "plan", "tier3": "tier3"},
    )
    graph.add_edge("plan", "tier2")
    graph.add_edge("tier2", END)
    graph.add_edge("tier3", END)
    graph.add_edge("approval", END)
    return graph.compile()


__all__ = ["build_supervisor_graph"]
