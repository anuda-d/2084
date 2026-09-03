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
        self.assertRegex(result.stdout, r"^ACQUIRED task-a\n$")
        record = json.loads(self.lock_path.read_text(encoding="utf-8"))
        self.assertEqual(record["task_id"], "task-a")
        self.assertIsInstance(record["claimed_at"], int)
        self.assertRegex(record["claim_token"], r"^[0-9a-f]{32}$")

    def test_current_codex_task_id_supplies_ownership(self):
        environment = os.environ.copy()
        environment["CODEX_THREAD_ID"] = "task-from-environment"

        result = self.run_lock("acquire", env=environment)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"^ACQUIRED task-from-environment\n$")

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
            all(
                result[0] == ""
                and result[1].startswith("HELD_BY task-")
                for result in conflicts
            )
        )

    def test_second_task_cannot_replace_the_owner(self):
        self.assertEqual(
            self.run_lock("acquire", "--task-id", "task-a").returncode,
            0,
        )

        result = self.run_lock("acquire", "--task-id", "task-b")

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertRegex(result.stderr, r"^HELD_BY task-a [0-9a-f]{32}\n$")
        owner = self.run_lock("assert-owner", "--task-id", "task-a")
        self.assertEqual(owner.returncode, 0, owner.stderr)

    def test_matching_terminal_owner_can_be_recovered_atomically(self):
        self.assertEqual(
            self.run_lock("acquire", "--task-id", "task-a").returncode,
            0,
        )

        result = self.run_lock(
            "recover",
            "--task-id",
            "task-b",
            "--expected-task-id",
            "task-a",
            "--expected-claim-token",
            json.loads(self.lock_path.read_text(encoding="utf-8"))["claim_token"],
            "--verified-terminal-state",
            "failed",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "RECOVERED task-a task-b failed\n")
        owner = self.run_lock("assert-owner", "--task-id", "task-b")
        self.assertEqual(owner.returncode, 0, owner.stderr)
        record = json.loads(self.lock_path.read_text(encoding="utf-8"))
        self.assertEqual(record["recovered_from"], "task-a")
        self.assertEqual(record["verified_terminal_state"], "failed")

    def test_recovery_fails_when_the_recorded_owner_changed(self):
        self.assertEqual(
            self.run_lock("acquire", "--task-id", "task-c").returncode,
            0,
        )

        result = self.run_lock(
            "recover",
            "--task-id",
            "task-b",
            "--expected-task-id",
            "task-a",
            "--expected-claim-token",
            "wrong-token",
            "--verified-terminal-state",
            "completed",
        )

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, "EXPECTED_OWNER_MISMATCH task-c\n")
        owner = self.run_lock("assert-owner", "--task-id", "task-c")
        self.assertEqual(owner.returncode, 0, owner.stderr)

    def test_resumed_owner_assertion_invalidates_an_old_recovery_observation(self):
        self.assertEqual(
            self.run_lock("acquire", "--task-id", "task-a").returncode,
            0,
        )
        observed_token = json.loads(self.lock_path.read_text(encoding="utf-8"))["claim_token"]
        resumed = self.run_lock("assert-owner", "--task-id", "task-a")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)

        result = self.run_lock(
            "recover",
            "--task-id",
            "task-b",
            "--expected-task-id",
            "task-a",
            "--expected-claim-token",
            observed_token,
            "--verified-terminal-state",
            "failed",
        )

        self.assertEqual(result.returncode, 1)
        self.assertRegex(
            result.stderr,
            r"^EXPECTED_CLAIM_TOKEN_MISMATCH [0-9a-f]{32}\n$",
        )
        owner = self.run_lock("assert-owner", "--task-id", "task-a")
        self.assertEqual(owner.returncode, 0, owner.stderr)

    def test_legacy_owner_record_can_be_recovered_with_derived_claim_token(self):
        self.lock_path.write_text(
            json.dumps({"task_id": "task-a", "claimed_at": 123}),
            encoding="utf-8",
        )

        result = self.run_lock(
            "recover",
            "--task-id",
            "task-b",
            "--expected-task-id",
            "task-a",
            "--expected-claim-token",
            "legacy:123",
            "--verified-terminal-state",
            "interrupted",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "RECOVERED task-a task-b interrupted\n")
        record = json.loads(self.lock_path.read_text(encoding="utf-8"))
        self.assertRegex(record["claim_token"], r"^[0-9a-f]{32}$")

    def test_recovery_fails_when_no_owner_exists(self):
        result = self.run_lock(
            "recover",
            "--task-id",
            "task-b",
            "--expected-task-id",
            "task-a",
            "--expected-claim-token",
            "any-token",
            "--verified-terminal-state",
            "interrupted",
        )

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, "NO_OWNER\n")

    def test_recovery_rejects_non_terminal_or_unknown_owner_states(self):
        self.assertEqual(
            self.run_lock("acquire", "--task-id", "task-a").returncode,
            0,
        )

        for state in ("active", "waiting-for-input", "unknown"):
            with self.subTest(state=state):
                result = self.run_lock(
                    "recover",
                    "--task-id",
                    "task-b",
                    "--expected-task-id",
                    "task-a",
                    "--expected-claim-token",
                    "any-token",
                    "--verified-terminal-state",
                    state,
                )

                self.assertEqual(result.returncode, 2)
                self.assertIn("invalid choice", result.stderr)
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

        recovery = self.run_lock(
            "recover",
            "--task-id",
            "task-b",
            "--expected-task-id",
            "task-a",
            "--expected-claim-token",
            "any-token",
            "--verified-terminal-state",
            "completed",
        )
        self.assertEqual(recovery.returncode, 2)
        self.assertIn("UNREADABLE_LOCK", recovery.stderr)

        self.lock_path.write_text(
            json.dumps({"task_id": "task-a", "claimed_at": 1, "claim_token": 7}),
            encoding="utf-8",
        )
        malformed_token = self.run_lock("status")
        self.assertEqual(malformed_token.returncode, 2)
        self.assertIn("UNREADABLE_LOCK invalid claim token", malformed_token.stderr)


if __name__ == "__main__":
    unittest.main()
