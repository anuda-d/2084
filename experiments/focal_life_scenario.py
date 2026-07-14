"""Provisional deterministic focal-life scenario.

This experiment composes source-linked history into one ordinary allocation
request.  Its names, quantities, and policy are local examples, not settled
worldbuilding or a production simulation design.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from experiments.source_linked_history import (
    Observation,
    SourceLinkedHistory,
    WorldEvent,
)


FOCAL_AGENT_ID = "provisional-focal"


def _require_units(value: int, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative integer")
    return value


@dataclass(frozen=True)
class AllocationNeed:
    """The focal character's ordinary need and request limit."""

    required_units: int
    maximum_request_units: int

    def __post_init__(self) -> None:
        _require_units(self.required_units, "required_units")
        _require_units(self.maximum_request_units, "maximum_request_units")


@dataclass(frozen=True)
class ObservedAvailability:
    """One availability value extracted from a delivered observation."""

    observation_id: str
    evidence_kind: str
    units: int


@dataclass(frozen=True)
class RequestDecisionTrace:
    """Inspectable inputs and rule used by the provisional policy."""

    observed_availability: Tuple[ObservedAvailability, ...]
    selected_observation_id: str | None
    selected_available_units: int
    required_units: int
    maximum_request_units: int
    rule: str


@dataclass(frozen=True)
class AllocationRequest:
    """An attempted request, with no claim about its world outcome."""

    requested_units: int
    trace: RequestDecisionTrace

    def __post_init__(self) -> None:
        _require_units(self.requested_units, "requested_units")
        if not isinstance(self.trace, RequestDecisionTrace):
            raise TypeError("trace must be a RequestDecisionTrace")


@dataclass(frozen=True)
class ObjectiveAllocation:
    """Objective state used by resolution, including an unobserved commitment."""

    availability_event_id: str
    shelf_units: int
    committed_units: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.availability_event_id, str)
            or not self.availability_event_id
        ):
            raise ValueError("availability_event_id must be a nonempty string")
        _require_units(self.shelf_units, "shelf_units")
        _require_units(self.committed_units, "committed_units")
        if self.committed_units > self.shelf_units:
            raise ValueError("committed_units cannot exceed shelf_units")

    @property
    def allocatable_units(self) -> int:
        return self.shelf_units - self.committed_units


@dataclass(frozen=True)
class AllocationResolution:
    """Objective result recorded separately from the selected request."""

    attempted_event: WorldEvent
    consequence_event: WorldEvent
    granted_units: int
    unfilled_units: int


@dataclass(frozen=True)
class FocalLifeScenarioEvidence:
    """Immutable evidence retained from one deterministic scenario run."""

    need: AllocationNeed
    objective_allocation: ObjectiveAllocation
    decision_observations: Tuple[Observation, ...]
    request: AllocationRequest
    resolution: AllocationResolution
    events: Tuple[WorldEvent, ...]
    focal_observations: Tuple[Observation, ...]


def choose_allocation_request(
    observations: Tuple[Observation, ...],
    need: AllocationNeed,
) -> AllocationRequest:
    """Choose a request from delivered observations and need constraints only.

    The provisional policy prefers the latest direct availability observation.
    When none was delivered, it uses the latest official claim.  The request is
    capped by that value, the ordinary need, and the request limit.  If neither
    supported observation kind was delivered, it requests zero.
    """
    if not isinstance(observations, tuple):
        raise TypeError("observations must be a tuple")
    if not isinstance(need, AllocationNeed):
        raise TypeError("need must be an AllocationNeed")

    extracted = []
    candidates = []
    for position, observation in enumerate(observations):
        if not isinstance(observation, Observation):
            raise TypeError("observations must contain Observation records")
        evidence_kind = observation.details.get("evidence_kind")
        units = observation.details.get("available_units")
        if evidence_kind not in ("direct", "official_claim") or units is None:
            continue
        _require_units(units, "observed available_units")
        evidence = ObservedAvailability(
            observation_id=observation.observation_id,
            evidence_kind=evidence_kind,
            units=units,
        )
        extracted.append(evidence)
        priority = 1 if evidence_kind == "direct" else 0
        candidates.append((priority, observation.delivery_tick, position, evidence))

    selected = max(candidates, default=None, key=lambda item: item[:3])
    selected_evidence = selected[3] if selected is not None else None
    selected_units = selected_evidence.units if selected_evidence is not None else 0
    requested_units = min(
        need.required_units,
        need.maximum_request_units,
        selected_units,
    )
    trace = RequestDecisionTrace(
        observed_availability=tuple(extracted),
        selected_observation_id=(
            selected_evidence.observation_id if selected_evidence is not None else None
        ),
        selected_available_units=selected_units,
        required_units=need.required_units,
        maximum_request_units=need.maximum_request_units,
        rule="prefer latest direct; otherwise latest official; cap by need and limit",
    )
    return AllocationRequest(requested_units=requested_units, trace=trace)


def resolve_allocation_request(
    *,
    history: SourceLinkedHistory,
    request: AllocationRequest,
    objective_allocation: ObjectiveAllocation,
    tick: int,
) -> AllocationResolution:
    """Constrain an attempted request with objective state and record its result."""
    if not isinstance(history, SourceLinkedHistory):
        raise TypeError("history must be a SourceLinkedHistory")
    if not isinstance(request, AllocationRequest):
        raise TypeError("request must be an AllocationRequest")
    _require_units(request.requested_units, "requested_units")
    if not isinstance(request.trace, RequestDecisionTrace):
        raise TypeError("request trace must be a RequestDecisionTrace")
    if not isinstance(objective_allocation, ObjectiveAllocation):
        raise TypeError("objective_allocation must be an ObjectiveAllocation")
    _require_units(tick, "tick")
    availability_event = next(
        (
            event
            for event in history.events()
            if event.event_id == objective_allocation.availability_event_id
        ),
        None,
    )
    if availability_event is None:
        raise ValueError("objective allocation must refer to a recorded event")
    if (
        availability_event.details.get("shelf_units")
        != objective_allocation.shelf_units
        or availability_event.details.get("committed_units")
        != objective_allocation.committed_units
    ):
        raise ValueError("objective allocation must match its recorded event")
    if tick < availability_event.tick:
        raise ValueError("resolution cannot occur before objective availability")

    attempted_event = history.record_event(
        tick=tick,
        kind="provisional_allocation_requested",
        details={
            "availability_event_id": objective_allocation.availability_event_id,
            "requested_units": request.requested_units,
        },
    )
    granted_units = min(request.requested_units, objective_allocation.allocatable_units)
    unfilled_units = request.requested_units - granted_units
    consequence_event = history.record_event(
        tick=tick,
        kind="provisional_allocation_resolved",
        details={
            "attempted_event_id": attempted_event.event_id,
            "shelf_units": objective_allocation.shelf_units,
            "committed_units": objective_allocation.committed_units,
            "allocatable_units": objective_allocation.allocatable_units,
            "requested_units": request.requested_units,
            "granted_units": granted_units,
            "unfilled_units": unfilled_units,
        },
    )
    return AllocationResolution(
        attempted_event=attempted_event,
        consequence_event=consequence_event,
        granted_units=granted_units,
        unfilled_units=unfilled_units,
    )


def run_provisional_focal_life_scenario() -> FocalLifeScenarioEvidence:
    """Run the fixed example and return its complete development evidence."""
    history = SourceLinkedHistory()
    availability_event = history.record_event(
        tick=1,
        kind="provisional_shelf_availability",
        details={"shelf_units": 2, "committed_units": 1},
    )
    objective_allocation = ObjectiveAllocation(
        availability_event_id=availability_event.event_id,
        shelf_units=availability_event.details["shelf_units"],
        committed_units=availability_event.details["committed_units"],
    )
    history.deliver_observation(
        agent_id=FOCAL_AGENT_ID,
        event_id=availability_event.event_id,
        source="direct sight",
        delivery_tick=1,
        details={"evidence_kind": "direct", "available_units": 2},
    )

    official_claim_event = history.record_event(
        tick=2,
        kind="provisional_official_availability_claim",
        details={"claimed_available_units": 4},
    )
    history.deliver_observation(
        agent_id=FOCAL_AGENT_ID,
        event_id=official_claim_event.event_id,
        source="official notice",
        delivery_tick=2,
        details={"evidence_kind": "official_claim", "available_units": 4},
    )

    need = AllocationNeed(required_units=3, maximum_request_units=3)
    decision_observations = history.observations_for(FOCAL_AGENT_ID)
    request = choose_allocation_request(decision_observations, need)
    resolution = resolve_allocation_request(
        history=history,
        request=request,
        objective_allocation=objective_allocation,
        tick=3,
    )
    history.deliver_observation(
        agent_id=FOCAL_AGENT_ID,
        event_id=resolution.consequence_event.event_id,
        source="direct handover",
        delivery_tick=3,
        details={
            "granted_units": resolution.granted_units,
            "unfilled_units": resolution.unfilled_units,
        },
    )
    return FocalLifeScenarioEvidence(
        need=need,
        objective_allocation=objective_allocation,
        decision_observations=decision_observations,
        request=request,
        resolution=resolution,
        events=history.events(),
        focal_observations=history.observations_for(FOCAL_AGENT_ID),
    )
