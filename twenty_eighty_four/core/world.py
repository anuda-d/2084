"""Objective spatial state for the living simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from twenty_eighty_four.core.agents import AgentState
from twenty_eighty_four.core.institutions import InstitutionState


@dataclass
class ResourceState:
    total_units: int
    committed_units: int
    granted_units: int = 0

    @property
    def allocatable_units(self) -> int:
        return max(0, self.total_units - self.committed_units - self.granted_units)


@dataclass(frozen=True)
class DiaryEntry:
    entry_id: str
    author_id: str
    proposition: str
    asserted_value: int
    source_observation_ids: tuple[str, ...]
    started_tick: int
    completed_tick: int


@dataclass
class PhysicalDiary:
    object_id: str
    location: str
    possessor_id: str | None = None
    entries: tuple[DiaryEntry, ...] = ()


@dataclass
class WorldState:
    tick: int
    seed: int
    travel_graph: Mapping[str, tuple[str, ...]]
    agents: dict[str, AgentState]
    resource: ResourceState
    institution: InstitutionState
    diaries: dict[str, PhysicalDiary]

    def can_travel(self, origin: str, destination: str) -> bool:
        return destination in self.travel_graph.get(origin, ())
