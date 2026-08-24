import unittest
from unittest.mock import patch

from policies.mara_harness import (
    RECORDED_MARA_CONFIGURATION_ID,
    MaraHarness,
)
from policies.model_focal_policy import ModelUnavailableError
from scenarios.first_day import FOCAL_AGENT_ID, build_first_day
from simulation.agents import DecisionRecordSource


class _StaticClient:
    def __init__(self, response):
        self.response = response
        self.inputs = []

    def choose(self, model_input):
        self.inputs.append(model_input)
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response


class _FakeOllamaClient(_StaticClient):
    instances = []

    def __init__(self, *, base_url, model, timeout_seconds=60):
        super().__init__(
            {
                "kind": "wait",
                "parameters": {},
                "explanation": "wait once",
                "decision_reason": "pause at home",
            }
        )
        self.base_url = base_url
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.configuration_id = "fake-ollama-configuration"
        self.authorship_identity = None
        self.__class__.instances.append(self)


def _wait_response():
    return {
        "kind": "wait",
        "parameters": {},
        "explanation": "wait and inspect the present situation",
        "decision_reason": "the supplied circumstances support pausing",
    }


class MaraHarnessTests(unittest.TestCase):
    def setUp(self):
        _FakeOllamaClient.instances.clear()

    def test_client_choice_becomes_one_unchanged_attempt_and_private_record(self):
        simulation = build_first_day(seed=42)
        view = simulation.agent_view(FOCAL_AGENT_ID)
        response = _wait_response()
        client = _StaticClient(response)
        harness = MaraHarness.from_client(
            client,
            configuration_id="fake-client-v1",
        )

        attempt = harness.choose(view)

        self.assertIsInstance(harness, DecisionRecordSource)
        self.assertEqual(len(client.inputs), 1)
        self.assertEqual(attempt.actor_id, FOCAL_AGENT_ID)
        self.assertEqual(attempt.kind, response["kind"])
        self.assertEqual(dict(attempt.parameters), response["parameters"])
        self.assertEqual(attempt.explanation, response["explanation"])
        self.assertEqual(attempt.decision_reason, response["decision_reason"])
        record = harness.take_decision_record()
        self.assertEqual(record.configuration_id, "fake-client-v1")
        self.assertEqual(record.status, "selected")
        self.assertEqual(record.attempted_action_kind, "wait")
        self.assertIsNone(harness.take_decision_record())

    def test_failure_modes_return_the_existing_safe_wait_without_retry(self):
        failures = (
            (TimeoutError("private timeout detail"), "timeout"),
            (ModelUnavailableError("private server detail"), "unavailable_model"),
            ({"kind": "wait"}, "malformed_response"),
            (
                {
                    "kind": "travel",
                    "parameters": {},
                    "explanation": "travel without naming a destination",
                    "decision_reason": "omit a required action parameter",
                },
                "invalid_attempt",
            ),
        )
        for response, failure_kind in failures:
            with self.subTest(failure_kind=failure_kind):
                view = build_first_day(seed=42).agent_view(FOCAL_AGENT_ID)
                client = _StaticClient(response)
                harness = MaraHarness.from_client(
                    client,
                    configuration_id="failing-client-v1",
                )

                attempt = harness.choose(view)

                self.assertEqual(len(client.inputs), 1)
                self.assertEqual(attempt.kind, "wait")
                self.assertEqual(dict(attempt.parameters), {})
                self.assertEqual(
                    attempt.explanation,
                    "wait because no valid model decision is available",
                )
                self.assertEqual(
                    attempt.decision_reason,
                    f"model decision failed safely: {failure_kind}",
                )
                record = harness.take_decision_record()
                self.assertEqual(record.status, "failed")
                self.assertEqual(record.failure_kind, failure_kind)

    def test_recorded_decision_reproduces_equal_attempt_for_equal_view(self):
        simulation = build_first_day(seed=42)
        view = simulation.agent_view(FOCAL_AGENT_ID)
        source_client = _StaticClient(_wait_response())
        source = MaraHarness.from_client(
            source_client,
            configuration_id="source-client-v1",
        )
        source_attempt = source.choose(view)
        source_record = source.take_decision_record()

        replay = MaraHarness.from_records((source_record,))
        replay_attempt = replay.choose(view)

        self.assertEqual(replay_attempt, source_attempt)
        self.assertEqual(len(source_client.inputs), 1)
        replay_record = replay.take_decision_record()
        self.assertEqual(
            replay_record.configuration_id,
            RECORDED_MARA_CONFIGURATION_ID,
        )
        self.assertEqual(replay_record.model_input, source_record.model_input)

    def test_ollama_construction_stays_behind_the_named_public_facade(self):
        view = build_first_day(seed=42).agent_view(FOCAL_AGENT_ID)
        with patch(
            "policies.mara_harness.OllamaDecisionClient",
            _FakeOllamaClient,
        ):
            harness = MaraHarness.from_ollama(
                base_url="http://127.0.0.1:11434",
                model="qwen3:4b-instruct",
                timeout_seconds=17,
            )
            attempt = harness.choose(view)

        self.assertEqual(len(_FakeOllamaClient.instances), 1)
        client = _FakeOllamaClient.instances[0]
        self.assertEqual(client.base_url, "http://127.0.0.1:11434")
        self.assertEqual(client.model, "qwen3:4b-instruct")
        self.assertEqual(client.timeout_seconds, 17)
        self.assertEqual(len(client.inputs), 1)
        self.assertEqual(attempt.kind, "wait")


if __name__ == "__main__":
    unittest.main()
