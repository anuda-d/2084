"""Project configuration and daily execution windows."""

from __future__ import annotations

import hashlib
import sys
import tomllib
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class Window:
    def __init__(self, values: dict):
        try:
            self.zone = ZoneInfo(values["timezone"])
        except ZoneInfoNotFoundError as error:
            raise ValueError("Install timezone data with: python -m pip install tzdata") from error
        self.start = time.fromisoformat(values["start"])
        self.end = time.fromisoformat(values["end"])
        self.checkpoint = int(values.get("checkpoint_seconds", 120))
        if self.checkpoint < 5:
            raise ValueError("checkpoint_seconds must allow at least five seconds to stop")

    def bounds(self, now: datetime) -> tuple[datetime, datetime]:
        local = now.astimezone(self.zone)
        start = datetime.combine(local.date(), self.start, self.zone)
        end = datetime.combine(local.date(), self.end, self.zone)
        if self.end <= self.start:
            if local.time().replace(tzinfo=None) < self.end:
                start -= timedelta(days=1)
            else:
                end += timedelta(days=1)
        return start, end

    def remaining(self, now: datetime) -> float:
        start, end = self.bounds(now)
        if now.timestamp() < start.timestamp() or now.timestamp() >= end.timestamp():
            return 0
        return end.timestamp() - now.timestamp()


class Config:
    def __init__(self, path: Path):
        self.path = path.resolve()
        self.root = self.path.parent
        self.data = tomllib.loads(self.path.read_text(encoding="utf-8"))
        self.project = self.data["project"]
        self.goal = self._file(self.data["goal"])
        self.skill = self._file(self.data["skill"])
        self.context = [self._file(p) for p in self.data.get("context", [])]
        self.window = Window(self.data["window"])
        self.agent = self.data["agent"]
        self.command = self.agent.get("command", ["codex"])
        self.limits = self.data["limits"]
        self.review = self.data.get("review", {})
        self.evidence = self.data.get("evidence", {})
        for key in ("required_for_completion", "recovery_roots"):
            if not isinstance(self.evidence.get(key, []), list) or not all(
                    isinstance(x, str) and x for x in self.evidence.get(key, [])):
                raise ValueError(f"evidence.{key} must be a list of strings")
        if self.evidence:
            directory = self.evidence.get("directory")
            if not isinstance(directory, str) or not Path(directory).expanduser().is_absolute():
                raise ValueError("Evidence directory must be an absolute path")
            if Path(directory).expanduser().resolve().is_relative_to(self.root):
                raise ValueError("Evidence directory must be outside the checkout")
        legacy = self.evidence.get("legacy", {})
        if not isinstance(legacy, dict) or not all(isinstance(k, str) and isinstance(v, str)
                and Path(v).expanduser().is_absolute() for k, v in legacy.items()):
            raise ValueError("Legacy evidence must map identifiers to absolute paths")
        if not isinstance(self.review.get("completion_paths", []), list) or not all(
                isinstance(x, str) and x and not Path(x).is_absolute() and ".." not in Path(x).parts
                and not any(c in x for c in "*?[") for x in self.review.get("completion_paths", [])):
            raise ValueError("Completion review paths must be explicit repository-relative files")
        self.checks = self.data["validation"]["commands"]
        for command in [self.command, *self.checks]:
            if not isinstance(command, list) or not command or not all(isinstance(x, str) for x in command):
                raise ValueError("Commands must be nonempty argument arrays")
        if not self.checks:
            raise ValueError("At least one deterministic validation command is required")
        for key in ("turn_seconds", "failed_attempts", "retry_seconds"):
            if self.limits[key] <= 0:
                raise ValueError(f"{key} must be positive")
        if self.agent.get("sandbox") not in {"workspace-write", "read-only"}:
            raise ValueError("Use a bounded Codex sandbox")

    def _file(self, value: str) -> Path:
        path = (self.root / value).resolve()
        if not path.is_relative_to(self.root) or not path.is_file():
            raise ValueError(f"Missing or out-of-repository context: {value}")
        return path

    def identity(self) -> str:
        return hashlib.sha256(self.path.read_bytes() + b"\0" + self.goal.read_bytes()).hexdigest()

    def check_commands(self) -> list[list[str]]:
        return [[sys.executable if arg == "{python}" else arg for arg in cmd] for cmd in self.checks]
