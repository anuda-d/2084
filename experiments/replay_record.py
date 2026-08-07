"""Provisional in-memory replay record for source-linked history.

The record retains the inputs needed to reproduce an existing history without
claiming to be a persistence format or a permanent simulation schema.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from experiments.source_linked_history import (
    Observation,
    SourceLinkedHistory,
    WorldEvent,
)


REPLAY_RECORD_VERSION = 1
ImmutableValue = Any


def _require_seed(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("seed must be an integer")
    return value


def _freeze(value: Any, *, field_name: str) -> ImmutableValue:
    if value is None or isinstance(value, (bool, int, float, str, bytes)):
        return value
    if isinstance(value, Mapping):
        frozen = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{field_name} keys must be strings")
            frozen[key] = _freeze(item, field_name=field_name)
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item, field_name=field_name) for item in value)
    raise TypeError(
        f"{field_name} supports only scalar values, mappings with string keys, "
        "and sequences"
    )


def _freeze_configuration(configuration: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(configuration, Mapping):
        raise TypeError("configuration must be a mapping")
    return _freeze(configuration, field_name="configuration")


def _thaw(value: ImmutableValue) -> Any:
    """Return a detached structured-data copy of an immutable value."""
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _require_record_keys(
    value: Any,
    *,
    field_name: str,
    expected: set[str],
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    actual = set(value)
    if actual != expected:
        differences = sorted(actual ^ expected)
        raise ValueError(f"{field_name} has missing or unexpected fields: {differences}")
    return value


def _require_records(value: Any, *, field_name: str) -> list[Any] | tuple[Any, ...]:
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{field_name} must be a sequence")
    return value


@dataclass(frozen=True, init=False)
class ReplayRecord:
    """Immutable seed, configuration, events, and observations for one run."""

    seed: int
    configuration: Mapping[str, ImmutableValue]
    events: Tuple[WorldEvent, ...]
    observations: Tuple[Observation, ...]

    @classmethod
    def capture(
        cls,
        *,
        seed: int,
        configuration: Mapping[str, Any],
        history: SourceLinkedHistory,
    ) -> "ReplayRecord":
        """Capture a detached immutable record from an existing history."""
        if not isinstance(history, SourceLinkedHistory):
            raise TypeError("history must be a SourceLinkedHistory")

        record = object.__new__(cls)
        object.__setattr__(record, "seed", _require_seed(seed))
        object.__setattr__(
            record,
            "configuration",
            _freeze_configuration(configuration),
        )
        object.__setattr__(record, "events", history.events())
        object.__setattr__(record, "observations", history.observations())
        return record

    def to_data(self) -> Mapping[str, Any]:
        """Return a detached deterministic structured-data representation."""
        return {
            "version": REPLAY_RECORD_VERSION,
            "seed": self.seed,
            "configuration": _thaw(self.configuration),
            "events": [
                {
                    "event_id": event.event_id,
                    "tick": event.tick,
                    "kind": event.kind,
                    "details": _thaw(event.details),
                }
                for event in self.events
            ],
            "observations": [
                {
                    "observation_id": observation.observation_id,
                    "agent_id": observation.agent_id,
                    "event_id": observation.event_id,
                    "source": observation.source,
                    "delivery_tick": observation.delivery_tick,
                    "details": _thaw(observation.details),
                }
                for observation in self.observations
            ],
        }

    @classmethod
    def from_data(cls, value: Mapping[str, Any]) -> "ReplayRecord":
        """Validate structured replay input atomically and return a record."""
        data = _require_record_keys(
            value,
            field_name="replay record",
            expected={"version", "seed", "configuration", "events", "observations"},
        )
        if (
            not isinstance(data["version"], int)
            or isinstance(data["version"], bool)
            or data["version"] != REPLAY_RECORD_VERSION
        ):
            raise ValueError(f"version must be {REPLAY_RECORD_VERSION}")

        seed = _require_seed(data["seed"])
        configuration = _freeze_configuration(data["configuration"])
        history = SourceLinkedHistory()

        for index, raw_event in enumerate(
            _require_records(data["events"], field_name="events")
        ):
            event_data = _require_record_keys(
                raw_event,
                field_name=f"events[{index}]",
                expected={"event_id", "tick", "kind", "details"},
            )
            event = history.record_event(
                tick=event_data["tick"],
                kind=event_data["kind"],
                details=event_data["details"],
            )
            if event.event_id != event_data["event_id"]:
                raise ValueError(
                    f"events[{index}].event_id must be {event.event_id}"
                )

        for index, raw_observation in enumerate(
            _require_records(data["observations"], field_name="observations")
        ):
            observation_data = _require_record_keys(
                raw_observation,
                field_name=f"observations[{index}]",
                expected={
                    "observation_id",
                    "agent_id",
                    "event_id",
                    "source",
                    "delivery_tick",
                    "details",
                },
            )
            observation = history.deliver_observation(
                agent_id=observation_data["agent_id"],
                event_id=observation_data["event_id"],
                source=observation_data["source"],
                delivery_tick=observation_data["delivery_tick"],
                details=observation_data["details"],
            )
            if observation.observation_id != observation_data["observation_id"]:
                raise ValueError(
                    "observations"
                    f"[{index}].observation_id must be {observation.observation_id}"
                )

        return cls.capture(
            seed=seed,
            configuration=configuration,
            history=history,
        )

    def restore_history(self) -> SourceLinkedHistory:
        """Restore a new history through its public invariant-enforcing methods."""
        return type(self).from_data(self.to_data())._validated_history()

    def _validated_history(self) -> SourceLinkedHistory:
        history = SourceLinkedHistory()
        for event in self.events:
            restored = history.record_event(
                tick=event.tick,
                kind=event.kind,
                details=event.details,
            )
            if restored.event_id != event.event_id:
                raise ValueError(f"event_id must be {restored.event_id}")
        for observation in self.observations:
            restored = history.deliver_observation(
                agent_id=observation.agent_id,
                event_id=observation.event_id,
                source=observation.source,
                delivery_tick=observation.delivery_tick,
                details=observation.details,
            )
            if restored.observation_id != observation.observation_id:
                raise ValueError(f"observation_id must be {restored.observation_id}")
        return history
