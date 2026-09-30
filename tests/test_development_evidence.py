"""Use real offline audit bundles to test durable runner evidence."""

import contextlib
import io
import os
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from devloop.runner import Runner
from tests import test_development_runner as fixtures
from tests.test_development_completion import result, review
from tests.test_autonomous_day_audit import (
    _ollama_day, _OllamaTransport, _AlwaysUnavailableOllamaTransport,
    _run_with_source_fingerprint, MODEL_IDENTITY,
)
from scenarios.autonomous_day_audit import write_autonomous_day_live_audit


class EvidenceTests(TestCase):
    def setUp(self):
        self.fixture = fixtures.RunnerTests("test_continues_multiple_changes_without_timer_or_new_worker")
        self.fixture.setUp()
        self.parent = tempfile.TemporaryDirectory()
        self.root = Path(self.parent.name) / "evidence"
        self.root.mkdir(mode=0o700)
        self.runner = self.fixture.runner
        self.runner.config.evidence = {"directory":str(self.root), "required_for_completion":["live"]}

    def tearDown(self):
        self.fixture.tearDown()
        self.parent.cleanup()

    def bundle(self, name="accepted", failed=False):
        path = self.root / name
        day = _ollama_day(_AlwaysUnavailableOllamaTransport() if failed else _OllamaTransport())
        summary, source = _run_with_source_fingerprint(day)
        write_autonomous_day_live_audit(day=day, summary=summary, directory=path,
                                       ollama_base_url="http://127.0.0.1:11434",
                                       ollama_model="qwen3:4b-instruct", source_before=source,
                                       model_identity=MODEL_IDENTITY)
        return path

    def register(self, path, identifier="live", classification="supporting"):
        self.runner.evidence.register([dict(id=identifier, path=str(path), classification=classification)])

    def test_required_missing_artifact_prevents_completion_before_review(self):
        calls = []
        def agent(prompt, *, review=False):
            calls.append(review)
            return globals()["review"]() if review else result()
        self.runner.agent = agent
        self.runner.step()
        self.assertEqual(calls, [False])
        self.assertNotEqual(self.runner.store.read()["phase"], "complete")
        self.assertIn("live", self.runner.store.read()["feedback"])

    def test_registered_bundle_survives_restart_and_missing_source_is_visible(self):
        path = self.bundle()
        self.register(path)
        before = self.runner.evidence.fingerprint(require_complete=True)
        restarted = Runner(self.runner.config, clock=lambda:self.fixture.now)
        self.assertEqual(restarted.evidence.fingerprint(require_complete=True), before)
        shutil.rmtree(path)
        with self.assertRaisesRegex(ValueError, "evidence"):
            restarted.evidence.fingerprint(require_complete=True)
        self.assertEqual(restarted.status()["evidence_status"]["artifacts"][0]["availability"], "missing")

    def test_modified_and_substituted_bundle_cannot_reuse_acceptance(self):
        path = self.bundle()
        self.register(path)
        (path / "normal.txt").write_text("modified")
        with self.assertRaisesRegex(ValueError, "evidence"):
            self.runner.evidence.fingerprint(require_complete=True)
        replacement = self.bundle("replacement")
        shutil.rmtree(path)
        path.symlink_to(replacement, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "evidence"):
            self.runner.evidence.fingerprint(require_complete=True)

    def test_contrary_bundle_is_retained_but_does_not_satisfy_required_evidence(self):
        path = self.bundle(failed=True)
        self.register(path, classification="contrary")
        self.assertTrue(path.exists())
        self.runner.evidence.fingerprint(require_complete=False)
        with self.assertRaisesRegex(ValueError, "evidence"):
            self.runner.evidence.fingerprint(require_complete=True)

    def test_identifier_cannot_overwrite_existing_artifact(self):
        self.register(self.bundle())
        with self.assertRaisesRegex(ValueError, "already"):
            self.register(self.bundle("another"))

    def test_evidence_changed_during_commit_cannot_finalize_completion(self):
        path = self.bundle()
        self.register(path)
        def worker(prompt, *, review=False):
            if review:
                return globals()["review"]()
            (self.fixture.root / "app.py").write_text("value = 1\n")
            return result()
        self.runner.agent = worker
        execute = self.runner.executor
        def changed_after_commit(command, **kwargs):
            returned = execute(command, **kwargs)
            if command[:2] == ["git", "commit"]:
                (path / "normal.txt").write_text("Changed during commit")
            return returned
        self.runner.executor = changed_after_commit
        self.runner.step()
        self.assertNotEqual(self.runner.store.read()["phase"], "complete")
        self.assertIsNotNone(self.runner.store.read()["commit_intent"])
        self.assertFalse(self.runner.status()["evidence_status"]["required_available"])

    def test_legacy_missing_artifact_keeps_historical_completion(self):
        self.runner.config.evidence["legacy"] = {"live":str(self.root / "lost")}
        self.runner.store.update(enabled=False, phase="complete", evidence="Previously reviewed")
        self.runner.evidence.migrate()
        state = self.runner.status()
        self.assertEqual(state["phase"], "complete")
        self.assertFalse(state["enabled"])
        self.assertEqual(state["evidence"], "Previously reviewed")
        self.assertEqual(state["evidence_status"]["summary"], "Previously accepted; original live evidence unavailable.")
        self.assertFalse(state.get("goal_review"))

    def test_migration_copies_verifies_and_preserves_original(self):
        path = self.bundle()
        original = Path(self.parent.name) / "legacy"
        path.rename(original)
        self.runner.config.evidence["legacy"] = {"live":str(original)}
        self.runner.store.update(enabled=False, phase="complete")
        self.runner.evidence.migrate()
        self.assertTrue(original.is_dir())
        self.runner.evidence.fingerprint(require_complete=True)
        registered = self.runner.status()["evidence_status"]["artifacts"][0]
        self.assertTrue(Path(registered["path"]).is_relative_to(self.root.resolve()))
        self.assertEqual(registered["availability"], "available")

    def test_cli_rejects_missing_or_outside_audit_before_provider_construction(self):
        from scenarios.autonomous_day import main
        args = ["--focal-policy", "ollama", "--ollama-base-url", "http://127.0.0.1:11434",
                "--ollama-model", "qwen3:4b-instruct"]
        for extra in ([], ["--audit-dir", str(Path(self.parent.name)/"outside")]):
            with self.subTest(extra=extra), patch.dict(os.environ, DEVLOOP_EVIDENCE_DIR=str(self.root)):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    main(args+extra, mara_harness_factory=lambda **_: self.fail("Provider constructed"))
