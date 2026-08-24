"""Authoritative wall-clock-independent time primitives for accelerated days."""

from __future__ import annotations

from dataclasses import dataclass


MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
MINUTES_PER_DAY = MINUTES_PER_HOUR * HOURS_PER_DAY


def _non_negative_integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


@dataclass(frozen=True, order=True)
class SimulatedTime:
    """One totally ordered instant represented only by elapsed whole minutes."""

    total_minutes: int

    def __post_init__(self) -> None:
        _non_negative_integer(self.total_minutes, "total_minutes")

    @classmethod
    def from_day_time(
        cls,
        *,
        day_index: int,
        hour: int,
        minute: int,
    ) -> SimulatedTime:
        day_index = _non_negative_integer(day_index, "day_index")
        hour = _non_negative_integer(hour, "hour")
        minute = _non_negative_integer(minute, "minute")
        if hour >= HOURS_PER_DAY:
            raise ValueError("hour must be less than 24")
        if minute >= MINUTES_PER_HOUR:
            raise ValueError("minute must be less than 60")
        return cls(
            day_index * MINUTES_PER_DAY + hour * MINUTES_PER_HOUR + minute
        )

    @property
    def day_index(self) -> int:
        return self.total_minutes // MINUTES_PER_DAY

    @property
    def minute_of_day(self) -> int:
        return self.total_minutes % MINUTES_PER_DAY

    @property
    def hour(self) -> int:
        return self.minute_of_day // MINUTES_PER_HOUR

    @property
    def minute(self) -> int:
        return self.minute_of_day % MINUTES_PER_HOUR

    @property
    def label(self) -> str:
        return f"Day {self.day_index} {self.hour:02d}:{self.minute:02d}"

    def plus_minutes(self, minutes: int) -> SimulatedTime:
        minutes = _non_negative_integer(minutes, "minutes")
        return SimulatedTime(self.total_minutes + minutes)

    def to_data(self) -> dict[str, object]:
        return {
            "total_minutes": self.total_minutes,
            "day_index": self.day_index,
            "hour": self.hour,
            "minute": self.minute,
            "label": self.label,
        }


class SimulatedDayClock:
    """Own monotonic advancement from one explicit start to one day boundary."""

    def __init__(self, start: SimulatedTime) -> None:
        if not isinstance(start, SimulatedTime):
            raise TypeError("start must be SimulatedTime")
        self._start = start
        self._current = start
        self._end = start.plus_minutes(MINUTES_PER_DAY)

    @property
    def start(self) -> SimulatedTime:
        return self._start

    @property
    def current(self) -> SimulatedTime:
        return self._current

    @property
    def end(self) -> SimulatedTime:
        return self._end

    @property
    def is_complete(self) -> bool:
        return self._current == self._end

    def advance_to(self, target: SimulatedTime) -> SimulatedTime:
        if not isinstance(target, SimulatedTime):
            raise TypeError("target must be SimulatedTime")
        if target < self._current:
            raise ValueError("simulated time cannot move backward")
        if target > self._end:
            raise ValueError("simulated time cannot advance beyond the day boundary")
        self._current = target
        return self._current

    def advance_by(self, minutes: int) -> SimulatedTime:
        return self.advance_to(self._current.plus_minutes(minutes))

    def to_data(self) -> dict[str, object]:
        return {
            "start": self._start.to_data(),
            "current": self._current.to_data(),
            "end": self._end.to_data(),
            "duration_minutes": MINUTES_PER_DAY,
            "reached_end_boundary": self.is_complete,
        }
