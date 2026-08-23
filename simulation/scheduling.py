"""Deterministic scheduling primitives for the accelerated-day successor."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from simulation.time import SimulatedDayClock, SimulatedTime


class TemporalPhase(IntEnum):
    """Causal order for work due at the same simulated minute.

    The order preserves the successful legacy loop's existing boundary:
    world and institutional activity precedes action completion, then delivery,
    understanding updates, and newly eligible decisions.
    """

    SCHEDULED_WORLD = 10
    ACTION_COMPLETION = 20
    OBSERVATION_DELIVERY = 30
    UNDERSTANDING_UPDATE = 40
    DECISION = 50


@dataclass(frozen=True)
class ScheduledWork:
    """One named unit of work due at an authoritative simulated instant."""

    item_id: str
    due_time: SimulatedTime
    phase: TemporalPhase
    kind: str

    def __post_init__(self) -> None:
        if not isinstance(self.item_id, str) or not self.item_id.strip():
            raise ValueError("item_id must be a non-empty string")
        if not isinstance(self.due_time, SimulatedTime):
            raise TypeError("due_time must be SimulatedTime")
        if not isinstance(self.phase, TemporalPhase):
            raise TypeError("phase must be TemporalPhase")
        if not isinstance(self.kind, str) or not self.kind.strip():
            raise ValueError("kind must be a non-empty string")

    @property
    def ordering_key(self) -> tuple[int, int, str]:
        return (self.due_time.total_minutes, int(self.phase), self.item_id)


class TemporalAgenda:
    """Own pending work and advance a day clock without per-minute no-ops."""

    def __init__(self, clock: SimulatedDayClock) -> None:
        if not isinstance(clock, SimulatedDayClock):
            raise TypeError("clock must be SimulatedDayClock")
        self._clock = clock
        self._pending_by_id: dict[str, ScheduledWork] = {}
        self._known_item_ids: set[str] = set()

    @property
    def clock(self) -> SimulatedDayClock:
        return self._clock

    @property
    def pending(self) -> tuple[ScheduledWork, ...]:
        return tuple(
            sorted(
                self._pending_by_id.values(),
                key=lambda item: item.ordering_key,
            )
        )

    def schedule(self, item: ScheduledWork) -> ScheduledWork:
        if not isinstance(item, ScheduledWork):
            raise TypeError("item must be ScheduledWork")
        if item.item_id in self._known_item_ids:
            raise ValueError(f"scheduled item identity already used: {item.item_id}")
        if item.due_time < self._clock.current:
            raise ValueError("scheduled work cannot be placed before current time")
        if item.due_time > self._clock.end:
            raise ValueError("scheduled work cannot be placed beyond the day boundary")
        self._pending_by_id[item.item_id] = item
        self._known_item_ids.add(item.item_id)
        return item

    @property
    def next_due_time(self) -> SimulatedTime:
        pending = self.pending
        if not pending:
            return self._clock.end
        earliest = pending[0].due_time
        if earliest < self._clock.current:
            raise RuntimeError("day clock advanced past pending scheduled work")
        return earliest

    def advance_to_next_due(self) -> tuple[ScheduledWork, ...]:
        """Jump to the next due instant (or day end) and remove work due there."""

        target = self.next_due_time
        self._clock.advance_to(target)
        due = tuple(
            item for item in self.pending if item.due_time == self._clock.current
        )
        for item in due:
            del self._pending_by_id[item.item_id]
        return due
