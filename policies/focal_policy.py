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
            private = next(
                belief for belief in reversed(view.beliefs) if belief.context == "private"
            )
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="write_diary",
                parameters={
                    "object_id": view.accessible_diary_id,
                    "proposition": private.proposition,
                    "asserted_value": private.asserted_value,
                    "source_observation_ids": private.source_observation_ids,
                },
                explanation=f"write the private {private.asserted_value}-unit perspective",
                decision_reason="the directly grounded private belief differs from the public claim and the diary is accessible",
            )
        if view.location == "home" and made_public_expression:
            revision_received = any(
                observation.details.get("evidence_kind") == "official_resource_claim"
                and observation.details.get("revises_event_id") is not None
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
                    decision_reason="the revised official claim conflicts with the earlier perspective preserved in the accessible diary",
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
        official_claim_received = any(
            observation.details.get("evidence_kind") == "official_resource_claim"
            for observation in view.observations
        )
        allocation_outcome_received = any(
            observation.details.get("evidence_kind") == "allocation_outcome"
            for observation in view.observations
        )
        consulted_record_ids = {
            observation.details.get("artifact_id")
            for observation in view.observations
            if observation.details.get("evidence_kind") == "official_record_version"
        }
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
            and allocation_outcome_received
            and pressure is not None
            and pressure.details.get("pressure", 0)
            >= self._public_conformity_threshold
            and (view.last_attempt is None or view.last_attempt.kind != "speak")
        ):
            official = next(
                observation
                for observation in reversed(view.observations)
                if observation.details.get("evidence_kind") == "official_resource_claim"
            )
            private = next(
                belief
                for belief in reversed(view.beliefs)
                if belief.context == "private"
            )
            value = official.details["asserted_value"]
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="speak",
                parameters={
                    "proposition": official.details["proposition"],
                    "asserted_value": value,
                    "private_belief_id": private.belief_id,
                    "evidence_observation_ids": (
                        official.observation_id,
                        pressure.observation_id,
                    ),
                    "pressure_reason": pressure.details["reason"],
                },
                explanation=f"repeat the official {value}-unit claim publicly",
                decision_reason=(
                    "public counter pressure favors repeating the delivered official "
                    "claim while the private belief remains "
                    f"{_number_word(private.asserted_value)} units"
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
                if artifact_id not in consulted_record_ids
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
            and official_claim_received
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
                    "direct sight supports three units for the household need, "
                    "despite the incompatible official claim"
                ),
            )
        if view.location == "allocation_office" and direct_claim_received:
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="wait",
                explanation="wait for the allocation briefing",
                decision_reason="direct sight established a quantity, but the known counter briefing has not occurred",
            )
        return ActionAttempt(
            actor_id=view.agent_id,
            kind="wait",
            explanation="wait",
            decision_reason="no currently delivered evidence changes the immediate plan",
        )
