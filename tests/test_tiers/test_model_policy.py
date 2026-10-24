from unittest import TestCase

from src.tiers.tier1_supervisor.state import create_initial_state
from src.tiers.tier2_subparent.model_policy import (
    Tier3ModelSelectionError,
    select_tier3_model,
)


class ModelPolicyTests(TestCase):
    def test_simple_task_gets_first_allowlisted_model(self) -> None:
        state = create_initial_state(
            title="Format file",
            description="Run formatter",
            requested_by="test",
        )
        state["metadata"] = state["metadata"].model_copy(update={"labels": ["simple"]})

        decision = select_tier3_model(state, ["small", "medium", "large"])

        self.assertEqual(decision.model, "small")

    def test_complex_task_gets_higher_allowlisted_model(self) -> None:
        state = create_initial_state(
            title="Security architecture refactor",
            description="Refactor the integration architecture and security boundaries " * 8,
            requested_by="test",
        )

        decision = select_tier3_model(state, ["small", "medium", "large"])

        self.assertEqual(decision.model, "large")

    def test_empty_catalog_fails_explicitly(self) -> None:
        state = create_initial_state(title="Task", description="Work", requested_by="test")

        with self.assertRaises(Tier3ModelSelectionError):
            select_tier3_model(state, [])
