"""Completion receipts are exercised through the real Git runner boundary."""

import contextlib
import io
import json
from datetime import timedelta
from unittest import TestCase
from unittest.mock import patch

from devloop.runner import Runner, Paused
from tests import test_development_runner as fixtures


def result(outcome="goal_complete", scope="goal"):
    return dict(outcome=outcome, review_scope=scope, summary="Goal behavior implemented",
                evidence="Fixture behavior verified", remaining="", commit_message="Complete goal",
                review_required=False, review_reason="", artifacts=[])


def review(verdict="pass", criteria=True, completion_only=False):
    return dict(verdict=verdict, findings="Correct completion wording" if verdict == "repair" else "",
                goal_criteria_verified=criteria, completion_only=completion_only)


class CompletionTests(TestCase):
    def setUp(self):
        self.fixture = fixtures.RunnerTests("test_continues_multiple_changes_without_timer_or_new_worker")
        self.fixture.setUp()
        self.runner = self.fixture.runner
        self.calls = []

    def tearDown(self):
        self.fixture.tearDown()

    def step(self, runner=None):
        with contextlib.redirect_stdout(io.StringIO()):
            return (runner or self.runner).step()

    def agent(self, worker, reviewer=None):
        def call(prompt, *, review=False):
            self.calls.append((review, prompt))
            return reviewer(prompt) if review and reviewer else globals()["review"]() if review else worker()
        self.runner.agent = call

    def test_final_change_completes_with_one_worker_and_one_review(self):
        def worker():
            (self.fixture.root / "app.py").write_text("value = 1\n")
            return result()
        self.agent(worker)
        self.assertEqual(self.step(), "complete")
        self.assertEqual([r for r, _ in self.calls], [False, True])
        self.assertEqual(self.fixture.git("rev-list", "--count", f"{self.fixture.initial}..HEAD"), "1")
        self.assertFalse(self.runner.dirty())

    def test_goal_review_survives_identical_tree_commit_and_completion_handoff(self):
        def worker():
            if self.runner.head() == self.fixture.initial:
                (self.fixture.root / "app.py").write_text("value = 1\n")
                return result("change_ready")
            return result()
        self.agent(worker)
        self.assertEqual(self.step(), "ready")
        self.assertEqual(self.step(), "complete")
        self.assertEqual(sum(r for r, _ in self.calls), 1)
        self.assertEqual(len(list((self.runner.store.directory / "runs").glob("*-checking.jsonl"))), 2)

    def test_restart_before_review_does_not_repeat_passed_checks(self):
        self.agent(lambda: result(), lambda _: (_ for _ in ()).throw(Paused()))
        self.assertEqual(self.step(), "paused")
        before = list((self.runner.store.directory / "runs").glob("*-checking.jsonl"))
        restarted = Runner(self.runner.config, clock=lambda: self.fixture.now)
        restarted.agent = lambda prompt, **kwargs: review()
        self.assertEqual(self.step(restarted), "complete")
        self.assertEqual(len(list((self.runner.store.directory / "runs").glob("*-checking.jsonl"))), len(before))

    def test_restart_after_review_commits_without_another_worker_or_review(self):
        def worker():
            (self.fixture.root / "app.py").write_text("value = 1\n")
            return result()
        self.agent(worker)
        with patch.object(self.runner, "accept_commit", side_effect=Paused()):
            self.assertEqual(self.step(), "paused")
        restarted = Runner(self.runner.config, clock=lambda:self.fixture.now)
        restarted.agent = lambda *args, **kwargs:self.fail("Unnecessary agent call")
        self.assertEqual(self.step(restarted), "complete")
        self.assertEqual([r for r, _ in self.calls], [False, True])
        self.assertEqual(len(list((self.runner.store.directory / "runs").glob("*-checking.jsonl"))), 2)

    def test_completed_check_is_retained_when_next_check_is_interrupted(self):
        self.agent(lambda: result())
        original = self.runner.execute
        count = 0
        def execute(command, name, prompt=None):
            nonlocal count
            if name == "checking":
                count += 1
                if count == 2:
                    raise Paused()
            return original(command, name, prompt)
        self.runner.execute = execute
        self.assertEqual(self.step(), "paused")
        self.runner.execute = original
        self.assertEqual(self.step(), "complete")
        self.assertEqual(len(list((self.runner.store.directory / "runs").glob("*-checking.jsonl"))), 2)

    def test_completion_document_repair_uses_focused_review(self):
        self.runner.config.review["completion_paths"] = ["completion.md"]
        count = 0
        def worker():
            nonlocal count
            count += 1
            (self.fixture.root / "completion.md").write_text("Candidate complete.\n" if count == 1 else "Evidence accepted.\n")
            return result()
        def reviewer(prompt):
            if count == 1:
                return review("repair", completion_only=True)
            self.assertIn("completion_correction", prompt)
            self.assertIn("Correct completion wording", prompt)
            return review(completion_only=True)
        self.agent(worker, reviewer)
        self.assertEqual(self.step(), "ready")
        self.runner.store.update(retry_after=0)
        self.assertEqual(self.step(), "complete")
        self.assertEqual(sum(r for r, _ in self.calls), 2)

    def test_substantive_repair_requires_whole_goal_review(self):
        count = 0
        def worker():
            nonlocal count
            count += 1
            (self.fixture.root / "app.py").write_text(f"value = {count}\n")
            return result()
        def reviewer(prompt):
            self.assertIn("Review scope: goal", prompt)
            return review("repair", completion_only=True) if count == 1 else review()
        self.agent(worker, reviewer)
        self.step()
        self.runner.store.update(retry_after=0)
        self.assertEqual(self.step(), "complete")

    def test_reviewer_can_escalate_allowlisted_semantic_edit(self):
        self.runner.config.review["completion_paths"] = ["completion.md"]
        n = 0
        def worker():
            nonlocal n
            n += 1
            (self.fixture.root / "completion.md").write_text(f"Changed semantics {n}\n")
            return result("change_ready" if n == 1 else "goal_complete")
        scopes = []
        def reviewer(prompt):
            scopes.append("correction" if "Review scope: completion_correction" in prompt else "goal")
            return review(criteria=False) if scopes[-1] == "correction" else review()
        self.agent(worker, reviewer)
        self.step()
        self.assertEqual(self.step(), "complete")
        self.assertEqual(scopes, ["goal", "correction", "goal"])

    def test_wall_deadline_stops_when_monotonic_clock_does_not_advance(self):
        def executor(command, **kwargs):
            self.fixture.now += timedelta(seconds=21)
            self.assertTrue(kwargs["stop"]())
            return -2, True
        self.runner.executor = executor
        with patch("devloop.runner.time.monotonic", return_value=100):
            with self.assertRaisesRegex(ValueError, "turn limit"):
                self.runner.execute(["fixture"], "working")
        state = self.runner.store.read()
        self.assertEqual(state["execution"]["stop_reason"], "timeout")
        self.assertGreaterEqual(state["execution"]["elapsed_seconds"], 21)

    def test_legacy_completed_state_has_no_invented_review_receipt(self):
        self.runner.store.update(phase="complete", enabled=False,
                                 review={"verdict":"pass", "findings":"Historical review"})
        restarted = Runner(self.runner.config, clock=lambda: self.fixture.now)
        state = restarted.status()
        self.assertEqual(state["phase"], "complete")
        self.assertFalse(state.get("goal_review"))
        self.assertEqual(self.step(restarted), "paused")

    def test_worker_cannot_drop_unresolved_review_requirement(self):
        first = True
        def worker():
            nonlocal first
            (self.fixture.root / "app.py").write_text("value = 1\n")
            value = result("change_ready", "change")
            value["review_required"] = first
            first = False
            return value
        self.agent(worker, lambda _:review("repair", criteria=False))
        self.step()
        self.runner.store.update(retry_after=0)
        self.step()
        self.assertEqual(self.runner.head(), self.fixture.initial)
        self.assertIn("Review requests repair", self.runner.store.read()["feedback"])

    def test_worker_cannot_downgrade_goal_repair_to_change_review(self):
        n = 0
        def worker():
            nonlocal n
            n += 1
            (self.fixture.root / "app.py").write_text(f"value = {n}\n")
            return result("change_ready", "goal" if n == 1 else "change")
        def reviewer(prompt):
            self.assertIn("Review scope: goal", prompt)
            return review("repair", criteria=False)
        self.agent(worker, reviewer)
        self.step()
        self.runner.store.update(retry_after=0)
        self.step()
        self.assertEqual(self.runner.head(), self.fixture.initial)

    def test_review_repair_receipt_and_obligation_survive_one_atomic_write(self):
        self.agent(lambda:result(), lambda _:review("repair", completion_only=True))
        update = self.runner.store.update
        def crash_after_receipt(**changes):
            state = update(**changes)
            if changes.get("review", {}).get("verdict") == "repair":
                raise RuntimeError("Simulated power loss")
            return state
        with patch.object(self.runner.store, "update", side_effect=crash_after_receipt):
            with self.assertRaisesRegex(RuntimeError, "power loss"):
                self.step()
        state = self.runner.store.read()
        self.assertEqual(state["review_obligation"]["result"]["verdict"], "repair")
        self.assertTrue(state["goal_review"]["result"]["goal_criteria_verified"])

    def test_completed_process_after_wall_deadline_is_not_accepted(self):
        def executor(command, **kwargs):
            self.fixture.now += timedelta(seconds=21)
            return 0, False
        self.runner.executor = executor
        with patch("devloop.runner.time.monotonic", return_value=100):
            with self.assertRaisesRegex(ValueError, "turn limit"):
                self.runner.execute(["fixture"], "working")

    def test_late_exit_after_window_closes_preserves_pause_without_acceptance(self):
        def executor(command, **kwargs):
            self.fixture.now += timedelta(hours=6)
            return 0, False
        self.runner.executor = executor
        with patch("devloop.runner.time.monotonic", return_value=100), self.assertRaises(Paused):
            self.runner.execute(["fixture"], "working")
        self.assertEqual(self.runner.store.read()["execution"]["stop_reason"], "window_closed")
        self.assertEqual(self.runner.store.read()["failures"], 0)

    def test_corrupt_receipt_fails_closed_before_worker(self):
        state = self.runner.store.read()
        state["verification"] = {"key":{}, "checks":[]}
        self.runner.store.path.write_text(json.dumps(state))
        self.agent(lambda:self.fail("Worker invoked"))
        with self.assertRaisesRegex(ValueError, "verification key"):
            self.step()

    def test_execution_logs_include_timing_without_model_events(self):
        import sys
        log = self.runner.execute([sys.executable, "-c", "print('fixture')"], "checking")
        events = []
        for line in log.read_text().splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                pass
        self.assertEqual([e["type"] for e in events], ["execution.started", "execution.finished"])
        self.assertEqual(events[-1]["stop_reason"], "completed")
        self.assertIsNotNone(events[-1]["last_output_at"])
