import unittest

from policies.model_focal_policy import (
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
