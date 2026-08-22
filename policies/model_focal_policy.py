"""Strict boundary between structured model output and an action attempt."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from policies.mara_decision_request import DecisionAuthorshipIdentity
from simulation.actions import (
    ActionAttempt,
    action_parameter_contract_data,
    action_parameter_shape_error,
)
from simulation.agents import AgentView, PolicyDecisionRecord
from simulation.events import freeze_mapping, to_plain_data


class StructuredChoiceError(ValueError):
    """A model-like value does not satisfy the attempted-action schema."""


class ModelUnavailableError(RuntimeError):
    """A configured model client explicitly reports that it is unavailable."""


class RecordedDecisionError(RuntimeError):
    """Recorded decision data cannot be applied to the current restricted input."""


class _InvalidStructuredAttemptError(StructuredChoiceError):
    """A response cannot describe one supported attempted action."""


class ModelDecisionClient(Protocol):
    """Narrow source of one choice from detached restricted model input."""

    def choose(self, model_input: Mapping[str, object]) -> object:
        ...


class RecordedDecisionClient:
    """Replay detached decision records without calling a model provider."""

    def __init__(self, records: tuple[Mapping[str, object], ...]) -> None:
        frozen_records = []
        for index, record in enumerate(records):
            if not isinstance(record, Mapping):
                raise RecordedDecisionError(
                    f"recorded decision {index} must be an object"
                )
            model_input = record.get("model_input")
            status = record.get("status")
            if not isinstance(model_input, Mapping):
                raise RecordedDecisionError(
                    f"recorded decision {index} has no restricted input"
                )
            if status == "selected":
                if not isinstance(record.get("structured_response"), Mapping):
                    raise RecordedDecisionError(
                        f"recorded decision {index} has no structured response"
                    )
            elif status == "failed":
                if not isinstance(record.get("attempted_action"), Mapping):
                    raise RecordedDecisionError(
                        f"recorded decision {index} has no safe attempted action"
                    )
            else:
                raise RecordedDecisionError(
                    f"recorded decision {index} has unsupported status"
                )
            try:
                frozen_record = freeze_mapping(record)
                _validate_recorded_choice(frozen_record, index)
            except (KeyError, TypeError, ValueError, RecursionError) as error:
                raise RecordedDecisionError(
                    f"recorded decision {index} is invalid: {error}"
                ) from error
            frozen_records.append(frozen_record)
        self._records = tuple(frozen_records)
        self._index = 0

    @classmethod
    def from_records(
        cls, records: tuple[PolicyDecisionRecord, ...]
    ) -> RecordedDecisionClient:
        return cls(tuple(record.to_data() for record in records))

    @property
    def consumed_count(self) -> int:
        return self._index

    @property
    def remaining_count(self) -> int:
        return len(self._records) - self._index

    def choose(self, model_input: Mapping[str, object]) -> object:
        if self._index >= len(self._records):
            raise RecordedDecisionError("recorded decisions are exhausted")
        record = self._records[self._index]
        expected_input = to_plain_data(record["model_input"])
        if to_plain_data(freeze_mapping(model_input)) != expected_input:
            raise RecordedDecisionError(
                f"recorded decision input mismatch at index {self._index}"
            )
        response = _recorded_choice(record)
        self._index += 1
        return to_plain_data(response)


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


def _grounded_claim_options(view: AgentView) -> list[dict[str, object]]:
    options: list[dict[str, object]] = []
    for belief in view.beliefs:
        options.append(
            {
                "source_kind": "belief",
                "source_id": belief.belief_id,
                "proposition": belief.proposition,
                "asserted_value": belief.asserted_value,
                "evidence_observation_ids": list(
                    belief.source_observation_ids
                ),
                "private_belief_id": belief.belief_id,
            }
        )
    trace_by_id = {trace.trace_id: trace for trace in view.memory_traces}
    for claim in view.interpreted_claims:
        trace = trace_by_id.get(claim.origin_trace_id)
        if trace is None:
            continue
        options.append(
            {
                "source_kind": "interpreted_claim",
                "source_id": claim.claim_id,
                "proposition": claim.proposition,
                "asserted_value": claim.asserted_value,
                "evidence_observation_ids": [trace.source_observation_id],
                "private_belief_id": None,
            }
        )
    return options


def _action_affordances(view: AgentView) -> dict[str, dict[str, object]]:
    delivered_ids = [
        observation.observation_id for observation in view.observations
    ]
    claim_options = _grounded_claim_options(view)
    pressure_options = [
        {
            "evidence_observation_id": observation.observation_id,
            "pressure": observation.details["pressure"],
            "pressure_reason": observation.details["reason"],
        }
        for observation in view.observations
        if observation.details.get("evidence_kind") == "social_pressure"
        and isinstance(observation.details.get("pressure"), (int, float))
        and not isinstance(observation.details.get("pressure"), bool)
        and isinstance(observation.details.get("reason"), str)
    ]
    diary_entries = [
        {
            "object_id": view.accessible_diary_id,
            "entry_id": entry.entry_id,
        }
        for entry in view.accessible_diary_entries
        if view.accessible_diary_id is not None
    ]
    return {
        "travel": {
            "currently_applicable": bool(view.reachable_destinations),
            "parameter_options": {
                "destination": list(view.reachable_destinations)
            },
        },
        "work": {
            "currently_applicable": view.work_action_available,
            "parameter_options": {},
        },
        "consult_official_record": {
            "currently_applicable": bool(view.consultable_official_record_ids),
            "parameter_options": {
                "artifact_id": list(view.consultable_official_record_ids)
            },
        },
        "request_allocation": {
            "currently_applicable": view.allocation_action_available,
            "parameter_options": {
                "requested_units": {
                    "minimum": 1,
                    "suggested": max(1, view.remaining_required_units),
                },
                "evidence_observation_ids": delivered_ids,
            },
        },
        "speak": {
            "currently_applicable": bool(claim_options and delivered_ids),
            "parameter_options": {
                "grounded_claims": claim_options,
                "evidence_observation_ids": delivered_ids,
                "pressure_pairs": pressure_options,
            },
        },
        "write_diary": {
            "currently_applicable": bool(
                view.accessible_diary_id is not None and claim_options
            ),
            "parameter_options": {
                "object_id": (
                    [view.accessible_diary_id]
                    if view.accessible_diary_id is not None
                    else []
                ),
                "grounded_claims": claim_options,
            },
        },
        "read_diary": {
            "currently_applicable": bool(diary_entries),
            "parameter_options": {"entries": diary_entries},
        },
        "wait": {"currently_applicable": True, "parameter_options": {}},
    }


def model_input_from_view(view: AgentView) -> dict[str, object]:
    """Serialize only the restricted agent view into detached JSON-like data."""
    stance = view.contextual_stance
    affordances = _action_affordances(view)
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
            "currently_applicable_kinds": [
                kind
                for kind in view.valid_actions
                if affordances[kind]["currently_applicable"]
            ],
            "parameters_by_kind": action_parameter_contract_data(
                view.valid_actions
            ),
            "affordances_by_kind": affordances,
        },
    }


class ModelFocalPolicy:
    """Use a model-compatible client as the focal character's chooser."""

    def __init__(
        self,
        client: ModelDecisionClient,
        *,
        configuration_id: str,
        authorship_identity: DecisionAuthorshipIdentity | None = None,
    ) -> None:
        if not isinstance(configuration_id, str) or not configuration_id.strip():
            raise ValueError("configuration_id must be a non-empty string")
        self._client = client
        self._configuration_id = configuration_id
        self._authorship_identity = (
            freeze_mapping(authorship_identity.to_data())
            if authorship_identity is not None
            else None
        )
        self._decision_record: PolicyDecisionRecord | None = None

    def choose(self, view: AgentView) -> ActionAttempt:
        self._decision_record = None
        model_input = model_input_from_view(view)
        recorded_input = freeze_mapping(model_input)
        try:
            response = self._client.choose(model_input)
        except TimeoutError as error:
            return self._safe_failure(
                view,
                recorded_input,
                "timeout",
                type(error).__name__,
            )
        except ModelUnavailableError as error:
            return self._safe_failure(
                view,
                recorded_input,
                "unavailable_model",
                type(error).__name__,
            )
        try:
            attempt = structured_choice_to_attempt(view, response)
        except _InvalidStructuredAttemptError as error:
            return self._safe_failure(
                view,
                recorded_input,
                "invalid_attempt",
                type(error).__name__,
            )
        except StructuredChoiceError as error:
            return self._safe_failure(
                view,
                recorded_input,
                "malformed_response",
                type(error).__name__,
            )
        self._decision_record = PolicyDecisionRecord(
            decision_id=f"model-decision-{view.agent_id}-{view.tick:04d}",
            tick=view.tick,
            agent_id=view.agent_id,
            policy_kind="model",
            configuration_id=self._configuration_id,
            status="selected",
            model_input=recorded_input,
            structured_response=response,
            attempted_action=_attempt_data(attempt) or {},
            attempted_action_kind=attempt.kind,
            authorship_identity=self._authorship_identity,
        )
        return attempt

    def _safe_failure(
        self,
        view: AgentView,
        model_input: Mapping[str, object],
        failure_kind: str,
        failure_type: str,
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
            configuration_id=self._configuration_id,
            status="failed",
            model_input=model_input,
            structured_response=None,
            attempted_action=_attempt_data(attempt) or {},
            authorship_identity=self._authorship_identity,
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


def _recorded_choice(record: Mapping[str, object]) -> Mapping[str, object]:
    if record["status"] == "selected":
        response = record["structured_response"]
        if not isinstance(response, Mapping):
            raise RecordedDecisionError("selected record has no response")
        return response
    attempt = record["attempted_action"]
    if not isinstance(attempt, Mapping):
        raise RecordedDecisionError("failed record has no safe attempt")
    return {
        "kind": attempt["kind"],
        "parameters": attempt["parameters"],
        "explanation": attempt["explanation"],
        "decision_reason": attempt["decision_reason"],
    }


def _validate_recorded_choice(
    record: Mapping[str, object], index: int
) -> None:
    response = _recorded_choice(record)
    if frozenset(response) != _CHOICE_FIELDS:
        raise RecordedDecisionError("recorded response fields are not exact")
    kind = response["kind"]
    model_input = record["model_input"]
    if not isinstance(kind, str) or not isinstance(model_input, Mapping):
        raise RecordedDecisionError("recorded response kind is invalid")
    action_contract = model_input.get("action_contract")
    if not isinstance(action_contract, Mapping):
        raise RecordedDecisionError("recorded input has no action contract")
    character = model_input.get("character")
    attempt = record.get("attempted_action")
    if not isinstance(character, Mapping) or not isinstance(attempt, Mapping):
        raise RecordedDecisionError("recorded action identity is incomplete")
    if frozenset(attempt) != {
        "actor_id",
        "kind",
        "parameters",
        "explanation",
        "decision_reason",
    }:
        raise RecordedDecisionError("recorded attempted action fields are not exact")
    if attempt["actor_id"] != character.get("agent_id"):
        raise RecordedDecisionError("recorded attempted action actor does not match")
    projected_attempt = {
        "kind": attempt["kind"],
        "parameters": attempt["parameters"],
        "explanation": attempt["explanation"],
        "decision_reason": attempt["decision_reason"],
    }
    if to_plain_data(projected_attempt) != to_plain_data(response):
        raise RecordedDecisionError("recorded response and attempted action disagree")
    if record.get("attempted_action_kind") != kind:
        raise RecordedDecisionError("recorded attempted action kind does not match")
    if record["status"] == "failed":
        failure_kind = record.get("failure_kind")
        if (
            kind != "wait"
            or to_plain_data(response["parameters"]) != {}
            or response["explanation"]
            != "wait because no valid model decision is available"
            or not isinstance(failure_kind, str)
            or response["decision_reason"]
            != f"model decision failed safely: {failure_kind}"
        ):
            raise RecordedDecisionError("failed record is not the generated safe wait")
    supported = action_contract.get("supported_kinds")
    if not isinstance(supported, (list, tuple)) or kind not in supported:
        raise RecordedDecisionError("recorded response kind is not supported")
    parameters = response["parameters"]
    if not isinstance(parameters, Mapping):
        raise RecordedDecisionError("recorded response parameters are invalid")
    _validate_parameter_value(parameters, set())
    if parameter_error := action_parameter_shape_error(kind, parameters):
        raise RecordedDecisionError(parameter_error)
    for field in ("explanation", "decision_reason"):
        value = response[field]
        if not isinstance(value, str) or not value.strip():
            raise RecordedDecisionError(f"recorded response {field} is empty")


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
    if parameter_error := action_parameter_shape_error(kind, parameters):
        raise _InvalidStructuredAttemptError(parameter_error)

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
