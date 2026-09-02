"""Small schedule/reactive policies for supporting characters."""

from dataclasses import dataclass
from typing import Protocol

from simulation.actions import ActionAttempt, ActionResult
from simulation.agents import AgentView
from simulation.decision_eligibility import DecisionTrigger
from simulation.events import Observation


@dataclass(frozen=True)
class TransitStatementView:
    """Finite actor-safe input for one supporting transit statement choice."""

    tick: int
    agent_id: str
    location: str
    observations: tuple[Observation, ...]
    action_results: tuple[ActionResult, ...]
    triggers: tuple[DecisionTrigger, ...]
    addressable_actor_ids: tuple[str, ...]
    valid_actions: tuple[str, ...]


class TransitStatementDecisionPolicy(Protocol):
    def choose(self, view: TransitStatementView) -> ActionAttempt:
        ...


@dataclass(frozen=True)
class TransitStatementPolicy:
    """Choose one source-citing statement or an ordinary alternative."""

    recipient_id: str
    route: str = "workplace-home"

    def choose(self, view: TransitStatementView) -> ActionAttempt:
        evidence = next(
            (
                observation
                for observation in reversed(view.observations)
                if observation.agent_id == view.agent_id
                and observation.details.get("evidence_kind")
                == "transit_service_status"
                and observation.details.get("route") == self.route
                and observation.details.get("current_status")
                in {"normal", "reduced"}
            ),
            None,
        )
        if (
            evidence is not None
            and self.recipient_id in view.addressable_actor_ids
            and "speak" in view.valid_actions
        ):
            return ActionAttempt(
                actor_id=view.agent_id,
                kind="speak",
                parameters={
                    "proposition": evidence.details["proposition"],
                    "asserted_value": evidence.details["asserted_value"],
                    "evidence_observation_ids": (evidence.observation_id,),
                },
                explanation="tell Mara about the delivered workplace transit notice",
                decision_reason="Mara is present and the notice is available to cite",
            )
        if "wait" not in view.valid_actions:
            raise RuntimeError("transit statement view offers no ordinary alternative")
        return ActionAttempt(
            actor_id=view.agent_id,
            kind="wait",
            explanation="continue the ledger shift without addressing Mara",
            decision_reason="no evidence-bound statement is physically available",
        )


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
