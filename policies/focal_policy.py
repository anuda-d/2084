"""Restricted policy for the focal character."""

from simulation.actions import ActionAttempt
from simulation.agents import AgentView


def _number_word(value: int) -> str:
    return {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}.get(
        value, str(value)
    )


class FocalPolicy:
    def __init__(self, public_conformity_threshold: float = 0.7) -> None:
        if not isinstance(public_conformity_threshold, (int, float)) or isinstance(
            public_conformity_threshold, bool
        ):
            raise ValueError("public_conformity_threshold must be numeric")
        if not 0 <= public_conformity_threshold <= 1:
            raise ValueError("public_conformity_threshold must be between 0 and 1")
        self._public_conformity_threshold = float(public_conformity_threshold)

    def choose(self, view: AgentView) -> ActionAttempt:
        made_public_expression = any(
            result.action_kind == "speak" and result.status == "completed"
            for result in view.action_results
        )
        official_record_observations = tuple(
            observation
            for observation in view.observations
            if observation.details.get("evidence_kind") == "official_record_version"
        )
        read_diary = any(
            observation.details.get("evidence_kind") == "diary_read_completed"
            for observation in view.observations
        )
        if view.location == "home" and not made_public_expression:
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="travel",
                parameters={"destination": "workplace"},
                explanation="travel to workplace",
                decision_reason="the scheduled workplace obligation comes before the allocation errand",
            )
        if view.location == "allocation_office" and made_public_expression:
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="travel",
                parameters={"destination": "workplace"},
                explanation="travel back through the workplace",
                decision_reason="the private diary is at home and the permitted route passes through the workplace",
            )
        if view.location == "workplace" and made_public_expression and not read_diary:
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="travel",
                parameters={"destination": "home"},
                explanation="travel home to the private diary",
                decision_reason="the private perspective can be written only with physical access to the diary at home",
            )
        if view.location == "workplace" and read_diary:
            completed_work = sum(
                1
                for result in view.action_results
                if result.action_kind == "work" and result.status == "completed"
            )
            if completed_work < 2:
                return ActionAttempt(
                    actor_id=view.agent_id,
                    kind="work",
                    explanation="resume the afternoon ledger shift",
                    decision_reason="the diary check is complete and the remaining obligation is the afternoon ledger",
                )
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="wait",
                explanation="finish the ordinary workday",
                decision_reason=(
                    f"scheduled work is complete; {_number_word(view.remaining_required_units)} "
                    "household allocation unit remains unmet"
                    if view.remaining_required_units == 1
                    else (
                        f"scheduled work is complete; {view.remaining_required_units} "
                        "household allocation units remain unmet"
                        if view.remaining_required_units > 1
                        else "scheduled work and the household allocation are complete"
                    )
                ),
            )
        if (
            view.location == "home"
            and made_public_expression
            and view.accessible_diary_id is not None
            and view.accessible_diary_entry_count == 0
        ):
            superseded_version_ids = {
                observation.details.get("previous_version_id")
                for observation in official_record_observations
                if observation.details.get("previous_version_id") is not None
            }
            earlier_schedule = next(
                observation
                for observation in official_record_observations
                if observation.details.get("version_id") in superseded_version_ids
            )
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="write_diary",
                parameters={
                    "object_id": view.accessible_diary_id,
                    "proposition": earlier_schedule.details["proposition"],
                    "asserted_value": earlier_schedule.details["asserted_value"],
                    "source_observation_ids": (earlier_schedule.observation_id,),
                },
                explanation="write the earlier three-packet schedule",
                decision_reason="the delivered earlier official schedule can be preserved while the diary is accessible",
            )
        if view.location == "home" and made_public_expression:
            revision_received = any(
                observation.details.get("evidence_kind") == "official_record_version"
                and observation.details.get("previous_version_id") is not None
                for observation in view.observations
            )
            if (
                revision_received
                and not read_diary
                and view.accessible_diary_id is not None
                and view.accessible_diary_entries
            ):
                entry = view.accessible_diary_entries[-1]
                return ActionAttempt(
                    actor_id=view.agent_id,
                    kind="read_diary",
                    parameters={
                        "object_id": view.accessible_diary_id,
                        "entry_id": entry.entry_id,
                    },
                    explanation="read the earlier private diary entry",
                    decision_reason="the newly encountered schedule gives reason to re-read the separately sourced counter perspective preserved in the diary",
                )
            if read_diary:
                return ActionAttempt(
                    actor_id=view.agent_id,
                    kind="travel",
                    parameters={"destination": "workplace"},
                    explanation="travel to workplace after reading the diary",
                    decision_reason="the earlier perspective has been checked and the remaining ordinary obligation is at work",
                )
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="wait",
                explanation="wait beside the private diary",
                decision_reason="no additional diary action is needed yet",
            )
        arrived_at_work = any(
            observation.details.get("evidence_kind") == "arrival"
            and observation.details.get("destination") == "workplace"
            for observation in view.observations
        )
        completed_work = any(
            observation.details.get("evidence_kind") == "work_completed"
            for observation in view.observations
        )
        if view.location == "workplace" and completed_work:
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="travel",
                parameters={"destination": "allocation_office"},
                explanation="travel to allocation office",
                decision_reason="the work obligation is complete and the household allocation is still needed",
            )
        if view.location == "workplace" and arrived_at_work:
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="work",
                explanation="work the morning ledger shift",
                decision_reason="the delivered arrival confirms physical presence for the scheduled work",
            )
        direct_claim_received = any(
            observation.details.get("evidence_kind") == "direct_resource_claim"
            for observation in view.observations
        )
        official_record_received = bool(official_record_observations)
        allocation_outcome_received = any(
            observation.details.get("evidence_kind") == "allocation_outcome"
            for observation in view.observations
        )
        pressure = next(
            (
                observation
                for observation in reversed(view.observations)
                if observation.details.get("evidence_kind") == "social_pressure"
            ),
            None,
        )
        if (
            view.location == "allocation_office"
            and not made_public_expression
            and allocation_outcome_received
            and view.contextual_stance is None
            and len(official_record_observations) == 1
            and pressure is not None
            and pressure.details.get("pressure", 0)
            >= self._public_conformity_threshold
        ):
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="consult_official_record",
                parameters={
                    "artifact_id": official_record_observations[0].details["artifact_id"]
                },
                explanation="consult the weekly ration schedule again",
                decision_reason=(
                    "the partial handover and public counter pressure justify checking "
                    "the accessible schedule again"
                ),
            )
        stance = (
            view.contextual_stance
            if view.contextual_stance is not None
            and view.contextual_stance.context == "public_counter"
            else None
        )
        stance_pressure = (
            next(
                (
                    observation
                    for observation in view.observations
                    if stance is not None
                    and observation.observation_id
                    == stance.pressure_observation_id
                ),
                None,
            )
            if stance is not None
            else None
        )
        if (
            view.location == "allocation_office"
            and not made_public_expression
            and allocation_outcome_received
            and stance is not None
            and stance_pressure is not None
        ):
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="speak",
                parameters={
                    "proposition": stance.proposition,
                    "asserted_value": stance.asserted_value,
                    "evidence_observation_ids": stance.source_observation_ids,
                    "pressure_reason": stance_pressure.details["reason"],
                },
                explanation=(
                    f"repeat the official {stance.asserted_value}-packet entitlement "
                    "publicly"
                ),
                decision_reason=(
                    "the public-counter stance supplies the revised delivered schedule "
                    "while the physical handover remains separate"
                ),
            )
        if view.location == "allocation_office" and allocation_outcome_received:
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="wait",
                explanation="wait after the partial allocation",
                decision_reason="the delivered handover leaves one household unit unfilled while the clerk responds",
            )
        consultable_record_id = next(
            (
                artifact_id
                for artifact_id in view.consultable_official_record_ids
                if not official_record_observations
            ),
            None,
        )
        if consultable_record_id is not None:
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="consult_official_record",
                parameters={"artifact_id": consultable_record_id},
                explanation="consult the weekly ration schedule",
                decision_reason=(
                    "the public schedule is accessible at the allocation office and "
                    "has not yet been encountered"
                ),
            )
        if (
            view.location == "allocation_office"
            and direct_claim_received
            and official_record_received
            and not allocation_outcome_received
        ):
            direct = next(
                observation
                for observation in reversed(view.observations)
                if observation.details.get("evidence_kind") == "direct_resource_claim"
            )
            requested = min(view.required_units, direct.details["asserted_value"])
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="request_allocation",
                parameters={
                    "requested_units": requested,
                    "evidence_observation_ids": (direct.observation_id,),
                },
                explanation=f"request {requested} allocation units",
                decision_reason=(
                    "direct sight supports three units for the household need, and the "
                    "encountered schedule separately promises three packets"
                ),
            )
        if view.location == "allocation_office" and direct_claim_received:
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="wait",
                explanation="wait for the allocation briefing",
                decision_reason="direct sight established a quantity, but the schedule consultation has not arrived",
            )
        return ActionAttempt(
            actor_id=view.agent_id,
            kind="wait",
            explanation="wait",
            decision_reason="no currently delivered evidence changes the immediate plan",
        )
