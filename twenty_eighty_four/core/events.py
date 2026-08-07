"""Immutable event records for the living simulation."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


def freeze_mapping(values: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    """Detach supported structured data from mutable caller-owned containers."""
    def freeze(value: Any) -> Any:
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, Mapping):
            return MappingProxyType({str(key): freeze(item) for key, item in value.items()})
        if isinstance(value, (list, tuple)):
            return tuple(freeze(item) for item in value)
        raise TypeError(f"unsupported event detail value: {type(value).__name__}")

    return freeze(values or {})


def to_plain_data(value: Any) -> Any:
    """Convert immutable engine records to JSON-compatible detached data."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return {key: to_plain_data(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_plain_data(item) for item in value]
    raise TypeError(f"unsupported serialized value: {type(value).__name__}")


@dataclass(frozen=True)
class Event:
    event_id: str
    tick: int
    kind: str
    actor_id: str | None
    action_id: str | None
    caused_by: tuple[str, ...]
    details: Mapping[str, Any]


@dataclass(frozen=True)
class Observation:
    observation_id: str
    agent_id: str
    event_id: str
    source: str
    delivery_tick: int
    details: Mapping[str, Any]


class EventLog:
    """Append-only event history with deterministic identifiers."""

    def __init__(self) -> None:
        self._events: list[Event] = []
        self._events_by_id: dict[str, Event] = {}
        self._observations: list[Observation] = []

    @property
    def events(self) -> tuple[Event, ...]:
        return tuple(self._events)

    @property
    def observations(self) -> tuple[Observation, ...]:
        return tuple(self._observations)

    def record(
        self,
        *,
        tick: int,
        kind: str,
        actor_id: str | None = None,
        action_id: str | None = None,
        caused_by: tuple[str, ...] = (),
        details: Mapping[str, Any] | None = None,
    ) -> Event:
        event = Event(
            event_id=f"event-{len(self._events) + 1:04d}",
            tick=tick,
            kind=kind,
            actor_id=actor_id,
            action_id=action_id,
            caused_by=tuple(caused_by),
            details=freeze_mapping(details),
        )
        self._events.append(event)
        self._events_by_id[event.event_id] = event
        return event

    def deliver(
        self,
        *,
        agent_id: str,
        event_id: str,
        source: str,
        delivery_tick: int,
        details: Mapping[str, Any] | None = None,
    ) -> Observation:
        event = self._events_by_id.get(event_id)
        if event is None:
            raise ValueError(f"unknown event_id: {event_id}")
        if delivery_tick < event.tick:
            raise ValueError("observation cannot be delivered before its source event")
        observation = Observation(
            observation_id=f"observation-{len(self._observations) + 1:04d}",
            agent_id=agent_id,
            event_id=event_id,
            source=source,
            delivery_tick=delivery_tick,
            details=freeze_mapping(details),
        )
        self._observations.append(observation)
        return observation
