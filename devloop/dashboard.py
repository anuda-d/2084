"""Keyboard-driven terminal dashboard; viewing it never starts agent work."""

from __future__ import annotations

import curses
import locale
import sys
import time

from .dashboard_data import DashboardData, cells, clean, wrap
from .runtime import process_alive

TABS = ("Activity", "Changes", "Checks", "Details")
HELP = [
    ("NAVIGATION", "accent"),
    ("1-4             Open Activity, Changes, Checks, or Details", "normal"),
    ("h / l / Tab     Switch views (arrow keys also work)", "normal"),
    ("j / k           Scroll down / up", "normal"),
    ("Ctrl-d / Ctrl-u Scroll half a page", "normal"),
    ("g / G           Go to the top / follow the latest output", "normal"),
    ("[ / ]           Older / newer execution log", "normal"),
    ("/               Filter the current view; Enter applies", "normal"),
    ("Esc             Clear a filter or dismiss help", "normal"),
    ("", "normal"),
    ("CONTROL", "accent"),
    ("p               Pause work and preserve the current session", "normal"),
    ("r               Resume the approved goal within its daily window", "normal"),
    ("q / :q          Close this dashboard; leave the loop as it is", "normal"),
    (":pause :resume  Named control commands", "normal"),
    ("? / :help       Show these keys", "normal"),
    ("", "normal"),
    ("Resume never resets the repair budget or bypasses a blocked goal.", "muted"),
    ("Views refresh automatically. No models or provider probes are called.", "muted"),
]


class Dashboard:
    def __init__(self, runner):
        self.runner = runner
        self.data = DashboardData(runner)
        self.tab = 0
        self.offset: int | None = None
        self.page_size = 1
        self.line_count = 0
        self.filter = ""
        self.edit = ""
        self.edit_mode = ""
        self.help = False
        self.message = "Viewing only. q closes the dashboard without pausing work."
        self.quitting = False
        self.colors = {tone: 0 for tone in ("normal", "accent", "good", "warning", "error", "muted")}
        self.goal_title = clean(runner.config.goal.read_text().splitlines()[0].lstrip("# "))

    def control(self, command: str):
        try:
            if command == "pause":
                self.runner.store.update(enabled=False)
                self.message = "Pause requested. The child will stop; unfinished work is preserved."
            elif command == "resume":
                if self.data.error:
                    raise ValueError("Resolve the state read error before resuming")
                state = self.runner.store.read()
                if not process_alive(state.get("runner_pid")):
                    raise ValueError("Service is offline. Start the runner before resuming work.")
                self.runner.resume()
                self.message = "Resumed. Work continues whenever the daily window is open."
            else:
                self.message = "Unknown command. Use :pause, :resume, :help, or :q."
        except (OSError, ValueError) as error:
            self.message = "Cannot " + command + ": " + str(error)
        self.data.refresh()

    def key(self, key):
        if self.edit_mode:
            if key == "\x1b":
                self.edit_mode, self.edit = "", ""
            elif key in ("\n", "\r", curses.KEY_ENTER):
                mode, text = self.edit_mode, self.edit.strip()
                self.edit_mode, self.edit = "", ""
                if mode == "/":
                    self.filter, self.offset = text, 0
                elif text in {"q", "quit"}:
                    self.quitting = True
                elif text in {"help", "h"}:
                    self.help, self.offset = True, 0
                else:
                    self.control(text)
            elif key in (curses.KEY_BACKSPACE, "\x7f", "\b"):
                self.edit = self.edit[:-1]
            elif isinstance(key, str) and key.isprintable() and len(self.edit) < 200:
                self.edit += key
            return
        if key == "q":
            self.quitting = True
        elif key in ("/", ":"):
            self.edit_mode, self.edit = key, ""
        elif key in ("?", "\x1b"):
            self.help = not self.help if key == "?" else False
            self.filter, self.offset = "", 0
        elif self.help:
            self.scroll(key)
        elif key in ("p", "r"):
            self.control("pause" if key == "p" else "resume")
        elif key in ("h", "l", "\t", curses.KEY_LEFT, curses.KEY_RIGHT, "1", "2", "3", "4"):
            if key in ("1", "2", "3", "4"):
                self.tab = int(key) - 1
            else:
                self.tab = (self.tab + (-1 if key in ("h", curses.KEY_LEFT) else 1)) % len(TABS)
            self.offset = None if self.tab == 0 else 0
            self.filter = ""
        elif key in ("[", "]"):
            self.data.choose_log(1 if key == "[" else -1)
            self.tab, self.offset, self.filter = 0, None, ""
        else:
            self.scroll(key)

    def scroll(self, key):
        end = max(0, self.line_count - self.page_size)
        current = end if self.offset is None else self.offset
        if key in ("g", curses.KEY_HOME):
            self.offset = 0
        elif key in ("G", curses.KEY_END):
            self.offset = None
        elif key in ("j", "k", curses.KEY_DOWN, curses.KEY_UP, "\x04", "\x15", curses.KEY_NPAGE, curses.KEY_PPAGE):
            delta = max(1, self.page_size // 2) if key in ("\x04", "\x15", curses.KEY_NPAGE, curses.KEY_PPAGE) else 1
            if key in ("k", curses.KEY_UP, "\x15", curses.KEY_PPAGE):
                delta = -delta
            self.offset = min(end, max(0, current + delta))

    def text(self, screen, y, x, text, width, tone="normal", bold=False):
        height, columns = screen.getmaxyx()
        if y < 0 or y >= height or x < 0 or x >= columns - 1 or width <= 0:
            return
        available = min(width, columns - x - 1)
        rendered = ""
        for char in clean(text).replace("\n", " "):
            if cells(rendered + char) > available:
                break
            rendered += char
        try:
            screen.addstr(y, x, rendered, self.colors.get(tone, 0) | (curses.A_BOLD if bold else 0))
        except curses.error:
            pass  # A resize may arrive between measuring and drawing.

    def draw(self, screen):
        height, width = screen.getmaxyx()
        screen.erase()
        if height < 16 or width < 52:
            self.text(screen, 0, 0, "2084 loop / enlarge to at least 52 x 16", width, "warning")
            self.text(screen, 2, 0, "q closes the dashboard; the loop keeps its state.", width)
            screen.refresh()
            return
        status, tone = self.data.status()
        state, config = self.data.state, self.runner.config
        self.text(screen, 0, 2, f"{config.project} / DEVELOPMENT", width - len(status) - 8, "accent", True)
        self.text(screen, 0, width - len(status) - 3, status, len(status), tone, True)
        self.text(screen, 1, 2, self.goal_title, width - 4, "muted")
        note = self.data.error or state.get("reason") or state.get("remaining") or "No result recorded yet. Open Activity to follow the next run."
        note_lines = wrap(note, width - 10)
        self.text(screen, 3, 2, "NEXT", 5, "muted")
        for index, line in enumerate(note_lines[:2]):
            if index == 1 and len(note_lines) > 2:
                line = line[:max(0, width - 14)] + "..."
            self.text(screen, 3 + index, 8, line, width - 10, "error" if self.data.error else "normal")
        x = 2
        for index, title in enumerate(TABS):
            label = f" {index + 1} {title if width >= 65 else title[:3]} "
            self.text(screen, 6, x, label, len(label), "accent" if index == self.tab and not self.help else "muted", index == self.tab)
            x += len(label) + 1
        self.text(screen, 7, 2, "-" * (width - 4), width - 4, "muted")
        left = 33 if width >= 110 else 2
        if left > 2:
            now = self.runner.clock().astimezone(config.window.zone)
            remaining = config.window.remaining(now)
            usage = state.get("usage", {})
            sidebar = [
                ("WINDOW", "accent"),
                (f"{config.window.start:%H:%M} - {config.window.end:%H:%M}", "normal"),
                (str(config.window.zone), "muted"),
                (f"{int(remaining)//3600}h {int(remaining)//60%60:02}m left" if remaining else "Outside work window", "muted"),
                ("", "normal"), ("WORKER", "accent"), (config.agent["model"], "normal"),
                ("", "normal"), ("SERVICE", "accent"),
                ("Running" if process_alive(state.get("runner_pid")) else "Offline", "normal"),
                (f"Unsuccessful attempts  {state.get('failures', 0)}/{config.limits['failed_attempts']}", "normal"),
                ("", "normal"), ("TOKEN USAGE", "accent"),
                (f"Input   {usage.get('input_tokens', 0):,}", "normal"),
                (f"Cached  {usage.get('cached_input_tokens', 0):,}", "muted"),
                (f"Output  {usage.get('output_tokens', 0):,}", "normal"),
                ("", "normal"), ("p pause    r resume", "muted"),
            ]
            for index, (line, color) in enumerate(sidebar[:height - 12]):
                self.text(screen, 8 + index, 2, line, 28, color)
            for y in range(8, height - 4):
                self.text(screen, y, 30, "|", 1, "muted")
        rows = HELP if self.help else (self.data.activity, self.data.changes, self.data.checks, self.data.details)[self.tab]()
        if self.filter:
            rows = [row for row in rows if self.filter.casefold() in row[0].casefold()]
        content = [(part, color) for text, color in rows for part in wrap(text, width - left - 3)]
        if not content:
            content = [("No matching lines. Esc clears the filter.", "muted")]
        self.page_size, self.line_count = height - 12, len(content)
        end = max(0, len(content) - self.page_size)
        start = end if self.offset is None else min(self.offset, end)
        for y, (line, color) in enumerate(content[start:start + self.page_size], 8):
            if self.tab == 1 and color == "normal":
                color = "good" if line.startswith("+") else "error" if line.startswith("-") else color
            self.text(screen, y, left, line, width - left - 3, color)
        position = "FOLLOW" if self.offset is None else f"{start + 1}-{min(len(content), start + self.page_size)}/{len(content)}"
        path = self.data.log_path() if self.tab == 0 and not self.help else None
        label = f"{position}  {'Help' if self.help else path.name if path else TABS[self.tab]}"
        if self.filter:
            label += "  /" + self.filter
        self.text(screen, height - 4, 2, label, width - 4, "muted")
        self.text(screen, height - 3, 2, self.edit_mode + self.edit if self.edit_mode else self.message, width - 4, "warning" if self.edit_mode else "muted")
        self.text(screen, height - 2, 2, "j/k scroll h/l views g/G top/follow [/] logs", width - 4, "accent")
        self.text(screen, height - 1, 2, "p pause r resume / filter ? help q close", width - 4, "accent")
        screen.refresh()

    def run(self, screen):
        screen.keypad(True)
        screen.timeout(100)
        curses.set_escdelay(25)
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        self.colors["muted"] = curses.A_DIM
        if curses.has_colors():
            curses.start_color()
            try:
                curses.use_default_colors()
                background = -1
            except curses.error:
                background = curses.COLOR_BLACK
            for index, (tone, color) in enumerate((("accent", curses.COLOR_CYAN), ("good", curses.COLOR_GREEN),
                                                    ("warning", curses.COLOR_YELLOW), ("error", curses.COLOR_RED)), 1):
                curses.init_pair(index, color, background)
                self.colors[tone] = curses.color_pair(index)
        refreshed, dirty = 0.0, True
        while not self.quitting:
            if time.monotonic() - refreshed >= 1:
                self.data.refresh()
                refreshed = time.monotonic()
                dirty = True
            if dirty:
                self.draw(screen)
                dirty = False
            try:
                self.key(screen.get_wch())
                dirty = True
            except curses.error:
                pass


def open_dashboard(runner) -> int:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise ValueError("The dashboard needs an interactive terminal. Use 'python3 -m devloop status' for plain output.")
    locale.setlocale(locale.LC_ALL, "")
    try:
        curses.wrapper(Dashboard(runner).run)
    except KeyboardInterrupt:
        pass
    except curses.error as error:
        raise ValueError(f"Cannot open the terminal dashboard: {error}") from error
    return 0
