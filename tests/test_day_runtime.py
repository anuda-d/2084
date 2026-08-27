import json
import unittest

from simulation.day_runtime import AcceleratedDayRuntime
from simulation.decision_eligibility import DecisionTrigger, DecisionTriggerKind
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

    def test_time_observer_runs_before_handlers_and_at_exact_end(self):
        observed: list[tuple[str, int]] = []

        def on_time_advanced(current):
            observed.append(("time", current.total_minutes))

        def record(work, context):
            observed.append(("handler", context.current.total_minutes))

        runtime = AcceleratedDayRuntime(
            start=SimulatedTime(0),
            handlers={"world": record},
            on_time_advanced=on_time_advanced,
        )
        runtime.schedule(
            ScheduledWork(
                "midday-work",
                SimulatedTime(720),
                TemporalPhase.SCHEDULED_WORLD,
                "world",
            )
        )

        runtime.run()

        self.assertEqual(
            observed,
            [("time", 720), ("handler", 720), ("time", 1440)],
        )

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
        self.assertEqual(
            failure.failed_dispatch.to_data(),
            {
                "due_time": failed_time.to_data(),
                "phase": "scheduled_world",
                "sequence": 1,
            },
        )
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

    def test_dispatch_commit_observer_runs_only_after_successful_handlers(self):
        committed: list[tuple[int, str, str]] = []

        def record_commit(sequence, work):
            committed.append((sequence, work.item_id, work.phase.name.lower()))

        successful = AcceleratedDayRuntime(
            start=self._start(),
            handlers={"success": lambda work, context: None},
            on_dispatch_committed=record_commit,
        )
        successful.schedule(
            ScheduledWork(
                "successful-work",
                successful.start.plus_minutes(10),
                TemporalPhase.SCHEDULED_WORLD,
                "success",
            )
        )

        successful.run()

        self.assertEqual(committed, [(1, "successful-work", "scheduled_world")])

        def fail(work, context):
            raise ValueError()

        failed = AcceleratedDayRuntime(
            start=self._start(),
            handlers={"failure": fail},
            on_dispatch_committed=record_commit,
        )
        failed.schedule(
            ScheduledWork(
                "failed-work",
                failed.start.plus_minutes(10),
                TemporalPhase.SCHEDULED_WORLD,
                "failure",
            )
        )

        with self.assertRaises(ValueError):
            failed.run()

        self.assertEqual(committed, [(1, "successful-work", "scheduled_world")])

        def fail_after_commit(sequence, work):
            raise RuntimeError("observer failure")

        observer_failed = AcceleratedDayRuntime(
            start=self._start(),
            handlers={"success": lambda work, context: None},
            on_dispatch_committed=fail_after_commit,
        )
        observer_failed.schedule(
            ScheduledWork(
                "committed-before-observer-failure",
                observer_failed.start.plus_minutes(10),
                TemporalPhase.SCHEDULED_WORLD,
                "success",
            )
        )

        with self.assertRaisesRegex(RuntimeError, "observer failure"):
            observer_failed.run()

        observer_failure = observer_failed.runtime_failure
        self.assertEqual(observer_failure.committed_work_count, 1)
        self.assertIsNone(observer_failure.failed_dispatch)
        self.assertEqual(
            [work.item_id for work in observer_failed.summary().executed_work],
            ["committed-before-observer-failure"],
        )

    def test_failed_dispatch_sequence_follows_committed_same_minute_work(self):
        def fail(work, context):
            raise ValueError()

        runtime = AcceleratedDayRuntime(
            start=self._start(),
            handlers={
                "commit": lambda work, context: None,
                "fail": fail,
            },
        )
        due_time = runtime.start.plus_minutes(10)
        runtime.schedule(
            ScheduledWork(
                "committed-first",
                due_time,
                TemporalPhase.SCHEDULED_WORLD,
                "commit",
            )
        )
        runtime.schedule(
            ScheduledWork(
                "private-second",
                due_time,
                TemporalPhase.SCHEDULED_WORLD,
                "fail",
            )
        )

        with self.assertRaises(ValueError):
            runtime.run()

        failure = runtime.runtime_failure
        self.assertEqual(failure.committed_work_count, 1)
        self.assertEqual(
            failure.failed_dispatch.to_data(),
            {
                "due_time": due_time.to_data(),
                "phase": "scheduled_world",
                "sequence": 2,
            },
        )

    def test_only_active_decision_actor_can_schedule_safe_failure_retry(self):
        attempted_retries = []
        retained_contexts = []

        def unrelated_work(work, context):
            with self.assertRaisesRegex(RuntimeError, "only available"):
                context.request_safe_failure_retry(
                    actor_id="mara-vale",
                    failure_id="unrelated-work-failure",
                )
            with self.assertRaisesRegex(
                RuntimeError, "active decision|expired"
            ):
                retained_contexts[0].request_safe_failure_retry(
                    actor_id="mara-vale",
                    failure_id="stale-decision-failure",
                )
            with self.assertRaisesRegex(ValueError, "require the active"):
                context.request_decision(
                    actor_id="ilan-reed",
                    due_time=runtime.start.plus_minutes(21),
                    trigger=DecisionTrigger(
                        DecisionTriggerKind.SAFE_FAILURE_RETRY,
                        "forged-unrelated-retry",
                    ),
                )
            with self.assertRaisesRegex(ValueError, "require the active"):
                retained_contexts[0].request_decision(
                    actor_id="ilan-reed",
                    due_time=runtime.start.plus_minutes(21),
                    trigger=DecisionTrigger(
                        DecisionTriggerKind.SAFE_FAILURE_RETRY,
                        "forged-stale-retry",
                    ),
                )

        def handle_decision(decision, context):
            if any(
                trigger.kind is DecisionTriggerKind.SAFE_FAILURE_RETRY
                for trigger in decision.triggers
            ):
                return
            retained_contexts.append(context)
            with self.assertRaisesRegex(ValueError, "match the active decision"):
                context.request_safe_failure_retry(
                    actor_id="ilan-reed",
                    failure_id="mismatched-actor-failure",
                )
            attempted_retries.append(
                context.request_safe_failure_retry(
                    actor_id=decision.actor_id,
                    failure_id="mara-decision-failure",
                )
            )

        runtime = AcceleratedDayRuntime(
            start=self._start(),
            handlers={"unrelated": unrelated_work},
            decision_handler=handle_decision,
        )
        runtime.schedule(
            ScheduledWork(
                "unrelated-work",
                runtime.start.plus_minutes(20),
                TemporalPhase.SCHEDULED_WORLD,
                "unrelated",
            )
        )
        runtime.request_decision(
            actor_id="mara-vale",
            due_time=runtime.start.plus_minutes(10),
            trigger=DecisionTrigger(
                DecisionTriggerKind.SCHEDULED_WAKE,
                "mara-morning-wake",
            ),
        )
        with self.assertRaisesRegex(ValueError, "require the active"):
            runtime.request_decision(
                actor_id="ilan-reed",
                due_time=runtime.start.plus_minutes(1),
                trigger=DecisionTrigger(
                    DecisionTriggerKind.SAFE_FAILURE_RETRY,
                    "forged-direct-retry",
                ),
            )

        summary = runtime.run()

        self.assertTrue(summary.reached_end_boundary)
        self.assertFalse(hasattr(runtime, "request_safe_failure_retry"))
        self.assertEqual(len(retained_contexts), 1)
        self.assertEqual(len(attempted_retries), 1)
        self.assertIsNotNone(attempted_retries[0])
        self.assertEqual(
            attempted_retries[0].due_time,
            runtime.start.plus_minutes(40),
        )
        self.assertEqual(
            summary.to_data()["decision_counts_by_actor"], {"mara-vale": 2}
        )


if __name__ == "__main__":
    unittest.main()
