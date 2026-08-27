"""Agent-owned state and the restricted view supplied to decision policies."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from typing import Any, Literal, Mapping, Protocol, runtime_checkable

from simulation.actions import ActionAttempt, ActionResult
from simulation.beliefs import Belief
from simulation.events import Observation, freeze_mapping, to_plain_data
from simulation.understanding import ContextualStance, InterpretedClaim, MemoryTrace


MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES = 8 * 1024 * 1024
PRIVATE_DECISION_RECORD_RESOLUTION_BASE_BYTES = 4 * 1024


class PrivateDecisionRecordLimitError(RuntimeError):
    """A candidate private evidence collection exceeds its approved ceiling."""

    def __init__(self, *, attempted_bytes: int, maximum_bytes: int) -> None:
        super().__init__(
            "retained private decision records exceed the approved "
            f"{maximum_bytes}-byte ceiling"
        )
        self.attempted_bytes = attempted_bytes
        self.maximum_bytes = maximum_bytes


@dataclass(frozen=True)
class DiaryEntryKnowledge:
    entry_id: str
    proposition: str
    asserted_value: int
    source_observation_ids: tuple[str, ...]
    started_tick: int
    completed_tick: int


@dataclass(frozen=True)
class ActionContinuityRequirement:
    """World-owned reference to one older action that still explains state.

    The requirement points into the actor's append-only action history and
    actor-safe result collection. Policies can inspect the resolved projection
    but cannot author or clear the canonical requirement.
    """

    requirement_id: str
    action_id: str
    attempt_event_id: str
    action_history_index: int
    attempt: ActionAttempt
    result: ActionResult
    reason: Literal["fulfilled_obligation"]
    state_field: Literal["obligations"]
    state_value: str
    lifecycle: Literal["through_selected_decision"]

    def __post_init__(self) -> None:
        for label, value in (
            ("requirement_id", self.requirement_id),
            ("action_id", self.action_id),
            ("attempt_event_id", self.attempt_event_id),
            ("state_value", self.state_value),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"continuity requirement {label} must be non-empty")
        if (
            not isinstance(self.action_history_index, int)
            or isinstance(self.action_history_index, bool)
            or self.action_history_index < 0
        ):
            raise ValueError(
                "continuity requirement action_history_index must be non-negative"
            )
        if not isinstance(self.attempt, ActionAttempt):
            raise ValueError("continuity requirement attempt must be actor-safe")
        if not isinstance(self.result, ActionResult):
            raise ValueError("continuity requirement result must be actor-safe")
        if (
            self.result.action_id != self.action_id
            or self.result.attempt_event_id != self.attempt_event_id
            or self.result.actor_id != self.attempt.actor_id
            or self.result.action_kind != self.attempt.kind
            or self.result.status != "completed"
        ):
            raise ValueError(
                "continuity requirement snapshots must identify one completed action"
            )
        if self.reason != "fulfilled_obligation":
            raise ValueError("unsupported continuity requirement reason")
        if self.state_field != "obligations":
            raise ValueError("unsupported continuity requirement state field")
        if self.lifecycle != "through_selected_decision":
            raise ValueError("unsupported continuity requirement lifecycle")


@dataclass
class AgentState:
    agent_id: str
    display_name: str
    role: str
    location: str
    aim: str
    required_resource_id: str | None = None
    required_units: int = 0
    resource_holdings: dict[str, int] = field(default_factory=dict)
    obligations: tuple[str, ...] = ()
    last_attempt: ActionAttempt | None = None
    action_history: list[ActionAttempt] = field(default_factory=list)
    action_results: list[ActionResult] = field(default_factory=list)
    continuity_requirements: tuple[ActionContinuityRequirement, ...] = ()
    observations: list[Observation] = field(default_factory=list)
    beliefs: list[Belief] = field(default_factory=list)
    memory_traces: tuple[MemoryTrace, ...] = ()
    interpreted_claims: tuple[InterpretedClaim, ...] = ()
    contextual_stance: ContextualStance | None = None


@dataclass(frozen=True)
class AgentView:
    """The complete policy input; it deliberately contains no objective world state."""

    tick: int
    agent_id: str
    display_name: str
    role: str
    location: str
    aim: str
    required_resource_id: str | None
    required_units: int
    resource_holdings: Mapping[str, int]
    remaining_required_units: int
    obligations: tuple[str, ...]
    last_attempt: ActionAttempt | None
    action_history: tuple[ActionAttempt, ...]
    action_results: tuple[ActionResult, ...]
    observations: tuple[Observation, ...]
    beliefs: tuple[Belief, ...]
    memory_traces: tuple[MemoryTrace, ...]
    interpreted_claims: tuple[InterpretedClaim, ...]
    contextual_stance: ContextualStance | None
    accessible_diary_id: str | None
    accessible_diary_entry_count: int
    accessible_diary_entries: tuple[DiaryEntryKnowledge, ...]
    consultable_official_record_ids: tuple[str, ...]
    reachable_destinations: tuple[str, ...]
    work_action_available: bool
    allocation_action_available: bool
    valid_actions: tuple[str, ...]
    household_action_available: bool = False
    continuity_requirements: tuple[ActionContinuityRequirement, ...] = ()


@dataclass(frozen=True)
class PolicyDecisionRecord:
    """Private decision evidence kept outside objective event history."""

    decision_id: str
    tick: int
    agent_id: str
    policy_kind: str
    configuration_id: str
    status: Literal["selected", "failed"]
    model_input: Mapping[str, Any]
    model_input_bytes: int
    structured_response: Mapping[str, Any] | None
    attempted_action: Mapping[str, Any]
    attempted_action_kind: str
    authorship_identity: Mapping[str, Any] | None = None
    failure_kind: str | None = None
    failure_type: str | None = None
    provider_call_attempted: bool = False
    attempt_event_id: str | None = None
    action_id: str | None = None
    validation_status: Literal["accepted", "rejected"] | None = None
    resolution_status: Literal["completed", "rejected"] | None = None
    outcome_event_id: str | None = None
    resolved_tick: int | None = None
    resolution_reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "model_input", freeze_mapping(self.model_input))
        object.__setattr__(
            self,
            "structured_response",
            (
                freeze_mapping(self.structured_response)
                if self.structured_response is not None
                else None
            ),
        )
        object.__setattr__(
            self, "attempted_action", freeze_mapping(self.attempted_action)
        )
        object.__setattr__(
            self,
            "authorship_identity",
            (
                freeze_mapping(self.authorship_identity)
                if self.authorship_identity is not None
                else None
            ),
        )

    def linked_to(
        self,
        *,
        attempt_event_id: str,
        action_id: str,
        validation_status: Literal["accepted", "rejected"],
    ) -> PolicyDecisionRecord:
        return replace(
            self,
            attempt_event_id=attempt_event_id,
            action_id=action_id,
            validation_status=validation_status,
        )

    def resolved_with(self, result: ActionResult) -> PolicyDecisionRecord:
        return replace(
            self,
            resolution_status=result.status,
            outcome_event_id=result.outcome_event_id,
            resolved_tick=result.resolved_tick,
            resolution_reason=result.reason,
        )

    def to_data(self) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "tick": self.tick,
            "agent_id": self.agent_id,
            "policy_kind": self.policy_kind,
            "configuration_id": self.configuration_id,
            "authorship_identity": (
                to_plain_data(self.authorship_identity)
                if self.authorship_identity is not None
                else None
            ),
            "status": self.status,
            "model_input": to_plain_data(self.model_input),
            "model_input_bytes": self.model_input_bytes,
            "structured_response": (
                to_plain_data(self.structured_response)
                if self.structured_response is not None
                else None
            ),
            "attempted_action": to_plain_data(self.attempted_action),
            "failure_kind": self.failure_kind,
            "failure_type": self.failure_type,
            "provider_call_attempted": self.provider_call_attempted,
            "attempted_action_kind": self.attempted_action_kind,
            "attempt_event_id": self.attempt_event_id,
            "action_id": self.action_id,
            "validation_status": self.validation_status,
            "resolution_status": self.resolution_status,
            "outcome_event_id": self.outcome_event_id,
            "resolved_tick": self.resolved_tick,
            "resolution_reason": self.resolution_reason,
        }


def serialize_private_decision_records(
    records: tuple[PolicyDecisionRecord, ...],
) -> str:
    """Serialize retained inspector-only evidence with one canonical format."""
    return json.dumps(
        [record.to_data() for record in records],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def private_decision_records_size_bytes(
    records: tuple[PolicyDecisionRecord, ...],
) -> int:
    """Measure exact UTF-8 bytes retained by the canonical record collection."""
    return len(serialize_private_decision_records(records).encode("utf-8"))


def validate_private_decision_record_retention(
    records: tuple[PolicyDecisionRecord, ...],
    *,
    reserved_bytes: int = 0,
) -> int:
    """Return candidate size or refuse retention above the approved ceiling."""
    if (
        not isinstance(reserved_bytes, int)
        or isinstance(reserved_bytes, bool)
        or reserved_bytes < 0
    ):
        raise ValueError("reserved_bytes must be a non-negative integer")
    retained_bytes = private_decision_records_size_bytes(records)
    required_bytes = retained_bytes + reserved_bytes
    if required_bytes > MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES:
        raise PrivateDecisionRecordLimitError(
            attempted_bytes=required_bytes,
            maximum_bytes=MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES,
        )
    return retained_bytes


class DecisionPolicy(Protocol):
    def choose(self, view: AgentView) -> ActionAttempt:
        ...


@runtime_checkable
class DecisionRecordSource(Protocol):
    """Optional policy seam for one private record produced by the latest choice."""

    def take_decision_record(self) -> PolicyDecisionRecord | None:
        ...
