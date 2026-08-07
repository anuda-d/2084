"""Provisional deterministic transition over a generic integer state.

This experiment records its one transition at the prior state's tick plus one.
That local rule does not impose repository-wide monotonic event chronology.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

from experiments.source_linked_history import SourceLinkedHistory, WorldEvent


def _require_integer(value: int, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    return value


@dataclass(frozen=True)
class GenericIntegerState:
    """The deliberately generic immutable state used by this experiment."""

    tick: int
    value: int

    def __post_init__(self) -> None:
        _require_integer(self.tick, "tick")
        if self.tick < 0:
            raise ValueError("tick must be a nonnegative integer")
        _require_integer(self.value, "value")


@dataclass(frozen=True, init=False)
class TransitionConfiguration:
    """Detached immutable choices and objective event kind."""

    deltas: Tuple[int, ...]
    event_kind: str

    def __init__(self, *, deltas: Sequence[int], event_kind: str) -> None:
        if not isinstance(deltas, (list, tuple)) or not deltas:
            raise ValueError("deltas must be a nonempty ordered sequence")
        detached_deltas = tuple(
            _require_integer(delta, f"deltas[{index}]")
            for index, delta in enumerate(deltas)
        )
        if not isinstance(event_kind, str) or not event_kind.strip():
            raise ValueError("event_kind must be a nonempty string")
        object.__setattr__(self, "deltas", detached_deltas)
        object.__setattr__(self, "event_kind", event_kind)


@dataclass(frozen=True)
class TransitionResult:
    """The next immutable state and the objective event that records it."""

    next_state: GenericIntegerState
    event: WorldEvent


def apply_transition(
    *,
    state: GenericIntegerState,
    seed: int,
    configuration: TransitionConfiguration,
    history: SourceLinkedHistory,
) -> TransitionResult:
    """Apply exactly one deterministic transition and record its event."""
    if not isinstance(state, GenericIntegerState):
        raise TypeError("state must be a GenericIntegerState")
    _require_integer(seed, "seed")
    if not isinstance(configuration, TransitionConfiguration):
        raise TypeError("configuration must be a TransitionConfiguration")
    if not isinstance(history, SourceLinkedHistory):
        raise TypeError("history must be a SourceLinkedHistory")

    selected_delta = configuration.deltas[seed % len(configuration.deltas)]
    next_state = GenericIntegerState(
        tick=state.tick + 1,
        value=state.value + selected_delta,
    )
    event = history.record_event(
        tick=next_state.tick,
        kind=configuration.event_kind,
        details={
            "before_value": state.value,
            "selected_delta": selected_delta,
            "after_value": next_state.value,
        },
    )
    return TransitionResult(next_state=next_state, event=event)
