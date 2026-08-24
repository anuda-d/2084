import unittest

from simulation.day_runtime import (
    MAX_MODEL_DECISION_CALLS_PER_DAY,
    AcceleratedDayRuntime,
    ModelDecisionCallLimitError,
)
from simulation.decision_eligibility import DecisionTrigger, DecisionTriggerKind
from simulation.time import SimulatedTime


class AcceleratedDayDecisionBudgetTests(unittest.TestCase):
    def _runtime(self, calls, *, model_backed_actor_ids=("mara-vale",)):
        return AcceleratedDayRuntime(
            start=SimulatedTime.from_day_time(
                day_index=8,
                hour=6,
                minute=0,
            ),
            handlers={},
            decision_handler=lambda decision, context: calls.append(decision),
            model_backed_actor_ids=model_backed_actor_ids,
        )

    def _schedule_calls(self, runtime, *, actor_id, count):
        for offset in range(count):
            runtime.request_decision(
                actor_id=actor_id,
                due_time=runtime.start.plus_minutes(offset),
                trigger=DecisionTrigger(
                    DecisionTriggerKind.SCHEDULED_WAKE,
                    f"wake-{offset:04d}",
                ),
            )

    def test_exactly_128_model_decision_calls_can_complete_the_day(self):
        calls = []
        runtime = self._runtime(calls)
        self._schedule_calls(
            runtime,
            actor_id="mara-vale",
            count=MAX_MODEL_DECISION_CALLS_PER_DAY,
        )

        summary = runtime.run()

        self.assertTrue(summary.reached_end_boundary)
        self.assertEqual(len(calls), MAX_MODEL_DECISION_CALLS_PER_DAY)
        self.assertEqual(
            summary.to_data()["decision_counts_by_actor"],
            {"mara-vale": MAX_MODEL_DECISION_CALLS_PER_DAY},
        )
        self.assertEqual(summary.decision_counts[0].model_bounded, True)

    def test_129th_model_decision_is_terminal_before_handler_call(self):
        calls = []
        runtime = self._runtime(calls)
        self._schedule_calls(
            runtime,
            actor_id="mara-vale",
            count=MAX_MODEL_DECISION_CALLS_PER_DAY + 1,
        )

        with self.assertRaises(ModelDecisionCallLimitError):
            runtime.run()

        self.assertEqual(len(calls), MAX_MODEL_DECISION_CALLS_PER_DAY)
        self.assertFalse(runtime.is_complete)
        self.assertEqual(
            runtime.runtime_failure.failure_type,
            "ModelDecisionCallLimitError",
        )
        self.assertEqual(
            runtime.summary().to_data()["decision_counts_by_actor"],
            {"mara-vale": MAX_MODEL_DECISION_CALLS_PER_DAY},
        )
        self.assertTrue(runtime.is_registration_closed)

    def test_unmarked_supporting_actor_is_not_given_the_focal_model_limit(self):
        calls = []
        runtime = self._runtime(calls)
        self._schedule_calls(
            runtime,
            actor_id="ilan-reed",
            count=MAX_MODEL_DECISION_CALLS_PER_DAY + 1,
        )

        summary = runtime.run()

        self.assertTrue(runtime.is_complete)
        self.assertEqual(len(calls), MAX_MODEL_DECISION_CALLS_PER_DAY + 1)
        self.assertEqual(
            summary.to_data()["decision_counts_by_actor"],
            {
                "ilan-reed": MAX_MODEL_DECISION_CALLS_PER_DAY + 1,
                "mara-vale": 0,
            },
        )
        self.assertEqual(
            [
                (item.actor_id, item.count, item.model_bounded)
                for item in summary.decision_counts
            ],
            [
                (
                    "ilan-reed",
                    MAX_MODEL_DECISION_CALLS_PER_DAY + 1,
                    False,
                ),
                ("mara-vale", 0, True),
            ],
        )


if __name__ == "__main__":
    unittest.main()
