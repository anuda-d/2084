"""Bounded institutional records and policy input."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from simulation.events import Observation
from simulation.official_record import OfficialRecord


@dataclass
class InstitutionState:
    institution_id: str
    display_name: str
    official_record: OfficialRecord
    records: dict[str, Any] = field(default_factory=dict)
    reports: list[Observation] = field(default_factory=list)
    last_public_claim_event_id: str | None = None
    official_record_rewrite_authorized_actor_ids: tuple[str, ...] = ()


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


@dataclass(frozen=True)
class OfficialRecordPublication:
    artifact_id: str
    version_id: str
    period_id: str
    entitlement_packets: int


@dataclass(frozen=True)
class OfficialRecordRewrite:
    actor_id: str
    reason: str
    artifact_id: str
    expected_current_version_id: str
    version_id: str
    period_id: str
    entitlement_packets: int


class InstitutionDecisionPolicy(Protocol):
    def choose_initial_publication(
        self, view: InstitutionView
    ) -> OfficialRecordPublication | None:
        ...

    def choose_official_record_rewrite(
        self, view: InstitutionView
    ) -> OfficialRecordRewrite | None:
        ...

    def choose_claim(self, view: InstitutionView) -> OfficialClaim | None:
        ...
