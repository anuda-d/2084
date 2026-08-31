import unittest

from simulation.decision_eligibility import (
    SAFE_FAILURE_RETRY_MINUTES,
    DecisionEligibility,
    DecisionTrigger,
    DecisionTriggerKind,
)
from simulation.scheduling import TemporalAgenda
from simulation.time import SimulatedDayClock, SimulatedTime


class DecisionEligibilityTests(unittest.TestCase):
    def _components(self) -> tuple[TemporalAgenda, DecisionEligibility]:
        agenda = TemporalAgenda(
            SimulatedDayClock(
                SimulatedTime.from_day_time(day_index=4, hour=6, minute=0)
            )
        )
        return agenda, DecisionEligibility(agenda)

    def test_explicit_simultaneous_causes_coalesce_into_one_actor_decision(self):
        agenda, eligibility = self._components()
        due_time = agenda.clock.current
        requested = (
            DecisionTrigger(
                DecisionTriggerKind.OBSERVATION_DELIVERED,
                "observation-0002",
            ),
            DecisionTrigger(
                DecisionTriggerKind.INITIAL_ACTIVATION,
                "day-start",
            ),
            DecisionTrigger(
                DecisionTriggerKind.ACTION_RESULT,
                "result-0001",
            ),
        )
        work = tuple(
            eligibility.request(
                actor_id="mara-vale",
                due_time=due_time,
                trigger=trigger,
            )
            for trigger in requested
        )

        self.assertEqual(work, (work[0], work[0], work[0]))
        self.assertEqual(eligibility.pending_count, 1)
        self.assertEqual(agenda.advance_to_next_due(), (work[0],))
        decision = eligibility.consume(work[0])
        self.assertEqual(decision.actor_id, "mara-vale")
        self.assertEqual(decision.due_time, due_time)
        self.assertEqual(
            [(trigger.kind, trigger.source_id) for trigger in decision.triggers],
            [
                (DecisionTriggerKind.ACTION_RESULT, "result-0001"),
                (DecisionTriggerKind.INITIAL_ACTIVATION, "day-start"),
                (
                    DecisionTriggerKind.OBSERVATION_DELIVERED,
                    "observation-0002",
                ),
            ],
        )
        self.assertEqual(eligibility.pending_count, 0)

    def test_time_passage_alone_creates_no_decision_or_noop_work(self):
        agenda, eligibility = self._components()

        self.assertEqual(eligibility.pending_count, 0)
        self.assertEqual(agenda.pending, ())
        self.assertEqual(agenda.advance_to_next_due(), ())
        self.assertTrue(agenda.clock.is_complete)
        self.assertEqual(eligibility.pending_count, 0)

    def test_safe_failure_creates_one_retry_exactly_thirty_minutes_later(self):
        agenda, eligibility = self._components()
        failed_at = agenda.clock.current

        retry = eligibility.request_safe_failure_retry(
            actor_id="mara-vale",
            failed_at=failed_at,
            failure_id="decision-failure-0001",
        )

        self.assertIsNotNone(retry)
        self.assertEqual(
            retry.due_time,
            failed_at.plus_minutes(SAFE_FAILURE_RETRY_MINUTES),
        )
        self.assertEqual(agenda.next_due_time, retry.due_time)
        self.assertEqual(agenda.advance_to_next_due(), (retry,))
        decision = eligibility.consume(retry)
        self.assertEqual(
            decision.triggers,
            (
                DecisionTrigger(
                    DecisionTriggerKind.SAFE_FAILURE_RETRY,
                    "decision-failure-0001",
                ),
            ),
        )
        self.assertEqual(agenda.clock.current, failed_at.plus_minutes(30))

    def test_safe_failure_at_or_beyond_day_has_no_retry_or_pending_identity(self):
        agenda, eligibility = self._components()
        exact_boundary_failure = SimulatedTime(
            agenda.clock.end.total_minutes - SAFE_FAILURE_RETRY_MINUTES
        )
        agenda.clock.advance_to(exact_boundary_failure)
        self.assertIsNone(
            eligibility.request_safe_failure_retry(
                actor_id="mara-vale",
                failed_at=exact_boundary_failure,
                failure_id="decision-failure-boundary",
            )
        )
        self.assertEqual(eligibility.pending_count, 0)
        self.assertEqual(agenda.pending, ())

        agenda, eligibility = self._components()
        failed_at = SimulatedTime(
            agenda.clock.end.total_minutes - (SAFE_FAILURE_RETRY_MINUTES - 1)
        )
        agenda.clock.advance_to(failed_at)

        self.assertIsNone(
            eligibility.request_safe_failure_retry(
                actor_id="mara-vale",
                failed_at=failed_at,
                failure_id="decision-failure-final",
            )
        )
        self.assertEqual(eligibility.pending_count, 0)
        self.assertEqual(agenda.pending, ())

        with self.assertRaisesRegex(ValueError, "must equal current"):
            eligibility.request_safe_failure_retry(
                actor_id="mara-vale",
                failed_at=SimulatedTime(failed_at.total_minutes - 1),
                failure_id="decision-failure-stale",
            )

    def test_existing_retry_remains_available_after_a_later_boundary_failure(self):
        agenda, eligibility = self._components()
        first_failure = SimulatedTime(
            agenda.clock.end.total_minutes - SAFE_FAILURE_RETRY_MINUTES - 5
        )
        agenda.clock.advance_to(first_failure)
        pending_retry = eligibility.request_safe_failure_retry(
            actor_id="mara-vale",
            failed_at=first_failure,
            failure_id="decision-failure-first",
        )
        self.assertIsNotNone(pending_retry)

        later_failure = SimulatedTime(agenda.clock.end.total_minutes - 20)
        agenda.clock.advance_to(later_failure)
        self.assertIs(
            eligibility.request_safe_failure_retry(
                actor_id="mara-vale",
                failed_at=later_failure,
                failure_id="decision-failure-too-late",
            ),
            pending_retry,
        )

    def test_consumed_retry_can_start_the_next_retry_chain_link(self):
        agenda, eligibility = self._components()
        first_retry = eligibility.request_safe_failure_retry(
            actor_id="mara-vale",
            failed_at=agenda.clock.current,
            failure_id="decision-failure-first",
        )
        self.assertIsNotNone(first_retry)
        agenda.advance_to_next_due()
        eligibility.consume(first_retry)

        second_retry = eligibility.request_safe_failure_retry(
            actor_id="mara-vale",
            failed_at=agenda.clock.current,
            failure_id="decision-failure-second",
        )

        self.assertIsNotNone(second_retry)
        self.assertEqual(
            second_retry.due_time,
            first_retry.due_time.plus_minutes(SAFE_FAILURE_RETRY_MINUTES),
        )

    def test_duplicate_trigger_is_idempotent_and_consumption_is_once_only(self):
        agenda, eligibility = self._components()
        trigger = DecisionTrigger(
            DecisionTriggerKind.SCHEDULED_WAKE,
            "wake-after-rest",
        )
        work = eligibility.request(
            actor_id="mara-vale",
            due_time=agenda.clock.current.plus_minutes(90),
            trigger=trigger,
        )
        eligibility.request(
            actor_id="mara-vale",
            due_time=work.due_time,
            trigger=trigger,
        )
        with self.assertRaisesRegex(ValueError, "has not been released"):
            eligibility.consume(work)
        agenda.advance_to_next_due()

        decision = eligibility.consume(work)
        self.assertEqual(decision.triggers, (trigger,))
        with self.assertRaisesRegex(ValueError, "unknown or already consumed"):
            eligibility.consume(work)

    def test_released_eligibility_cannot_be_consumed_after_time_advances(self):
        agenda, eligibility = self._components()
        work = eligibility.request(
            actor_id="mara-vale",
            due_time=agenda.clock.current,
            trigger=DecisionTrigger(
                DecisionTriggerKind.INITIAL_ACTIVATION,
                "day-start",
            ),
        )
        agenda.advance_to_next_due()
        agenda.advance_to_next_due()

        with self.assertRaisesRegex(ValueError, "not at current time"):
            eligibility.consume(work)
        self.assertEqual(eligibility.pending_count, 1)


if __name__ == "__main__":
    unittest.main()
