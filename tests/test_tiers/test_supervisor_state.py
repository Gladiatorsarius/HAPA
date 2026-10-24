from unittest import TestCase

from pydantic import ValidationError

from src.core.schemas import Tier
from src.tiers.tier1_supervisor.state import create_initial_state, record_handoff


class SupervisorStateTests(TestCase):
    def test_initial_state_has_root_lineage_and_limits(self) -> None:
        state = create_initial_state(
            title="Add feature",
            description="Implement a feature",
            requested_by="test",
        )

        self.assertEqual(state["lineage"].root_task_id, state["metadata"].task_id)
        self.assertEqual(state["metadata"].provenance.source, "api")
        self.assertEqual(state["metadata"].provenance.actor, "test")
        self.assertEqual(state["current_tier"], Tier.TIER_1)
        self.assertEqual(state["max_iterations"], 3)

    def test_record_handoff_advances_lineage_and_history(self) -> None:
        state = create_initial_state(
            title="Add feature",
            description="Implement a feature",
            requested_by="test",
        )

        handoff = record_handoff(state, destination_tier=Tier.TIER_2, payload={"task": "plan"})

        self.assertEqual(handoff.origin_tier, Tier.TIER_1)
        self.assertEqual(state["current_tier"], Tier.TIER_2)
        self.assertEqual(state["lineage"].hop_number, 1)
        self.assertEqual(len(state["handoff_history"]), 1)

    def test_handoff_rejects_tier_one_destination(self) -> None:
        state = create_initial_state(
            title="Add feature",
            description="Implement a feature",
            requested_by="test",
        )

        with self.assertRaises(ValueError):
            record_handoff(state, destination_tier=Tier.TIER_1)

    def test_invalid_task_metadata_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            create_initial_state(title="", description="x", requested_by="test")
