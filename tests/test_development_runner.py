"""Exercise the runner against real Git repositories and child processes."""

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from devloop.config import Config, Window
from devloop.runner import Runner, validate_result, WORK_SCHEMA
from devloop.runtime import Busy, Store, lock, run_process


FAKE_CODEX = r'''
import json, sys
from pathlib import Path
args = sys.argv[1:]
root = Path.cwd()
store = root / '.git'
calls = store / 'fake-calls.json'
history = json.loads(calls.read_text()) if calls.exists() else []
review = 'sandbox_mode="read-only"' in args
prompt = sys.stdin.read()
history.append({'review':review, 'resume':'resume' in args, 'prompt':prompt})
calls.write_text(json.dumps(history))
mode = (store / 'fake-mode').read_text() if (store / 'fake-mode').exists() else 'normal'
if not review:
 print(json.dumps({'type':'thread.started','thread_id':'fixture-session'}),flush=True)
number = sum(not item['review'] for item in history)
if review:
 result = {'verdict':'repair' if mode == 'review-fails' else 'pass','findings':'Fix the boundary' if mode == 'review-fails' else '', 'goal_criteria_verified':mode != 'review-fails','completion_only':False}
else:
 if mode == 'missing-result': sys.exit(0)
 if mode == 'crash': sys.exit(7)
 if number <= 2 or mode == 'always-change':
  target = 'boundary.py' if mode in {'risky','review-fails'} else 'app.py'
  (root / target).write_text('value = ' + str(number) + '\n')
  outcome = 'change_ready'
 else: outcome = 'goal_complete'
 if mode == 'blocked': outcome = 'blocked'
 if mode == 'false-progress': outcome = 'change_ready'; (root / 'app.py').write_text('value = 0\n')
 result = {'outcome':outcome,'summary':'Implemented behavior '+str(number),'evidence':'Executed the fixture behavior and its checks','remaining':'Need owner direction' if mode == 'blocked' else '','commit_message':'Implement behavior '+str(number),'review_required':False,'review_reason':''}
 result.update(review_scope='goal' if outcome == 'goal_complete' else 'change', artifacts=[])
 if mode == 'wait-for-pause':
  import time
  time.sleep(30)
output = Path(args[args.index('-o')+1])
output.write_text(json.dumps(result))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':10,'output_tokens':4}}),flush=True)
'''


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Fixture')
        (self.root / 'goal.md').write_text('Implement two useful changes; preserve the boundary.\n')
        (self.root / 'skill.md').write_text('Complete the approved goal.\n')
        (self.root / 'app.py').write_text('value = 0\n')
        (self.root / 'boundary.py').write_text('value = 0\n')
        (self.root / '.gitignore').write_text('__pycache__/\n*.pyc\n')
        (self.root / 'tests').mkdir()
        (self.root / 'tests' / 'check.py').write_text('assert True\n')
        fake = self.root / '.git' / 'fake_codex.py'
        fake.write_text(FAKE_CODEX)
        config = f'''project = "fixture"
goal = "goal.md"
skill = "skill.md"
[window]
timezone = "America/Toronto"
start = "18:00"
end = "23:00"
checkpoint_seconds = 120
[agent]
command = {json.dumps([sys.executable, str(fake)])}
model = "fixture"
review_model = "fixture-review"
reasoning = "high"
sandbox = "workspace-write"
[limits]
turn_seconds = 20
failed_attempts = 3
retry_seconds = 1
[validation]
commands = [["{{python}}", "-c", "import app; assert app.value >= 0"], ["git", "diff", "--check"]]
[review]
paths = ["boundary.py"]
test_paths = ["tests/**"]
'''
        (self.root / 'development-loop.toml').write_text(config)
        self.git('add', '.')
        self.git('commit', '-qm', 'Fixture baseline')
        self.initial = self.git('rev-parse', 'HEAD')
        self.now = datetime(2026, 9, 22, 22, 37, tzinfo=timezone.utc)  # 18:37 Toronto
        self.runner = Runner(Config(self.root / 'development-loop.toml'), clock=lambda: self.now)
        self.runner.enable()

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, text=True).strip()

    def mode(self, value):
        (self.root / '.git' / 'fake-mode').write_text(value)

    def calls(self):
        path = self.root / '.git' / 'fake-calls.json'
        return json.loads(path.read_text()) if path.exists() else []

    def test_continues_multiple_changes_without_timer_or_new_worker(self):
        self.assertEqual(self.runner.run(), 0)
        calls = self.calls()
        self.assertEqual([c['review'] for c in calls], [False, False, False, True])
        self.assertFalse(calls[0]['resume'])
        self.assertTrue(calls[1]['resume'])
        self.assertEqual(self.git('rev-list', '--count', f'{self.initial}..HEAD'), '2')
        state = self.runner.store.read()
        self.assertEqual(state['phase'], 'complete')
        self.assertEqual(state['usage']['input_tokens'], 40)
        self.assertFalse(self.runner.dirty())

    def test_no_model_outside_window_and_restart_midwindow_works(self):
        self.now = datetime(2026, 9, 22, 21, 59, tzinfo=timezone.utc)
        self.assertEqual(self.runner.step(), 'outside_window')
        self.assertEqual(self.calls(), [])
        self.now = datetime(2026, 9, 23, 0, 37, tzinfo=timezone.utc)
        self.assertEqual(self.runner.step(), 'ready')
        self.assertEqual(len(self.calls()), 1)

    def test_no_new_work_during_checkpoint_margin(self):
        self.now = datetime(2026, 9, 23, 2, 59, tzinfo=timezone.utc)
        self.assertEqual(self.runner.step(), 'outside_window')
        self.assertEqual(self.calls(), [])

    def test_sensitive_change_is_reviewed_despite_passing_tests(self):
        self.mode('risky')
        self.assertEqual(self.runner.step(), 'ready')
        self.assertEqual([c['review'] for c in self.calls()], [False, True])
        self.assertEqual(self.runner.store.read()['review']['verdict'], 'pass')

    def test_review_failure_preserves_work_and_does_not_commit(self):
        self.mode('review-fails')
        self.assertEqual(self.runner.step(), 'ready')
        state = self.runner.store.read()
        self.assertIn('Fix the boundary', state['feedback'])
        self.assertEqual(state['failures'], 1)
        self.assertEqual(self.runner.head(), self.initial)
        self.assertTrue(self.runner.dirty())

    def test_check_failure_returns_to_worker_without_review(self):
        self.runner.config.checks = [[sys.executable, '-c', 'raise SystemExit(1)']]
        self.runner.step()
        self.assertEqual(len(self.calls()), 1)
        self.assertIn('checking failed', self.runner.store.read()['feedback'])
        self.assertEqual(self.runner.head(), self.initial)

    def test_validation_mutation_invalidates_candidate(self):
        self.runner.config.checks = [[sys.executable, '-c', 'from pathlib import Path; Path("app.py").write_text("value = 9\\n")']]
        self.runner.step()
        self.assertIn('Validation changed', self.runner.store.read()['feedback'])
        self.assertEqual(self.runner.head(), self.initial)

    def test_retry_limit_survives_restart(self):
        self.mode('crash')
        for _ in range(3):
            self.runner.store.update(retry_after=0)
            self.runner = Runner(self.runner.config, clock=lambda: self.now)
            self.runner.step()
        self.assertEqual(self.runner.store.read()['phase'], 'blocked')
        self.assertEqual(self.runner.store.read()['failures'], 3)
        self.assertEqual(self.runner.step(), 'blocked')
        self.assertEqual(len(self.calls()), 3)

    def test_missing_result_cannot_reuse_previous_output(self):
        self.runner.step()
        self.mode('missing-result')
        self.runner.step()
        self.assertIn('without the required structured result', self.runner.store.read()['feedback'])
        self.assertEqual(self.git('rev-list', '--count', f'{self.initial}..HEAD'), '1')

    def test_blocked_result_stops_without_accepting_unfinished_work(self):
        self.mode('blocked')
        self.assertEqual(self.runner.run(), 2)
        self.assertIn('Need owner direction', self.runner.store.read()['reason'])
        self.assertEqual(self.runner.head(), self.initial)

    def test_goal_change_blocks_before_next_model_call(self):
        (self.root / 'goal.md').write_text('A different product goal.\n')
        self.assertEqual(self.runner.step(), 'blocked')
        self.assertEqual(self.calls(), [])

    def test_unowned_changes_block_without_absorbing_them(self):
        (self.root / 'user.txt').write_text('My unfinished work')
        self.assertEqual(self.runner.step(), 'blocked')
        self.assertEqual(self.calls(), [])
        self.assertEqual(self.runner.head(), self.initial)

    def test_pause_during_child_keeps_checkpoint_for_next_session(self):
        original = self.runner.executor

        def pause(*args, **kwargs):
            code, _ = original(*args, **kwargs)
            self.runner.store.update(enabled=False)
            return code, True

        self.runner.executor = pause
        self.assertEqual(self.runner.step(), 'paused')
        self.assertTrue(self.runner.dirty())
        state = self.runner.store.read()
        self.assertEqual(state['session_id'], 'fixture-session')
        self.assertEqual(state['failures'], 0)
        self.assertEqual(self.runner.head(), self.initial)
        self.runner.executor = original
        self.runner.enable()
        self.assertEqual(self.runner.step(), 'ready')
        self.assertTrue(self.calls()[-1]['resume'])

    def test_running_service_can_pause_and_resume_without_releasing_ownership(self):
        self.mode('wait-for-pause')
        errors = []

        def serve():
            try:
                self.runner.run(service=True)
            except Exception as error:
                errors.append(error)

        def until(predicate):
            deadline = time.monotonic() + 12
            while not predicate():
                if time.monotonic() >= deadline:
                    self.fail('Service did not reach the expected state')
                time.sleep(0.05)

        thread = threading.Thread(target=serve)
        thread.start()
        try:
            until(lambda: (self.root / 'app.py').read_text() == 'value = 1\n')
            self.runner.store.update(enabled=False)
            until(lambda: self.runner.store.read().get('child_pid') is None)
            self.assertEqual(self.runner.head(), self.initial)
            self.assertTrue(self.runner.dirty())
            with self.assertRaises(Busy):
                self.runner.enable()
            self.mode('normal')
            self.runner.resume()
            until(lambda: self.runner.store.read()['phase'] == 'complete')
            self.assertTrue(thread.is_alive())
            self.assertTrue(self.calls()[1]['resume'])
            self.assertFalse(errors)
        finally:
            self.runner.interrupted = True
            thread.join(timeout=15)
            self.assertFalse(thread.is_alive())

    def test_resume_keeps_failure_budget_and_cannot_bypass_a_block(self):
        self.runner.store.update(enabled=False, failures=2)
        self.runner.resume()
        self.assertEqual(self.runner.store.read()['failures'], 2)
        self.runner.store.update(enabled=False, phase='blocked')
        with self.assertRaises(ValueError):
            self.runner.resume()

    def test_window_closing_preserves_work_for_next_evening(self):
        original = self.runner.executor

        def close_window(*args, **kwargs):
            code, _ = original(*args, **kwargs)
            self.now = datetime(2026, 9, 23, 2, 58, tzinfo=timezone.utc)
            return code, True

        self.runner.executor = close_window
        self.assertEqual(self.runner.step(), 'paused')
        self.assertEqual(self.runner.store.read()['failures'], 0)
        self.assertEqual(self.runner.step(), 'outside_window')
        self.assertEqual(len(self.calls()), 1)
        self.runner.executor = original
        self.now = datetime(2026, 9, 23, 22, 37, tzinfo=timezone.utc)
        self.assertEqual(self.runner.step(), 'ready')
        self.assertTrue(self.calls()[-1]['resume'])

    def test_new_goal_cannot_absorb_unfinished_old_goal_work(self):
        self.mode('review-fails')
        self.runner.step()
        (self.root / 'goal.md').write_text('A different approved responsibility.\n')
        with self.assertRaisesRegex(ValueError, 'Resolve unfinished work'):
            self.runner.enable()

    def test_corrupt_enable_flag_fails_closed(self):
        self.runner.store.path.write_text(json.dumps({'version':1, 'enabled':'false', 'phase':'ready', 'failures':0}))
        with self.assertRaises(ValueError):
            self.runner.step()
        self.assertEqual(self.calls(), [])

    def test_crash_after_commit_finalizes_exactly_once(self):
        with patch.object(self.runner, 'finish', side_effect=RuntimeError('simulated power loss')):
            with self.assertRaises(RuntimeError):
                self.runner.step()
        committed = self.runner.head()
        self.assertNotEqual(committed, self.initial)
        self.runner = Runner(self.runner.config, clock=lambda: self.now)
        self.assertEqual(self.runner.step(), 'ready')
        self.assertEqual(self.runner.head(), committed)
        self.assertEqual(len(self.calls()), 1)
        self.assertIsNone(self.runner.store.read()['commit_intent'])

    def test_test_deletion_triggers_review_but_addition_does_not(self):
        path = self.root / 'tests' / 'check.py'
        result = {'review_required':False,'outcome':'change_ready','review_reason':''}
        path.write_text('assert True\nassert 1 == 1\n')
        self.runner.tree()
        self.assertEqual(self.runner.review_reasons(result), [])
        path.write_text('assert 1 == 1\n')
        self.runner.tree()
        self.assertIn('Existing test behavior changed', self.runner.review_reasons(result)[0])

    def test_second_runner_cannot_acquire_exclusive_ownership(self):
        with lock(self.runner.store.directory / 'runner.lock', blocking=False):
            with self.assertRaises(Busy):
                self.runner.run()

    def test_service_replacement_waits_for_ownership_to_be_released(self):
        path = self.runner.store.directory / 'runner.lock'
        acquired = threading.Event()

        def shutting_down():
            with lock(path):
                acquired.set()
                time.sleep(0.25)

        thread = threading.Thread(target=shutting_down)
        thread.start()
        self.assertTrue(acquired.wait(timeout=2))
        try:
            with self.assertRaises(Busy):
                with lock(path, timeout=0.01):
                    pass
            with lock(path, timeout=2):
                pass
        finally:
            thread.join(timeout=2)

    def test_enable_does_not_override_a_live_child(self):
        self.runner.store.update(child_pid=os.getpid())
        with self.assertRaises(Busy):
            self.runner.enable()

    def test_state_updates_preserve_owner_pause(self):
        self.runner.store.update(enabled=False)
        self.runner.store.update(summary='child finished')
        self.assertFalse(self.runner.store.read()['enabled'])

    def test_process_interruption_returns_and_preserves_partial_output(self):
        log = self.root / '.git' / 'stopped.log'
        seen = []
        code, stopped = run_process([sys.executable, '-c', 'import time; print("started",flush=True); time.sleep(30)'],
                                    cwd=self.root, log=log, input_text=None, env=os.environ.copy(),
                                    stop=lambda: 'started' in log.read_text(), event=lambda _:None,
                                    started=seen.append)
        self.assertTrue(stopped)
        self.assertNotEqual(code, 0)
        self.assertIsNone(seen[-1])
        self.assertIn('started', log.read_text())

    def test_invalid_result_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_result({'outcome':'goal_complete'}, WORK_SCHEMA)


class WindowTests(unittest.TestCase):
    def test_dst_uses_toronto_wall_clock(self):
        window = Window({'timezone':'America/Toronto','start':'18:00','end':'23:00'})
        self.assertEqual(window.remaining(datetime(2026, 9, 22, 22, 0, tzinfo=timezone.utc)), 5 * 3600)
        self.assertEqual(window.remaining(datetime(2026, 12, 22, 23, 0, tzinfo=timezone.utc)), 5 * 3600)
        self.assertEqual(window.remaining(datetime(2026, 9, 23, 3, 0, tzinfo=timezone.utc)), 0)

    def test_overnight_window(self):
        window = Window({'timezone':'UTC','start':'22:00','end':'02:00'})
        self.assertEqual(window.remaining(datetime(2026, 9, 23, 1, 0, tzinfo=timezone.utc)), 3600)
        self.assertEqual(window.remaining(datetime(2026, 9, 23, 3, 0, tzinfo=timezone.utc)), 0)


if __name__ == '__main__':
    unittest.main()
