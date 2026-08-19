"""Agent-owned traces and claims derived only from delivered observations."""

from __future__ import annotations

from dataclasses import dataclass

from simulation.events import Observation


@dataclass(frozen=True)
class InterpretedClaim:
    claim_id: str
    proposition: str
    asserted_value: int
    period_id: str | None
    origin_trace_id: str


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
