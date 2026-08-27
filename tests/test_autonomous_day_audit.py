import json
from hashlib import sha256
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock

from policies.mara_harness import MaraHarness
from policies.model_focal_policy import RecordedDecisionArchive
from policies.ollama_client import OllamaDecisionClient, OllamaHttpResponse
from scenarios.autonomous_day import build_autonomous_day
from scenarios.autonomous_day_audit import (
    AD12_OLLAMA_MODEL_DIGEST,
    AUDIT_ARTIFACT_NAMES,
    capture_live_audit_source_state,
    fetch_ollama_model_identity,
    reserve_live_audit_directory,
    verify_autonomous_day_live_audit,
    write_autonomous_day_live_audit,
)


MODEL_IDENTITY = {
    "source": "ollama_api_tags",
    "model": "qwen3:4b-instruct",
    "digest": AD12_OLLAMA_MODEL_DIGEST,
    "family": "qwen3",
    "parameter_size": "4.0B",
    "quantization_level": "Q4_K_M",
}


class _OllamaTransport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def post_json(self, *, url, headers, payload, timeout_seconds):
        self.calls.append(payload)
        response = self.responses.pop(0) if self.responses else {
            "kind": "wait",
            "parameters": {},
            "explanation": "wait while the scheduled world continues",
            "decision_reason": "there is no immediate need to move",
        }
        if isinstance(response, BaseException):
            raise response
        return OllamaHttpResponse(
            status=200,
            body=json.dumps(
                {
                    "model": payload["model"],
                    "done": True,
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(response),
                    },
                }
            ).encode("utf-8"),
        )


class _InjectedWaitClient:
    def choose(self, model_input):
        return {
            "kind": "wait",
            "parameters": {},
            "explanation": "wait through an injected client",
            "decision_reason": "this is not Ollama provenance",
        }


class _AlwaysUnavailableOllamaTransport:
    def post_json(self, *, url, headers, payload, timeout_seconds):
        raise TimeoutError("private provider detail")


class _TagsResponse:
    status = 200

    def __init__(self, document):
        self.body = json.dumps(document).encode("utf-8")

    def read(self, maximum_bytes):
        return self.body[:maximum_bytes]


class _TagsConnection:
    def __init__(self, document):
        self.document = document
        self.requests = []
        self.closed = False

    def request(self, method, path, headers):
        self.requests.append((method, path, headers))

    def getresponse(self):
        return _TagsResponse(self.document)

    def close(self):
        self.closed = True


def _ollama_day(transport, *, seed=42):
    client = OllamaDecisionClient(
        base_url="http://127.0.0.1:11434",
        model="qwen3:4b-instruct",
        transport=transport,
    )
    return build_autonomous_day(
        seed=seed,
        mara_harness=MaraHarness.from_ollama_client(client),
    )


def _run_with_source_fingerprint(day):
    source_before = capture_live_audit_source_state()
    summary = day.run()
    return summary, source_before


class AutonomousDayAuditTests(unittest.TestCase):
    def test_model_identity_preflight_pins_exact_published_weights(self):
        document = {
            "models": [
                {
                    "name": "qwen3:4b-instruct",
                    "model": "qwen3:4b-instruct",
                    "digest": AD12_OLLAMA_MODEL_DIGEST,
                    "details": {
                        "family": "qwen3",
                        "parameter_size": "4.0B",
                        "quantization_level": "Q4_K_M",
                    },
                }
            ]
        }
        connection = _TagsConnection(document)
        identity = fetch_ollama_model_identity(
            base_url="http://127.0.0.1:11434",
            model="qwen3:4b-instruct",
            connection_factory=lambda host, port, timeout: connection,
        )

        self.assertEqual(identity, MODEL_IDENTITY)
        self.assertEqual(connection.requests[0][:2], ("GET", "/api/tags"))
        self.assertTrue(connection.closed)

        document["models"][0]["digest"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "digest does not match"):
            fetch_ollama_model_identity(
                base_url="http://127.0.0.1:11434",
                model="qwen3:4b-instruct",
                connection_factory=lambda host, port, timeout: _TagsConnection(
                    document
                ),
            )

    def test_bundle_is_private_complete_replay_equal_and_integrity_checked(self):
        day = _ollama_day(_OllamaTransport())
        summary, source_before = _run_with_source_fingerprint(day)

        with tempfile.TemporaryDirectory() as parent:
            audit_path = Path(parent) / "live-audit"
            result = write_autonomous_day_live_audit(
                day=day,
                summary=summary,
                directory=audit_path,
                ollama_base_url="http://127.0.0.1:11434",
                ollama_model="qwen3:4b-instruct",
                source_before=source_before,
                model_identity=MODEL_IDENTITY,
            )

            self.assertTrue(result.passed)
            self.assertEqual(
                {path.name for path in audit_path.iterdir()},
                {*AUDIT_ARTIFACT_NAMES, "manifest.json"},
            )
            self.assertEqual(stat.S_IMODE(audit_path.stat().st_mode), 0o700)
            for artifact in audit_path.iterdir():
                self.assertEqual(stat.S_IMODE(artifact.stat().st_mode), 0o600)

            verdict = json.loads((audit_path / "verdict.json").read_text())
            self.assertTrue(verdict["passed"])
            self.assertTrue(all(verdict["checks"].values()))
            self.assertGreater(verdict["measurements"]["provider_selected_count"], 0)
            self.assertLessEqual(
                verdict["measurements"]["decision_count"],
                128,
            )
            manifest = json.loads((audit_path / "manifest.json").read_text())
            self.assertEqual(manifest["model"], "qwen3:4b-instruct")
            self.assertRegex(
                manifest["source"]["before"]["revision"],
                r"^[0-9a-f]{40}$",
            )
            self.assertTrue(manifest["source"]["unchanged_during_run"])
            self.assertIsInstance(
                manifest["source"]["before"]["clean"],
                bool,
            )
            self.assertRegex(
                manifest["source"]["before"]["working_diff_sha256"],
                r"^[0-9a-f]{64}$",
            )
            self.assertEqual(manifest["provider_adapter"], "ollama")
            self.assertEqual(manifest["model_identity"], MODEL_IDENTITY)
            for artifact_name in AUDIT_ARTIFACT_NAMES:
                self.assertRegex(
                    manifest["artifacts"][artifact_name]["sha256"],
                    r"^[0-9a-f]{64}$",
                )

            endpoint = "http://127.0.0.1:11434"
            self.assertTrue(
                all(
                    endpoint not in artifact.read_text()
                    for artifact in audit_path.iterdir()
                )
            )
            self.assertTrue(verify_autonomous_day_live_audit(audit_path)["passed"])

            verdict_path = audit_path / "verdict.json"
            original_verdict = verdict_path.read_bytes()
            verdict_path.write_text("[]", encoding="utf-8")
            wrong_verdict_shape = verify_autonomous_day_live_audit(audit_path)
            self.assertFalse(wrong_verdict_shape["passed"])
            self.assertIn("verdict_unreadable", wrong_verdict_shape["errors"])
            verdict_path.write_bytes(original_verdict)

            (audit_path / "normal.txt").write_text("tampered", encoding="utf-8")
            tampered = verify_autonomous_day_live_audit(audit_path)
            self.assertFalse(tampered["passed"])
            self.assertIn("sha256:normal.txt", tampered["errors"])

            (audit_path / "manifest.json").write_text("not json", encoding="utf-8")
            damaged_manifest = verify_autonomous_day_live_audit(audit_path)
            self.assertFalse(damaged_manifest["passed"])
            self.assertIn("manifest_unreadable", damaged_manifest["errors"])

            (audit_path / "manifest.json").write_text("[]", encoding="utf-8")
            wrong_shape = verify_autonomous_day_live_audit(audit_path)
            self.assertFalse(wrong_shape["passed"])
            self.assertIn("manifest_unreadable", wrong_shape["errors"])

    def test_bundle_accepts_the_runtime_negative_integer_seed_domain(self):
        day = _ollama_day(_OllamaTransport(), seed=-1)
        summary, source_before = _run_with_source_fingerprint(day)

        with tempfile.TemporaryDirectory() as parent:
            result = write_autonomous_day_live_audit(
                day=day,
                summary=summary,
                directory=Path(parent) / "negative-seed-audit",
                ollama_base_url="http://127.0.0.1:11434",
                ollama_model="qwen3:4b-instruct",
                source_before=source_before,
                model_identity=MODEL_IDENTITY,
            )

            self.assertTrue(result.passed)
            self.assertTrue(
                verify_autonomous_day_live_audit(result.directory)["passed"]
            )

    def test_existing_target_is_rejected_without_overwrite(self):
        day = _ollama_day(_OllamaTransport())
        summary, source_before = _run_with_source_fingerprint(day)

        with tempfile.TemporaryDirectory() as parent:
            audit_path = Path(parent) / "existing"
            audit_path.mkdir()
            sentinel = audit_path / "sentinel.txt"
            sentinel.write_text("keep", encoding="utf-8")

            with self.assertRaisesRegex(FileExistsError, "already exists"):
                write_autonomous_day_live_audit(
                    day=day,
                    summary=summary,
                    directory=audit_path,
                    ollama_base_url="http://127.0.0.1:11434",
                    ollama_model="qwen3:4b-instruct",
                    source_before=source_before,
                    model_identity=MODEL_IDENTITY,
                )

            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_reserved_inode_receives_writes_when_path_is_replaced(self):
        day = _ollama_day(_OllamaTransport())
        summary, source_before = _run_with_source_fingerprint(day)

        with tempfile.TemporaryDirectory() as parent:
            audit_path = Path(parent) / "reserved"
            displaced_path = Path(parent) / "displaced-original"
            reservation = reserve_live_audit_directory(audit_path)

            def replace_reserved_path():
                audit_path.replace(displaced_path)
                audit_path.mkdir(mode=0o700)
                return source_before

            with mock.patch(
                "scenarios.autonomous_day_audit.capture_live_audit_source_state",
                side_effect=replace_reserved_path,
            ):
                result = write_autonomous_day_live_audit(
                    day=day,
                    summary=summary,
                    directory=audit_path,
                    ollama_base_url="http://127.0.0.1:11434",
                    ollama_model="qwen3:4b-instruct",
                    source_before=source_before,
                    model_identity=MODEL_IDENTITY,
                    reservation=reservation,
                )

            self.assertFalse(result.passed)
            self.assertEqual(list(audit_path.iterdir()), [])
            self.assertEqual(
                {path.name for path in displaced_path.iterdir()},
                {*AUDIT_ARTIFACT_NAMES, "manifest.json"},
            )

    def test_verifier_validates_unhashed_provenance_and_exact_verdict_schema(self):
        day = _ollama_day(_OllamaTransport())
        summary, source_before = _run_with_source_fingerprint(day)

        with tempfile.TemporaryDirectory() as parent:
            audit_path = Path(parent) / "provenance-audit"
            write_autonomous_day_live_audit(
                day=day,
                summary=summary,
                directory=audit_path,
                ollama_base_url="http://127.0.0.1:11434",
                ollama_model="qwen3:4b-instruct",
                source_before=source_before,
                model_identity=MODEL_IDENTITY,
            )
            manifest_path = audit_path / "manifest.json"
            original_manifest = manifest_path.read_bytes()
            manifest = json.loads(original_manifest)

            for field, damaged_value in (
                ("model_identity", {"digest": "wrong"}),
                ("provider_adapter", "recorded"),
                ("source", "not-source-evidence"),
            ):
                damaged_manifest = dict(manifest)
                damaged_manifest[field] = damaged_value
                manifest_path.write_text(
                    json.dumps(damaged_manifest),
                    encoding="utf-8",
                )
                verification = verify_autonomous_day_live_audit(audit_path)
                self.assertFalse(verification["passed"])
                self.assertIn("manifest_provenance", verification["errors"])

            verdict_path = audit_path / "verdict.json"
            damaged_verdict = b'{"passed":true}\n'
            verdict_path.write_bytes(damaged_verdict)
            manifest["artifacts"]["verdict.json"] = {
                "sha256": sha256(damaged_verdict).hexdigest(),
                "bytes": len(damaged_verdict),
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            verification = verify_autonomous_day_live_audit(audit_path)
            self.assertFalse(verification["passed"])
            self.assertIn("verdict_unreadable", verification["errors"])

    def test_verifier_rejects_links_and_recursive_json_without_throwing(self):
        day = _ollama_day(_OllamaTransport())
        summary, source_before = _run_with_source_fingerprint(day)

        with tempfile.TemporaryDirectory() as parent:
            parent_path = Path(parent)
            audit_path = parent_path / "link-audit"
            write_autonomous_day_live_audit(
                day=day,
                summary=summary,
                directory=audit_path,
                ollama_base_url="http://127.0.0.1:11434",
                ollama_model="qwen3:4b-instruct",
                source_before=source_before,
                model_identity=MODEL_IDENTITY,
            )

            hardlink = parent_path / "normal-hardlink"
            os.link(audit_path / "normal.txt", hardlink)
            hardlinked = verify_autonomous_day_live_audit(audit_path)
            self.assertFalse(hardlinked["passed"])
            self.assertIn("unreadable:normal.txt", hardlinked["errors"])
            hardlink.unlink()

            external_normal = parent_path / "external-normal.txt"
            (audit_path / "normal.txt").replace(external_normal)
            os.symlink(external_normal, audit_path / "normal.txt")
            symlinked_file = verify_autonomous_day_live_audit(audit_path)
            self.assertFalse(symlinked_file["passed"])
            self.assertIn("unreadable:normal.txt", symlinked_file["errors"])
            (audit_path / "normal.txt").unlink()
            external_normal.replace(audit_path / "normal.txt")

            recursive_json = "[" * 10_000 + "0" + "]" * 10_000
            verdict_path = audit_path / "verdict.json"
            original_verdict = verdict_path.read_bytes()
            verdict_path.write_text(recursive_json, encoding="utf-8")
            recursive_verdict = verify_autonomous_day_live_audit(audit_path)
            self.assertFalse(recursive_verdict["passed"])
            self.assertIn("verdict_unreadable", recursive_verdict["errors"])
            verdict_path.write_bytes(original_verdict)

            manifest_path = audit_path / "manifest.json"
            manifest_path.write_text(recursive_json, encoding="utf-8")
            recursive_manifest = verify_autonomous_day_live_audit(audit_path)
            self.assertFalse(recursive_manifest["passed"])
            self.assertIn("manifest_unreadable", recursive_manifest["errors"])

            real_directory = parent_path / "real-audit"
            audit_path.replace(real_directory)
            os.symlink(real_directory, audit_path)
            symlinked_directory = verify_autonomous_day_live_audit(audit_path)
            self.assertFalse(symlinked_directory["passed"])
            self.assertIn(
                "audit_directory_unreadable",
                symlinked_directory["errors"],
            )

    def test_changed_source_fingerprint_and_repository_target_fail_closed(self):
        repository_target = Path(__file__).resolve().parents[1] / "private-audit"
        with self.assertRaisesRegex(ValueError, "outside the repository"):
            reserve_live_audit_directory(repository_target)

        day = _ollama_day(_OllamaTransport())
        summary, source_before = _run_with_source_fingerprint(day)
        stale_source = dict(source_before)
        stale_source["revision"] = "0" * 40
        with tempfile.TemporaryDirectory() as parent:
            result = write_autonomous_day_live_audit(
                day=day,
                summary=summary,
                directory=Path(parent) / "stale-source",
                ollama_base_url="http://127.0.0.1:11434",
                ollama_model="qwen3:4b-instruct",
                source_before=stale_source,
                model_identity=MODEL_IDENTITY,
            )
            self.assertFalse(result.passed)
            self.assertFalse(
                result.verdict["checks"]["source_unchanged_during_run"]
            )

    def test_provider_failures_reach_boundary_but_fail_live_selection_verdict(self):
        day = _ollama_day(_AlwaysUnavailableOllamaTransport())
        summary, source_before = _run_with_source_fingerprint(day)
        self.assertTrue(summary.reached_end_boundary)

        with tempfile.TemporaryDirectory() as parent:
            result = write_autonomous_day_live_audit(
                day=day,
                summary=summary,
                directory=Path(parent) / "failed-live-audit",
                ollama_base_url="http://127.0.0.1:11434",
                ollama_model="qwen3:4b-instruct",
                source_before=source_before,
                model_identity=MODEL_IDENTITY,
            )

            self.assertFalse(result.passed)
            self.assertFalse(
                result.verdict["checks"]["provider_selected_at_least_once"]
            )
            self.assertGreater(
                result.verdict["measurements"]["provider_failure_count"],
                0,
            )
            self.assertTrue(result.verdict["checks"]["recorded_replay_equal"])

    def test_injected_and_recorded_harnesses_cannot_attest_live_ollama(self):
        injected = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_client(
                _InjectedWaitClient(),
                configuration_id="injected-client",
            ),
        )
        injected_summary, injected_source_before = _run_with_source_fingerprint(
            injected
        )

        with tempfile.TemporaryDirectory() as parent:
            injected_result = write_autonomous_day_live_audit(
                day=injected,
                summary=injected_summary,
                directory=Path(parent) / "injected",
                ollama_base_url="http://127.0.0.1:11434",
                ollama_model="qwen3:4b-instruct",
                source_before=injected_source_before,
                model_identity=MODEL_IDENTITY,
            )
            self.assertFalse(injected_result.passed)
            self.assertFalse(
                injected_result.verdict["checks"]["provider_adapter_is_ollama"]
            )

        source = _ollama_day(_OllamaTransport())
        source.run()
        integrity_key = b"audit-recorded-provider-kind"
        archive = RecordedDecisionArchive.seal(
            source.private_decision_records,
            integrity_key=integrity_key,
        )
        recorded = build_autonomous_day(
            seed=42,
            mara_harness=MaraHarness.from_recorded_archive(
                archive,
                integrity_key=integrity_key,
            ),
        )
        recorded_summary, recorded_source_before = _run_with_source_fingerprint(
            recorded
        )
        with tempfile.TemporaryDirectory() as parent:
            recorded_result = write_autonomous_day_live_audit(
                day=recorded,
                summary=recorded_summary,
                directory=Path(parent) / "recorded",
                ollama_base_url="http://127.0.0.1:11434",
                ollama_model="qwen3:4b-instruct",
                source_before=recorded_source_before,
                model_identity=MODEL_IDENTITY,
            )
            self.assertFalse(recorded_result.passed)
            self.assertFalse(
                recorded_result.verdict["checks"]["provider_adapter_is_ollama"]
            )


if __name__ == "__main__":
    unittest.main()
