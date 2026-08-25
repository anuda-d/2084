import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from scripts.autonomous_loop_lock import main


class AutonomousLoopLockTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.lock_path = Path(self.tempdir.name) / "loop-owner.json"

    def tearDown(self):
        self.tempdir.cleanup()

    def run_lock(self, *args):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--path", str(self.lock_path), *args])
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_acquire_status_and_release(self):
        exit_code, output, error = self.run_lock("acquire", "--task-id", "task-a")
        self.assertEqual((exit_code, error), (0, ""))
        self.assertIn("ACQUIRED task-a", output)

        exit_code, output, error = self.run_lock("assert-owner", "--task-id", "task-a")
        self.assertEqual((exit_code, error), (0, ""))
        self.assertIn("OWNERSHIP_CONFIRMED task-a", output)

        exit_code, output, error = self.run_lock("status")
        self.assertEqual((exit_code, error), (0, ""))
        self.assertIn("HELD task-a", output)

        exit_code, output, error = self.run_lock("release", "--task-id", "task-a")
        self.assertEqual((exit_code, error), (0, ""))
        self.assertIn("RELEASED task-a", output)

        exit_code, output, error = self.run_lock("status")
        self.assertEqual((exit_code, error), (0, ""))
        self.assertEqual(output, "UNLOCKED\n")

    def test_second_task_cannot_overwrite_active_owner(self):
        self.run_lock("acquire", "--task-id", "task-a")

        exit_code, output, error = self.run_lock("acquire", "--task-id", "task-b")
        self.assertEqual(exit_code, 1)
        self.assertEqual(output, "")
        self.assertIn("HELD_BY task-a", error)

        exit_code, output, error = self.run_lock("status")
        self.assertEqual((exit_code, error), (0, ""))
        self.assertIn("HELD task-a", output)

    def test_recovery_requires_the_recorded_owner_and_explicit_verification(self):
        self.run_lock("acquire", "--task-id", "task-a")

        exit_code, output, error = self.run_lock(
            "takeover", "--task-id", "task-b", "--expected-task-id", "wrong-task"
        )
        self.assertEqual(exit_code, 1)
        self.assertEqual(output, "")
        self.assertIn("EXPECTED_OWNER_MISMATCH task-a", error)

        exit_code, output, error = self.run_lock(
            "takeover", "--task-id", "task-b", "--expected-task-id", "task-a"
        )
        self.assertEqual(exit_code, 2)
        self.assertEqual(output, "")
        self.assertIn("--verified-inactive", error)

        exit_code, output, error = self.run_lock(
            "takeover",
            "--task-id",
            "task-b",
            "--expected-task-id",
            "task-a",
            "--verified-inactive",
        )
        self.assertEqual((exit_code, error), (0, ""))
        self.assertIn("TAKEN_OVER task-a task-b", output)

        exit_code, output, error = self.run_lock("status")
        self.assertEqual((exit_code, error), (0, ""))
        self.assertIn("HELD task-b", output)

        exit_code, output, error = self.run_lock("assert-owner", "--task-id", "task-a")
        self.assertEqual(exit_code, 1)
        self.assertEqual(output, "")
        self.assertIn("OWNER_MISMATCH task-b", error)

        exit_code, output, error = self.run_lock("assert-owner", "--task-id", "task-b")
        self.assertEqual((exit_code, error), (0, ""))
        self.assertIn("OWNERSHIP_CONFIRMED task-b", output)

    def test_only_current_owner_can_release(self):
        self.run_lock("acquire", "--task-id", "task-a")

        exit_code, output, error = self.run_lock("release", "--task-id", "task-b")
        self.assertEqual(exit_code, 1)
        self.assertEqual(output, "")
        self.assertIn("OWNER_MISMATCH task-a", error)

        exit_code, output, error = self.run_lock("status")
        self.assertEqual((exit_code, error), (0, ""))
        self.assertIn("HELD task-a", output)


if __name__ == "__main__":
    unittest.main()
