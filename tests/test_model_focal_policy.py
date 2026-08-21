import unittest

from policies.model_focal_policy import (
    ModelFocalPolicy,
    StructuredChoiceError,
    structured_choice_to_attempt,
)
from scenarios.first_day import FOCAL_AGENT_ID, build_first_day


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


class StaticModelDecisionClient:
    def __init__(self, response):
        self.response = response
        self.views = []

    def choose(self, view):
        self.views.append(view)
        return self.response


class SequenceModelDecisionClient:
    def __init__(self, *responses):
        self.responses = responses
        self.views = []

    def choose(self, view):
        response = self.responses[len(self.views)]
        self.views.append(view)
        return response


class ResultResponsiveModelDecisionClient:
    def __init__(self, first_destination):
        self.first_destination = first_destination
        self.views = []

    def choose(self, view):
        self.views.append(view)
        if not view.action_results:
            return {
                "kind": "travel",
                "parameters": {"destination": self.first_destination},
                "explanation": f"travel to {self.first_destination}",
                "decision_reason": "the first decision follows the current obligation",
            }
        latest_result = view.action_results[-1]
        if latest_result.status == "completed":
            return {
                "kind": "work",
                "parameters": {},
                "explanation": "begin work after arriving",
                "decision_reason": (
                    f"the completed {latest_result.action_kind} placed Mara at "
                    f"{view.location}"
                ),
            }
        return {
            "kind": "wait",
            "parameters": {},
            "explanation": "wait after the rejected route",
            "decision_reason": (
                f"the previous {latest_result.action_kind} was rejected: "
                f"{latest_result.reason}"
            ),
        }


class ModelFocalPolicyTests(unittest.TestCase):
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
            seed=42, focal_policy=ModelFocalPolicy(client)
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
        self.assertEqual(len(client.views), 1)
        self.assertEqual(client.views[0].agent_id, FOCAL_AGENT_ID)
        self.assertEqual(client.views[0].display_name, "Mara Vale")

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
            seed=42, focal_policy=ModelFocalPolicy(wait_client)
        )
        travelling = build_first_day(
            seed=42, focal_policy=ModelFocalPolicy(travel_client)
        )
        self.assertEqual(waiting.inspector_state(), travelling.inspector_state())

        waiting_snapshots = [waiting.step() for _ in range(3)]
        travelling_snapshots = [travelling.step() for _ in range(3)]

        self.assertEqual(wait_client.views[0], travel_client.views[0])
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
            seed=42, focal_policy=ModelFocalPolicy(client)
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
        self.assertEqual(len(client.views), 2)
        self.assertEqual(client.views[0].action_results, ())
        completed_result = client.views[1].action_results[-1]
        self.assertEqual(completed_result.action_id, travel_attempt.action_id)
        self.assertEqual(completed_result.status, "completed")
        self.assertEqual(completed_result.resolved_tick, 3)

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
            seed=42, focal_policy=ModelFocalPolicy(client)
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
        self.assertEqual(len(client.views), 1)

    def test_later_choice_uses_completed_result_and_persistent_location(self):
        client = ResultResponsiveModelDecisionClient("workplace")
        simulation = build_first_day(
            seed=42, focal_policy=ModelFocalPolicy(client)
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
        self.assertEqual(len(client.views), 2)
        later_view = client.views[1]
        completed = later_view.action_results[-1]
        self.assertEqual(later_view.location, "workplace")
        self.assertEqual(later_view.last_attempt.kind, "travel")
        self.assertEqual(later_view.action_history, (later_view.last_attempt,))
        self.assertEqual(completed.action_kind, "travel")
        self.assertEqual(completed.status, "completed")
        self.assertEqual(
            focal_attempts[1].details["decision_explanation"],
            "the completed travel placed Mara at workplace",
        )

    def test_later_choice_uses_rejected_result_without_provider_history(self):
        client = ResultResponsiveModelDecisionClient("allocation_office")
        simulation = build_first_day(
            seed=42, focal_policy=ModelFocalPolicy(client)
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
        self.assertEqual(len(client.views), 2)
        later_view = client.views[1]
        rejected = later_view.action_results[-1]
        self.assertEqual(later_view.location, "home")
        self.assertEqual(later_view.last_attempt.kind, "travel")
        self.assertEqual(rejected.action_kind, "travel")
        self.assertEqual(rejected.status, "rejected")
        self.assertIn("not reachable", rejected.reason)
        self.assertEqual(
            focal_attempts[1].details["decision_explanation"],
            "the previous travel was rejected: " + rejected.reason,
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
