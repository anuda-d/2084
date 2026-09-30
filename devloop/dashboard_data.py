"""Bounded, read-only views of runner state, execution logs, and Git changes."""

from __future__ import annotations

import json
import re
import subprocess
import time
import unicodedata
from pathlib import Path

from .runtime import process_alive

ANSI = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\))")
Row = tuple[str, str]


def clean(value: object) -> str:
    text = ANSI.sub("", str(value)).expandtabs(4)
    return "".join(c for c in text if c == "\n" or c.isprintable())


def cells(text: str) -> int:
    return sum(0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def wrap(text: str, width: int) -> list[str]:
    """Wrap by terminal cells, including long commands and wide Unicode text."""
    lines = []
    for paragraph in clean(text).split("\n"):
        line = ""
        for word in paragraph.split(" "):
            prefix = " " if line else ""
            if cells(line + prefix + word) <= width:
                line += prefix + word
                continue
            if line:
                lines.append(line)
                line = ""
            for char in word:
                if cells(line + char) > width and line:
                    lines.append(line)
                    line = ""
                line += char
        lines.append(line)
    return lines


def section(title: str, text: object, tone: str = "normal") -> list[Row]:
    return [(title.upper(), "accent"), (clean(text) or "Nothing recorded yet.", tone), ("", "normal")]


def event_rows(record: dict) -> list[Row]:
    kind = record.get("type", "")
    if kind in {"execution.started", "execution.finished"}:
        text = f"{record.get('phase', '')}: "
        text += (f"{record.get('elapsed_seconds', 0):.1f}s session elapsed; {record.get('stop_reason', '')}"
                 if kind == "execution.finished" else "started")
        return section("execution timing", text)
    item = record.get("item", {})
    if not isinstance(item, dict):
        return []
    if kind == "thread.started":
        return [("SESSION  " + str(record.get("thread_id", "")), "muted")]
    if kind in {"error", "turn.failed"}:
        return section("error", record.get("message") or record.get("error"), "error")
    if kind == "turn.completed":
        return [("TURN FINISHED", "good"), ("", "normal")]
    if kind not in {"item.started", "item.completed"}:
        return []
    item_type = item.get("type")
    if item_type == "agent_message" and kind == "item.completed":
        text = item.get("text", "")
        try:
            result = json.loads(text)
        except (ValueError, TypeError):
            result = None
        if isinstance(result, dict) and "summary" in result:
            rows = section("agent / " + str(result.get("outcome", "result")), result["summary"])
            for key in ("evidence", "remaining"):
                if result.get(key):
                    rows += section(key, result[key])
            return rows
        return section("agent", text)
    if item_type == "command_execution":
        if kind == "item.started":
            return section("running", item.get("command", ""), "muted")
        code = item.get("exit_code")
        rows = section(f"command / exit {code}", item.get("command", ""), "good" if code == 0 else "error")
        output = clean(item.get("aggregated_output", ""))
        if output:
            lines = output.splitlines()
            if len(lines) > 35:
                rows.append(("[output shortened; showing the last 35 lines]", "muted"))
            rows += [(line[:4000], "normal") for line in lines[-35:]] + [("", "normal")]
        return rows
    if item_type == "file_change" and kind == "item.completed":
        return section("files changed", "\n".join(str(change.get("path", "")) for change in item.get("changes", []) if isinstance(change, dict)))
    if item_type == "mcp_tool_call":
        return [(f"TOOL  {item.get('server', '')} / {item.get('tool', '')}  {item.get('status', '')}", "muted")]
    return []


class DashboardData:
    def __init__(self, runner):
        self.runner = runner
        self.state = {}
        self.error = ""
        self.logs: list[Path] = []
        self.selected_log: Path | None = None  # None follows the newest execution.
        self._log_key = None
        self._log_rows: list[Row] = []
        self._git_at = 0.0
        self._git_rows: list[Row] = []
        self._evidence_at = 0.0
        self._evidence_status = {}

    def refresh(self):
        try:
            self.state = self.runner.store.read()
            if not self._evidence_status or time.monotonic() - self._evidence_at >= 5:
                self._evidence_status = self.runner.evidence.report()
                self._evidence_at = time.monotonic()
            self.state["evidence_status"] = self._evidence_status
            self.error = ""
            folder = self.runner.store.directory / "runs"
            self.logs = sorted((p for p in folder.glob("*.jsonl") if p.is_file()),
                               key=lambda p: p.stat().st_mtime, reverse=True)
        except (OSError, ValueError) as error:
            self.error = str(error)

    def status(self) -> tuple[str, str]:
        state = self.state
        if self.error:
            return "READ ERROR", "error"
        if not state.get("enabled"):
            return ("PAUSING", "warning") if process_alive(state.get("child_pid")) else ("PAUSED", "warning")
        if state.get("phase") in {"blocked", "complete"}:
            return ("BLOCKED", "error") if state["phase"] == "blocked" else ("COMPLETE", "good")
        if not process_alive(state.get("runner_pid")):
            return "SERVICE OFFLINE", "error"
        if self.runner.config.window.remaining(self.runner.clock()) <= self.runner.config.window.checkpoint:
            return "WAITING FOR WINDOW", "muted"
        if state.get("retry_after", 0) > time.time():
            return "RETRY WAIT", "warning"
        return str(state.get("phase", "ready")).upper(), "accent"

    def choose_log(self, direction: int):
        if self.logs:
            index = self.logs.index(self.selected_log) if self.selected_log in self.logs else 0
            index = min(len(self.logs) - 1, max(0, index + direction))
            self.selected_log = self.logs[index] if index else None

    def log_path(self) -> Path | None:
        return self.selected_log or (self.logs[0] if self.logs else None)

    def activity(self) -> list[Row]:
        path = self.log_path()
        if path is None:
            return section("No activity yet", "Execution output will appear here when the runner starts work.")
        try:
            if not path.resolve().is_relative_to((self.runner.store.directory / "runs").resolve()):
                raise ValueError("Log is outside the runner's execution directory")
            stat = path.stat()
            key = (path, stat.st_mtime_ns, stat.st_size)
            if key == self._log_key:
                return self._log_rows
            with path.open("rb") as stream:
                stream.seek(max(0, stat.st_size - 131072))
                raw = stream.read(131072)
            if stat.st_size > 131072:
                raw = raw.partition(b"\n")[2]
            rows: list[Row] = []
            for line in raw.decode("utf-8", errors="replace").splitlines(keepends=True):
                if not line.endswith("\n"):
                    continue  # The writer may be halfway through a JSON event.
                try:
                    record = json.loads(line)
                except ValueError:
                    rows.append((clean(line.rstrip())[:4000], "normal"))
                else:
                    if isinstance(record, dict):
                        rows += event_rows(record)
            self._log_key = key
            self._log_rows = rows[-2000:] or [("Waiting for execution output...", "muted")]
            return self._log_rows
        except (OSError, ValueError) as error:
            return section("Log unavailable", error, "error")

    def changes(self) -> list[Row]:
        if time.monotonic() - self._git_at < 3:
            return self._git_rows
        rows = []
        for title, args, empty in (
            ("Working tree", ["status", "--short"], "Clean. No uncommitted changes."),
            ("Uncommitted tracked diff", ["diff", "--no-ext-diff", "--no-textconv", "HEAD"], "No tracked edits. New files are listed above."),
            ("Recent commits", ["log", "-6", "--format=%h  %s"], "No commits recorded."),
        ):
            try:
                result = subprocess.run(["git", "--no-pager", *args], cwd=self.runner.root,
                                        capture_output=True, text=True, errors="replace", timeout=2,
                                        env={**self.runner.env, "GIT_OPTIONAL_LOCKS": "0"})
                output = result.stdout if result.returncode == 0 else result.stderr
                text = output[:50000] + ("\n[diff shortened]" if len(output) > 50000 else "")
                rows += section(title, text or empty)
            except (OSError, subprocess.TimeoutExpired) as error:
                rows += section(title, error, "error")
        self._git_at, self._git_rows = time.monotonic(), rows
        return rows

    def checks(self) -> list[Row]:
        state = self.state
        rows = section("Latest recorded validation", "No completed checks recorded yet.") if not state.get("checks") else []
        for check in state.get("checks", []):
            rows += section("pass" if check.get("exit_code") == 0 else "fail", " ".join(check.get("command", [])))
            rows += [(str(check.get("log", "")), "muted"), ("", "normal")]
        review = state.get("review")
        rows += section("Latest recorded review", (review.get("verdict", "") + "\n" + review.get("findings", "")) if review else "No independent review recorded.")
        rows += section("Current feedback", state.get("feedback") or "No failures reported.")
        return rows

    def details(self) -> list[Row]:
        state = self.state
        rows = []
        rows += section("Historical goal status", state.get("phase", "unknown"))
        evidence = state.get("evidence_status", {})
        rows += section("Evidence availability", evidence.get("summary", "Not checked"))
        for artifact in evidence.get("artifacts", []):
            rows += section(artifact["id"], f"{artifact['availability']}: {artifact.get('path', 'not registered')}")
        execution = state.get("execution")
        if execution:
            elapsed = (execution.get("elapsed_seconds", 0) if execution.get("finished_at") is not None
                       else max(0, time.time() - execution["started_at"]))
            rows += section("Session elapsed", f"{elapsed:.1f}s; {execution.get('stop_reason') or 'running'}")
            rows += section("Last output timestamp", execution.get("last_output_at") or "No output recorded")
        for title, key in (("Latest result", "summary"), ("Remaining work", "remaining"),
                           ("Last accepted evidence", "evidence"), ("Stop reason", "reason")):
            rows += section(title, state.get(key, ""))
        for title, value in (("Goal", self.runner.config.goal), ("Checkout", self.runner.root),
                             ("Session", state.get("session_id", "Not started")),
                             ("Ollama endpoint (configured, not a health check)", self.runner.env.get("OLLAMA_BASE_URL", "Not configured")),
                             ("Runtime state", self.runner.store.path)):
            rows += section(title, value, "muted")
        return rows
