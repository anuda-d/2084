"""Small structured claims derived only from delivered observations."""

from __future__ import annotations

from dataclasses import dataclass, replace

from experiments.core.events import Observation


@dataclass(frozen=True)
class Belief:
    belief_id: str
    proposition: str
    asserted_value: int
    source_observation_ids: tuple[str, ...]
    confidence: float
    last_updated_tick: int
    context: str
    conflicts_with: tuple[str, ...] = ()


@dataclass(frozen=True)
class BeliefTransition:
    transition_id: str
    agent_id: str
    tick: int
    source_observation_id: str
    belief_id: str
    proposition: str
    asserted_value: int
    confidence: float
    context: str
    conflicts_with: tuple[str, ...]


def belief_from_claim_observation(
    observation: Observation, *, belief_id: str
) -> Belief | None:
    """Apply the inspectable evidence rules for the first structured claim."""
    evidence_kind = observation.details.get("evidence_kind")
    if evidence_kind not in {"direct_resource_claim", "official_resource_claim"}:
        return None
    is_direct = evidence_kind == "direct_resource_claim"
    return Belief(
        belief_id=belief_id,
        proposition=observation.details["proposition"],
        asserted_value=observation.details["asserted_value"],
        source_observation_ids=(observation.observation_id,),
        confidence=0.9 if is_direct else 0.65,
        last_updated_tick=observation.delivery_tick,
        context="private" if is_direct else "public",
    )


def link_conflicts(existing: list[Belief], incoming: Belief) -> Belief:
    """Retain incompatible claims and add explicit reciprocal links."""
    conflicting_indexes = [
        index
        for index, belief in enumerate(existing)
        if belief.proposition == incoming.proposition
        and belief.asserted_value != incoming.asserted_value
    ]
    if not conflicting_indexes:
        return incoming
    incoming = replace(
        incoming,
        conflicts_with=tuple(existing[index].belief_id for index in conflicting_indexes),
    )
    for index in conflicting_indexes:
        belief = existing[index]
        existing[index] = replace(
            belief,
            conflicts_with=belief.conflicts_with + (incoming.belief_id,),
        )
    return incoming
