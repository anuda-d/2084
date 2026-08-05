"""Small schedule/reactive policies for supporting characters."""

from experiments.core.actions import ActionAttempt
from experiments.core.agents import AgentView


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
        if any(attempt.kind == "speak" for attempt in view.action_history):
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
        official_claim = next(
            (
                observation
                for observation in reversed(view.observations)
                if observation.details.get("evidence_kind")
                == "official_resource_claim"
            ),
            None,
        )
        if visible_request is not None and official_claim is not None:
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="speak",
                parameters={
                    "proposition": official_claim.details["proposition"],
                    "asserted_value": official_claim.details["asserted_value"],
                    "evidence_observation_ids": (
                        visible_request.observation_id,
                        official_claim.observation_id,
                    ),
                    "pressure_reason": "public counter protocol",
                    "pressure": 0.8,
                },
                explanation="repeat the official allocation claim at the counter",
            )
        return ActionAttempt(
            actor_id=view.agent_id,
            kind="wait",
            explanation="staff the allocation counter",
        )
