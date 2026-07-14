"""Provisional event history and source-linked observation experiment.

This module tests one boundary only: objective events are recorded without being
rewritten, while information about those events is delivered to named agents.
It is deliberately not a simulation architecture or persistence format.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple


ImmutableValue = Any


def _require_name(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a nonempty string")
    return value


def _require_tick(value: int, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative integer")
    return value


def _freeze(value: Any) -> ImmutableValue:
    """Copy supported values into recursively immutable containers."""
    if value is None or isinstance(value, (bool, int, float, str, bytes)):
        return value
    if isinstance(value, Mapping):
        frozen = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("detail keys must be strings")
            frozen[key] = _freeze(item)
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    raise TypeError(
        "details support only scalar values, mappings with string keys, and sequences"
    )


def _freeze_details(details: Mapping[str, Any] | None) -> Mapping[str, ImmutableValue]:
    if details is None:
        return MappingProxyType({})
    if not isinstance(details, Mapping):
        raise TypeError("details must be a mapping")
    return _freeze(details)


@dataclass(frozen=True)
class WorldEvent:
    """An objective record that something occurred in the world."""

    event_id: str
    tick: int
    kind: str
    details: Mapping[str, ImmutableValue]


@dataclass(frozen=True)
class Observation:
    """Information about an event delivered to one specific agent."""

    observation_id: str
    agent_id: str
    event_id: str
    source: str
    delivery_tick: int
    details: Mapping[str, ImmutableValue]


class SourceLinkedHistory:
    """Append-only in-memory history for this bounded experiment."""

    def __init__(self) -> None:
        self._events = []
        self._events_by_id = {}
        self._observations = []

    def record_event(
        self,
        *,
        tick: int,
        kind: str,
        details: Mapping[str, Any] | None = None,
    ) -> WorldEvent:
        event = WorldEvent(
            event_id=f"event-{len(self._events) + 1:04d}",
            tick=_require_tick(tick, "tick"),
            kind=_require_name(kind, "kind"),
            details=_freeze_details(details),
        )
        self._events.append(event)
        self._events_by_id[event.event_id] = event
        return event

    def deliver_observation(
        self,
        *,
        agent_id: str,
        event_id: str,
        source: str,
        delivery_tick: int,
        details: Mapping[str, Any] | None = None,
    ) -> Observation:
        _require_name(agent_id, "agent_id")
        _require_name(event_id, "event_id")
        _require_name(source, "source")
        _require_tick(delivery_tick, "delivery_tick")

        event = self._events_by_id.get(event_id)
        if event is None:
            raise ValueError(f"unknown event_id: {event_id}")
        if delivery_tick < event.tick:
            raise ValueError("an observation cannot arrive before its event occurred")

        observation = Observation(
            observation_id=f"observation-{len(self._observations) + 1:04d}",
            agent_id=agent_id,
            event_id=event_id,
            source=source,
            delivery_tick=delivery_tick,
            details=_freeze_details(details),
        )
        self._observations.append(observation)
        return observation

    def events(self) -> Tuple[WorldEvent, ...]:
        """Return the complete objective history as an immutable sequence."""
        return tuple(self._events)

    def observations(self) -> Tuple[Observation, ...]:
        """Return all observations for an omniscient development consumer."""
        return tuple(self._observations)

    def observations_for(self, agent_id: str) -> Tuple[Observation, ...]:
        """Return only observations delivered to the named agent."""
        _require_name(agent_id, "agent_id")
        return tuple(
            observation
            for observation in self._observations
            if observation.agent_id == agent_id
        )
