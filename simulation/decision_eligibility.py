"""Explicit decision-trigger eligibility for the accelerated-day successor."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from simulation.scheduling import ScheduledWork, TemporalAgenda, TemporalPhase
from simulation.time import SimulatedTime


SAFE_FAILURE_RETRY_MINUTES = 30
DECISION_ELIGIBILITY_WORK_KIND = "decision_eligibility"


class DecisionTriggerKind(str, Enum):
    INITIAL_ACTIVATION = "initial_activation"
    ACTION_RESULT = "action_result"
    OBSERVATION_DELIVERED = "observation_delivered"
    SCHEDULED_WAKE = "scheduled_wake"
    SAFE_FAILURE_RETRY = "safe_failure_retry"


@dataclass(frozen=True)
class DecisionTrigger:
    kind: DecisionTriggerKind
    source_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, DecisionTriggerKind):
            raise TypeError("kind must be DecisionTriggerKind")
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("source_id must be a non-empty string")

    @property
    def ordering_key(self) -> tuple[str, str]:
        return (self.kind.value, self.source_id)


@dataclass(frozen=True)
class EligibleDecision:
    actor_id: str
    due_time: SimulatedTime
    triggers: tuple[DecisionTrigger, ...]
    scheduled_work_id: str


class DecisionEligibility:
    """Coalesce explicit causes into at most one actor decision per minute."""

    def __init__(self, agenda: TemporalAgenda) -> None:
        if not isinstance(agenda, TemporalAgenda):
            raise TypeError("agenda must be TemporalAgenda")
        self._agenda = agenda
        self._work_by_actor_time: dict[tuple[str, int], ScheduledWork] = {}
        self._triggers_by_work_id: dict[
            str, dict[tuple[str, str], DecisionTrigger]
        ] = {}

    @property
    def pending_count(self) -> int:
        return len(self._work_by_actor_time)

    def request(
        self,
        *,
        actor_id: str,
        due_time: SimulatedTime,
        trigger: DecisionTrigger,
    ) -> ScheduledWork:
        if not isinstance(actor_id, str) or not actor_id.strip():
            raise ValueError("actor_id must be a non-empty string")
        if not isinstance(due_time, SimulatedTime):
            raise TypeError("due_time must be SimulatedTime")
        if not isinstance(trigger, DecisionTrigger):
            raise TypeError("trigger must be DecisionTrigger")

        actor_time = (actor_id, due_time.total_minutes)
        work = self._work_by_actor_time.get(actor_time)
        if work is None:
            work = ScheduledWork(
                item_id=(
                    f"decision:{due_time.total_minutes}:{actor_id}"
                ),
                due_time=due_time,
                phase=TemporalPhase.DECISION,
                kind=DECISION_ELIGIBILITY_WORK_KIND,
            )
            self._agenda.schedule(work)
            self._work_by_actor_time[actor_time] = work
            self._triggers_by_work_id[work.item_id] = {}

        self._triggers_by_work_id[work.item_id][trigger.ordering_key] = trigger
        return work

    def request_safe_failure_retry(
        self,
        *,
        actor_id: str,
        failed_at: SimulatedTime,
        failure_id: str,
    ) -> ScheduledWork | None:
        if not isinstance(actor_id, str) or not actor_id.strip():
            raise ValueError("actor_id must be a non-empty string")
        if not isinstance(failed_at, SimulatedTime):
            raise TypeError("failed_at must be SimulatedTime")
        if not isinstance(failure_id, str) or not failure_id.strip():
            raise ValueError("failure_id must be a non-empty string")
        if failed_at != self._agenda.clock.current:
            raise ValueError("failed_at must equal current simulated time")
        retry_at = failed_at.plus_minutes(SAFE_FAILURE_RETRY_MINUTES)
        if retry_at > self._agenda.clock.end:
            return None
        return self.request(
            actor_id=actor_id,
            due_time=retry_at,
            trigger=DecisionTrigger(
                kind=DecisionTriggerKind.SAFE_FAILURE_RETRY,
                source_id=failure_id,
            ),
        )

    def consume(self, work: ScheduledWork) -> EligibleDecision:
        if not isinstance(work, ScheduledWork):
            raise TypeError("work must be ScheduledWork")
        if (
            work.kind != DECISION_ELIGIBILITY_WORK_KIND
            or work.phase is not TemporalPhase.DECISION
        ):
            raise ValueError("work is not a decision-eligibility item")
        if work in self._agenda.pending:
            raise ValueError("decision-eligibility item has not been released")
        if work.due_time != self._agenda.clock.current:
            raise ValueError("decision-eligibility item is not at current time")
        triggers_by_key = self._triggers_by_work_id.get(work.item_id)
        if triggers_by_key is None:
            raise ValueError("decision-eligibility item is unknown or already consumed")
        registered = self._work_by_actor_time.get(
            (self._actor_id_from(work), work.due_time.total_minutes)
        )
        if registered != work:
            raise ValueError("decision-eligibility item does not match registration")

        actor_id = self._actor_id_from(work)
        del self._triggers_by_work_id[work.item_id]
        del self._work_by_actor_time[(actor_id, work.due_time.total_minutes)]
        return EligibleDecision(
            actor_id=actor_id,
            due_time=work.due_time,
            triggers=tuple(
                sorted(
                    triggers_by_key.values(),
                    key=lambda trigger: trigger.ordering_key,
                )
            ),
            scheduled_work_id=work.item_id,
        )

    @staticmethod
    def _actor_id_from(work: ScheduledWork) -> str:
        prefix = f"decision:{work.due_time.total_minutes}:"
        if not work.item_id.startswith(prefix):
            raise ValueError("decision-eligibility item identity is invalid")
        actor_id = work.item_id[len(prefix):]
        if not actor_id:
            raise ValueError("decision-eligibility item has no actor identity")
        return actor_id
