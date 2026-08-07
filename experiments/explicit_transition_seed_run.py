"""Candidate-local repeated transitions with one explicit seed per step.
Tests Contract A without selecting it or defining durable replay data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Tuple

from experiments.deterministic_transition import (
    GenericIntegerState,
    TransitionConfiguration,
    apply_transition,
)
from experiments.source_linked_history import SourceLinkedHistory, WorldEvent


SUPPORTED_STREAM = "transition"


class ExplicitTransitionInputError(ValueError):
    """Candidate inputs or a retained resume boundary are inconsistent."""


class ExplicitTransitionMismatchError(ValueError):
    """A valid reproduction differs from the retained candidate evidence."""

    def __init__(
        self,
        *,
        step_id: int,
        stream_id: str,
        seed: int,
        recorded_event: WorldEvent | None,
        reproduced_event: WorldEvent | None,
        recorded_trace: "TransitionTrace | None",
        reproduced_trace: "TransitionTrace | None",
    ) -> None:
        super().__init__(
            "reproduction differs at "
            f"step {step_id}, stream {stream_id!r}, supplied seed {seed}"
        )
        self.step_id = step_id
        self.stream_id = stream_id
        self.seed = seed
        self.recorded_event = recorded_event
        self.reproduced_event = reproduced_event
        self.recorded_trace = recorded_trace
        self.reproduced_trace = reproduced_trace


def _require_integer(value: object, *, location: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ExplicitTransitionInputError(
            f"{location}: supplied {value!r}; expected an integer (not Boolean)"
        )
    return value


@dataclass(frozen=True)
class TransitionInput:
    """One immutable, explicitly identified seed-consuming transition."""

    step_id: int
    stream_id: str
    seed: int


@dataclass(frozen=True)
class TransitionTrace:
    """Immutable diagnostic evidence adjacent to objective history."""

    step_id: int
    stream_id: str
    seed: int
    event: WorldEvent


@dataclass(frozen=True)
class ExplicitTransitionRun:
    """Immutable in-memory evidence for this candidate experiment."""

    initial_state: GenericIntegerState
    configuration: TransitionConfiguration
    transition_inputs: Tuple[TransitionInput, ...]
    final_state: GenericIntegerState
    events: Tuple[WorldEvent, ...]
    traces: Tuple[TransitionTrace, ...]


def _normalize_item(item: object, *, index: int) -> TransitionInput:
    if isinstance(item, TransitionInput):
        values = {
            "step_id": item.step_id,
            "stream_id": item.stream_id,
            "seed": item.seed,
        }
    elif isinstance(item, Mapping):
        expected_fields = {"step_id", "stream_id", "seed"}
        actual_fields = set(item)
        if actual_fields != expected_fields:
            missing = sorted(expected_fields - actual_fields)
            extra = sorted(actual_fields - expected_fields, key=repr)
            raise ExplicitTransitionInputError(
                f"transition_inputs[{index}] fields: missing {missing}, extra {extra}; "
                "expected exactly ['seed', 'step_id', 'stream_id']"
            )
        values = {field: item[field] for field in expected_fields}
    else:
        raise ExplicitTransitionInputError(
            f"transition_inputs[{index}]: supplied {item!r}; expected a "
            "TransitionInput or mapping with exactly step_id, stream_id, and seed"
        )

    step_id = _require_integer(
        values["step_id"], location=f"transition_inputs[{index}].step_id"
    )
    if step_id < 0:
        raise ExplicitTransitionInputError(
            f"transition_inputs[{index}].step_id: supplied {step_id}; "
            "expected a nonnegative integer"
        )
    stream_id = values["stream_id"]
    if not isinstance(stream_id, str) or not stream_id:
        raise ExplicitTransitionInputError(
            f"transition_inputs[{index}].stream_id: supplied {stream_id!r}; "
            "expected the nonempty string 'transition'"
        )
    if stream_id != SUPPORTED_STREAM:
        raise ExplicitTransitionInputError(
            f"transition_inputs[{index}].stream_id: supplied {stream_id!r}; "
            f"expected the only supported stream {SUPPORTED_STREAM!r}"
        )
    seed = _require_integer(
        values["seed"], location=f"transition_inputs[{index}].seed"
    )
    return TransitionInput(step_id=step_id, stream_id=stream_id, seed=seed)


def _normalize_inputs(
    inputs: object,
    *,
    start_step: int,
    allow_empty: bool,
    location: str = "transition_inputs",
) -> Tuple[TransitionInput, ...]:
    if not isinstance(inputs, tuple):
        raise ExplicitTransitionInputError(
            f"{location}: supplied {type(inputs).__name__}; expected an immutable tuple"
        )
    if not inputs and not allow_empty:
        raise ExplicitTransitionInputError(
            f"{location}: supplied an empty tuple; expected at least one item"
        )

    normalized = tuple(
        _normalize_item(item, index=index) for index, item in enumerate(inputs)
    )
    for index, item in enumerate(normalized):
        expected_step = start_step + index
        if item.step_id != expected_step:
            raise ExplicitTransitionInputError(
                f"{location}[{index}].step_id: supplied {item.step_id}; "
                f"expected {expected_step} (duplicate, skipped, or reordered step)"
            )
    return normalized


def _validate_state_and_configuration(initial_state: object, configuration: object) -> None:
    if not isinstance(initial_state, GenericIntegerState):
        raise ExplicitTransitionInputError(
            "initial_state: expected a GenericIntegerState"
        )
    if not isinstance(configuration, TransitionConfiguration):
        raise ExplicitTransitionInputError(
            "configuration: expected a TransitionConfiguration"
        )


def _validate_run_boundary(run: object, *, location: str) -> ExplicitTransitionRun:
    if not isinstance(run, ExplicitTransitionRun):
        raise ExplicitTransitionInputError(
            f"{location}: expected an ExplicitTransitionRun"
        )
    _validate_state_and_configuration(run.initial_state, run.configuration)
    inputs = _normalize_inputs(
        run.transition_inputs,
        start_step=0,
        allow_empty=True,
        location=f"{location}.transition_inputs",
    )
    if not isinstance(run.events, tuple):
        raise ExplicitTransitionInputError(f"{location}.events: expected an immutable tuple")
    if not isinstance(run.traces, tuple):
        raise ExplicitTransitionInputError(f"{location}.traces: expected an immutable tuple")
    if len(inputs) != len(run.events) or len(inputs) != len(run.traces):
        raise ExplicitTransitionInputError(
            f"{location} boundary: supplied input/event/trace lengths "
            f"{len(inputs)}/{len(run.events)}/{len(run.traces)}; expected equal lengths"
        )

    value = run.initial_state.value
    for index, (item, event, trace) in enumerate(zip(inputs, run.events, run.traces)):
        if not isinstance(event, WorldEvent):
            raise ExplicitTransitionInputError(
                f"{location}.events[{index}]: expected a WorldEvent"
            )
        if not isinstance(trace, TransitionTrace):
            raise ExplicitTransitionInputError(
                f"{location}.traces[{index}]: expected a TransitionTrace"
            )
        expected_metadata = (item.step_id, item.stream_id, item.seed)
        supplied_metadata = (trace.step_id, trace.stream_id, trace.seed)
        if supplied_metadata != expected_metadata:
            raise ExplicitTransitionInputError(
                f"{location}.traces[{index}] metadata: supplied {supplied_metadata!r}; "
                f"expected {expected_metadata!r} from matching input"
            )
        if trace.event != event:
            raise ExplicitTransitionInputError(
                f"{location}.traces[{index}].event: supplied {trace.event!r}; "
                f"expected matching objective event {event!r}"
            )

        delta = run.configuration.deltas[item.seed % len(run.configuration.deltas)]
        expected_details = {
            "before_value": value,
            "selected_delta": delta,
            "after_value": value + delta,
        }
        expected_tick = run.initial_state.tick + index + 1
        if (
            event.event_id != f"event-{index + 1:04d}"
            or event.tick != expected_tick
            or event.kind != run.configuration.event_kind
            or dict(event.details) != expected_details
        ):
            raise ExplicitTransitionInputError(
                f"{location}.events[{index}] boundary: supplied {event!r}; expected "
                f"event-{index + 1:04d} at tick {expected_tick} with kind "
                f"{run.configuration.event_kind!r} and details {expected_details!r}"
            )
        value += delta

    expected_state = GenericIntegerState(
        tick=run.initial_state.tick + len(inputs), value=value
    )
    if run.final_state != expected_state:
        raise ExplicitTransitionInputError(
            f"{location}.final_state boundary: supplied {run.final_state!r}; "
            f"expected {expected_state!r} from the complete prefix"
        )
    return run


def _execute_validated(
    *,
    initial_state: GenericIntegerState,
    configuration: TransitionConfiguration,
    transition_inputs: Tuple[TransitionInput, ...],
    history: SourceLinkedHistory,
) -> ExplicitTransitionRun:
    state = initial_state
    traces = []
    for item in transition_inputs:
        result = apply_transition(
            state=state,
            seed=item.seed,
            configuration=configuration,
            history=history,
        )
        traces.append(
            TransitionTrace(
                step_id=item.step_id,
                stream_id=item.stream_id,
                seed=item.seed,
                event=result.event,
            )
        )
        state = result.next_state
    return ExplicitTransitionRun(
        initial_state=initial_state,
        configuration=configuration,
        transition_inputs=transition_inputs,
        final_state=state,
        events=history.events(),
        traces=tuple(traces),
    )


def execute_explicit_transitions(
    *,
    initial_state: GenericIntegerState,
    configuration: TransitionConfiguration,
    transition_inputs: object,
) -> ExplicitTransitionRun:
    """Validate a complete nonempty input tuple, then execute on fresh history."""
    _validate_state_and_configuration(initial_state, configuration)
    inputs = _normalize_inputs(
        transition_inputs, start_step=0, allow_empty=False
    )
    return _execute_validated(
        initial_state=initial_state,
        configuration=configuration,
        transition_inputs=inputs,
        history=SourceLinkedHistory(),
    )


def empty_explicit_transition_prefix(
    *, initial_state: GenericIntegerState, configuration: TransitionConfiguration
) -> ExplicitTransitionRun:
    """Create the validated zero-length boundary used to resume a whole run."""
    _validate_state_and_configuration(initial_state, configuration)
    return ExplicitTransitionRun(
        initial_state=initial_state,
        configuration=configuration,
        transition_inputs=(),
        final_state=initial_state,
        events=(),
        traces=(),
    )


def resume_explicit_transitions(
    *, prefix: ExplicitTransitionRun, suffix_inputs: object
) -> ExplicitTransitionRun:
    """Validate a complete prefix/suffix boundary before rebuilding and resuming."""
    prefix = _validate_run_boundary(prefix, location="prefix")
    suffix = _normalize_inputs(
        suffix_inputs,
        start_step=len(prefix.transition_inputs),
        allow_empty=True,
        location="suffix_inputs",
    )
    if not prefix.transition_inputs and not suffix:
        raise ExplicitTransitionInputError(
            "resume boundary: prefix and suffix are both empty; expected a nonempty run"
        )

    history = SourceLinkedHistory()
    for event in prefix.events:
        copied = history.record_event(
            tick=event.tick, kind=event.kind, details=event.details
        )
        if copied != event:
            raise ExplicitTransitionInputError(
                "prefix history boundary changed while rebuilding validated events"
            )

    suffix_run = _execute_validated(
        initial_state=prefix.final_state,
        configuration=prefix.configuration,
        transition_inputs=suffix,
        history=history,
    )
    return ExplicitTransitionRun(
        initial_state=prefix.initial_state,
        configuration=prefix.configuration,
        transition_inputs=prefix.transition_inputs + suffix,
        final_state=suffix_run.final_state,
        events=suffix_run.events,
        traces=prefix.traces + suffix_run.traces,
    )


def reproduce_explicit_transitions(
    *, retained: ExplicitTransitionRun, transition_inputs: object
) -> ExplicitTransitionRun:
    """Re-execute complete matching inputs and compare all retained evidence."""
    retained = _validate_run_boundary(retained, location="retained")
    supplied = _normalize_inputs(
        transition_inputs, start_step=0, allow_empty=False
    )
    if len(supplied) != len(retained.transition_inputs):
        raise ExplicitTransitionInputError(
            "transition_inputs boundary: supplied length "
            f"{len(supplied)}; expected {len(retained.transition_inputs)}"
        )
    for index, (item, trace) in enumerate(zip(supplied, retained.traces)):
        supplied_metadata = (item.step_id, item.stream_id, item.seed)
        retained_metadata = (trace.step_id, trace.stream_id, trace.seed)
        if supplied_metadata != retained_metadata:
            raise ExplicitTransitionInputError(
                f"transition_inputs[{index}] metadata: supplied {supplied_metadata!r}; "
                f"expected retained trace metadata {retained_metadata!r}"
            )

    reproduced = execute_explicit_transitions(
        initial_state=retained.initial_state,
        configuration=retained.configuration,
        transition_inputs=supplied,
    )
    if (
        reproduced.final_state == retained.final_state
        and reproduced.events == retained.events
        and reproduced.traces == retained.traces
    ):
        return reproduced

    comparison_length = max(len(retained.traces), len(reproduced.traces))
    for index in range(comparison_length):
        recorded_trace = retained.traces[index] if index < len(retained.traces) else None
        reproduced_trace = (
            reproduced.traces[index] if index < len(reproduced.traces) else None
        )
        recorded_event = retained.events[index] if index < len(retained.events) else None
        reproduced_event = (
            reproduced.events[index] if index < len(reproduced.events) else None
        )
        if recorded_trace != reproduced_trace or recorded_event != reproduced_event:
            trace = reproduced_trace or recorded_trace
            assert trace is not None
            raise ExplicitTransitionMismatchError(
                step_id=trace.step_id,
                stream_id=trace.stream_id,
                seed=trace.seed,
                recorded_event=recorded_event,
                reproduced_event=reproduced_event,
                recorded_trace=recorded_trace,
                reproduced_trace=reproduced_trace,
            )

    last = reproduced.traces[-1]
    raise ExplicitTransitionMismatchError(
        step_id=last.step_id,
        stream_id=last.stream_id,
        seed=last.seed,
        recorded_event=retained.events[-1],
        reproduced_event=reproduced.events[-1],
        recorded_trace=retained.traces[-1],
        reproduced_trace=reproduced.traces[-1],
    )
