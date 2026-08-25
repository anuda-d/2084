import unittest
from dataclasses import replace

from policies.mara_harness import MaraHarness
from scenarios.autonomous_day import (
    ILAN_ID,
    MARA_ID,
    autonomous_day_inspector_data,
    build_autonomous_day,
    render_autonomous_day,
)
from policies.model_focal_policy import (
    RecordedDecisionError,
    model_input_from_view,
)
from policies.mara_decision_request import MAX_RESTRICTED_DECISION_INPUT_BYTES
from simulation.agents import MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES
from simulation.decision_eligibility import DecisionTrigger, DecisionTriggerKind


class _SequenceClient:
    def __init__(self, *responses):
        self._responses = responses
        self.inputs = []

    def choose(self, model_input):
        self.inputs.append(model_input)
        return self._responses[len(self.inputs) - 1]


class AutonomousDayWorldTests(unittest.TestCase):
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
                for key in ("configured", "exercised", "provider_failure_count")
            },
            {
                "configured": True,
                "exercised": True,
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
            },
        )
        self.assertGreater(
            model_path["growth"]["peak_retained_private_record_bytes"],
            day.private_decision_records_bytes - 1,
        )
        self.assertNotIn("model_input", model_path["growth"])
        self.assertNotIn("private_decision_records", model_path["growth"])

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
            {MARA_ID: 3},
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
            dispatched.append(decision)
            original_handler(decision, context)

        day.runtime._decision_handler = capture_decision

        summary = day.run()

        self.assertTrue(summary.reached_end_boundary)
        self.assertEqual(len(client.inputs), 2)
        self.assertEqual(client.inputs[1]["tick"], 450)
        self.assertEqual(client.inputs[1]["state"]["location"], "workplace")
        self.assertEqual(day.world.agents[MARA_ID].location, "workplace")
        self.assertEqual(day.observations, ())
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
            summary.to_data()["decision_counts_by_actor"], {MARA_ID: 2}
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

    def test_equal_deterministic_harness_runs_reproduce_complete_day_evidence(
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
            summary.to_data()["decision_counts_by_actor"], {MARA_ID: 2}
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
        bulletin = day.observations[0]
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
            summary.to_data()["decision_counts_by_actor"], {MARA_ID: 2}
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

        bulletin = day.observations[0]
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
        self.assertEqual(day.observations, ())
        self.assertEqual(
            summary.to_data()["decision_counts_by_actor"], {MARA_ID: 1}
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
                (600, "work_completed", ILAN_ID),
            ],
        )
        attempted, transit_change, completed = day.events
        self.assertEqual(completed.caused_by, (attempted.event_id,))
        self.assertEqual(completed.action_id, attempted.action_id)
        self.assertEqual(transit_change.details["prior_status"], "normal")
        self.assertEqual(transit_change.details["current_status"], "reduced")
        self.assertEqual(day.world.institution.records["tram_service"], "reduced")

        ilan = day.world.agents[ILAN_ID]
        self.assertEqual([attempt.kind for attempt in ilan.action_history], ["work"])
        self.assertEqual([result.status for result in ilan.action_results], ["completed"])
        self.assertEqual(day.pending_action_count, 0)

        mara = day.world.agents[MARA_ID]
        self.assertEqual(mara.location, "home")
        self.assertEqual(mara.action_history, [])
        self.assertEqual(mara.action_results, [])
        self.assertEqual(len(mara.observations), 1)
        self.assertEqual(tuple(mara.observations), day.observations)
        bulletin = mara.observations[0]
        self.assertEqual(bulletin.event_id, transit_change.event_id)
        self.assertEqual(bulletin.delivery_tick, 660)
        self.assertEqual(bulletin.source, "home transit bulletin receiver")
        self.assertEqual(bulletin.details["evidence_kind"], "transit_service_status")
        self.assertEqual(bulletin.details["current_status"], "reduced")
        self.assertEqual(summary.to_data()["decision_counts_by_actor"], {MARA_ID: 0})

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
        self.assertEqual(len(day.events), 3)
        self.assertEqual(day.world.institution.records["tram_service"], "reduced")
        self.assertEqual(day.observations, ())
        self.assertEqual(day.world.agents[MARA_ID].observations, [])
        self.assertEqual(summary.to_data()["decision_counts_by_actor"], {MARA_ID: 0})

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

        replay = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_records(source.private_decision_records),
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
        altered = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_records(altered_records),
        )
        with self.assertRaisesRegex(RecordedDecisionError, "input mismatch"):
            altered.run()
        self.assertFalse(altered.runtime.is_complete)
        self.assertEqual(
            altered.runtime.summary().runtime_failure.failure_type,
            "RecordedDecisionError",
        )

        exhausted = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_records(
                source.private_decision_records[:1]
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
