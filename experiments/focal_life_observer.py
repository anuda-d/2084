"""Normal-perspective transcript for the fixed focal-life experiment."""

from __future__ import annotations

from experiments.focal_life_scenario import (
    FocalLifeScenarioEvidence,
    run_provisional_focal_life_scenario,
)


def _unit_phrase(units: int) -> str:
    return f"{units} unit" if units == 1 else f"{units} units"


def render_focal_life_transcript(evidence: FocalLifeScenarioEvidence) -> str:
    """Render the fixed scenario using only focal-visible and decision evidence."""
    need = evidence.need
    request = evidence.request
    request_trace = request.trace
    observations_by_id = {
        observation.observation_id: observation
        for observation in evidence.follow_up_observations
    }

    lines = [
        "2084 focal-life observer (provisional)",
        (
            f"Need: {_unit_phrase(need.required_units)}; request limit: "
            f"{_unit_phrase(need.maximum_request_units)}."
        ),
    ]
    for observation in evidence.decision_observations:
        evidence_kind = observation.details["evidence_kind"].replace("_", " ")
        available_units = observation.details["available_units"]
        lines.append(
            f"Observed at tick {observation.delivery_tick} via {observation.source} "
            f"[{evidence_kind}]: {_unit_phrase(available_units)} available."
        )

    selected = observations_by_id[request_trace.selected_observation_id]
    selected_kind = selected.details["evidence_kind"].replace("_", " ")
    lines.extend(
        (
            f"Decision: request {_unit_phrase(request.requested_units)}.",
            (
                f"Reason: preferred {selected_kind} observation "
                f"{selected.observation_id} "
                f"({_unit_phrase(request_trace.selected_available_units)}), then "
                f"capped by need {need.required_units} and request limit "
                f"{need.maximum_request_units}."
            ),
        )
    )

    follow_up = evidence.follow_up
    follow_up_trace = follow_up.trace
    handover = observations_by_id[follow_up_trace.selected_observation_id]
    granted_units = handover.details["granted_units"]
    unfilled_units = handover.details["unfilled_units"]
    lines.extend(
        (
            (
                f"Delivered at tick {handover.delivery_tick} via {handover.source}: "
                f"{_unit_phrase(granted_units)} granted; "
                f"{_unit_phrase(unfilled_units)} unfilled."
            ),
            (
                f"Decision: {follow_up.choice.replace('_', ' ')} "
                f"({_unit_phrase(follow_up_trace.remaining_units)})."
            ),
            (
                f"Reason: handover {handover.observation_id} granted "
                f"{granted_units} of {follow_up_trace.required_units} needed, leaving "
                f"{_unit_phrase(follow_up_trace.remaining_units)}."
            ),
        )
    )

    outcome = evidence.follow_up_outcome_observation
    lines.append(
        f"Delivered at tick {outcome.delivery_tick} via {outcome.source}: "
        f"{_unit_phrase(outcome.details['granted_units'])} granted; "
        f"{_unit_phrase(outcome.details['unfilled_units'])} unfilled."
    )
    pressure = evidence.focal_pressure_observation
    pressure_action = pressure.details["action"].replace("_", " ")
    lines.append(
        f"Social pressure delivered at tick {pressure.delivery_tick} via "
        f"{pressure.source}: {pressure_action}."
    )
    third_choice = evidence.third_choice
    third_trace = third_choice.trace
    lines.extend(
        (
            (
                "Remaining-need constraint: "
                f"{_unit_phrase(third_trace.remaining_need_units)} from "
                f"follow-up outcome {third_trace.selected_observation_id}."
            ),
            f"Decision: {third_choice.choice.replace('_', ' ')}.",
            (
                f"Reason: follow-up outcome "
                f"{third_trace.selected_observation_id} granted "
                f"{_unit_phrase(third_trace.observed_granted_units)} and left "
                f"{_unit_phrase(third_trace.observed_unfilled_units)} unfilled; "
                f"pressure {third_trace.selected_pressure_observation_id} said "
                f"{pressure_action}; "
                f"rule: {third_trace.rule}."
            ),
        )
    )
    alternative_outcome = evidence.third_choice_outcome_observation
    if alternative_outcome is not None:
        lines.append(
            f"Resolved at tick {alternative_outcome.delivery_tick} via "
            f"{alternative_outcome.source}: "
            f"{_unit_phrase(alternative_outcome.details['granted_units'])} granted; "
            f"{_unit_phrase(alternative_outcome.details['unfilled_units'])} unfilled."
        )
    private = evidence.private_availability_belief
    public = evidence.public_expression
    lines.extend(
        (
            (
                f"Private belief: {_unit_phrase(private.units)} available from "
                f"direct observation {private.source_observation_id}."
            ),
            f"Public expression: {_unit_phrase(public.expressed_units)} available.",
            (
                f"Reason: pressure {public.trace.selected_pressure_observation_id} "
                f"urged public agreement, so official claim "
                f"{public.trace.selected_official_observation_id} was repeated while "
                "the private belief remained unchanged."
            ),
        )
    )
    diary_write = evidence.diary_write
    diary_read = evidence.diary_read
    lines.extend(
        (
            (
                "Diary write (private perspective): started at tick "
                f"{diary_write.started_tick} and completed at tick "
                f"{diary_write.completed_tick}; retained "
                f"{_unit_phrase(diary_write.entry.units)} available."
            ),
            (
                f"Diary read at tick {diary_read.read_tick}: returned the same "
                "retained private entry, "
                f"{_unit_phrase(diary_read.entry.units)} available."
            ),
        )
    )
    return "\n".join(lines) + "\n"


def _main() -> None:
    print(
        render_focal_life_transcript(run_provisional_focal_life_scenario()),
        end="",
    )


if __name__ == "__main__":
    _main()
