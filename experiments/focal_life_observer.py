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
    relocation = evidence.diary_relocation_decision
    relocation_observation = evidence.diary_relocation_observation
    lines.extend(
        (
            (
                "Diary relocation attempted at tick "
                f"{relocation_observation.details['attempted_tick']}: "
                f"{relocation.choice.replace('_', ' ')}, from "
                f"{relocation_observation.details['origin']} to "
                f"{relocation_observation.details['destination']}."
            ),
            (
                "Diary relocation resolved at tick "
                f"{relocation_observation.delivery_tick}: "
                "the diary is now at "
                f"{relocation_observation.details['destination']}."
            ),
        )
    )
    revision = evidence.official_revision_observation
    lines.append(
        f"Official revision received at tick {revision.delivery_tick} via "
        f"{revision.source}: claim revised to "
        f"{_unit_phrase(revision.details['available_units'])} available."
    )
    consult = evidence.diary_consult_observation
    lines.append(
        "Diary consult attempted at tick "
        f"{consult.details['attempted_tick']} after the official revision."
    )
    if consult.details["outcome"] == "entry_retrieved":
        lines.append(
            f"Diary consult resolved at tick {consult.delivery_tick} via "
            f"{consult.source}: returned retained private entry "
            f"{consult.details['entry_id']}, "
            f"{_unit_phrase(consult.details['available_units'])} available."
        )
    else:
        lines.append(
            f"Diary consult resolved at tick {consult.delivery_tick} via "
            f"{consult.source}: {consult.details['message']}"
        )
    reconsideration = evidence.reconsideration
    reconsideration_trace = reconsideration.trace
    lines.append(
        f"Later decision: {reconsideration.choice.replace('_', ' ')}."
    )
    if reconsideration_trace.diary_entry_id is not None:
        lines.append(
            "Reason: official revision "
            f"{reconsideration_trace.selected_revision_observation_id} said "
            f"{_unit_phrase(reconsideration_trace.observed_revision_units)}; "
            f"retained diary entry {reconsideration_trace.diary_entry_id} said "
            f"{_unit_phrase(reconsideration_trace.retained_private_units)}, so "
            "the local rule chooses to recheck local supply."
        )
    else:
        lines.append(
            "Reason: official revision "
            f"{reconsideration_trace.selected_revision_observation_id} said "
            f"{_unit_phrase(reconsideration_trace.observed_revision_units)}; no "
            "diary perspective was currently accessible, so the local rule "
            "adjusts the next request."
        )
    retrieval_constraint = evidence.diary_retrieval_constraint_observation
    retrieval_decision = evidence.diary_retrieval_decision
    if retrieval_constraint is not None and retrieval_decision is not None:
        retrieval_trace = retrieval_decision.trace
        lines.extend(
            (
                (
                    "Retrieval constraint delivered at tick "
                    f"{retrieval_constraint.delivery_tick}: reachable in "
                    f"{retrieval_trace.observed_reachable_in_ticks} ticks; "
                    f"deadline tick {retrieval_trace.observed_deadline_tick}."
                ),
                f"Retrieval decision: {retrieval_decision.choice.replace('_', ' ')}.",
                (
                    "Reason: inaccessible consult "
                    f"{retrieval_trace.selected_consult_observation_id} and time "
                    f"constraint {retrieval_trace.selected_constraint_observation_id} "
                    "leave enough delivered time."
                    if retrieval_decision.choice == "retrieve_private_diary"
                    else (
                        "Reason: inaccessible consult "
                        f"{retrieval_trace.selected_consult_observation_id} and time "
                        "constraint "
                        f"{retrieval_trace.selected_constraint_observation_id} do not "
                        "leave enough delivered time."
                    )
                ),
            )
        )
    retrieval_resolution = evidence.diary_retrieval_resolution
    retrieval_read = evidence.diary_retrieval_read
    if retrieval_resolution is not None and retrieval_read is not None:
        lines.extend(
            (
                (
                    "Diary retrieval attempted at tick "
                    f"{retrieval_resolution.started_tick} from "
                    f"{retrieval_resolution.actor_location}."
                ),
                (
                    "Diary retrieval resolved at tick "
                    f"{retrieval_resolution.resolved_tick}: possession changed only "
                    "through the resolved consequence."
                ),
                (
                    f"Diary read at tick {retrieval_read.read_tick}: returned the "
                    f"exact original private entry {retrieval_read.entry.entry_id}, "
                    f"{_unit_phrase(retrieval_read.entry.units)} available."
                ),
            )
        )
    return "\n".join(lines) + "\n"


def _main() -> None:
    print(
        render_focal_life_transcript(
            run_provisional_focal_life_scenario(
                diary_relocation="entrust_to_supporting_person",
                diary_retrieval_window_ticks=2,
            )
        ),
        end="",
    )


if __name__ == "__main__":
    _main()
