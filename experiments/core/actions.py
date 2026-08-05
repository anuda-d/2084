"""Attempted actions, kept separate from resolved world consequences."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from experiments.core.events import freeze_mapping


ACTION_KINDS = frozenset(
    {"travel", "work", "request_allocation", "speak", "write_diary", "read_diary", "wait"}
)


@dataclass(frozen=True)
class ActionAttempt:
    actor_id: str
    kind: str
    explanation: str
    decision_reason: str = ""
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.kind not in ACTION_KINDS:
            raise ValueError(f"unsupported action kind: {self.kind}")
        object.__setattr__(self, "parameters", freeze_mapping(self.parameters))


@dataclass(frozen=True)
class PendingAction:
    action_id: str
    attempt_event_id: str
    attempt: ActionAttempt
    started_tick: int
    completes_tick: int
