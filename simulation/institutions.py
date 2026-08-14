"""Bounded institutional records and policy input."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from simulation.events import Observation


@dataclass
class InstitutionState:
    institution_id: str
    display_name: str
    records: dict[str, Any] = field(default_factory=dict)
    reports: list[Observation] = field(default_factory=list)
    last_public_claim_event_id: str | None = None


@dataclass(frozen=True)
class InstitutionView:
    """Institutional policy input; private agent state and diaries are absent."""

    tick: int
    records: Mapping[str, Any]
    reports: tuple[Observation, ...]


@dataclass(frozen=True)
class OfficialClaim:
    proposition: str
    asserted_value: int


class InstitutionDecisionPolicy(Protocol):
    def choose_claim(self, view: InstitutionView) -> OfficialClaim | None:
        ...
