#!/usr/bin/env python3
"""Check that scheduled-loop ownership cannot be blocked by thread-list pagination."""

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
AUTOMATION = CODEX_HOME / "automations/autonomous-2084-development-loop/automation.toml"


def require_tokens(path: Path, tokens: tuple[str, ...]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [f"{path}: missing {token!r}" for token in tokens if token not in text]


def reject_tokens(path: Path, tokens: tuple[str, ...]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [f"{path}: retained obsolete {token!r}" for token in tokens if token in text]


def main() -> int:
    failures: list[str] = []
    repository_requirements = {
        ROOT / "AGENTS.md": (
            "autonomous_loop_lock.py acquire",
            "full task-list page is not itself terminal",
            "read_thread",
            "--verified-inactive",
            "idle` or `notLoaded",
            "`completed`, `failed`, or `interrupted`",
            "assert-owner --task-id",
        ),
        ROOT / "docs/main/DEVELOPMENT_LOOP.md": (
            "autonomous_loop_lock.py acquire",
            "full task-list page is not itself terminal",
            "read_thread",
            "--verified-inactive",
            "idle` or `notLoaded",
            "`completed`, `failed`, or `interrupted`",
            "assert-owner --task-id",
        ),
        ROOT / "docs/plans/CURRENT.md": (
            "autonomous_loop_lock.py acquire",
            "full task-list page is not itself terminal",
            "assert-owner --task-id",
        ),
    }
    for path, tokens in repository_requirements.items():
        failures.extend(require_tokens(path, tokens))
        failures.extend(reject_tokens(path, ("fewer than 50",)))

    automation_tokens = (
        "autonomous_loop_lock.py acquire",
        "full task-list page is not itself terminal",
        "read_thread",
        "--verified-inactive",
        "idle or notLoaded",
        "completed, failed, or interrupted",
        "assert-owner --task-id",
        "autonomous_loop_lock.py release",
    )
    failures.extend(require_tokens(AUTOMATION, automation_tokens))
    failures.extend(reject_tokens(AUTOMATION, ("fewer than 50",)))

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("autonomous loop contract verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
