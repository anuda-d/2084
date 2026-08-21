"""Attempted actions, kept separate from resolved world consequences."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, Mapping

from simulation.events import freeze_mapping


ACTION_KINDS = frozenset(
    {
        "travel",
        "work",
        "consult_official_record",
        "request_allocation",
        "speak",
        "write_diary",
        "read_diary",
        "wait",
    }
)


@dataclass(frozen=True)
class ActionParameterContract:
    required: Mapping[str, str]
    optional: Mapping[str, str]
    required_when_present: tuple[tuple[str, str], ...]


def _contract(
    *, required: Mapping[str, str] | None = None,
    optional: Mapping[str, str] | None = None,
    required_when_present: tuple[tuple[str, str], ...] = (),
) -> ActionParameterContract:
    return ActionParameterContract(
        required=MappingProxyType(dict(required or {})),
        optional=MappingProxyType(dict(optional or {})),
        required_when_present=required_when_present,
    )


ACTION_PARAMETER_CONTRACTS: Mapping[str, ActionParameterContract] = MappingProxyType(
    {
        "travel": _contract(required={"destination": "non_empty_string"}),
        "work": _contract(),
        "consult_official_record": _contract(
            required={"artifact_id": "non_empty_string"}
        ),
        "request_allocation": _contract(
            required={"requested_units": "positive_integer"},
            optional={"evidence_observation_ids": "string_list"},
        ),
        "speak": _contract(
            required={
                "proposition": "non_empty_string",
                "asserted_value": "integer",
                "evidence_observation_ids": "non_empty_string_list",
            },
            optional={
                "private_belief_id": "non_empty_string",
                "pressure_reason": "non_empty_string",
                "pressure": "positive_unit_number",
            },
            required_when_present=(("pressure", "pressure_reason"),),
        ),
        "write_diary": _contract(
            required={
                "object_id": "non_empty_string",
                "proposition": "non_empty_string",
                "asserted_value": "integer",
                "source_observation_ids": "non_empty_string_list",
            }
        ),
        "read_diary": _contract(
            required={
                "object_id": "non_empty_string",
                "entry_id": "non_empty_string",
            }
        ),
        "wait": _contract(),
    }
)


def action_parameter_contract_data(
    kinds: tuple[str, ...],
) -> dict[str, dict[str, object]]:
    """Return detached JSON-compatible parameter shapes for supported kinds."""
    return {
        kind: {
            "required": dict(ACTION_PARAMETER_CONTRACTS[kind].required),
            "optional": dict(ACTION_PARAMETER_CONTRACTS[kind].optional),
            "conditional_requirements": [
                {"if_present": trigger, "requires": [required]}
                for trigger, required in ACTION_PARAMETER_CONTRACTS[
                    kind
                ].required_when_present
            ],
        }
        for kind in kinds
    }


def _matches_parameter_shape(value: object, shape: str) -> bool:
    if shape == "non_empty_string":
        return isinstance(value, str) and bool(value.strip())
    if shape == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if shape == "positive_integer":
        return (
            isinstance(value, int)
            and not isinstance(value, bool)
            and value > 0
        )
    if shape in {"string_list", "non_empty_string_list"}:
        if not isinstance(value, (list, tuple)):
            return False
        if shape == "non_empty_string_list" and not value:
            return False
        return all(isinstance(item, str) and bool(item) for item in value)
    if shape == "positive_unit_number":
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and 0 < value <= 1
        )
    raise ValueError(f"unknown action parameter shape: {shape}")


def action_parameter_shape_error(
    kind: str, parameters: Mapping[str, object]
) -> str | None:
    """Validate only authored parameter fields and JSON value shapes."""
    contract = ACTION_PARAMETER_CONTRACTS[kind]
    missing = sorted(set(contract.required) - set(parameters))
    if missing:
        return f"{kind} is missing required parameters: " + ", ".join(missing)
    allowed = set(contract.required) | set(contract.optional)
    unexpected = sorted(set(parameters) - allowed)
    if unexpected:
        return f"{kind} contains unexpected parameters: " + ", ".join(unexpected)
    shapes = {**contract.required, **contract.optional}
    for name in sorted(parameters):
        if not _matches_parameter_shape(parameters[name], shapes[name]):
            return f"{kind} parameter {name} must be {shapes[name]}"
    for trigger, required in contract.required_when_present:
        if trigger in parameters and required not in parameters:
            return f"{kind} parameter {trigger} requires {required}"
    return None


@dataclass(frozen=True)
class ActionAttempt:
    actor_id: str
    kind: str
    explanation: str
    decision_reason: str = ""
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.kind not in ACTION_KINDS:
            raise ValueError(f"unsupported action kind: {self.kind}")
        object.__setattr__(self, "parameters", freeze_mapping(self.parameters))


@dataclass(frozen=True)
class PendingAction:
    action_id: str
    attempt_event_id: str
    attempt: ActionAttempt
    started_tick: int
    completes_tick: int


@dataclass(frozen=True)
class ActionResult:
    """Actor-safe knowledge that an attempted action reached a terminal state."""

    action_id: str
    attempt_event_id: str
    outcome_event_id: str
    actor_id: str
    action_kind: str
    status: Literal["completed", "rejected"]
    resolved_tick: int
    reason: str | None = None
