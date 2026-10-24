"""Deterministic Tier 2 selection of an allowlisted Tier 3 model."""

from __future__ import annotations

from dataclasses import dataclass

from src.tiers.tier1_supervisor.state import GlobalSupervisorState


class Tier3ModelSelectionError(ValueError):
    """Raised when no valid Tier 3 model can be selected."""


@dataclass(frozen=True)
class Tier3ModelDecision:
    model: str
    complexity_score: int
    reason: str


def select_tier3_model(
    state: GlobalSupervisorState,
    allowed_models: list[str],
) -> Tier3ModelDecision:
    """Select a model name from the configured catalog, never an arbitrary string."""

    if not allowed_models or any(not model.strip() for model in allowed_models):
        raise Tier3ModelSelectionError("Tier 3 model allowlist must contain non-empty names")
    if len(allowed_models) != len(set(allowed_models)):
        raise Tier3ModelSelectionError("Tier 3 model allowlist must not contain duplicates")

    text = f"{state['metadata'].title} {state['metadata'].description}".lower()
    labels = {label.lower() for label in state["metadata"].labels}
    complexity_score = 0
    complexity_score += 2 if len(text) > 240 else 1 if len(text) > 80 else 0
    complexity_score += 1 if any(
        term in text for term in ("architecture", "refactor", "security", "integration")
    ) else 0
    complexity_score += 1 if "complex" in labels else 0
    complexity_score -= 1 if {"simple", "fast-path"} & labels else 0
    index = min(max(complexity_score, 0), len(allowed_models) - 1)
    model = allowed_models[index]
    return Tier3ModelDecision(
        model=model,
        complexity_score=complexity_score,
        reason=f"Selected catalog entry {index} from complexity score {complexity_score}",
    )


def apply_tier3_model(
    state: GlobalSupervisorState,
    allowed_models: list[str],
) -> Tier3ModelDecision:
    decision = select_tier3_model(state, allowed_models)
    state["tier3_model"] = decision.model
    return decision


__all__ = [
    "Tier3ModelDecision",
    "Tier3ModelSelectionError",
    "apply_tier3_model",
    "select_tier3_model",
]
