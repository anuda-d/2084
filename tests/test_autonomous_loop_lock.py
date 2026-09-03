import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCK_SCRIPT = ROOT / "scripts/autonomous_loop_lock.py"


class AutonomousLoopLockTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.lock_path = Path(self.tempdir.name) / "loop-owner.json"

    def tearDown(self):
        self.tempdir.cleanup()

    def run_lock(self, *args, env=None):
        return subprocess.run(
            [sys.executable, str(LOCK_SCRIPT), "--path", str(self.lock_path), *args],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def test_recovery_task_claims_an_idle_checkout_without_task_listing(self):
        result = self.run_lock("acquire", "--task-id", "task-a")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "ACQUIRED task-a\n")
        record = json.loads(self.lock_path.read_text(encoding="utf-8"))
        self.assertEqual(record["task_id"], "task-a")
        self.assertIsInstance(record["claimed_at"], int)

    def test_current_codex_task_id_supplies_ownership(self):
        environment = os.environ.copy()
        environment["CODEX_THREAD_ID"] = "task-from-environment"

        result = self.run_lock("acquire", env=environment)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "ACQUIRED task-from-environment\n")

    def test_missing_task_identity_fails_closed(self):
        environment = os.environ.copy()
        environment.pop("CODEX_THREAD_ID", None)

        result = self.run_lock("acquire", env=environment)

        self.assertEqual(result.returncode, 2)
        self.assertIn("MISSING_TASK_ID", result.stderr)

    def test_simultaneous_starts_produce_exactly_one_owner(self):
        processes = [
            subprocess.Popen(
                [
                    sys.executable,
                    str(LOCK_SCRIPT),
                    "--path",
                    str(self.lock_path),
                    "acquire",
                    "--task-id",
                    f"task-{index}",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for index in range(12)
        ]
        results = [(*process.communicate(), process.returncode) for process in processes]

        winners = [result for result in results if result[2] == 0]
        conflicts = [result for result in results if result[2] == 1]
        self.assertEqual(len(winners), 1)
        self.assertEqual(len(conflicts), 11)
        self.assertRegex(winners[0][0], r"^ACQUIRED task-\d+\n$")
        self.assertTrue(
            all(result[0] == "" and result[1].startswith("HELD_BY task-") for result in conflicts)
        )

    def test_second_task_cannot_replace_the_owner(self):
        self.assertEqual(
            self.run_lock("acquire", "--task-id", "task-a").returncode,
            0,
        )

        result = self.run_lock("acquire", "--task-id", "task-b")

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "HELD_BY task-a\n")
        owner = self.run_lock("assert-owner", "--task-id", "task-a")
        self.assertEqual(owner.returncode, 0, owner.stderr)

    def test_takeover_command_does_not_exist(self):
        self.assertEqual(
            self.run_lock("acquire", "--task-id", "task-a").returncode,
            0,
        )

        result = self.run_lock(
            "takeover",
            "--task-id",
            "task-b",
            "--expected-task-id",
            "task-a",
            "--verified-inactive",
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid choice: 'takeover'", result.stderr)
        owner = self.run_lock("assert-owner", "--task-id", "task-a")
        self.assertEqual(owner.returncode, 0, owner.stderr)

    def test_only_the_recorded_owner_can_release(self):
        self.assertEqual(
            self.run_lock("acquire", "--task-id", "task-a").returncode,
            0,
        )

        wrong_owner = self.run_lock("release", "--task-id", "task-b")
        self.assertEqual(wrong_owner.returncode, 1)
        self.assertEqual(wrong_owner.stderr, "OWNER_MISMATCH task-a\n")

        release = self.run_lock("release", "--task-id", "task-a")
        self.assertEqual(release.returncode, 0, release.stderr)
        self.assertEqual(release.stdout, "RELEASED task-a\n")
        self.assertEqual(self.run_lock("status").stdout, "UNLOCKED\n")

    def test_unreadable_record_fails_closed(self):
        self.lock_path.write_text("not-json\n", encoding="utf-8")

        result = self.run_lock("acquire", "--task-id", "task-a")

        self.assertEqual(result.returncode, 2)
        self.assertIn("UNREADABLE_LOCK", result.stderr)


if __name__ == "__main__":
    unittest.main()
