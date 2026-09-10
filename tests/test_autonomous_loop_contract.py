import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.check_autonomous_loop_contract import (
    CURRENT_PATHS,
    OBSOLETE_CURRENT_RULES,
    REQUIRED_BY_PATH,
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

    def test_runtime_state_must_remain_stopped_and_unauthorized_at_migration(self):
        state_path = self.root / "docs/plans/AUTONOMOUS_LOOP_STATE.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["authorization"] = {
            "status": "standing",
            "goal_id": "legacy-goal",
            "source": "owner",
        }
        state["phase"] = "ready"
        state_path.write_text(json.dumps(state), encoding="utf-8")

        failures = state_failures(self.root)

        self.assertTrue(any("stopped and unauthorized" in item for item in failures))

    def test_legacy_authorization_discrepancy_is_explicit(self):
        current = (self.root / "docs/plans/CURRENT.md").read_text(encoding="utf-8")
        loop = (self.root / "docs/main/DEVELOPMENT_LOOP.md").read_text(encoding="utf-8")

        self.assertIn("saved automation was paused", loop)
        self.assertIn("legacy authorization is deliberately not imported", current)
        self.assertIn("historical evidence", current)


if __name__ == "__main__":
    unittest.main()
