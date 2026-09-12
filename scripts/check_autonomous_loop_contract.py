#!/usr/bin/env python3
"""Verify the three-slice autonomous development-loop contract."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURRENT_PATHS = (
    Path("AGENTS.md"),
    Path("docs/main/DEVELOPMENT_LOOP.md"),
    Path("docs/main/AUTONOMOUS_LOOP_AUTOMATION_PROMPT.md"),
    Path("docs/plans/CURRENT.md"),
)
REQUIRED_BY_PATH = {
    Path("AGENTS.md"): (
        "authoritative runtime",
        "liveness and recovery trigger",
        "at most three sequential accepted",
        "fresh writer",
        "sole repository modifier",
        "fresh read-only",
        "recover it exactly",
    ),
    Path("docs/main/DEVELOPMENT_LOOP.md"): (
        "Runtime State Machine",
        "expected revision",
        "unique event identifier",
        "frozen slice contract",
        "at most three slices",
        "sole repository modifier",
        "two repair cycles",
        "three writer attempts",
        "whole-goal alignment",
        "fresh orchestrator",
        "saved automation was paused",
        "exact current `HEAD`",
    ),
    Path("docs/main/AUTONOMOUS_LOOP_AUTOMATION_PROMPT.md"): (
        "liveness and recovery trigger only",
        "state is stopped or unauthorized",
        "Do not select product work",
        "recover-actor",
        "three sequential accepted slices",
        "one fresh writer",
        "sole repository modifier",
        "whole-goal alignment",
    ),
    Path("docs/plans/CURRENT.md"): (
        "Authoritative state",
        "Active autonomous goal",
        "Owner authorization",
        "Scheduler status",
        "one fresh writer",
        "three sequential accepted slices",
    ),
}
OBSOLETE_CURRENT_RULES = (
    "One implementation task owns at most one work unit",
    "Every implementation unit begins in a newly created fresh task",
    "fresh successor task",
    "Current run",
    "Incomplete run",
    "Alignment due",
    "scheduled autonomous relay",
)


def require_tokens(path: Path, tokens: tuple[str, ...]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [f"{path}: missing {token!r}" for token in tokens if token not in text]


def reject_tokens(path: Path, tokens: tuple[str, ...]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [f"{path}: retained obsolete {token!r}" for token in tokens if token in text]


def state_failures(root: Path = ROOT) -> list[str]:
    state_path = root / "docs/plans/AUTONOMOUS_LOOP_STATE.json"
    try:
        json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"{state_path}: unreadable runtime state: {error}"]
    validator = root / "scripts/autonomous_loop_state.py"
    result = subprocess.run(
        [
            sys.executable,
            str(validator),
            "--state-path",
            str(state_path),
            "validate",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return []
    detail = result.stderr.strip() or result.stdout.strip() or "validation failed"
    return [f"{state_path}: {detail}"]


def current_summary_failures(root: Path = ROOT) -> list[str]:
    state_path = root / "docs/plans/AUTONOMOUS_LOOP_STATE.json"
    current_path = root / "docs/plans/CURRENT.md"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        current = current_path.read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError) as error:
        return [f"runtime summary unreadable: {error}"]

    def field(label: str) -> str | None:
        prefix = f"- {label}:"
        for line in current.splitlines():
            if line.startswith(prefix):
                return line[len(prefix) :].strip()
        return None

    failures: list[str] = []

    def fail(label: str) -> None:
        if label not in failures:
            failures.append(label)

    status_line = next(
        (line for line in current.splitlines() if line.startswith("Status:")),
        None,
    )
    goal_summary = field("Active autonomous goal")
    authorization_summary = field("Owner authorization")
    scheduler_summary = field("Scheduler status")
    authorization = state.get("authorization", {})
    if authorization.get("status") == "standing":
        goal_id = authorization.get("goal_id")
        if (
            not isinstance(goal_id, str)
            or goal_summary is None
            or goal_summary == "none"
            or goal_id not in goal_summary
        ):
            fail("CURRENT_GOAL_MISMATCH")
        if authorization_summary is None or not authorization_summary.startswith(
            "standing"
        ):
            fail("CURRENT_AUTHORIZATION_MISMATCH")
        if scheduler_summary not in {
            "active",
            "pending activation after the repository activation commit",
        }:
            fail("CURRENT_SCHEDULER_MISMATCH")
        if status_line is None or "stopped" in status_line:
            fail("CURRENT_PHASE_MISMATCH")
    elif authorization.get("status") == "none":
        if goal_summary != "none":
            fail("CURRENT_GOAL_MISMATCH")
        if authorization_summary != "none":
            fail("CURRENT_AUTHORIZATION_MISMATCH")
        if scheduler_summary != "paused":
            fail("CURRENT_SCHEDULER_MISMATCH")
        if status_line is None or "autonomous development is stopped" not in status_line:
            fail("CURRENT_PHASE_MISMATCH")

    orchestrator = state.get("orchestrator")
    orchestrator_summary = field("Current orchestrator")
    if orchestrator is None:
        if orchestrator_summary != "none":
            fail("CURRENT_ORCHESTRATOR_MISMATCH")
    else:
        for key in ("generation_id", "task_id"):
            value = orchestrator.get(key)
            if (
                not isinstance(value, str)
                or orchestrator_summary is None
                or value not in orchestrator_summary
            ):
                fail("CURRENT_ORCHESTRATOR_MISMATCH")
                break

    active_slice = state.get("slice")
    slice_summary = field("Current slice")
    if active_slice is None:
        if slice_summary != "none":
            fail("CURRENT_SLICE_MISMATCH")
    else:
        slice_id = active_slice.get("slice_id")
        if (
            not isinstance(slice_id, str)
            or slice_summary is None
            or slice_id not in slice_summary
        ):
            fail("CURRENT_SLICE_MISMATCH")
    return failures


def repository_contract_failures(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    for relative_path in CURRENT_PATHS:
        path = root / relative_path
        if not path.is_file():
            failures.append(f"{path}: missing current loop document")
            continue
        failures.extend(require_tokens(path, REQUIRED_BY_PATH[relative_path]))
        failures.extend(reject_tokens(path, OBSOLETE_CURRENT_RULES))

    state_script = root / "scripts/autonomous_loop_state.py"
    failures.extend(
        require_tokens(
            state_script,
            (
                "MAX_ACCEPTED_SLICES = 3",
                "MAX_REPAIRS = 2",
                "expected_revision",
                "EVENT_ID_REUSED",
                "CONTRACT_DIGEST_MISMATCH",
                "REVIEWER_MUST_BE_FRESH_READ_ONLY_TASK",
                "alignment_required",
                "recover_actor",
                "ACCEPTED_COMMIT_IS_NOT_CURRENT_HEAD",
            ),
        )
    )
    lock_script = root / "scripts/autonomous_loop_lock.py"
    failures.extend(
        require_tokens(
            lock_script,
            (
                "CODEX_THREAD_ID",
                "expected-claim-token",
                "verified-terminal-state",
                "claim_token",
                "transfer",
                "to-role",
                "generation-id",
                "slice-id",
            ),
        )
    )
    failures.extend(state_failures(root))
    failures.extend(current_summary_failures(root))
    return failures


def main() -> int:
    failures = repository_contract_failures()
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("three-slice autonomous loop contract verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
