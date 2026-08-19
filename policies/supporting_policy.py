"""Small schedule/reactive policies for supporting characters."""

from simulation.actions import ActionAttempt
from simulation.agents import AgentView


class CoworkerPolicy:
    def choose(self, view: AgentView) -> ActionAttempt:
        completed_shift = any(
            observation.details.get("evidence_kind") == "work_completed"
            for observation in view.observations
        )
        if view.location == "workplace" and not completed_shift:
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="work",
                explanation="complete the morning ledger shift",
            )
        return ActionAttempt(
            actor_id=view.agent_id,
            kind="wait",
            explanation="remain available after the scheduled shift",
        )


class AllocationClerkPolicy:
    def choose(self, view: AgentView) -> ActionAttempt:
        official_record = next(
            (
                observation
                for observation in reversed(view.observations)
                if observation.details.get("evidence_kind")
                == "official_record_version"
            ),
            None,
        )
        if official_record is None and view.consultable_official_record_ids:
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="consult_official_record",
                parameters={"artifact_id": view.consultable_official_record_ids[0]},
                explanation="consult the weekly ration schedule before opening the counter",
            )
        if any(
            result.action_kind == "speak" and result.status == "completed"
            for result in view.action_results
        ):
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="wait",
                explanation="resume counter duties after the public reminder",
            )
        visible_request = next(
            (
                observation
                for observation in reversed(view.observations)
                if observation.details.get("evidence_kind")
                == "visible_allocation_request"
            ),
            None,
        )
        if visible_request is not None and official_record is not None:
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="speak",
                parameters={
                    "proposition": official_record.details["proposition"],
                    "asserted_value": official_record.details["asserted_value"],
                    "evidence_observation_ids": (
                        visible_request.observation_id,
                        official_record.observation_id,
                    ),
                    "pressure_reason": "public counter protocol",
                    "pressure": 0.8,
                },
                explanation="repeat the official ration schedule at the counter",
            )
        return ActionAttempt(
            actor_id=view.agent_id,
            kind="wait",
            explanation="staff the allocation counter",
        )
