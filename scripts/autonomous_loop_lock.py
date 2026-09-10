#!/usr/bin/env python3
"""Durable single-writer ownership for the 2084 development checkout."""

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import secrets
import sys
import tempfile
import time
from pathlib import Path
from typing import Iterator


TERMINAL_TASK_STATES = ("completed", "failed", "interrupted")


def default_lock_path() -> Path:
    repository = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256(str(repository).encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"2084-autonomous-loop-{digest}.json"


@contextlib.contextmanager
def guarded(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    guard_path = path.with_suffix(path.suffix + ".guard")
    with guard_path.open("a+", encoding="utf-8") as guard:
        fcntl.flock(guard.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(guard.fileno(), fcntl.LOCK_UN)


def read_owner(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"UNREADABLE_LOCK {path}: {error}") from error
    if (
        not isinstance(record, dict)
        or not isinstance(record.get("task_id"), str)
        or not record["task_id"].strip()
    ):
        raise ValueError(f"UNREADABLE_LOCK {path}: missing task_id")
    role = record.get("role", "orchestrator")
    if role not in {"orchestrator", "writer"}:
        raise ValueError(f"UNREADABLE_LOCK {path}: invalid role")
    generation_id = record.get("generation_id")
    slice_id = record.get("slice_id")
    if generation_id is not None and (
        not isinstance(generation_id, str) or not generation_id.strip()
    ):
        raise ValueError(f"UNREADABLE_LOCK {path}: invalid generation_id")
    if slice_id is not None and (not isinstance(slice_id, str) or not slice_id.strip()):
        raise ValueError(f"UNREADABLE_LOCK {path}: invalid slice_id")
    if role == "writer" and generation_id is not None and slice_id is None:
        raise ValueError(f"UNREADABLE_LOCK {path}: scoped writer missing slice_id")
    if role == "orchestrator" and slice_id is not None:
        raise ValueError(f"UNREADABLE_LOCK {path}: orchestrator has slice_id")
    return record


def write_owner(
    path: Path,
    task_id: str,
    *,
    role: str = "orchestrator",
    generation_id: str | None = None,
    slice_id: str | None = None,
    recovered_from: str | None = None,
    verified_terminal_state: str | None = None,
) -> None:
    record = {
        "task_id": task_id,
        "role": role,
        "claimed_at": int(time.time()),
        "claim_token": secrets.token_hex(16),
    }
    if generation_id is not None:
        record["generation_id"] = generation_id
    if slice_id is not None:
        record["slice_id"] = slice_id
    if recovered_from is not None:
        record["recovered_from"] = recovered_from
        record["verified_terminal_state"] = verified_terminal_state
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def write_record(path: Path, record: dict[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def recorded_task_id(record: dict[str, object]) -> str:
    return str(record["task_id"])


def recorded_claim_token(record: dict[str, object]) -> str:
    token = record.get("claim_token")
    if "claim_token" in record:
        if isinstance(token, str) and token.strip():
            return token
        raise ValueError("UNREADABLE_LOCK invalid claim token")
    claimed_at = record.get("claimed_at")
    if isinstance(claimed_at, int) and not isinstance(claimed_at, bool):
        return f"legacy:{claimed_at}"
    raise ValueError("UNREADABLE_LOCK missing claim token")


def current_task_id(explicit_task_id: str | None) -> str:
    task_id = explicit_task_id or os.environ.get("CODEX_THREAD_ID", "")
    if not task_id.strip():
        raise ValueError("MISSING_TASK_ID pass --task-id or set CODEX_THREAD_ID")
    return task_id.strip()


def acquire(
    path: Path,
    task_id: str,
    role: str,
    generation_id: str | None,
    slice_id: str | None,
) -> int:
    if role == "writer" and slice_id is None:
        print("ACQUIRE_WRITER_REQUIRES_SLICE", file=sys.stderr)
        return 2
    if role == "orchestrator" and slice_id is not None:
        print("ACQUIRE_ORCHESTRATOR_REJECTS_SLICE", file=sys.stderr)
        return 2
    if slice_id is not None and generation_id is None:
        print("ACQUIRE_SLICE_REQUIRES_GENERATION", file=sys.stderr)
        return 2
    with guarded(path):
        owner = read_owner(path)
        if owner is not None:
            print(
                f"HELD_BY {recorded_task_id(owner)} {recorded_claim_token(owner)}",
                file=sys.stderr,
            )
            return 1
        write_owner(
            path,
            task_id,
            role=role,
            generation_id=generation_id,
            slice_id=slice_id,
        )
    print(f"ACQUIRED {task_id}")
    return 0


def status(path: Path) -> int:
    with guarded(path):
        owner = read_owner(path)
    if owner is None:
        print("UNLOCKED")
    else:
        print(f"HELD {recorded_task_id(owner)} {recorded_claim_token(owner)}")
    return 0


def assert_owner(path: Path, task_id: str) -> int:
    with guarded(path):
        owner = read_owner(path)
        if owner is None:
            print("NO_OWNER", file=sys.stderr)
            return 1
        if recorded_task_id(owner) != task_id:
            print(f"OWNER_MISMATCH {recorded_task_id(owner)}", file=sys.stderr)
            return 1
        updated = dict(owner)
        updated["claim_token"] = secrets.token_hex(16)
        write_record(path, updated)
        claim_token = str(updated["claim_token"])
    print(f"OWNERSHIP_CONFIRMED {task_id} {claim_token}")
    return 0


def recover(
    path: Path,
    task_id: str,
    expected_task_id: str,
    expected_claim_token: str,
    verified_terminal_state: str,
) -> int:
    with guarded(path):
        owner = read_owner(path)
        if owner is None:
            print("NO_OWNER", file=sys.stderr)
            return 1
        recorded_owner = recorded_task_id(owner)
        if recorded_owner != expected_task_id:
            print(f"EXPECTED_OWNER_MISMATCH {recorded_owner}", file=sys.stderr)
            return 1
        recorded_token = recorded_claim_token(owner)
        if recorded_token != expected_claim_token:
            print(
                f"EXPECTED_CLAIM_TOKEN_MISMATCH {recorded_token}",
                file=sys.stderr,
            )
            return 1
        if recorded_owner == task_id:
            print("RECOVERY_OWNER_UNCHANGED", file=sys.stderr)
            return 1
        write_owner(
            path,
            task_id,
            role=str(owner.get("role", "orchestrator")),
            generation_id=(
                str(owner["generation_id"])
                if owner.get("generation_id") is not None
                else None
            ),
            slice_id=(
                str(owner["slice_id"])
                if owner.get("slice_id") is not None
                else None
            ),
            recovered_from=recorded_owner,
            verified_terminal_state=verified_terminal_state,
        )
    print(f"RECOVERED {recorded_owner} {task_id} {verified_terminal_state}")
    return 0


def transfer(
    path: Path,
    task_id: str,
    to_task_id: str,
    to_role: str,
    generation_id: str,
    slice_id: str | None,
) -> int:
    if task_id == to_task_id:
        print("TRANSFER_OWNER_UNCHANGED", file=sys.stderr)
        return 1
    if to_role == "writer" and slice_id is None:
        print("TRANSFER_WRITER_REQUIRES_SLICE", file=sys.stderr)
        return 2
    if to_role == "orchestrator" and slice_id is not None:
        print("TRANSFER_ORCHESTRATOR_REJECTS_SLICE", file=sys.stderr)
        return 2
    with guarded(path):
        owner = read_owner(path)
        if owner is None:
            print("NO_OWNER", file=sys.stderr)
            return 1
        if recorded_task_id(owner) != task_id:
            print(f"OWNER_MISMATCH {recorded_task_id(owner)}", file=sys.stderr)
            return 1
        recorded_generation = owner.get("generation_id")
        if recorded_generation is not None and recorded_generation != generation_id:
            print(f"GENERATION_MISMATCH {recorded_generation}", file=sys.stderr)
            return 1
        write_owner(
            path,
            to_task_id,
            role=to_role,
            generation_id=generation_id,
            slice_id=slice_id,
        )
    print(f"TRANSFERRED {task_id} {to_task_id} {to_role}")
    return 0


def release(path: Path, task_id: str) -> int:
    with guarded(path):
        owner = read_owner(path)
        if owner is None:
            print("NO_OWNER", file=sys.stderr)
            return 1
        if recorded_task_id(owner) != task_id:
            print(f"OWNER_MISMATCH {recorded_task_id(owner)}", file=sys.stderr)
            return 1
        path.unlink()
    print(f"RELEASED {task_id}")
    return 0


def add_current_task_argument(command: argparse.ArgumentParser) -> None:
    command.add_argument(
        "--task-id",
        help="Codex task ID; defaults to CODEX_THREAD_ID",
    )


def add_scope_arguments(command: argparse.ArgumentParser) -> None:
    command.add_argument(
        "--role",
        choices=("orchestrator", "writer"),
        default="orchestrator",
    )
    command.add_argument("--generation-id")
    command.add_argument("--slice-id")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=default_lock_path())
    commands = parser.add_subparsers(dest="command", required=True)

    acquire_command = commands.add_parser("acquire")
    add_current_task_argument(acquire_command)
    add_scope_arguments(acquire_command)

    for name in ("assert-owner", "release"):
        add_current_task_argument(commands.add_parser(name))

    recover_command = commands.add_parser("recover")
    add_current_task_argument(recover_command)
    recover_command.add_argument("--expected-task-id", required=True)
    recover_command.add_argument("--expected-claim-token", required=True)
    recover_command.add_argument(
        "--verified-terminal-state",
        required=True,
        choices=TERMINAL_TASK_STATES,
        help="Terminal latest-turn state verified with read_thread",
    )

    transfer_command = commands.add_parser("transfer")
    add_current_task_argument(transfer_command)
    transfer_command.add_argument("--to-task-id", required=True)
    transfer_command.add_argument(
        "--to-role",
        required=True,
        choices=("orchestrator", "writer"),
    )
    transfer_command.add_argument("--generation-id", required=True)
    transfer_command.add_argument("--slice-id")

    commands.add_parser("status")
    return parser


def main(arguments: list[str] | None = None) -> int:
    args = build_parser().parse_args(arguments)
    try:
        if args.command == "status":
            return status(args.path)
        task_id = current_task_id(args.task_id)
        if args.command == "acquire":
            return acquire(
                args.path,
                task_id,
                args.role,
                args.generation_id,
                args.slice_id,
            )
        if args.command == "assert-owner":
            return assert_owner(args.path, task_id)
        if args.command == "recover":
            return recover(
                args.path,
                task_id,
                args.expected_task_id,
                args.expected_claim_token,
                args.verified_terminal_state,
            )
        if args.command == "transfer":
            return transfer(
                args.path,
                task_id,
                args.to_task_id,
                args.to_role,
                args.generation_id,
                args.slice_id,
            )
        return release(args.path, task_id)
    except (OSError, ValueError) as error:
        print(f"LOCK_ERROR {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
