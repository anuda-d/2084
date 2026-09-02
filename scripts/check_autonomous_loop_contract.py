#!/usr/bin/env python3
"""Check durable ownership and continuation rules for the development loop."""

import os
import re
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
    "same task continues automatically across turns",
    "must not direct continuation to a new agent, task, chat, or handoff",
    "must not release the repository lock between work units",
    "`clear` the conflicting Goal",
)
GOAL_REJECTIONS = (
    "Continuous Goal may use `create_thread`",
    "`status: paused` is sufficient",
    "an unfinished Goal is sufficient",
)
CONTINUOUS_TRANSFER_PATTERNS = (
    re.compile(
        r"\b(?:a|the) (?:new|fresh|successor|different|another) "
        r"(?:agent|task|chat) (?:will |must |should |may |can )?"
        r"(?:continue|resume|start|take(?:s)? over)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:continue|resume|start) (?:work )?(?:in|with) (?:a )?"
        r"(?:new|fresh|another|different) (?:agent|task|chat)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:handoff|transfer|relay) (?:to )?(?:a )?"
        r"(?:new|fresh|successor|different|another) (?:agent|task|chat)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\brelease(?:s|d|ing)? (?:the )?(?:repository )?lock "
        r"(?:after|between|for) (?:each |every |a |the )?"
        r"(?:committed )?work unit\b",
        re.IGNORECASE,
    ),
)
RUN_STATE_FIELDS = (
    "Incomplete run",
    "Last completed run",
    "Verified implementation runs since alignment",
    "Alignment due",
)
CONTINUOUS_SECTION_BOUNDS = {
    "AGENTS.md": (
        "- Continuous Goal mode requires a real app-level Goal",
        "- Every scheduled task and manual one-shot",
    ),
    "docs/main/DEVELOPMENT_LOOP.md": (
        "### Continuous Goal",
        "### Scheduled relay or manual one-shot",
    ),
    "docs/plans/CURRENT.md": (
        "- Continuous Goal requires a real app-level Goal",
        "- Confirm the no-overlap gate before repository work.",
    ),
}


def require_tokens(path: Path, tokens: tuple[str, ...]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [f"{path}: missing {token!r}" for token in tokens if token not in text]


def reject_tokens(path: Path, tokens: tuple[str, ...]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [f"{path}: retained obsolete {token!r}" for token in tokens if token in text]


def continuous_transfer_failures(path: Path, root: Path = ROOT) -> list[str]:
    relative_path = path.relative_to(root).as_posix()
    bounds = CONTINUOUS_SECTION_BOUNDS.get(relative_path)
    if bounds is None:
        return [f"{path}: no Continuous Goal section boundary is configured"]

    text = path.read_text(encoding="utf-8")
    start_marker, end_marker = bounds
    start = text.find(start_marker)
    end = text.find(end_marker, start + len(start_marker)) if start >= 0 else -1
    if start < 0 or end < 0:
        return [f"{path}: could not isolate the Continuous Goal section"]

    section = re.sub(r"\s+", " ", text[start:end])
    return [
        f"{path}: Continuous Goal section contains transfer rule {match.group(0)!r}"
        for pattern in CONTINUOUS_TRANSFER_PATTERNS
        if (match := pattern.search(section)) is not None
    ]


def active_implementation_state_path(root: Path = ROOT) -> Path | None:
    current_path = root / "docs/plans/CURRENT.md"
    current_text = current_path.read_text(encoding="utf-8")
    implementation_links = re.findall(
        r"(?m)^- Shared implementation state:[ \t]*"
        r"(?:\n[ \t]*)?\[[^]]+\]\(([^)\n]+)\)",
        current_text,
    )
    if len(implementation_links) != 1:
        return None
    return current_path.parent / implementation_links[0]


def active_implementation_state_failures(root: Path = ROOT) -> list[str]:
    current_path = root / "docs/plans/CURRENT.md"
    current_text = current_path.read_text(encoding="utf-8")
    implementation_links = re.findall(
        r"(?m)^- Shared implementation state:[ \t]*"
        r"(?:\n[ \t]*)?\[[^]]+\]\(([^)\n]+)\)",
        current_text,
    )
    if len(implementation_links) != 1:
        return [
            f"{current_path}: expected exactly one Shared implementation state link"
        ]

    implementation_path = active_implementation_state_path(root)
    assert implementation_path is not None
    if not implementation_path.is_file():
        return [
            f"{current_path}: missing active implementation state "
            f"{implementation_path}"
        ]
    text = implementation_path.read_text(encoding="utf-8")
    sections = re.findall(
        r"(?ms)^## Run State[ \t]*\n(.*?)(?=^## |\Z)",
        text,
    )
    if len(sections) != 1:
        return [f"{implementation_path}: expected exactly one Run State section"]

    entries = [line for line in sections[0].splitlines() if line.strip()]
    fields: list[str] = []
    failures: list[str] = []
    for entry in entries:
        match = re.fullmatch(r"- ([^:]+):(?: .*)?", entry)
        if match is None:
            failures.append(
                f"{implementation_path}: unexpected Run State entry {entry!r}"
            )
            continue
        field = match.group(1)
        fields.append(field)
        if field not in RUN_STATE_FIELDS:
            failures.append(
                f"{implementation_path}: unexpected Run State field {field!r}"
            )
    for field in RUN_STATE_FIELDS:
        count = fields.count(field)
        if count != 1:
            failures.append(
                f"{implementation_path}: expected one Run State field "
                f"{field!r}, found {count}"
            )
    return failures


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
        failures.extend(continuous_transfer_failures(path, root))

    failures.extend(active_implementation_state_failures(root))
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
