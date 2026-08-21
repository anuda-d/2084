"""Agent-owned state and the restricted view supplied to decision policies."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Literal, Mapping, Protocol, runtime_checkable

from simulation.actions import ActionAttempt, ActionResult
from simulation.beliefs import Belief
from simulation.events import Observation
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
    status: Literal["failed"]
    failure_kind: str
    failure_type: str
    attempted_action_kind: str
    attempt_event_id: str | None = None
    action_id: str | None = None

    def linked_to(
        self, *, attempt_event_id: str, action_id: str
    ) -> PolicyDecisionRecord:
        return replace(
            self,
            attempt_event_id=attempt_event_id,
            action_id=action_id,
        )

    def to_data(self) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "tick": self.tick,
            "agent_id": self.agent_id,
            "policy_kind": self.policy_kind,
            "status": self.status,
            "failure_kind": self.failure_kind,
            "failure_type": self.failure_type,
            "attempted_action_kind": self.attempted_action_kind,
            "attempt_event_id": self.attempt_event_id,
            "action_id": self.action_id,
        }


class DecisionPolicy(Protocol):
    def choose(self, view: AgentView) -> ActionAttempt:
        ...


@runtime_checkable
class DecisionRecordSource(Protocol):
    """Optional policy seam for one private record produced by the latest choice."""

    def take_decision_record(self) -> PolicyDecisionRecord | None:
        ...
