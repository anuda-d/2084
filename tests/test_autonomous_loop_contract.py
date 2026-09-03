import tempfile
import unittest
from pathlib import Path

from scripts.check_autonomous_loop_contract import (
    COMMON_REQUIREMENTS,
    CONTRACT_PATHS,
    OBSOLETE_RULES,
    ROOT,
    current_state_failures,
    repository_contract_failures,
)


class AutonomousLoopContractTests(unittest.TestCase):
    def fixture_root(self):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = Path(tempdir.name)
        copied_paths = CONTRACT_PATHS + (Path("scripts/autonomous_loop_lock.py"),)
        for relative_path in copied_paths:
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                (ROOT / relative_path).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        return root

    def active_state_fixture(self, owner_authorization="standing"):
        root = self.fixture_root()
        current_path = root / "docs/plans/CURRENT.md"
        current_text = current_path.read_text(encoding="utf-8")
        active_status = (
            "Status: Sample Goal is active under standing scheduled authorization."
            if owner_authorization == "standing"
            else "Status: Sample Goal is active with owner authorization paused."
        )
        current_text = current_text.replace("Status: no active goal.", active_status, 1)
        current_text = current_text.replace(
            "- Active goal: none\n",
            "- Goal: [Sample Goal](sample-goal/GOAL.md)\n"
            "- Shared implementation state: "
            "[Implementation Plan](sample-goal/IMPLEMENTATION_PLAN.md)\n",
            1,
        )
        replacements = {
            "- Active goal id: none": "- Active goal id: sample-goal",
            "- Owner authorization: pending": (
                f"- Owner authorization: {owner_authorization}"
            ),
            "- Authorization scope: none": "- Authorization scope: active goal",
            "- Authorization source: none": "- Authorization source: owner",
            "- Loop cadence: stopped": (
                "- Loop cadence: scheduled autonomous relay"
                if owner_authorization == "standing"
                else "- Loop cadence: paused"
            ),
            "- Fresh-task relay: stopped": (
                "- Fresh-task relay: active"
                if owner_authorization == "standing"
                else "- Fresh-task relay: paused"
            ),
            "- Standing implementation authority: none": (
                "- Standing implementation authority: active"
                if owner_authorization == "standing"
                else "- Standing implementation authority: paused"
            ),
        }
        replacements["- Run status: none"] = (
            "- Run status: awaiting scheduled fresh task"
            if owner_authorization == "standing"
            else "- Run status: paused"
        )
        for old, new in replacements.items():
            current_text = current_text.replace(old, new, 1)
        current_path.write_text(current_text, encoding="utf-8")

        goal_path = root / "docs/plans/sample-goal/GOAL.md"
        goal_path.parent.mkdir(parents=True, exist_ok=True)
        goal_path.write_text(
            "# Sample Goal\n\nStatus: active; owner-approved goal.\n",
            encoding="utf-8",
        )
        state_path = goal_path.parent / "IMPLEMENTATION_PLAN.md"
        state_path.write_text(
            "# Implementation Plan\n\n"
            "## Run State Snapshot\n\n"
            + "\n".join(
                line
                for line in current_text.splitlines()
                if line.startswith("- ")
                and line.split(":", 1)[0][2:] in {
                    "Active goal id",
                    "Owner authorization",
                    "Authorization scope",
                    "Authorization source",
                    "Loop cadence",
                    "Current run",
                    "Incomplete run",
                    "Run status",
                    "Pending owner decision",
                    "Scheduled window",
                    "Fresh-task relay",
                    "Alignment due",
                    "Standing implementation authority",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return root, current_path, goal_path

    def test_repository_uses_the_fresh_task_contract(self):
        failures = repository_contract_failures()

        self.assertEqual(failures, [], "\n".join(failures))

    def test_each_fresh_task_clause_is_load_bearing(self):
        for relative_path in CONTRACT_PATHS:
            for token in COMMON_REQUIREMENTS:
                with self.subTest(path=relative_path, token=token):
                    root = self.fixture_root()
                    path = root / relative_path
                    text = path.read_text(encoding="utf-8")
                    self.assertIn(token, text)
                    path.write_text(text.replace(token, "<removed>"), encoding="utf-8")

                    failures = repository_contract_failures(root)

                    self.assertTrue(
                        any(str(path) in failure and token in failure for failure in failures),
                        failures,
                    )

    def test_contract_requires_the_lean_lock_lifecycle(self):
        lifecycle = (
            "Read-only work does not require checkout ownership",
            "Immediately before the first repository write",
            "Assert ownership after any resumed turn and immediately before commit",
            "Release ownership at completion",
            "recover --expected-task-id",
        )

        for relative_path in CONTRACT_PATHS:
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            for requirement in lifecycle:
                with self.subTest(path=relative_path, requirement=requirement):
                    self.assertIn(requirement, text)

    def test_contract_requires_assertion_before_commit_and_release_after_handoff(self):
        root = self.fixture_root()
        path = root / "docs/main/DEVELOPMENT_LOOP.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.replace(
                "9. assert checkout ownership and create one local commit;",
                "9. create one local commit;",
                1,
            ),
            encoding="utf-8",
        )

        failures = repository_contract_failures(root)

        self.assertTrue(any("ordered lifecycle token" in failure for failure in failures))

    def test_contract_requires_release_on_each_owned_terminal_path(self):
        removals = (
            "11. release checkout ownership;",
            "If the current task owns checkout ownership, release it after writing the\n  blocked handoff and before stopping.",
            "If the current task owns checkout ownership, release it after writing the\nhandoff and before stopping.",
            "write the handoff, release ownership if the\ncurrent task owns the record, and do not relay.",
        )
        for removal in removals:
            with self.subTest(removal=removal):
                root = self.fixture_root()
                path = root / "docs/main/DEVELOPMENT_LOOP.md"
                text = path.read_text(encoding="utf-8")
                path.write_text(text.replace(removal, "", 1), encoding="utf-8")

                failures = repository_contract_failures(root)

                self.assertTrue(any("ordered lifecycle token" in failure for failure in failures))

        root = self.fixture_root()
        path = root / "docs/main/DEVELOPMENT_LOOP.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.replace(
                "If the current task owns checkout ownership, release it after writing the\nhandoff and before stopping.",
                "",
                1,
            ),
            encoding="utf-8",
        )

        failures = repository_contract_failures(root)

        self.assertTrue(any("ordered lifecycle token" in failure for failure in failures))

    def test_contract_rejects_relocated_normal_commit_lifecycle(self):
        root = self.fixture_root()
        path = root / "docs/main/DEVELOPMENT_LOOP.md"
        text = path.read_text(encoding="utf-8")
        sequence = (
            "9. assert checkout ownership and create one local commit;\n"
            "10. write the temporary handoff with `No next unit selected`;\n"
            "11. assert checkout ownership, release checkout ownership, and enter\n"
            "    handoff-only state;"
        )
        self.assertIn(sequence, text)
        path.write_text(text.replace(sequence, "", 1) + "\n" + sequence, encoding="utf-8")

        failures = repository_contract_failures(root)

        self.assertTrue(any("Accept, Commit, Hand Off, Relay" in failure for failure in failures))

        root = self.fixture_root()
        path = root / "docs/main/DEVELOPMENT_LOOP.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.replace(
                "11. assert checkout ownership, release checkout ownership, and enter",
                "11. enter",
                1,
            ),
            encoding="utf-8",
        )

        failures = repository_contract_failures(root)

        self.assertTrue(any("ordered lifecycle token" in failure for failure in failures))

    def test_obsolete_same_task_and_takeover_rules_are_rejected(self):
        for relative_path in CONTRACT_PATHS:
            for rule in OBSOLETE_RULES:
                with self.subTest(path=relative_path, rule=rule):
                    root = self.fixture_root()
                    path = root / relative_path
                    path.write_text(
                        path.read_text(encoding="utf-8") + f"\n{rule}\n",
                        encoding="utf-8",
                    )

                    failures = repository_contract_failures(root)

                    self.assertTrue(any(rule in failure for failure in failures), failures)

    def test_no_goal_state_is_stopped_and_pending_owner_authorization(self):
        failures = current_state_failures()

        self.assertEqual(failures, [], "\n".join(failures))

    def test_no_goal_state_rejects_an_active_relay(self):
        root = self.fixture_root()
        current_path = root / "docs/plans/CURRENT.md"
        text = current_path.read_text(encoding="utf-8")
        current_path.write_text(
            text.replace("- Fresh-task relay: stopped", "- Fresh-task relay: active", 1),
            encoding="utf-8",
        )

        failures = current_state_failures(root)

        self.assertTrue(any("Fresh-task relay" in failure for failure in failures), failures)

    def test_no_goal_state_rejects_a_hidden_active_goal(self):
        root = self.fixture_root()
        hidden_goal = root / "docs/plans/hidden-goal/GOAL.md"
        hidden_goal.parent.mkdir(parents=True, exist_ok=True)
        hidden_goal.write_text(
            "# Hidden Goal\n\nStatus: active; owner-approved goal.\n",
            encoding="utf-8",
        )

        failures = current_state_failures(root)

        self.assertTrue(any("zero active goals" in failure for failure in failures), failures)

    def test_current_and_incomplete_run_fields_are_required(self):
        root = self.fixture_root()
        current_path = root / "docs/plans/CURRENT.md"
        text = current_path.read_text(encoding="utf-8")
        current_path.write_text(
            text.replace("- Incomplete run: none\n", "", 1),
            encoding="utf-8",
        )

        failures = current_state_failures(root)

        self.assertTrue(any("Incomplete run" in failure for failure in failures), failures)

    def test_standing_active_goal_binds_goal_and_state(self):
        root, _, _ = self.active_state_fixture()

        failures = current_state_failures(root)

        self.assertEqual(failures, [], "\n".join(failures))

    def test_owner_paused_active_goal_is_valid(self):
        root, _, _ = self.active_state_fixture(owner_authorization="paused")

        failures = current_state_failures(root)

        self.assertEqual(failures, [], "\n".join(failures))

    def test_unrelated_active_goal_cannot_supply_authority(self):
        root, _, linked_goal_path = self.active_state_fixture()
        linked_goal_path.write_text(
            "# Sample Goal\n\nStatus: deferred; not active.\n",
            encoding="utf-8",
        )
        unrelated_goal = root / "docs/plans/unrelated/GOAL.md"
        unrelated_goal.parent.mkdir(parents=True, exist_ok=True)
        unrelated_goal.write_text(
            "# Unrelated Goal\n\nStatus: active; owner-approved goal.\n",
            encoding="utf-8",
        )

        failures = current_state_failures(root)

        self.assertTrue(
            any("linked goal must be the only active goal" in failure for failure in failures),
            failures,
        )

    def test_active_goal_rejects_no_goal_status_line(self):
        root, current_path, _ = self.active_state_fixture()
        text = current_path.read_text(encoding="utf-8")
        current_path.write_text(
            text.replace(
                "Status: Sample Goal is active under standing scheduled authorization.",
                "Status: no active goal.",
                1,
            ),
            encoding="utf-8",
        )

        failures = current_state_failures(root)

        self.assertTrue(any("active-goal status" in failure for failure in failures), failures)

    def test_no_goal_state_rejects_malformed_active_status(self):
        root = self.fixture_root()
        malformed_goal = root / "docs/plans/malformed/GOAL.md"
        malformed_goal.parent.mkdir(parents=True, exist_ok=True)
        malformed_goal.write_text(
            "# Malformed Goal\n\nStatus: active.\n",
            encoding="utf-8",
        )

        failures = current_state_failures(root)

        self.assertTrue(any("zero active goals" in failure for failure in failures), failures)

    def test_active_goal_requires_owner_approved_status(self):
        root, _, goal_path = self.active_state_fixture()
        goal_path.write_text(
            "# Sample Goal\n\nStatus: active; agent-selected, not owner approved.\n",
            encoding="utf-8",
        )

        failures = current_state_failures(root)

        self.assertTrue(any("must record owner approval" in failure for failure in failures), failures)

    def test_active_goal_rejects_invalid_schedule_and_alignment(self):
        root, current_path, _ = self.active_state_fixture()
        text = current_path.read_text(encoding="utf-8")
        text = text.replace(
            "- Scheduled window: daily 18:00-23:00 America/Toronto",
            "- Scheduled window: never",
            1,
        )
        text = text.replace("- Alignment due: no", "- Alignment due: later", 1)
        current_path.write_text(text, encoding="utf-8")

        failures = current_state_failures(root)

        self.assertTrue(any("Scheduled window" in failure for failure in failures), failures)
        self.assertTrue(any("Alignment due" in failure for failure in failures), failures)

    def test_active_goal_rejects_implementation_without_a_current_run(self):
        root, current_path, state_path = self.active_state_fixture()
        current_text = current_path.read_text(encoding="utf-8").replace(
            "- Run status: awaiting scheduled fresh task",
            "- Run status: implementation",
            1,
        )
        current_path.write_text(current_text, encoding="utf-8")
        state_file = state_path.parent / "IMPLEMENTATION_PLAN.md"
        state_file.write_text(
            state_file.read_text(encoding="utf-8").replace(
                "- Run status: awaiting scheduled fresh task",
                "- Run status: implementation",
                1,
            ),
            encoding="utf-8",
        )

        failures = current_state_failures(root)

        self.assertTrue(any("Run status is invalid" in failure for failure in failures), failures)

    def test_pending_decision_requires_matching_run_status(self):
        root, current_path, state_path = self.active_state_fixture()
        current_text = current_path.read_text(encoding="utf-8").replace(
            "- Pending owner decision: none",
            "- Pending owner decision: choose a boundary",
            1,
        )
        current_path.write_text(current_text, encoding="utf-8")
        state_file = state_path.parent / "IMPLEMENTATION_PLAN.md"
        state_file.write_text(
            state_file.read_text(encoding="utf-8").replace(
                "- Pending owner decision: none",
                "- Pending owner decision: choose a boundary",
                1,
            ),
            encoding="utf-8",
        )

        failures = current_state_failures(root)

        self.assertTrue(
            any("pending owner decision requires" in failure for failure in failures),
            failures,
        )

    def test_duplicate_current_run_state_snapshot_is_rejected(self):
        root = self.fixture_root()
        current_path = root / "docs/plans/CURRENT.md"
        current_path.write_text(
            current_path.read_text(encoding="utf-8")
            + "\n## Run State Snapshot\n\n- Active goal id: hidden\n",
            encoding="utf-8",
        )

        failures = current_state_failures(root)

        self.assertTrue(any("exactly one Run State Snapshot" in failure for failure in failures), failures)

    def test_duplicate_active_implementation_snapshot_is_rejected(self):
        root, _, goal_path = self.active_state_fixture()
        state_path = goal_path.parent / "IMPLEMENTATION_PLAN.md"
        state_path.write_text(
            state_path.read_text(encoding="utf-8")
            + "\n## Run State Snapshot\n\n- Active goal id: hidden\n",
            encoding="utf-8",
        )

        failures = current_state_failures(root)

        self.assertTrue(any("exactly one Run State Snapshot" in failure for failure in failures), failures)

    def test_alignment_due_routes_only_to_alignment(self):
        root, current_path, goal_path = self.active_state_fixture()
        current_path.write_text(
            current_path.read_text(encoding="utf-8").replace(
                "- Alignment due: no",
                "- Alignment due: yes",
                1,
            ),
            encoding="utf-8",
        )
        state_path = goal_path.parent / "IMPLEMENTATION_PLAN.md"
        state_path.write_text(
            state_path.read_text(encoding="utf-8").replace(
                "- Alignment due: no",
                "- Alignment due: yes",
                1,
            ),
            encoding="utf-8",
        )

        self.assertEqual(current_state_failures(root), [])

        current_path.write_text(
            current_path.read_text(encoding="utf-8").replace(
                "- Run status: awaiting scheduled fresh task",
                "- Run status: selecting",
                1,
            ),
            encoding="utf-8",
        )
        state_path.write_text(
            state_path.read_text(encoding="utf-8").replace(
                "- Run status: awaiting scheduled fresh task",
                "- Run status: selecting",
                1,
            ),
            encoding="utf-8",
        )

        failures = current_state_failures(root)

        self.assertTrue(any("route only to alignment" in failure for failure in failures), failures)


if __name__ == "__main__":
    unittest.main()
