#!/usr/bin/env python3
"""Check the fresh-task scheduled development-loop contract."""

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATHS = (
    Path("AGENTS.md"),
    Path("docs/main/DEVELOPMENT_LOOP.md"),
    Path("docs/plans/CURRENT.md"),
)
COMMON_REQUIREMENTS = (
    "One implementation task owns at most one work unit",
    "No next unit selected",
    "fresh successor task",
    "autonomous_loop_lock.py acquire",
    "Read-only work does not require checkout ownership",
    "Immediately before the first repository write",
    "Assert ownership after any resumed turn and immediately before commit",
    "Release ownership at completion",
    "recover --expected-task-id",
    "unscoped Codex task listing is not an ownership precondition",
    "Do not call `list_threads` as part of the no-overlap gate",
    "read_thread",
    "gpt-5.6-terra",
    "gpt-5.6-sol",
)
OBSOLETE_RULES = (
    "Continuous Goal",
    "`create_goal`",
    "`get_goal`",
    "`update_goal`",
    "--verified-inactive",
    "Before any subagent spawn or repository change",
    "Before every later repository mutation phase",
    "Ownership is never taken over or force-released",
    "full task-list page",
    "installed `$unlazy`",
)
STATE_FIELDS = (
    "Active goal id",
    "Owner authorization",
    "Authorization scope",
    "Authorization source",
    "Loop cadence",
    "Current run",
    "Incomplete run",
    "Run status",
    "Pending owner decision",
    "Scheduled window",
    "Fresh-task relay",
    "Alignment due",
    "Standing implementation authority",
)


def require_tokens(path: Path, tokens: tuple[str, ...]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [f"{path}: missing {token!r}" for token in tokens if token not in text]


def reject_tokens(path: Path, tokens: tuple[str, ...]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [f"{path}: retained obsolete {token!r}" for token in tokens if token in text]


def ordered_tokens(label: str, text: str, tokens: tuple[str, ...]) -> list[str]:
    failures: list[str] = []
    offset = 0
    for token in tokens:
        position = text.find(token, offset)
        if position < 0:
            failures.append(f"{label}: missing ordered lifecycle token {token!r}")
            continue
        offset = position + len(token)
    return failures


def require_order(path: Path, tokens: tuple[str, ...]) -> list[str]:
    return ordered_tokens(str(path), path.read_text(encoding="utf-8"), tokens)


def require_section_order(
    path: Path,
    heading: str,
    tokens: tuple[str, ...],
) -> list[str]:
    text = path.read_text(encoding="utf-8")
    body = section(text, heading)
    if body is None:
        return [f"{path}: missing section {heading!r}"]
    return ordered_tokens(f"{path} [{heading}]", body, tokens)


def section(text: str, heading: str) -> str | None:
    matches = re.findall(
        rf"(?ms)^## {re.escape(heading)}[ \t]*\n(.*?)(?=^## |\Z)",
        text,
    )
    return matches[0] if len(matches) == 1 else None


def subsection(text: str, heading: str) -> str | None:
    matches = re.findall(
        rf"(?ms)^### {re.escape(heading)}[ \t]*\n(.*?)(?=^### |^## |\Z)",
        text,
    )
    return matches[0] if len(matches) == 1 else None


def fields_from_section(path: Path, heading: str) -> tuple[dict[str, str], list[str]]:
    text = path.read_text(encoding="utf-8")
    body = section(text, heading)
    if body is None:
        return {}, [f"{path}: expected exactly one {heading} section"]

    values: dict[str, str] = {}
    failures: list[str] = []
    for line in body.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"- ([^:]+): (.+)", line)
        if match is None:
            failures.append(f"{path}: unexpected {heading} entry {line!r}")
            continue
        field, value = match.groups()
        if field in values:
            failures.append(f"{path}: duplicate {heading} field {field!r}")
        values[field] = value
    return values, failures


def current_state_failures(root: Path = ROOT) -> list[str]:
    current_path = root / "docs/plans/CURRENT.md"
    current_text = current_path.read_text(encoding="utf-8")
    values, failures = fields_from_section(current_path, "Run State Snapshot")
    for field in STATE_FIELDS:
        if field not in values:
            failures.append(f"{current_path}: missing state field {field!r}")
    for field in values:
        if field not in STATE_FIELDS:
            failures.append(f"{current_path}: unexpected state field {field!r}")
    if failures:
        return failures

    status_lines = re.findall(r"(?m)^Status: .+$", current_text)
    if len(status_lines) != 1:
        failures.append(
            f"{current_path}: expected exactly one top-level Status line"
        )
    active_goals = []
    for candidate in (root / "docs/plans").glob("*/GOAL.md"):
        if re.search(
            r"(?m)^Status: active(?:[;.]|$)",
            candidate.read_text(encoding="utf-8"),
        ):
            active_goals.append(candidate)
    if values["Scheduled window"] != "daily 18:00-23:00 America/Toronto":
        failures.append(f"{current_path}: Scheduled window is invalid")
    if values["Alignment due"] not in {"yes", "no"}:
        failures.append(f"{current_path}: Alignment due must be 'yes' or 'no'")

    active_goal_id = values["Active goal id"]
    if active_goal_id == "none":
        expected = {
            "Owner authorization": "pending",
            "Authorization scope": "none",
            "Authorization source": "none",
            "Loop cadence": "stopped",
            "Current run": "none",
            "Incomplete run": "none",
            "Run status": "none",
            "Pending owner decision": "none",
            "Fresh-task relay": "stopped",
            "Alignment due": "no",
            "Standing implementation authority": "none",
        }
        for field, expected_value in expected.items():
            if values[field] != expected_value:
                failures.append(
                    f"{current_path}: {field} must be {expected_value!r} "
                    "when no goal is active"
                )
        if status_lines != ["Status: no active goal."]:
            failures.append(f"{current_path}: no-goal status is missing")
        if active_goals:
            failures.append(
                f"{current_path}: no-goal state requires zero active goals"
            )
        return failures

    expected_active = {
        "Authorization scope": "active goal",
        "Authorization source": "owner",
    }
    for field, expected_value in expected_active.items():
        if values[field] != expected_value:
            failures.append(
                f"{current_path}: {field} must be {expected_value!r} "
                "when a goal is active"
            )
    owner_authorization = values["Owner authorization"]
    if owner_authorization == "standing":
        if len(status_lines) == 1 and re.fullmatch(
            r"Status: .+ is active under standing scheduled authorization\.",
            status_lines[0],
        ) is None:
            failures.append(f"{current_path}: standing active-goal status is invalid")
        standing_values = {
            "Loop cadence": "scheduled autonomous relay",
            "Fresh-task relay": "active",
            "Standing implementation authority": "active",
        }
        for field, expected_value in standing_values.items():
            if values[field] != expected_value:
                failures.append(
                    f"{current_path}: {field} must be {expected_value!r} "
                    "under standing authorization"
                )
        current_run = values["Current run"]
        if current_run == "none":
            allowed_statuses = {
                "awaiting scheduled fresh task",
                "selecting",
                "alignment",
                "needs owner decision",
            }
        else:
            allowed_statuses = {
                "exploration",
                "implementation",
                "validation",
                "scenario validation",
                "independent review",
                "alignment",
                "blocked",
                "needs owner decision",
            }
        if values["Run status"] not in allowed_statuses:
            failures.append(
                f"{current_path}: Run status is invalid for the current run state"
            )
        alignment_due = values["Alignment due"]
        if alignment_due == "yes":
            expected_alignment_status = (
                "awaiting scheduled fresh task"
                if current_run == "none"
                else "alignment"
            )
            if values["Run status"] != expected_alignment_status:
                failures.append(
                    f"{current_path}: Alignment due must route only to alignment"
                )
        elif values["Run status"] == "alignment":
            failures.append(
                f"{current_path}: alignment run status requires Alignment due: yes"
            )
        pending_decision = values["Pending owner decision"]
        if pending_decision == "none" and values["Run status"] == "needs owner decision":
            failures.append(
                f"{current_path}: needs owner decision status requires a pending decision"
            )
        if pending_decision != "none" and values["Run status"] != "needs owner decision":
            failures.append(
                f"{current_path}: pending owner decision requires matching run status"
            )
    elif owner_authorization == "paused":
        if len(status_lines) == 1 and re.fullmatch(
            r"Status: .+ is active with owner authorization paused\.",
            status_lines[0],
        ) is None:
            failures.append(f"{current_path}: paused active-goal status is invalid")
        paused_values = {
            "Loop cadence": "paused",
            "Fresh-task relay": "paused",
            "Standing implementation authority": "paused",
            "Run status": "paused",
        }
        for field, expected_value in paused_values.items():
            if values[field] != expected_value:
                failures.append(
                    f"{current_path}: {field} must be {expected_value!r} "
                    "while authorization is paused"
                )
    else:
        failures.append(
            f"{current_path}: active goal requires standing or paused owner "
            "authorization"
        )

    current_run = values["Current run"]
    incomplete_run = values["Incomplete run"]
    if current_run != incomplete_run:
        failures.append(f"{current_path}: Current run and Incomplete run disagree")

    goal_links = re.findall(
        r"(?m)^- Goal:[ \t]*(?:\n[ \t]*)?\[[^]]+\]\(([^)\n]+)\)",
        current_text,
    )
    if len(goal_links) != 1:
        failures.append(f"{current_path}: expected exactly one active Goal link")
        return failures
    goal_path = current_path.parent / goal_links[0]
    if not goal_path.is_file():
        failures.append(f"{current_path}: missing linked active goal {goal_path}")
        return failures
    if goal_path.parent.name != active_goal_id:
        failures.append(
            f"{current_path}: Goal link does not match Active goal id "
            f"{active_goal_id!r}"
        )
    goal_text = goal_path.read_text(encoding="utf-8")
    if re.search(
        r"(?m)^Status: active; owner-approved goal(?: .+)?\.$",
        goal_text,
    ) is None:
        failures.append(
            f"{goal_path}: active goal status must record owner approval"
        )

    if active_goals != [goal_path]:
        failures.append(
            f"{current_path}: linked goal must be the only active goal"
        )

    links = re.findall(
        r"(?m)^- Shared implementation state:[ \t]*"
        r"(?:\n[ \t]*)?\[[^]]+\]\(([^)\n]+)\)",
        current_text,
    )
    if len(links) != 1:
        failures.append(
            f"{current_path}: expected exactly one Shared implementation state link"
        )
        return failures

    state_path = current_path.parent / links[0]
    if not state_path.is_file():
        failures.append(f"{current_path}: missing active state {state_path}")
        return failures
    if state_path.parent != goal_path.parent:
        failures.append(
            f"{current_path}: active goal and implementation state must share a directory"
        )
    state_values, state_failures = fields_from_section(state_path, "Run State Snapshot")
    failures.extend(state_failures)
    for field in STATE_FIELDS:
        if state_values.get(field) != values[field]:
            failures.append(f"{state_path}: state field {field!r} is not synchronized")
    return failures


def repository_contract_failures(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    for relative_path in CONTRACT_PATHS:
        path = root / relative_path
        failures.extend(require_tokens(path, COMMON_REQUIREMENTS))
        failures.extend(reject_tokens(path, OBSOLETE_RULES))

    lock_path = root / "scripts/autonomous_loop_lock.py"
    failures.extend(
        require_tokens(
            lock_path,
            (
                "CODEX_THREAD_ID",
                "MISSING_TASK_ID",
                "assert-owner",
                "recover",
                "verified-terminal-state",
                "expected-claim-token",
                "EXPECTED_OWNER_MISMATCH",
                "EXPECTED_CLAIM_TOKEN_MISMATCH",
                "release",
                "HELD_BY",
                "UNREADABLE_LOCK",
            ),
        )
    )
    failures.extend(reject_tokens(lock_path, ("takeover", "verified_inactive")))
    development_loop = root / "docs/main/DEVELOPMENT_LOOP.md"
    failures.extend(
        require_order(
            development_loop,
            (
                "Read-only work does not require checkout ownership.",
                "Immediately before the first repository write",
                "Assert ownership after any resumed turn and immediately before commit",
                "Release ownership at completion",
            ),
        )
    )
    failures.extend(
        require_section_order(
            development_loop,
            "Owner Decision Boundary",
            (
                "write the handoff, release ownership if the",
                "current task owns the record, and do not relay.",
            ),
        )
    )
    failures.extend(
        require_section_order(
            development_loop,
            "Blocked Units",
            (
                "For an unsafe baseline or overlap",
                "release it after writing the\n  blocked handoff and before stopping.",
            ),
        )
    )
    failures.extend(
        require_section_order(
            development_loop,
            "Owner Pause or Stop",
            (
                "write a handoff, and stop.",
                "release it after writing the\nhandoff and before stopping.",
            ),
        )
    )
    failures.extend(
        require_section_order(
            development_loop,
            "Goal Completion",
            (
                "assert checkout ownership and create the final local commit;",
                "write the final handoff using the captured completing goal id;",
                "release checkout ownership;",
            ),
        )
    )
    development_text = development_loop.read_text(encoding="utf-8")
    accept_body = subsection(
        development_text,
        "7. Accept, Commit, Hand Off, Relay, and Stop",
    )
    if accept_body is None:
        failures.append(
            f"{development_loop}: missing accept/commit/relay subsection"
        )
    else:
        failures.extend(
            ordered_tokens(
                f"{development_loop} [Accept, Commit, Hand Off, Relay, and Stop]",
                accept_body,
                (
                    "assert checkout ownership and create one local commit;",
                    "write the temporary handoff with `No next unit selected`;",
                    "assert checkout ownership, release checkout ownership, and enter",
                ),
            )
        )
    failures.extend(current_state_failures(root))
    return failures


def main() -> int:
    failures = repository_contract_failures()
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("fresh-task development loop contract verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
