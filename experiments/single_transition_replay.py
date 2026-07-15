"""Provisional replay seam for exactly one deterministic transition."""

from __future__ import annotations

from dataclasses import dataclass

from experiments.deterministic_transition import (
    GenericIntegerState,
    TransitionConfiguration,
    TransitionResult,
    apply_transition,
)
from experiments.replay_record import ReplayRecord
from experiments.source_linked_history import SourceLinkedHistory, WorldEvent


class SingleTransitionReplayInputError(ValueError):
    """Retained inputs cannot describe one deterministic transition."""


class SingleTransitionReplayMismatchError(ValueError):
    """The reproduced objective history differs from the retained record."""

    def __init__(
        self,
        *,
        recorded_events: tuple[WorldEvent, ...],
        reproduced_events: tuple[WorldEvent, ...],
    ) -> None:
        super().__init__("reproduced objective history does not match the record")
        self.recorded_events = tuple(recorded_events)
        self.reproduced_events = tuple(reproduced_events)


def _configuration_from_record(record: ReplayRecord) -> TransitionConfiguration:
    expected_fields = {"deltas", "event_kind"}
    actual_fields = set(record.configuration)
    if actual_fields != expected_fields:
        differences = sorted(actual_fields ^ expected_fields)
        raise SingleTransitionReplayInputError(
            "record configuration fields do not describe a transition: "
            f"{differences}"
        )
    try:
        return TransitionConfiguration(
            deltas=record.configuration["deltas"],
            event_kind=record.configuration["event_kind"],
        )
    except (TypeError, ValueError) as error:
        raise SingleTransitionReplayInputError(
            f"invalid transition configuration: {error}"
        ) from error


@dataclass(frozen=True, init=False)
class SingleTransitionReplay:
    """Immutable inputs capable of verifying one recorded transition."""

    initial_state: GenericIntegerState
    record: ReplayRecord

    @classmethod
    def capture(
        cls,
        *,
        initial_state: GenericIntegerState,
        record: ReplayRecord,
    ) -> "SingleTransitionReplay":
        """Retain detached immutable inputs for one transition reproduction."""
        if not isinstance(initial_state, GenericIntegerState):
            raise TypeError("initial_state must be a GenericIntegerState")
        if not isinstance(record, ReplayRecord):
            raise TypeError("record must be a ReplayRecord")
        if len(record.events) != 1:
            raise SingleTransitionReplayInputError(
                "record must contain exactly one objective event"
            )
        _configuration_from_record(record)

        replay = object.__new__(cls)
        object.__setattr__(
            replay,
            "initial_state",
            GenericIntegerState(tick=initial_state.tick, value=initial_state.value),
        )
        object.__setattr__(replay, "record", record)
        return replay

    def reproduce(self) -> TransitionResult:
        """Reproduce and verify exactly one objective transition event."""
        configuration = _configuration_from_record(self.record)
        history = SourceLinkedHistory()
        result = apply_transition(
            state=self.initial_state,
            seed=self.record.seed,
            configuration=configuration,
            history=history,
        )
        reproduced_events = history.events()
        if reproduced_events != self.record.events:
            raise SingleTransitionReplayMismatchError(
                recorded_events=self.record.events,
                reproduced_events=reproduced_events,
            )
        return result
