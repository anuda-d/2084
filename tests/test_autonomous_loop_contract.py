import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.check_autonomous_loop_contract import (
    CURRENT_PATHS,
    OBSOLETE_CURRENT_RULES,
    REQUIRED_BY_PATH,
    current_summary_failures,
    repository_contract_failures,
    state_failures,
)


ROOT = Path(__file__).resolve().parents[1]


class AutonomousLoopContractTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        copied = set(CURRENT_PATHS) | {
            Path("docs/plans/AUTONOMOUS_LOOP_STATE.json"),
            Path("scripts/autonomous_loop_state.py"),
            Path("scripts/autonomous_loop_lock.py"),
        }
        for relative_path in copied:
            destination = self.root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative_path, destination)

    def tearDown(self):
        self.tempdir.cleanup()

    def write_current_summary(
        self,
        *,
        status: str,
        goal: str,
        authorization: str,
        scheduler: str,
    ) -> None:
        current_path = self.root / "docs/plans/CURRENT.md"
        replacements = {
            "Status:": f"Status: {status}",
            "- Active autonomous goal:": f"- Active autonomous goal: {goal}",
            "- Owner authorization:": f"- Owner authorization: {authorization}",
            "- Scheduler status:": f"- Scheduler status: {scheduler}",
        }
        lines = current_path.read_text(encoding="utf-8").splitlines()
        current_path.write_text(
            "\n".join(
                next(
                    (
                        replacement
                        for prefix, replacement in replacements.items()
                        if line.startswith(prefix)
                    ),
                    line,
                )
                for line in lines
            )
            + "\n",
            encoding="utf-8",
        )

    def test_repository_contract_is_consistent(self):
        self.assertEqual(repository_contract_failures(), [])

    def test_each_current_document_requirement_is_enforced(self):
        for relative_path, tokens in REQUIRED_BY_PATH.items():
            for token in tokens:
                with self.subTest(path=relative_path, token=token):
                    path = self.root / relative_path
                    original = path.read_text(encoding="utf-8")
                    path.write_text(original.replace(token, "<removed>"), encoding="utf-8")
                    failures = repository_contract_failures(self.root)
                    self.assertTrue(
                        any(str(path) in failure and token in failure for failure in failures),
                        failures,
                    )
                    path.write_text(original, encoding="utf-8")

    def test_obsolete_one_task_per_slice_rules_are_rejected(self):
        path = self.root / "docs/main/DEVELOPMENT_LOOP.md"
        original = path.read_text(encoding="utf-8")
        for token in OBSOLETE_CURRENT_RULES:
            with self.subTest(token=token):
                path.write_text(original + "\n" + token + "\n", encoding="utf-8")
                failures = repository_contract_failures(self.root)
                self.assertTrue(any(token in failure for failure in failures), failures)
        path.write_text(original, encoding="utf-8")

    def test_runtime_state_must_satisfy_the_production_validator(self):
        state_path = self.root / "docs/plans/AUTONOMOUS_LOOP_STATE.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["schema_version"] = 999
        state_path.write_text(json.dumps(state), encoding="utf-8")

        failures = state_failures(self.root)

        self.assertTrue(any("UNSUPPORTED_SCHEMA_VERSION" in item for item in failures))

    def test_ready_state_rejects_an_inactive_current_summary(self):
        state_path = self.root / "docs/plans/AUTONOMOUS_LOOP_STATE.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["authorization"] = {
            "goal_id": "first-consequential-choice",
            "source": "owner",
            "status": "standing",
        }
        state["phase"] = "ready"
        state["stop_reason"] = None
        state_path.write_text(json.dumps(state), encoding="utf-8")
        self.write_current_summary(
            status="autonomous development is stopped for this fixture",
            goal="none",
            authorization="none",
            scheduler="paused",
        )

        failures = current_summary_failures(self.root)

        self.assertIn("CURRENT_GOAL_MISMATCH", failures)
        self.assertIn("CURRENT_AUTHORIZATION_MISMATCH", failures)
        self.assertIn("CURRENT_SCHEDULER_MISMATCH", failures)

    def test_ready_state_rejects_an_unknown_scheduler_summary(self):
        current_path = self.root / "docs/plans/CURRENT.md"
        current = current_path.read_text(encoding="utf-8")
        scheduler_line = next(
            line
            for line in current.splitlines()
            if line.startswith("- Scheduler status:")
        )
        current = current.replace(
            scheduler_line,
            "- Scheduler status: unknown",
        )
        current_path.write_text(current, encoding="utf-8")

        failures = current_summary_failures(self.root)

        self.assertIn("CURRENT_SCHEDULER_MISMATCH", failures)

    def test_active_orchestrator_and_slice_require_exact_current_identifiers(self):
        state_path = self.root / "docs/plans/AUTONOMOUS_LOOP_STATE.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["orchestrator"] = {
            "accepted_slices": 0,
            "generation_id": "gen-test",
            "recovery_count": 0,
            "task_id": "orch-test",
        }
        state["slice"] = {"slice_id": "slice-test"}
        state_path.write_text(json.dumps(state), encoding="utf-8")

        failures = current_summary_failures(self.root)

        self.assertIn("CURRENT_ORCHESTRATOR_MISMATCH", failures)
        self.assertIn("CURRENT_SLICE_MISMATCH", failures)

    def test_stopped_state_rejects_an_active_current_summary(self):
        state_path = self.root / "docs/plans/AUTONOMOUS_LOOP_STATE.json"
        state_path.write_text(
            json.dumps(
                {
                    "authorization": {
                        "goal_id": None,
                        "source": None,
                        "status": "none",
                    },
                    "events": [],
                    "last_handoff": None,
                    "orchestrator": None,
                    "phase": "stopped",
                    "revision": 0,
                    "schema_version": 2,
                    "slice": None,
                    "stop_reason": "owner_stopped",
                    "writer_history": [],
                }
            ),
            encoding="utf-8",
        )
        self.write_current_summary(
            status="autonomous development is active for this fixture",
            goal=(
                "[First Consequential Choice Under Conflicting Information]"
                "(first-consequential-choice/GOAL.md)"
            ),
            authorization="standing for the active goal",
            scheduler="active",
        )

        failures = current_summary_failures(self.root)

        self.assertIn("CURRENT_GOAL_MISMATCH", failures)
        self.assertIn("CURRENT_AUTHORIZATION_MISMATCH", failures)
        self.assertIn("CURRENT_SCHEDULER_MISMATCH", failures)
        self.assertIn("CURRENT_PHASE_MISMATCH", failures)

    def test_legacy_authorization_discrepancy_is_explicit(self):
        current = (self.root / "docs/plans/CURRENT.md").read_text(encoding="utf-8")
        loop = (self.root / "docs/main/DEVELOPMENT_LOOP.md").read_text(encoding="utf-8")

        self.assertIn("saved automation was paused", loop)
        self.assertIn("legacy authorization is deliberately not imported", current)
        self.assertIn("historical evidence", current)


if __name__ == "__main__":
    unittest.main()
