"""Agent-owned state and the restricted view supplied to decision policies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from experiments.core.actions import ActionAttempt
from experiments.core.beliefs import Belief
from experiments.core.events import Observation


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
    required_units: int = 0
    obligations: tuple[str, ...] = ()
    last_attempt: ActionAttempt | None = None
    action_history: list[ActionAttempt] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)
    beliefs: list[Belief] = field(default_factory=list)


@dataclass(frozen=True)
class AgentView:
    """The complete policy input; it deliberately contains no objective world state."""

    tick: int
    agent_id: str
    location: str
    aim: str
    required_units: int
    obligations: tuple[str, ...]
    last_attempt: ActionAttempt | None
    action_history: tuple[ActionAttempt, ...]
    observations: tuple[Observation, ...]
    beliefs: tuple[Belief, ...]
    accessible_diary_id: str | None
    accessible_diary_entry_count: int
    accessible_diary_entries: tuple[DiaryEntryKnowledge, ...]
    valid_actions: tuple[str, ...]


class DecisionPolicy(Protocol):
    def choose(self, view: AgentView) -> ActionAttempt:
        ...
