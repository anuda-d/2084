"""Agent-owned traces and claims derived only from delivered observations."""

from __future__ import annotations

from dataclasses import dataclass, replace

from simulation.events import Observation


@dataclass(frozen=True)
class InterpretedClaim:
    claim_id: str
    proposition: str
    asserted_value: int
    period_id: str | None
    origin_trace_id: str
    conflicts_with: tuple[str, ...] = ()


@dataclass(frozen=True)
class MemoryTrace:
    trace_id: str
    source_observation_id: str
    source_event_id: str
    source: str
    evidence_kind: str
    interpreted_claim_id: str
    proposition: str
    asserted_value: int
    delivery_tick: int
    period_id: str | None


@dataclass(frozen=True)
class ContextualStance:
    context: str
    proposition: str
    asserted_value: int
    source_claim_id: str
    source_trace_id: str
    source_observation_ids: tuple[str, ...]
    pressure_observation_id: str | None
    selected_tick: int


@dataclass(frozen=True)
class StanceTransition:
    transition_id: str
    agent_id: str
    tick: int
    context: str
    active: bool
    proposition: str
    asserted_value: int
    source_claim_id: str
    source_trace_id: str
    source_observation_ids: tuple[str, ...]
    pressure_observation_id: str | None
    stance_selected_tick: int


def trace_from_delivered_observation(
    observation: Observation,
    *,
    trace_id: str,
    claim_id: str,
    existing_claims: tuple[InterpretedClaim, ...],
) -> tuple[MemoryTrace, InterpretedClaim | None] | None:
    """Interpret one supported delivery without consulting objective world state."""
    evidence_kind = observation.details.get("evidence_kind")
    if evidence_kind not in {"direct_resource_claim", "official_record_version"}:
        return None

    proposition = observation.details.get("proposition")
    asserted_value = observation.details.get("asserted_value")
    period_id = observation.details.get("period_id")
    if not isinstance(proposition, str):
        return None
    if not isinstance(asserted_value, int) or isinstance(asserted_value, bool):
        return None
    if period_id is not None and not isinstance(period_id, str):
        return None

    existing_claim = next(
        (
            claim
            for claim in existing_claims
            if claim.proposition == proposition
            and claim.asserted_value == asserted_value
            and claim.period_id == period_id
        ),
        None,
    )
    interpreted_claim_id = (
        existing_claim.claim_id if existing_claim is not None else claim_id
    )
    trace = MemoryTrace(
        trace_id=trace_id,
        source_observation_id=observation.observation_id,
        source_event_id=observation.event_id,
        source=observation.source,
        evidence_kind=evidence_kind,
        interpreted_claim_id=interpreted_claim_id,
        proposition=proposition,
        asserted_value=asserted_value,
        delivery_tick=observation.delivery_tick,
        period_id=period_id,
    )
    if existing_claim is not None:
        return trace, None
    return trace, InterpretedClaim(
        claim_id=interpreted_claim_id,
        proposition=proposition,
        asserted_value=asserted_value,
        period_id=period_id,
        origin_trace_id=trace_id,
    )


def link_official_version_conflicts(
    existing_claims: tuple[InterpretedClaim, ...],
    existing_traces: tuple[MemoryTrace, ...],
    new_claim: InterpretedClaim,
    new_trace: MemoryTrace,
) -> tuple[InterpretedClaim, ...]:
    """Link only delivered official versions that disagree about one period."""
    if new_trace.evidence_kind != "official_record_version":
        return existing_claims + (new_claim,)

    trace_by_claim_id = {
        trace.interpreted_claim_id: trace for trace in existing_traces
    }
    conflicting_claim_ids = tuple(
        claim.claim_id
        for claim in existing_claims
        if (
            (trace := trace_by_claim_id.get(claim.claim_id)) is not None
            and trace.evidence_kind == "official_record_version"
            and claim.proposition == new_claim.proposition
            and claim.period_id == new_claim.period_id
            and claim.asserted_value != new_claim.asserted_value
        )
    )
    if not conflicting_claim_ids:
        return existing_claims + (new_claim,)

    linked_existing_claims = tuple(
        replace(
            claim,
            conflicts_with=claim.conflicts_with + (new_claim.claim_id,),
        )
        if claim.claim_id in conflicting_claim_ids
        else claim
        for claim in existing_claims
    )
    return linked_existing_claims + (
        replace(new_claim, conflicts_with=conflicting_claim_ids),
    )


def select_public_counter_stance(
    *,
    location: str,
    counter_location: str,
    pressure_threshold: float,
    claims: tuple[InterpretedClaim, ...],
    traces: tuple[MemoryTrace, ...],
    observations: tuple[Observation, ...],
) -> ContextualStance | None:
    """Derive the revised public stance from only delivered agent evidence."""
    if not isinstance(pressure_threshold, (int, float)) or isinstance(
        pressure_threshold, bool
    ):
        raise ValueError("pressure_threshold must be numeric")
    if not 0 <= pressure_threshold <= 1:
        raise ValueError("pressure_threshold must be between zero and one")
    if location != counter_location:
        return None

    qualifying_pressure = tuple(
        observation
        for observation in observations
        if observation.details.get("evidence_kind") == "social_pressure"
        and isinstance(observation.details.get("pressure"), (int, float))
        and not isinstance(observation.details.get("pressure"), bool)
        and observation.details["pressure"] >= pressure_threshold
    )
    if not qualifying_pressure:
        return None
    pressure = max(
        qualifying_pressure,
        key=lambda observation: (
            observation.delivery_tick,
            observation.observation_id,
        ),
    )

    observation_by_id = {
        observation.observation_id: observation for observation in observations
    }
    trace_by_id = {trace.trace_id: trace for trace in traces}
    revised_candidates: list[tuple[InterpretedClaim, MemoryTrace]] = []
    for claim in claims:
        trace = trace_by_id.get(claim.origin_trace_id)
        if trace is None or trace.evidence_kind != "official_record_version":
            continue
        source = observation_by_id.get(trace.source_observation_id)
        if (
            not claim.conflicts_with
            or source is None
            or source.details.get("previous_version_id") is None
        ):
            continue
        revised_candidates.append((claim, trace))
    if not revised_candidates:
        return None

    claim, trace = max(
        revised_candidates,
        key=lambda item: (
            item[1].delivery_tick,
            item[1].trace_id,
        ),
    )
    return ContextualStance(
        context="public_counter",
        proposition=trace.proposition,
        asserted_value=trace.asserted_value,
        source_claim_id=claim.claim_id,
        source_trace_id=trace.trace_id,
        source_observation_ids=(
            trace.source_observation_id,
            pressure.observation_id,
        ),
        pressure_observation_id=pressure.observation_id,
        selected_tick=max(trace.delivery_tick, pressure.delivery_tick),
    )


def select_private_diary_stance(
    *,
    claims: tuple[InterpretedClaim, ...],
    traces: tuple[MemoryTrace, ...],
    observations: tuple[Observation, ...],
) -> ContextualStance | None:
    """Resurface an earlier official claim only through its delivered diary read."""
    observation_by_id = {
        observation.observation_id: observation for observation in observations
    }
    trace_by_source_id = {
        trace.source_observation_id: trace for trace in traces
    }
    claim_by_id = {claim.claim_id: claim for claim in claims}
    candidates: list[tuple[Observation, InterpretedClaim, MemoryTrace]] = []
    for read in observations:
        if read.details.get("evidence_kind") != "diary_read_completed":
            continue
        source_ids = read.details.get("source_observation_ids")
        if (
            not isinstance(source_ids, (tuple, list))
            or len(source_ids) != 1
            or not isinstance(source_ids[0], str)
        ):
            continue
        trace = trace_by_source_id.get(source_ids[0])
        claim = (
            claim_by_id.get(trace.interpreted_claim_id)
            if trace is not None
            else None
        )
        source = observation_by_id.get(source_ids[0])
        later_recheck = any(
            observation.details.get("evidence_kind") == "official_record_version"
            and observation.delivery_tick > read.delivery_tick
            and observation.details.get("proposition")
            == read.details.get("proposition")
            for observation in observations
        )
        if (
            trace is None
            or claim is None
            or trace.evidence_kind != "official_record_version"
            or not claim.conflicts_with
            or source is None
            or source.details.get("previous_version_id") is not None
            or read.details.get("proposition") != claim.proposition
            or read.details.get("asserted_value") != claim.asserted_value
            or later_recheck
        ):
            continue
        candidates.append((read, claim, trace))
    if not candidates:
        return None

    read, claim, trace = max(
        candidates,
        key=lambda item: (
            item[0].delivery_tick,
            item[0].observation_id,
        ),
    )
    return ContextualStance(
        context="private_diary",
        proposition=claim.proposition,
        asserted_value=claim.asserted_value,
        source_claim_id=claim.claim_id,
        source_trace_id=trace.trace_id,
        source_observation_ids=(trace.source_observation_id, read.observation_id),
        pressure_observation_id=None,
        selected_tick=read.delivery_tick,
    )
