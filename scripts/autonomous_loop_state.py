#!/usr/bin/env python3
"""Guarded state transitions for the goal-bounded autonomous loop."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Iterator

from autonomous_loop_lock import default_lock_path, read_owner, recorded_task_id


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE_PATH = ROOT / "docs/plans/AUTONOMOUS_LOOP_STATE.json"
SCHEMA_VERSION = 2
MAX_ACCEPTED_SLICES = 3
MAX_REPAIRS = 2
TERMINAL_TASK_STATES = {"completed", "failed", "interrupted"}
ACTIVE_SLICE_PHASES = {
    "contracted",
    "implementing",
    "validating",
    "reviewing",
    "repairing",
}
TERMINAL_SLICE_PHASES = {"blocked", "needs_owner_decision"}
PHASES = {
    "stopped",
    "ready",
    *ACTIVE_SLICE_PHASES,
    "alignment_required",
    "aligning",
    "handoff_ready",
    "blocked",
    "needs_owner_decision",
}
CONTRACT_FIELDS = {
    "criterion",
    "intended_result",
    "evidence_claim",
    "scope",
    "gates",
    "validation",
}


class StateError(ValueError):
    """A fail-closed state or transition error."""


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


def load_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise StateError(f"UNREADABLE_{label} {path}: {error}") from error


def require_nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StateError(f"INVALID_{label}")
    return value.strip()


def validate_contract(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != CONTRACT_FIELDS:
        raise StateError("INVALID_CONTRACT_FIELDS")
    for field in ("criterion", "intended_result", "evidence_claim"):
        require_nonempty(value[field], f"CONTRACT_{field.upper()}")
    scope = value["scope"]
    if (
        not isinstance(scope, list)
        or not scope
        or any(not isinstance(item, str) or not item.strip() for item in scope)
    ):
        raise StateError("INVALID_CONTRACT_SCOPE")
    validation = value["validation"]
    if (
        not isinstance(validation, list)
        or not validation
        or any(not isinstance(item, str) or not item.strip() for item in validation)
    ):
        raise StateError("INVALID_CONTRACT_VALIDATION")
    gates = value["gates"]
    if not isinstance(gates, list) or not gates:
        raise StateError("INVALID_CONTRACT_GATES")
    for gate in gates:
        if not isinstance(gate, dict) or set(gate) != {"check", "expect"}:
            raise StateError("INVALID_CONTRACT_GATE")
        require_nonempty(gate["check"], "CONTRACT_GATE_CHECK")
        require_nonempty(gate["expect"], "CONTRACT_GATE_EXPECT")
    return value


def validate_review(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"verdict", "findings"}:
        raise StateError("INVALID_REVIEW_FIELDS")
    if value["verdict"] not in {"accept", "reject"}:
        raise StateError("INVALID_REVIEW_VERDICT")
    findings = value["findings"]
    if not isinstance(findings, list) or any(
        not isinstance(item, str) or not item.strip() for item in findings
    ):
        raise StateError("INVALID_REVIEW_FINDINGS")
    if value["verdict"] == "reject" and not findings:
        raise StateError("REJECT_REQUIRES_FINDINGS")
    if value["verdict"] == "accept" and findings:
        raise StateError("ACCEPT_REQUIRES_NO_FINDINGS")
    return value


def validate_evidence(value: Any) -> dict[str, Any]:
    required = {"focused", "full", "contract_gates"}
    if not isinstance(value, dict) or set(value) != required:
        raise StateError("INVALID_EVIDENCE_FIELDS")
    for field in required:
        if not isinstance(value[field], str) or not value[field].strip():
            raise StateError(f"INVALID_EVIDENCE_{field.upper()}")
    return value


def contract_digest(contract: dict[str, Any]) -> str:
    canonical = json.dumps(contract, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def current_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise StateError("CURRENT_COMMIT_UNAVAILABLE")
    return require_nonempty(result.stdout, "CURRENT_COMMIT")


def validate_state(state: Any) -> dict[str, Any]:
    if not isinstance(state, dict):
        raise StateError("INVALID_STATE_ROOT")
    required = {
        "schema_version",
        "revision",
        "phase",
        "authorization",
        "orchestrator",
        "slice",
        "last_handoff",
        "stop_reason",
        "events",
        "writer_history",
    }
    if set(state) != required:
        raise StateError("INVALID_STATE_FIELDS")
    if state["schema_version"] != SCHEMA_VERSION:
        raise StateError("UNSUPPORTED_SCHEMA_VERSION")
    if not isinstance(state["revision"], int) or state["revision"] < 0:
        raise StateError("INVALID_REVISION")
    if state["phase"] not in PHASES:
        raise StateError("INVALID_PHASE")
    if state["stop_reason"] is not None and (
        not isinstance(state["stop_reason"], str) or not state["stop_reason"].strip()
    ):
        raise StateError("INVALID_STOP_REASON")
    writer_history = state["writer_history"]
    if (
        not isinstance(writer_history, list)
        or any(not isinstance(item, str) or not item.strip() for item in writer_history)
        or len(set(writer_history)) != len(writer_history)
    ):
        raise StateError("INVALID_WRITER_HISTORY")
    authorization = state["authorization"]
    if not isinstance(authorization, dict) or set(authorization) != {
        "status",
        "goal_id",
        "source",
    }:
        raise StateError("INVALID_AUTHORIZATION")
    if authorization["status"] == "none":
        if authorization["goal_id"] is not None or authorization["source"] is not None:
            raise StateError("UNAUTHORIZED_STATE_HAS_GOAL")
        if state["phase"] != "stopped":
            raise StateError("UNAUTHORIZED_STATE_NOT_STOPPED")
    elif authorization["status"] == "standing":
        require_nonempty(authorization["goal_id"], "GOAL_ID")
        if authorization["source"] != "owner":
            raise StateError("INVALID_AUTHORIZATION_SOURCE")
        if state["phase"] == "stopped":
            raise StateError("AUTHORIZED_STATE_STOPPED")
    else:
        raise StateError("INVALID_AUTHORIZATION_STATUS")
    orchestrator = state["orchestrator"]
    if orchestrator is not None:
        if not isinstance(orchestrator, dict) or set(orchestrator) != {
            "generation_id",
            "task_id",
            "accepted_slices",
            "recovery_count",
        }:
            raise StateError("INVALID_ORCHESTRATOR")
        require_nonempty(orchestrator["generation_id"], "GENERATION_ID")
        require_nonempty(orchestrator["task_id"], "ORCHESTRATOR_TASK_ID")
        accepted = orchestrator["accepted_slices"]
        if not isinstance(accepted, int) or not 0 <= accepted <= MAX_ACCEPTED_SLICES:
            raise StateError("INVALID_ACCEPTED_SLICE_COUNT")
        if not isinstance(orchestrator["recovery_count"], int) or orchestrator[
            "recovery_count"
        ] < 0:
            raise StateError("INVALID_ORCHESTRATOR_RECOVERY_COUNT")
    if state["phase"] not in {"stopped", "ready", "handoff_ready"} and orchestrator is None:
        raise StateError("ACTIVE_PHASE_REQUIRES_ORCHESTRATOR")
    slice_state = state["slice"]
    if state["phase"] in ACTIVE_SLICE_PHASES | TERMINAL_SLICE_PHASES:
        if not isinstance(slice_state, dict):
            raise StateError("ACTIVE_SLICE_PHASE_REQUIRES_SLICE")
        expected_slice_fields = {
            "slice_id",
            "writer_task_id",
            "writer_attempt",
            "repair_count",
            "contract",
            "contract_sha256",
            "evidence",
            "review",
            "reviewer_task_ids",
        }
        if set(slice_state) != expected_slice_fields:
            raise StateError("INVALID_SLICE_FIELDS")
        require_nonempty(slice_state["slice_id"], "SLICE_ID")
        require_nonempty(slice_state["writer_task_id"], "WRITER_TASK_ID")
        if not isinstance(slice_state["writer_attempt"], int) or not 1 <= slice_state[
            "writer_attempt"
        ] <= MAX_REPAIRS + 1:
            raise StateError("INVALID_WRITER_ATTEMPT")
        if not isinstance(slice_state["repair_count"], int) or not 0 <= slice_state[
            "repair_count"
        ] <= MAX_REPAIRS:
            raise StateError("INVALID_REPAIR_COUNT")
        contract = validate_contract(slice_state["contract"])
        if slice_state["contract_sha256"] != contract_digest(contract):
            raise StateError("CONTRACT_DIGEST_MISMATCH")
        reviewers = slice_state["reviewer_task_ids"]
        if (
            not isinstance(reviewers, list)
            or any(not isinstance(item, str) or not item.strip() for item in reviewers)
            or len(set(reviewers)) != len(reviewers)
        ):
            raise StateError("INVALID_REVIEWER_HISTORY")
    elif slice_state is not None:
        raise StateError("NON_SLICE_PHASE_HAS_SLICE")
    events = state["events"]
    if not isinstance(events, list) or len(events) > 64:
        raise StateError("INVALID_EVENT_LEDGER")
    event_ids: set[str] = set()
    for event in events:
        if not isinstance(event, dict) or set(event) != {
            "id",
            "type",
            "actor",
            "revision",
        }:
            raise StateError("INVALID_EVENT")
        event_id = require_nonempty(event["id"], "EVENT_ID")
        if event_id in event_ids:
            raise StateError("DUPLICATE_EVENT_ID")
        event_ids.add(event_id)
    return state


def read_state(path: Path) -> dict[str, Any]:
    return validate_state(load_json(path, "STATE"))


def write_state(path: Path, state: dict[str, Any]) -> None:
    validate_state(state)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def task_id(explicit: str | None) -> str:
    return require_nonempty(explicit or os.environ.get("CODEX_THREAD_ID"), "TASK_ID")


def require_checkout_owner(
    lock_path: Path,
    actor: str,
    *,
    expected_role: str | None = None,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    owner = read_owner(lock_path)
    if owner is None:
        raise StateError("NO_CHECKOUT_OWNER")
    if recorded_task_id(owner) != actor:
        raise StateError(f"CHECKOUT_OWNER_MISMATCH {recorded_task_id(owner)}")
    if expected_role is not None and owner.get("role", "orchestrator") != expected_role:
        raise StateError("CHECKOUT_OWNER_ROLE_MISMATCH")
    if state is not None and state["orchestrator"] is not None:
        generation_id = state["orchestrator"]["generation_id"]
        if owner.get("generation_id") not in {None, generation_id}:
            raise StateError("CHECKOUT_GENERATION_MISMATCH")
        if expected_role == "writer":
            active_slice = state["slice"]
            if active_slice is None or owner.get("slice_id") not in {
                None,
                active_slice["slice_id"],
            }:
                raise StateError("CHECKOUT_SLICE_MISMATCH")
    return owner


def ensure_event_is_new(
    state: dict[str, Any], event_id: str, event_type: str, actor: str
) -> bool:
    require_nonempty(event_id, "EVENT_ID")
    for event in state["events"]:
        if event["id"] != event_id:
            continue
        if event["type"] == event_type and event["actor"] == actor:
            return False
        raise StateError("EVENT_ID_REUSED")
    return True


def mutate(
    args: argparse.Namespace,
    event_type: str,
    operation: Callable[[dict[str, Any], str], None],
    *,
    role: str | None,
) -> int:
    actor = task_id(args.task_id)
    with guarded(args.state_path):
        state = read_state(args.state_path)
        if not ensure_event_is_new(state, args.event_id, event_type, actor):
            print(f"ALREADY_APPLIED {args.event_id} {state['revision']}")
            return 0
        if state["revision"] != args.expected_revision:
            raise StateError(f"REVISION_MISMATCH {state['revision']}")
        require_checkout_owner(args.lock_path, actor, expected_role=role, state=state)
        operation(state, actor)
        state["revision"] += 1
        state["events"] = (
            state["events"]
            + [
                {
                    "id": args.event_id,
                    "type": event_type,
                    "actor": actor,
                    "revision": state["revision"],
                }
            ]
        )[-64:]
        write_state(args.state_path, state)
    print(f"TRANSITIONED {event_type} {state['phase']} {state['revision']}")
    return 0


def activate(args: argparse.Namespace) -> int:
    def operation(state: dict[str, Any], actor: str) -> None:
        if state["phase"] != "stopped" or state["authorization"]["status"] != "none":
            raise StateError("ACTIVATION_REQUIRES_STOPPED_UNAUTHORIZED_STATE")
        if not args.confirm_owner_approved:
            raise StateError("OWNER_APPROVAL_CONFIRMATION_REQUIRED")
        state["authorization"] = {
            "status": "standing",
            "goal_id": require_nonempty(args.goal_id, "GOAL_ID"),
            "source": "owner",
        }
        state["phase"] = "ready"
        state["stop_reason"] = None

    return mutate(args, "activate", operation, role="orchestrator")


def start_generation(args: argparse.Namespace) -> int:
    def operation(state: dict[str, Any], actor: str) -> None:
        if state["authorization"]["status"] != "standing":
            raise StateError("GENERATION_REQUIRES_STANDING_AUTHORIZATION")
        if state["phase"] not in {"ready", "handoff_ready"}:
            raise StateError("GENERATION_START_NOT_ALLOWED")
        if state["phase"] == "ready" and state["orchestrator"] is not None:
            raise StateError("GENERATION_ALREADY_ACTIVE")
        state["orchestrator"] = {
            "generation_id": require_nonempty(args.generation_id, "GENERATION_ID"),
            "task_id": actor,
            "accepted_slices": 0,
            "recovery_count": 0,
        }
        state["slice"] = None
        state["phase"] = "ready"

    return mutate(args, "start_generation", operation, role="orchestrator")


def contract_slice(args: argparse.Namespace) -> int:
    contract = validate_contract(load_json(args.contract, "CONTRACT"))

    def operation(state: dict[str, Any], actor: str) -> None:
        orchestrator = state["orchestrator"]
        if state["phase"] != "ready" or orchestrator is None:
            raise StateError("SLICE_CONTRACT_REQUIRES_READY_GENERATION")
        if orchestrator["task_id"] != actor:
            raise StateError("ORCHESTRATOR_TASK_MISMATCH")
        if orchestrator["accepted_slices"] >= MAX_ACCEPTED_SLICES:
            raise StateError("GENERATION_SLICE_LIMIT_REACHED")
        writer = require_nonempty(args.writer_task_id, "WRITER_TASK_ID")
        if writer == actor:
            raise StateError("WRITER_MUST_BE_FRESH_TASK")
        if writer in state["writer_history"]:
            raise StateError("WRITER_TASK_ALREADY_USED")
        state["writer_history"].append(writer)
        state["slice"] = {
            "slice_id": require_nonempty(args.slice_id, "SLICE_ID"),
            "writer_task_id": writer,
            "writer_attempt": 1,
            "repair_count": 0,
            "contract": contract,
            "contract_sha256": contract_digest(contract),
            "evidence": None,
            "review": None,
            "reviewer_task_ids": [],
        }
        state["phase"] = "contracted"

    return mutate(args, "contract_slice", operation, role="orchestrator")


def writer_transition(
    args: argparse.Namespace, event_type: str, source: set[str], target: str
) -> int:
    def operation(state: dict[str, Any], actor: str) -> None:
        if state["phase"] not in source or state["slice"] is None:
            raise StateError(f"{event_type.upper()}_NOT_ALLOWED")
        if state["slice"]["writer_task_id"] != actor:
            raise StateError("WRITER_TASK_MISMATCH")
        state["phase"] = target

    return mutate(args, event_type, operation, role="writer")


def begin_review(args: argparse.Namespace) -> int:
    evidence = validate_evidence(load_json(args.evidence, "EVIDENCE"))

    def operation(state: dict[str, Any], actor: str) -> None:
        if state["phase"] != "validating" or state["slice"] is None:
            raise StateError("BEGIN_REVIEW_NOT_ALLOWED")
        if state["slice"]["writer_task_id"] != actor:
            raise StateError("WRITER_TASK_MISMATCH")
        state["slice"]["evidence"] = evidence
        state["slice"]["review"] = None
        state["phase"] = "reviewing"

    return mutate(args, "begin_review", operation, role="writer")


def record_review(args: argparse.Namespace) -> int:
    review = validate_review(load_json(args.review, "REVIEW"))

    def operation(state: dict[str, Any], actor: str) -> None:
        if state["phase"] != "reviewing" or state["slice"] is None:
            raise StateError("RECORD_REVIEW_NOT_ALLOWED")
        active_slice = state["slice"]
        if active_slice["writer_task_id"] != actor:
            raise StateError("WRITER_TASK_MISMATCH")
        reviewer = require_nonempty(args.reviewer_task_id, "REVIEWER_TASK_ID")
        orchestrator_id = state["orchestrator"]["task_id"]
        if reviewer in {actor, orchestrator_id}:
            raise StateError("REVIEWER_MUST_BE_FRESH_READ_ONLY_TASK")
        if reviewer in active_slice["reviewer_task_ids"]:
            raise StateError("REVIEWER_TASK_ALREADY_USED_FOR_SLICE")
        active_slice["reviewer_task_ids"].append(reviewer)
        active_slice["review"] = {**review, "reviewer_task_id": reviewer}
        if review["verdict"] == "reject":
            if active_slice["repair_count"] >= MAX_REPAIRS:
                state["phase"] = "blocked"
            else:
                active_slice["repair_count"] += 1
                state["phase"] = "repairing"
            return
        accepted_commit = require_nonempty(args.accepted_commit, "ACCEPTED_COMMIT")
        if accepted_commit != current_commit():
            raise StateError("ACCEPTED_COMMIT_IS_NOT_CURRENT_HEAD")
        state["orchestrator"]["accepted_slices"] += 1
        accepted = state["orchestrator"]["accepted_slices"]
        state["last_handoff"] = {
            "generation_id": state["orchestrator"]["generation_id"],
            "slice_id": active_slice["slice_id"],
            "contract_sha256": active_slice["contract_sha256"],
            "evidence": active_slice["evidence"],
            "review": active_slice["review"],
            "accepted_commit": accepted_commit,
        }
        state["slice"] = None
        state["phase"] = (
            "alignment_required" if accepted == MAX_ACCEPTED_SLICES else "ready"
        )

    return mutate(args, "record_review", operation, role="writer")


def begin_alignment(args: argparse.Namespace) -> int:
    def operation(state: dict[str, Any], actor: str) -> None:
        if state["phase"] != "alignment_required":
            raise StateError("ALIGNMENT_NOT_REQUIRED")
        if state["orchestrator"]["task_id"] != actor:
            raise StateError("ORCHESTRATOR_TASK_MISMATCH")
        state["phase"] = "aligning"

    return mutate(args, "begin_alignment", operation, role="orchestrator")


def complete_alignment(args: argparse.Namespace) -> int:
    report = load_json(args.report, "ALIGNMENT_REPORT")
    if not isinstance(report, dict) or set(report) != {
        "goal_status",
        "accepted_slices",
        "remaining_gaps",
        "risks",
        "recommended_next_slice",
    }:
        raise StateError("INVALID_ALIGNMENT_REPORT_FIELDS")

    def operation(state: dict[str, Any], actor: str) -> None:
        if state["phase"] != "aligning":
            raise StateError("COMPLETE_ALIGNMENT_NOT_ALLOWED")
        if state["orchestrator"]["task_id"] != actor:
            raise StateError("ORCHESTRATOR_TASK_MISMATCH")
        if report["accepted_slices"] != MAX_ACCEPTED_SLICES:
            raise StateError("ALIGNMENT_REPORT_SLICE_COUNT_MISMATCH")
        state["last_handoff"] = {
            "generation_id": state["orchestrator"]["generation_id"],
            "alignment": report,
        }
        state["orchestrator"] = None
        state["phase"] = "handoff_ready"

    return mutate(args, "complete_alignment", operation, role="orchestrator")


def recover_actor(args: argparse.Namespace) -> int:
    def operation(state: dict[str, Any], actor: str) -> None:
        if args.terminal_state not in TERMINAL_TASK_STATES:
            raise StateError("INVALID_TERMINAL_TASK_STATE")
        owner = require_checkout_owner(args.lock_path, actor, state=state)
        if owner.get("recovered_from") != args.expected_task_id:
            raise StateError("LOCK_RECOVERY_SOURCE_MISMATCH")
        if owner.get("verified_terminal_state") != args.terminal_state:
            raise StateError("LOCK_RECOVERY_STATE_MISMATCH")
        orchestrator = state["orchestrator"]
        active_slice = state["slice"]
        if active_slice is not None and active_slice["writer_task_id"] == args.expected_task_id:
            active_slice["writer_task_id"] = actor
            if active_slice["writer_attempt"] >= MAX_REPAIRS + 1:
                state["phase"] = "blocked"
            else:
                active_slice["writer_attempt"] += 1
            return
        if orchestrator is not None and orchestrator["task_id"] == args.expected_task_id:
            orchestrator["task_id"] = actor
            orchestrator["recovery_count"] += 1
            return
        raise StateError("EXPECTED_ACTOR_NOT_ACTIVE")

    return mutate(args, "recover_actor", operation, role=None)


def stop(args: argparse.Namespace) -> int:
    def operation(state: dict[str, Any], actor: str) -> None:
        state["authorization"] = {"status": "none", "goal_id": None, "source": None}
        state["orchestrator"] = None
        state["slice"] = None
        state["phase"] = "stopped"
        state["stop_reason"] = require_nonempty(args.reason, "STOP_REASON")

    return mutate(args, "stop", operation, role=None)


def add_mutation_arguments(command: argparse.ArgumentParser) -> None:
    command.add_argument("--task-id")
    command.add_argument("--event-id", required=True)
    command.add_argument("--expected-revision", required=True, type=int)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--lock-path", type=Path, default=default_lock_path())
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("validate")
    commands.add_parser("status")

    activate_command = commands.add_parser("activate")
    add_mutation_arguments(activate_command)
    activate_command.add_argument("--goal-id", required=True)
    activate_command.add_argument("--confirm-owner-approved", action="store_true")

    generation_command = commands.add_parser("start-generation")
    add_mutation_arguments(generation_command)
    generation_command.add_argument("--generation-id", required=True)

    contract_command = commands.add_parser("contract-slice")
    add_mutation_arguments(contract_command)
    contract_command.add_argument("--slice-id", required=True)
    contract_command.add_argument("--writer-task-id", required=True)
    contract_command.add_argument("--contract", type=Path, required=True)

    for name in ("begin-implementation", "begin-validation"):
        command = commands.add_parser(name)
        add_mutation_arguments(command)

    review_command = commands.add_parser("begin-review")
    add_mutation_arguments(review_command)
    review_command.add_argument("--evidence", type=Path, required=True)

    record_review_command = commands.add_parser("record-review")
    add_mutation_arguments(record_review_command)
    record_review_command.add_argument("--review", type=Path, required=True)
    record_review_command.add_argument("--reviewer-task-id", required=True)
    record_review_command.add_argument("--accepted-commit")

    for name in ("begin-alignment",):
        command = commands.add_parser(name)
        add_mutation_arguments(command)

    alignment_command = commands.add_parser("complete-alignment")
    add_mutation_arguments(alignment_command)
    alignment_command.add_argument("--report", type=Path, required=True)

    recovery_command = commands.add_parser("recover-actor")
    add_mutation_arguments(recovery_command)
    recovery_command.add_argument("--expected-task-id", required=True)
    recovery_command.add_argument("--terminal-state", required=True)

    stop_command = commands.add_parser("stop")
    add_mutation_arguments(stop_command)
    stop_command.add_argument("--reason", required=True)
    return parser


def main(arguments: list[str] | None = None) -> int:
    args = build_parser().parse_args(arguments)
    try:
        if args.command in {"validate", "status"}:
            state = read_state(args.state_path)
            if args.command == "status":
                print(json.dumps(state, indent=2, sort_keys=True))
            else:
                print(f"STATE_VALID {state['phase']} {state['revision']}")
            return 0
        if args.command == "activate":
            return activate(args)
        if args.command == "start-generation":
            return start_generation(args)
        if args.command == "contract-slice":
            return contract_slice(args)
        if args.command == "begin-implementation":
            return writer_transition(args, "begin_implementation", {"contracted"}, "implementing")
        if args.command == "begin-validation":
            return writer_transition(
                args,
                "begin_validation",
                {"implementing", "repairing"},
                "validating",
            )
        if args.command == "begin-review":
            return begin_review(args)
        if args.command == "record-review":
            return record_review(args)
        if args.command == "begin-alignment":
            return begin_alignment(args)
        if args.command == "complete-alignment":
            return complete_alignment(args)
        if args.command == "recover-actor":
            return recover_actor(args)
        return stop(args)
    except (OSError, StateError, ValueError) as error:
        print(f"STATE_ERROR {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
