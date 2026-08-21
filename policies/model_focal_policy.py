"""Strict boundary between structured model output and an action attempt."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from simulation.actions import ActionAttempt
from simulation.agents import AgentView, PolicyDecisionRecord
from simulation.events import to_plain_data


class StructuredChoiceError(ValueError):
    """A model-like value does not satisfy the attempted-action schema."""


class ModelUnavailableError(RuntimeError):
    """A configured model client explicitly reports that it is unavailable."""


class _InvalidStructuredAttemptError(StructuredChoiceError):
    """A response cannot describe one supported attempted action."""


class ModelDecisionClient(Protocol):
    """Narrow source of one choice from detached restricted model input."""

    def choose(self, model_input: Mapping[str, object]) -> object:
        ...


def _attempt_data(attempt: ActionAttempt | None) -> dict[str, object] | None:
    if attempt is None:
        return None
    return {
        "actor_id": attempt.actor_id,
        "kind": attempt.kind,
        "parameters": to_plain_data(attempt.parameters),
        "explanation": attempt.explanation,
        "decision_reason": attempt.decision_reason,
    }


def model_input_from_view(view: AgentView) -> dict[str, object]:
    """Serialize only the restricted agent view into detached JSON-like data."""
    stance = view.contextual_stance
    return {
        "tick": view.tick,
        "character": {
            "agent_id": view.agent_id,
            "display_name": view.display_name,
            "role": view.role,
        },
        "state": {
            "location": view.location,
            "aim": view.aim,
            "required_resource_id": view.required_resource_id,
            "required_units": view.required_units,
            "resource_holdings": to_plain_data(view.resource_holdings),
            "remaining_required_units": view.remaining_required_units,
            "obligations": list(view.obligations),
        },
        "decision_history": {
            "last_attempt": _attempt_data(view.last_attempt),
            "attempts": [_attempt_data(attempt) for attempt in view.action_history],
            "results": [
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
                for result in view.action_results
            ],
        },
        "delivered_observations": [
            {
                "observation_id": observation.observation_id,
                "agent_id": observation.agent_id,
                "event_id": observation.event_id,
                "source": observation.source,
                "delivery_tick": observation.delivery_tick,
                "details": to_plain_data(observation.details),
            }
            for observation in view.observations
        ],
        "understanding": {
            "beliefs": [
                {
                    "belief_id": belief.belief_id,
                    "proposition": belief.proposition,
                    "asserted_value": belief.asserted_value,
                    "source_observation_ids": list(belief.source_observation_ids),
                    "confidence": belief.confidence,
                    "last_updated_tick": belief.last_updated_tick,
                    "context": belief.context,
                    "conflicts_with": list(belief.conflicts_with),
                }
                for belief in view.beliefs
            ],
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
                for trace in view.memory_traces
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
                for claim in view.interpreted_claims
            ],
            "contextual_stance": (
                {
                    "context": stance.context,
                    "proposition": stance.proposition,
                    "asserted_value": stance.asserted_value,
                    "source_claim_id": stance.source_claim_id,
                    "source_trace_id": stance.source_trace_id,
                    "source_observation_ids": list(stance.source_observation_ids),
                    "pressure_observation_id": stance.pressure_observation_id,
                    "selected_tick": stance.selected_tick,
                }
                if stance is not None
                else None
            ),
        },
        "accessible_objects": {
            "diary": (
                {
                    "object_id": view.accessible_diary_id,
                    "entry_count": view.accessible_diary_entry_count,
                    "entries": [
                        {
                            "entry_id": entry.entry_id,
                            "proposition": entry.proposition,
                            "asserted_value": entry.asserted_value,
                            "source_observation_ids": list(
                                entry.source_observation_ids
                            ),
                            "started_tick": entry.started_tick,
                            "completed_tick": entry.completed_tick,
                        }
                        for entry in view.accessible_diary_entries
                    ],
                }
                if view.accessible_diary_id is not None
                else None
            ),
            "consultable_official_record_ids": list(
                view.consultable_official_record_ids
            ),
        },
        "action_contract": {
            "supported_kinds": list(view.valid_actions),
        },
    }


class ModelFocalPolicy:
    """Use a model-compatible client as the focal character's chooser."""

    def __init__(self, client: ModelDecisionClient) -> None:
        self._client = client
        self._decision_record: PolicyDecisionRecord | None = None

    def choose(self, view: AgentView) -> ActionAttempt:
        self._decision_record = None
        try:
            response = self._client.choose(model_input_from_view(view))
        except TimeoutError as error:
            return self._safe_failure(view, "timeout", type(error).__name__)
        except ModelUnavailableError as error:
            return self._safe_failure(
                view, "unavailable_model", type(error).__name__
            )
        try:
            return structured_choice_to_attempt(view, response)
        except _InvalidStructuredAttemptError as error:
            return self._safe_failure(
                view, "invalid_attempt", type(error).__name__
            )
        except StructuredChoiceError as error:
            return self._safe_failure(
                view, "malformed_response", type(error).__name__
            )

    def _safe_failure(
        self, view: AgentView, failure_kind: str, failure_type: str
    ) -> ActionAttempt:
        attempt = ActionAttempt(
            actor_id=view.agent_id,
            kind="wait",
            parameters={},
            explanation="wait because no valid model decision is available",
            decision_reason=f"model decision failed safely: {failure_kind}",
        )
        self._decision_record = PolicyDecisionRecord(
            decision_id=f"model-decision-{view.agent_id}-{view.tick:04d}",
            tick=view.tick,
            agent_id=view.agent_id,
            policy_kind="model",
            status="failed",
            failure_kind=failure_kind,
            failure_type=failure_type,
            attempted_action_kind=attempt.kind,
        )
        return attempt

    def take_decision_record(self) -> PolicyDecisionRecord | None:
        record = self._decision_record
        self._decision_record = None
        return record


_CHOICE_FIELDS = frozenset(
    {"kind", "parameters", "explanation", "decision_reason"}
)


def _validate_parameter_value(value: object, active_container_ids: set[int]) -> None:
    if value is None or isinstance(value, (bool, int, float, str)):
        return
    if isinstance(value, Mapping):
        container_id = id(value)
        if container_id in active_container_ids:
            raise _InvalidStructuredAttemptError(
                "structured choice parameters cannot be cyclic"
            )
        active_container_ids.add(container_id)
        try:
            for key, item in value.items():
                if not isinstance(key, str):
                    raise _InvalidStructuredAttemptError(
                        "structured choice parameter fields must be strings"
                    )
                _validate_parameter_value(item, active_container_ids)
        finally:
            active_container_ids.remove(container_id)
        return
    if isinstance(value, (list, tuple)):
        container_id = id(value)
        if container_id in active_container_ids:
            raise _InvalidStructuredAttemptError(
                "structured choice parameters cannot be cyclic"
            )
        active_container_ids.add(container_id)
        try:
            for item in value:
                _validate_parameter_value(item, active_container_ids)
        finally:
            active_container_ids.remove(container_id)
        return
    raise _InvalidStructuredAttemptError(
        f"unsupported structured choice parameter value: {type(value).__name__}"
    )


def structured_choice_to_attempt(
    view: AgentView, response: object
) -> ActionAttempt:
    """Parse one exact structured choice without consulting or mutating the world."""
    if not isinstance(response, Mapping):
        raise StructuredChoiceError("structured choice must be an object")
    if any(not isinstance(key, str) for key in response):
        raise StructuredChoiceError("structured choice fields must be strings")

    response_fields = frozenset(response)
    if response_fields != _CHOICE_FIELDS:
        missing = sorted(_CHOICE_FIELDS - response_fields)
        unexpected = sorted(response_fields - _CHOICE_FIELDS)
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if unexpected:
            details.append("unexpected: " + ", ".join(unexpected))
        raise StructuredChoiceError(
            "invalid structured choice fields (" + "; ".join(details) + ")"
        )

    kind = response["kind"]
    if not isinstance(kind, str) or kind not in view.valid_actions:
        raise _InvalidStructuredAttemptError(
            "structured choice kind is not supported"
        )

    parameters = response["parameters"]
    if not isinstance(parameters, Mapping) or any(
        not isinstance(key, str) for key in parameters
    ):
        raise _InvalidStructuredAttemptError(
            "structured choice parameters must be an object"
        )
    try:
        _validate_parameter_value(parameters, set())
    except RecursionError as error:
        raise _InvalidStructuredAttemptError(
            "structured choice parameter nesting is too deep"
        ) from error

    explanation = response["explanation"]
    if not isinstance(explanation, str) or not explanation.strip():
        raise StructuredChoiceError("structured choice explanation must be non-empty")
    decision_reason = response["decision_reason"]
    if not isinstance(decision_reason, str) or not decision_reason.strip():
        raise StructuredChoiceError("structured choice decision_reason must be non-empty")

    try:
        return ActionAttempt(
            actor_id=view.agent_id,
            kind=kind,
            parameters=parameters,
            explanation=explanation,
            decision_reason=decision_reason,
        )
    except (TypeError, ValueError, RecursionError) as error:
        raise _InvalidStructuredAttemptError(str(error)) from error
