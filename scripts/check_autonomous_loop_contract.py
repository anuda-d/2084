#!/usr/bin/env python3
"""Verify the three-slice autonomous development-loop contract."""

from __future__ import annotations

import json
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
        "autonomous development is stopped",
        "Active autonomous goal: none",
        "Owner authorization: none",
        "Scheduler status: paused",
        "legacy authorization is deliberately not imported",
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
    failures: list[str] = []
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"{state_path}: unreadable runtime state: {error}"]

    expected = {
        "schema_version": 2,
        "revision": 0,
        "phase": "stopped",
        "authorization": {"status": "none", "goal_id": None, "source": None},
        "orchestrator": None,
        "slice": None,
        "last_handoff": None,
        "stop_reason": "migration_requires_explicit_owner_activation",
        "events": [],
        "writer_history": [],
    }
    if state != expected:
        failures.append(
            f"{state_path}: migration state must remain stopped and unauthorized"
        )
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
