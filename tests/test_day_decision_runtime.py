import unittest

from simulation.day_runtime import AcceleratedDayRuntime
from simulation.decision_eligibility import (
    SAFE_FAILURE_RETRY_MINUTES,
    DecisionTrigger,
    DecisionTriggerKind,
)
from simulation.time import MINUTES_PER_DAY, SimulatedTime


class AcceleratedDayDecisionRuntimeTests(unittest.TestCase):
    def _start(self) -> SimulatedTime:
        return SimulatedTime.from_day_time(day_index=6, hour=7, minute=0)

    def test_initial_and_simultaneous_causes_dispatch_one_decision(self):
        decisions = []

        def decide(decision, context):
            decisions.append(decision)

        runtime = AcceleratedDayRuntime(
            start=self._start(),
            handlers={},
            decision_handler=decide,
        )
        runtime.request_decision(
            actor_id="mara-vale",
            due_time=runtime.start,
            trigger=DecisionTrigger(
                DecisionTriggerKind.INITIAL_ACTIVATION,
                "day-start",
            ),
        )
        runtime.request_decision(
            actor_id="mara-vale",
            due_time=runtime.start,
            trigger=DecisionTrigger(
                DecisionTriggerKind.OBSERVATION_DELIVERED,
                "observation-0001",
            ),
        )

        summary = runtime.run()

        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0].actor_id, "mara-vale")
        self.assertEqual(
            [trigger.kind for trigger in decisions[0].triggers],
            [
                DecisionTriggerKind.INITIAL_ACTIVATION,
                DecisionTriggerKind.OBSERVATION_DELIVERED,
            ],
        )
        self.assertEqual(len(summary.executed_work), 1)
        self.assertEqual(runtime.pending_decision_count, 0)
        self.assertTrue(runtime.is_complete)

    def test_quiet_day_calls_no_decision_handler(self):
        decisions = []
        runtime = AcceleratedDayRuntime(
            start=self._start(),
            handlers={},
            decision_handler=lambda decision, context: decisions.append(decision),
        )

        summary = runtime.run()

        self.assertEqual(decisions, [])
        self.assertEqual(summary.executed_work, ())
        self.assertEqual(len(summary.quiet_spans), 1)
        self.assertEqual(summary.quiet_spans[0].duration_minutes, MINUTES_PER_DAY)

    def test_safe_failure_causes_only_one_retry_thirty_minutes_later(self):
        decisions = []

        def decide(decision, context):
            decisions.append(decision)
            if decision.triggers[0].kind is DecisionTriggerKind.INITIAL_ACTIVATION:
                context.request_safe_failure_retry(
                    actor_id=decision.actor_id,
                    failure_id="provider-timeout-0001",
                )

        runtime = AcceleratedDayRuntime(
            start=self._start(),
            handlers={},
            decision_handler=decide,
        )
        runtime.request_decision(
            actor_id="mara-vale",
            due_time=runtime.start,
            trigger=DecisionTrigger(
                DecisionTriggerKind.INITIAL_ACTIVATION,
                "day-start",
            ),
        )

        summary = runtime.run()

        self.assertEqual(len(decisions), 2)
        self.assertEqual(
            decisions[1].due_time.total_minutes
            - decisions[0].due_time.total_minutes,
            SAFE_FAILURE_RETRY_MINUTES,
        )
        self.assertEqual(
            decisions[1].triggers[0].kind,
            DecisionTriggerKind.SAFE_FAILURE_RETRY,
        )
        self.assertEqual(
            [span.duration_minutes for span in summary.quiet_spans],
            [
                SAFE_FAILURE_RETRY_MINUTES,
                MINUTES_PER_DAY - SAFE_FAILURE_RETRY_MINUTES,
            ],
        )
        self.assertEqual(len(summary.executed_work), 2)

    def test_trigger_without_decision_handler_is_terminal_not_complete(self):
        runtime = AcceleratedDayRuntime(start=self._start(), handlers={})
        runtime.request_decision(
            actor_id="mara-vale",
            due_time=runtime.start,
            trigger=DecisionTrigger(
                DecisionTriggerKind.SCHEDULED_WAKE,
                "wake-0001",
            ),
        )

        with self.assertRaisesRegex(RuntimeError, "no decision handler"):
            runtime.run()

        self.assertFalse(runtime.is_complete)
        self.assertIsNotNone(runtime.runtime_failure)
        self.assertTrue(runtime.is_registration_closed)

    def test_decision_handler_cannot_add_same_minute_cause_after_release(self):
        for source_actor, target_actor in (
            ("actor-a", "actor-b"),
            ("actor-b", "actor-a"),
        ):
            with self.subTest(source_actor=source_actor):
                def decide(decision, context):
                    if decision.actor_id == source_actor:
                        context.request_decision(
                            actor_id=target_actor,
                            due_time=context.current,
                            trigger=DecisionTrigger(
                                DecisionTriggerKind.OBSERVATION_DELIVERED,
                                "late-same-minute-cause",
                            ),
                        )

                runtime = AcceleratedDayRuntime(
                    start=self._start(),
                    handlers={},
                    decision_handler=decide,
                )
                for actor_id in ("actor-a", "actor-b"):
                    runtime.request_decision(
                        actor_id=actor_id,
                        due_time=runtime.start,
                        trigger=DecisionTrigger(
                            DecisionTriggerKind.INITIAL_ACTIVATION,
                            f"start-{actor_id}",
                        ),
                    )

                with self.assertRaisesRegex(
                    ValueError,
                    "already been released|identity already used",
                ):
                    runtime.run()

                self.assertFalse(runtime.is_complete)
                self.assertIsNotNone(runtime.runtime_failure)


if __name__ == "__main__":
    unittest.main()
