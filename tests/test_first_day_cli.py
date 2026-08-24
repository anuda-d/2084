import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from policies.mara_harness import MaraHarness
from scenarios.first_day import main


class _FakeOllamaClient:
    instances = []

    def __init__(self, *, base_url, model):
        self.base_url = base_url
        self.model = model
        self.configuration_id = "fake-ollama-configuration"
        self.authorship_identity = None
        self.calls = []
        self.__class__.instances.append(self)

    def choose(self, model_input):
        self.calls.append(model_input)
        return {
            "kind": "wait",
            "parameters": {},
            "explanation": "wait and take stock of the morning",
            "decision_reason": "the immediate obligations can wait one moment",
        }


def _fake_mara_harness_factory(*, base_url, model):
    client = _FakeOllamaClient(base_url=base_url, model=model)
    return MaraHarness.from_client(
        client,
        configuration_id=client.configuration_id,
        authorship_identity=client.authorship_identity,
    )


class FirstDayCliTests(unittest.TestCase):
    def setUp(self):
        _FakeOllamaClient.instances.clear()

    def test_scripted_command_is_the_default_and_constructs_no_live_client(self):
        def unexpected_harness(**kwargs):
            raise AssertionError(f"live harness constructed with {kwargs}")

        output = io.StringIO()
        with redirect_stdout(output):
            result = main(
                ["--seed", "42", "--ticks", "1"],
                mara_harness_factory=unexpected_harness,
            )

        self.assertEqual(result, 0)
        self.assertIn("Action: travel to workplace", output.getvalue())
        self.assertNotIn("fake-ollama-configuration", output.getvalue())

    def test_live_selection_requires_external_endpoint_and_model_before_running(self):
        error = io.StringIO()
        with redirect_stderr(error), self.assertRaises(SystemExit) as raised:
            main(
                ["--focal-policy", "ollama", "--ticks", "1"],
                mara_harness_factory=_fake_mara_harness_factory,
            )

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("--ollama-base-url and --ollama-model are required", error.getvalue())
        self.assertEqual(_FakeOllamaClient.instances, [])

    def test_live_selection_rejects_a_different_model_before_constructing_client(self):
        error = io.StringIO()
        with redirect_stderr(error), self.assertRaises(SystemExit) as raised:
            main(
                [
                    "--focal-policy",
                    "ollama",
                    "--ollama-base-url",
                    "http://127.0.0.1:11434",
                    "--ollama-model",
                    "another-model",
                ],
                mara_harness_factory=_fake_mara_harness_factory,
            )

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("Ollama model must be qwen3:4b-instruct", error.getvalue())
        self.assertEqual(_FakeOllamaClient.instances, [])

    def test_invalid_live_origin_is_a_controlled_cli_error_without_traceback(self):
        error = io.StringIO()
        with redirect_stderr(error), self.assertRaises(SystemExit) as raised:
            main(
                [
                    "--focal-policy",
                    "ollama",
                    "--ollama-base-url",
                    "http://localhost:11434",
                    "--ollama-model",
                    "qwen3:4b-instruct",
                ]
            )

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("Ollama base URL host must be an IP address", error.getvalue())
        self.assertNotIn("Traceback", error.getvalue())
        self.assertEqual(_FakeOllamaClient.instances, [])

    def test_explicit_live_selection_uses_one_client_without_normal_view_leaks(self):
        output = io.StringIO()
        with redirect_stdout(output):
            result = main(
                [
                    "--seed",
                    "42",
                    "--ticks",
                    "1",
                    "--focal-policy",
                    "ollama",
                    "--ollama-base-url",
                    "http://127.0.0.1:11434",
                    "--ollama-model",
                    "qwen3:4b-instruct",
                ],
                mara_harness_factory=_fake_mara_harness_factory,
            )

        self.assertEqual(result, 0)
        self.assertEqual(len(_FakeOllamaClient.instances), 1)
        client = _FakeOllamaClient.instances[0]
        self.assertEqual(client.base_url, "http://127.0.0.1:11434")
        self.assertEqual(client.model, "qwen3:4b-instruct")
        self.assertEqual(len(client.calls), 1)
        self.assertIn("Action: wait and take stock of the morning", output.getvalue())
        self.assertIn("Reason: the immediate obligations can wait one moment", output.getvalue())
        self.assertNotIn("fake-ollama-configuration", output.getvalue())
        self.assertNotIn("127.0.0.1", output.getvalue())


if __name__ == "__main__":
    unittest.main()
