from dataclasses import replace
import json
import unittest

from observer.inspector import render_inspector
from observer.terminal import render_terminal
from policies.model_focal_policy import (
    DECISION_HISTORY_PROJECTION_KIND,
    MAX_RETAINED_DECISION_HISTORY_ENTRIES,
    ModelFocalPolicy,
    ModelUnavailableError,
    RecordedDecisionClient,
    RecordedDecisionError,
    StructuredChoiceError,
    model_input_from_view,
    structured_choice_to_attempt,
)
from policies.mara_decision_request import restricted_decision_input_size_bytes
from scenarios.first_day import CLERK_ID, CO_WORKER_ID, FOCAL_AGENT_ID, build_first_day
from simulation.actions import ActionAttempt, ActionResult
from simulation.agents import (
    MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES,
    PRIVATE_DECISION_RECORD_RESOLUTION_BASE_BYTES,
    PrivateDecisionRecordLimitError,
    private_decision_records_size_bytes,
    serialize_private_decision_records,
    validate_private_decision_record_retention,
)
from simulation.events import to_plain_data


class StructuredModelChoiceTests(unittest.TestCase):
    def test_valid_choice_becomes_a_detached_attempt_for_the_view_actor(self):
        simulation = build_first_day(seed=42)
        view = simulation.agent_view(FOCAL_AGENT_ID)
        state_before = simulation.inspector_state()
        events_before = simulation.events
        response = {
            "kind": "travel",
            "parameters": {"destination": "workplace"},
            "explanation": "travel to workplace",
            "decision_reason": "the workplace shift is the immediate obligation",
        }

        attempt = structured_choice_to_attempt(view, response)
        response["parameters"]["destination"] = "allocation_office"

        self.assertEqual(attempt.actor_id, FOCAL_AGENT_ID)
        self.assertEqual(attempt.kind, "travel")
        self.assertEqual(attempt.parameters["destination"], "workplace")
        self.assertEqual(simulation.inspector_state(), state_before)
        self.assertEqual(simulation.events, events_before)
        with self.assertRaises(TypeError):
            attempt.parameters["destination"] = "home"

    def test_every_action_kind_has_an_enforced_parameter_shape(self):
        simulation = build_first_day(seed=42)
        view = simulation.agent_view(FOCAL_AGENT_ID)
        state_before = simulation.inspector_state()
        events_before = simulation.events
        valid_parameters = {
            "travel": {"destination": "workplace"},
            "work": {},
            "consult_official_record": {"artifact_id": "weekly-schedule"},
            "request_allocation": {
                "requested_units": 1,
                "evidence_observation_ids": [],
            },
            "speak": {
                "proposition": "daily_allocation_units",
                "asserted_value": 2,
                "evidence_observation_ids": ["observation-0001"],
                "pressure": 0.5,
                "pressure_reason": "public protocol",
            },
            "write_diary": {
                "object_id": "mara-private-diary",
                "proposition": "daily_allocation_units",
                "asserted_value": 2,
                "source_observation_ids": ["observation-0001"],
            },
            "read_diary": {
                "object_id": "mara-private-diary",
                "entry_id": "entry-0001",
            },
            "wait": {},
        }
        for kind, parameters in valid_parameters.items():
            with self.subTest(valid_kind=kind):
                attempt = structured_choice_to_attempt(
                    view,
                    {
                        "kind": kind,
                        "parameters": parameters,
                        "explanation": f"attempt {kind}",
                        "decision_reason": "choose one supported action",
                    },
                )
                self.assertEqual(attempt.kind, kind)

        invalid_parameters = (
            ("travel", {}),
            ("travel", {"destination": 7}),
            ("work", {"duration": 1}),
            ("consult_official_record", {"artifact_id": ""}),
            ("request_allocation", {"requested_units": 0}),
            (
                "request_allocation",
                {"requested_units": 1, "evidence_observation_ids": "obs"},
            ),
            (
                "speak",
                {
                    "proposition": "claim",
                    "asserted_value": True,
                    "evidence_observation_ids": ["observation-0001"],
                },
            ),
            (
                "speak",
                {
                    "proposition": "claim",
                    "asserted_value": 2,
                    "evidence_observation_ids": [],
                },
            ),
            (
                "speak",
                {
                    "proposition": "claim",
                    "asserted_value": 2,
                    "evidence_observation_ids": ["observation-0001"],
                    "pressure": 0.5,
                },
            ),
            (
                "write_diary",
                {
                    "object_id": "mara-private-diary",
                    "proposition": "claim",
                    "asserted_value": 2,
                },
            ),
            ("read_diary", {"object_id": "mara-private-diary", "entry_id": ""}),
            ("wait", {"until": 2}),
        )
        for kind, parameters in invalid_parameters:
            with self.subTest(invalid_kind=kind, parameters=parameters):
                with self.assertRaises(StructuredChoiceError):
                    structured_choice_to_attempt(
                        view,
                        {
                            "kind": kind,
                            "parameters": parameters,
                            "explanation": f"attempt {kind}",
                            "decision_reason": "choose one supported action",
                        },
                    )

        self.assertEqual(simulation.inspector_state(), state_before)
        self.assertEqual(simulation.events, events_before)


class StaticModelDecisionClient:
    def __init__(self, response):
        self.response = response
        self.inputs = []

    def choose(self, model_input):
        self.inputs.append(model_input)
        return self.response


class FailingModelDecisionClient:
    def __init__(self, error):
        self.error = error
        self.inputs = []

    def choose(self, model_input):
        self.inputs.append(model_input)
        raise self.error


class MutatingModelDecisionClient:
    def __init__(self, response):
        self.response = response

    def choose(self, model_input):
        model_input["character"]["display_name"] = "mutated by client"
        model_input["action_contract"]["supported_kinds"].append("rewrite_world")
        return self.response


class SequenceModelDecisionClient:
    def __init__(self, *responses):
        self.responses = responses
        self.inputs = []

    def choose(self, model_input):
        response = self.responses[len(self.inputs)]
        self.inputs.append(model_input)
        return response


class ResultResponsiveModelDecisionClient:
    def __init__(self, first_destination):
        self.first_destination = first_destination
        self.inputs = []

    def choose(self, model_input):
        self.inputs.append(model_input)
        history = model_input["decision_history"]
        if not history["results"]:
            return {
                "kind": "travel",
                "parameters": {"destination": self.first_destination},
                "explanation": f"travel to {self.first_destination}",
                "decision_reason": "the first decision follows the current obligation",
            }
        latest_result = history["results"][-1]
        if latest_result["status"] == "completed":
            return {
                "kind": "work",
                "parameters": {},
                "explanation": "begin work after arriving",
                "decision_reason": (
                    f"the completed {latest_result['action_kind']} placed Mara at "
                    f"{model_input['state']['location']}"
                ),
            }
        return {
            "kind": "wait",
            "parameters": {},
            "explanation": "wait after the rejected route",
            "decision_reason": (
                f"the previous {latest_result['action_kind']} was rejected: "
                f"{latest_result['reason']}"
            ),
        }


def model_policy(client):
    return ModelFocalPolicy(client, configuration_id="deterministic-test-v1")


class ModelFocalPolicyTests(unittest.TestCase):
    def test_private_record_retention_accepts_exact_limit_and_rejects_overflow(
        self,
    ):
        simulation = build_first_day(
            seed=42,
            focal_policy=model_policy(
                StaticModelDecisionClient(
                    {
                        "kind": "wait",
                        "parameters": {},
                        "explanation": "wait briefly",
                        "decision_reason": "retain boundary evidence",
                    }
                )
            ),
        )
        simulation.step()
        record = simulation.decision_records[0]
        base = replace(record, model_input={"padding": ""})
        base_bytes = private_decision_records_size_bytes((base,))
        padding_bytes = MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES - base_bytes
        exact = replace(base, model_input={"padding": "x" * padding_bytes})
        overflow = replace(
            base,
            model_input={"padding": "x" * (padding_bytes + 1)},
        )

        self.assertEqual(
            private_decision_records_size_bytes((exact,)),
            MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES,
        )
        self.assertEqual(
            validate_private_decision_record_retention((exact,)),
            MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES,
        )
        simulation._retain_decision_records((exact,))
        self.assertEqual(simulation.decision_records, (exact,))
        self.assertEqual(
            simulation.private_decision_records_bytes,
            MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES,
        )
        with self.assertRaises(PrivateDecisionRecordLimitError) as raised:
            simulation._retain_decision_records((overflow,))
        self.assertEqual(
            raised.exception.attempted_bytes,
            MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES + 1,
        )
        self.assertEqual(
            raised.exception.maximum_bytes,
            MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES,
        )
        self.assertEqual(simulation.decision_records, (exact,))
        self.assertEqual(
            simulation.private_decision_records_bytes,
            MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES,
        )

        class NearLimitRecordPolicy:
            def __init__(self, retained_record):
                self._record = retained_record

            def choose(self, view):
                return ActionAttempt(
                    actor_id=view.agent_id,
                    kind="work",
                    parameters={},
                    explanation="attempt work without an oversized record",
                    decision_reason="exercise private-record preflight",
                )

            def take_decision_record(self):
                record_to_return = self._record
                self._record = None
                return record_to_return

        near_limit = replace(
            base,
            model_input={
                "padding": "x"
                * (
                    padding_bytes
                    - PRIVATE_DECISION_RECORD_RESOLUTION_BASE_BYTES
                )
            },
        )
        preflight = build_first_day(
            seed=42,
            focal_policy=NearLimitRecordPolicy(near_limit),
        )
        preflight.rules = replace(
            preflight.rules,
            work_location="w" * 5_000,
        )
        prospective_attempt = ActionAttempt(
            actor_id=FOCAL_AGENT_ID,
            kind="work",
            parameters={},
            explanation="attempt work without an oversized record",
            decision_reason="exercise private-record preflight",
        )
        reserve_bytes = preflight._decision_record_resolution_reserve_bytes(
            prospective_attempt
        )
        with self.assertRaises(PrivateDecisionRecordLimitError) as preflight_error:
            preflight.step()
        self.assertEqual(
            preflight_error.exception.attempted_bytes,
            MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES
            - PRIVATE_DECISION_RECORD_RESOLUTION_BASE_BYTES
            + reserve_bytes,
        )
        self.assertEqual(preflight.decision_records, ())
        self.assertEqual(
            preflight.world.agents[FOCAL_AGENT_ID].action_history,
            [],
        )
        self.assertFalse(
            any(
                event.kind == "action_attempted"
                and event.actor_id == FOCAL_AGENT_ID
                for event in preflight.events
            )
        )

    def test_pending_record_overflow_preflights_before_world_completion(self):
        client = StaticModelDecisionClient(
            {
                "kind": "travel",
                "parameters": {"destination": "workplace"},
                "explanation": "travel to workplace",
                "decision_reason": "exercise resolution preflight",
            }
        )
        simulation = build_first_day(seed=42, focal_policy=model_policy(client))
        simulation.step()
        pending_record = simulation.decision_records[0]
        base = replace(pending_record, model_input={"padding": ""})
        base_bytes = private_decision_records_size_bytes((base,))
        exact = replace(
            base,
            model_input={
                "padding": "x"
                * (MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES - base_bytes)
            },
        )
        simulation._retain_decision_records((exact,))
        simulation.step()
        focal = simulation.world.agents[FOCAL_AGENT_ID]
        events_before = simulation.events
        results_before = tuple(focal.action_results)

        with self.assertRaises(PrivateDecisionRecordLimitError):
            simulation.step()

        self.assertEqual(focal.location, "home")
        self.assertEqual(tuple(focal.action_results), results_before)
        self.assertEqual(simulation.decision_records, (exact,))
        self.assertIsNone(simulation.decision_records[0].resolution_status)
        self.assertFalse(
            any(
                event.kind == "travel_completed"
                and event.actor_id == FOCAL_AGENT_ID
                for event in simulation.events[len(events_before):]
            )
        )
        self.assertIn(FOCAL_AGENT_ID, simulation._pending)

    def test_inspector_reports_exact_current_and_peak_private_record_bytes_only(self):
        client = StaticModelDecisionClient(
            {
                "kind": "travel",
                "parameters": {"destination": "workplace"},
                "explanation": "travel to workplace",
                "decision_reason": "follow the current obligation",
            }
        )
        simulation = build_first_day(seed=42, focal_policy=model_policy(client))

        simulation.step()
        pending_bytes = simulation.private_decision_records_bytes
        self.assertEqual(
            pending_bytes,
            len(
                serialize_private_decision_records(
                    simulation.decision_records
                ).encode("utf-8")
            ),
        )
        simulation.step()
        simulation.step()

        completed_bytes = private_decision_records_size_bytes(
            simulation.decision_records
        )
        self.assertEqual(simulation.private_decision_records_bytes, completed_bytes)
        self.assertGreater(completed_bytes, pending_bytes)
        self.assertEqual(
            simulation.peak_private_decision_records_bytes,
            completed_bytes,
        )
        inspector_lines = render_inspector(simulation).splitlines()
        inspector = json.loads("\n".join(inspector_lines[2:]))
        self.assertEqual(
            inspector["private_decision_record_storage"],
            {
                "retained_bytes": completed_bytes,
                "peak_retained_bytes": completed_bytes,
                "maximum_bytes": MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES,
            },
        )
        normal = render_terminal(simulation.snapshots)
        objective = json.dumps(simulation.history_data(), sort_keys=True)
        self.assertNotIn("private_decision_record_storage", normal)
        self.assertNotIn("private_decision_record_storage", objective)
        self.assertNotIn(str(completed_bytes), normal)

    def test_decision_history_projection_retains_a_bounded_recent_window(self):
        simulation = build_first_day(seed=42)
        view = simulation.agent_view(FOCAL_AGENT_ID)
        lifetime_count = MAX_RETAINED_DECISION_HISTORY_ENTRIES + 3
        attempts = tuple(
            ActionAttempt(
                actor_id=FOCAL_AGENT_ID,
                kind="wait",
                parameters={},
                explanation=f"wait attempt {index:02d}",
                decision_reason=f"reason {index:02d}",
            )
            for index in range(lifetime_count)
        )
        results = tuple(
            ActionResult(
                action_id=f"action-{index:04d}",
                attempt_event_id=f"event-attempt-{index:04d}",
                outcome_event_id=f"event-outcome-{index:04d}",
                actor_id=FOCAL_AGENT_ID,
                action_kind="wait",
                status="completed",
                resolved_tick=index + 1,
                reason=f"completed wait {index:02d}",
            )
            for index in range(lifetime_count)
        )
        projected = model_input_from_view(
            replace(
                view,
                last_attempt=attempts[-1],
                action_history=attempts,
                action_results=results,
            )
        )["decision_history"]

        self.assertEqual(
            projected["projection"],
            {
                "kind": DECISION_HISTORY_PROJECTION_KIND,
                "maximum_attempts": MAX_RETAINED_DECISION_HISTORY_ENTRIES,
                "maximum_results": MAX_RETAINED_DECISION_HISTORY_ENTRIES,
                "total_attempts": lifetime_count,
                "total_results": lifetime_count,
                "omitted_attempts": 3,
                "omitted_results": 3,
            },
        )
        self.assertEqual(
            len(projected["attempts"]),
            MAX_RETAINED_DECISION_HISTORY_ENTRIES,
        )
        self.assertEqual(
            len(projected["results"]),
            MAX_RETAINED_DECISION_HISTORY_ENTRIES,
        )
        self.assertEqual(
            projected["attempts"][0]["explanation"], "wait attempt 03"
        )
        self.assertEqual(
            projected["attempts"][-1], projected["last_attempt"]
        )
        self.assertEqual(
            projected["results"][0]["action_id"], "action-0003"
        )
        self.assertEqual(
            projected["results"][-1]["action_id"],
            f"action-{lifetime_count - 1:04d}",
        )

    def test_decision_history_collection_size_stops_growing_after_its_window(self):
        simulation = build_first_day(seed=42)
        view = simulation.agent_view(FOCAL_AGENT_ID)

        def projected_lengths(lifetime_count: int) -> tuple[int, int]:
            attempts = tuple(
                ActionAttempt(
                    actor_id=FOCAL_AGENT_ID,
                    kind="wait",
                    parameters={},
                    explanation="bounded wait",
                    decision_reason="bounded continuity test",
                )
                for _ in range(lifetime_count)
            )
            results = tuple(
                ActionResult(
                    action_id=f"action-{index:04d}",
                    attempt_event_id=f"event-attempt-{index:04d}",
                    outcome_event_id=f"event-outcome-{index:04d}",
                    actor_id=FOCAL_AGENT_ID,
                    action_kind="wait",
                    status="completed",
                    resolved_tick=index + 1,
                )
                for index in range(lifetime_count)
            )
            history = model_input_from_view(
                replace(
                    view,
                    last_attempt=attempts[-1],
                    action_history=attempts,
                    action_results=results,
                )
            )["decision_history"]
            return len(history["attempts"]), len(history["results"])

        self.assertEqual(
            projected_lengths(MAX_RETAINED_DECISION_HISTORY_ENTRIES),
            (
                MAX_RETAINED_DECISION_HISTORY_ENTRIES,
                MAX_RETAINED_DECISION_HISTORY_ENTRIES,
            ),
        )
        self.assertEqual(
            projected_lengths(MAX_RETAINED_DECISION_HISTORY_ENTRIES + 80),
            (
                MAX_RETAINED_DECISION_HISTORY_ENTRIES,
                MAX_RETAINED_DECISION_HISTORY_ENTRIES,
            ),
        )

    def test_recorded_decisions_reproduce_complete_ordered_world_history(self):
        scripted = build_first_day(seed=42)
        scripted.run(max_ticks=30)
        scripted_attempts = scripted.world.agents[FOCAL_AGENT_ID].action_history
        responses = tuple(
            {
                "kind": attempt.kind,
                "parameters": to_plain_data(attempt.parameters),
                "explanation": attempt.explanation,
                "decision_reason": attempt.decision_reason,
            }
            for attempt in scripted_attempts
        )
        source_client = SequenceModelDecisionClient(*responses)
        source = build_first_day(
            seed=42, focal_policy=model_policy(source_client)
        )
        source.run(max_ticks=30)
        source_call_count = len(source_client.inputs)

        recorded_client = RecordedDecisionClient.from_records(
            source.decision_records
        )
        replay = build_first_day(
            seed=42,
            focal_policy=ModelFocalPolicy(
                recorded_client,
                configuration_id="recorded:first-day-v1",
            ),
        )
        replay.run(max_ticks=30)

        self.assertTrue(source.is_complete)
        self.assertTrue(replay.is_complete)
        self.assertEqual(source.tick, 28)
        self.assertEqual(replay.tick, 28)
        self.assertEqual(source.history_data(), scripted.history_data())
        self.assertEqual(replay.history_data(), source.history_data())
        self.assertEqual(
            [event.event_id for event in replay.events],
            [event.event_id for event in source.events],
        )
        self.assertEqual(len(source_client.inputs), source_call_count)
        self.assertEqual(recorded_client.consumed_count, len(source.decision_records))
        self.assertEqual(recorded_client.remaining_count, 0)

    def test_recorded_client_is_strict_detached_and_explicit_on_bad_data(self):
        source_client = StaticModelDecisionClient(
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "wait once",
                "decision_reason": "create one recorded choice",
            }
        )
        source = build_first_day(
            seed=42, focal_policy=model_policy(source_client)
        )
        source.step()
        record_data = source.decision_records[0].to_data()
        recorded_client = RecordedDecisionClient((record_data,))
        mismatch = json.loads(json.dumps(record_data["model_input"]))
        mismatch["tick"] += 1

        with self.assertRaisesRegex(RecordedDecisionError, "input mismatch"):
            recorded_client.choose(mismatch)
        self.assertEqual(recorded_client.consumed_count, 0)

        choice = recorded_client.choose(record_data["model_input"])
        choice["kind"] = "travel"
        self.assertEqual(
            source.decision_records[0].structured_response["kind"], "wait"
        )
        with self.assertRaisesRegex(RecordedDecisionError, "exhausted"):
            recorded_client.choose(record_data["model_input"])

        disagreeing_choice = json.loads(json.dumps(record_data))
        disagreeing_choice["structured_response"]["parameters"] = {"until": 2}
        with self.assertRaisesRegex(RecordedDecisionError, "disagree"):
            RecordedDecisionClient((disagreeing_choice,))

        invalid_choice = json.loads(json.dumps(record_data))
        invalid_choice["structured_response"]["parameters"] = {"until": 2}
        invalid_choice["attempted_action"]["parameters"] = {"until": 2}
        with self.assertRaisesRegex(RecordedDecisionError, "unexpected"):
            RecordedDecisionClient((invalid_choice,))

        invalid_records = (
            ({"status": "selected"}, "no restricted input"),
            (
                {"status": "selected", "model_input": {}},
                "no structured response",
            ),
            (
                {"status": "failed", "model_input": {}},
                "no safe attempted action",
            ),
            (
                {"status": "unknown", "model_input": {}},
                "unsupported status",
            ),
        )
        for invalid, message in invalid_records:
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(RecordedDecisionError, message):
                    RecordedDecisionClient((invalid,))

    def test_failed_decision_record_replays_safe_world_behavior(self):
        failing_client = FailingModelDecisionClient(TimeoutError("private detail"))
        source = build_first_day(
            seed=42, focal_policy=model_policy(failing_client)
        )
        source.step()
        tampered = source.decision_records[0].to_data()
        tampered["attempted_action"] = {
            "actor_id": FOCAL_AGENT_ID,
            "kind": "travel",
            "parameters": {"destination": "workplace"},
            "explanation": "tampered failure route",
            "decision_reason": "replace the safe failure",
        }
        tampered["attempted_action_kind"] = "travel"
        with self.assertRaisesRegex(RecordedDecisionError, "safe wait"):
            RecordedDecisionClient((tampered,))
        recorded_client = RecordedDecisionClient.from_records(
            source.decision_records
        )
        replay = build_first_day(
            seed=42,
            focal_policy=ModelFocalPolicy(
                recorded_client,
                configuration_id="recorded:failure-v1",
            ),
        )

        replay.step()

        self.assertEqual(replay.history_data(), source.history_data())
        self.assertEqual(recorded_client.consumed_count, 1)
        self.assertEqual(replay.decision_records[0].status, "selected")
        self.assertEqual(
            replay.decision_records[0].attempted_action_kind, "wait"
        )

    def test_client_receives_detached_json_compatible_restricted_input(self):
        simulation = build_first_day(seed=42)
        view = simulation.agent_view(FOCAL_AGENT_ID)
        state_before = simulation.inspector_state()
        events_before = simulation.events
        client = StaticModelDecisionClient(
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "wait briefly",
                "decision_reason": "pause at the current location",
            }
        )

        selected = model_policy(client).choose(view)

        self.assertEqual(selected.kind, "wait")
        self.assertEqual(len(client.inputs), 1)
        model_input = client.inputs[0]
        self.assertEqual(
            set(model_input),
            {
                "tick",
                "character",
                "state",
                "decision_history",
                "delivered_observations",
                "understanding",
                "accessible_objects",
                "action_contract",
            },
        )
        self.assertEqual(model_input["character"]["agent_id"], FOCAL_AGENT_ID)
        self.assertEqual(model_input["character"]["display_name"], "Mara Vale")
        parameter_contract = model_input["action_contract"]["parameters_by_kind"]
        self.assertEqual(set(parameter_contract), set(view.valid_actions))
        self.assertEqual(
            parameter_contract["travel"]["required"],
            {"destination": "non_empty_string"},
        )
        self.assertEqual(
            parameter_contract["work"],
            {"required": {}, "optional": {}, "conditional_requirements": []},
        )
        self.assertEqual(
            parameter_contract["speak"]["conditional_requirements"],
            [{"if_present": "pressure", "requires": ["pressure_reason"]}],
        )
        action_contract = model_input["action_contract"]
        self.assertEqual(
            action_contract["currently_applicable_kinds"], ["travel", "wait"]
        )
        self.assertEqual(
            action_contract["affordances_by_kind"]["travel"][
                "parameter_options"
            ]["destination"],
            ["workplace"],
        )
        self.assertEqual(json.loads(json.dumps(model_input)), model_input)

        def nested_keys(value):
            if isinstance(value, dict):
                return set(value).union(
                    *(nested_keys(item) for item in value.values())
                )
            if isinstance(value, list):
                return set().union(*(nested_keys(item) for item in value))
            return set()

        forbidden_fields = {
            "world",
            "objective_resources",
            "event_history",
            "institution_records",
            "official_record",
            "official_record_versions",
            "travel_graph",
            "allocatable_units",
            "committed_units",
            "model_configuration",
            "configuration_id",
            "structured_response",
            "decision_records",
            "private_decision_records",
            "api_key",
            "authorization",
        }
        self.assertTrue(forbidden_fields.isdisjoint(nested_keys(model_input)))
        encoded = json.dumps(model_input, sort_keys=True)
        self.assertNotIn(CO_WORKER_ID, encoded)
        self.assertNotIn(CLERK_ID, encoded)

        model_input["character"]["display_name"] = "mutated"
        model_input["state"]["resource_holdings"]["household_allocation"] = 99
        model_input["action_contract"]["supported_kinds"].append("rewrite_world")
        model_input["action_contract"]["affordances_by_kind"]["travel"][
            "parameter_options"
        ]["destination"].append("allocation_office")
        parameter_contract["travel"]["required"]["destination"] = "integer"
        self.assertEqual(view.display_name, "Mara Vale")
        self.assertEqual(dict(view.resource_holdings), {})
        self.assertNotIn("rewrite_world", view.valid_actions)
        self.assertEqual(view.reachable_destinations, ("workplace",))
        fresh_contract = model_input_from_view(view)["action_contract"][
            "parameters_by_kind"
        ]
        self.assertEqual(
            fresh_contract["travel"]["required"]["destination"],
            "non_empty_string",
        )
        self.assertEqual(simulation.inspector_state(), state_before)
        self.assertEqual(simulation.events, events_before)

    def test_action_affordances_follow_only_agent_safe_state_and_access(self):
        simulation = build_first_day(seed=42)

        initial = model_input_from_view(simulation.agent_view(FOCAL_AGENT_ID))
        initial_contract = initial["action_contract"]
        self.assertEqual(
            initial_contract["currently_applicable_kinds"], ["travel", "wait"]
        )
        self.assertEqual(
            initial_contract["affordances_by_kind"]["travel"][
                "parameter_options"
            ]["destination"],
            ["workplace"],
        )
        self.assertFalse(
            initial_contract["affordances_by_kind"]["write_diary"][
                "currently_applicable"
            ]
        )

        for _ in range(6):
            simulation.step()
        workplace = model_input_from_view(
            simulation.agent_view(FOCAL_AGENT_ID)
        )
        workplace_contract = workplace["action_contract"]
        self.assertEqual(workplace["state"]["location"], "workplace")
        self.assertIn("work", workplace_contract["currently_applicable_kinds"])
        self.assertEqual(
            workplace_contract["affordances_by_kind"]["travel"][
                "parameter_options"
            ]["destination"],
            ["home", "allocation_office"],
        )

        simulation.step()
        counter = model_input_from_view(simulation.agent_view(FOCAL_AGENT_ID))
        counter_contract = counter["action_contract"]
        self.assertEqual(counter["state"]["location"], "allocation_office")
        for kind in ("consult_official_record", "request_allocation", "speak"):
            self.assertIn(kind, counter_contract["currently_applicable_kinds"])
        claim_options = counter_contract["affordances_by_kind"]["speak"][
            "parameter_options"
        ]["grounded_claims"]
        delivered_ids = {
            item["observation_id"] for item in counter["delivered_observations"]
        }
        self.assertTrue(claim_options)
        self.assertTrue(
            all(
                set(option["evidence_observation_ids"]).issubset(delivered_ids)
                for option in claim_options
            )
        )
        counter_encoded = json.dumps(counter, sort_keys=True)
        self.assertNotIn("allocatable_units", counter_encoded)
        self.assertNotIn("committed_units", counter_encoded)
        self.assertNotIn("travel_graph", counter_encoded)

        for _ in range(11):
            simulation.step()
        home = model_input_from_view(simulation.agent_view(FOCAL_AGENT_ID))
        home_contract = home["action_contract"]
        self.assertEqual(home["state"]["location"], "home")
        self.assertIn("read_diary", home_contract["currently_applicable_kinds"])
        self.assertEqual(
            home_contract["affordances_by_kind"]["read_diary"][
                "parameter_options"
            ]["entries"],
            [
                {
                    "object_id": "mara-private-diary",
                    "entry_id": "entry-0001",
                }
            ],
        )

    def test_model_input_carries_only_delivered_source_linked_understanding(self):
        simulation = build_first_day(seed=42)
        initial_input = model_input_from_view(
            simulation.agent_view(FOCAL_AGENT_ID)
        )
        self.assertEqual(initial_input["understanding"]["memory_traces"], [])
        self.assertEqual(initial_input["understanding"]["interpreted_claims"], [])

        for _ in range(7):
            simulation.step()
        view = simulation.agent_view(FOCAL_AGENT_ID)
        client = StaticModelDecisionClient(
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after reviewing delivered evidence",
                "decision_reason": "retain the source-linked understanding",
            }
        )

        model_policy(client).choose(view)

        model_input = client.inputs[0]
        traces = model_input["understanding"]["memory_traces"]
        claims = model_input["understanding"]["interpreted_claims"]
        delivered_ids = {
            item["observation_id"]
            for item in model_input["delivered_observations"]
        }
        self.assertEqual(
            [trace["trace_id"] for trace in traces],
            [trace.trace_id for trace in view.memory_traces],
        )
        self.assertEqual(
            [claim["claim_id"] for claim in claims],
            [claim.claim_id for claim in view.interpreted_claims],
        )
        self.assertTrue(traces)
        self.assertTrue(
            all(trace["source_observation_id"] in delivered_ids for trace in traces)
        )
        self.assertTrue(
            all(
                claim["origin_trace_id"]
                in {trace["trace_id"] for trace in traces}
                for claim in claims
            )
        )

    def test_model_selection_failures_record_a_linked_safe_wait_without_fallback(self):
        cases = (
            (
                "timeout",
                FailingModelDecisionClient(TimeoutError("secret timeout detail")),
                "timeout",
                "TimeoutError",
            ),
            (
                "unavailable",
                FailingModelDecisionClient(
                    ModelUnavailableError("secret provider detail")
                ),
                "unavailable_model",
                "ModelUnavailableError",
            ),
            (
                "malformed",
                StaticModelDecisionClient("secret unstructured response"),
                "malformed_response",
                "StructuredChoiceError",
            ),
            (
                "invalid_attempt",
                StaticModelDecisionClient(
                    {
                        "kind": "rewrite_world",
                        "parameters": {},
                        "explanation": "replace objective state",
                        "decision_reason": "claim direct authority",
                    }
                ),
                "invalid_attempt",
                "_InvalidStructuredAttemptError",
            ),
        )

        for label, client, failure_kind, failure_type in cases:
            with self.subTest(label=label):
                simulation = build_first_day(
                    seed=42, focal_policy=model_policy(client)
                )

                snapshot = simulation.step()

                focal_attempts = [
                    event
                    for event in simulation.events
                    if event.kind == "action_attempted"
                    and event.actor_id == FOCAL_AGENT_ID
                ]
                self.assertEqual(len(focal_attempts), 1)
                attempted = focal_attempts[0]
                self.assertEqual(attempted.details["action_kind"], "wait")
                self.assertEqual(
                    snapshot.current_action,
                    "wait because no valid model decision is available",
                )
                self.assertEqual(
                    snapshot.explanation,
                    f"model decision failed safely: {failure_kind}",
                )
                self.assertEqual(len(client.inputs), 1)

                self.assertEqual(len(simulation.decision_records), 1)
                record = simulation.decision_records[0]
                self.assertEqual(record.status, "failed")
                self.assertEqual(record.configuration_id, "deterministic-test-v1")
                self.assertEqual(record.failure_kind, failure_kind)
                self.assertEqual(record.failure_type, failure_type)
                self.assertIsNone(record.structured_response)
                self.assertEqual(record.attempted_action_kind, "wait")
                self.assertEqual(record.attempt_event_id, attempted.event_id)
                self.assertEqual(record.action_id, attempted.action_id)
                self.assertEqual(record.validation_status, "accepted")
                self.assertEqual(record.resolution_status, "completed")

                inspector_lines = render_inspector(simulation).splitlines()
                inspector = json.loads("\n".join(inspector_lines[2:]))
                self.assertEqual(
                    inspector["private_decision_records"], [record.to_data()]
                )
                self.assertNotIn("secret", render_inspector(simulation).lower())
                normal = render_terminal(simulation.snapshots)
                self.assertNotIn("private_decision_records", normal)
                self.assertNotIn(record.decision_id, normal)

    def test_schema_valid_but_invalid_world_parameters_are_rejected_normally(self):
        client = StaticModelDecisionClient(
            {
                "kind": "travel",
                "parameters": {"destination": "nowhere"},
                "explanation": "attempt a route",
                "decision_reason": "try the supplied destination",
            }
        )
        simulation = build_first_day(
            seed=42, focal_policy=model_policy(client)
        )

        simulation.step()

        focal_events = [
            event
            for event in simulation.events
            if event.actor_id == FOCAL_AGENT_ID
        ]
        self.assertEqual(focal_events[0].kind, "action_attempted")
        self.assertEqual(focal_events[0].details["action_kind"], "travel")
        self.assertEqual(focal_events[1].kind, "action_rejected")
        self.assertEqual(focal_events[1].caused_by, (focal_events[0].event_id,))
        self.assertEqual(len(simulation.decision_records), 1)
        record = simulation.decision_records[0]
        self.assertEqual(record.status, "selected")
        self.assertEqual(record.structured_response["kind"], "travel")
        self.assertEqual(record.validation_status, "rejected")
        self.assertEqual(record.resolution_status, "rejected")
        self.assertEqual(record.outcome_event_id, focal_events[1].event_id)
        self.assertEqual(record.resolution_reason, focal_events[1].details["reason"])
        self.assertEqual(simulation.agent_view(FOCAL_AGENT_ID).location, "home")

    def test_successful_decision_record_links_private_evidence_to_resolution(self):
        response = {
            "kind": "wait",
            "parameters": {},
            "explanation": "remain home briefly",
            "decision_reason": "pause before travelling",
        }
        client = StaticModelDecisionClient(response)
        client.api_key = "credential-marker-must-not-be-recorded"
        simulation = build_first_day(
            seed=42, focal_policy=model_policy(client)
        )

        snapshot = simulation.step()

        record = simulation.decision_records[0]
        attempted = next(
            event
            for event in simulation.events
            if event.kind == "action_attempted"
            and event.actor_id == FOCAL_AGENT_ID
        )
        completed = next(
            event
            for event in simulation.events
            if event.kind == "wait_completed"
            and event.actor_id == FOCAL_AGENT_ID
        )
        self.assertEqual(record.status, "selected")
        self.assertEqual(
            record.model_input_bytes,
            restricted_decision_input_size_bytes(record.model_input),
        )
        self.assertEqual(record.configuration_id, "deterministic-test-v1")
        self.assertIsNone(record.authorship_identity)
        self.assertEqual(record.to_data()["model_input"], client.inputs[0])
        self.assertEqual(record.to_data()["structured_response"], response)
        self.assertEqual(record.attempted_action["kind"], "wait")
        self.assertEqual(record.attempt_event_id, attempted.event_id)
        self.assertEqual(record.action_id, attempted.action_id)
        self.assertEqual(record.validation_status, "accepted")
        self.assertEqual(record.resolution_status, "completed")
        self.assertEqual(record.outcome_event_id, completed.event_id)
        self.assertEqual(record.resolved_tick, 1)
        self.assertIsNone(record.resolution_reason)
        json.dumps(record.to_data())

        inspector = render_inspector(simulation)
        normal = render_terminal((snapshot,))
        history = json.dumps(simulation.history_data(), sort_keys=True)
        self.assertIn("deterministic-test-v1", inspector)
        self.assertNotIn("credential-marker", inspector)
        self.assertNotIn("deterministic-test-v1", normal)
        self.assertNotIn("deterministic-test-v1", history)
        self.assertNotIn("private_decision_records", normal)
        self.assertNotIn("private_decision_records", history)

    def test_pending_decision_record_gains_eventual_completion_link(self):
        client = StaticModelDecisionClient(
            {
                "kind": "travel",
                "parameters": {"destination": "workplace"},
                "explanation": "travel to workplace",
                "decision_reason": "follow the current obligation",
            }
        )
        simulation = build_first_day(
            seed=42, focal_policy=model_policy(client)
        )

        simulation.step()
        initial_record = simulation.decision_records[0]
        self.assertEqual(initial_record.validation_status, "accepted")
        self.assertIsNone(initial_record.resolution_status)
        simulation.step()
        simulation.step()

        completed_record = simulation.decision_records[0]
        completion = next(
            event
            for event in simulation.events
            if event.kind == "travel_completed"
            and event.actor_id == FOCAL_AGENT_ID
        )
        self.assertEqual(completed_record.resolution_status, "completed")
        self.assertEqual(completed_record.outcome_event_id, completion.event_id)
        self.assertEqual(completed_record.resolved_tick, 3)

    def test_recorded_input_is_detached_before_client_mutation(self):
        client = MutatingModelDecisionClient(
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "wait",
                "decision_reason": "choose a safe pause",
            }
        )
        simulation = build_first_day(
            seed=42, focal_policy=model_policy(client)
        )

        simulation.step()

        record_input = simulation.decision_records[0].model_input
        self.assertEqual(record_input["character"]["display_name"], "Mara Vale")
        self.assertNotIn(
            "rewrite_world", record_input["action_contract"]["supported_kinds"]
        )
        self.assertEqual(
            simulation.agent_view(FOCAL_AGENT_ID).display_name, "Mara Vale"
        )

    def test_valid_client_choice_is_maras_attempt_without_scripted_substitution(self):
        scripted = build_first_day(seed=42)
        client = StaticModelDecisionClient(
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "remain at home for one decision",
                "decision_reason": "the immediate choice is to pause",
            }
        )
        model_backed = build_first_day(
            seed=42, focal_policy=model_policy(client)
        )
        self.assertEqual(scripted.inspector_state(), model_backed.inspector_state())

        scripted.step()
        snapshot = model_backed.step()

        scripted_attempt = next(
            event
            for event in scripted.events
            if event.kind == "action_attempted" and event.actor_id == FOCAL_AGENT_ID
        )
        model_attempt = next(
            event
            for event in model_backed.events
            if event.kind == "action_attempted" and event.actor_id == FOCAL_AGENT_ID
        )
        self.assertEqual(scripted_attempt.details["action_kind"], "travel")
        self.assertEqual(model_attempt.details["action_kind"], "wait")
        self.assertEqual(
            model_attempt.details["decision_explanation"],
            "the immediate choice is to pause",
        )
        self.assertEqual(snapshot.current_action, "remain at home for one decision")
        self.assertEqual(len(client.inputs), 1)
        self.assertEqual(
            client.inputs[0]["character"]["agent_id"], FOCAL_AGENT_ID
        )
        self.assertEqual(
            client.inputs[0]["character"]["display_name"], "Mara Vale"
        )

    def test_equal_model_inputs_with_different_valid_choices_diverge_in_world(self):
        wait_client = StaticModelDecisionClient(
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "remain home",
                "decision_reason": "choose to pause before leaving",
            }
        )
        travel_client = SequenceModelDecisionClient(
            {
                "kind": "travel",
                "parameters": {"destination": "workplace"},
                "explanation": "travel to workplace",
                "decision_reason": "choose to begin the workplace obligation",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after arriving",
                "decision_reason": "the chosen journey is complete",
            },
        )
        waiting = build_first_day(
            seed=42, focal_policy=model_policy(wait_client)
        )
        travelling = build_first_day(
            seed=42, focal_policy=model_policy(travel_client)
        )
        self.assertEqual(waiting.inspector_state(), travelling.inspector_state())

        waiting_snapshots = [waiting.step() for _ in range(3)]
        travelling_snapshots = [travelling.step() for _ in range(3)]

        self.assertEqual(wait_client.inputs[0], travel_client.inputs[0])
        waiting_attempt = next(
            event
            for event in waiting.events
            if event.kind == "action_attempted" and event.actor_id == FOCAL_AGENT_ID
        )
        travelling_attempt = next(
            event
            for event in travelling.events
            if event.kind == "action_attempted" and event.actor_id == FOCAL_AGENT_ID
        )
        wait_completed = next(
            event
            for event in waiting.events
            if event.kind == "wait_completed" and event.actor_id == FOCAL_AGENT_ID
        )
        travel_completed = next(
            event
            for event in travelling.events
            if event.kind == "travel_completed" and event.actor_id == FOCAL_AGENT_ID
        )
        self.assertEqual(waiting_attempt.details["action_kind"], "wait")
        self.assertEqual(travelling_attempt.details["action_kind"], "travel")
        self.assertEqual(wait_completed.caused_by, (waiting_attempt.event_id,))
        self.assertEqual(travel_completed.caused_by, (travelling_attempt.event_id,))
        self.assertEqual(waiting_snapshots[-1].location, "home")
        self.assertEqual(travelling_snapshots[-1].location, "workplace")

    def test_world_schedules_and_completes_model_selected_travel(self):
        client = SequenceModelDecisionClient(
            {
                "kind": "travel",
                "parameters": {"destination": "workplace"},
                "explanation": "travel to workplace",
                "decision_reason": "the workplace obligation is current",
            },
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "pause after arriving",
                "decision_reason": "arrival completes the selected journey",
            },
        )
        simulation = build_first_day(
            seed=42, focal_policy=model_policy(client)
        )

        tick_one = simulation.step()
        simulation.step()
        tick_three = simulation.step()

        travel_attempt = next(
            event
            for event in simulation.events
            if event.kind == "action_attempted"
            and event.actor_id == FOCAL_AGENT_ID
            and event.details["action_kind"] == "travel"
        )
        completion = next(
            event
            for event in simulation.events
            if event.kind == "travel_completed" and event.actor_id == FOCAL_AGENT_ID
        )
        self.assertEqual(tick_one.location, "home")
        self.assertEqual(tick_three.location, "workplace")
        self.assertEqual(travel_attempt.tick, 1)
        self.assertEqual(completion.tick, 3)
        self.assertEqual(completion.action_id, travel_attempt.action_id)
        self.assertEqual(completion.caused_by, (travel_attempt.event_id,))
        self.assertEqual(len(client.inputs), 2)
        self.assertEqual(client.inputs[0]["decision_history"]["results"], [])
        completed_result = client.inputs[1]["decision_history"]["results"][-1]
        self.assertEqual(completed_result["action_id"], travel_attempt.action_id)
        self.assertEqual(completed_result["status"], "completed")
        self.assertEqual(completed_result["resolved_tick"], 3)

    def test_world_rejects_unreachable_model_travel_and_returns_actor_safe_result(self):
        client = StaticModelDecisionClient(
            {
                "kind": "travel",
                "parameters": {"destination": "allocation_office"},
                "explanation": "travel directly to the allocation office",
                "decision_reason": "attempt the shortest apparent route",
            }
        )
        simulation = build_first_day(
            seed=42, focal_policy=model_policy(client)
        )

        simulation.step()

        attempted = next(
            event
            for event in simulation.events
            if event.kind == "action_attempted" and event.actor_id == FOCAL_AGENT_ID
        )
        rejected = next(
            event
            for event in simulation.events
            if event.kind == "action_rejected" and event.actor_id == FOCAL_AGENT_ID
        )
        result = simulation.agent_view(FOCAL_AGENT_ID).action_results[-1]
        self.assertEqual(simulation.agent_view(FOCAL_AGENT_ID).location, "home")
        self.assertEqual(attempted.details["destination"], "allocation_office")
        self.assertEqual(rejected.action_id, attempted.action_id)
        self.assertEqual(rejected.caused_by, (attempted.event_id,))
        self.assertIn("not reachable", rejected.details["reason"])
        self.assertEqual(result.action_id, attempted.action_id)
        self.assertEqual(result.outcome_event_id, rejected.event_id)
        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.reason, rejected.details["reason"])
        self.assertEqual(len(client.inputs), 1)

    def test_later_choice_uses_completed_result_and_persistent_location(self):
        client = ResultResponsiveModelDecisionClient("workplace")
        simulation = build_first_day(
            seed=42, focal_policy=model_policy(client)
        )

        simulation.step()
        simulation.step()
        simulation.step()

        focal_attempts = [
            event
            for event in simulation.events
            if event.kind == "action_attempted" and event.actor_id == FOCAL_AGENT_ID
        ]
        self.assertEqual(
            [event.details["action_kind"] for event in focal_attempts],
            ["travel", "work"],
        )
        self.assertEqual(len(client.inputs), 2)
        later_input = client.inputs[1]
        completed = later_input["decision_history"]["results"][-1]
        self.assertEqual(later_input["state"]["location"], "workplace")
        self.assertEqual(
            later_input["decision_history"]["last_attempt"]["kind"], "travel"
        )
        self.assertEqual(
            later_input["decision_history"]["attempts"],
            [later_input["decision_history"]["last_attempt"]],
        )
        self.assertEqual(completed["action_kind"], "travel")
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(
            focal_attempts[1].details["decision_explanation"],
            "the completed travel placed Mara at workplace",
        )

    def test_later_choice_uses_rejected_result_without_provider_history(self):
        client = ResultResponsiveModelDecisionClient("allocation_office")
        simulation = build_first_day(
            seed=42, focal_policy=model_policy(client)
        )

        simulation.step()
        simulation.step()

        focal_attempts = [
            event
            for event in simulation.events
            if event.kind == "action_attempted" and event.actor_id == FOCAL_AGENT_ID
        ]
        self.assertEqual(
            [event.details["action_kind"] for event in focal_attempts],
            ["travel", "wait"],
        )
        self.assertEqual(len(client.inputs), 2)
        later_input = client.inputs[1]
        rejected = later_input["decision_history"]["results"][-1]
        self.assertEqual(later_input["state"]["location"], "home")
        self.assertEqual(
            later_input["decision_history"]["last_attempt"]["kind"], "travel"
        )
        self.assertEqual(rejected["action_kind"], "travel")
        self.assertEqual(rejected["status"], "rejected")
        self.assertIn("not reachable", rejected["reason"])
        self.assertEqual(
            focal_attempts[1].details["decision_explanation"],
            "the previous travel was rejected: " + rejected["reason"],
        )

    def test_invalid_model_like_values_fail_before_touching_simulation(self):
        simulation = build_first_day(seed=42)
        view = simulation.agent_view(FOCAL_AGENT_ID)
        state_before = simulation.inspector_state()
        events_before = simulation.events
        valid = {
            "kind": "wait",
            "parameters": {},
            "explanation": "wait briefly",
            "decision_reason": "no immediate action is appropriate",
        }
        cyclic_parameters = {}
        cyclic_parameters["self"] = cyclic_parameters
        invalid_values = (
            "I choose to wait.",
            {key: value for key, value in valid.items() if key != "decision_reason"},
            {**valid, "actor_id": "sena-orr"},
            {**valid, "kind": "rewrite_world"},
            {**valid, "parameters": []},
            {**valid, "explanation": ""},
            {**valid, "decision_reason": ""},
            {**valid, "parameters": {"value": object()}},
            {**valid, "parameters": {"nested": {1: "value"}}},
            {**valid, "parameters": cyclic_parameters},
        )

        for response in invalid_values:
            with self.subTest(response=response):
                with self.assertRaises(StructuredChoiceError):
                    structured_choice_to_attempt(view, response)

        self.assertEqual(simulation.inspector_state(), state_before)
        self.assertEqual(simulation.events, events_before)


if __name__ == "__main__":
    unittest.main()
