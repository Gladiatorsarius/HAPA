from unittest import TestCase

from src.core.schemas import Tier
from src.tiers.tier1_supervisor.graph import build_supervisor_graph
from src.tiers.tier1_supervisor.state import create_initial_state, record_handoff


class Phase3IntegrationTests(TestCase):
    def test_handoff_lineage_is_preserved_across_tier_routing(self) -> None:
        state = create_initial_state(
            title="Implement feature",
            description="Implement and test a feature",
            requested_by="integration-test",
        )

        result = build_supervisor_graph().invoke(state)

        self.assertEqual(result["current_tier"], Tier.TIER_2)
        self.assertEqual(result["lineage"].hop_number, 1)
        self.assertEqual(result["handoff_history"][0].lineage.root_task_id, state["lineage"].root_task_id)

    def test_invalid_tier_one_destination_is_rejected_before_graph_work(self) -> None:
        state = create_initial_state(
            title="Implement feature",
            description="Implement and test a feature",
            requested_by="integration-test",
        )

        with self.assertRaises(ValueError):
            record_handoff(state, destination_tier=Tier.TIER_1)

    def test_approval_escalation_does_not_create_a_handoff(self) -> None:
        state = create_initial_state(
            title="Delete production data",
            description="Delete production records",
            requested_by="integration-test",
        )

        result = build_supervisor_graph().invoke(state)

        self.assertTrue(result["approval_required"])
        self.assertEqual(result["handoff_history"], [])
