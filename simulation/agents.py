"""Agent-owned state and the restricted view supplied to decision policies."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Literal, Mapping, Protocol, runtime_checkable

from simulation.actions import ActionAttempt, ActionResult
from simulation.beliefs import Belief
from simulation.events import Observation, freeze_mapping, to_plain_data
from simulation.understanding import ContextualStance, InterpretedClaim, MemoryTrace


@dataclass(frozen=True)
class DiaryEntryKnowledge:
    entry_id: str
    proposition: str
    asserted_value: int
    source_observation_ids: tuple[str, ...]
    started_tick: int
    completed_tick: int


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
    structured_response: Mapping[str, Any] | None
    attempted_action: Mapping[str, Any]
    attempted_action_kind: str
    failure_kind: str | None = None
    failure_type: str | None = None
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
            "status": self.status,
            "model_input": to_plain_data(self.model_input),
            "structured_response": (
                to_plain_data(self.structured_response)
                if self.structured_response is not None
                else None
            ),
            "attempted_action": to_plain_data(self.attempted_action),
            "failure_kind": self.failure_kind,
            "failure_type": self.failure_type,
            "attempted_action_kind": self.attempted_action_kind,
            "attempt_event_id": self.attempt_event_id,
            "action_id": self.action_id,
            "validation_status": self.validation_status,
            "resolution_status": self.resolution_status,
            "outcome_event_id": self.outcome_event_id,
            "resolved_tick": self.resolved_tick,
            "resolution_reason": self.resolution_reason,
        }


class DecisionPolicy(Protocol):
    def choose(self, view: AgentView) -> ActionAttempt:
        ...


@runtime_checkable
class DecisionRecordSource(Protocol):
    """Optional policy seam for one private record produced by the latest choice."""

    def take_decision_record(self) -> PolicyDecisionRecord | None:
        ...
