"""Reusable engine for the first living simulation slice."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Mapping

from simulation.actions import ACTION_KINDS, ActionAttempt, ActionResult, PendingAction
from simulation.agents import AgentView, DecisionPolicy, DiaryEntryKnowledge
from simulation.beliefs import (
    Belief,
    BeliefTransition,
    belief_from_claim_observation,
    link_conflicts,
)
from simulation.events import (
    Event,
    EventLog,
    Observation,
    freeze_mapping,
    to_plain_data,
)
from simulation.institutions import (
    InstitutionDecisionPolicy,
    InstitutionView,
    OfficialRecordRewrite,
)
from simulation.understanding import (
    StanceTransition,
    link_official_version_conflicts,
    select_public_counter_stance,
    trace_from_delivered_observation,
)
from simulation.world import DiaryEntry, PhysicalDiary, WorldState


@dataclass(frozen=True)
class FocalSnapshot:
    tick: int
    location: str
    aim: str
    required_units: int
    held_units: int
    remaining_required_units: int
    current_action: str
    explanation: str
    new_observations: tuple[Observation, ...]
    new_action_results: tuple[ActionResult, ...]
    beliefs: tuple[Belief, ...]
    accessible_diary_entry_count: int
    diary_entries: tuple[DiaryEntryKnowledge, ...]


@dataclass(frozen=True)
class SimulationRules:
    work_location: str
    allocation_location: str
    resource_id: str
    resource_proposition: str
    official_record_access_location: str
    official_record_artifact_id: str
    public_conformity_threshold: float = 0.7
    travel_duration_ticks: int = 2
    work_duration_ticks: int = 2
    diary_write_duration_ticks: int = 2
    diary_read_duration_ticks: int = 1


class Simulation:
    """Advance objective state, agents, and a restricted focal projection one tick."""

    def __init__(
        self,
        *,
        world: WorldState,
        policies: Mapping[str, DecisionPolicy],
        institution_policy: InstitutionDecisionPolicy,
        rules: SimulationRules,
        focal_agent_id: str,
        max_ticks: int,
        completion_tick: int,
        scenario_configuration: Mapping[str, object],
    ) -> None:
        self.world = world
        self._policies = dict(policies)
        self._institution_policy = institution_policy
        self.rules = rules
        self.focal_agent_id = focal_agent_id
        self.max_ticks = max_ticks
        self.completion_tick = completion_tick
        self.scenario_configuration = freeze_mapping(scenario_configuration)
        self._rng = random.Random(world.seed)
        self._event_log = EventLog()
        self._pending: dict[str, PendingAction] = {}
        self._action_count = 0
        self._belief_counts: dict[str, int] = {}
        self._belief_transitions: list[BeliefTransition] = []
        self._memory_trace_counts: dict[str, int] = {}
        self._interpreted_claim_counts: dict[str, int] = {}
        self._stance_transitions: list[StanceTransition] = []
        self._action_results: list[ActionResult] = []
        self._snapshots: list[FocalSnapshot] = []
        self._queued_observations: list[dict[str, object]] = []

    @property
    def tick(self) -> int:
        return self.world.tick

    @property
    def events(self) -> tuple[Event, ...]:
        return self._event_log.events

    def observations_for(self, agent_id: str) -> tuple[Observation, ...]:
        return tuple(self.world.agents[agent_id].observations)

    @property
    def snapshots(self) -> tuple[FocalSnapshot, ...]:
        return tuple(self._snapshots)

    @property
    def is_complete(self) -> bool:
        focal_work_completions = sum(
            1
            for event in self.events
            if event.kind == "work_completed" and event.actor_id == self.focal_agent_id
        )
        diary_was_read = any(
            event.kind == "diary_read_completed" and event.actor_id == self.focal_agent_id
            for event in self.events
        )
        return (
            self.tick >= self.completion_tick
            and focal_work_completions >= 2
            and diary_was_read
        )

    def snapshot_at(self, tick: int) -> FocalSnapshot:
        if tick <= 0 or tick > len(self._snapshots):
            raise ValueError("snapshot tick has not been produced")
        return self._snapshots[tick - 1]

    def _accessible_diary(self, agent_id: str) -> PhysicalDiary | None:
        agent = self.world.agents[agent_id]
        return next(
            (
                diary
                for diary in self.world.diaries.values()
                if diary.possessor_id == agent_id
                or (diary.possessor_id is None and diary.location == agent.location)
            ),
            None,
        )

    def _view_for(self, agent_id: str) -> AgentView:
        agent = self.world.agents[agent_id]
        diary = self._accessible_diary(agent_id)
        held_units = (
            agent.resource_holdings.get(agent.required_resource_id, 0)
            if agent.required_resource_id is not None
            else 0
        )
        return AgentView(
            tick=self.tick,
            agent_id=agent.agent_id,
            location=agent.location,
            aim=agent.aim,
            required_resource_id=agent.required_resource_id,
            required_units=agent.required_units,
            resource_holdings=freeze_mapping(agent.resource_holdings),
            remaining_required_units=max(0, agent.required_units - held_units),
            obligations=agent.obligations,
            last_attempt=agent.last_attempt,
            action_history=tuple(agent.action_history),
            action_results=tuple(agent.action_results),
            observations=tuple(agent.observations),
            beliefs=tuple(agent.beliefs),
            contextual_stance=agent.contextual_stance,
            accessible_diary_id=diary.object_id if diary is not None else None,
            accessible_diary_entry_count=len(diary.entries) if diary is not None else 0,
            accessible_diary_entries=tuple(
                DiaryEntryKnowledge(
                    entry_id=entry.entry_id,
                    proposition=entry.proposition,
                    asserted_value=entry.asserted_value,
                    source_observation_ids=entry.source_observation_ids,
                    started_tick=entry.started_tick,
                    completed_tick=entry.completed_tick,
                )
                for entry in (diary.entries if diary is not None else ())
            ),
            consultable_official_record_ids=(
                (self.rules.official_record_artifact_id,)
                if agent.location == self.rules.official_record_access_location
                and self.rules.official_record_artifact_id
                == self.world.institution.official_record.artifact_id
                else ()
            ),
            valid_actions=tuple(sorted(ACTION_KINDS)),
        )

    def agent_view(self, agent_id: str) -> AgentView:
        """Return the same restricted immutable input used by a decision policy."""
        if agent_id not in self.world.agents:
            raise ValueError(f"unknown agent_id: {agent_id}")
        return self._view_for(agent_id)

    def _record_rejection(self, *, attempted: Event, actor_id: str, reason: str) -> Event:
        rejected = self._event_log.record(
            tick=self.tick,
            kind="action_rejected",
            actor_id=actor_id,
            action_id=attempted.action_id,
            caused_by=(attempted.event_id,),
            details={"reason": reason},
        )
        self._append_action_result(
            ActionResult(
                action_id=attempted.action_id or "",
                attempt_event_id=attempted.event_id,
                outcome_event_id=rejected.event_id,
                actor_id=actor_id,
                action_kind=attempted.details["action_kind"],
                status="rejected",
                resolved_tick=self.tick,
                reason=reason,
            )
        )
        return rejected

    def _append_action_result(self, result: ActionResult) -> None:
        self._action_results.append(result)
        actor = self.world.agents.get(result.actor_id)
        if actor is not None:
            actor.action_results.append(result)

    def _record_completion(
        self, *, attempted: Event, outcome: Event, actor_id: str, action_kind: str
    ) -> None:
        self._append_action_result(
            ActionResult(
                action_id=attempted.action_id or "",
                attempt_event_id=attempted.event_id,
                outcome_event_id=outcome.event_id,
                actor_id=actor_id,
                action_kind=action_kind,
                status="completed",
                resolved_tick=self.tick,
            )
        )

    def _validate_speak(self, actor_id: str, attempt: ActionAttempt) -> str | None:
        proposition = attempt.parameters.get("proposition")
        if not isinstance(proposition, str) or not proposition.strip():
            return "speak requires a non-empty proposition"
        asserted_value = attempt.parameters.get("asserted_value")
        if not isinstance(asserted_value, int) or isinstance(asserted_value, bool):
            return "speak requires an integer asserted_value"
        evidence_ids = attempt.parameters.get("evidence_observation_ids")
        if (
            not isinstance(evidence_ids, (tuple, list))
            or not evidence_ids
            or any(not isinstance(item, str) or not item for item in evidence_ids)
        ):
            return "speak requires delivered evidence observation identifiers"
        if len(set(evidence_ids)) != len(evidence_ids):
            return "speak evidence observation identifiers must be unique"
        actor = self.world.agents[actor_id]
        delivered_ids = {observation.observation_id for observation in actor.observations}
        if not set(evidence_ids).issubset(delivered_ids):
            return "speak evidence must have been delivered to the actor"
        private_belief_id = attempt.parameters.get("private_belief_id")
        if private_belief_id is not None:
            belief = next(
                (
                    belief
                    for belief in actor.beliefs
                    if belief.belief_id == private_belief_id
                ),
                None,
            )
            if belief is None or belief.proposition != proposition:
                return "speak private belief must belong to the actor and proposition"
        pressure = attempt.parameters.get("pressure")
        if pressure is not None:
            if (
                not isinstance(pressure, (int, float))
                or isinstance(pressure, bool)
                or not 0 < pressure <= 1
            ):
                return "speak pressure must be greater than zero and at most one"
            pressure_reason = attempt.parameters.get("pressure_reason")
            if not isinstance(pressure_reason, str) or not pressure_reason.strip():
                return "speak pressure requires a non-empty reason"
        return None

    def _unexpected_parameter_error(self, attempt: ActionAttempt) -> str | None:
        allowed_by_kind = {
            "travel": {"destination"},
            "work": set(),
            "consult_official_record": {"artifact_id"},
            "request_allocation": {"requested_units", "evidence_observation_ids"},
            "speak": {
                "proposition",
                "asserted_value",
                "private_belief_id",
                "evidence_observation_ids",
                "pressure_reason",
                "pressure",
            },
            "write_diary": {
                "object_id",
                "proposition",
                "asserted_value",
                "source_observation_ids",
            },
            "read_diary": {"object_id", "entry_id"},
            "wait": set(),
        }
        unexpected = sorted(set(attempt.parameters) - allowed_by_kind[attempt.kind])
        if not unexpected:
            return None
        return f"{attempt.kind} contains unexpected parameters: " + ", ".join(
            unexpected
        )

    def _evidence_id_error(
        self,
        *,
        actor_id: str,
        value: object,
        label: str,
        required: bool,
    ) -> str | None:
        if value is None and not required:
            return None
        if (
            not isinstance(value, (tuple, list))
            or (required and not value)
            or any(not isinstance(item, str) or not item for item in value)
        ):
            return f"{label} must contain observation identifiers"
        if len(set(value)) != len(value):
            return f"{label} observation identifiers must be unique"
        delivered_ids = {
            observation.observation_id
            for observation in self.world.agents[actor_id].observations
        }
        if not set(value).issubset(delivered_ids):
            return f"{label} must have been delivered to the actor"
        return None

    def _validate_diary_write(self, actor_id: str, attempt: ActionAttempt) -> str | None:
        proposition = attempt.parameters.get("proposition")
        if not isinstance(proposition, str) or not proposition.strip():
            return "diary write requires a non-empty proposition"
        asserted_value = attempt.parameters.get("asserted_value")
        if not isinstance(asserted_value, int) or isinstance(asserted_value, bool):
            return "diary write requires an integer asserted_value"
        evidence_ids = attempt.parameters.get("source_observation_ids")
        evidence_error = self._evidence_id_error(
            actor_id=actor_id,
            value=evidence_ids,
            label="diary sources",
            required=True,
        )
        if evidence_error is not None:
            return evidence_error
        actor = self.world.agents[actor_id]
        matches_belief = any(
            belief.proposition == proposition
            and belief.asserted_value == asserted_value
            and belief.source_observation_ids == tuple(evidence_ids)
            for belief in actor.beliefs
        )
        matching_trace = next(
            (
                trace
                for trace in actor.memory_traces
                if trace.proposition == proposition
                and trace.asserted_value == asserted_value
                and (trace.source_observation_id,) == tuple(evidence_ids)
            ),
            None,
        )
        matches_interpreted_claim = matching_trace is not None and any(
            claim.claim_id == matching_trace.interpreted_claim_id
            and claim.proposition == proposition
            and claim.asserted_value == asserted_value
            for claim in actor.interpreted_claims
        )
        if not matches_belief and not matches_interpreted_claim:
            return "diary perspective must match actor understanding and its sources"
        return None

    def resolve_attempt(self, attempt: ActionAttempt) -> Event:
        """Record and validate an attempt; consequences remain a separate event."""
        self._action_count += 1
        action_id = f"action-{self._action_count:04d}"
        attempted = self._event_log.record(
            tick=self.tick,
            kind="action_attempted",
            actor_id=attempt.actor_id,
            action_id=action_id,
            details={
                "action_kind": attempt.kind,
                "decision_explanation": attempt.decision_reason or attempt.explanation,
                **dict(attempt.parameters),
            },
        )
        actor = self.world.agents.get(attempt.actor_id)
        if actor is None:
            self._record_rejection(
                attempted=attempted,
                actor_id=attempt.actor_id,
                reason="action actor is not registered in the world",
            )
            return attempted
        actor.last_attempt = attempt
        actor.action_history.append(attempt)
        parameter_error = self._unexpected_parameter_error(attempt)
        if parameter_error is not None:
            self._record_rejection(
                attempted=attempted,
                actor_id=attempt.actor_id,
                reason=parameter_error,
            )
            return attempted
        if attempt.actor_id in self._pending:
            self._record_rejection(
                attempted=attempted,
                actor_id=attempt.actor_id,
                reason="another action is already in progress",
            )
            return attempted
        if attempt.kind == "travel":
            destination = attempt.parameters.get("destination")
            if not isinstance(destination, str) or not self.world.can_travel(
                actor.location, destination
            ):
                self._record_rejection(
                    attempted=attempted,
                    actor_id=attempt.actor_id,
                    reason="destination is not reachable from the current location",
                )
                return attempted
            self._pending[attempt.actor_id] = PendingAction(
                action_id=action_id,
                attempt_event_id=attempted.event_id,
                attempt=attempt,
                started_tick=self.tick,
                completes_tick=self.tick + self.rules.travel_duration_ticks,
            )
        elif attempt.kind == "consult_official_record":
            artifact_id = attempt.parameters.get("artifact_id")
            record = self.world.institution.official_record
            if actor.location != self.rules.official_record_access_location:
                self._record_rejection(
                    attempted=attempted,
                    actor_id=attempt.actor_id,
                    reason=(
                        "consult_official_record requires presence at "
                        + self.rules.official_record_access_location
                    ),
                )
            elif (
                artifact_id != self.rules.official_record_artifact_id
                or artifact_id != record.artifact_id
            ):
                self._record_rejection(
                    attempted=attempted,
                    actor_id=attempt.actor_id,
                    reason="official record artifact is not available for consultation",
                )
            elif record.current_version is None:
                self._record_rejection(
                    attempted=attempted,
                    actor_id=attempt.actor_id,
                    reason="official record has no current published version",
                )
            else:
                version = record.current_version
                publication_event = next(
                    (
                        event
                        for event in reversed(self.events)
                        if event.kind
                        in {"official_record_published", "official_record_rewritten"}
                        and event.details.get("artifact_id") == version.artifact_id
                        and event.details.get("version_id") == version.version_id
                    ),
                    None,
                )
                if publication_event is None:
                    self._record_rejection(
                        attempted=attempted,
                        actor_id=attempt.actor_id,
                        reason="official record version has no publication evidence",
                    )
                else:
                    consultation = self._event_log.record(
                        tick=self.tick,
                        kind="official_record_consulted",
                        actor_id=attempt.actor_id,
                        action_id=action_id,
                        caused_by=(attempted.event_id, publication_event.event_id),
                        details={
                            "artifact_id": version.artifact_id,
                            "version_id": version.version_id,
                            "period_id": version.period_id,
                            "entitlement_packets": version.entitlement_packets,
                            "previous_version_id": version.previous_version_id,
                            "publication_event_id": publication_event.event_id,
                        },
                    )
                    self._record_completion(
                        attempted=attempted,
                        outcome=consultation,
                        actor_id=attempt.actor_id,
                        action_kind=attempt.kind,
                    )
                    self._queued_observations.append(
                        {
                            "delivery_tick": self.tick + 1,
                            "agent_id": attempt.actor_id,
                            "event_id": consultation.event_id,
                            "source": self.world.institution.display_name + " public record",
                            "details": {
                                "evidence_kind": "official_record_version",
                                "artifact_id": version.artifact_id,
                                "version_id": version.version_id,
                                "period_id": version.period_id,
                                "proposition": "weekly_household_ration_entitlement_packets",
                                "asserted_value": version.entitlement_packets,
                                "previous_version_id": version.previous_version_id,
                                "publication_event_id": publication_event.event_id,
                            },
                        }
                    )
        elif attempt.kind == "request_allocation":
            if actor.location != self.rules.allocation_location:
                self._record_rejection(
                    attempted=attempted,
                    actor_id=attempt.actor_id,
                    reason=(
                        "request_allocation requires presence at "
                        + self.rules.allocation_location
                    ),
                )
            else:
                requested = attempt.parameters.get("requested_units")
                evidence_error = self._evidence_id_error(
                    actor_id=attempt.actor_id,
                    value=attempt.parameters.get("evidence_observation_ids"),
                    label="request evidence",
                    required=False,
                )
                if evidence_error is not None:
                    self._record_rejection(
                        attempted=attempted,
                        actor_id=attempt.actor_id,
                        reason=evidence_error,
                    )
                elif (
                    not isinstance(requested, int)
                    or isinstance(requested, bool)
                    or requested <= 0
                ):
                    self._record_rejection(
                        attempted=attempted,
                        actor_id=attempt.actor_id,
                        reason="requested_units must be a positive integer",
                    )
                else:
                    available_before = self.world.resource.allocatable_units
                    granted = min(requested, available_before)
                    self.world.resource.granted_units += granted
                    outcome = self._event_log.record(
                        tick=self.tick,
                        kind="allocation_resolved",
                        actor_id=self.world.institution.institution_id,
                        action_id=action_id,
                        caused_by=(attempted.event_id,),
                        details={
                            "resource_id": self.rules.resource_id,
                            "requested_units": requested,
                            "granted_units": granted,
                            "unfilled_units": requested - granted,
                            "objective_allocatable_before": available_before,
                            "committed_units": self.world.resource.committed_units,
                            "recipient_id": attempt.actor_id,
                        },
                    )
                    self._record_completion(
                        attempted=attempted,
                        outcome=outcome,
                        actor_id=attempt.actor_id,
                        action_kind=attempt.kind,
                    )
                    self._queued_observations.append(
                        {
                            "delivery_tick": self.tick + 1,
                            "agent_id": attempt.actor_id,
                            "event_id": outcome.event_id,
                            "source": "allocation counter handover",
                            "resource_id": self.rules.resource_id,
                            "details": {
                                "evidence_kind": "allocation_outcome",
                                "resource_id": self.rules.resource_id,
                                "granted_units": granted,
                                "unfilled_units": requested - granted,
                            },
                        }
                    )
                    for observer_id, observer in self.world.agents.items():
                        if (
                            observer_id == attempt.actor_id
                            or observer.location != actor.location
                        ):
                            continue
                        self._queued_observations.append(
                            {
                                "delivery_tick": self.tick + 1,
                                "agent_id": observer_id,
                                "event_id": attempted.event_id,
                                "source": "visible allocation-counter activity",
                                "details": {
                                    "evidence_kind": "visible_allocation_request",
                                    "actor_id": attempt.actor_id,
                                    "requested_units": requested,
                                },
                            }
                        )
        elif attempt.kind == "speak":
            validation_error = self._validate_speak(attempt.actor_id, attempt)
            if validation_error is not None:
                self._record_rejection(
                    attempted=attempted,
                    actor_id=attempt.actor_id,
                    reason=validation_error,
                )
            else:
                evidence_ids = attempt.parameters["evidence_observation_ids"]
                statement = self._event_log.record(
                    tick=self.tick,
                    kind="public_statement_made",
                    actor_id=attempt.actor_id,
                    action_id=action_id,
                    caused_by=(attempted.event_id,),
                    details={
                        "proposition": attempt.parameters.get("proposition"),
                        "asserted_value": attempt.parameters.get("asserted_value"),
                        "private_belief_id": attempt.parameters.get("private_belief_id"),
                        "evidence_observation_ids": tuple(evidence_ids),
                        "pressure_reason": attempt.parameters.get("pressure_reason"),
                    },
                )
                self._record_completion(
                    attempted=attempted,
                    outcome=statement,
                    actor_id=attempt.actor_id,
                    action_kind=attempt.kind,
                )
                for observer_id, observer in self.world.agents.items():
                    if observer_id == attempt.actor_id or observer.location != actor.location:
                        continue
                    pressure_level = attempt.parameters.get("pressure")
                    is_pressure = (
                        isinstance(pressure_level, (int, float))
                        and not isinstance(pressure_level, bool)
                        and pressure_level > 0
                    )
                    perceived_details = {
                        "evidence_kind": (
                            "social_pressure" if is_pressure else "public_statement"
                        ),
                        "actor_id": attempt.actor_id,
                        "proposition": attempt.parameters.get("proposition"),
                        "asserted_value": attempt.parameters.get("asserted_value"),
                    }
                    if is_pressure:
                        perceived_details.update(
                            {
                                "pressure": pressure_level,
                                "reason": attempt.parameters.get("pressure_reason"),
                            }
                        )
                    self._queued_observations.append(
                        {
                            "delivery_tick": self.tick + 1,
                            "agent_id": observer_id,
                            "event_id": statement.event_id,
                            "source": actor.display_name,
                            "details": perceived_details,
                        }
                    )
        elif attempt.kind == "write_diary":
            object_id = attempt.parameters.get("object_id")
            diary = (
                self.world.diaries.get(object_id)
                if isinstance(object_id, str)
                else None
            )
            if diary is None or self._accessible_diary(actor.agent_id) is not diary:
                self._record_rejection(
                    attempted=attempted,
                    actor_id=attempt.actor_id,
                    reason="write_diary requires physical access to the diary",
                )
            elif (
                validation_error := self._validate_diary_write(
                    attempt.actor_id, attempt
                )
            ) is not None:
                self._record_rejection(
                    attempted=attempted,
                    actor_id=attempt.actor_id,
                    reason=validation_error,
                )
            else:
                self._pending[attempt.actor_id] = PendingAction(
                    action_id=action_id,
                    attempt_event_id=attempted.event_id,
                    attempt=attempt,
                    started_tick=self.tick,
                    completes_tick=self.tick + self.rules.diary_write_duration_ticks,
                )
        elif attempt.kind == "read_diary":
            object_id = attempt.parameters.get("object_id")
            diary = (
                self.world.diaries.get(object_id)
                if isinstance(object_id, str)
                else None
            )
            entry_id = attempt.parameters.get("entry_id")
            retained_entry = (
                next((entry for entry in diary.entries if entry.entry_id == entry_id), None)
                if diary is not None
                else None
            )
            if diary is None or self._accessible_diary(actor.agent_id) is not diary:
                reason = "read_diary requires physical access to the diary"
            elif retained_entry is None:
                reason = "read_diary requires an existing entry"
            else:
                reason = None
            if reason is not None:
                self._record_rejection(
                    attempted=attempted,
                    actor_id=attempt.actor_id,
                    reason=reason,
                )
            else:
                self._pending[attempt.actor_id] = PendingAction(
                    action_id=action_id,
                    attempt_event_id=attempted.event_id,
                    attempt=attempt,
                    started_tick=self.tick,
                    completes_tick=self.tick + self.rules.diary_read_duration_ticks,
                )
        elif attempt.kind == "wait":
            outcome = self._event_log.record(
                tick=self.tick,
                kind="wait_completed",
                actor_id=attempt.actor_id,
                action_id=action_id,
                caused_by=(attempted.event_id,),
                details={"location": actor.location},
            )
            self._record_completion(
                attempted=attempted,
                outcome=outcome,
                actor_id=attempt.actor_id,
                action_kind=attempt.kind,
            )
        elif attempt.kind == "work":
            if actor.location != self.rules.work_location:
                self._record_rejection(
                    attempted=attempted,
                    actor_id=attempt.actor_id,
                    reason="work requires presence at " + self.rules.work_location,
                )
            else:
                self._pending[attempt.actor_id] = PendingAction(
                    action_id=action_id,
                    attempt_event_id=attempted.event_id,
                    attempt=attempt,
                    started_tick=self.tick,
                    completes_tick=self.tick + self.rules.work_duration_ticks,
                )
        return attempted

    def _complete_due_actions(self) -> tuple[Event, ...]:
        completed: list[Event] = []
        due = sorted(
            (
                pending
                for pending in self._pending.values()
                if pending.completes_tick <= self.tick
            ),
            key=lambda pending: pending.action_id,
        )
        for pending in due:
            actor = self.world.agents[pending.attempt.actor_id]
            if pending.attempt.kind == "travel":
                origin = actor.location
                destination = pending.attempt.parameters["destination"]
                actor.location = destination
                completed.append(self._event_log.record(
                    tick=self.tick,
                    kind="travel_completed",
                    actor_id=actor.agent_id,
                    action_id=pending.action_id,
                    caused_by=(pending.attempt_event_id,),
                    details={"origin": origin, "destination": destination},
                ))
            elif pending.attempt.kind == "work":
                completed.append(self._event_log.record(
                    tick=self.tick,
                    kind="work_completed",
                    actor_id=actor.agent_id,
                    action_id=pending.action_id,
                    caused_by=(pending.attempt_event_id,),
                    details={"location": actor.location},
                ))
            elif pending.attempt.kind == "write_diary":
                diary = self.world.diaries[pending.attempt.parameters["object_id"]]
                entry = DiaryEntry(
                    entry_id=f"entry-{len(diary.entries) + 1:04d}",
                    author_id=actor.agent_id,
                    proposition=pending.attempt.parameters["proposition"],
                    asserted_value=pending.attempt.parameters["asserted_value"],
                    source_observation_ids=tuple(
                        pending.attempt.parameters["source_observation_ids"]
                    ),
                    started_tick=pending.started_tick,
                    completed_tick=self.tick,
                )
                diary.entries = diary.entries + (entry,)
                completed.append(self._event_log.record(
                    tick=self.tick,
                    kind="diary_write_completed",
                    actor_id=actor.agent_id,
                    action_id=pending.action_id,
                    caused_by=(pending.attempt_event_id,),
                    details={
                        "object_id": diary.object_id,
                        "entry_id": entry.entry_id,
                        "proposition": entry.proposition,
                        "asserted_value": entry.asserted_value,
                        "source_observation_ids": entry.source_observation_ids,
                        "started_tick": entry.started_tick,
                        "completed_tick": entry.completed_tick,
                    },
                ))
            elif pending.attempt.kind == "read_diary":
                diary = self.world.diaries[pending.attempt.parameters["object_id"]]
                entry = next(
                    entry
                    for entry in diary.entries
                    if entry.entry_id == pending.attempt.parameters["entry_id"]
                )
                completed.append(self._event_log.record(
                    tick=self.tick,
                    kind="diary_read_completed",
                    actor_id=actor.agent_id,
                    action_id=pending.action_id,
                    caused_by=(pending.attempt_event_id,),
                    details={
                        "object_id": diary.object_id,
                        "entry_id": entry.entry_id,
                        "proposition": entry.proposition,
                        "asserted_value": entry.asserted_value,
                        "source_observation_ids": entry.source_observation_ids,
                        "started_tick": entry.started_tick,
                        "completed_tick": entry.completed_tick,
                        "read_tick": self.tick,
                    },
                ))
            outcome = completed[-1]
            self._append_action_result(
                ActionResult(
                    action_id=pending.action_id,
                    attempt_event_id=pending.attempt_event_id,
                    outcome_event_id=outcome.event_id,
                    actor_id=actor.agent_id,
                    action_kind=pending.attempt.kind,
                    status="completed",
                    resolved_tick=self.tick,
                )
            )
            del self._pending[actor.agent_id]
        return tuple(completed)

    def _deliver_completion_observations(
        self, completed_events: tuple[Event, ...]
    ) -> tuple[Observation, ...]:
        delivered: list[Observation] = []
        for event in completed_events:
            if event.actor_id is None:
                continue
            if event.kind == "travel_completed":
                source = "direct movement"
                details = {
                    "evidence_kind": "arrival",
                    "origin": event.details["origin"],
                    "destination": event.details["destination"],
                }
            elif event.kind == "work_completed":
                source = "direct work"
                details = {
                    "evidence_kind": "work_completed",
                    "location": event.details["location"],
                }
            elif event.kind == "diary_write_completed":
                source = "direct diary writing"
                details = {
                    "evidence_kind": "diary_write_completed",
                    "entry_id": event.details["entry_id"],
                    "proposition": event.details["proposition"],
                    "asserted_value": event.details["asserted_value"],
                    "source_observation_ids": event.details["source_observation_ids"],
                    "started_tick": event.details["started_tick"],
                    "completed_tick": event.details["completed_tick"],
                }
            elif event.kind == "diary_read_completed":
                source = "direct diary reading"
                details = {
                    "evidence_kind": "diary_read_completed",
                    "entry_id": event.details["entry_id"],
                    "proposition": event.details["proposition"],
                    "asserted_value": event.details["asserted_value"],
                    "source_observation_ids": event.details["source_observation_ids"],
                    "started_tick": event.details["started_tick"],
                    "completed_tick": event.details["completed_tick"],
                    "read_tick": event.details["read_tick"],
                }
            else:
                continue
            observation = self._event_log.deliver(
                agent_id=event.actor_id,
                event_id=event.event_id,
                source=source,
                delivery_tick=self.tick,
                details=details,
            )
            self.world.agents[event.actor_id].observations.append(observation)
            delivered.append(observation)
            if event.kind == "work_completed":
                actor_location = self.world.agents[event.actor_id].location
                for observer_id, observer in self.world.agents.items():
                    if observer_id == event.actor_id or observer.location != actor_location:
                        continue
                    visible = self._event_log.deliver(
                        agent_id=observer_id,
                        event_id=event.event_id,
                        source="visible workplace activity",
                        delivery_tick=self.tick,
                        details={
                            "evidence_kind": "visible_supporting_action",
                            "actor_id": event.actor_id,
                            "action_kind": "work",
                        },
                    )
                    observer.observations.append(visible)
                    delivered.append(visible)
            if (
                event.kind == "travel_completed"
                and event.details["destination"] == self.rules.allocation_location
            ):
                visible_resource_event = self._event_log.record(
                    tick=self.tick,
                    kind="resource_amount_seen",
                    actor_id=event.actor_id,
                    caused_by=(event.event_id,),
                    details={
                        "resource": self.rules.resource_id,
                        "visible_units": self.world.resource.total_units,
                    },
                )
                direct = self._event_log.deliver(
                    agent_id=event.actor_id,
                    event_id=visible_resource_event.event_id,
                    source="direct sight at the allocation counter",
                    delivery_tick=self.tick,
                    details={
                        "evidence_kind": "direct_resource_claim",
                        "proposition": self.rules.resource_proposition,
                        "asserted_value": self.world.resource.total_units,
                    },
                )
                self.world.agents[event.actor_id].observations.append(direct)
                delivered.append(direct)
        return tuple(delivered)

    def _update_beliefs(self, observations: tuple[Observation, ...]) -> None:
        for observation in observations:
            count = self._belief_counts.get(observation.agent_id, 0) + 1
            belief = belief_from_claim_observation(
                observation,
                belief_id=f"belief-{observation.agent_id}-{count:03d}",
            )
            if belief is None:
                continue
            self._belief_counts[observation.agent_id] = count
            beliefs = self.world.agents[observation.agent_id].beliefs
            belief = link_conflicts(beliefs, belief)
            beliefs.append(belief)
            self._belief_transitions.append(
                BeliefTransition(
                    transition_id=(
                        f"belief-transition-{len(self._belief_transitions) + 1:04d}"
                    ),
                    agent_id=observation.agent_id,
                    tick=observation.delivery_tick,
                    source_observation_id=observation.observation_id,
                    belief_id=belief.belief_id,
                    proposition=belief.proposition,
                    asserted_value=belief.asserted_value,
                    confidence=belief.confidence,
                    context=belief.context,
                    conflicts_with=belief.conflicts_with,
                )
            )

    def _update_understanding(self, observations: tuple[Observation, ...]) -> None:
        for observation in observations:
            if observation.agent_id != self.focal_agent_id:
                continue
            agent = self.world.agents[observation.agent_id]
            trace_count = self._memory_trace_counts.get(observation.agent_id, 0) + 1
            claim_count = self._interpreted_claim_counts.get(observation.agent_id, 0) + 1
            interpreted = trace_from_delivered_observation(
                observation,
                trace_id=f"memory-trace-{observation.agent_id}-{trace_count:03d}",
                claim_id=f"interpreted-claim-{observation.agent_id}-{claim_count:03d}",
                existing_claims=agent.interpreted_claims,
            )
            if interpreted is None:
                continue
            trace, new_claim = interpreted
            self._memory_trace_counts[observation.agent_id] = trace_count
            agent.memory_traces += (trace,)
            if new_claim is not None:
                self._interpreted_claim_counts[observation.agent_id] = claim_count
                agent.interpreted_claims = link_official_version_conflicts(
                    agent.interpreted_claims,
                    agent.memory_traces[:-1],
                    new_claim,
                    trace,
                )

    def _update_contextual_stance(self) -> None:
        focal = self.world.agents[self.focal_agent_id]
        previous = focal.contextual_stance
        selected = select_public_counter_stance(
            location=focal.location,
            counter_location=self.rules.allocation_location,
            pressure_threshold=self.rules.public_conformity_threshold,
            claims=focal.interpreted_claims,
            traces=focal.memory_traces,
            observations=tuple(focal.observations),
        )
        if selected == previous:
            return
        focal.contextual_stance = selected
        source_stance = selected if selected is not None else previous
        if source_stance is None:
            return
        self._stance_transitions.append(
            StanceTransition(
                transition_id=(
                    f"stance-transition-{len(self._stance_transitions) + 1:04d}"
                ),
                agent_id=focal.agent_id,
                tick=self.tick,
                context=source_stance.context,
                active=selected is not None,
                proposition=source_stance.proposition,
                asserted_value=source_stance.asserted_value,
                source_claim_id=source_stance.source_claim_id,
                source_trace_id=source_stance.source_trace_id,
                source_observation_ids=source_stance.source_observation_ids,
                pressure_observation_id=source_stance.pressure_observation_id,
                stance_selected_tick=source_stance.selected_tick,
            )
        )

    def _resolve_scheduled_official_record_rewrite(
        self, rewrite: OfficialRecordRewrite
    ) -> None:
        institution = self.world.institution
        attempted = self._event_log.record(
            tick=self.tick,
            kind="official_record_rewrite_attempted",
            actor_id=rewrite.actor_id,
            details={
                "reason": rewrite.reason,
                "artifact_id": rewrite.artifact_id,
                "expected_current_version_id": rewrite.expected_current_version_id,
                "version_id": rewrite.version_id,
                "period_id": rewrite.period_id,
                "entitlement_packets": rewrite.entitlement_packets,
            },
        )
        if (
            rewrite.actor_id
            not in institution.official_record_rewrite_authorized_actor_ids
        ):
            self._event_log.record(
                tick=self.tick,
                kind="official_record_rewrite_rejected",
                actor_id=rewrite.actor_id,
                caused_by=(attempted.event_id,),
                details={"reason": "actor is not authorized to rewrite this record"},
            )
            return

        prior_publication = next(
            (
                event
                for event in reversed(self.events)
                if event.kind in {"official_record_published", "official_record_rewritten"}
                and event.details.get("artifact_id") == rewrite.artifact_id
                and event.details.get("version_id")
                == rewrite.expected_current_version_id
            ),
            None,
        )
        try:
            version = institution.official_record.rewrite(
                artifact_id=rewrite.artifact_id,
                expected_current_version_id=rewrite.expected_current_version_id,
                version_id=rewrite.version_id,
                period_id=rewrite.period_id,
                entitlement_packets=rewrite.entitlement_packets,
            )
        except ValueError:
            self._event_log.record(
                tick=self.tick,
                kind="official_record_rewrite_rejected",
                actor_id=rewrite.actor_id,
                caused_by=(attempted.event_id,),
                details={"reason": "official record rejected the requested rewrite"},
            )
            return

        self._event_log.record(
            tick=self.tick,
            kind="official_record_rewritten",
            actor_id=rewrite.actor_id,
            caused_by=(
                (attempted.event_id, prior_publication.event_id)
                if prior_publication is not None
                else (attempted.event_id,)
            ),
            details={
                "reason": rewrite.reason,
                "artifact_id": version.artifact_id,
                "version_id": version.version_id,
                "period_id": version.period_id,
                "entitlement_packets": version.entitlement_packets,
                "previous_version_id": version.previous_version_id,
            },
        )

    def _apply_scheduled_institutional_events(self) -> tuple[Observation, ...]:
        institution = self.world.institution
        view = InstitutionView(
            tick=self.tick,
            records=dict(institution.records),
            reports=tuple(institution.reports),
        )
        publication = self._institution_policy.choose_initial_publication(view)
        if publication is not None:
            version = institution.official_record.publish_initial(
                artifact_id=publication.artifact_id,
                version_id=publication.version_id,
                period_id=publication.period_id,
                entitlement_packets=publication.entitlement_packets,
            )
            self._event_log.record(
                tick=self.tick,
                kind="official_record_published",
                actor_id=institution.institution_id,
                details={
                    "artifact_id": version.artifact_id,
                    "version_id": version.version_id,
                    "period_id": version.period_id,
                    "entitlement_packets": version.entitlement_packets,
                    "previous_version_id": version.previous_version_id,
                },
            )

        rewrite = self._institution_policy.choose_official_record_rewrite(view)
        if rewrite is not None:
            self._resolve_scheduled_official_record_rewrite(rewrite)

        claim = self._institution_policy.choose_claim(view)
        if claim is None:
            return ()
        prior_claim = institution.last_public_claim_event_id
        event = self._event_log.record(
            tick=self.tick,
            kind="official_claim_issued",
            actor_id=institution.institution_id,
            caused_by=(prior_claim,) if prior_claim is not None else (),
            details={
                "proposition": claim.proposition,
                "asserted_value": claim.asserted_value,
                "revises_event_id": prior_claim,
            },
        )
        institution.records["current_public_claim"] = claim.asserted_value
        institution.last_public_claim_event_id = event.event_id
        delivered: list[Observation] = []
        for agent_id in self.world.agents:
            observation = self._event_log.deliver(
                agent_id=agent_id,
                event_id=event.event_id,
                source=institution.display_name + " broadcast",
                delivery_tick=self.tick,
                details={
                    "evidence_kind": "official_resource_claim",
                    "proposition": claim.proposition,
                    "asserted_value": claim.asserted_value,
                    "revises_event_id": prior_claim,
                },
            )
            self.world.agents[agent_id].observations.append(observation)
            delivered.append(observation)
        return tuple(delivered)

    def _deliver_queued_observations(self) -> tuple[Observation, ...]:
        due = [
            item for item in self._queued_observations if item["delivery_tick"] == self.tick
        ]
        self._queued_observations = [
            item for item in self._queued_observations if item["delivery_tick"] != self.tick
        ]
        delivered: list[Observation] = []
        for item in due:
            observation = self._event_log.deliver(
                agent_id=item["agent_id"],
                event_id=item["event_id"],
                source=item["source"],
                delivery_tick=item["delivery_tick"],
                details=item["details"],
            )
            self.world.agents[observation.agent_id].observations.append(observation)
            if observation.details.get("evidence_kind") == "allocation_outcome":
                resource_id = item["resource_id"]
                holdings = self.world.agents[observation.agent_id].resource_holdings
                holdings[resource_id] = (
                    holdings.get(resource_id, 0)
                    + observation.details["granted_units"]
                )
            delivered.append(observation)
        return tuple(delivered)

    def step(self) -> FocalSnapshot:
        if self.is_complete:
            raise RuntimeError("simulation scenario is complete")
        if self.tick >= self.max_ticks:
            raise RuntimeError("simulation has reached its configured tick limit")
        self.world.tick += 1
        scheduled_deliveries = self._apply_scheduled_institutional_events()
        completed_events = self._complete_due_actions()
        delivered = (
            scheduled_deliveries
            + self._deliver_completion_observations(completed_events)
            + self._deliver_queued_observations()
        )
        self._update_beliefs(delivered)
        self._update_understanding(delivered)
        self._update_contextual_stance()
        focal_attempt: ActionAttempt | None = None
        for agent_id in sorted(self._policies):
            if agent_id in self._pending:
                continue
            attempt = self._policies[agent_id].choose(self._view_for(agent_id))
            self.resolve_attempt(attempt)
            if agent_id == self.focal_agent_id:
                focal_attempt = attempt

        focal = self.world.agents[self.focal_agent_id]
        focal_held_units = (
            focal.resource_holdings.get(focal.required_resource_id, 0)
            if focal.required_resource_id is not None
            else 0
        )
        accessible_diary = self._accessible_diary(self.focal_agent_id)
        diary_entries = tuple(
            DiaryEntryKnowledge(
                entry_id=entry.entry_id,
                proposition=entry.proposition,
                asserted_value=entry.asserted_value,
                source_observation_ids=entry.source_observation_ids,
                started_tick=entry.started_tick,
                completed_tick=entry.completed_tick,
            )
            for entry in (accessible_diary.entries if accessible_diary is not None else ())
        )
        if focal_attempt is None:
            pending = self._pending.get(self.focal_agent_id)
            current_action = pending.attempt.explanation if pending else "wait"
            explanation = (
                (pending.attempt.decision_reason or pending.attempt.explanation)
                if pending
                else "No new action selected."
            )
        else:
            current_action = focal_attempt.explanation
            explanation = focal_attempt.decision_reason or focal_attempt.explanation
        snapshot = FocalSnapshot(
            tick=self.tick,
            location=focal.location,
            aim=focal.aim,
            required_units=focal.required_units,
            held_units=focal_held_units,
            remaining_required_units=max(0, focal.required_units - focal_held_units),
            current_action=current_action,
            explanation=explanation,
            new_observations=tuple(
                observation
                for observation in delivered
                if observation.agent_id == self.focal_agent_id
            ),
            new_action_results=tuple(
                result
                for result in focal.action_results
                if result.resolved_tick == self.tick
            ),
            beliefs=tuple(focal.beliefs),
            accessible_diary_entry_count=(
                len(accessible_diary.entries) if accessible_diary is not None else 0
            ),
            diary_entries=diary_entries,
        )
        self._snapshots.append(snapshot)
        return snapshot

    def run(self, max_ticks: int = 30) -> tuple[FocalSnapshot, ...]:
        if not isinstance(max_ticks, int) or isinstance(max_ticks, bool) or max_ticks <= 0:
            raise ValueError("max_ticks must be a positive integer")
        stop_tick = min(max_ticks, self.max_ticks)
        while not self.is_complete and self.tick < stop_tick:
            self.step()
        return self.snapshots

    def history_data(self) -> dict[str, object]:
        """Return complete omniscient replay evidence as JSON-compatible data."""
        action_results = sorted(self._action_results, key=lambda result: result.action_id)
        return {
            "configuration": {
                "seed": self.world.seed,
                "max_ticks": self.max_ticks,
                "completion_tick": self.completion_tick,
                "focal_agent_id": self.focal_agent_id,
                "scenario": to_plain_data(self.scenario_configuration),
            },
            "official_record": self.world.institution.official_record.to_data(),
            "events": [
                {
                    "event_id": event.event_id,
                    "tick": event.tick,
                    "kind": event.kind,
                    "actor_id": event.actor_id,
                    "action_id": event.action_id,
                    "caused_by": list(event.caused_by),
                    "details": to_plain_data(event.details),
                }
                for event in self._event_log.events
            ],
            "observations": [
                {
                    "observation_id": observation.observation_id,
                    "agent_id": observation.agent_id,
                    "event_id": observation.event_id,
                    "source": observation.source,
                    "delivery_tick": observation.delivery_tick,
                    "details": to_plain_data(observation.details),
                }
                for observation in self._event_log.observations
            ],
            "action_results": [
                {
                    "action_id": result.action_id,
                    "attempt_event_id": result.attempt_event_id,
                    "outcome_event_id": result.outcome_event_id,
                    "actor_id": result.actor_id,
                    "action_kind": result.action_kind,
                    "status": result.status,
                    "resolved_tick": result.resolved_tick,
                    "reason": result.reason,
                }
                for result in action_results
            ],
            "agent_resource_holdings": {
                agent_id: dict(agent.resource_holdings)
                for agent_id, agent in self.world.agents.items()
            },
            "belief_transitions": [
                {
                    "transition_id": transition.transition_id,
                    "agent_id": transition.agent_id,
                    "tick": transition.tick,
                    "source_observation_id": transition.source_observation_id,
                    "belief_id": transition.belief_id,
                    "proposition": transition.proposition,
                    "asserted_value": transition.asserted_value,
                    "confidence": transition.confidence,
                    "context": transition.context,
                    "conflicts_with": list(transition.conflicts_with),
                }
                for transition in self._belief_transitions
            ],
            "stance_transitions": [
                {
                    "transition_id": transition.transition_id,
                    "agent_id": transition.agent_id,
                    "tick": transition.tick,
                    "context": transition.context,
                    "active": transition.active,
                    "proposition": transition.proposition,
                    "asserted_value": transition.asserted_value,
                    "source_claim_id": transition.source_claim_id,
                    "source_trace_id": transition.source_trace_id,
                    "source_observation_ids": list(
                        transition.source_observation_ids
                    ),
                    "pressure_observation_id": (
                        transition.pressure_observation_id
                    ),
                    "stance_selected_tick": transition.stance_selected_tick,
                }
                for transition in self._stance_transitions
            ],
            "agent_understanding": {
                agent_id: {
                    "memory_traces": [
                        {
                            "trace_id": trace.trace_id,
                            "source_observation_id": trace.source_observation_id,
                            "source_event_id": trace.source_event_id,
                            "source": trace.source,
                            "evidence_kind": trace.evidence_kind,
                            "interpreted_claim_id": trace.interpreted_claim_id,
                            "proposition": trace.proposition,
                            "asserted_value": trace.asserted_value,
                            "delivery_tick": trace.delivery_tick,
                            "period_id": trace.period_id,
                        }
                        for trace in agent.memory_traces
                    ],
                    "interpreted_claims": [
                        {
                            "claim_id": claim.claim_id,
                            "proposition": claim.proposition,
                            "asserted_value": claim.asserted_value,
                            "period_id": claim.period_id,
                            "origin_trace_id": claim.origin_trace_id,
                            "conflicts_with": list(claim.conflicts_with),
                        }
                        for claim in agent.interpreted_claims
                    ],
                    "contextual_stance": (
                        {
                            "context": agent.contextual_stance.context,
                            "proposition": agent.contextual_stance.proposition,
                            "asserted_value": agent.contextual_stance.asserted_value,
                            "source_claim_id": agent.contextual_stance.source_claim_id,
                            "source_trace_id": agent.contextual_stance.source_trace_id,
                            "source_observation_ids": list(
                                agent.contextual_stance.source_observation_ids
                            ),
                            "pressure_observation_id": (
                                agent.contextual_stance.pressure_observation_id
                            ),
                            "selected_tick": agent.contextual_stance.selected_tick,
                        }
                        if agent.contextual_stance is not None
                        else None
                    ),
                }
                for agent_id, agent in self.world.agents.items()
            },
        }

    def inspector_state(self) -> dict[str, object]:
        return {
            "tick": self.tick,
            "seed": self.world.seed,
            "agent_locations": {
                agent_id: agent.location for agent_id, agent in self.world.agents.items()
            },
            "agent_resource_holdings": {
                agent_id: dict(agent.resource_holdings)
                for agent_id, agent in self.world.agents.items()
            },
            "objective_resources": {
                "total_units": self.world.resource.total_units,
                "committed_units": self.world.resource.committed_units,
                "granted_units": self.world.resource.granted_units,
                "allocatable_units": self.world.resource.allocatable_units,
            },
            "diaries": {
                diary_id: {
                    "location": diary.location,
                    "possessor_id": diary.possessor_id,
                    "entries": [
                        {
                            "entry_id": entry.entry_id,
                            "author_id": entry.author_id,
                            "proposition": entry.proposition,
                            "asserted_value": entry.asserted_value,
                            "source_observation_ids": list(entry.source_observation_ids),
                            "started_tick": entry.started_tick,
                            "completed_tick": entry.completed_tick,
                        }
                        for entry in diary.entries
                    ],
                }
                for diary_id, diary in self.world.diaries.items()
            },
        }
