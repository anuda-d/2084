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
