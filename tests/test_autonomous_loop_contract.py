import re
import tempfile
import unittest
from pathlib import Path

from scripts.check_autonomous_loop_contract import (
    ROOT,
    active_implementation_state_failures,
    active_implementation_state_path,
    repository_contract_failures,
)


class AutonomousLoopContractTests(unittest.TestCase):
    contract_paths = (
        Path("AGENTS.md"),
        Path("docs/main/DEVELOPMENT_LOOP.md"),
        Path("docs/plans/CURRENT.md"),
    )
    required_goal_clauses = (
        "app-level Goal",
        "`create_goal`",
        "`get_goal` again",
        "`get_goal` reports `status: active`",
        "before task listing or lock acquisition",
        "Never claim Continuous Goal mode",
        "Continuous Goal does not use `create_thread`",
        "releasing a lock it owns",
        "**GOAL MODE NOT ACTIVE**",
        "`update_goal` with `status: complete`",
        "same task continues automatically across turns",
        "must not direct continuation to a new agent, task, chat, or handoff",
        "must not release the repository lock between work units",
        "`clear` the conflicting Goal",
    )
    continuous_section_end = {
        Path("AGENTS.md"): "- Every scheduled task and manual one-shot",
        Path("docs/main/DEVELOPMENT_LOOP.md"):
            "### Scheduled relay or manual one-shot",
        Path("docs/plans/CURRENT.md"):
            "- Confirm the no-overlap gate before repository work.",
    }
    scheduled_section_start = {
        Path("AGENTS.md"): "- A scheduled relay task may create its successor",
        Path("docs/main/DEVELOPMENT_LOOP.md"):
            "### Scheduled relay or manual one-shot",
        Path("docs/plans/CURRENT.md"):
            "- In the current scheduled relay window",
    }

    def active_state_relative_path(self):
        path = active_implementation_state_path()
        self.assertIsNotNone(path)
        assert path is not None
        return path.relative_to(ROOT)

    def fixture_root(self):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = Path(tempdir.name)
        paths = self.contract_paths + (self.active_state_relative_path(),)
        for relative_path in paths:
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                (ROOT / relative_path).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        return root

    def insert_continuous_rule(self, root, relative_path, rule):
        path = root / relative_path
        end_marker = self.continuous_section_end[relative_path]
        text = path.read_text(encoding="utf-8")
        self.assertIn(end_marker, text)
        path.write_text(
            text.replace(end_marker, f"{rule}\n{end_marker}", 1),
            encoding="utf-8",
        )
        return path

    def test_continuous_mode_requires_a_real_app_goal(self):
        failures = repository_contract_failures()

        self.assertEqual(failures, [], "\n".join(failures))

    def test_current_active_state_contains_only_product_progress(self):
        failures = active_implementation_state_failures()

        self.assertEqual(failures, [], "\n".join(failures))

    def test_each_goal_activation_clause_is_load_bearing(self):
        for relative_path in self.contract_paths:
            for token in self.required_goal_clauses:
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

    def test_continuous_mode_rejects_transfer_paraphrases(self):
        contradictions = (
            "A new agent will continue in a new chat.",
            "A fresh task takes over after every committed work unit.",
            "Continue work in another chat after each checkpoint.",
            "Handoff to a successor agent after this work unit.",
            "Release the repository lock after every work unit.",
        )
        for relative_path in self.contract_paths:
            for contradiction in contradictions:
                with self.subTest(path=relative_path, contradiction=contradiction):
                    root = self.fixture_root()
                    path = self.insert_continuous_rule(
                        root,
                        relative_path,
                        contradiction,
                    )

                    failures = repository_contract_failures(root)

                    self.assertTrue(
                        any(
                            str(path) in failure and "transfer rule" in failure
                            for failure in failures
                        ),
                        failures,
                    )

    def test_obsolete_goal_rules_are_rejected(self):
        contradictions = (
            "Continuous Goal may use `create_thread`",
            "`status: paused` is sufficient",
            "an unfinished Goal is sufficient",
            "fewer than 50",
        )
        for relative_path in self.contract_paths:
            for contradiction in contradictions:
                with self.subTest(path=relative_path, contradiction=contradiction):
                    root = self.fixture_root()
                    path = root / relative_path
                    path.write_text(
                        path.read_text(encoding="utf-8") + f"\n{contradiction}\n",
                        encoding="utf-8",
                    )

                    failures = repository_contract_failures(root)

                    self.assertTrue(
                        any(
                            str(path) in failure and contradiction in failure
                            for failure in failures
                        ),
                        failures,
                    )

    def test_scheduled_relay_allows_transfer_language(self):
        transfer_rules = (
            "A new agent will continue in a new chat.",
            "A fresh task takes over after every committed work unit.",
            "Continue work in another chat after each checkpoint.",
            "Handoff to a successor agent after this work unit.",
            "Release the repository lock after every work unit.",
        )
        for relative_path in self.contract_paths:
            for rule in transfer_rules:
                with self.subTest(path=relative_path, rule=rule):
                    root = self.fixture_root()
                    path = root / relative_path
                    marker = self.scheduled_section_start[relative_path]
                    text = path.read_text(encoding="utf-8")
                    self.assertIn(marker, text)
                    if relative_path == Path("docs/main/DEVELOPMENT_LOOP.md"):
                        replacement = f"{marker}\n{rule}"
                    else:
                        replacement = f"{rule}\n{marker}"
                    path.write_text(
                        text.replace(marker, replacement, 1),
                        encoding="utf-8",
                    )

                    failures = repository_contract_failures(root)

                    self.assertEqual(failures, [], "\n".join(failures))

    def test_active_state_rejects_unrecognized_run_state_fields(self):
        invalid_fields = (
            "Automation state",
            "Execution mode",
            "Handoff owner",
            "Next task",
        )
        for field in invalid_fields:
            with self.subTest(field=field):
                root = self.fixture_root()
                path = root / self.active_state_relative_path()
                text = path.read_text(encoding="utf-8")
                path.write_text(
                    text.replace(
                        "## Goal Progress",
                        f"- {field}: handoff prepared for a new chat\n\n"
                        "## Goal Progress",
                        1,
                    ),
                    encoding="utf-8",
                )

                failures = active_implementation_state_failures(root)

                self.assertTrue(any(field in failure for failure in failures), failures)

    def test_active_state_rejects_unstructured_run_state_entry(self):
        root = self.fixture_root()
        path = root / self.active_state_relative_path()
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.replace(
                "## Goal Progress",
                "- Handoff prepared for a new chat\n\n## Goal Progress",
                1,
            ),
            encoding="utf-8",
        )

        failures = active_implementation_state_failures(root)

        self.assertTrue(
            any("Handoff prepared" in failure for failure in failures),
            failures,
        )

    def test_active_state_requires_each_product_progress_field_once(self):
        root = self.fixture_root()
        path = root / self.active_state_relative_path()
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"(?m)^- Alignment due:.*\n", "", text, count=1)
        path.write_text(text, encoding="utf-8")

        failures = active_implementation_state_failures(root)

        self.assertTrue(any("Alignment due" in failure for failure in failures), failures)

    def test_active_state_ignores_product_prose_outside_run_state(self):
        root = self.fixture_root()
        path = root / self.active_state_relative_path()
        path.write_text(
            path.read_text(encoding="utf-8")
            + "\nProduct note: Task state is observable evidence.\n",
            encoding="utf-8",
        )

        failures = active_implementation_state_failures(root)

        self.assertEqual(failures, [], "\n".join(failures))

    def test_active_state_link_must_exist_once(self):
        root = self.fixture_root()
        current_path = root / "docs/plans/CURRENT.md"
        text = current_path.read_text(encoding="utf-8")
        link_pattern = re.compile(
            r"(?m)^- Shared implementation state:[ \t]*\n"
            r"[ \t]*\[[^]]+\]\([^)\n]+\)\n"
        )
        match = link_pattern.search(text)
        self.assertIsNotNone(match)
        assert match is not None
        link_block = match.group(0)

        current_path.write_text(text.replace(link_block, "", 1), encoding="utf-8")
        missing_failures = active_implementation_state_failures(root)
        self.assertTrue(
            any("expected exactly one" in failure for failure in missing_failures),
            missing_failures,
        )

        current_path.write_text(text + "\n" + link_block, encoding="utf-8")
        duplicate_failures = active_implementation_state_failures(root)
        self.assertTrue(
            any("expected exactly one" in failure for failure in duplicate_failures),
            duplicate_failures,
        )

    def test_active_state_link_accepts_single_line_format(self):
        root = self.fixture_root()
        current_path = root / "docs/plans/CURRENT.md"
        text = current_path.read_text(encoding="utf-8")
        text = re.sub(
            r"(?m)^- Shared implementation state:[ \t]*\n[ \t]*(\[[^]]+\]\([^)\n]+\))",
            r"- Shared implementation state: \1",
            text,
            count=1,
        )
        current_path.write_text(text, encoding="utf-8")

        failures = active_implementation_state_failures(root)

        self.assertEqual(failures, [], "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
