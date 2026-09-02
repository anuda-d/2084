import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from policies.mara_harness import MaraHarness
from policies.ollama_client import OllamaDecisionClient, OllamaHttpResponse
from scenarios.autonomous_day import main
from scenarios.autonomous_day_audit import (
    AD12_OLLAMA_MODEL_DIGEST,
    verify_autonomous_day_live_audit,
)


class _FakeOllamaClient:
    instances = []

    def __init__(self, *, base_url, model):
        self.base_url = base_url
        self.model = model
        self.configuration_id = "fake-autonomous-day-ollama-configuration"
        self.authorship_identity = None
        self.calls = []
        self.__class__.instances.append(self)

    def choose(self, model_input):
        self.calls.append(model_input)
        return {
            "kind": "wait",
            "parameters": {},
            "explanation": "remain where the world can advance safely",
            "decision_reason": "no immediate movement is necessary",
        }


def _fake_mara_harness_factory(*, base_url, model):
    client = _FakeOllamaClient(base_url=base_url, model=model)
    return MaraHarness.from_client(
        client,
        configuration_id=client.configuration_id,
        authorship_identity=client.authorship_identity,
    )


class _FakeOllamaTransport:
    instances = []

    def __init__(self):
        self.calls = []
        self.__class__.instances.append(self)

    def post_json(self, *, url, headers, payload, timeout_seconds):
        self.calls.append(payload)
        content = {
            "kind": "wait",
            "parameters": {},
            "explanation": "remain where the world can advance safely",
            "decision_reason": "no immediate movement is necessary",
        }
        return OllamaHttpResponse(
            status=200,
            body=json.dumps(
                {
                    "model": payload["model"],
                    "done": True,
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(content),
                    },
                }
            ).encode("utf-8"),
        )


def _fake_attested_ollama_harness_factory(*, base_url, model):
    client = OllamaDecisionClient(
        base_url=base_url,
        model=model,
        transport=_FakeOllamaTransport(),
    )
    return MaraHarness.from_ollama_client(client)


def _fake_ollama_identity_factory(*, base_url, model):
    return {
        "source": "ollama_api_tags",
        "model": model,
        "digest": AD12_OLLAMA_MODEL_DIGEST,
        "family": "qwen3",
        "parameter_size": "4.0B",
        "quantization_level": "Q4_K_M",
    }


class AutonomousDayCliTests(unittest.TestCase):
    def setUp(self):
        _FakeOllamaClient.instances.clear()
        _FakeOllamaTransport.instances.clear()

    def test_module_command_runs_exact_day_with_focal_safe_output(self):
        result = subprocess.run(
            [sys.executable, "-m", "scenarios.autonomous_day", "--seed", "42"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertIn("Start: Day 0 00:00 | Mara at Home", result.stdout)
        self.assertIn(
            "Day 0 00:00–Day 0 11:00 | No focal updates.", result.stdout
        )
        self.assertIn("Day 0 11:00 | Home transit bulletin", result.stdout)
        self.assertIn(
            "Day 0 11:00–Day 1 00:00 | No focal updates.", result.stdout
        )
        self.assertIn("End: Day 1 00:00", result.stdout)
        self.assertIn("Exact 24-hour boundary reached: yes", result.stdout)
        for hidden in (
            "Ilan",
            "transit_service_changed",
            "action_attempted",
            "work_completed",
            "event-",
            "executed_work",
            "district-transit-authority",
            "peak_restricted_input_bytes",
            "retained_private_record",
        ):
            self.assertNotIn(hidden, result.stdout)

    def test_equal_seed_produces_equal_normal_output(self):
        outputs = []
        for _ in range(2):
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(["--seed", "7"])
            self.assertEqual(exit_code, 0)
            outputs.append(output.getvalue())

        self.assertEqual(outputs[0], outputs[1])

    def test_inspector_is_explicit_and_reconstructs_successful_day(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scenarios.autonomous_day",
                "--seed",
                "42",
                "--inspect",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(
            result.stdout.startswith(
                "2084 AUTONOMOUS DAY INSPECTOR — OMNISCIENT\n"
                "Not part of the normal observer experience.\n"
            )
        )
        data = json.loads(result.stdout[result.stdout.index("{"):])
        self.assertEqual(data["counts"], {
            "action_results": 2,
            "events": 5,
            "observations": 2,
        })
        self.assertEqual(data["model_path"], {
            "configured": False,
            "decision_status_sequence": None,
            "decision_status_counts": None,
            "exercised": False,
            "provider_failure_count": None,
            "growth": None,
        })
        self.assertEqual(data["objective_state"]["tick"], 1440)
        self.assertEqual(
            [item["kind"] for item in data["history"]["events"]],
            [
                "action_attempted",
                "transit_service_changed",
                "action_attempted",
                "wait_completed",
                "work_completed",
            ],
        )
        work_attempted, transit, social_attempted, waited, completed = data[
            "history"
        ]["events"]
        self.assertEqual(completed["caused_by"], [work_attempted["event_id"]])
        self.assertEqual(waited["caused_by"], [social_attempted["event_id"]])
        self.assertTrue(
            all(
                observation["event_id"] == transit["event_id"]
                for observation in data["history"]["observations"]
            )
        )
        self.assertEqual(
            data["history"]["action_results"][1]["outcome_event_id"],
            completed["event_id"],
        )
        self.assertEqual(
            data["history"]["action_results"][0]["outcome_event_id"],
            waited["event_id"],
        )
        self.assertEqual(data["runtime"]["executed_work_count"], 7)
        self.assertEqual(
            [item["kind"] for item in data["runtime"]["executed_work"]],
            [
                "autonomous_day_supporting_work_start",
                "autonomous_day_institutional_service_change",
                "autonomous_day_ilan_transit_observation_delivery",
                "decision_eligibility",
                "autonomous_day_supporting_work_completion",
                "autonomous_day_transit_bulletin_delivery",
                "autonomous_day_mara_transit_understanding_update",
            ],
        )
        self.assertEqual(data["runtime"]["quiet_span_count"], 5)
        self.assertTrue(data["runtime"]["reached_end_boundary"])

    def test_invalid_seed_is_controlled_before_world_construction(self):
        result = subprocess.run(
            [sys.executable, "-m", "scenarios.autonomous_day", "--seed", "invalid"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid int value", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_live_selection_requires_external_endpoint_and_model_before_running(self):
        error = io.StringIO()
        with redirect_stderr(error), self.assertRaises(SystemExit) as raised:
            main(
                ["--focal-policy", "ollama"],
                mara_harness_factory=_fake_mara_harness_factory,
            )

        self.assertEqual(raised.exception.code, 2)
        self.assertIn(
            "--ollama-base-url and --ollama-model are required",
            error.getvalue(),
        )
        self.assertEqual(_FakeOllamaClient.instances, [])

    def test_offline_selection_rejects_live_configuration(self):
        error = io.StringIO()
        with redirect_stderr(error), self.assertRaises(SystemExit) as raised:
            main(
                [
                    "--ollama-base-url",
                    "http://127.0.0.1:11434",
                    "--ollama-model",
                    "qwen3:4b-instruct",
                ],
                mara_harness_factory=_fake_mara_harness_factory,
            )

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("require --focal-policy ollama", error.getvalue())
        self.assertEqual(_FakeOllamaClient.instances, [])

    def test_live_selection_rejects_wrong_model_before_constructing_harness(self):
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
        self.assertIn(
            "Ollama model must be qwen3:4b-instruct",
            error.getvalue(),
        )
        self.assertEqual(_FakeOllamaClient.instances, [])

    def test_invalid_live_origin_is_controlled_without_traceback(self):
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
        self.assertIn(
            "Ollama base URL host must be an IP address",
            error.getvalue(),
        )
        self.assertNotIn("Traceback", error.getvalue())

    def test_explicit_live_selection_completes_one_day_without_normal_leaks(self):
        output = io.StringIO()
        with redirect_stdout(output):
            result = main(
                [
                    "--seed",
                    "42",
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
        self.assertGreater(len(client.calls), 0)
        self.assertLessEqual(len(client.calls), 128)
        self.assertIn("Exact 24-hour boundary reached: yes", output.getvalue())
        self.assertNotIn("127.0.0.1", output.getvalue())
        self.assertNotIn(client.configuration_id, output.getvalue())

    def test_live_inspector_reports_sanitized_model_path_for_same_entry_point(self):
        output = io.StringIO()
        with redirect_stdout(output):
            result = main(
                [
                    "--seed",
                    "42",
                    "--inspect",
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
        document = output.getvalue()
        inspector = json.loads(document[document.index("{") :])
        self.assertTrue(inspector["runtime"]["reached_end_boundary"])
        self.assertTrue(inspector["model_path"]["configured"])
        self.assertTrue(inspector["model_path"]["exercised"])
        self.assertLessEqual(
            inspector["model_path"]["growth"]["peak_restricted_input_bytes"],
            inspector["model_path"]["growth"]["maximum_restricted_input_bytes"],
        )
        self.assertNotIn("127.0.0.1", document)
        self.assertNotIn("fake-autonomous-day-ollama-configuration", document)

    def test_live_selection_writes_one_verified_bundle_without_a_second_client(self):
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as parent:
            audit_path = Path(parent) / "one-live-run"
            with redirect_stdout(output):
                result = main(
                    [
                        "--seed",
                        "42",
                        "--audit-dir",
                        str(audit_path),
                        "--focal-policy",
                        "ollama",
                        "--ollama-base-url",
                        "http://127.0.0.1:11434",
                        "--ollama-model",
                        "qwen3:4b-instruct",
                    ],
                    mara_harness_factory=_fake_attested_ollama_harness_factory,
                    ollama_identity_factory=_fake_ollama_identity_factory,
                )

            self.assertEqual(result, 0)
            self.assertEqual(len(_FakeOllamaTransport.instances), 1)
            transport = _FakeOllamaTransport.instances[0]
            verdict = json.loads((audit_path / "verdict.json").read_text())
            self.assertEqual(
                len(transport.calls),
                verdict["measurements"]["provider_call_attempt_count"],
            )
            self.assertTrue(verify_autonomous_day_live_audit(audit_path)["passed"])
            self.assertNotIn("127.0.0.1", output.getvalue())

    def test_dangling_audit_symlink_is_rejected_before_provider_call(self):
        with tempfile.TemporaryDirectory() as parent:
            audit_path = Path(parent) / "dangling"
            os.symlink(Path(parent) / "missing-target", audit_path)
            error = io.StringIO()
            with redirect_stderr(error), self.assertRaises(SystemExit) as raised:
                main(
                    [
                        "--seed",
                        "42",
                        "--audit-dir",
                        str(audit_path),
                        "--focal-policy",
                        "ollama",
                        "--ollama-base-url",
                        "http://127.0.0.1:11434",
                        "--ollama-model",
                        "qwen3:4b-instruct",
                    ],
                    mara_harness_factory=_fake_attested_ollama_harness_factory,
                    ollama_identity_factory=_fake_ollama_identity_factory,
                )

            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(len(_FakeOllamaTransport.instances), 1)
            self.assertEqual(_FakeOllamaTransport.instances[0].calls, [])
            self.assertIn("already exists", error.getvalue())


if __name__ == "__main__":
    unittest.main()
