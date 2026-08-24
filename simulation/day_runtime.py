"""One-shot executor for an accelerated simulated day agenda."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from simulation.decision_eligibility import (
    DECISION_ELIGIBILITY_WORK_KIND,
    DecisionEligibility,
    DecisionTrigger,
    EligibleDecision,
)
from simulation.scheduling import ScheduledWork, TemporalAgenda
from simulation.time import SimulatedDayClock, SimulatedTime


DayWorkHandler = Callable[[ScheduledWork, "DayWorkContext"], None]
DayDecisionHandler = Callable[[EligibleDecision, "DayWorkContext"], None]
DayTimeObserver = Callable[[SimulatedTime], None]
MAX_MODEL_DECISION_CALLS_PER_DAY = 128


class ModelDecisionCallLimitError(RuntimeError):
    """A configured model-backed actor would exceed the approved day limit."""


class DayWorkContext:
    """Restricted handler authority: inspect time and schedule validated work."""

    def __init__(
        self,
        *,
        current: SimulatedTime,
        end: SimulatedTime,
        schedule: Callable[[ScheduledWork], ScheduledWork],
        request_decision: Callable[..., ScheduledWork],
        request_safe_failure_retry: Callable[..., ScheduledWork | None],
    ) -> None:
        self._current = current
        self._end = end
        self._schedule = schedule
        self._request_decision = request_decision
        self._request_safe_failure_retry = request_safe_failure_retry

    @property
    def current(self) -> SimulatedTime:
        return self._current

    @property
    def end(self) -> SimulatedTime:
        return self._end

    def schedule(self, work: ScheduledWork) -> ScheduledWork:
        return self._schedule(work)

    def request_decision(
        self,
        *,
        actor_id: str,
        due_time: SimulatedTime,
        trigger: DecisionTrigger,
    ) -> ScheduledWork:
        return self._request_decision(
            actor_id=actor_id,
            due_time=due_time,
            trigger=trigger,
        )

    def request_safe_failure_retry(
        self,
        *,
        actor_id: str,
        failure_id: str,
    ) -> ScheduledWork | None:
        return self._request_safe_failure_retry(
            actor_id=actor_id,
            failure_id=failure_id,
        )


@dataclass(frozen=True)
class QuietSpan:
    start: SimulatedTime
    end: SimulatedTime

    @property
    def duration_minutes(self) -> int:
        return self.end.total_minutes - self.start.total_minutes

    def to_data(self) -> dict[str, object]:
        return {
            "start": self.start.to_data(),
            "end": self.end.to_data(),
            "duration_minutes": self.duration_minutes,
        }


@dataclass(frozen=True)
class ExecutedWorkEvidence:
    sequence: int
    item_id: str
    due_time: SimulatedTime
    phase: str
    kind: str

    def to_data(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "item_id": self.item_id,
            "due_time": self.due_time.to_data(),
            "phase": self.phase,
            "kind": self.kind,
        }


@dataclass(frozen=True)
class DecisionCountEvidence:
    actor_id: str
    count: int
    model_bounded: bool

    def to_data(self) -> dict[str, object]:
        return {
            "actor_id": self.actor_id,
            "count": self.count,
            "model_bounded": self.model_bounded,
        }


@dataclass(frozen=True)
class DayRuntimeFailureEvidence:
    failure_type: str
    last_committed_time: SimulatedTime
    failed_time: SimulatedTime
    committed_work_count: int
    released_uncommitted_count: int
    pending_work_count: int

    def to_data(self) -> dict[str, object]:
        return {
            "failure_type": self.failure_type,
            "last_committed_time": self.last_committed_time.to_data(),
            "failed_time": self.failed_time.to_data(),
            "committed_work_count": self.committed_work_count,
            "released_uncommitted_count": self.released_uncommitted_count,
            "pending_work_count": self.pending_work_count,
        }


@dataclass(frozen=True)
class DayRunSummary:
    start: SimulatedTime
    current: SimulatedTime
    end: SimulatedTime
    executed_work: tuple[ExecutedWorkEvidence, ...]
    quiet_spans: tuple[QuietSpan, ...]
    decision_counts: tuple[DecisionCountEvidence, ...]
    reached_end_boundary: bool
    runtime_failure: DayRuntimeFailureEvidence | None

    def to_data(self) -> dict[str, object]:
        return {
            "start": self.start.to_data(),
            "current": self.current.to_data(),
            "end": self.end.to_data(),
            "executed_work": [item.to_data() for item in self.executed_work],
            "quiet_spans": [span.to_data() for span in self.quiet_spans],
            "decision_counts": [
                decision_count.to_data()
                for decision_count in self.decision_counts
            ],
            "decision_counts_by_actor": {
                decision_count.actor_id: decision_count.count
                for decision_count in self.decision_counts
            },
            "executed_work_count": len(self.executed_work),
            "quiet_span_count": len(self.quiet_spans),
            "reached_end_boundary": self.reached_end_boundary,
            "runtime_failure": (
                self.runtime_failure.to_data()
                if self.runtime_failure is not None
                else None
            ),
        }


class AcceleratedDayRuntime:
    """Dispatch registered work until exact day end or terminal failure."""

    def __init__(
        self,
        *,
        start: SimulatedTime,
        handlers: Mapping[str, DayWorkHandler],
        decision_handler: DayDecisionHandler | None = None,
        model_backed_actor_ids: tuple[str, ...] = (),
        on_time_advanced: DayTimeObserver | None = None,
    ) -> None:
        if not isinstance(start, SimulatedTime):
            raise TypeError("start must be SimulatedTime")
        if not isinstance(handlers, Mapping):
            raise TypeError("handlers must be a mapping")
        copied_handlers: dict[str, DayWorkHandler] = {}
        for kind, handler in handlers.items():
            if not isinstance(kind, str) or not kind.strip():
                raise ValueError("handler kind must be a non-empty string")
            if not callable(handler):
                raise TypeError("day work handler must be callable")
            if kind == DECISION_ELIGIBILITY_WORK_KIND:
                raise ValueError(
                    "decision eligibility uses the dedicated decision handler"
                )
            copied_handlers[kind] = handler
        if decision_handler is not None and not callable(decision_handler):
            raise TypeError("decision_handler must be callable")
        if on_time_advanced is not None and not callable(on_time_advanced):
            raise TypeError("on_time_advanced must be callable")
        if not isinstance(model_backed_actor_ids, tuple):
            raise TypeError("model_backed_actor_ids must be a tuple")
        if any(
            not isinstance(actor_id, str) or not actor_id.strip()
            for actor_id in model_backed_actor_ids
        ):
            raise ValueError(
                "model-backed actor identities must be non-empty strings"
            )
        if len(set(model_backed_actor_ids)) != len(model_backed_actor_ids):
            raise ValueError("model-backed actor identities must be unique")

        self._clock = SimulatedDayClock(start)
        self._agenda = TemporalAgenda(self._clock)
        self._decision_eligibility = DecisionEligibility(self._agenda)
        self._handlers = copied_handlers
        self._decision_handler = decision_handler
        self._on_time_advanced = on_time_advanced
        self._model_backed_actor_ids = frozenset(model_backed_actor_ids)
        self._decision_counts_by_actor: dict[str, int] = {}
        self._executed_work: list[ExecutedWorkEvidence] = []
        self._quiet_spans: list[QuietSpan] = []
        self._runtime_failure: DayRuntimeFailureEvidence | None = None
        self._completed = False

    @property
    def start(self) -> SimulatedTime:
        return self._clock.start

    @property
    def current(self) -> SimulatedTime:
        return self._clock.current

    @property
    def end(self) -> SimulatedTime:
        return self._clock.end

    @property
    def is_registration_closed(self) -> bool:
        return self._agenda.is_closed or self._runtime_failure is not None

    @property
    def is_complete(self) -> bool:
        return (
            self._completed
            and self._clock.is_complete
            and self._agenda.is_closed
            and self._runtime_failure is None
        )

    @property
    def runtime_failure(self) -> DayRuntimeFailureEvidence | None:
        return self._runtime_failure

    @property
    def pending_decision_count(self) -> int:
        return self._decision_eligibility.pending_count

    def schedule(self, work: ScheduledWork) -> ScheduledWork:
        if self._runtime_failure is not None:
            raise RuntimeError("accelerated day stopped after a runtime failure")
        return self._agenda.schedule(work)

    def request_decision(
        self,
        *,
        actor_id: str,
        due_time: SimulatedTime,
        trigger: DecisionTrigger,
    ) -> ScheduledWork:
        if self._runtime_failure is not None:
            raise RuntimeError("accelerated day stopped after a runtime failure")
        return self._decision_eligibility.request(
            actor_id=actor_id,
            due_time=due_time,
            trigger=trigger,
        )

    def request_safe_failure_retry(
        self,
        *,
        actor_id: str,
        failure_id: str,
    ) -> ScheduledWork | None:
        if self._runtime_failure is not None:
            raise RuntimeError("accelerated day stopped after a runtime failure")
        return self._decision_eligibility.request_safe_failure_retry(
            actor_id=actor_id,
            failed_at=self._clock.current,
            failure_id=failure_id,
        )

    def summary(self) -> DayRunSummary:
        return DayRunSummary(
            start=self._clock.start,
            current=self._clock.current,
            end=self._clock.end,
            executed_work=tuple(self._executed_work),
            quiet_spans=tuple(self._quiet_spans),
            decision_counts=tuple(
                DecisionCountEvidence(
                    actor_id=actor_id,
                    count=self._decision_counts_by_actor.get(actor_id, 0),
                    model_bounded=actor_id in self._model_backed_actor_ids,
                )
                for actor_id in sorted(
                    set(self._decision_counts_by_actor)
                    | self._model_backed_actor_ids
                )
            ),
            reached_end_boundary=self.is_complete,
            runtime_failure=self._runtime_failure,
        )

    def run(self) -> DayRunSummary:
        if self._runtime_failure is not None:
            raise RuntimeError("accelerated day stopped after a runtime failure")
        if self.is_complete:
            return self.summary()

        while True:
            previous_time = self._clock.current
            try:
                batch = self._agenda.advance_to_next_due()
            except Exception as error:
                self._record_failure(error, released_uncommitted_count=0)
                raise

            if self._clock.current > previous_time:
                if self._on_time_advanced is not None:
                    try:
                        self._on_time_advanced(self._clock.current)
                    except Exception as error:
                        self._record_failure(
                            error,
                            released_uncommitted_count=len(batch),
                        )
                        raise
                self._quiet_spans.append(
                    QuietSpan(start=previous_time, end=self._clock.current)
                )

            if not batch:
                try:
                    self._agenda.close()
                except Exception as error:
                    self._record_failure(error, released_uncommitted_count=0)
                    raise
                self._completed = True
                return self.summary()

            for index, work in enumerate(batch):
                try:
                    context = DayWorkContext(
                        current=self._clock.current,
                        end=self._clock.end,
                        schedule=self.schedule,
                        request_decision=self.request_decision,
                        request_safe_failure_retry=(
                            self.request_safe_failure_retry
                        ),
                    )
                    if work.kind == DECISION_ELIGIBILITY_WORK_KIND:
                        if self._decision_handler is None:
                            raise RuntimeError(
                                "no decision handler registered"
                            )
                        decision = self._decision_eligibility.consume(work)
                        prior_count = self._decision_counts_by_actor.get(
                            decision.actor_id,
                            0,
                        )
                        if (
                            decision.actor_id in self._model_backed_actor_ids
                            and prior_count
                            >= MAX_MODEL_DECISION_CALLS_PER_DAY
                        ):
                            raise ModelDecisionCallLimitError(
                                "model-backed actor exceeded the approved "
                                "decision-call ceiling"
                            )
                        self._decision_counts_by_actor[decision.actor_id] = (
                            prior_count + 1
                        )
                        self._decision_handler(decision, context)
                    else:
                        handler = self._handlers.get(work.kind)
                        if handler is None:
                            raise RuntimeError(
                                "no handler registered for scheduled work kind"
                            )
                        handler(work, context)
                except Exception as error:
                    self._record_failure(
                        error,
                        released_uncommitted_count=len(batch) - index,
                    )
                    raise
                self._executed_work.append(
                    ExecutedWorkEvidence(
                        sequence=len(self._executed_work) + 1,
                        item_id=work.item_id,
                        due_time=work.due_time,
                        phase=work.phase.name.lower(),
                        kind=work.kind,
                    )
                )

    def _record_failure(
        self,
        error: Exception,
        *,
        released_uncommitted_count: int,
    ) -> None:
        last_committed_time = (
            self._executed_work[-1].due_time
            if self._executed_work
            else self._clock.start
        )
        self._runtime_failure = DayRuntimeFailureEvidence(
            failure_type=type(error).__name__,
            last_committed_time=last_committed_time,
            failed_time=self._clock.current,
            committed_work_count=len(self._executed_work),
            released_uncommitted_count=released_uncommitted_count,
            pending_work_count=len(self._agenda.pending),
        )
