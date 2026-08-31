"""Concrete successor world for one accelerated autonomous day."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal

from policies.mara_harness import MaraHarness
from simulation.actions import ActionAttempt, ActionResult, PendingAction
from simulation.agents import (
    ActionContinuityRequirement,
    AgentState,
    AgentView,
    MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES,
    PRIVATE_DECISION_RECORD_RESOLUTION_BASE_BYTES,
    PolicyDecisionRecord,
    private_decision_records_size_bytes,
    validate_private_decision_record_retention,
)
from policies.mara_decision_request import MAX_RESTRICTED_DECISION_INPUT_BYTES
from simulation.day_runtime import AcceleratedDayRuntime, DayRunSummary, DayWorkContext
from simulation.decision_eligibility import (
    DecisionTrigger,
    DecisionTriggerKind,
    EligibleDecision,
)
from simulation.events import Event, EventLog, Observation, freeze_mapping, to_plain_data
from simulation.institutions import InstitutionState
from simulation.official_record import OfficialRecord
from simulation.scheduling import ScheduledWork, TemporalPhase
from simulation.time import SimulatedTime
from simulation.understanding import (
    link_official_version_conflicts,
    trace_from_delivered_observation,
)
from simulation.world import ResourceState, WorldState


MARA_ID = "mara-vale"
ILAN_ID = "ilan-reed"
TRANSIT_AUTHORITY_ID = "district-transit-authority"

_SUPPORTING_WORK_START = "autonomous_day_supporting_work_start"
_SUPPORTING_WORK_COMPLETION = "autonomous_day_supporting_work_completion"
_INSTITUTIONAL_SERVICE_CHANGE = "autonomous_day_institutional_service_change"
_TRANSIT_BULLETIN_DELIVERY = "autonomous_day_transit_bulletin_delivery"
_MARA_TRANSIT_UNDERSTANDING_UPDATE = "autonomous_day_mara_transit_understanding_update"
_MARA_TRAVEL_COMPLETION = "autonomous_day_mara_travel_completion"
_MARA_REST_COMPLETION = "autonomous_day_mara_rest_completion"
_MARA_WORK_COMPLETION = "autonomous_day_mara_work_completion"
_MARA_HOUSEHOLD_COMPLETION = "autonomous_day_mara_household_completion"

_ILAN_WORK_START_MINUTE = 8 * 60
_MARA_SCHEDULED_WAKE_MINUTE = 7 * 60
_TRANSIT_CHANGE_MINUTE = 8 * 60 + 30
_ILAN_WORK_DURATION_MINUTES = 2 * 60
_TRANSIT_BULLETIN_MINUTE = 11 * 60
_TRANSIT_BULLETIN_LOCATIONS = frozenset({"home"})
_MARA_TRAVEL_DURATION_MINUTES = 30
_MARA_REST_DURATION_MINUTES = 60
_MARA_WORK_DURATION_MINUTES = 120
_MARA_HOUSEHOLD_DURATION_MINUTES = 60
AD12_OLLAMA_MODEL = "qwen3:4b-instruct"


@dataclass(frozen=True)
class MaraActionContinuityRule:
    """Scenario-owned classification for one action's lasting context."""

    retention: Literal[
        "canonical_current_state",
        "recent_result_only",
        "fulfilled_obligation_requirement",
    ]
    obligation: str | None = None

    def __post_init__(self) -> None:
        requires_obligation = self.retention == "fulfilled_obligation_requirement"
        if requires_obligation != (self.obligation is not None):
            raise ValueError(
                "only fulfilled-obligation continuity rules name an obligation"
            )


AUTONOMOUS_DAY_MARA_RESOLVER_KINDS = frozenset(
    ("travel", "work", "household", "wait")
)


# The classification must cover the resolver's independently declared finite
# vocabulary. A regression test keeps the sets equal as either side evolves.
AUTONOMOUS_DAY_MARA_ACTION_CONTINUITY_RULES = {
    "travel": MaraActionContinuityRule("canonical_current_state"),
    "work": MaraActionContinuityRule(
        "fulfilled_obligation_requirement",
        obligation="workplace shift",
    ),
    "household": MaraActionContinuityRule(
        "fulfilled_obligation_requirement",
        obligation="household time",
    ),
    "wait": MaraActionContinuityRule("recent_result_only"),
}


def autonomous_day_mara_valid_actions(location: str) -> tuple[str, ...]:
    """Return locally available actions from the classified resolver vocabulary."""

    candidates = (
        ("travel", "work", "wait")
        if location == "workplace"
        else ("household", "travel", "wait")
    )
    return tuple(
        kind
        for kind in candidates
        if kind in AUTONOMOUS_DAY_MARA_RESOLVER_KINDS
    )


MaraDecisionCallback = Callable[[EligibleDecision, AgentView], None]


@dataclass
class AutonomousDay:
    """One world, event history, and accelerated-day executor."""

    world: WorldState
    runtime: AcceleratedDayRuntime
    _event_log: EventLog
    _pending_actions: dict[str, PendingAction]
    _private_decision_records: list[PolicyDecisionRecord]
    _private_decision_record_byte_measurements: list[int]
    _understanding_transitions: list[dict[str, object]]
    _dispatch_history_checkpoints: dict[
        int, tuple[frozenset[str], frozenset[str], frozenset[str], int]
    ]
    _committed_objective_dispatches: dict[tuple[str, str], dict[str, object]]
    _committed_model_decision_dispatches: dict[str, dict[str, object]]
    _mara_harness_configured: bool
    _mara_provider_kind: str | None

    @property
    def events(self) -> tuple[Event, ...]:
        return self._event_log.events

    @property
    def observations(self) -> tuple[Observation, ...]:
        return self._event_log.observations

    @property
    def pending_action_count(self) -> int:
        return len(self._pending_actions)

    @property
    def private_decision_records(self) -> tuple[PolicyDecisionRecord, ...]:
        """Return inspector-only model evidence, never objective history."""
        return tuple(self._private_decision_records)

    @property
    def private_decision_records_bytes(self) -> int:
        return private_decision_records_size_bytes(self.private_decision_records)

    @property
    def peak_retained_private_decision_records_bytes(self) -> int:
        """Return the largest retained private-evidence footprint this run saw."""
        return max(self._private_decision_record_byte_measurements)

    @property
    def mara_harness_configured(self) -> bool:
        return self._mara_harness_configured

    @property
    def mara_provider_kind(self) -> str | None:
        return self._mara_provider_kind

    @property
    def understanding_transitions(self) -> tuple[dict[str, object], ...]:
        """Return inspector-only records of canonical understanding changes."""
        return tuple(self._understanding_transitions)

    def run(self) -> DayRunSummary:
        return self.runtime.run()


def build_autonomous_day(
    *,
    seed: int = 42,
    on_mara_decision: MaraDecisionCallback | None = None,
    mara_harness: MaraHarness | None = None,
) -> AutonomousDay:
    """Build the first concrete world hosted by the successor day runtime."""

    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")
    if on_mara_decision is not None and not callable(on_mara_decision):
        raise TypeError("on_mara_decision must be callable")
    if mara_harness is not None and not isinstance(mara_harness, MaraHarness):
        raise TypeError("mara_harness must be MaraHarness")
    if on_mara_decision is not None and mara_harness is not None:
        raise ValueError("choose either on_mara_decision or mara_harness")

    world = WorldState(
        tick=0,
        seed=seed,
        travel_graph={
            "home": ("workplace",),
            "workplace": ("home", "transit_stop"),
            "transit_stop": ("workplace",),
        },
        agents={
            MARA_ID: AgentState(
                agent_id=MARA_ID,
                display_name="Mara Vale",
                role="focal",
                location="home",
                aim="live an ordinary day without privileged world knowledge",
                obligations=("workplace shift", "household time"),
            ),
            ILAN_ID: AgentState(
                agent_id=ILAN_ID,
                display_name="Ilan Reed",
                role="co-worker",
                location="workplace",
                aim="complete the morning ledger shift",
                obligations=("morning ledger shift",),
            ),
        },
        resource=ResourceState(total_units=0, committed_units=0),
        institution=InstitutionState(
            institution_id=TRANSIT_AUTHORITY_ID,
            display_name="District Transit Authority",
            official_record=OfficialRecord(artifact_id="district-transit-notices"),
            records={"tram_service": "normal"},
        ),
        diaries={},
    )
    event_log = EventLog()
    pending_actions: dict[str, PendingAction] = {}
    transit_change_events: dict[str, Event] = {}
    transit_bulletin_observations: dict[str, Observation] = {}
    understanding_transitions: list[dict[str, object]] = []
    dispatch_history_checkpoints: dict[
        int, tuple[frozenset[str], frozenset[str], frozenset[str], int]
    ] = {}
    committed_objective_dispatches: dict[tuple[str, str], dict[str, object]] = {}
    committed_model_decision_dispatches: dict[str, dict[str, object]] = {}
    decision_record_ids_by_scheduled_work_id: dict[str, str] = {}
    private_decision_records: list[PolicyDecisionRecord] = []
    private_decision_record_byte_measurements = [
        private_decision_records_size_bytes(())
    ]
    mara_action_count = 0

    def measure_private_decision_record_footprint() -> None:
        private_decision_record_byte_measurements.append(
            private_decision_records_size_bytes(tuple(private_decision_records)),
        )

    def checkpoint_objective_history(
        sequence: int,
        work: ScheduledWork,
    ) -> None:
        """Remember the objective boundary before a dispatch may mutate it."""
        del work
        dispatch_history_checkpoints[sequence] = (
            frozenset(event.event_id for event in event_log.events),
            frozenset(observation.observation_id for observation in event_log.observations),
            frozenset(
                result.action_id
                for actor in world.agents.values()
                for result in actor.action_results
            ),
            len(understanding_transitions),
        )

    def record_committed_objective_dispatch(
        sequence: int,
        work: ScheduledWork,
    ) -> None:
        """Link newly created objective evidence to its successful dispatch."""
        event_ids, observation_ids, action_ids, transition_count = (
            dispatch_history_checkpoints[sequence]
        )
        dispatch = {
            "sequence": sequence,
            "phase": work.phase.name.lower(),
        }
        new_artifacts = [
            *(
                ("event", event.event_id)
                for event in event_log.events
                if event.event_id not in event_ids
            ),
            *(
                ("observation", observation.observation_id)
                for observation in event_log.observations
                if observation.observation_id not in observation_ids
            ),
            *(
                ("action_result", result.action_id)
                for actor in world.agents.values()
                for result in actor.action_results
                if result.action_id not in action_ids
            ),
            *(
                ("understanding_transition", str(transition["trace_id"]))
                for transition in understanding_transitions[transition_count:]
            ),
        ]
        committed_objective_dispatches.update(
            {artifact: dispatch for artifact in new_artifacts}
        )
        decision_record_id = decision_record_ids_by_scheduled_work_id.get(
            work.item_id
        )
        if decision_record_id is not None:
            committed_model_decision_dispatches[decision_record_id] = dispatch

    def mara_view() -> AgentView:
        """Construct the same agent-safe shape used at Mara's decision seam."""
        mara = world.agents[MARA_ID]
        held_units = (
            mara.resource_holdings.get(mara.required_resource_id, 0)
            if mara.required_resource_id is not None
            else 0
        )
        return AgentView(
            tick=world.tick,
            agent_id=mara.agent_id,
            display_name=mara.display_name,
            role=mara.role,
            location=mara.location,
            aim=mara.aim,
            required_resource_id=mara.required_resource_id,
            required_units=mara.required_units,
            resource_holdings=freeze_mapping(mara.resource_holdings),
            remaining_required_units=max(0, mara.required_units - held_units),
            obligations=mara.obligations,
            last_attempt=mara.last_attempt,
            action_history=tuple(mara.action_history),
            action_results=tuple(mara.action_results),
            observations=tuple(mara.observations),
            beliefs=tuple(mara.beliefs),
            memory_traces=mara.memory_traces,
            interpreted_claims=mara.interpreted_claims,
            contextual_stance=mara.contextual_stance,
            accessible_diary_id=None,
            accessible_diary_entry_count=0,
            accessible_diary_entries=(),
            consultable_official_record_ids=(),
            reachable_destinations=tuple(
                world.travel_graph.get(mara.location, ())
            ),
            work_action_available=mara.location == "workplace",
            allocation_action_available=False,
            valid_actions=autonomous_day_mara_valid_actions(mara.location),
            household_action_available=mara.location == "home",
            continuity_requirements=mara.continuity_requirements,
        )

    def dispatch_mara_decision(
        decision: EligibleDecision,
        context: DayWorkContext,
    ) -> None:
        if decision.actor_id != MARA_ID:
            raise RuntimeError("autonomous day has no decision callback for actor")
        if on_mara_decision is not None:
            on_mara_decision(decision, mara_view())
            return
        if mara_harness is None:
            raise RuntimeError("Mara decision was requested without a callback")
        view = mara_view()
        attempt = mara_harness.choose(view)
        decision_record = mara_harness.take_decision_record()
        if decision_record is None:
            raise RuntimeError("Mara harness produced no private decision record")
        validate_private_decision_record_retention(
            (*private_decision_records, decision_record),
            reserved_bytes=mara_decision_record_resolution_reserve(attempt),
        )
        private_decision_records.append(decision_record)
        decision_record_ids_by_scheduled_work_id[decision.scheduled_work_id] = (
            decision_record.decision_id
        )
        measure_private_decision_record_footprint()
        resolve_mara_attempt(attempt, context, decision_record, decision)
        if decision_record.status == "failed":
            context.request_safe_failure_retry(
                actor_id=MARA_ID,
                failure_id=decision_record.decision_id,
            )
            return
        consumed_requirement_ids = {
            requirement.requirement_id
            for requirement in view.continuity_requirements
        }
        mara = world.agents[MARA_ID]
        mara.continuity_requirements = tuple(
            requirement
            for requirement in mara.continuity_requirements
            if requirement.requirement_id not in consumed_requirement_ids
            or requirement.state_value in mara.obligations
        )

    def replace_latest_private_decision_record(
        record: PolicyDecisionRecord,
    ) -> None:
        if not private_decision_records:
            raise RuntimeError("Mara has no private decision record to update")
        candidate = (*private_decision_records[:-1], record)
        validate_private_decision_record_retention(candidate)
        private_decision_records[-1] = record
        measure_private_decision_record_footprint()

    def mara_decision_record_resolution_reserve(attempt: ActionAttempt) -> int:
        """Reserve bounded private-record space before objective mutation."""
        dynamic_material = (
            attempt.actor_id,
            attempt.kind,
            "home",
            "workplace",
            "transit_stop",
            json.dumps(
                to_plain_data(attempt.parameters),
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ),
        )
        return PRIVATE_DECISION_RECORD_RESOLUTION_BASE_BYTES + sum(
            len(value.encode("utf-8")) for value in dynamic_material
        )

    def resolve_private_decision_record(result: ActionResult) -> None:
        for index in range(len(private_decision_records) - 1, -1, -1):
            record = private_decision_records[index]
            if (
                record.action_id == result.action_id
                and record.resolution_status is None
            ):
                candidate = list(private_decision_records)
                candidate[index] = record.resolved_with(result)
                validate_private_decision_record_retention(tuple(candidate))
                private_decision_records[:] = candidate
                measure_private_decision_record_footprint()
                return
        raise RuntimeError("Mara action result has no private decision record")

    def append_mara_result(
        *,
        action_id: str,
        attempt_event_id: str,
        action_kind: str,
        outcome: Event,
        status: str,
        reason: str | None = None,
    ) -> ActionResult:
        result = ActionResult(
            action_id=action_id,
            attempt_event_id=attempt_event_id,
            outcome_event_id=outcome.event_id,
            actor_id=MARA_ID,
            action_kind=action_kind,
            status=status,
            resolved_tick=outcome.tick,
            reason=reason,
        )
        world.agents[MARA_ID].action_results.append(result)
        return result

    def register_fulfilled_obligation_requirement(
        *,
        mara: AgentState,
        pending: PendingAction,
        result: ActionResult,
        obligation: str,
    ) -> None:
        rule = AUTONOMOUS_DAY_MARA_ACTION_CONTINUITY_RULES.get(
            pending.attempt.kind
        )
        if (
            rule is None
            or rule.retention != "fulfilled_obligation_requirement"
            or rule.obligation != obligation
            or result.status != "completed"
            or result.action_kind != pending.attempt.kind
            or result.action_id != pending.action_id
            or result.attempt_event_id != pending.attempt_event_id
        ):
            raise RuntimeError(
                "action does not match its fulfilled-obligation continuity rule"
            )
        if not mara.action_history or mara.action_history[-1] != pending.attempt:
            raise RuntimeError(
                "fulfilled obligation action is not the latest Mara attempt"
            )
        if any(
            requirement.action_id == result.action_id
            for requirement in mara.continuity_requirements
        ):
            raise RuntimeError("action already has a continuity requirement")
        mara.continuity_requirements = (
            *mara.continuity_requirements,
            ActionContinuityRequirement(
                requirement_id=f"continuity-{result.action_id}",
                action_id=result.action_id,
                attempt_event_id=result.attempt_event_id,
                action_history_index=len(mara.action_history) - 1,
                attempt=pending.attempt,
                result=result,
                reason="fulfilled_obligation",
                state_field="obligations",
                state_value=obligation,
                lifecycle="through_selected_decision",
            ),
        )

    def reject_mara_attempt(
        attempt: ActionAttempt,
        attempted: Event,
        reason: str,
    ) -> None:
        rejected = event_log.record(
            tick=attempted.tick,
            kind="action_rejected",
            actor_id=MARA_ID,
            action_id=attempted.action_id,
            caused_by=(attempted.event_id,),
            details={"reason": reason},
        )
        result = append_mara_result(
            action_id=attempted.action_id or "",
            attempt_event_id=attempted.event_id,
            action_kind=attempt.kind,
            outcome=rejected,
            status="rejected",
            reason=reason,
        )
        resolve_private_decision_record(result)

    def resolve_mara_attempt(
        attempt: ActionAttempt,
        context: DayWorkContext,
        decision_record: PolicyDecisionRecord,
        decision: EligibleDecision,
    ) -> None:
        nonlocal mara_action_count
        if attempt.actor_id != MARA_ID:
            raise ValueError("Mara harness attempted an action for another actor")
        mara_action_count += 1
        action_id = f"autonomous-day-mara-action-{mara_action_count:04d}"
        attempted = event_log.record(
            tick=context.current.total_minutes,
            kind="action_attempted",
            actor_id=MARA_ID,
            action_id=action_id,
            details={
                "action_kind": attempt.kind,
                "decision_explanation": attempt.explanation,
            },
        )
        mara = world.agents[MARA_ID]
        mara.last_attempt = attempt
        mara.action_history.append(attempt)
        continuity_rule = AUTONOMOUS_DAY_MARA_ACTION_CONTINUITY_RULES.get(
            attempt.kind
        )
        resolver_supports_kind = attempt.kind in AUTONOMOUS_DAY_MARA_RESOLVER_KINDS
        travel_destination = attempt.parameters.get("destination")
        accepted = (
            resolver_supports_kind
            and continuity_rule is not None
            and (
                attempt.kind == "wait"
                or (attempt.kind == "household" and mara.location == "home")
                or (
                    attempt.kind == "work" and mara.location == "workplace"
                )
                or (
                    attempt.kind == "travel"
                    and isinstance(travel_destination, str)
                    and travel_destination
                    in world.travel_graph.get(mara.location, ())
                )
            )
        )
        replace_latest_private_decision_record(
            decision_record.linked_to(
                attempt_event_id=attempted.event_id,
                action_id=action_id,
                validation_status="accepted" if accepted else "rejected",
            )
        )
        scheduled_rest = (
            decision_record.status == "selected"
            and any(
                trigger.kind is DecisionTriggerKind.SCHEDULED_WAKE
                for trigger in decision.triggers
            )
            and mara.location == "home"
        )
        if attempt.kind == "wait" and scheduled_rest:
            completion_time = context.current.plus_minutes(
                _MARA_REST_DURATION_MINUTES
            )
            pending_actions[MARA_ID] = PendingAction(
                action_id=action_id,
                attempt_event_id=attempted.event_id,
                attempt=attempt,
                started_tick=context.current.total_minutes,
                completes_tick=completion_time.total_minutes,
            )
            context.schedule(
                ScheduledWork(
                    item_id=f"{action_id}-rest-completion",
                    due_time=completion_time,
                    phase=TemporalPhase.ACTION_COMPLETION,
                    kind=_MARA_REST_COMPLETION,
                )
            )
            return
        if attempt.kind == "wait":
            completed = event_log.record(
                tick=context.current.total_minutes,
                kind="wait_completed",
                actor_id=MARA_ID,
                action_id=action_id,
                caused_by=(attempted.event_id,),
                details={"location": mara.location},
            )
            result = append_mara_result(
                action_id=action_id,
                attempt_event_id=attempted.event_id,
                action_kind=attempt.kind,
                outcome=completed,
                status="completed",
            )
            resolve_private_decision_record(result)
            return
        if attempt.kind == "household":
            if mara.location != "home":
                reject_mara_attempt(
                    attempt,
                    attempted,
                    "household activity requires Mara to be at home",
                )
                return
            completion_time = context.current.plus_minutes(
                _MARA_HOUSEHOLD_DURATION_MINUTES
            )
            pending_actions[MARA_ID] = PendingAction(
                action_id=action_id,
                attempt_event_id=attempted.event_id,
                attempt=attempt,
                started_tick=context.current.total_minutes,
                completes_tick=completion_time.total_minutes,
            )
            context.schedule(
                ScheduledWork(
                    item_id=f"{action_id}-household-completion",
                    due_time=completion_time,
                    phase=TemporalPhase.ACTION_COMPLETION,
                    kind=_MARA_HOUSEHOLD_COMPLETION,
                )
            )
            return
        if attempt.kind == "work":
            if mara.location != "workplace":
                reject_mara_attempt(
                    attempt,
                    attempted,
                    "work requires Mara to be at the workplace",
                )
                return
            completion_time = context.current.plus_minutes(
                _MARA_WORK_DURATION_MINUTES
            )
            pending_actions[MARA_ID] = PendingAction(
                action_id=action_id,
                attempt_event_id=attempted.event_id,
                attempt=attempt,
                started_tick=context.current.total_minutes,
                completes_tick=completion_time.total_minutes,
            )
            context.schedule(
                ScheduledWork(
                    item_id=f"{action_id}-work-completion",
                    due_time=completion_time,
                    phase=TemporalPhase.ACTION_COMPLETION,
                    kind=_MARA_WORK_COMPLETION,
                )
            )
            return
        if (
            not resolver_supports_kind
            or continuity_rule is None
            or attempt.kind != "travel"
        ):
            reject_mara_attempt(
                attempt,
                attempted,
                "action is not available in the autonomous-day composition",
            )
            return
        destination = travel_destination
        if not isinstance(destination, str) or destination not in world.travel_graph.get(
            mara.location, ()
        ):
            reject_mara_attempt(
                attempt,
                attempted,
                "travel destination is not reachable from Mara's location",
            )
            return
        completion_time = context.current.plus_minutes(_MARA_TRAVEL_DURATION_MINUTES)
        pending_actions[MARA_ID] = PendingAction(
            action_id=action_id,
            attempt_event_id=attempted.event_id,
            attempt=attempt,
            started_tick=context.current.total_minutes,
            completes_tick=completion_time.total_minutes,
        )
        context.schedule(
            ScheduledWork(
                item_id=f"{action_id}-completion",
                due_time=completion_time,
                phase=TemporalPhase.ACTION_COMPLETION,
                kind=_MARA_TRAVEL_COMPLETION,
            )
        )

    def complete_mara_travel(
        work: ScheduledWork,
        context: DayWorkContext,
    ) -> None:
        pending = pending_actions.pop(MARA_ID)
        if pending.completes_tick != context.current.total_minutes:
            raise RuntimeError("Mara travel released at the wrong time")
        destination = pending.attempt.parameters["destination"]
        if not isinstance(destination, str):
            raise RuntimeError("Mara travel is missing its destination")
        world.agents[MARA_ID].location = destination
        completed = event_log.record(
            tick=context.current.total_minutes,
            kind="travel_completed",
            actor_id=MARA_ID,
            action_id=pending.action_id,
            caused_by=(pending.attempt_event_id,),
            details={"destination": destination},
        )
        result = append_mara_result(
            action_id=pending.action_id,
            attempt_event_id=pending.attempt_event_id,
            action_kind=pending.attempt.kind,
            outcome=completed,
            status="completed",
        )
        resolve_private_decision_record(result)
        context.request_decision(
            actor_id=MARA_ID,
            due_time=context.current,
            trigger=DecisionTrigger(
                kind=DecisionTriggerKind.ACTION_RESULT,
                source_id=completed.event_id,
            ),
        )

    def complete_mara_rest(
        work: ScheduledWork,
        context: DayWorkContext,
    ) -> None:
        pending = pending_actions.pop(MARA_ID)
        if (
            pending.attempt.kind != "wait"
            or pending.completes_tick != context.current.total_minutes
        ):
            raise RuntimeError("Mara rest released at the wrong time")
        completed = event_log.record(
            tick=context.current.total_minutes,
            kind="rest_completed",
            actor_id=MARA_ID,
            action_id=pending.action_id,
            caused_by=(pending.attempt_event_id,),
            details={
                "location": world.agents[MARA_ID].location,
                "duration_minutes": _MARA_REST_DURATION_MINUTES,
            },
        )
        result = append_mara_result(
            action_id=pending.action_id,
            attempt_event_id=pending.attempt_event_id,
            action_kind=pending.attempt.kind,
            outcome=completed,
            status="completed",
        )
        resolve_private_decision_record(result)
        context.request_decision(
            actor_id=MARA_ID,
            due_time=context.current,
            trigger=DecisionTrigger(
                kind=DecisionTriggerKind.ACTION_RESULT,
                source_id=completed.event_id,
            ),
        )

    def complete_mara_work(
        work: ScheduledWork,
        context: DayWorkContext,
    ) -> None:
        pending = pending_actions.pop(MARA_ID)
        if (
            pending.attempt.kind != "work"
            or pending.completes_tick != context.current.total_minutes
            or world.agents[MARA_ID].location != "workplace"
        ):
            raise RuntimeError("Mara work released in an invalid state")
        completed = event_log.record(
            tick=context.current.total_minutes,
            kind="work_completed",
            actor_id=MARA_ID,
            action_id=pending.action_id,
            caused_by=(pending.attempt_event_id,),
            details={
                "location": world.agents[MARA_ID].location,
                "duration_minutes": _MARA_WORK_DURATION_MINUTES,
            },
        )
        result = append_mara_result(
            action_id=pending.action_id,
            attempt_event_id=pending.attempt_event_id,
            action_kind=pending.attempt.kind,
            outcome=completed,
            status="completed",
        )
        mara = world.agents[MARA_ID]
        if "workplace shift" in mara.obligations:
            mara.obligations = tuple(
                obligation
                for obligation in mara.obligations
                if obligation != "workplace shift"
            )
            register_fulfilled_obligation_requirement(
                mara=mara,
                pending=pending,
                result=result,
                obligation="workplace shift",
            )
        resolve_private_decision_record(result)
        context.request_decision(
            actor_id=MARA_ID,
            due_time=context.current,
            trigger=DecisionTrigger(
                kind=DecisionTriggerKind.ACTION_RESULT,
                source_id=completed.event_id,
            ),
        )

    def complete_mara_household(
        work: ScheduledWork,
        context: DayWorkContext,
    ) -> None:
        pending = pending_actions.pop(MARA_ID)
        if (
            pending.attempt.kind != "household"
            or pending.completes_tick != context.current.total_minutes
            or world.agents[MARA_ID].location != "home"
        ):
            raise RuntimeError("Mara household activity released in an invalid state")
        completed = event_log.record(
            tick=context.current.total_minutes,
            kind="household_time_completed",
            actor_id=MARA_ID,
            action_id=pending.action_id,
            caused_by=(pending.attempt_event_id,),
            details={
                "location": world.agents[MARA_ID].location,
                "duration_minutes": _MARA_HOUSEHOLD_DURATION_MINUTES,
            },
        )
        result = append_mara_result(
            action_id=pending.action_id,
            attempt_event_id=pending.attempt_event_id,
            action_kind=pending.attempt.kind,
            outcome=completed,
            status="completed",
        )
        mara = world.agents[MARA_ID]
        if "household time" in mara.obligations:
            mara.obligations = tuple(
                obligation
                for obligation in mara.obligations
                if obligation != "household time"
            )
            register_fulfilled_obligation_requirement(
                mara=mara,
                pending=pending,
                result=result,
                obligation="household time",
            )
        resolve_private_decision_record(result)
        context.request_decision(
            actor_id=MARA_ID,
            due_time=context.current,
            trigger=DecisionTrigger(
                kind=DecisionTriggerKind.ACTION_RESULT,
                source_id=completed.event_id,
            ),
        )

    def start_supporting_work(
        work: ScheduledWork,
        context: DayWorkContext,
    ) -> None:
        if work.due_time != context.current:
            raise RuntimeError("supporting work released at the wrong time")
        actor = world.agents[ILAN_ID]
        if actor.location != "workplace":
            raise RuntimeError("Ilan's scheduled work requires workplace presence")
        if actor.agent_id in pending_actions:
            raise RuntimeError("Ilan already has an action in progress")

        attempt = ActionAttempt(
            actor_id=actor.agent_id,
            kind="work",
            explanation="complete the scheduled morning ledger shift",
        )
        action_id = "autonomous-day-action-0001"
        attempted = event_log.record(
            tick=context.current.total_minutes,
            kind="action_attempted",
            actor_id=actor.agent_id,
            action_id=action_id,
            details={
                "action_kind": attempt.kind,
                "decision_explanation": attempt.explanation,
            },
        )
        actor.last_attempt = attempt
        actor.action_history.append(attempt)
        completion_time = context.current.plus_minutes(_ILAN_WORK_DURATION_MINUTES)
        pending_actions[actor.agent_id] = PendingAction(
            action_id=action_id,
            attempt_event_id=attempted.event_id,
            attempt=attempt,
            started_tick=context.current.total_minutes,
            completes_tick=completion_time.total_minutes,
        )
        context.schedule(
            ScheduledWork(
                item_id="ilan-morning-ledger-shift-completion",
                due_time=completion_time,
                phase=TemporalPhase.ACTION_COMPLETION,
                kind=_SUPPORTING_WORK_COMPLETION,
            )
        )

    def complete_supporting_work(
        work: ScheduledWork,
        context: DayWorkContext,
    ) -> None:
        if work.due_time != context.current:
            raise RuntimeError("supporting completion released at the wrong time")
        pending = pending_actions.pop(ILAN_ID)
        if pending.completes_tick != context.current.total_minutes:
            raise RuntimeError("supporting work released at the wrong time")
        completed = event_log.record(
            tick=context.current.total_minutes,
            kind="work_completed",
            actor_id=ILAN_ID,
            action_id=pending.action_id,
            caused_by=(pending.attempt_event_id,),
            details={"location": world.agents[ILAN_ID].location},
        )
        world.agents[ILAN_ID].action_results.append(
            ActionResult(
                action_id=pending.action_id,
                attempt_event_id=pending.attempt_event_id,
                outcome_event_id=completed.event_id,
                actor_id=ILAN_ID,
                action_kind=pending.attempt.kind,
                status="completed",
                resolved_tick=context.current.total_minutes,
            )
        )

    def change_transit_service(
        work: ScheduledWork,
        context: DayWorkContext,
    ) -> None:
        if work.due_time != context.current:
            raise RuntimeError("institutional work released at the wrong time")
        prior_status = world.institution.records["tram_service"]
        world.institution.records["tram_service"] = "reduced"
        changed = event_log.record(
            tick=context.current.total_minutes,
            kind="transit_service_changed",
            actor_id=world.institution.institution_id,
            details={
                "route": "workplace-home",
                "prior_status": prior_status,
                "current_status": "reduced",
            },
        )
        delivery_item_id = "home-transit-bulletin-delivery"
        transit_change_events[delivery_item_id] = changed
        context.schedule(
            ScheduledWork(
                item_id=delivery_item_id,
                due_time=SimulatedTime(_TRANSIT_BULLETIN_MINUTE),
                phase=TemporalPhase.OBSERVATION_DELIVERY,
                kind=_TRANSIT_BULLETIN_DELIVERY,
            )
        )

    def deliver_transit_bulletin(
        work: ScheduledWork,
        context: DayWorkContext,
    ) -> None:
        if work.due_time != context.current:
            raise RuntimeError("bulletin delivery released at the wrong time")
        mara = world.agents[MARA_ID]
        if mara.location not in _TRANSIT_BULLETIN_LOCATIONS:
            return
        source_event = transit_change_events[work.item_id]
        observation = event_log.deliver(
            agent_id=mara.agent_id,
            event_id=source_event.event_id,
            source="home transit bulletin receiver",
            delivery_tick=context.current.total_minutes,
            details={
                "evidence_kind": "transit_service_status",
                "route": "workplace-home",
                "current_status": source_event.details["current_status"],
                "proposition": "workplace-home tram service is reduced",
                "asserted_value": 1,
            },
        )
        mara.observations.append(observation)
        understanding_item_id = f"mara-understanding-{observation.observation_id}"
        transit_bulletin_observations[understanding_item_id] = observation
        context.schedule(
            ScheduledWork(
                item_id=understanding_item_id,
                due_time=context.current,
                phase=TemporalPhase.UNDERSTANDING_UPDATE,
                kind=_MARA_TRANSIT_UNDERSTANDING_UPDATE,
            )
        )
        if on_mara_decision is not None or mara_harness is not None:
            context.request_decision(
                actor_id=mara.agent_id,
                due_time=context.current,
                trigger=DecisionTrigger(
                    kind=DecisionTriggerKind.OBSERVATION_DELIVERED,
                    source_id=observation.observation_id,
                ),
            )

    def update_mara_transit_understanding(
        work: ScheduledWork,
        context: DayWorkContext,
    ) -> None:
        if work.due_time != context.current:
            raise RuntimeError("transit understanding released at the wrong time")
        observation = transit_bulletin_observations[work.item_id]
        mara = world.agents[MARA_ID]
        derived = trace_from_delivered_observation(
            observation,
            trace_id=f"trace-{observation.observation_id}",
            claim_id=f"claim-{observation.observation_id}",
            existing_claims=mara.interpreted_claims,
        )
        if derived is None:
            raise RuntimeError("transit bulletin did not support understanding")
        trace, new_claim = derived
        mara.memory_traces += (trace,)
        if new_claim is not None:
            mara.interpreted_claims = link_official_version_conflicts(
                mara.interpreted_claims,
                mara.memory_traces[:-1],
                new_claim,
                trace,
            )
        understanding_transitions.append(
            {
                "agent_id": mara.agent_id,
                "tick": context.current.total_minutes,
                "source_observation_id": observation.observation_id,
                "source_event_id": observation.event_id,
                "trace_id": trace.trace_id,
                "claim_id": trace.interpreted_claim_id,
                "claim_created": new_claim is not None,
            }
        )

    runtime = AcceleratedDayRuntime(
        start=SimulatedTime(0),
        handlers={
            _SUPPORTING_WORK_START: start_supporting_work,
            _SUPPORTING_WORK_COMPLETION: complete_supporting_work,
            _INSTITUTIONAL_SERVICE_CHANGE: change_transit_service,
            _TRANSIT_BULLETIN_DELIVERY: deliver_transit_bulletin,
            _MARA_TRANSIT_UNDERSTANDING_UPDATE: update_mara_transit_understanding,
            _MARA_TRAVEL_COMPLETION: complete_mara_travel,
            _MARA_REST_COMPLETION: complete_mara_rest,
            _MARA_WORK_COMPLETION: complete_mara_work,
            _MARA_HOUSEHOLD_COMPLETION: complete_mara_household,
        },
        decision_handler=(
            dispatch_mara_decision
            if on_mara_decision is not None or mara_harness is not None
            else None
        ),
        model_backed_actor_ids=(MARA_ID,),
        on_time_advanced=lambda current: setattr(
            world,
            "tick",
            current.total_minutes,
        ),
        on_dispatch_started=checkpoint_objective_history,
        on_dispatch_committed=record_committed_objective_dispatch,
    )
    runtime.schedule(
        ScheduledWork(
            item_id="ilan-morning-ledger-shift-start",
            due_time=SimulatedTime(_ILAN_WORK_START_MINUTE),
            phase=TemporalPhase.SCHEDULED_WORLD,
            kind=_SUPPORTING_WORK_START,
        )
    )
    if on_mara_decision is not None or mara_harness is not None:
        runtime.request_decision(
            actor_id=MARA_ID,
            due_time=SimulatedTime(_MARA_SCHEDULED_WAKE_MINUTE),
            trigger=DecisionTrigger(
                kind=DecisionTriggerKind.SCHEDULED_WAKE,
                source_id="autonomous-day-mara-morning-wake",
            ),
        )
    runtime.schedule(
        ScheduledWork(
            item_id="district-transit-morning-service-change",
            due_time=SimulatedTime(_TRANSIT_CHANGE_MINUTE),
            phase=TemporalPhase.SCHEDULED_WORLD,
            kind=_INSTITUTIONAL_SERVICE_CHANGE,
        )
    )
    return AutonomousDay(
        world=world,
        runtime=runtime,
        _event_log=event_log,
        _pending_actions=pending_actions,
        _private_decision_records=private_decision_records,
        _private_decision_record_byte_measurements=(
            private_decision_record_byte_measurements
        ),
        _understanding_transitions=understanding_transitions,
        _dispatch_history_checkpoints=dispatch_history_checkpoints,
        _committed_objective_dispatches=committed_objective_dispatches,
        _committed_model_decision_dispatches=(
            committed_model_decision_dispatches
        ),
        _mara_harness_configured=mara_harness is not None,
        _mara_provider_kind=(
            None if mara_harness is None else mara_harness.provider_kind
        ),
    )


def _focal_update_sort_key(
    update: tuple[SimulatedTime, int, int, str],
) -> tuple[int, int, int]:
    """Order visible ties by runtime phase, then committed source order."""

    visible_time, causal_phase, causal_order, _ = update
    return (visible_time.total_minutes, causal_phase, causal_order)


def render_autonomous_day(day: AutonomousDay, summary: DayRunSummary) -> str:
    """Render only focal-safe evidence from the narrow successor day."""

    lines = [
        "2084 — AUTONOMOUS DAY",
        "Normal observer: focal-character knowledge only",
        "",
        f"Start: {summary.start.label} | Mara at Home",
    ]
    focal_updates: list[tuple[SimulatedTime, int, int, str]] = []
    completed_activity_labels = {
        "household_time_completed": "Mara completed household time.",
        "rest_completed": "Mara completed a rest period.",
        "travel_completed": "Mara completed travel.",
        "work_completed": "Mara completed workplace work.",
    }
    event_kinds_by_id = {event.event_id: event.kind for event in day.events}
    event_order_by_id = {
        event.event_id: index for index, event in enumerate(day.events)
    }
    observation_order_by_id = {
        observation.observation_id: index
        for index, observation in enumerate(day.observations)
    }
    for result in day.world.agents[MARA_ID].action_results:
        activity_label = completed_activity_labels.get(
            event_kinds_by_id.get(result.outcome_event_id)
        )
        if result.status != "completed" or activity_label is None:
            continue
        completed_at = SimulatedTime(result.resolved_tick)
        focal_updates.append(
            (
                completed_at,
                int(TemporalPhase.ACTION_COMPLETION),
                event_order_by_id[result.outcome_event_id],
                f"{completed_at.label} | {activity_label}",
            )
        )
    for observation in day.world.agents[MARA_ID].observations:
        if observation.details.get("evidence_kind") != "transit_service_status":
            continue
        delivered_at = SimulatedTime(observation.delivery_tick)
        focal_updates.append(
            (
                delivered_at,
                int(TemporalPhase.OBSERVATION_DELIVERY),
                observation_order_by_id[observation.observation_id],
                f"{delivered_at.label} | Home transit bulletin: "
                f"{observation.details['route']} service is "
                f"{observation.details['current_status']}.",
            )
        )
    current_visible_time = summary.start
    for delivered_at, _, _, update in sorted(
        focal_updates,
        key=_focal_update_sort_key,
    ):
        if delivered_at > current_visible_time:
            lines.append(
                f"{current_visible_time.label}–{delivered_at.label} "
                "| No focal updates."
            )
        lines.append(update)
        current_visible_time = delivered_at
    if current_visible_time < summary.current:
        lines.append(
            f"{current_visible_time.label}–{summary.current.label} "
            "| No focal updates."
        )
    if summary.runtime_failure is not None:
        lines.append(
            "Run status: stopped without completing the day at "
            f"{summary.current.label}."
        )
    lines.extend(
        [
            f"End: {summary.current.label}",
            "Exact 24-hour boundary reached: "
            + ("yes" if summary.reached_end_boundary else "no"),
        ]
    )
    return "\n".join(lines) + "\n"


def autonomous_day_inspector_data(
    day: AutonomousDay,
    summary: DayRunSummary,
) -> dict[str, object]:
    """Return deterministic omniscient evidence for the successor day."""

    def committed_dispatch(
        artifact_kind: str,
        artifact_id: str,
    ) -> dict[str, object] | None:
        dispatch = day._committed_objective_dispatches.get(
            (artifact_kind, artifact_id)
        )
        return None if dispatch is None else dict(dispatch)

    events = [
        {
            "event_id": event.event_id,
            "tick": event.tick,
            "kind": event.kind,
            "actor_id": event.actor_id,
            "action_id": event.action_id,
            "caused_by": list(event.caused_by),
            "details": to_plain_data(event.details),
            "dispatch": committed_dispatch("event", event.event_id),
        }
        for event in day.events
    ]
    observations = [
        {
            "observation_id": observation.observation_id,
            "agent_id": observation.agent_id,
            "event_id": observation.event_id,
            "source": observation.source,
            "delivery_tick": observation.delivery_tick,
            "details": to_plain_data(observation.details),
            "dispatch": committed_dispatch(
                "observation",
                observation.observation_id,
            ),
        }
        for observation in day.observations
    ]
    event_order_by_id = {
        event.event_id: index for index, event in enumerate(day.events)
    }
    action_results = [
        {
            "action_id": result.action_id,
            "attempt_event_id": result.attempt_event_id,
            "outcome_event_id": result.outcome_event_id,
            "actor_id": result.actor_id,
            "action_kind": result.action_kind,
            "status": result.status,
            "resolved_tick": result.resolved_tick,
            "reason": result.reason,
            "dispatch": committed_dispatch("action_result", result.action_id),
        }
        for actor_id in sorted(day.world.agents)
        for result in day.world.agents[actor_id].action_results
    ]
    action_results.sort(
        key=lambda result: event_order_by_id[result["outcome_event_id"]]
    )
    uncommitted_objective_tail = None
    if summary.runtime_failure is not None:
        failed_dispatch = summary.runtime_failure.failed_dispatch
        if failed_dispatch is not None:
            checkpoint = day._dispatch_history_checkpoints.get(
                failed_dispatch.sequence
            )
            if checkpoint is not None:
                event_ids, observation_ids, action_ids, _ = checkpoint
                uncommitted_objective_tail = {
                    "events": [
                        event for event in events if event["event_id"] not in event_ids
                    ],
                    "observations": [
                        observation
                        for observation in observations
                        if observation["observation_id"] not in observation_ids
                    ],
                    "action_results": [
                        result
                        for result in action_results
                        if result["action_id"] not in action_ids
                    ],
                }
    model_growth = None
    if day.mara_harness_configured:
        model_growth = {
            "peak_restricted_input_bytes": max(
                (
                    record.model_input_bytes
                    for record in day.private_decision_records
                ),
                default=0,
            ),
            "maximum_restricted_input_bytes": (
                MAX_RESTRICTED_DECISION_INPUT_BYTES
            ),
            "retained_private_record_count": len(day.private_decision_records),
            "peak_retained_private_record_bytes": (
                day.peak_retained_private_decision_records_bytes
            ),
            "maximum_retained_private_record_bytes": (
                MAX_RETAINED_PRIVATE_DECISION_RECORD_BYTES
            ),
            "peak_context_counts": model_context_count_measurements(
                day.private_decision_records
            ),
        }
    decision_status_sequence = None
    if day.mara_harness_configured:
        decision_status_sequence = [
            {
                "tick": record.tick,
                "status": record.status,
                "failure_kind": record.failure_kind,
                "provider_call_attempted": record.provider_call_attempted,
                "validation_status": record.validation_status,
                "resolution_status": record.resolution_status,
                "resolved_tick": record.resolved_tick,
                "dispatch": (
                    None
                    if (
                        dispatch := day._committed_model_decision_dispatches.get(
                            record.decision_id
                        )
                    )
                    is None
                    else dict(dispatch)
                ),
            }
            for record in day.private_decision_records
        ]
    return {
        "runtime": summary.to_data(),
        "counts": {
            "events": len(events),
            "observations": len(observations),
            "action_results": len(action_results),
        },
        "model_path": {
            "configured": day.mara_harness_configured,
            "exercised": bool(day.private_decision_records),
            "decision_status_sequence": decision_status_sequence,
            "decision_status_counts": (
                {
                    status: sum(
                        record.status == status
                        for record in day.private_decision_records
                    )
                    for status in sorted(
                        {record.status for record in day.private_decision_records}
                    )
                }
                if day.mara_harness_configured
                else None
            ),
            "provider_failure_count": (
                sum(
                    record.status == "failed" and record.provider_call_attempted
                    for record in day.private_decision_records
                )
                if day.mara_harness_configured
                else None
            ),
            "growth": model_growth,
        },
        "objective_state": {
            "tick": day.world.tick,
            "seed": day.world.seed,
            "agent_locations": {
                actor_id: day.world.agents[actor_id].location
                for actor_id in sorted(day.world.agents)
            },
            "institution_records": to_plain_data(day.world.institution.records),
        },
        "history": {
            "events": events,
            "observations": observations,
            "action_results": action_results,
            "understanding_transitions": [
                {
                    **to_plain_data(transition),
                    "dispatch": committed_dispatch(
                        "understanding_transition",
                        str(transition["trace_id"]),
                    ),
                }
                for transition in day.understanding_transitions
            ],
            "uncommitted_objective_tail": uncommitted_objective_tail,
        },
    }


def model_context_count_measurements(
    records: tuple[PolicyDecisionRecord, ...],
) -> dict[str, object]:
    """Measure private model-context shape without exposing its material."""

    decision_history = {
        "attempts_included": 0,
        "results_included": 0,
        "continuity_requirements_included": 0,
        "active_continuity_requirements": 0,
        "total_attempts": 0,
        "total_results": 0,
        "omitted_attempts": 0,
        "omitted_results": 0,
    }
    understanding = {
        "beliefs": 0,
        "memory_traces": 0,
        "interpreted_claims": 0,
        "contextual_stance_present": 0,
    }
    peak_delivered_observation_count = 0

    for record in records:
        model_input = record.model_input
        history = model_input.get("decision_history")
        if isinstance(history, Mapping):
            projection = history.get("projection")
            if isinstance(projection, Mapping):
                for field in (
                    "total_attempts",
                    "total_results",
                    "omitted_attempts",
                    "omitted_results",
                ):
                    value = projection.get(field)
                    if isinstance(value, int) and not isinstance(value, bool):
                        decision_history[field] = max(decision_history[field], value)
                active_requirements = projection.get(
                    "explicit_relevant_actions"
                )
                if isinstance(active_requirements, int) and not isinstance(
                    active_requirements, bool
                ):
                    decision_history["active_continuity_requirements"] = max(
                        decision_history["active_continuity_requirements"],
                        active_requirements,
                    )
            for field, input_field in (
                ("attempts_included", "attempts"),
                ("results_included", "results"),
                ("continuity_requirements_included", "continuity_requirements"),
            ):
                entries = history.get(input_field)
                if isinstance(entries, tuple):
                    decision_history[field] = max(
                        decision_history[field], len(entries)
                    )

        delivered_observations = model_input.get("delivered_observations")
        if isinstance(delivered_observations, tuple):
            peak_delivered_observation_count = max(
                peak_delivered_observation_count, len(delivered_observations)
            )

        model_understanding = model_input.get("understanding")
        if isinstance(model_understanding, Mapping):
            for field in ("beliefs", "memory_traces", "interpreted_claims"):
                entries = model_understanding.get(field)
                if isinstance(entries, tuple):
                    understanding[field] = max(understanding[field], len(entries))
            if model_understanding.get("contextual_stance") is not None:
                understanding["contextual_stance_present"] = 1

    return {
        "decision_history": decision_history,
        "peak_delivered_observation_count": peak_delivered_observation_count,
        "understanding": understanding,
    }


def render_autonomous_day_inspector(
    day: AutonomousDay,
    summary: DayRunSummary,
) -> str:
    return (
        "2084 AUTONOMOUS DAY INSPECTOR — OMNISCIENT\n"
        "Not part of the normal observer experience.\n"
        + json.dumps(
            autonomous_day_inspector_data(day, summary),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _cli_mara_harness(
    *,
    policy_name: str,
    ollama_base_url: str | None,
    ollama_model: str | None,
    mara_harness_factory: Callable[..., MaraHarness],
) -> MaraHarness | None:
    """Construct only the explicitly selected exact-model live harness."""

    if policy_name == "offline":
        return None
    if policy_name != "ollama":
        raise ValueError("unsupported focal policy")
    if ollama_base_url is None or not ollama_base_url.strip():
        raise ValueError("Ollama base URL is required")
    if ollama_model is None or not ollama_model.strip():
        raise ValueError("Ollama model is required")
    if ollama_model.strip() != AD12_OLLAMA_MODEL:
        raise ValueError(
            f"Ollama model must be {AD12_OLLAMA_MODEL} for this integration"
        )
    return mara_harness_factory(
        base_url=ollama_base_url,
        model=ollama_model.strip(),
    )


def main(
    argv: list[str] | None = None,
    *,
    mara_harness_factory: Callable[..., MaraHarness] = MaraHarness.from_ollama,
    ollama_identity_factory: Callable[..., Mapping[str, object]] | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        description="Run the narrow 2084 autonomous-day successor"
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--focal-policy",
        choices=("offline", "ollama"),
        default="offline",
        help="choose the offline default or the explicit live Ollama policy",
    )
    parser.add_argument(
        "--ollama-base-url",
        help="private Ollama origin, required only with --focal-policy ollama",
    )
    parser.add_argument(
        "--ollama-model",
        help="Ollama model name, required only with --focal-policy ollama",
    )
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="show explicitly omniscient successor-day evidence",
    )
    parser.add_argument(
        "--audit-dir",
        help="write one new private live-run audit bundle to this directory",
    )
    args = parser.parse_args(argv)

    if args.focal_policy == "ollama" and (
        args.ollama_base_url is None
        or not args.ollama_base_url.strip()
        or args.ollama_model is None
        or not args.ollama_model.strip()
    ):
        parser.error(
            "--ollama-base-url and --ollama-model are required with "
            "--focal-policy ollama"
        )
    if args.focal_policy == "offline" and (
        args.ollama_base_url is not None or args.ollama_model is not None
    ):
        parser.error(
            "--ollama-base-url and --ollama-model require --focal-policy ollama"
        )
    if args.audit_dir is not None and args.focal_policy != "ollama":
        parser.error("--audit-dir requires --focal-policy ollama")
    try:
        mara_harness = _cli_mara_harness(
            policy_name=args.focal_policy,
            ollama_base_url=args.ollama_base_url,
            ollama_model=args.ollama_model,
            mara_harness_factory=mara_harness_factory,
        )
    except ValueError as error:
        parser.error(str(error))

    audit_reservation = None
    audit_source_before = None
    audit_model_identity = None
    if args.audit_dir is not None:
        from scenarios.autonomous_day_audit import (
            capture_live_audit_source_state,
            fetch_ollama_model_identity,
            reserve_live_audit_directory,
        )

        try:
            audit_reservation = reserve_live_audit_directory(args.audit_dir)
            audit_source_before = capture_live_audit_source_state()
            identity_factory = (
                fetch_ollama_model_identity
                if ollama_identity_factory is None
                else ollama_identity_factory
            )
            audit_model_identity = identity_factory(
                base_url=args.ollama_base_url,
                model=args.ollama_model,
            )
        except (OSError, RuntimeError, ValueError) as error:
            parser.error(str(error))

    day = build_autonomous_day(seed=args.seed, mara_harness=mara_harness)
    try:
        summary = day.run()
    except Exception:
        summary = day.runtime.summary()
        if summary.runtime_failure is None:
            raise
    output = (
        render_autonomous_day_inspector(day, summary)
        if args.inspect
        else render_autonomous_day(day, summary)
    )
    print(output, end="")
    audit_passed = True
    if args.audit_dir is not None:
        from scenarios.autonomous_day_audit import write_autonomous_day_live_audit

        try:
            audit = write_autonomous_day_live_audit(
                day=day,
                summary=summary,
                directory=args.audit_dir,
                ollama_base_url=args.ollama_base_url,
                ollama_model=args.ollama_model,
                source_before=audit_source_before,
                model_identity=audit_model_identity,
                reservation=audit_reservation,
            )
            audit_passed = audit.passed
        except (OSError, RuntimeError, ValueError) as error:
            print(
                f"Live audit bundle failed: {type(error).__name__}",
                file=sys.stderr,
            )
            audit_passed = False
    return 0 if summary.reached_end_boundary and audit_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
