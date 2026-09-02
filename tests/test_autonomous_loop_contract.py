import tempfile
import unittest
from pathlib import Path

from scripts.check_autonomous_loop_contract import (
    GOAL_REJECTIONS,
    GOAL_REQUIREMENTS,
    ROOT,
    repository_contract_failures,
)


class AutonomousLoopContractTests(unittest.TestCase):
    contract_paths = (
        Path("AGENTS.md"),
        Path("docs/main/DEVELOPMENT_LOOP.md"),
        Path("docs/plans/CURRENT.md"),
    )

    def fixture_root(self):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = Path(tempdir.name)
        for relative_path in self.contract_paths:
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                (ROOT / relative_path).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        return root

    def test_continuous_mode_requires_a_real_app_goal(self):
        failures = repository_contract_failures()

        self.assertEqual(failures, [], "\n".join(failures))

    def test_each_goal_activation_clause_is_load_bearing(self):
        for relative_path in self.contract_paths:
            for token in GOAL_REQUIREMENTS:
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

    def test_contradictory_goal_rules_are_rejected(self):
        for relative_path in self.contract_paths:
            for contradiction in GOAL_REJECTIONS:
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


if __name__ == "__main__":
    unittest.main()
