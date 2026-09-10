import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE_SCRIPT = ROOT / "scripts/autonomous_loop_state.py"
LOCK_SCRIPT = ROOT / "scripts/autonomous_loop_lock.py"


class AutonomousLoopStateTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        directory = Path(self.tempdir.name)
        self.state_path = directory / "state.json"
        self.lock_path = directory / "owner.json"
        self.contract_path = directory / "contract.json"
        self.evidence_path = directory / "evidence.json"
        self.accept_path = directory / "accept.json"
        self.reject_path = directory / "reject.json"
        self.report_path = directory / "alignment.json"
        self.write_json(
            self.state_path,
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
                "stop_reason": "test",
                "writer_history": [],
            },
        )
        self.write_json(
            self.contract_path,
            {
                "criterion": "criterion-1",
                "intended_result": "observable result",
                "evidence_claim": "the result is observed",
                "scope": ["simulation/example.py", "tests/test_example.py"],
                "gates": [
                    {"check": "python3 -m unittest tests.test_example", "expect": "passes"}
                ],
                "validation": ["./scripts/check.sh"],
            },
        )
        self.write_json(
            self.evidence_path,
            {
                "focused": "1 focused test passed",
                "full": "full check passed",
                "contract_gates": "all frozen gates observed",
            },
        )
        self.write_json(self.accept_path, {"verdict": "accept", "findings": []})
        self.write_json(
            self.reject_path,
            {"verdict": "reject", "findings": ["blocking defect"]},
        )
        self.write_json(
            self.report_path,
            {
                "goal_status": "incomplete",
                "accepted_slices": 3,
                "remaining_gaps": ["next observed gap"],
                "risks": [],
                "recommended_next_slice": "not selected; evidence-only suggestion",
            },
        )

    def tearDown(self):
        self.tempdir.cleanup()

    @staticmethod
    def write_json(path, value):
        path.write_text(json.dumps(value) + "\n", encoding="utf-8")

    def run_lock(self, *arguments):
        return subprocess.run(
            [sys.executable, str(LOCK_SCRIPT), "--path", str(self.lock_path), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )

    def run_state(self, *arguments):
        return subprocess.run(
            [
                sys.executable,
                str(STATE_SCRIPT),
                "--state-path",
                str(self.state_path),
                "--lock-path",
                str(self.lock_path),
                *arguments,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def mutate(self, command, actor, revision, event, *arguments):
        return self.run_state(
            command,
            "--task-id",
            actor,
            "--expected-revision",
            str(revision),
            "--event-id",
            event,
            *arguments,
        )

    def acquire_orchestrator(self, actor="orch-1"):
        result = self.run_lock(
            "acquire",
            "--task-id",
            actor,
            "--role",
            "orchestrator",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def activate_and_start(self):
        self.acquire_orchestrator()
        result = self.mutate(
            "activate",
            "orch-1",
            0,
            "activate-1",
            "--goal-id",
            "goal-1",
            "--confirm-owner-approved",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.mutate(
            "start-generation",
            "orch-1",
            1,
            "generation-1",
            "--generation-id",
            "gen-1",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def contract_and_transfer(self, number):
        revision = json.loads(self.state_path.read_text())["revision"]
        result = self.mutate(
            "contract-slice",
            "orch-1",
            revision,
            f"contract-{number}",
            "--slice-id",
            f"slice-{number}",
            "--writer-task-id",
            f"writer-{number}",
            "--contract",
            str(self.contract_path),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        transfer = self.run_lock(
            "transfer",
            "--task-id",
            "orch-1",
            "--to-task-id",
            f"writer-{number}",
            "--to-role",
            "writer",
            "--generation-id",
            "gen-1",
            "--slice-id",
            f"slice-{number}",
        )
        self.assertEqual(transfer.returncode, 0, transfer.stderr)

    def accept_slice(self, number):
        writer = f"writer-{number}"
        revision = json.loads(self.state_path.read_text())["revision"]
        result = self.mutate(
            "begin-implementation",
            writer,
            revision,
            f"implement-{number}",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.mutate(
            "begin-validation",
            writer,
            revision + 1,
            f"validate-{number}",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.mutate(
            "begin-review",
            writer,
            revision + 2,
            f"review-start-{number}",
            "--evidence",
            str(self.evidence_path),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.mutate(
            "record-review",
            writer,
            revision + 3,
            f"review-accept-{number}",
            "--review",
            str(self.accept_path),
            "--reviewer-task-id",
            f"reviewer-{number}",
            "--accepted-commit",
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip(),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        transfer = self.run_lock(
            "transfer",
            "--task-id",
            writer,
            "--to-task-id",
            "orch-1",
            "--to-role",
            "orchestrator",
            "--generation-id",
            "gen-1",
        )
        self.assertEqual(transfer.returncode, 0, transfer.stderr)

    def test_repository_state_starts_stopped_and_unauthorized(self):
        result = subprocess.run(
            [
                sys.executable,
                str(STATE_SCRIPT),
                "--state-path",
                str(ROOT / "docs/plans/AUTONOMOUS_LOOP_STATE.json"),
                "validate",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "STATE_VALID stopped 0\n")

    def test_activation_requires_explicit_confirmation_and_checkout_owner(self):
        no_owner = self.mutate(
            "activate",
            "orch-1",
            0,
            "activation-no-owner",
            "--goal-id",
            "goal-1",
            "--confirm-owner-approved",
        )
        self.assertEqual(no_owner.returncode, 2)
        self.assertIn("NO_CHECKOUT_OWNER", no_owner.stderr)

        self.acquire_orchestrator()
        unconfirmed = self.mutate(
            "activate",
            "orch-1",
            0,
            "activation-unconfirmed",
            "--goal-id",
            "goal-1",
        )
        self.assertEqual(unconfirmed.returncode, 2)
        self.assertIn("OWNER_APPROVAL_CONFIRMATION_REQUIRED", unconfirmed.stderr)

    def test_three_accepted_slices_force_alignment_and_fresh_generation(self):
        self.activate_and_start()
        for number in range(1, 4):
            self.contract_and_transfer(number)
            self.accept_slice(number)

        state = json.loads(self.state_path.read_text())
        self.assertEqual(state["phase"], "alignment_required")
        self.assertEqual(state["orchestrator"]["accepted_slices"], 3)

        result = self.mutate(
            "begin-alignment",
            "orch-1",
            state["revision"],
            "alignment-start",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.mutate(
            "complete-alignment",
            "orch-1",
            state["revision"] + 1,
            "alignment-complete",
            "--report",
            str(self.report_path),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads(self.state_path.read_text())
        self.assertEqual(state["phase"], "handoff_ready")
        self.assertIsNone(state["orchestrator"])

        transfer = self.run_lock(
            "transfer",
            "--task-id",
            "orch-1",
            "--to-task-id",
            "orch-2",
            "--to-role",
            "orchestrator",
            "--generation-id",
            "gen-2",
        )
        self.assertEqual(transfer.returncode, 1)
        self.assertIn("GENERATION_MISMATCH", transfer.stderr)
        self.assertEqual(self.run_lock("release", "--task-id", "orch-1").returncode, 0)
        self.assertEqual(
            self.run_lock(
                "acquire",
                "--task-id",
                "orch-2",
                "--role",
                "orchestrator",
                "--generation-id",
                "gen-2",
            ).returncode,
            0,
        )
        result = self.mutate(
            "start-generation",
            "orch-2",
            state["revision"],
            "generation-2",
            "--generation-id",
            "gen-2",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads(self.state_path.read_text())
        self.assertEqual(state["orchestrator"]["accepted_slices"], 0)
        self.assertEqual(state["orchestrator"]["task_id"], "orch-2")

    def test_contract_is_frozen_and_reviewer_must_be_fresh(self):
        self.activate_and_start()
        self.contract_and_transfer(1)
        state = json.loads(self.state_path.read_text())
        state["slice"]["contract"]["criterion"] = "weakened"
        self.write_json(self.state_path, state)

        result = self.run_state("validate")
        self.assertEqual(result.returncode, 2)
        self.assertIn("CONTRACT_DIGEST_MISMATCH", result.stderr)

    def test_writer_or_orchestrator_cannot_self_review(self):
        self.activate_and_start()
        self.contract_and_transfer(1)
        revision = json.loads(self.state_path.read_text())["revision"]
        for command, event, extra in (
            ("begin-implementation", "impl", ()),
            ("begin-validation", "validation", ()),
            ("begin-review", "review-start", ("--evidence", str(self.evidence_path))),
        ):
            result = self.mutate(command, "writer-1", revision, event, *extra)
            self.assertEqual(result.returncode, 0, result.stderr)
            revision += 1

        for reviewer in ("writer-1", "orch-1"):
            result = self.mutate(
                "record-review",
                "writer-1",
                revision,
                f"self-review-{reviewer}",
                "--review",
                str(self.accept_path),
                "--reviewer-task-id",
                reviewer,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("REVIEWER_MUST_BE_FRESH_READ_ONLY_TASK", result.stderr)

        wrong_commit = self.mutate(
            "record-review",
            "writer-1",
            revision,
            "wrong-accepted-commit",
            "--review",
            str(self.accept_path),
            "--reviewer-task-id",
            "reviewer-1",
            "--accepted-commit",
            "0" * 40,
        )
        self.assertEqual(wrong_commit.returncode, 2)
        self.assertIn("ACCEPTED_COMMIT_IS_NOT_CURRENT_HEAD", wrong_commit.stderr)

    def test_revision_and_event_id_make_retries_safe(self):
        self.acquire_orchestrator()
        arguments = (
            "activate",
            "orch-1",
            0,
            "same-event",
            "--goal-id",
            "goal-1",
            "--confirm-owner-approved",
        )
        first = self.mutate(*arguments)
        self.assertEqual(first.returncode, 0, first.stderr)
        duplicate = self.mutate(*arguments)
        self.assertEqual(duplicate.returncode, 0, duplicate.stderr)
        self.assertIn("ALREADY_APPLIED same-event 1", duplicate.stdout)

        stale = self.mutate(
            "start-generation",
            "orch-1",
            0,
            "new-event",
            "--generation-id",
            "gen-1",
        )
        self.assertEqual(stale.returncode, 2)
        self.assertIn("REVISION_MISMATCH 1", stale.stderr)

    def test_writer_task_identity_cannot_be_reused(self):
        self.activate_and_start()
        self.contract_and_transfer(1)
        self.accept_slice(1)
        revision = json.loads(self.state_path.read_text())["revision"]

        result = self.mutate(
            "contract-slice",
            "orch-1",
            revision,
            "contract-reused-writer",
            "--slice-id",
            "slice-2",
            "--writer-task-id",
            "writer-1",
            "--contract",
            str(self.contract_path),
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("WRITER_TASK_ALREADY_USED", result.stderr)

    def test_rejections_are_bounded_and_incomplete_slice_is_not_counted(self):
        self.activate_and_start()
        self.contract_and_transfer(1)
        writer = "writer-1"
        revision = json.loads(self.state_path.read_text())["revision"]
        self.assertEqual(
            self.mutate("begin-implementation", writer, revision, "impl").returncode,
            0,
        )
        revision += 1
        for attempt in range(1, 4):
            result = self.mutate(
                "begin-validation",
                writer,
                revision,
                f"validate-{attempt}",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            revision += 1
            result = self.mutate(
                "begin-review",
                writer,
                revision,
                f"review-start-{attempt}",
                "--evidence",
                str(self.evidence_path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            revision += 1
            result = self.mutate(
                "record-review",
                writer,
                revision,
                f"reject-{attempt}",
                "--review",
                str(self.reject_path),
                "--reviewer-task-id",
                f"reviewer-{attempt}",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            revision += 1
            if attempt < 3:
                self.assertEqual(json.loads(self.state_path.read_text())["phase"], "repairing")

        state = json.loads(self.state_path.read_text())
        self.assertEqual(state["phase"], "blocked")
        self.assertEqual(state["orchestrator"]["accepted_slices"], 0)
        self.assertEqual(state["slice"]["slice_id"], "slice-1")
        self.assertEqual(state["slice"]["repair_count"], 2)

    def test_recovery_rebinds_only_the_exact_verified_actor(self):
        self.activate_and_start()
        token = json.loads(self.lock_path.read_text())["claim_token"]
        recovered = self.run_lock(
            "recover",
            "--task-id",
            "orch-recovery",
            "--expected-task-id",
            "orch-1",
            "--expected-claim-token",
            token,
            "--verified-terminal-state",
            "failed",
        )
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        revision = json.loads(self.state_path.read_text())["revision"]
        result = self.mutate(
            "recover-actor",
            "orch-recovery",
            revision,
            "recover-orchestrator",
            "--expected-task-id",
            "orch-1",
            "--terminal-state",
            "failed",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads(self.state_path.read_text())
        self.assertEqual(state["orchestrator"]["task_id"], "orch-recovery")
        self.assertEqual(state["orchestrator"]["recovery_count"], 1)


if __name__ == "__main__":
    unittest.main()
