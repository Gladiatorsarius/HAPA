from unittest import TestCase

from src.tiers.tier1_supervisor.state import create_initial_state, record_handoff
from src.tiers.tier2_subparent.subgraphs import (
    Tier2Action,
    Tier2BoundaryError,
    build_tier2_graph,
    validate_tier2_action,
)
from src.core.schemas import Tier


class Tier2SubgraphTests(TestCase):
    def test_graph_coordinates_and_delegates(self) -> None:
        state = create_initial_state(
            title="Build feature",
            description="Implement and test a feature",
            requested_by="test",
        )
        record_handoff(state, destination_tier=Tier.TIER_2, payload={"task": "feature"})

        result = build_tier2_graph().invoke({"supervisor": state})

        self.assertTrue(result["delegated"])
        self.assertEqual(result["actions"], ["plan", "delegate"])

    def test_forbidden_actions_are_rejected(self) -> None:
        with self.assertRaises(Tier2BoundaryError):
            validate_tier2_action(Tier2Action.EXECUTE)
        with self.assertRaises(Tier2BoundaryError):
            validate_tier2_action("browser")

    def test_tier_two_requires_a_tier_two_handoff(self) -> None:
        state = create_initial_state(
            title="Build feature",
            description="Implement and test a feature",
            requested_by="test",
        )

        with self.assertRaises(Tier2BoundaryError):
            build_tier2_graph().invoke({"supervisor": state})
