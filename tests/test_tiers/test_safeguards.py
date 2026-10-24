from unittest import TestCase

from src.core.schemas import TaskLifecycle
from src.tiers.tier1_supervisor.safeguards import (
    TransitionLimitError,
    begin_iteration,
    begin_retry,
)
from src.tiers.tier1_supervisor.state import create_initial_state


class SafeguardTests(TestCase):
    def test_iterations_are_bounded(self) -> None:
        state = create_initial_state(
            title="Task",
            description="Work",
            requested_by="test",
            max_iterations=1,
        )
        begin_iteration(state)

        with self.assertRaises(TransitionLimitError):
            begin_iteration(state)

        self.assertEqual(state["status"].state, TaskLifecycle.BLOCKED_AT_HUMAN_GATE)
        self.assertTrue(state["approval_required"])

    def test_retries_are_bounded(self) -> None:
        state = create_initial_state(
            title="Task",
            description="Work",
            requested_by="test",
            max_retries=1,
        )
        begin_retry(state)

        with self.assertRaises(TransitionLimitError):
            begin_retry(state)

        self.assertIn("retries exceeded", state["error"])
