import unittest

from simulation.scheduling import ScheduledWork, TemporalAgenda, TemporalPhase
from simulation.time import MINUTES_PER_DAY, SimulatedDayClock, SimulatedTime


class TemporalAgendaTests(unittest.TestCase):
    def _agenda(self) -> TemporalAgenda:
        return TemporalAgenda(
            SimulatedDayClock(
                SimulatedTime.from_day_time(day_index=2, hour=6, minute=0)
            )
        )

    def _equal_time_items(self, due_time: SimulatedTime) -> tuple[ScheduledWork, ...]:
        return (
            ScheduledWork("decision-mara", due_time, TemporalPhase.DECISION, "decision"),
            ScheduledWork(
                "delivery-mara",
                due_time,
                TemporalPhase.OBSERVATION_DELIVERY,
                "delivery",
            ),
            ScheduledWork(
                "completion-mara",
                due_time,
                TemporalPhase.ACTION_COMPLETION,
                "completion",
            ),
            ScheduledWork(
                "world-broadcast",
                due_time,
                TemporalPhase.SCHEDULED_WORLD,
                "broadcast",
            ),
            ScheduledWork(
                "understanding-mara",
                due_time,
                TemporalPhase.UNDERSTANDING_UPDATE,
                "understanding",
            ),
            ScheduledWork(
                "completion-clerk",
                due_time,
                TemporalPhase.ACTION_COMPLETION,
                "completion",
            ),
        )

    def test_equal_time_work_uses_explicit_phase_then_stable_identity(self):
        agenda = self._agenda()
        due_time = agenda.clock.current.plus_minutes(15)
        for item in self._equal_time_items(due_time):
            agenda.schedule(item)

        due = agenda.advance_to_next_due()

        self.assertEqual(agenda.clock.current, due_time)
        self.assertEqual(
            [item.item_id for item in due],
            [
                "world-broadcast",
                "completion-clerk",
                "completion-mara",
                "delivery-mara",
                "understanding-mara",
                "decision-mara",
            ],
        )
        self.assertEqual(agenda.pending, ())

    def test_equal_configuration_is_independent_of_insertion_order(self):
        first = self._agenda()
        second = self._agenda()
        items = self._equal_time_items(first.clock.current.plus_minutes(30))
        for item in items:
            first.schedule(item)
        for item in reversed(items):
            second.schedule(item)

        self.assertEqual(first.pending, second.pending)
        self.assertEqual(
            first.advance_to_next_due(),
            second.advance_to_next_due(),
        )

    def test_quiet_intervals_jump_to_due_work_then_exact_day_end(self):
        agenda = self._agenda()
        afternoon = agenda.clock.current.plus_minutes(8 * 60 + 20)
        agenda.schedule(
            ScheduledWork(
                "afternoon-shift",
                afternoon,
                TemporalPhase.SCHEDULED_WORLD,
                "shift_change",
            )
        )

        due = agenda.advance_to_next_due()
        self.assertEqual([item.item_id for item in due], ["afternoon-shift"])
        self.assertEqual(agenda.clock.current, afternoon)
        self.assertEqual(agenda.advance_to_next_due(), ())
        self.assertEqual(
            agenda.clock.current.total_minutes - agenda.clock.start.total_minutes,
            MINUTES_PER_DAY,
        )
        self.assertTrue(agenda.clock.is_complete)

    def test_schedule_rejects_duplicate_past_and_beyond_day_without_mutation(self):
        agenda = self._agenda()
        current = agenda.clock.current
        accepted = ScheduledWork(
            "wake-mara",
            current,
            TemporalPhase.DECISION,
            "scheduled_wake",
        )
        agenda.schedule(accepted)
        with self.assertRaisesRegex(ValueError, "identity already used"):
            agenda.schedule(accepted)
        self.assertEqual(agenda.advance_to_next_due(), (accepted,))
        with self.assertRaisesRegex(ValueError, "identity already used"):
            agenda.schedule(accepted)
        with self.assertRaisesRegex(ValueError, "before current time"):
            agenda.schedule(
                ScheduledWork(
                    "past",
                    SimulatedTime(current.total_minutes - 1),
                    TemporalPhase.DECISION,
                    "decision",
                )
            )
        with self.assertRaisesRegex(ValueError, "beyond the day boundary"):
            agenda.schedule(
                ScheduledWork(
                    "tomorrow",
                    agenda.clock.end.plus_minutes(1),
                    TemporalPhase.SCHEDULED_WORLD,
                    "event",
                )
            )
        self.assertEqual(agenda.pending, ())

    def test_external_clock_advance_cannot_silently_skip_pending_work(self):
        agenda = self._agenda()
        due_time = agenda.clock.current.plus_minutes(10)
        agenda.schedule(
            ScheduledWork(
                "delivery",
                due_time,
                TemporalPhase.OBSERVATION_DELIVERY,
                "delivery",
            )
        )
        agenda.clock.advance_to(due_time.plus_minutes(1))

        with self.assertRaisesRegex(RuntimeError, "advanced past pending"):
            _ = agenda.next_due_time
        self.assertEqual([item.item_id for item in agenda.pending], ["delivery"])


if __name__ == "__main__":
    unittest.main()
