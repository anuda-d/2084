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
SUPPORTING_AGENT_ID = "provisional-supporting-person"


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
class FollowUpDecisionTrace:
    """Delivered handover and local rule used for one later choice."""

    selected_observation_id: str | None
    observed_granted_units: int | None
    required_units: int
    remaining_units: int
    rule: str


@dataclass(frozen=True)
class FollowUpDecision:
    """A later ordinary choice, with no claim about its world outcome."""

    choice: str
    trace: FollowUpDecisionTrace


@dataclass(frozen=True)
class FollowUpResolution:
    """Objective result recorded separately from one follow-up choice."""

    attempted_event: WorldEvent
    outcome_event: WorldEvent
    granted_units: int
    unfilled_units: int


@dataclass(frozen=True)
class OutcomeCarryoverTrace:
    """Delivered outcome, pressure, and local rule for one next choice."""

    selected_observation_id: str | None
    selected_pressure_observation_id: str | None
    observed_granted_units: int | None
    observed_unfilled_units: int | None
    observed_pressure_action: str | None
    remaining_need_units: int | None
    rule: str


@dataclass(frozen=True)
class OutcomeCarryoverDecision:
    """A third ordinary choice, with no claim about its world outcome."""

    choice: str
    trace: OutcomeCarryoverTrace


@dataclass(frozen=True)
class SupportingActionTrace:
    """Visible focal action and local rule used by one supporting person."""

    selected_observation_id: str | None
    observed_requested_units: int | None
    rule: str


@dataclass(frozen=True)
class SupportingActionDecision:
    """A supporting person's bounded social action, not its world outcome."""

    action: str
    trace: SupportingActionTrace


@dataclass(frozen=True)
class SupportingActionResolution:
    """Recorded world action produced separately from a supporting decision."""

    action_event: WorldEvent


@dataclass(frozen=True)
class ObjectiveAvailabilityEvidence:
    """The narrow objective proposition retained beside fuller allocation state."""

    proposition: str
    units: int
    source_event_id: str


@dataclass(frozen=True)
class PrivateAvailabilityBelief:
    """A retained availability belief derived from one direct observation."""

    proposition: str
    units: int
    source_observation_id: str
    source_event_id: str


@dataclass(frozen=True)
class PublicExpressionTrace:
    """Delivered evidence and local rule used for one public claim."""

    selected_private_observation_id: str
    selected_official_observation_id: str | None
    selected_pressure_observation_id: str | None
    rule: str


@dataclass(frozen=True)
class PublicExpressionDecision:
    """A public claim decision, with no authority to record a world event."""

    proposition: str
    expressed_units: int
    private_belief: PrivateAvailabilityBelief
    trace: PublicExpressionTrace


@dataclass(frozen=True)
class PublicExpressionResolution:
    """The separately recorded public expression."""

    expression_event: WorldEvent


@dataclass(frozen=True)
class FocalLifeScenarioEvidence:
    """Immutable evidence retained from one deterministic scenario run."""

    need: AllocationNeed
    objective_allocation: ObjectiveAllocation
    objective_availability_evidence: ObjectiveAvailabilityEvidence
    decision_observations: Tuple[Observation, ...]
    request: AllocationRequest
    resolution: AllocationResolution
    supporting_observations: Tuple[Observation, ...]
    supporting_decision: SupportingActionDecision
    supporting_resolution: SupportingActionResolution
    events: Tuple[WorldEvent, ...]
    focal_observations: Tuple[Observation, ...]
    follow_up_observations: Tuple[Observation, ...]
    follow_up: FollowUpDecision
    follow_up_resolution: FollowUpResolution
    follow_up_outcome_observation: Observation
    focal_pressure_observation: Observation | None
    third_choice_observations: Tuple[Observation, ...]
    third_choice: OutcomeCarryoverDecision
    private_availability_belief: PrivateAvailabilityBelief
    public_expression: PublicExpressionDecision
    public_expression_resolution: PublicExpressionResolution


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


def choose_follow_up_after_allocation(
    observations: Tuple[Observation, ...],
    need: AllocationNeed,
) -> FollowUpDecision:
    """Choose a provisional next activity from a delivered handover only."""
    if not isinstance(observations, tuple):
        raise TypeError("observations must be a tuple")
    if not isinstance(need, AllocationNeed):
        raise TypeError("need must be an AllocationNeed")

    candidates = []
    for position, observation in enumerate(observations):
        if not isinstance(observation, Observation):
            raise TypeError("observations must contain Observation records")
        if observation.details.get("evidence_kind") != "allocation_handover":
            continue
        granted_units = observation.details.get("granted_units")
        _require_units(granted_units, "observed granted_units")
        candidates.append(
            (observation.delivery_tick, position, observation, granted_units)
        )

    selected = max(candidates, default=None, key=lambda item: item[:2])
    selected_observation = selected[2] if selected is not None else None
    granted_units = selected[3] if selected is not None else None
    remaining_units = (
        max(need.required_units - granted_units, 0)
        if granted_units is not None
        else need.required_units
    )
    if granted_units is None:
        choice = "wait_for_handover"
    elif remaining_units > 0:
        choice = "seek_remaining_allocation"
    else:
        choice = "continue_ordinary_task"
    return FollowUpDecision(
        choice=choice,
        trace=FollowUpDecisionTrace(
            selected_observation_id=(
                selected_observation.observation_id
                if selected_observation is not None
                else None
            ),
            observed_granted_units=granted_units,
            required_units=need.required_units,
            remaining_units=remaining_units,
            rule=(
                "wait without a delivered handover; otherwise use the latest "
                "handover, seek remainder when observed grant is below need, "
                "or continue ordinary task"
            ),
        ),
    )


def choose_after_follow_up_outcome(
    observations: Tuple[Observation, ...],
) -> OutcomeCarryoverDecision:
    """Choose one next activity from delivered outcomes and social pressure."""
    if not isinstance(observations, tuple):
        raise TypeError("observations must be a tuple")

    candidates = []
    pressure_candidates = []
    for position, observation in enumerate(observations):
        if not isinstance(observation, Observation):
            raise TypeError("observations must contain Observation records")
        evidence_kind = observation.details.get("evidence_kind")
        if evidence_kind == "social_pressure":
            action = observation.details.get("action")
            if action == "urge_public_agreement":
                pressure_candidates.append(
                    (observation.delivery_tick, position, observation, action)
                )
            continue
        if evidence_kind != "follow_up_allocation_outcome":
            continue
        granted_units = observation.details.get("granted_units")
        unfilled_units = observation.details.get("unfilled_units")
        _require_units(granted_units, "observed granted_units")
        _require_units(unfilled_units, "observed unfilled_units")
        candidates.append(
            (
                observation.delivery_tick,
                position,
                observation,
                granted_units,
                unfilled_units,
            )
        )

    selected = max(candidates, default=None, key=lambda item: item[:2])
    selected_observation = selected[2] if selected is not None else None
    granted_units = selected[3] if selected is not None else None
    unfilled_units = selected[4] if selected is not None else None
    selected_pressure = max(
        pressure_candidates,
        default=None,
        key=lambda item: item[:2],
    )
    pressure_observation = selected_pressure[2] if selected_pressure is not None else None
    pressure_action = selected_pressure[3] if selected_pressure is not None else None
    if selected_observation is None:
        choice = "wait_for_follow_up_outcome"
    elif unfilled_units > 0 and pressure_observation is not None:
        choice = "seek_alternative_source"
    elif unfilled_units > 0:
        choice = "wait_for_changed_conditions"
    else:
        choice = "continue_ordinary_task"
    return OutcomeCarryoverDecision(
        choice=choice,
        trace=OutcomeCarryoverTrace(
            selected_observation_id=(
                selected_observation.observation_id
                if selected_observation is not None
                else None
            ),
            selected_pressure_observation_id=(
                pressure_observation.observation_id
                if pressure_observation is not None
                else None
            ),
            observed_granted_units=granted_units,
            observed_unfilled_units=unfilled_units,
            observed_pressure_action=pressure_action,
            remaining_need_units=unfilled_units,
            rule=(
                "wait without a delivered follow-up outcome; otherwise use the "
                "latest outcome shortfall as remaining need, seek an alternative "
                "source when matching social pressure was delivered, wait for "
                "changed conditions while need remains, or continue ordinary task"
            ),
        ),
    )


def choose_supporting_action(
    observations: Tuple[Observation, ...],
) -> SupportingActionDecision:
    """Choose a bounded social response from this person's observations only."""
    if not isinstance(observations, tuple):
        raise TypeError("observations must be a tuple")

    candidates = []
    for position, observation in enumerate(observations):
        if not isinstance(observation, Observation):
            raise TypeError("observations must contain Observation records")
        if observation.details.get("evidence_kind") != "visible_allocation_request":
            continue
        requested_units = observation.details.get("requested_units")
        _require_units(requested_units, "observed requested_units")
        candidates.append(
            (observation.delivery_tick, position, observation, requested_units)
        )

    selected = max(candidates, default=None, key=lambda item: item[:2])
    selected_observation = selected[2] if selected is not None else None
    requested_units = selected[3] if selected is not None else None
    action = (
        "urge_public_agreement"
        if selected_observation is not None and requested_units > 0
        else "take_no_social_action"
    )
    return SupportingActionDecision(
        action=action,
        trace=SupportingActionTrace(
            selected_observation_id=(
                selected_observation.observation_id
                if selected_observation is not None
                else None
            ),
            observed_requested_units=requested_units,
            rule=(
                "urge public agreement after the latest visible allocation request "
                "for more than zero units; otherwise take no social action"
            ),
        ),
    )


def resolve_supporting_action(
    *,
    history: SourceLinkedHistory,
    decision: SupportingActionDecision,
    selected_observation: Observation,
    tick: int,
) -> SupportingActionResolution:
    """Validate source-linked evidence, then record one supporting action."""
    if not isinstance(history, SourceLinkedHistory):
        raise TypeError("history must be a SourceLinkedHistory")
    if not isinstance(decision, SupportingActionDecision):
        raise TypeError("decision must be a SupportingActionDecision")
    if not isinstance(decision.trace, SupportingActionTrace):
        raise TypeError("decision trace must be a SupportingActionTrace")
    if not isinstance(selected_observation, Observation):
        raise TypeError("selected_observation must be an Observation")
    _require_units(tick, "tick")

    events = history.events()
    observations = history.observations()
    visible_request_event = next(
        (
            event
            for event in events
            if event.event_id == selected_observation.event_id
        ),
        None,
    )
    if visible_request_event is None or selected_observation not in observations:
        raise ValueError("selected supporting evidence must be recorded in history")
    requested_units = selected_observation.details.get("requested_units")
    _require_units(requested_units, "supporting observed requested_units")
    if (
        selected_observation.agent_id != SUPPORTING_AGENT_ID
        or selected_observation.details.get("evidence_kind")
        != "visible_allocation_request"
        or visible_request_event.kind != "provisional_allocation_requested"
        or visible_request_event.details.get("requested_units") != requested_units
    ):
        raise ValueError("selected supporting evidence is inconsistent")
    if decision != choose_supporting_action((selected_observation,)):
        raise ValueError("supporting decision is inconsistent with selected evidence")
    if tick < max(visible_request_event.tick, selected_observation.delivery_tick):
        raise ValueError("supporting action cannot precede its evidence")

    action_event = history.record_event(
        tick=tick,
        kind="provisional_supporting_action",
        details={
            "actor_id": SUPPORTING_AGENT_ID,
            "action": decision.action,
            "selected_observation_id": selected_observation.observation_id,
            "visible_request_event_id": visible_request_event.event_id,
        },
    )
    return SupportingActionResolution(action_event=action_event)


def choose_public_availability_expression(
    observations: Tuple[Observation, ...],
) -> PublicExpressionDecision:
    """Choose one public claim from delivered availability and pressure only."""
    if not isinstance(observations, tuple):
        raise TypeError("observations must be a tuple")
    direct_candidates = []
    official_candidates = []
    pressure_candidates = []
    for position, observation in enumerate(observations):
        if not isinstance(observation, Observation):
            raise TypeError("observations must contain Observation records")
        evidence_kind = observation.details.get("evidence_kind")
        if evidence_kind == "direct":
            units = observation.details.get("available_units")
            _require_units(units, "direct available_units")
            direct_candidates.append((observation.delivery_tick, position, observation))
        elif evidence_kind == "official_claim":
            units = observation.details.get("available_units")
            _require_units(units, "official available_units")
            official_candidates.append((observation.delivery_tick, position, observation))
        elif (
            evidence_kind == "social_pressure"
            and observation.details.get("action") == "urge_public_agreement"
        ):
            pressure_candidates.append((observation.delivery_tick, position, observation))
    direct_selected = max(direct_candidates, default=None, key=lambda item: item[:2])
    official_selected = max(
        official_candidates, default=None, key=lambda item: item[:2]
    )
    pressure_selected = max(
        pressure_candidates, default=None, key=lambda item: item[:2]
    )
    direct = direct_selected[2] if direct_selected is not None else None
    official = official_selected[2] if official_selected is not None else None
    pressure = pressure_selected[2] if pressure_selected is not None else None
    if direct is None:
        raise ValueError("a direct availability observation is required")

    private = PrivateAvailabilityBelief(
        proposition="available_units",
        units=direct.details["available_units"],
        source_observation_id=direct.observation_id,
        source_event_id=direct.event_id,
    )
    selected_official = official if pressure is not None else None
    expressed_units = (
        selected_official.details["available_units"]
        if selected_official is not None
        else private.units
    )
    return PublicExpressionDecision(
        proposition=private.proposition,
        expressed_units=expressed_units,
        private_belief=private,
        trace=PublicExpressionTrace(
            selected_private_observation_id=direct.observation_id,
            selected_official_observation_id=(
                selected_official.observation_id
                if selected_official is not None
                else None
            ),
            selected_pressure_observation_id=(
                pressure.observation_id if pressure is not None else None
            ),
            rule=(
                "repeat the latest delivered official availability claim when "
                "social pressure is delivered; otherwise express retained direct evidence"
            ),
        ),
    )


def resolve_public_expression(
    *,
    history: SourceLinkedHistory,
    decision: PublicExpressionDecision,
    selected_private_observation: Observation,
    selected_official_observation: Observation | None,
    selected_pressure_observation: Observation | None,
    tick: int,
) -> PublicExpressionResolution:
    """Validate delivered evidence, then record one public expression."""
    if not isinstance(history, SourceLinkedHistory):
        raise TypeError("history must be a SourceLinkedHistory")
    if not isinstance(decision, PublicExpressionDecision):
        raise TypeError("decision must be a PublicExpressionDecision")
    if not isinstance(selected_private_observation, Observation):
        raise TypeError("selected_private_observation must be an Observation")
    if selected_official_observation is not None and not isinstance(
        selected_official_observation, Observation
    ):
        raise TypeError("selected_official_observation must be an Observation or None")
    if selected_pressure_observation is not None and not isinstance(
        selected_pressure_observation, Observation
    ):
        raise TypeError("selected_pressure_observation must be an Observation or None")
    _require_units(tick, "tick")

    observations = history.observations()
    selected = tuple(
        observation
        for observation in (
            selected_private_observation,
            selected_official_observation,
            selected_pressure_observation,
        )
        if observation is not None
    )
    if any(observation not in observations for observation in selected):
        raise ValueError("public expression evidence must be recorded in history")
    events_by_id = {event.event_id: event for event in history.events()}
    private_event = events_by_id.get(selected_private_observation.event_id)
    official_event = (
        events_by_id.get(selected_official_observation.event_id)
        if selected_official_observation is not None
        else None
    )
    pressure_event = (
        events_by_id.get(selected_pressure_observation.event_id)
        if selected_pressure_observation is not None
        else None
    )
    if (
        private_event is None
        or selected_private_observation.agent_id != FOCAL_AGENT_ID
        or selected_private_observation.details.get("evidence_kind") != "direct"
        or private_event.kind != "provisional_shelf_availability"
        or selected_private_observation.details.get("available_units")
        != private_event.details.get("shelf_units")
    ):
        raise ValueError("private availability evidence is inconsistent")
    if selected_official_observation is not None and (
        official_event is None
        or selected_official_observation.agent_id != FOCAL_AGENT_ID
        or selected_official_observation.details.get("evidence_kind")
        != "official_claim"
        or official_event.kind != "provisional_official_availability_claim"
        or selected_official_observation.details.get("available_units")
        != official_event.details.get("claimed_available_units")
    ):
        raise ValueError("official availability evidence is inconsistent")
    if selected_pressure_observation is not None and (
        pressure_event is None
        or selected_pressure_observation.agent_id != FOCAL_AGENT_ID
        or selected_pressure_observation.details.get("evidence_kind")
        != "social_pressure"
        or selected_pressure_observation.details.get("action")
        != "urge_public_agreement"
        or selected_pressure_observation.details.get("actor_id")
        != SUPPORTING_AGENT_ID
        or pressure_event.kind != "provisional_supporting_action"
        or pressure_event.details.get("action") != "urge_public_agreement"
        or pressure_event.details.get("actor_id") != SUPPORTING_AGENT_ID
    ):
        raise ValueError("public pressure evidence is inconsistent")
    if decision != choose_public_availability_expression(selected):
        raise ValueError("public expression decision is inconsistent with evidence")
    latest_evidence_tick = max(
        max(observation.delivery_tick for observation in selected),
        max(events_by_id[observation.event_id].tick for observation in selected),
    )
    if tick < latest_evidence_tick:
        raise ValueError("public expression cannot precede its evidence")

    event = history.record_event(
        tick=tick,
        kind="provisional_public_availability_expression",
        details={
            "actor_id": FOCAL_AGENT_ID,
            "proposition": decision.proposition,
            "expressed_units": decision.expressed_units,
            "private_source_observation_id": (
                decision.private_belief.source_observation_id
            ),
            "official_source_observation_id": (
                decision.trace.selected_official_observation_id
            ),
            "pressure_observation_id": decision.trace.selected_pressure_observation_id,
            "objective_availability_event_id": decision.private_belief.source_event_id,
        },
    )
    return PublicExpressionResolution(expression_event=event)


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


def resolve_follow_up_choice(
    *,
    history: SourceLinkedHistory,
    decision: FollowUpDecision,
    selected_handover: Observation,
    prior_resolution: AllocationResolution,
    objective_allocation: ObjectiveAllocation,
    tick: int,
) -> FollowUpResolution:
    """Resolve the provisional seek choice against remaining objective supply."""
    if not isinstance(history, SourceLinkedHistory):
        raise TypeError("history must be a SourceLinkedHistory")
    if not isinstance(decision, FollowUpDecision):
        raise TypeError("decision must be a FollowUpDecision")
    if not isinstance(decision.trace, FollowUpDecisionTrace):
        raise TypeError("decision trace must be a FollowUpDecisionTrace")
    if not isinstance(selected_handover, Observation):
        raise TypeError("selected_handover must be an Observation")
    if not isinstance(prior_resolution, AllocationResolution):
        raise TypeError("prior_resolution must be an AllocationResolution")
    if not isinstance(objective_allocation, ObjectiveAllocation):
        raise TypeError("objective_allocation must be an ObjectiveAllocation")
    _require_units(tick, "tick")

    events = history.events()
    observations = history.observations()
    availability_event = next(
        (
            event
            for event in events
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
    if prior_resolution.attempted_event not in events:
        raise ValueError("prior attempted event must be recorded in history")
    if prior_resolution.consequence_event not in events:
        raise ValueError("prior consequence event must be recorded in history")
    prior_attempt_details = prior_resolution.attempted_event.details
    prior_details = prior_resolution.consequence_event.details
    prior_requested_units = prior_attempt_details.get("requested_units")
    _require_units(prior_requested_units, "prior requested_units")
    _require_units(prior_resolution.granted_units, "prior granted_units")
    _require_units(prior_resolution.unfilled_units, "prior unfilled_units")
    if (
        prior_attempt_details.get("availability_event_id")
        != objective_allocation.availability_event_id
        or prior_details.get("attempted_event_id")
        != prior_resolution.attempted_event.event_id
        or prior_details.get("shelf_units") != objective_allocation.shelf_units
        or prior_details.get("committed_units")
        != objective_allocation.committed_units
        or prior_details.get("allocatable_units")
        != objective_allocation.allocatable_units
        or prior_details.get("requested_units") != prior_requested_units
        or prior_details.get("granted_units") != prior_resolution.granted_units
        or prior_details.get("unfilled_units") != prior_resolution.unfilled_units
        or prior_resolution.granted_units
        != min(prior_requested_units, objective_allocation.allocatable_units)
        or prior_resolution.unfilled_units
        != prior_requested_units - prior_resolution.granted_units
    ):
        raise ValueError("prior resolution evidence is inconsistent")
    if prior_resolution.granted_units > objective_allocation.allocatable_units:
        raise ValueError("prior grant exceeds objective allocation")
    if selected_handover not in observations:
        raise ValueError("selected handover must be recorded in history")
    if (
        selected_handover.agent_id != FOCAL_AGENT_ID
        or selected_handover.event_id != prior_resolution.consequence_event.event_id
        or selected_handover.details.get("evidence_kind") != "allocation_handover"
        or selected_handover.details.get("granted_units")
        != prior_resolution.granted_units
        or selected_handover.details.get("unfilled_units")
        != prior_resolution.unfilled_units
    ):
        raise ValueError("selected handover is inconsistent with prior resolution")

    trace = decision.trace
    _require_units(
        trace.observed_granted_units,
        "follow-up observed_granted_units",
    )
    _require_units(trace.required_units, "follow-up required_units")
    _require_units(trace.remaining_units, "follow-up remaining_units")
    if (
        decision.choice != "seek_remaining_allocation"
        or trace.selected_observation_id != selected_handover.observation_id
        or trace.observed_granted_units != prior_resolution.granted_units
        or trace.remaining_units
        != max(trace.required_units - prior_resolution.granted_units, 0)
    ):
        raise ValueError("follow-up decision is inconsistent with selected handover")
    if tick < max(
        prior_resolution.consequence_event.tick,
        selected_handover.delivery_tick,
    ):
        raise ValueError("follow-up resolution cannot precede its evidence")

    attempted_event = history.record_event(
        tick=tick,
        kind="provisional_follow_up_attempted",
        details={
            "choice": decision.choice,
            "selected_observation_id": selected_handover.observation_id,
            "prior_consequence_event_id": prior_resolution.consequence_event.event_id,
            "requested_units": trace.remaining_units,
        },
    )
    remaining_allocatable_units = (
        objective_allocation.allocatable_units - prior_resolution.granted_units
    )
    granted_units = min(trace.remaining_units, remaining_allocatable_units)
    unfilled_units = trace.remaining_units - granted_units
    outcome_event = history.record_event(
        tick=tick,
        kind="provisional_follow_up_resolved",
        details={
            "attempted_event_id": attempted_event.event_id,
            "prior_consequence_event_id": prior_resolution.consequence_event.event_id,
            "remaining_allocatable_units": remaining_allocatable_units,
            "requested_units": trace.remaining_units,
            "granted_units": granted_units,
            "unfilled_units": unfilled_units,
        },
    )
    return FollowUpResolution(
        attempted_event=attempted_event,
        outcome_event=outcome_event,
        granted_units=granted_units,
        unfilled_units=unfilled_units,
    )


def run_provisional_focal_life_scenario(
    *, include_public_pressure: bool = True
) -> FocalLifeScenarioEvidence:
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
    objective_availability_evidence = ObjectiveAvailabilityEvidence(
        proposition="available_units",
        units=availability_event.details["shelf_units"],
        source_event_id=availability_event.event_id,
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
        agent_id=SUPPORTING_AGENT_ID,
        event_id=resolution.attempted_event.event_id,
        source="direct sight",
        delivery_tick=3,
        details={
            "evidence_kind": "visible_allocation_request",
            "requested_units": request.requested_units,
        },
    )
    supporting_observations = history.observations_for(SUPPORTING_AGENT_ID)
    supporting_decision = choose_supporting_action(supporting_observations)
    supporting_resolution = resolve_supporting_action(
        history=history,
        decision=supporting_decision,
        selected_observation=supporting_observations[-1],
        tick=3,
    )
    history.deliver_observation(
        agent_id=FOCAL_AGENT_ID,
        event_id=resolution.consequence_event.event_id,
        source="direct handover",
        delivery_tick=3,
        details={
            "evidence_kind": "allocation_handover",
            "granted_units": resolution.granted_units,
            "unfilled_units": resolution.unfilled_units,
        },
    )
    follow_up_observations = history.observations_for(FOCAL_AGENT_ID)
    follow_up = choose_follow_up_after_allocation(follow_up_observations, need)
    follow_up_resolution = resolve_follow_up_choice(
        history=history,
        decision=follow_up,
        selected_handover=follow_up_observations[-1],
        prior_resolution=resolution,
        objective_allocation=objective_allocation,
        tick=4,
    )
    follow_up_outcome_observation = history.deliver_observation(
        agent_id=FOCAL_AGENT_ID,
        event_id=follow_up_resolution.outcome_event.event_id,
        source="direct allocation outcome",
        delivery_tick=4,
        details={
            "evidence_kind": "follow_up_allocation_outcome",
            "granted_units": follow_up_resolution.granted_units,
            "unfilled_units": follow_up_resolution.unfilled_units,
        },
    )
    focal_pressure_observation = None
    if include_public_pressure:
        focal_pressure_observation = history.deliver_observation(
            agent_id=FOCAL_AGENT_ID,
            event_id=supporting_resolution.action_event.event_id,
            source="supporting person",
            delivery_tick=4,
            details={
                "evidence_kind": "social_pressure",
                "actor_id": SUPPORTING_AGENT_ID,
                "action": supporting_decision.action,
            },
        )
    third_choice_observations = history.observations_for(FOCAL_AGENT_ID)
    third_choice = choose_after_follow_up_outcome(third_choice_observations)
    public_expression = choose_public_availability_expression(
        third_choice_observations
    )
    public_expression_resolution = resolve_public_expression(
        history=history,
        decision=public_expression,
        selected_private_observation=decision_observations[0],
        selected_official_observation=(
            decision_observations[1] if include_public_pressure else None
        ),
        selected_pressure_observation=focal_pressure_observation,
        tick=5,
    )
    return FocalLifeScenarioEvidence(
        need=need,
        objective_allocation=objective_allocation,
        objective_availability_evidence=objective_availability_evidence,
        decision_observations=decision_observations,
        request=request,
        resolution=resolution,
        supporting_observations=supporting_observations,
        supporting_decision=supporting_decision,
        supporting_resolution=supporting_resolution,
        events=history.events(),
        focal_observations=history.observations_for(FOCAL_AGENT_ID),
        follow_up_observations=follow_up_observations,
        follow_up=follow_up,
        follow_up_resolution=follow_up_resolution,
        follow_up_outcome_observation=follow_up_outcome_observation,
        focal_pressure_observation=focal_pressure_observation,
        third_choice_observations=third_choice_observations,
        third_choice=third_choice,
        private_availability_belief=public_expression.private_belief,
        public_expression=public_expression,
        public_expression_resolution=public_expression_resolution,
    )
