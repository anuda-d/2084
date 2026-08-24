import json
import unittest

from simulation.day_runtime import AcceleratedDayRuntime
from simulation.scheduling import ScheduledWork, TemporalPhase
from simulation.time import MINUTES_PER_DAY, SimulatedTime


class AcceleratedDayRuntimeTests(unittest.TestCase):
    def _start(self) -> SimulatedTime:
        return SimulatedTime.from_day_time(day_index=5, hour=6, minute=30)

    def test_empty_day_reaches_exact_end_with_one_quiet_span_and_closes(self):
        runtime = AcceleratedDayRuntime(start=self._start(), handlers={})

        summary = runtime.run()

        self.assertTrue(runtime.is_complete)
        self.assertTrue(runtime.is_registration_closed)
        self.assertEqual(summary.current, summary.end)
        self.assertEqual(
            summary.end.total_minutes - summary.start.total_minutes,
            MINUTES_PER_DAY,
        )
        self.assertEqual(summary.executed_work, ())
        self.assertEqual(len(summary.quiet_spans), 1)
        self.assertEqual(summary.quiet_spans[0].duration_minutes, MINUTES_PER_DAY)
        self.assertEqual(runtime.run(), summary)
        with self.assertRaisesRegex(RuntimeError, "agenda is closed"):
            runtime.schedule(
                ScheduledWork(
                    "after-close",
                    runtime.end,
                    TemporalPhase.SCHEDULED_WORLD,
                    "world",
                )
            )

    def test_handlers_can_schedule_later_same_time_phases_before_decision(self):
        execution: list[str] = []

        def handle_world(work, context):
            execution.append(work.item_id)
            self.assertFalse(hasattr(context, "agenda"))
            self.assertFalse(hasattr(context, "clock"))
            self.assertFalse(hasattr(context, "run"))
            context.schedule(
                ScheduledWork(
                    "completion",
                    work.due_time,
                    TemporalPhase.ACTION_COMPLETION,
                    "completion",
                )
            )

        def handle_completion(work, context):
            execution.append(work.item_id)
            context.schedule(
                ScheduledWork(
                    "delivery",
                    work.due_time,
                    TemporalPhase.OBSERVATION_DELIVERY,
                    "delivery",
                )
            )

        def record(work, context):
            execution.append(work.item_id)

        runtime = AcceleratedDayRuntime(
            start=self._start(),
            handlers={
                "world": handle_world,
                "completion": handle_completion,
                "delivery": record,
                "decision": record,
            },
        )
        due_time = runtime.start.plus_minutes(60)
        runtime.schedule(
            ScheduledWork(
                "decision",
                due_time,
                TemporalPhase.DECISION,
                "decision",
            )
        )
        runtime.schedule(
            ScheduledWork(
                "world",
                due_time,
                TemporalPhase.SCHEDULED_WORLD,
                "world",
            )
        )

        summary = runtime.run()

        self.assertEqual(execution, ["world", "completion", "delivery", "decision"])
        self.assertEqual(
            [item.item_id for item in summary.executed_work],
            execution,
        )
        self.assertEqual(
            [span.duration_minutes for span in summary.quiet_spans],
            [60, MINUTES_PER_DAY - 60],
        )
        self.assertTrue(summary.reached_end_boundary)

    def test_equal_configuration_produces_equal_order_independent_of_insertion(self):
        def build(reverse: bool):
            runtime = AcceleratedDayRuntime(
                start=self._start(),
                handlers={"world": lambda work, active: None},
            )
            items = (
                ScheduledWork(
                    "world-b",
                    runtime.start.plus_minutes(15),
                    TemporalPhase.SCHEDULED_WORLD,
                    "world",
                ),
                ScheduledWork(
                    "world-a",
                    runtime.start.plus_minutes(15),
                    TemporalPhase.SCHEDULED_WORLD,
                    "world",
                ),
            )
            for item in reversed(items) if reverse else items:
                runtime.schedule(item)
            return runtime

        first = build(False).run()
        second = build(True).run()

        self.assertEqual(first.to_data(), second.to_data())
        self.assertEqual(
            [item.item_id for item in first.executed_work],
            ["world-a", "world-b"],
        )

    def test_work_due_exactly_at_end_executes_before_registration_closes(self):
        executed: list[str] = []

        def record(work, context):
            executed.append(work.item_id)

        runtime = AcceleratedDayRuntime(
            start=self._start(),
            handlers={"world": record},
        )
        runtime.schedule(
            ScheduledWork(
                "end-boundary-work",
                runtime.end,
                TemporalPhase.SCHEDULED_WORLD,
                "world",
            )
        )

        summary = runtime.run()

        self.assertEqual(executed, ["end-boundary-work"])
        self.assertEqual(summary.current, summary.end)
        self.assertTrue(summary.reached_end_boundary)
        self.assertTrue(runtime.is_registration_closed)

    def test_handler_exception_is_terminal_sanitized_and_not_false_complete(self):
        def fail(work, context):
            raise ValueError("private-provider-marker")

        runtime = AcceleratedDayRuntime(
            start=self._start(),
            handlers={"failure": fail},
        )
        failed_time = runtime.start.plus_minutes(10)
        runtime.schedule(
            ScheduledWork(
                "private-work-id",
                failed_time,
                TemporalPhase.SCHEDULED_WORLD,
                "failure",
            )
        )

        with self.assertRaisesRegex(ValueError, "private-provider-marker"):
            runtime.run()

        self.assertFalse(runtime.is_complete)
        failure = runtime.runtime_failure
        self.assertEqual(failure.failure_type, "ValueError")
        self.assertEqual(failure.last_committed_time, runtime.start)
        self.assertEqual(failure.failed_time, failed_time)
        self.assertEqual(failure.committed_work_count, 0)
        self.assertEqual(failure.released_uncommitted_count, 1)
        serialized = json.dumps(runtime.summary().to_data(), sort_keys=True)
        self.assertNotIn("private-provider-marker", serialized)
        self.assertNotIn("private-work-id", serialized)
        before_retry = runtime.summary().to_data()
        with self.assertRaisesRegex(RuntimeError, "stopped after"):
            runtime.schedule(
                ScheduledWork(
                    "post-failure",
                    runtime.current,
                    TemporalPhase.DECISION,
                    "failure",
                )
            )
        with self.assertRaisesRegex(RuntimeError, "stopped after"):
            runtime.run()
        self.assertEqual(runtime.summary().to_data(), before_retry)


if __name__ == "__main__":
    unittest.main()
