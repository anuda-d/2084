"""Strict boundary between structured model output and an action attempt."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from simulation.actions import ActionAttempt
from simulation.agents import AgentView, PolicyDecisionRecord


class StructuredChoiceError(ValueError):
    """A model-like value does not satisfy the attempted-action schema."""


class ModelUnavailableError(RuntimeError):
    """A configured model client explicitly reports that it is unavailable."""


class _InvalidStructuredAttemptError(StructuredChoiceError):
    """A response cannot describe one supported attempted action."""


class ModelDecisionClient(Protocol):
    """Narrow source of one structured choice for a restricted agent view."""

    def choose(self, view: AgentView) -> object:
        ...


class ModelFocalPolicy:
    """Use a model-compatible client as the focal character's chooser."""

    def __init__(self, client: ModelDecisionClient) -> None:
        self._client = client
        self._decision_record: PolicyDecisionRecord | None = None

    def choose(self, view: AgentView) -> ActionAttempt:
        self._decision_record = None
        try:
            response = self._client.choose(view)
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
