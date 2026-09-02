#!/usr/bin/env python3
"""Check that scheduled-loop ownership cannot be blocked by thread-list pagination."""

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
AUTOMATION = CODEX_HOME / "automations/autonomous-2084-development-loop/automation.toml"
GOAL_REQUIREMENTS = (
    "app-level Goal",
    "`create_goal`",
    "`get_goal` again",
    "`get_goal` reports `status: active`",
    "before task listing or lock acquisition",
    "Never claim Continuous Goal mode",
    "Continuous Goal does not use `create_thread`",
    "releasing a lock it owns",
    "**GOAL MODE NOT ACTIVE**",
    "`update_goal` with `status: complete`",
)
GOAL_REJECTIONS = (
    "Continuous Goal may use `create_thread`",
    "`status: paused` is sufficient",
    "an unfinished Goal is sufficient",
)


def require_tokens(path: Path, tokens: tuple[str, ...]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [f"{path}: missing {token!r}" for token in tokens if token not in text]


def reject_tokens(path: Path, tokens: tuple[str, ...]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [f"{path}: retained obsolete {token!r}" for token in tokens if token in text]


def repository_contract_failures(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    repository_requirements = {
        root / "AGENTS.md": GOAL_REQUIREMENTS
        + (
            "autonomous_loop_lock.py acquire",
            "full task-list page is not itself terminal",
            "read_thread",
            "--verified-inactive",
            "idle` or `notLoaded",
            "`completed`, `failed`, or `interrupted`",
            "assert-owner --task-id",
        ),
        root / "docs/main/DEVELOPMENT_LOOP.md": GOAL_REQUIREMENTS
        + (
            "autonomous_loop_lock.py acquire",
            "full task-list page is not itself terminal",
            "read_thread",
            "--verified-inactive",
            "idle` or `notLoaded",
            "`completed`, `failed`, or `interrupted`",
            "assert-owner --task-id",
        ),
        root / "docs/plans/CURRENT.md": GOAL_REQUIREMENTS
        + (
            "autonomous_loop_lock.py acquire",
            "full task-list page is not itself terminal",
            "assert-owner --task-id",
        ),
    }
    for path, tokens in repository_requirements.items():
        failures.extend(require_tokens(path, tokens))
        failures.extend(reject_tokens(path, ("fewer than 50",) + GOAL_REJECTIONS))
    return failures


def main() -> int:
    failures = repository_contract_failures()

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
