from unittest import TestCase

from src.core.schemas import Tier
from src.tiers.tier1_supervisor.router import RouteTarget, route_task
from src.tiers.tier1_supervisor.state import create_initial_state


class RouterTests(TestCase):
    def test_simple_label_uses_tier_three_fast_path(self) -> None:
        state = create_initial_state(
            title="Format file",
            description="Apply the formatter",
            requested_by="test",
        )
        state["metadata"] = state["metadata"].model_copy(update={"labels": ["simple"]})

        decision = route_task(state)

        self.assertEqual(decision.target, RouteTarget.TIER_3)
        self.assertEqual(decision.destination_tier, Tier.TIER_3)
        self.assertFalse(decision.requires_approval)

    def test_normal_task_routes_to_tier_two(self) -> None:
        state = create_initial_state(
            title="Implement feature",
            description="Design and test a feature",
            requested_by="test",
        )

        self.assertEqual(route_task(state).target, RouteTarget.TIER_2)

    def test_irreversible_task_requires_human_approval(self) -> None:
        state = create_initial_state(
            title="Deploy service",
            description="Deploy the service to production",
            requested_by="test",
        )

        decision = route_task(state)

        self.assertEqual(decision.target, RouteTarget.HUMAN_APPROVAL)
        self.assertTrue(decision.requires_approval)
        self.assertTrue(state["approval_required"])
