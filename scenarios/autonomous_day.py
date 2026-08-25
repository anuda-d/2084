"""Concrete successor world for one accelerated autonomous day."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass

from simulation.actions import ActionAttempt, ActionResult, PendingAction
from simulation.agents import AgentState
from simulation.day_runtime import AcceleratedDayRuntime, DayRunSummary, DayWorkContext
from simulation.events import Event, EventLog, Observation, to_plain_data
from simulation.institutions import InstitutionState
from simulation.official_record import OfficialRecord
from simulation.scheduling import ScheduledWork, TemporalPhase
from simulation.time import SimulatedTime
from simulation.world import ResourceState, WorldState


MARA_ID = "mara-vale"
ILAN_ID = "ilan-reed"
TRANSIT_AUTHORITY_ID = "district-transit-authority"

_SUPPORTING_WORK_START = "autonomous_day_supporting_work_start"
_SUPPORTING_WORK_COMPLETION = "autonomous_day_supporting_work_completion"
_INSTITUTIONAL_SERVICE_CHANGE = "autonomous_day_institutional_service_change"
_TRANSIT_BULLETIN_DELIVERY = "autonomous_day_transit_bulletin_delivery"

_ILAN_WORK_START_MINUTE = 8 * 60
_TRANSIT_CHANGE_MINUTE = 8 * 60 + 30
_ILAN_WORK_DURATION_MINUTES = 2 * 60
_TRANSIT_BULLETIN_MINUTE = 11 * 60
_TRANSIT_BULLETIN_LOCATIONS = frozenset({"home"})


@dataclass
class AutonomousDay:
    """One world, event history, and accelerated-day executor."""

    world: WorldState
    runtime: AcceleratedDayRuntime
    _event_log: EventLog
    _pending_actions: dict[str, PendingAction]

    @property
    def events(self) -> tuple[Event, ...]:
        return self._event_log.events

    @property
    def observations(self) -> tuple[Observation, ...]:
        return self._event_log.observations

    @property
    def pending_action_count(self) -> int:
        return len(self._pending_actions)

    def run(self) -> DayRunSummary:
        return self.runtime.run()


def build_autonomous_day(*, seed: int = 42) -> AutonomousDay:
    """Build the first concrete world hosted by the successor day runtime."""

    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")

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
            },
        )
        mara.observations.append(observation)

    runtime = AcceleratedDayRuntime(
        start=SimulatedTime(0),
        handlers={
            _SUPPORTING_WORK_START: start_supporting_work,
            _SUPPORTING_WORK_COMPLETION: complete_supporting_work,
            _INSTITUTIONAL_SERVICE_CHANGE: change_transit_service,
            _TRANSIT_BULLETIN_DELIVERY: deliver_transit_bulletin,
        },
        model_backed_actor_ids=(MARA_ID,),
        on_time_advanced=lambda current: setattr(
            world,
            "tick",
            current.total_minutes,
        ),
    )
    runtime.schedule(
        ScheduledWork(
            item_id="ilan-morning-ledger-shift-start",
            due_time=SimulatedTime(_ILAN_WORK_START_MINUTE),
            phase=TemporalPhase.SCHEDULED_WORLD,
            kind=_SUPPORTING_WORK_START,
        )
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
    )


def render_autonomous_day(day: AutonomousDay, summary: DayRunSummary) -> str:
    """Render only focal-safe evidence from the narrow successor day."""

    lines = [
        "2084 — AUTONOMOUS DAY",
        "Normal observer: focal-character knowledge only",
        "",
        f"Start: {summary.start.label} | Mara at Home",
    ]
    focal_updates: list[tuple[SimulatedTime, str]] = []
    for observation in day.world.agents[MARA_ID].observations:
        if observation.details.get("evidence_kind") != "transit_service_status":
            continue
        delivered_at = SimulatedTime(observation.delivery_tick)
        focal_updates.append(
            (
                delivered_at,
                f"{delivered_at.label} | Home transit bulletin: "
                f"{observation.details['route']} service is "
                f"{observation.details['current_status']}.",
            )
        )
    current_visible_time = summary.start
    for delivered_at, update in sorted(focal_updates):
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

    events = [
        {
            "event_id": event.event_id,
            "tick": event.tick,
            "kind": event.kind,
            "actor_id": event.actor_id,
            "action_id": event.action_id,
            "caused_by": list(event.caused_by),
            "details": to_plain_data(event.details),
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
        }
        for observation in day.observations
    ]
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
        }
        for actor_id in sorted(day.world.agents)
        for result in day.world.agents[actor_id].action_results
    ]
    return {
        "runtime": summary.to_data(),
        "counts": {
            "events": len(events),
            "observations": len(observations),
            "action_results": len(action_results),
        },
        "model_path": {
            "configured": False,
            "exercised": False,
            "provider_failure_count": None,
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
        },
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the narrow offline 2084 autonomous-day successor"
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="show explicitly omniscient successor-day evidence",
    )
    args = parser.parse_args(argv)

    day = build_autonomous_day(seed=args.seed)
    summary = day.run()
    output = (
        render_autonomous_day_inspector(day, summary)
        if args.inspect
        else render_autonomous_day(day, summary)
    )
    print(output, end="")
    return 0 if summary.reached_end_boundary else 1


if __name__ == "__main__":
    raise SystemExit(main())
