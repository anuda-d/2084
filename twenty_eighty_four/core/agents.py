"""Agent-owned state and the restricted view supplied to decision policies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol

from twenty_eighty_four.core.actions import ActionAttempt, ActionResult
from twenty_eighty_four.core.beliefs import Belief
from twenty_eighty_four.core.events import Observation


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


@dataclass(frozen=True)
class AgentView:
    """The complete policy input; it deliberately contains no objective world state."""

    tick: int
    agent_id: str
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
    accessible_diary_id: str | None
    accessible_diary_entry_count: int
    accessible_diary_entries: tuple[DiaryEntryKnowledge, ...]
    valid_actions: tuple[str, ...]


class DecisionPolicy(Protocol):
    def choose(self, view: AgentView) -> ActionAttempt:
        ...
