import json
import io
import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from unittest.mock import patch

from policies.mara_harness import MaraHarness
from policies.ollama_client import OllamaDecisionClient
from scenarios.autonomous_day import (
    AUTONOMOUS_DAY_MARA_ACTION_CONTINUITY_RULES,
    AUTONOMOUS_DAY_MARA_RESOLVER_KINDS,
    ILAN_ID,
    MARA_ID,
    _focal_update_sort_key,
    autonomous_day_mara_valid_actions,
    autonomous_day_inspector_data,
    build_autonomous_day,
    main,
    render_autonomous_day,
)
from policies.model_focal_policy import (
    RecordedDecisionArchive,
    RecordedDecisionError,
    model_input_from_view,
)
from policies.mara_decision_request import MAX_RESTRICTED_DECISION_INPUT_BYTES
from simulation.actions import ActionAttempt, ActionResult
from simulation.agents import (
    ActionContinuityRequirement,
    MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES,
)
from simulation.decision_eligibility import DecisionTrigger, DecisionTriggerKind
from simulation.scheduling import ScheduledWork, TemporalPhase
from simulation.time import SimulatedTime


class _SequenceClient:
    def __init__(self, *responses):
        self._responses = responses
        self.inputs = []

    def choose(self, model_input):
        self.inputs.append(model_input)
        response = self._responses[len(self.inputs) - 1]
        if isinstance(response, BaseException):
            raise response
        return response


class AutonomousDayWorldTests(unittest.TestCase):
    def test_action_continuity_table_covers_the_resolver_vocabulary(self):
        rules = AUTONOMOUS_DAY_MARA_ACTION_CONTINUITY_RULES

        self.assertEqual(set(rules), set(AUTONOMOUS_DAY_MARA_RESOLVER_KINDS))
        self.assertEqual(
            set(autonomous_day_mara_valid_actions("home"))
            | set(autonomous_day_mara_valid_actions("workplace")),
            set(AUTONOMOUS_DAY_MARA_RESOLVER_KINDS),
        )
        self.assertEqual(rules["travel"].retention, "canonical_current_state")
        self.assertEqual(rules["wait"].retention, "recent_result_only")
        self.assertEqual(
            {
                kind: rule.obligation
                for kind, rule in rules.items()
                if rule.retention == "fulfilled_obligation_requirement"
            },
            {
                "work": "workplace shift",
                "household": "household time",
            },
        )

    def test_inspector_reports_sanitized_model_decision_status_sequence(self):
        client = _SequenceClient(
            TimeoutError("private provider detail"),
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after retry",
                "decision_reason": "the morning remains quiet",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the bulletin",
                "decision_reason": "no immediate action is needed",
            },
        )
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id="inspector-decision-status-sequence-test",
            ),
        )

        inspector = autonomous_day_inspector_data(day, day.run())
        model_path = inspector["model_path"]

        self.assertEqual(
            model_path["decision_status_sequence"],
            [
                {
                    "tick": 420,
                    "status": "failed",
                    "failure_kind": "timeout",
                    "provider_call_attempted": True,
                    "validation_status": "accepted",
                    "resolution_status": "completed",
                    "resolved_tick": 420,
                    "dispatch": {"sequence": 1, "phase": "decision"},
                },
                {
                    "tick": 450,
                    "status": "selected",
                    "failure_kind": None,
                    "provider_call_attempted": True,
                    "validation_status": "accepted",
                    "resolution_status": "completed",
                    "resolved_tick": 450,
                    "dispatch": {"sequence": 2, "phase": "decision"},
                },
                {
                    "tick": 660,
                    "status": "selected",
                    "failure_kind": None,
                    "provider_call_attempted": True,
                    "validation_status": "accepted",
                    "resolution_status": "completed",
                    "resolved_tick": 660,
                    "dispatch": {"sequence": 10, "phase": "decision"},
                },
            ],
        )
        self.assertTrue(
            all(
                set(entry) == {
                    "tick",
                    "status",
                    "failure_kind",
                    "provider_call_attempted",
                    "validation_status",
                    "resolution_status",
                    "resolved_tick",
                    "dispatch",
                }
                for entry in model_path["decision_status_sequence"]
            )
        )
        runtime_decisions = [
            work
            for work in inspector["runtime"]["executed_work"]
            if work["kind"] == "decision_eligibility"
            and work["item_id"].endswith(f":{MARA_ID}")
        ]
        self.assertEqual(
            [entry["dispatch"] for entry in model_path["decision_status_sequence"]],
            [
                {"sequence": work["sequence"], "phase": work["phase"]}
                for work in runtime_decisions
            ],
        )
        serialized_status_sequence = json.dumps(
            model_path["decision_status_sequence"]
        )
        self.assertNotIn("private provider detail", serialized_status_sequence)
        self.assertNotIn("pause after retry", serialized_status_sequence)

        failed_dispatch_day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                _SequenceClient(
                    {
                        "kind": "wait",
                        "parameters": {},
                        "explanation": "pause before the forced failure",
                        "decision_reason": "the morning is quiet",
                    }
                ),
                configuration_id="inspector-uncommitted-decision-test",
            ),
        )
        original_handler = failed_dispatch_day.runtime._decision_handler
        self.assertIsNotNone(original_handler)

        def fail_after_private_decision(decision, context):
            original_handler(decision, context)
            raise RuntimeError("private decision dispatch failure")

        failed_dispatch_day.runtime._decision_handler = fail_after_private_decision
        with self.assertRaisesRegex(RuntimeError, "private decision dispatch failure"):
            failed_dispatch_day.run()
        failed_sequence = autonomous_day_inspector_data(
            failed_dispatch_day,
            failed_dispatch_day.runtime.summary(),
        )["model_path"]["decision_status_sequence"]
        self.assertEqual(len(failed_sequence), 1)
        self.assertIsNone(failed_sequence[0]["dispatch"])
        self.assertNotIn("private decision dispatch failure", json.dumps(failed_sequence))

        def incomplete_projection(view):
            model_input = model_input_from_view(view)
            continuity_projection = dict(model_input["continuity_projection"])
            continuity_projection["complete"] = False
            return {
                **model_input,
                "continuity_projection": continuity_projection,
            }

        with patch(
            "policies.model_focal_policy.model_input_from_view",
            side_effect=incomplete_projection,
        ):
            pre_client_day = build_autonomous_day(
                seed=42,
                mara_harness=MaraHarness.from_client(
                    _SequenceClient(),
                    configuration_id="inspector-pre-client-status-sequence-test",
                ),
            )
            pre_client_sequence = autonomous_day_inspector_data(
                pre_client_day,
                pre_client_day.run(),
            )["model_path"]["decision_status_sequence"]

        self.assertTrue(pre_client_sequence)
        self.assertTrue(
            all(
                entry["status"] == "failed"
                and entry["failure_kind"] == "continuity_projection_incomplete"
                and not entry["provider_call_attempted"]
                for entry in pre_client_sequence
            )
        )

    def test_inspector_action_results_follow_objective_event_order(self):
        client = _SequenceClient(
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause before the scheduled shift",
                "decision_reason": "the morning is quiet",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after resting",
                "decision_reason": "the completed rest needs no response",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the second wait",
                "decision_reason": "there is no immediate change",
            },
        )
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id="inspector-objective-result-order-test",
            ),
        )

        inspector = autonomous_day_inspector_data(day, day.run())
        results = inspector["history"]["action_results"]
        event_order = {
            event["event_id"]: index
            for index, event in enumerate(inspector["history"]["events"])
        }

        self.assertEqual(
            [result["actor_id"] for result in results],
            [MARA_ID, MARA_ID, ILAN_ID, ILAN_ID, MARA_ID],
        )
        self.assertEqual(
            [event_order[result["outcome_event_id"]] for result in results],
            sorted(event_order[result["outcome_event_id"]] for result in results),
        )

    def test_inspector_places_objective_tail_from_failed_dispatch(self):
        day = build_autonomous_day(seed=42)

        def record_then_commit(work, context):
            day._event_log.record(
                tick=context.current.total_minutes,
                kind="test_committed_objective_event",
                actor_id=None,
                action_id=None,
                details={"source": "committed"},
            )

        def record_then_fail(work, context):
            day._event_log.record(
                tick=context.current.total_minutes,
                kind="test_uncommitted_objective_event",
                actor_id=None,
                action_id=None,
                details={"source": "test"},
            )
            raise RuntimeError("private-failure-marker")

        day.runtime._handlers["test_committed_handler"] = record_then_commit
        day.runtime._handlers["test_uncommitted_handler"] = record_then_fail
        due_time = SimulatedTime(15)
        day.runtime.schedule(
            ScheduledWork(
                "committed-first-work-id",
                due_time,
                TemporalPhase.SCHEDULED_WORLD,
                "test_committed_handler",
            )
        )
        day.runtime.schedule(
            ScheduledWork(
                "private-uncommitted-work-id",
                due_time,
                TemporalPhase.SCHEDULED_WORLD,
                "test_uncommitted_handler",
            )
        )

        with self.assertRaisesRegex(RuntimeError, "private-failure-marker"):
            day.run()

        inspector = autonomous_day_inspector_data(day, day.runtime.summary())
        self.assertEqual(inspector["runtime"]["executed_work_count"], 1)
        self.assertEqual(
            inspector["runtime"]["runtime_failure"]["failed_dispatch"],
            {
                "due_time": due_time.to_data(),
                "phase": "scheduled_world",
                "sequence": 2,
            },
        )
        self.assertEqual(
            inspector["history"]["events"],
            [
                {
                    "event_id": "event-0001",
                    "tick": 15,
                    "kind": "test_committed_objective_event",
                    "actor_id": None,
                    "action_id": None,
                    "caused_by": [],
                    "details": {"source": "committed"},
                    "dispatch": {
                        "sequence": 1,
                        "phase": "scheduled_world",
                    },
                },
                {
                    "event_id": "event-0002",
                    "tick": 15,
                    "kind": "test_uncommitted_objective_event",
                    "actor_id": None,
                    "action_id": None,
                    "caused_by": [],
                    "details": {"source": "test"},
                    "dispatch": None,
                }
            ],
        )
        self.assertEqual(
            inspector["history"]["uncommitted_objective_tail"],
            {
                "events": [inspector["history"]["events"][1]],
                "observations": [],
                "action_results": [],
            },
        )
        rendered = json.dumps(inspector)
        self.assertNotIn("private-failure-marker", rendered)
        self.assertNotIn("private-uncommitted-work-id", rendered)
        self.assertNotIn("private-second", rendered)
        self.assertNotIn("test_uncommitted_handler", rendered)

    def test_inspector_exposes_consumed_decisions_and_understanding_transitions(
        self,
    ):
        client = _SequenceClient(
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "rest before the workday",
                "decision_reason": "the morning is quiet",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "wait after resting",
                "decision_reason": "rest is complete",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "wait after the bulletin",
                "decision_reason": "the bulletin needs no action",
            },
        )
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id="inspector-causal-evidence-test",
            ),
        )

        inspector = autonomous_day_inspector_data(day, day.run())

        self.assertEqual(
            inspector["runtime"]["consumed_decisions"],
            [
                {
                    "actor_id": MARA_ID,
                    "due_time": SimulatedTime(420).to_data(),
                    "scheduled_work_id": "decision:420:mara-vale",
                    "triggers": [
                        {
                            "kind": "scheduled_wake",
                            "source_id": "autonomous-day-mara-morning-wake",
                        }
                    ],
                },
                {
                    "actor_id": MARA_ID,
                    "due_time": SimulatedTime(480).to_data(),
                    "scheduled_work_id": "decision:480:mara-vale",
                    "triggers": [
                        {
                            "kind": "action_result",
                            "source_id": "event-0003",
                        }
                    ],
                },
                {
                    "actor_id": ILAN_ID,
                    "due_time": SimulatedTime(510).to_data(),
                    "scheduled_work_id": "decision:510:ilan-reed",
                    "triggers": [
                        {
                            "kind": "observation_delivered",
                            "source_id": "observation-0001",
                        }
                    ],
                },
                {
                    "actor_id": MARA_ID,
                    "due_time": SimulatedTime(660).to_data(),
                    "scheduled_work_id": "decision:660:mara-vale",
                    "triggers": [
                        {
                            "kind": "observation_delivered",
                            "source_id": "observation-0002",
                        }
                    ],
                },
            ],
        )
        observation = next(
            item
            for item in inspector["history"]["observations"]
            if item["agent_id"] == MARA_ID
        )
        self.assertEqual(
            inspector["history"]["understanding_transitions"],
            [
                {
                    "agent_id": MARA_ID,
                    "tick": 660,
                    "source_observation_id": observation["observation_id"],
                    "source_event_id": observation["event_id"],
                    "trace_id": f"trace-{observation['observation_id']}",
                    "claim_id": f"claim-{observation['observation_id']}",
                    "claim_created": True,
                    "dispatch": {
                        "sequence": 10,
                        "phase": "understanding_update",
                    },
                }
            ],
        )
        inspector["history"]["understanding_transitions"][0]["claim_id"] = (
            "forged-claim"
        )
        self.assertEqual(
            autonomous_day_inspector_data(day, day.run())["history"][
                "understanding_transitions"
            ][0]["claim_id"],
            f"claim-{observation['observation_id']}",
        )
        self.assertNotIn("model_input", json.dumps(inspector))
        self.assertNotIn("private_decision_records", json.dumps(inspector))

    def test_inspector_links_committed_objective_history_to_runtime_dispatches(self):
        day = build_autonomous_day(seed=42)

        inspector = autonomous_day_inspector_data(day, day.run())

        self.assertEqual(
            [event["dispatch"] for event in inspector["history"]["events"]],
            [
                {"sequence": 1, "phase": "scheduled_world"},
                {"sequence": 2, "phase": "scheduled_world"},
                {"sequence": 4, "phase": "decision"},
                {"sequence": 4, "phase": "decision"},
                {"sequence": 5, "phase": "action_completion"},
            ],
        )
        self.assertEqual(
            inspector["history"]["observations"][0]["dispatch"],
            {"sequence": 3, "phase": "observation_delivery"},
        )
        self.assertEqual(
            inspector["history"]["observations"][1]["dispatch"],
            {"sequence": 6, "phase": "observation_delivery"},
        )
        self.assertEqual(
            inspector["history"]["action_results"][0]["dispatch"],
            {"sequence": 4, "phase": "decision"},
        )
        self.assertEqual(
            inspector["history"]["action_results"][1]["dispatch"],
            {"sequence": 5, "phase": "action_completion"},
        )
        self.assertEqual(
            inspector["history"]["understanding_transitions"][0]["dispatch"],
            {"sequence": 7, "phase": "understanding_update"},
        )

    def test_harness_choice_becomes_private_evidence_and_resolved_wait(self):
        client = _SequenceClient(
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause at home before the morning shift",
                "decision_reason": "the available information supports waiting",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after completing a rest period",
                "decision_reason": "the completed rest leaves no immediate task",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after reading the home bulletin",
                "decision_reason": "the delivery does not require immediate travel",
            },
        )
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id="deterministic-autonomous-day-test",
            ),
        )
        summary = day.run()

        self.assertTrue(summary.reached_end_boundary)
        self.assertEqual(len(client.inputs), 3)
        self.assertEqual(
            client.inputs[0]["action_contract"]["supported_kinds"],
            ["household", "travel", "wait"],
        )
        self.assertEqual(
            client.inputs[0]["action_contract"]["currently_applicable_kinds"],
            ["household", "travel", "wait"],
        )
        self.assertEqual(
            [event.kind for event in day.events if event.actor_id == MARA_ID],
            [
                "action_attempted",
                "rest_completed",
                "action_attempted",
                "wait_completed",
                "action_attempted",
                "wait_completed",
            ],
        )
        mara = day.world.agents[MARA_ID]
        self.assertEqual(
            [attempt.kind for attempt in mara.action_history],
            ["wait", "wait", "wait"],
        )
        self.assertEqual(
            [result.status for result in mara.action_results],
            ["completed", "completed", "completed"],
        )
        self.assertEqual(
            [record.status for record in day.private_decision_records],
            ["selected", "selected", "selected"],
        )
        self.assertTrue(
            all(
                record.validation_status == "accepted"
                and record.resolution_status == "completed"
                and record.action_id is not None
                and record.outcome_event_id is not None
                for record in day.private_decision_records
            )
        )
        self.assertGreater(day.private_decision_records_bytes, 0)
        self.assertNotIn("institution_records", client.inputs[2])
        self.assertEqual(
            client.inputs[2]["delivered_observations"][0]["details"]["current_status"],
            "reduced",
        )
        model_path = autonomous_day_inspector_data(day, summary)["model_path"]
        self.assertEqual(
            {
                key: model_path[key]
                for key in (
                    "configured",
                    "exercised",
                    "decision_status_counts",
                    "provider_failure_count",
                )
            },
            {
                "configured": True,
                "exercised": True,
                "decision_status_counts": {"selected": 3},
                "provider_failure_count": 0,
            },
        )
        self.assertEqual(
            model_path["growth"],
            {
                "peak_restricted_input_bytes": max(
                    record.model_input_bytes
                    for record in day.private_decision_records
                ),
                "maximum_restricted_input_bytes": (
                    MAX_RESTRICTED_DECISION_INPUT_BYTES
                ),
                "retained_private_record_count": 3,
                "peak_retained_private_record_bytes": (
                    day.peak_retained_private_decision_records_bytes
                ),
                "maximum_retained_private_record_bytes": (
                    MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES
                ),
                "peak_context_counts": {
                    "decision_history": {
                        "attempts_included": 2,
                        "results_included": 2,
                        "continuity_requirements_included": 0,
                        "active_continuity_requirements": 0,
                        "total_attempts": 2,
                        "total_results": 2,
                        "omitted_attempts": 0,
                        "omitted_results": 0,
                    },
                    "peak_delivered_observation_count": 1,
                    "understanding": {
                        "beliefs": 0,
                        "memory_traces": 1,
                        "interpreted_claims": 1,
                        "contextual_stance_present": 0,
                    },
                },
            },
        )
        self.assertGreater(
            model_path["growth"]["peak_retained_private_record_bytes"],
            day.private_decision_records_bytes - 1,
        )
        self.assertNotIn("model_input", model_path["growth"])
        self.assertNotIn("private_decision_records", model_path["growth"])
        self.assertNotIn("delivered_observations", model_path["growth"])
        self.assertNotIn("model_input", model_path)
        self.assertNotIn("private_decision_records", model_path)

    def test_completed_rest_dispatches_later_action_result_decision(self):
        client = _SequenceClient(
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "rest at home before leaving",
                "decision_reason": "the scheduled wake allows a quiet interval",
            },
            {
                "kind": "travel",
                "parameters": {"destination": "workplace"},
                "explanation": "leave home after resting",
                "decision_reason": "the workplace is reachable after rest",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after arriving",
                "decision_reason": "arrival creates a new decision opportunity",
            },
        )
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id="deterministic-autonomous-day-rest-test",
            ),
        )
        dispatched = []
        original_handler = day.runtime._decision_handler
        self.assertIsNotNone(original_handler)

        def capture_decision(decision, context):
            if decision.actor_id == MARA_ID:
                dispatched.append(decision)
            original_handler(decision, context)

        day.runtime._decision_handler = capture_decision

        summary = day.run()

        self.assertTrue(summary.reached_end_boundary)
        rest_completed = next(
            event for event in day.events if event.kind == "rest_completed"
        )
        self.assertEqual(rest_completed.tick, 480)
        self.assertEqual(rest_completed.details["duration_minutes"], 60)
        self.assertEqual(rest_completed.caused_by, ("event-0001",))
        self.assertEqual(client.inputs[1]["tick"], 480)
        self.assertEqual(client.inputs[1]["state"]["location"], "home")
        self.assertEqual(
            dispatched[1].triggers,
            (
                DecisionTrigger(
                    kind=DecisionTriggerKind.ACTION_RESULT,
                    source_id=rest_completed.event_id,
                ),
            ),
        )
        self.assertEqual(
            [
                (item.phase, item.kind)
                for item in summary.executed_work
                if item.due_time.total_minutes == 480
            ],
            [
                ("scheduled_world", "autonomous_day_supporting_work_start"),
                ("action_completion", "autonomous_day_mara_rest_completion"),
                ("decision", "decision_eligibility"),
            ],
        )

    def test_safe_failure_wait_does_not_become_rest(self):
        client = _SequenceClient(
            TimeoutError("unavailable provider"),
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the retry succeeds",
                "decision_reason": "there is no immediate movement to make",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after reading the home bulletin",
                "decision_reason": "the delivered status does not require travel",
            },
        )
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id="deterministic-autonomous-day-failure-test",
            ),
        )
        dispatched = []
        original_handler = day.runtime._decision_handler
        self.assertIsNotNone(original_handler)

        def capture_decision(decision, context):
            if decision.actor_id == MARA_ID:
                dispatched.append(decision)
            original_handler(decision, context)

        day.runtime._decision_handler = capture_decision

        summary = day.run()

        self.assertTrue(summary.reached_end_boundary)
        self.assertEqual(len(client.inputs), 3)
        self.assertEqual([model_input["tick"] for model_input in client.inputs], [420, 450, 660])
        self.assertEqual(
            [event.kind for event in day.events if event.actor_id == MARA_ID],
            [
                "action_attempted",
                "wait_completed",
                "action_attempted",
                "wait_completed",
                "action_attempted",
                "wait_completed",
            ],
        )
        self.assertFalse(any(event.kind == "rest_completed" for event in day.events))
        self.assertEqual(
            [record.status for record in day.private_decision_records],
            ["failed", "selected", "selected"],
        )
        self.assertEqual(
            autonomous_day_inspector_data(day, summary)["model_path"][
                "decision_status_counts"
            ],
            {"failed": 1, "selected": 2},
        )
        self.assertEqual(
            autonomous_day_inspector_data(day, summary)["model_path"][
                "provider_failure_count"
            ],
            1,
        )
        self.assertEqual(
            dispatched[1].triggers,
            (
                DecisionTrigger(
                    kind=DecisionTriggerKind.SAFE_FAILURE_RETRY,
                    source_id="model-decision-mara-vale-0420",
                ),
            ),
        )
        self.assertEqual(
            summary.to_data()["decision_counts_by_actor"],
            {ILAN_ID: 1, MARA_ID: 3},
        )

    def test_inspector_provider_failure_count_excludes_pre_client_failures(self):
        def incomplete_projection(view):
            model_input = model_input_from_view(view)
            continuity_projection = dict(model_input["continuity_projection"])
            continuity_projection["complete"] = False
            model_input["continuity_projection"] = continuity_projection
            return model_input

        client = _SequenceClient(
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "this response must not be used",
                "decision_reason": "continuity failure precedes this client",
            }
        )
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id="deterministic-autonomous-day-pre-client-failure",
            ),
        )

        with patch(
            "policies.model_focal_policy.model_input_from_view",
            side_effect=incomplete_projection,
        ):
            summary = day.run()

        self.assertTrue(summary.reached_end_boundary)
        self.assertEqual(client.inputs, [])
        self.assertTrue(day.private_decision_records)
        self.assertTrue(
            all(
                record.status == "failed"
                and not record.provider_call_attempted
                and record.failure_kind == "continuity_projection_incomplete"
                for record in day.private_decision_records
            )
        )
        model_path = autonomous_day_inspector_data(day, summary)["model_path"]
        self.assertGreater(model_path["decision_status_counts"]["failed"], 0)
        self.assertEqual(model_path["provider_failure_count"], 0)

        integrity_key = b"autonomous-day-pre-client-failure"
        archive = RecordedDecisionArchive.seal(
            day.private_decision_records,
            integrity_key=integrity_key,
        )
        replay = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_recorded_archive(
                archive,
                integrity_key=integrity_key,
            ),
        )
        with patch(
            "policies.model_focal_policy.model_input_from_view",
            side_effect=incomplete_projection,
        ):
            replay_summary = replay.run()

        self.assertTrue(replay_summary.reached_end_boundary)
        self.assertEqual(
            [
                record.provider_call_attempted
                for record in replay.private_decision_records
            ],
            [
                record.provider_call_attempted
                for record in day.private_decision_records
            ],
        )
        self.assertEqual(
            autonomous_day_inspector_data(replay, replay_summary)["model_path"][
                "provider_failure_count"
            ],
            0,
        )

    def test_inspector_provider_failure_count_excludes_oversized_ollama_input(self):
        class _TransportMustNotBeCalled:
            def post_json(self, **_call):
                raise AssertionError("oversized input must not reach transport")

        client = OllamaDecisionClient(
            base_url="http://10.255.255.1:11434",
            model="qwen3:4b-instruct",
            transport=_TransportMustNotBeCalled(),
        )
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id=client.configuration_id,
                authorship_identity=client.authorship_identity,
            ),
        )
        day.world.agents[MARA_ID].aim = "x" * MAX_RESTRICTED_DECISION_INPUT_BYTES

        summary = day.run()

        self.assertTrue(summary.reached_end_boundary)
        model_path = autonomous_day_inspector_data(day, summary)["model_path"]
        self.assertGreater(model_path["decision_status_counts"]["failed"], 0)
        self.assertEqual(model_path["provider_failure_count"], 0)
        self.assertTrue(
            all(
                record.failure_kind == "restricted_input_too_large"
                and not record.provider_call_attempted
                for record in day.private_decision_records
            )
        )

    def test_completed_travel_dispatches_action_result_decision(self):
        client = _SequenceClient(
            {
                "kind": "travel",
                "parameters": {"destination": "workplace"},
                "explanation": "leave home for the workplace",
                "decision_reason": "the authored work obligation is nearby",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after arriving at the workplace",
                "decision_reason": "arrival creates a new decision opportunity",
            },
        )
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id="deterministic-autonomous-day-test",
            ),
        )
        dispatched = []
        original_handler = day.runtime._decision_handler
        self.assertIsNotNone(original_handler)

        def capture_decision(decision, context):
            if decision.actor_id == MARA_ID:
                dispatched.append(decision)
            original_handler(decision, context)

        day.runtime._decision_handler = capture_decision

        summary = day.run()

        self.assertTrue(summary.reached_end_boundary)
        self.assertEqual(len(client.inputs), 2)
        self.assertEqual(client.inputs[1]["tick"], 450)
        self.assertEqual(client.inputs[1]["state"]["location"], "workplace")
        self.assertEqual(day.world.agents[MARA_ID].location, "workplace")
        self.assertEqual(day.world.agents[MARA_ID].observations, [])
        self.assertEqual(
            [event.kind for event in day.events if event.actor_id == MARA_ID],
            [
                "action_attempted",
                "travel_completed",
                "action_attempted",
                "wait_completed",
            ],
        )
        travel_completed = next(
            event for event in day.events if event.kind == "travel_completed"
        )
        action_result_work = next(
            item
            for item in summary.executed_work
            if item.due_time.total_minutes == 450
            and item.kind == "decision_eligibility"
        )
        self.assertEqual(travel_completed.tick, 450)
        self.assertEqual(action_result_work.phase, "decision")
        self.assertEqual(
            [result.action_kind for result in day.world.agents[MARA_ID].action_results],
            ["travel", "wait"],
        )
        self.assertEqual(len(dispatched), 2)
        self.assertEqual(
            dispatched[1].triggers,
            (
                DecisionTrigger(
                    kind=DecisionTriggerKind.ACTION_RESULT,
                    source_id=travel_completed.event_id,
                ),
            ),
        )
        self.assertEqual(
            summary.to_data()["decision_counts_by_actor"],
            {ILAN_ID: 1, MARA_ID: 2},
        )

    def test_workplace_work_completes_after_model_selected_travel(self):
        client = _SequenceClient(
            {
                "kind": "travel",
                "parameters": {"destination": "workplace"},
                "explanation": "leave home for the morning shift",
                "decision_reason": "the workplace obligation is reachable",
            },
            {
                "kind": "work",
                "parameters": {},
                "explanation": "begin the available ledger shift",
                "decision_reason": "arriving at the workplace makes work possible",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the shift concludes",
                "decision_reason": "the completed work creates no further obligation",
            },
        )
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id="deterministic-autonomous-day-work-test",
            ),
        )
        dispatched = []
        original_handler = day.runtime._decision_handler
        self.assertIsNotNone(original_handler)

        def capture_decision(decision, context):
            if decision.actor_id == MARA_ID:
                dispatched.append(decision)
            original_handler(decision, context)

        day.runtime._decision_handler = capture_decision

        summary = day.run()

        self.assertTrue(summary.reached_end_boundary)
        self.assertEqual([model_input["tick"] for model_input in client.inputs], [420, 450, 570])
        self.assertEqual(
            client.inputs[1]["action_contract"]["supported_kinds"],
            ["travel", "work", "wait"],
        )
        self.assertEqual(
            client.inputs[1]["action_contract"]["currently_applicable_kinds"],
            ["travel", "work", "wait"],
        )
        work_completed = next(
            event
            for event in day.events
            if event.kind == "work_completed" and event.actor_id == MARA_ID
        )
        self.assertEqual(work_completed.tick, 570)
        self.assertEqual(work_completed.details["duration_minutes"], 120)
        self.assertEqual(
            [result.action_kind for result in day.world.agents[MARA_ID].action_results],
            ["travel", "work", "wait"],
        )
        self.assertEqual(
            dispatched[2].triggers,
            (
                DecisionTrigger(
                    kind=DecisionTriggerKind.ACTION_RESULT,
                    source_id=work_completed.event_id,
                ),
            ),
        )

    def test_completed_work_requirement_carries_exact_action_then_clears(
        self,
    ):
        client = _SequenceClient(
            {
                "kind": "travel",
                "parameters": {"destination": "workplace"},
                "explanation": "leave home for the morning shift",
                "decision_reason": "the workplace obligation is reachable",
            },
            {
                "kind": "work",
                "parameters": {},
                "explanation": "complete the available workplace shift",
                "decision_reason": "arriving at the workplace makes work possible",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the completed shift",
                "decision_reason": "the fulfilled shift needs no immediate action",
            },
        )
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id="autonomous-day-work-result-relevance-test",
            ),
        )

        day.run()

        work_result = next(
            result
            for result in day.world.agents[MARA_ID].action_results
            if result.action_kind == "work"
        )
        following_input = client.inputs[2]
        following_history = following_input["decision_history"]

        self.assertEqual(
            following_input["state"]["obligations"],
            ["household time"],
        )
        self.assertEqual(
            day.world.agents[MARA_ID].continuity_requirements,
            (),
        )
        self.assertEqual(
            following_history["projection"]["explicit_relevant_actions"],
            1,
        )
        self.assertEqual(
            following_history["projection"]["included_explicit_relevant_actions"],
            1,
        )
        self.assertIn(
            work_result.action_id,
            [result["action_id"] for result in following_history["results"]],
        )
        requirement = following_history["continuity_requirements"][0]
        self.assertEqual(requirement["reason"], "fulfilled_obligation")
        self.assertEqual(
            requirement["lifecycle"], "through_selected_decision"
        )
        self.assertEqual(requirement["attempt"]["action_id"], work_result.action_id)
        self.assertEqual(requirement["attempt"]["kind"], "work")
        self.assertEqual(requirement["result"]["action_id"], work_result.action_id)
        self.assertEqual(
            requirement["canonical_state"],
            {"field": "obligations", "removed_value": "workplace shift"},
        )

    def test_completed_work_requirement_survives_failure_retry_then_clears(self):
        client = _SequenceClient(
            {
                "kind": "travel",
                "parameters": {"destination": "workplace"},
                "explanation": "leave home for the morning shift",
                "decision_reason": "the workplace obligation is reachable",
            },
            {
                "kind": "work",
                "parameters": {},
                "explanation": "complete the available workplace shift",
                "decision_reason": "arriving at the workplace makes work possible",
            },
            TimeoutError("provider unavailable after the fulfillment result"),
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the retry",
                "decision_reason": "the fulfilled shift needs no immediate action",
            },
        )
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id="autonomous-day-work-result-retry-relevance-test",
            ),
        )

        day.run()

        work_result = next(
            result
            for result in day.world.agents[MARA_ID].action_results
            if result.action_kind == "work"
        )
        for model_input in (client.inputs[2], client.inputs[3]):
            history = model_input["decision_history"]
            projection = history["projection"]
            self.assertEqual(projection["explicit_relevant_actions"], 1)
            self.assertEqual(projection["included_explicit_relevant_actions"], 1)
            self.assertIn(
                work_result.action_id,
                [
                    result["action_id"]
                    for result in history["results"]
                ],
            )
            self.assertEqual(
                history["continuity_requirements"][0]["attempt"]["action_id"],
                work_result.action_id,
            )
            self.assertEqual(
                history["continuity_requirements"][0]["result"]["action_id"],
                work_result.action_id,
            )
        self.assertEqual(
            day.world.agents[MARA_ID].continuity_requirements,
            (),
        )

    def test_repeated_work_after_fulfillment_does_not_add_a_relevance_requirement(self):
        client = _SequenceClient(
            {
                "kind": "travel",
                "parameters": {"destination": "workplace"},
                "explanation": "leave home for the morning shift",
                "decision_reason": "the workplace obligation is reachable",
            },
            {
                "kind": "work",
                "parameters": {},
                "explanation": "complete the available workplace shift",
                "decision_reason": "arriving at the workplace makes work possible",
            },
            {
                "kind": "work",
                "parameters": {},
                "explanation": "continue working after the shift",
                "decision_reason": "work remains physically available",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the additional work",
                "decision_reason": "no further obligation changed",
            },
        )
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id="autonomous-day-repeated-work-relevance-test",
            ),
        )

        day.run()

        work_results = [
            result
            for result in day.world.agents[MARA_ID].action_results
            if result.action_kind == "work"
        ]
        consumed_history = client.inputs[2]["decision_history"]
        following_history = client.inputs[3]["decision_history"]

        self.assertEqual(len(work_results), 2)
        self.assertEqual(
            day.world.agents[MARA_ID].continuity_requirements,
            (),
        )
        self.assertEqual(
            consumed_history["projection"]["explicit_relevant_actions"],
            1,
        )
        self.assertIn(
            work_results[0].action_id,
            [result["action_id"] for result in consumed_history["results"]],
        )
        self.assertEqual(
            following_history["projection"]["explicit_relevant_actions"],
            0,
        )

    def test_completed_household_requirement_carries_exact_action_then_clears(
        self,
    ):
        client = _SequenceClient(
            {
                "kind": "household",
                "parameters": {},
                "explanation": "complete the household obligation at home",
                "decision_reason": "household time is available at home",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the household activity",
                "decision_reason": "the household obligation is fulfilled",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the bulletin",
                "decision_reason": "no new obligation is available",
            },
        )
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id="autonomous-day-household-result-relevance-test",
            ),
        )

        day.run()

        household_result = next(
            result
            for result in day.world.agents[MARA_ID].action_results
            if result.action_kind == "household"
        )
        following_input = client.inputs[1]
        following_history = following_input["decision_history"]

        self.assertEqual(following_input["state"]["obligations"], ["workplace shift"])
        self.assertEqual(
            day.world.agents[MARA_ID].continuity_requirements,
            (),
        )
        self.assertEqual(
            following_history["projection"]["explicit_relevant_actions"],
            1,
        )
        self.assertEqual(
            following_history["projection"]["included_explicit_relevant_actions"],
            1,
        )
        self.assertIn(
            household_result.action_id,
            [result["action_id"] for result in following_history["results"]],
        )
        requirement = following_history["continuity_requirements"][0]
        self.assertEqual(requirement["attempt"]["action_id"], household_result.action_id)
        self.assertEqual(requirement["attempt"]["kind"], "household")
        self.assertEqual(
            requirement["result"]["action_id"], household_result.action_id
        )
        self.assertEqual(
            requirement["canonical_state"],
            {"field": "obligations", "removed_value": "household time"},
        )

    def test_repeated_household_after_fulfillment_does_not_add_a_relevance_requirement(
        self,
    ):
        client = _SequenceClient(
            {
                "kind": "household",
                "parameters": {},
                "explanation": "complete the household obligation at home",
                "decision_reason": "household time is available at home",
            },
            {
                "kind": "household",
                "parameters": {},
                "explanation": "continue household activity after it is fulfilled",
                "decision_reason": "household activity remains physically available",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the additional household activity",
                "decision_reason": "no further obligation changed",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the bulletin",
                "decision_reason": "no new obligation is available",
            },
        )
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id="autonomous-day-repeated-household-relevance-test",
            ),
        )

        day.run()

        household_results = [
            result
            for result in day.world.agents[MARA_ID].action_results
            if result.action_kind == "household"
        ]
        consumed_history = client.inputs[1]["decision_history"]
        following_history = client.inputs[2]["decision_history"]

        self.assertEqual(len(household_results), 2)
        self.assertEqual(
            day.world.agents[MARA_ID].continuity_requirements,
            (),
        )
        self.assertEqual(
            consumed_history["projection"]["explicit_relevant_actions"],
            1,
        )
        self.assertEqual(
            consumed_history["projection"]["included_explicit_relevant_actions"],
            1,
        )
        self.assertIn(
            household_results[0].action_id,
            [result["action_id"] for result in consumed_history["results"]],
        )
        self.assertEqual(
            following_history["projection"]["explicit_relevant_actions"],
            0,
        )
        print("focused AD-7 continuity verification passed")

    def test_model_action_completing_at_day_end_does_not_dispatch_again(self):
        class _RepeatingHouseholdClient:
            def __init__(self):
                self.inputs = []

            def choose(self, model_input):
                self.inputs.append(model_input)
                return {
                    "kind": "household",
                    "parameters": {},
                    "explanation": "continue ordinary household activity",
                    "decision_reason": "household activity remains available",
                }

        client = _RepeatingHouseholdClient()
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id="exact-boundary-action-completion-test",
            ),
        )

        summary = day.run()

        self.assertTrue(summary.reached_end_boundary)
        self.assertIsNone(summary.runtime_failure)
        self.assertEqual(day.world.tick, 1440)
        self.assertEqual(
            day.world.agents[MARA_ID].action_results[-1].resolved_tick,
            1440,
        )
        self.assertNotIn(1440, [model_input["tick"] for model_input in client.inputs])
        self.assertNotIn(
            1440,
            [record.tick for record in day.private_decision_records],
        )

    def test_home_household_activity_completes_after_model_selection(self):
        client = _SequenceClient(
            {
                "kind": "household",
                "parameters": {},
                "explanation": "complete a basic task at home",
                "decision_reason": "household time is available before leaving",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the household task",
                "decision_reason": "the completed task needs no immediate follow-up",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "wait after the accessible bulletin",
                "decision_reason": "the delivered status needs no immediate action",
            },
        )
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id="deterministic-autonomous-day-household-test",
            ),
        )
        dispatched = []
        original_handler = day.runtime._decision_handler
        self.assertIsNotNone(original_handler)

        def capture_decision(decision, context):
            if decision.actor_id == MARA_ID:
                dispatched.append(decision)
            original_handler(decision, context)

        day.runtime._decision_handler = capture_decision
        summary = day.run()

        self.assertTrue(summary.reached_end_boundary)
        self.assertEqual([model_input["tick"] for model_input in client.inputs], [420, 480, 660])
        self.assertEqual(
            client.inputs[0]["action_contract"]["supported_kinds"],
            ["household", "travel", "wait"],
        )
        household_completed = next(
            event for event in day.events if event.kind == "household_time_completed"
        )
        self.assertEqual(household_completed.tick, 480)
        self.assertEqual(household_completed.details["duration_minutes"], 60)
        self.assertEqual(
            [result.action_kind for result in day.world.agents[MARA_ID].action_results],
            ["household", "wait", "wait"],
        )
        self.assertEqual(
            dispatched[1].triggers,
            (
                DecisionTrigger(
                    kind=DecisionTriggerKind.ACTION_RESULT,
                    source_id=household_completed.event_id,
                ),
            ),
        )
        normal_output = render_autonomous_day(day, summary)
        self.assertIn("Day 0 08:00 | Mara completed household time.", normal_output)
        self.assertNotIn("decision_reason", normal_output)
        self.assertNotIn("Ilan", normal_output)
        self.assertNotIn("event-", normal_output)

    def test_normal_output_preserves_same_minute_focal_causal_order(self):
        client = _SequenceClient(
            {
                "kind": "travel",
                "parameters": {"destination": "workplace"},
                "explanation": "leave home for the workplace",
                "decision_reason": "the workplace is reachable",
            },
            {
                "kind": "work",
                "parameters": {},
                "explanation": "complete the workplace obligation",
                "decision_reason": "work is available here",
            },
            {
                "kind": "travel",
                "parameters": {"destination": "home"},
                "explanation": "return home after work",
                "decision_reason": "home is reachable",
            },
            {
                "kind": "household",
                "parameters": {},
                "explanation": "complete household time at home",
                "decision_reason": "household time is available here",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the completed activity",
                "decision_reason": "no immediate action is needed",
            },
        )
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id="deterministic-autonomous-day-order-test",
            ),
        )

        summary = day.run()
        normal_output = render_autonomous_day(day, summary)

        household_update = "Day 0 11:00 | Mara completed household time."
        bulletin_update = "Day 0 11:00 | Home transit bulletin"
        self.assertIn(household_update, normal_output)
        self.assertIn(bulletin_update, normal_output)
        self.assertLess(normal_output.index(household_update), normal_output.index(bulletin_update))

        inspector = autonomous_day_inspector_data(day, summary)
        household_result = next(
            result
            for result in inspector["history"]["action_results"]
            if result["action_kind"] == "household"
        )
        bulletin = next(
            observation
            for observation in inspector["history"]["observations"]
            if observation["agent_id"] == MARA_ID
        )
        self.assertEqual(household_result["resolved_tick"], bulletin["delivery_tick"])
        self.assertEqual(
            household_result["dispatch"]["phase"], "action_completion"
        )
        self.assertEqual(bulletin["dispatch"]["phase"], "observation_delivery")
        self.assertLess(
            household_result["dispatch"]["sequence"],
            bulletin["dispatch"]["sequence"],
        )

    def test_focal_update_sorting_uses_causal_phase_not_input_position(self):
        simultaneous_updates = [
            (
                SimulatedTime(660),
                int(TemporalPhase.OBSERVATION_DELIVERY),
                0,
                "delivery",
            ),
            (
                SimulatedTime(660),
                int(TemporalPhase.ACTION_COMPLETION),
                99,
                "completion",
            ),
        ]

        ordered_labels = [
            update[-1]
            for update in sorted(simultaneous_updates, key=_focal_update_sort_key)
        ]

        self.assertEqual(ordered_labels, ["completion", "delivery"])

    def test_two_equal_seed_model_days_match_complete_evidence_and_growth_limits(
        self,
    ):
        responses = (
            {
                "kind": "travel",
                "parameters": {"destination": "workplace"},
                "explanation": "leave home for the workplace",
                "decision_reason": "the workplace is reachable",
            },
            {
                "kind": "work",
                "parameters": {},
                "explanation": "complete the workplace obligation",
                "decision_reason": "work is available at the workplace",
            },
            {
                "kind": "travel",
                "parameters": {"destination": "home"},
                "explanation": "return home after workplace work",
                "decision_reason": "home is reachable from the workplace",
            },
            {
                "kind": "household",
                "parameters": {},
                "explanation": "complete household time at home",
                "decision_reason": "household time is available at home",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the completed household activity",
                "decision_reason": "no immediate action is required",
            },
        )
        first_client = _SequenceClient(*responses)
        second_client = _SequenceClient(*responses)
        first = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                first_client,
                configuration_id="deterministic-autonomous-day-offline-proof",
            ),
        )
        second = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                second_client,
                configuration_id="deterministic-autonomous-day-offline-proof",
            ),
        )

        first_summary = first.run()
        second_summary = second.run()

        self.assertTrue(first_summary.reached_end_boundary)
        self.assertTrue(second_summary.reached_end_boundary)
        self.assertEqual(len(first_client.inputs), 5)
        self.assertEqual(second_client.inputs, first_client.inputs)
        requirement_counts = [
            model_input["decision_history"]["projection"][
                "explicit_relevant_actions"
            ]
            for model_input in first_client.inputs
        ]
        self.assertEqual(requirement_counts, [0, 0, 1, 0, 1])
        self.assertTrue(
            all(
                model_input["decision_history"]["projection"]["complete"]
                for model_input in first_client.inputs
            )
        )
        self.assertEqual(first.world.agents[MARA_ID].continuity_requirements, ())
        self.assertEqual(second.world.agents[MARA_ID].continuity_requirements, ())
        growth = autonomous_day_inspector_data(first, first_summary)["model_path"][
            "growth"
        ]
        self.assertEqual(
            growth["peak_context_counts"]["decision_history"][
                "active_continuity_requirements"
            ],
            1,
        )
        self.assertEqual(
            growth["peak_context_counts"]["decision_history"][
                "continuity_requirements_included"
            ],
            1,
        )
        self.assertEqual(second_summary.to_data(), first_summary.to_data())
        self.assertEqual(second.events, first.events)
        self.assertEqual(second.observations, first.observations)
        self.assertEqual(
            second.private_decision_records,
            first.private_decision_records,
        )
        self.assertEqual(
            autonomous_day_inspector_data(second, second_summary),
            autonomous_day_inspector_data(first, first_summary),
        )
        self.assertEqual(
            first_summary.to_data()["decision_counts_by_actor"][MARA_ID],
            len(first.private_decision_records),
        )
        self.assertLessEqual(
            len(first.private_decision_records),
            128,
        )
        self.assertTrue(
            all(
                record.model_input_bytes <= MAX_RESTRICTED_DECISION_INPUT_BYTES
                for record in first.private_decision_records
            )
        )
        self.assertLessEqual(
            first.peak_retained_private_decision_records_bytes,
            MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES,
        )
        print("deterministic full-day model growth verification passed")

    def test_scheduled_wake_dispatches_one_restricted_mara_decision(self):
        dispatched = []
        day = build_autonomous_day(
            seed=42,
            on_mara_decision=lambda decision, view: dispatched.append(
                (decision, view)
            ),
        )

        summary = day.run()

        self.assertTrue(summary.reached_end_boundary)
        self.assertEqual(len(dispatched), 2)
        decision, view = dispatched[0]
        self.assertEqual(decision.actor_id, MARA_ID)
        self.assertEqual(decision.due_time.total_minutes, 7 * 60)
        self.assertEqual(
            decision.triggers[0].kind,
            DecisionTriggerKind.SCHEDULED_WAKE,
        )
        self.assertEqual(
            decision.triggers[0].source_id,
            "autonomous-day-mara-morning-wake",
        )
        self.assertEqual(view.tick, 7 * 60)
        self.assertEqual(view.agent_id, MARA_ID)
        self.assertEqual(view.location, "home")
        self.assertEqual(view.observations, ())
        self.assertEqual(view.reachable_destinations, ("workplace",))
        self.assertFalse(hasattr(view, "institution"))
        self.assertFalse(hasattr(view, "world"))
        self.assertEqual(
            [item.kind for item in summary.executed_work[:1]],
            ["decision_eligibility"],
        )
        self.assertEqual(
            summary.to_data()["decision_counts_by_actor"],
            {ILAN_ID: 1, MARA_ID: 2},
        )

    def test_successor_mara_view_copies_world_owned_continuity_requirements(self):
        dispatched = []
        day = build_autonomous_day(
            seed=42,
            on_mara_decision=lambda decision, view: dispatched.append(
                (decision, view)
            ),
        )
        prior_attempt = ActionAttempt(
            actor_id=MARA_ID,
            kind="work",
            parameters={},
            explanation="complete a prior shift",
        )
        prior_result = ActionResult(
            action_id="action-mara-prior-work",
            attempt_event_id="event-mara-prior-work-attempt",
            outcome_event_id="event-mara-prior-work-result",
            actor_id=MARA_ID,
            action_kind="work",
            status="completed",
            resolved_tick=1,
        )
        mara = day.world.agents[MARA_ID]
        mara.action_history.append(prior_attempt)
        mara.action_results.append(prior_result)
        mara.continuity_requirements = (
            ActionContinuityRequirement(
                requirement_id="continuity-action-mara-prior-work",
                action_id=prior_result.action_id,
                attempt_event_id=prior_result.attempt_event_id,
                action_history_index=0,
                attempt=prior_attempt,
                result=prior_result,
                reason="fulfilled_obligation",
                state_field="obligations",
                state_value="workplace shift",
                lifecycle="through_selected_decision",
            ),
        )

        day.run()

        self.assertEqual(
            dispatched[0][1].continuity_requirements,
            mara.continuity_requirements,
        )

    def test_accessible_bulletin_dispatches_one_restricted_mara_decision(self):
        dispatched = []
        day = build_autonomous_day(
            seed=42,
            on_mara_decision=lambda decision, view: dispatched.append(
                (decision, view)
            ),
        )

        summary = day.run()

        self.assertTrue(summary.reached_end_boundary)
        self.assertEqual(len(dispatched), 2)
        decision, view = dispatched[1]
        bulletin = next(
            observation
            for observation in day.observations
            if observation.agent_id == MARA_ID
        )
        self.assertEqual(decision.actor_id, MARA_ID)
        self.assertEqual(decision.due_time.total_minutes, bulletin.delivery_tick)
        self.assertEqual(
            decision.triggers[0].kind,
            DecisionTriggerKind.OBSERVATION_DELIVERED,
        )
        self.assertEqual(decision.triggers[0].source_id, bulletin.observation_id)
        self.assertEqual(view.tick, bulletin.delivery_tick)
        self.assertEqual(view.agent_id, MARA_ID)
        self.assertEqual(view.observations, (bulletin,))
        self.assertFalse(hasattr(view, "institution"))
        self.assertFalse(hasattr(view, "world"))
        model_input = model_input_from_view(view)
        self.assertEqual(
            model_input["delivered_observations"][0]["observation_id"],
            bulletin.observation_id,
        )
        self.assertNotIn("institution_records", model_input)
        self.assertEqual(
            [item.kind for item in summary.executed_work[-3:]],
            [
                "autonomous_day_transit_bulletin_delivery",
                "autonomous_day_mara_transit_understanding_update",
                "decision_eligibility",
            ],
        )
        self.assertEqual(
            summary.to_data()["decision_counts_by_actor"],
            {ILAN_ID: 1, MARA_ID: 2},
        )

    def test_home_transit_bulletin_updates_source_linked_understanding_before_decision(
        self,
    ):
        dispatched = []
        day = build_autonomous_day(
            seed=42,
            on_mara_decision=lambda decision, view: dispatched.append(
                (decision, view)
            ),
        )

        summary = day.run()

        bulletin = next(
            observation
            for observation in day.observations
            if observation.agent_id == MARA_ID
        )
        decision, view = dispatched[1]
        self.assertEqual(decision.due_time.total_minutes, 660)
        self.assertEqual(len(view.memory_traces), 1)
        trace = view.memory_traces[0]
        self.assertEqual(trace.source_observation_id, bulletin.observation_id)
        self.assertEqual(trace.source_event_id, bulletin.event_id)
        self.assertEqual(trace.delivery_tick, bulletin.delivery_tick)
        self.assertEqual(trace.proposition, "workplace-home tram service is reduced")
        self.assertEqual(len(view.interpreted_claims), 1)
        claim = view.interpreted_claims[0]
        self.assertEqual(claim.claim_id, trace.interpreted_claim_id)
        self.assertEqual(claim.origin_trace_id, trace.trace_id)
        self.assertEqual(
            [item.kind for item in summary.executed_work[-3:]],
            [
                "autonomous_day_transit_bulletin_delivery",
                "autonomous_day_mara_transit_understanding_update",
                "decision_eligibility",
            ],
        )

        mara = day.world.agents[MARA_ID]
        self.assertEqual(mara.memory_traces, view.memory_traces)
        self.assertEqual(mara.interpreted_claims, view.interpreted_claims)

    def test_inaccessible_transit_change_does_not_dispatch_mara_decision(self):
        dispatched = []
        day = build_autonomous_day(
            seed=42,
            on_mara_decision=lambda decision, view: dispatched.append(
                (decision, view)
            ),
        )
        day.world.agents[MARA_ID].location = "workplace"

        summary = day.run()

        self.assertTrue(summary.reached_end_boundary)
        self.assertEqual(len(dispatched), 1)
        self.assertEqual(
            dispatched[0][0].triggers[0].kind,
            DecisionTriggerKind.SCHEDULED_WAKE,
        )
        self.assertEqual(
            [
                observation
                for observation in day.observations
                if observation.agent_id == MARA_ID
            ],
            [],
        )
        self.assertEqual(
            summary.to_data()["decision_counts_by_actor"],
            {ILAN_ID: 1, MARA_ID: 1},
        )

    def test_background_consequence_reaches_mara_only_through_home_bulletin(self):
        day = build_autonomous_day(seed=42)

        summary = day.run()

        self.assertTrue(summary.reached_end_boundary)
        self.assertTrue(day.runtime.is_complete)
        self.assertEqual(summary.current.total_minutes, 1440)
        self.assertEqual(day.world.tick, 1440)
        self.assertEqual(
            [(event.tick, event.kind, event.actor_id) for event in day.events],
            [
                (480, "action_attempted", ILAN_ID),
                (510, "transit_service_changed", "district-transit-authority"),
                (510, "action_attempted", ILAN_ID),
                (510, "wait_completed", ILAN_ID),
                (600, "work_completed", ILAN_ID),
            ],
        )
        work_attempted, transit_change, social_attempted, waited, completed = day.events
        self.assertEqual(completed.caused_by, (work_attempted.event_id,))
        self.assertEqual(completed.action_id, work_attempted.action_id)
        self.assertEqual(waited.caused_by, (social_attempted.event_id,))
        self.assertEqual(waited.action_id, social_attempted.action_id)
        self.assertEqual(transit_change.details["prior_status"], "normal")
        self.assertEqual(transit_change.details["current_status"], "reduced")
        self.assertEqual(day.world.institution.records["tram_service"], "reduced")

        ilan = day.world.agents[ILAN_ID]
        self.assertEqual(
            [attempt.kind for attempt in ilan.action_history],
            ["work", "wait"],
        )
        self.assertEqual(
            [result.action_kind for result in ilan.action_results],
            ["wait", "work"],
        )
        self.assertEqual(
            [result.status for result in ilan.action_results],
            ["completed", "completed"],
        )
        self.assertEqual(day.pending_action_count, 0)

        mara = day.world.agents[MARA_ID]
        self.assertEqual(mara.location, "home")
        self.assertEqual(mara.action_history, [])
        self.assertEqual(mara.action_results, [])
        self.assertEqual(len(mara.observations), 1)
        self.assertEqual(
            tuple(mara.observations),
            tuple(
                observation
                for observation in day.observations
                if observation.agent_id == MARA_ID
            ),
        )
        bulletin = mara.observations[0]
        self.assertEqual(bulletin.event_id, transit_change.event_id)
        self.assertEqual(bulletin.delivery_tick, 660)
        self.assertEqual(bulletin.source, "home transit bulletin receiver")
        self.assertEqual(bulletin.details["evidence_kind"], "transit_service_status")
        self.assertEqual(bulletin.details["current_status"], "reduced")
        self.assertEqual(
            summary.to_data()["decision_counts_by_actor"],
            {ILAN_ID: 1, MARA_ID: 0},
        )

    def test_transit_change_delivers_source_linked_evidence_only_to_ilan(self):
        day = build_autonomous_day(seed=42)

        summary = day.run()

        transit_change = next(
            event for event in day.events if event.kind == "transit_service_changed"
        )
        ilan = day.world.agents[ILAN_ID]
        self.assertEqual(len(ilan.observations), 1)
        observation = ilan.observations[0]
        self.assertEqual(observation.agent_id, ILAN_ID)
        self.assertEqual(observation.event_id, transit_change.event_id)
        self.assertEqual(observation.delivery_tick, transit_change.tick)
        self.assertEqual(observation.source, "workplace transit service terminal")
        self.assertEqual(
            dict(observation.details),
            {
                "evidence_kind": "transit_service_status",
                "route": "workplace-home",
                "current_status": "reduced",
                "proposition": "workplace-home tram service is reduced",
                "asserted_value": 1,
            },
        )
        self.assertIn(observation, day.observations)
        self.assertNotIn(observation, day.world.agents[MARA_ID].observations)

        inspector = autonomous_day_inspector_data(day, summary)
        inspector_observation = next(
            item
            for item in inspector["history"]["observations"]
            if item["observation_id"] == observation.observation_id
        )
        self.assertEqual(
            inspector_observation["dispatch"],
            {"sequence": 3, "phase": "observation_delivery"},
        )

    def test_ilan_observation_triggers_restricted_deterministic_choice(self):
        client = _SequenceClient(
            {
                "kind": "travel",
                "parameters": {"destination": "workplace"},
                "explanation": "travel to the workplace",
                "decision_reason": "the shift is due",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "wait at the workplace",
                "decision_reason": "arrival needs no further action",
            },
        )
        day = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                client,
                configuration_id="ilan-restricted-choice-test",
            ),
        )

        summary = day.run()

        ilan_observation = day.world.agents[ILAN_ID].observations[0]
        ilan_decisions = [
            decision
            for decision in summary.consumed_decisions
            if decision.actor_id == ILAN_ID
        ]
        self.assertEqual(len(ilan_decisions), 1)
        self.assertEqual(ilan_decisions[0].due_time, SimulatedTime(510))
        self.assertEqual(
            ilan_decisions[0].triggers,
            (
                DecisionTrigger(
                    kind=DecisionTriggerKind.OBSERVATION_DELIVERED,
                    source_id=ilan_observation.observation_id,
                ),
            ),
        )
        attempted = next(
            event
            for event in day.events
            if event.actor_id == ILAN_ID
            and event.kind == "action_attempted"
            and event.details["action_kind"] == "speak"
        )
        completed = next(
            event
            for event in day.events
            if event.actor_id == ILAN_ID and event.kind == "statement_completed"
        )
        self.assertEqual(completed.action_id, attempted.action_id)
        self.assertEqual(completed.caused_by, (attempted.event_id,))
        self.assertEqual(completed.details["recipient_id"], MARA_ID)
        self.assertEqual(
            completed.details["evidence_observation_id"],
            ilan_observation.observation_id,
        )
        self.assertEqual(
            completed.details["source_event_id"],
            ilan_observation.event_id,
        )
        statement_result = next(
            result
            for result in day.world.agents[ILAN_ID].action_results
            if result.action_kind == "speak"
        )
        self.assertEqual(statement_result.status, "completed")
        self.assertEqual(
            summary.to_data()["decision_counts_by_actor"],
            {ILAN_ID: 1, MARA_ID: 2},
        )
        self.assertEqual(day.world.agents[MARA_ID].observations, [])
        self.assertEqual(day.understanding_transitions, ())
        normal_output = render_autonomous_day(day, summary)
        for hidden in (
            "Ilan",
            "statement_completed",
            "workplace-home tram service is reduced",
            ilan_observation.observation_id,
            ilan_observation.event_id,
        ):
            self.assertNotIn(hidden, normal_output)

    def test_world_time_is_authoritative_during_successor_dispatch(self):
        day = build_autonomous_day(seed=42)
        observed: list[tuple[str, int, int]] = []
        original_record = day._event_log.record
        original_deliver = day._event_log.deliver

        def record(**values):
            observed.append(("event", values["tick"], day.world.tick))
            return original_record(**values)

        def deliver(**values):
            observed.append(
                ("observation", values["delivery_tick"], day.world.tick)
            )
            return original_deliver(**values)

        day._event_log.record = record
        day._event_log.deliver = deliver

        day.runtime.run()

        self.assertEqual(
            observed,
            [
                ("event", 480, 480),
                ("event", 510, 510),
                ("observation", 510, 510),
                ("event", 510, 510),
                ("event", 510, 510),
                ("event", 600, 600),
                ("observation", 660, 660),
            ],
        )
        self.assertEqual(day.world.tick, 1440)

    def test_transit_change_remains_undelivered_without_channel_access(self):
        day = build_autonomous_day(seed=42)
        day.world.agents[MARA_ID].location = "workplace"

        summary = day.run()

        self.assertTrue(summary.reached_end_boundary)
        self.assertEqual(day.world.tick, 1440)
        self.assertEqual(len(day.events), 5)
        self.assertEqual(day.world.institution.records["tram_service"], "reduced")
        self.assertEqual(
            [
                observation
                for observation in day.observations
                if observation.agent_id == MARA_ID
            ],
            [],
        )
        self.assertEqual(day.world.agents[MARA_ID].observations, [])
        self.assertEqual(
            summary.to_data()["decision_counts_by_actor"],
            {ILAN_ID: 1, MARA_ID: 0},
        )

    def test_equal_seed_builds_equal_ordered_world_evidence(self):
        first = build_autonomous_day(seed=7)
        second = build_autonomous_day(seed=7)

        first_summary = first.run().to_data()
        second_summary = second.run().to_data()

        self.assertEqual(first.events, second.events)
        self.assertEqual(first.observations, second.observations)
        self.assertEqual(first_summary, second_summary)
        self.assertEqual(first.world.institution.records, second.world.institution.records)
        self.assertEqual(
            first.world.agents[ILAN_ID].action_results,
            second.world.agents[ILAN_ID].action_results,
        )

    def test_recorded_decisions_replay_complete_autonomous_day_without_provider_calls(
        self,
    ):
        source_client = _SequenceClient(
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "rest at home after the scheduled wake",
                "decision_reason": "the morning begins with time to rest",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the completed rest",
                "decision_reason": "no further action is required immediately",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the accessible bulletin",
                "decision_reason": "the bulletin changes no immediate action",
            },
        )
        source = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                source_client,
                configuration_id="deterministic-autonomous-day-replay-source",
            ),
        )
        source_summary = source.run()
        source_record_count = len(source.private_decision_records)
        integrity_key = b"autonomous-day-replay-integrity-v1"
        archive = RecordedDecisionArchive.seal(
            source.private_decision_records,
            integrity_key=integrity_key,
        )

        replay = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_recorded_archive(
                archive,
                integrity_key=integrity_key,
            ),
        )
        replay_summary = replay.run()

        self.assertTrue(source_summary.reached_end_boundary)
        self.assertTrue(replay_summary.reached_end_boundary)
        self.assertEqual(len(source_client.inputs), source_record_count)
        self.assertEqual(replay_summary.to_data(), source_summary.to_data())
        self.assertEqual(replay.events, source.events)
        self.assertEqual(replay.observations, source.observations)
        self.assertEqual(
            autonomous_day_inspector_data(replay, replay_summary)["objective_state"],
            autonomous_day_inspector_data(source, source_summary)["objective_state"],
        )
        self.assertEqual(
            [record.model_input for record in replay.private_decision_records],
            [record.model_input for record in source.private_decision_records],
        )

    def test_recorded_safe_failure_decisions_replay_complete_autonomous_day_without_provider_calls(
        self,
    ):
        source_client = _SequenceClient(
            TimeoutError("provider unavailable"),
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the recorded retry",
                "decision_reason": "the retry made no immediate task available",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the accessible bulletin",
                "decision_reason": "the bulletin changes no immediate action",
            },
        )
        source = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                source_client,
                configuration_id="deterministic-autonomous-day-replay-failure-source",
            ),
        )
        source_summary = source.run()
        source_call_count = len(source_client.inputs)
        integrity_key = b"autonomous-day-replay-failure-integrity-v1"
        archive = RecordedDecisionArchive.seal(
            source.private_decision_records,
            integrity_key=integrity_key,
        )

        replay = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_recorded_archive(
                archive,
                integrity_key=integrity_key,
            ),
        )
        replay_summary = replay.run()

        self.assertTrue(source_summary.reached_end_boundary)
        self.assertTrue(replay_summary.reached_end_boundary)
        self.assertEqual(source_call_count, len(source.private_decision_records))
        self.assertEqual(len(source_client.inputs), source_call_count)
        self.assertEqual(replay_summary.to_data(), source_summary.to_data())
        self.assertEqual(replay.events, source.events)
        self.assertEqual(replay.observations, source.observations)
        replay_inspector = autonomous_day_inspector_data(replay, replay_summary)
        source_inspector = autonomous_day_inspector_data(source, source_summary)
        self.assertEqual(
            replay_inspector["objective_state"],
            source_inspector["objective_state"],
        )
        self.assertEqual(
            replay_inspector["history"]["action_results"],
            source_inspector["history"]["action_results"],
        )
        self.assertEqual(
            [record.model_input for record in replay.private_decision_records],
            [record.model_input for record in source.private_decision_records],
        )
        self.assertEqual(
            [
                (record.status, record.failure_kind, record.failure_type)
                for record in replay.private_decision_records
            ],
            [
                (record.status, record.failure_kind, record.failure_type)
                for record in source.private_decision_records
            ],
        )
        self.assertEqual(
            [
                (record.status, record.failure_kind, record.failure_type)
                for record in source.private_decision_records
            ],
            [
                ("failed", "timeout", "TimeoutError"),
                ("selected", None, None),
                ("selected", None, None),
            ],
        )
        replay_model_path = replay_inspector["model_path"]
        source_model_path = source_inspector["model_path"]
        self.assertEqual(
            {
                key: replay_model_path[key]
                for key in ("exercised", "decision_status_counts", "provider_failure_count")
            },
            {
                key: source_model_path[key]
                for key in ("exercised", "decision_status_counts", "provider_failure_count")
            },
        )

    def test_sealed_recording_rejects_a_self_consistent_selected_action_edit(self):
        source = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                _SequenceClient(
                    {
                        "kind": "wait",
                        "parameters": {},
                        "explanation": "rest after the scheduled wake",
                        "decision_reason": "the morning is quiet",
                    },
                    {
                        "kind": "wait",
                        "parameters": {},
                        "explanation": "pause after completing rest",
                        "decision_reason": "no immediate action is needed",
                    },
                    {
                        "kind": "wait",
                        "parameters": {},
                        "explanation": "pause after the accessible bulletin",
                        "decision_reason": "the bulletin changes no immediate action",
                    },
                ),
                configuration_id="deterministic-autonomous-day-integrity-source",
            ),
        )
        source.run()
        integrity_key = b"autonomous-day-recording-edit-detection-v1"
        archive = RecordedDecisionArchive.seal(
            source.private_decision_records,
            integrity_key=integrity_key,
        )
        selected_index = next(
            index
            for index, record in enumerate(archive.records)
            if record.status == "selected"
        )
        selected_record = archive.records[selected_index]
        altered_response = dict(selected_record.structured_response)
        altered_response["explanation"] = "a changed but schema-valid explanation"
        altered_attempt = dict(selected_record.attempted_action)
        altered_attempt["explanation"] = altered_response["explanation"]
        altered_records = list(archive.records)
        altered_records[selected_index] = replace(
            selected_record,
            structured_response=altered_response,
            attempted_action=altered_attempt,
        )
        altered_archive = replace(archive, records=tuple(altered_records))

        with self.assertRaisesRegex(
            RecordedDecisionError,
            "archive integrity mismatch",
        ):
            MaraHarness.from_recorded_archive(
                altered_archive,
                integrity_key=integrity_key,
            )

    def test_recorded_autonomous_day_failure_is_explicit_for_altered_or_exhausted_evidence(
        self,
    ):
        source_client = _SequenceClient(
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "rest at home after the scheduled wake",
                "decision_reason": "the morning begins with time to rest",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the completed rest",
                "decision_reason": "no further action is required immediately",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after the accessible bulletin",
                "decision_reason": "the bulletin changes no immediate action",
            },
        )
        source = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                source_client,
                configuration_id="deterministic-autonomous-day-replay-failure-source",
            ),
        )
        source.run()

        altered_input = dict(source.private_decision_records[0].model_input)
        altered_input["tick"] = 421
        altered_records = (
            replace(source.private_decision_records[0], model_input=altered_input),
            *source.private_decision_records[1:],
        )
        altered_integrity_key = b"autonomous-day-input-mismatch-integrity-v1"
        altered = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_recorded_archive(
                RecordedDecisionArchive.seal(
                    altered_records,
                    integrity_key=altered_integrity_key,
                ),
                integrity_key=altered_integrity_key,
            ),
        )
        with self.assertRaisesRegex(RecordedDecisionError, "input mismatch"):
            altered.run()
        self.assertFalse(altered.runtime.is_complete)
        altered_summary = altered.runtime.summary()
        self.assertEqual(
            altered_summary.runtime_failure.failure_type,
            "RecordedDecisionError",
        )
        normal_output = render_autonomous_day(altered, altered_summary)
        self.assertIn(
            "Run status: stopped without completing the day at Day 0 07:00.",
            normal_output,
        )
        self.assertIn("Exact 24-hour boundary reached: no", normal_output)
        self.assertNotIn("RecordedDecisionError", normal_output)
        self.assertNotIn("input mismatch", normal_output)
        inspector_data = autonomous_day_inspector_data(altered, altered_summary)
        self.assertEqual(
            inspector_data["runtime"]["runtime_failure"],
            {
                "failure_type": "RecordedDecisionError",
                "last_committed_time": {
                    "total_minutes": 0,
                    "day_index": 0,
                    "hour": 0,
                    "minute": 0,
                    "label": "Day 0 00:00",
                },
                "failed_time": {
                    "total_minutes": 420,
                    "day_index": 0,
                    "hour": 7,
                    "minute": 0,
                    "label": "Day 0 07:00",
                },
                "committed_work_count": 0,
                "released_uncommitted_count": 1,
                "pending_work_count": 2,
                "failed_dispatch": {
                    "due_time": {
                        "total_minutes": 420,
                        "day_index": 0,
                        "hour": 7,
                        "minute": 0,
                        "label": "Day 0 07:00",
                    },
                    "phase": "decision",
                    "sequence": 1,
                },
            },
        )
        self.assertNotIn("input mismatch", json.dumps(inspector_data))
        command_output = io.StringIO()
        with patch(
            "scenarios.autonomous_day.build_autonomous_day", return_value=altered
        ), redirect_stdout(command_output):
            self.assertEqual(main(["--seed", "42"]), 1)
        self.assertIn(
            "Run status: stopped without completing the day at Day 0 07:00.",
            command_output.getvalue(),
        )
        self.assertNotIn("RecordedDecisionError", command_output.getvalue())
        self.assertNotIn("input mismatch", command_output.getvalue())

        end_failed = build_autonomous_day(seed=42)

        def fail_at_end(work, context):
            raise RuntimeError("private-end-failure")

        end_failed.runtime._handlers["test_end_failure"] = fail_at_end
        end_failed.runtime.schedule(
            ScheduledWork(
                "test-end-failure",
                end_failed.runtime.end,
                TemporalPhase.SCHEDULED_WORLD,
                "test_end_failure",
            )
        )
        with self.assertRaisesRegex(RuntimeError, "private-end-failure"):
            end_failed.run()
        end_failure_output = render_autonomous_day(
            end_failed,
            end_failed.runtime.summary(),
        )
        self.assertIn(
            "Run status: stopped without completing the day at Day 1 00:00.",
            end_failure_output,
        )
        self.assertNotIn("before the day boundary", end_failure_output)

        exhausted_integrity_key = b"autonomous-day-exhausted-integrity-v1"
        exhausted = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_recorded_archive(
                RecordedDecisionArchive.seal(
                    source.private_decision_records[:1],
                    integrity_key=exhausted_integrity_key,
                ),
                integrity_key=exhausted_integrity_key,
            ),
        )
        with self.assertRaisesRegex(RecordedDecisionError, "exhausted"):
            exhausted.run()
        self.assertFalse(exhausted.runtime.is_complete)
        self.assertEqual(
            exhausted.runtime.summary().runtime_failure.failure_type,
            "RecordedDecisionError",
        )


if __name__ == "__main__":
    unittest.main()
