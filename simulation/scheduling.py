"""Deterministic scheduling primitives for the accelerated-day successor."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from simulation.time import SimulatedDayClock, SimulatedTime


class TemporalPhase(IntEnum):
    """Causal order for work due at the same simulated minute.

    The successor order is world and institutional activity, action completion,
    observation delivery, understanding updates, then newly eligible decisions.
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
        self._released_phase_by_minute: dict[int, TemporalPhase] = {}
        self._closed = False

    @property
    def clock(self) -> SimulatedDayClock:
        return self._clock

    @property
    def is_closed(self) -> bool:
        return self._closed

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
        if self._closed:
            raise RuntimeError("temporal agenda is closed")
        if item.item_id in self._known_item_ids:
            raise ValueError(f"scheduled item identity already used: {item.item_id}")
        if item.due_time < self._clock.current:
            raise ValueError("scheduled work cannot be placed before current time")
        if item.due_time > self._clock.end:
            raise ValueError("scheduled work cannot be placed beyond the day boundary")
        released_phase = self._released_phase_by_minute.get(
            item.due_time.total_minutes
        )
        if released_phase is not None and item.phase <= released_phase:
            raise ValueError(
                "scheduled work phase has already been released at this time"
            )
        self._pending_by_id[item.item_id] = item
        self._known_item_ids.add(item.item_id)
        return item

    def close(self) -> None:
        if not self._clock.is_complete:
            raise RuntimeError("temporal agenda cannot close before day end")
        if self._pending_by_id:
            raise RuntimeError("temporal agenda cannot close with pending work")
        self._closed = True

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
        """Jump if needed, then release only the next causal phase due."""

        if self._closed:
            raise RuntimeError("temporal agenda is closed")
        target = self.next_due_time
        self._clock.advance_to(target)
        due_now = tuple(
            item for item in self.pending if item.due_time == self._clock.current
        )
        if not due_now:
            return ()
        phase = due_now[0].phase
        due = tuple(item for item in due_now if item.phase == phase)
        for item in due:
            del self._pending_by_id[item.item_id]
        self._released_phase_by_minute[target.total_minutes] = phase
        return due
