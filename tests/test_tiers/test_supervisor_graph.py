from unittest import TestCase

from src.core.schemas import Tier
from src.llm.providers import LLMResponse, ProviderName
from src.tiers.tier1_supervisor.graph import build_supervisor_graph
from src.tiers.tier1_supervisor.state import create_initial_state


class FakeProvider:
    name = ProviderName.ANTHROPIC
    model = "test-model"

    def complete(self, messages, *, temperature=0.0):
        return LLMResponse(
            provider=self.name,
            model=self.model,
            content="plan from provider",
            raw={},
        )


class SupervisorGraphTests(TestCase):
    def test_normal_task_is_planned_and_handed_to_tier_two(self) -> None:
        state = create_initial_state(
            title="Implement feature",
            description="Build a feature",
            requested_by="test",
        )

        result = build_supervisor_graph(FakeProvider()).invoke(state)

        self.assertEqual(result["plan"], "plan from provider")
        self.assertEqual(result["current_tier"], Tier.TIER_2)
        self.assertEqual(len(result["handoff_history"]), 1)
        self.assertEqual(result["tier3_model"], "claude-3-5-haiku-latest")
        self.assertEqual(result["handoff_history"][0].payload["tier3_model"], result["tier3_model"])

    def test_simple_task_uses_tier_three_fast_path(self) -> None:
        state = create_initial_state(
            title="Format file",
            description="Run formatter",
            requested_by="test",
        )
        state["metadata"] = state["metadata"].model_copy(update={"labels": ["simple"]})

        result = build_supervisor_graph().invoke(state)

        self.assertEqual(result["current_tier"], Tier.TIER_3)
        self.assertIn(result["handoff_history"][0].payload["model"], {
            "claude-3-5-haiku-latest",
            "gpt-4o-mini",
            "gemini-2.0-flash",
        })

    def test_production_task_stops_at_approval_gate(self) -> None:
        state = create_initial_state(
            title="Deploy service",
            description="Deploy to production",
            requested_by="test",
        )

        result = build_supervisor_graph().invoke(state)

        self.assertTrue(result["approval_required"])
        self.assertEqual(result["status"].state.value, "BLOCKED_AT_HUMAN_GATE")
