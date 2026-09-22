"""Exercise dashboard controls and terminal behavior without starting models."""

import fcntl
import json
import os
import pty
import select
import signal
import struct
import subprocess
import sys
import termios
import time
import unittest
from pathlib import Path

from devloop.dashboard import Dashboard
from devloop.dashboard_data import DashboardData, cells, clean, event_rows, wrap
from tests import test_development_runner as fixtures


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.RunnerTests('test_no_new_work_during_checkpoint_margin')
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.runner = self.fixture.runner
        self.runner.store.update(enabled=False, runner_pid=os.getpid())
        self.data = DashboardData(self.runner)
        self.data.refresh()

    def test_structured_messages_are_readable_and_controls_are_removed(self):
        rows = event_rows({'type':'item.completed', 'item':{'type':'agent_message', 'text':json.dumps({
            'outcome':'checkpoint', 'summary':'Waiting for Qwen', 'remaining':'Restore endpoint', 'evidence':'Timed out'})}})
        self.assertIn(('Waiting for Qwen', 'normal'), rows)
        self.assertIn(('REMAINING', 'accent'), rows)
        self.assertNotIn('"outcome"', str(rows))
        self.assertEqual(clean('\x1b[31mred\x1b[0m\x1b]0;danger\x07\r\x00'), 'red')

    def test_logs_handle_partial_events_and_follow_new_execution(self):
        folder = self.runner.store.directory / 'runs'
        folder.mkdir()
        older = folder / 'older.jsonl'
        older.write_text('plain check output\n')
        self.data.refresh()
        self.assertIn(('plain check output', 'normal'), self.data.activity())
        newer = folder / 'newer.jsonl'
        newer.write_text('{"type":"item.completed","item":{"type":"agent_message","text":"new message"}}\n{"type":')
        os.utime(newer, (time.time() + 1, time.time() + 1))
        self.data.refresh()
        self.assertIn(('new message', 'normal'), self.data.activity())
        self.assertNotIn('{"type":', str(self.data.activity()))
        self.data.choose_log(1)
        self.assertEqual(self.data.log_path(), older)
        self.data.choose_log(-1)
        self.assertEqual(self.data.log_path(), newer)

    def test_log_tail_is_bounded_and_cannot_follow_an_external_symlink(self):
        folder = self.runner.store.directory / 'runs'
        folder.mkdir()
        large = folder / 'large.jsonl'
        large.write_text('old output\n' * 20000 + 'latest output\n')
        self.data.refresh()
        rows = self.data.activity()
        self.assertLessEqual(len(rows), 2000)
        self.assertEqual(rows[-1], ('latest output', 'normal'))
        link = folder / 'linked.jsonl'
        link.symlink_to(self.fixture.root / 'goal.md')
        self.data.selected_log = link
        self.assertIn('outside', str(self.data.activity()))

    def test_status_distinguishes_pause_window_wait_and_block(self):
        self.assertEqual(self.data.status()[0], 'PAUSED')
        self.runner.store.update(enabled=True, phase='ready')
        self.data.refresh()
        self.assertEqual(self.data.status()[0], 'READY')
        self.runner.store.update(phase='blocked')
        self.data.refresh()
        self.assertEqual(self.data.status()[0], 'BLOCKED')
        self.runner.store.update(phase='ready')
        self.fixture.now = self.fixture.now.replace(hour=12)
        self.data.refresh()
        self.assertEqual(self.data.status()[0], 'WAITING FOR WINDOW')

    def test_resume_does_not_clear_a_block_or_failure_budget(self):
        dashboard = Dashboard(self.runner)
        self.runner.store.update(phase='blocked', failures=3)
        dashboard.control('resume')
        state = self.runner.store.read()
        self.assertFalse(state['enabled'])
        self.assertEqual(state['failures'], 3)
        self.assertIn('Cannot resume', dashboard.message)

    def test_corrupt_state_is_visible_without_overwriting_it(self):
        self.runner.store.path.write_text('{partial')
        self.data.refresh()
        self.assertEqual(self.data.status()[0], 'READ ERROR')
        self.assertEqual(self.runner.store.path.read_text(), '{partial')

    def test_changes_show_new_files_and_commits_without_writing_state(self):
        (self.fixture.root / 'new-behavior.py').write_text('value = 1\n')
        state_before = self.runner.store.path.read_bytes()
        rows = str(self.data.changes())
        self.assertIn('new-behavior.py', rows)
        self.assertIn('Fixture baseline', rows)
        self.assertIn('No tracked edits', rows)
        self.assertEqual(self.runner.store.path.read_bytes(), state_before)
        self.assertEqual(self.runner.head(), self.fixture.initial)

    def test_navigation_filter_and_command_modes(self):
        dashboard = Dashboard(self.runner)
        dashboard.page_size, dashboard.line_count = 10, 100
        dashboard.key('k')
        self.assertEqual(dashboard.offset, 89)
        dashboard.key('g')
        dashboard.key('\x04')
        self.assertEqual(dashboard.offset, 5)
        dashboard.key('G')
        self.assertIsNone(dashboard.offset)
        dashboard.key('2')
        self.assertEqual(dashboard.tab, 1)
        for key in '/needle\n':
            dashboard.key(key)
        self.assertEqual(dashboard.filter, 'needle')
        dashboard.key('\x1b')
        self.assertEqual(dashboard.filter, '')
        for key in ':q\n':
            dashboard.key(key)
        self.assertTrue(dashboard.quitting)

    def test_wrapping_preserves_wide_text_and_respects_terminal_columns(self):
        text = 'Mara sees 世界 at the café ' + 'x' * 80
        lines = wrap(text, 15)
        self.assertTrue(all(cells(line) <= 15 for line in lines))
        self.assertEqual(''.join(lines).replace(' ', ''), text.replace(' ', ''))

    def terminal(self):
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 24, 80, 0, 0))
        before = termios.tcgetattr(slave)
        repository = str(Path(__file__).resolve().parents[1])
        process = subprocess.Popen([sys.executable, '-m', 'devloop', '--config', str(self.runner.config.path), 'dashboard'],
                                   cwd=self.runner.root, stdin=slave, stdout=slave, stderr=slave,
                                   env={**os.environ, 'TERM':'xterm-256color', 'PYTHONPATH':repository}, start_new_session=True)

        def cleanup():
            if process.poll() is None:
                process.kill()
                process.wait(timeout=3)
            os.close(master)
            os.close(slave)

        self.addCleanup(cleanup)
        return process, master, slave, before

    def wait_terminal(self, process, master, predicate, timeout=5):
        output = b''
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if select.select([master], [], [], 0.05)[0]:
                try:
                    output += os.read(master, 65536)
                except OSError:
                    break
            if predicate(output):
                return output
            if process.poll() is not None:
                break
        self.fail(f'Terminal did not reach expected state: {output[-1500:]!r}')

    def test_real_terminal_resize_and_exit_preserve_state_and_restore_terminal(self):
        state_before = self.runner.store.path.read_bytes()
        process, master, slave, terminal_before = self.terminal()
        self.wait_terminal(process, master, lambda out: b'PAUSED' in out and b'Activity' in out)
        for rows, columns, expected in ((38, 132, b'WINDOW'), (12, 40, b'enlarge'), (24, 80, b'Activity')):
            fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', rows, columns, 0, 0))
            os.kill(process.pid, signal.SIGWINCH)
            self.wait_terminal(process, master, lambda out: expected in out)
        os.write(master, b'q')
        self.wait_terminal(process, master, lambda out: process.poll() is not None)
        self.assertEqual(process.wait(timeout=3), 0)
        self.assertEqual(self.runner.store.path.read_bytes(), state_before)
        restored = termios.tcgetattr(slave)
        # macOS may set PENDIN while canonical input resumes; it is not a mode leak.
        restored[3] &= ~getattr(termios, 'PENDIN', 0)
        terminal_before[3] &= ~getattr(termios, 'PENDIN', 0)
        self.assertEqual(restored, terminal_before)
        self.assertFalse((self.fixture.root / '.git' / 'fake-calls.json').exists())

    def test_real_terminal_pause_resume_controls_and_quit_leave_loop_running(self):
        process, master, _, _ = self.terminal()
        self.wait_terminal(process, master, lambda out: b'PAUSED' in out)
        os.write(master, b'r')
        self.wait_terminal(process, master, lambda out: self.runner.store.read()['enabled'])
        os.write(master, b'p')
        self.wait_terminal(process, master, lambda out: not self.runner.store.read()['enabled'])
        os.write(master, b':resume\n')
        self.wait_terminal(process, master, lambda out: self.runner.store.read()['enabled'])
        os.write(master, b'q')
        self.wait_terminal(process, master, lambda out: process.poll() is not None)
        self.assertEqual(process.wait(timeout=3), 0)
        self.assertTrue(self.runner.store.read()['enabled'])
        self.assertFalse((self.fixture.root / '.git' / 'fake-calls.json').exists())


if __name__ == '__main__':
    unittest.main()
