"""Strict boundary between structured model output and an action attempt."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
import hashlib
import hmac
import json
from typing import Protocol

from policies.mara_decision_request import (
    DecisionAuthorshipIdentity,
    restricted_decision_input_size_bytes,
)
from simulation.actions import (
    ACTION_PARAMETER_CONTRACTS,
    ActionAttempt,
    action_parameter_contract_data,
    action_parameter_shape_error,
)
from simulation.agents import AgentView, PolicyDecisionRecord
from simulation.events import freeze_mapping, to_plain_data


MAX_RETAINED_DECISION_HISTORY_ENTRIES = 16
MAX_RETAINED_ACTION_ATTEMPT_KIND_SUMMARIES = len(ACTION_PARAMETER_CONTRACTS)
_ACTION_RESULT_CONTINUITY_STATUSES = frozenset(("completed", "rejected"))
MAX_RETAINED_ACTION_RESULT_KIND_SUMMARIES = (
    len(ACTION_PARAMETER_CONTRACTS) * len(_ACTION_RESULT_CONTINUITY_STATUSES)
)
DECISION_HISTORY_PROJECTION_KIND = "recent_window_with_latest_action_kind_status_v2"
MAX_RESTRICTED_CONTINUITY_ENTRIES = 64
RESTRICTED_CONTINUITY_PROJECTION_KIND = "complete_source_linked_window_v0"


class StructuredChoiceError(ValueError):
    """A model-like value does not satisfy the attempted-action schema."""


class ModelUnavailableError(RuntimeError):
    """A configured model client explicitly reports that it is unavailable."""


class RestrictedInputTooLargeError(RuntimeError):
    """A provider adapter refused a restricted input above its approved ceiling."""


class RecordedDecisionError(RuntimeError):
    """Recorded decision data cannot be applied to the current restricted input."""


class _RecordedSafeFailure(RuntimeError):
    """A replayed record preserves one prior explicit model failure."""

    def __init__(
        self,
        *,
        failure_kind: str,
        failure_type: str,
        provider_call_attempted: bool,
    ) -> None:
        self.failure_kind = failure_kind
        self.failure_type = failure_type
        self.provider_call_attempted = provider_call_attempted


@dataclass(frozen=True)
class RecordedDecisionArchive:
    """Private, integrity-sealed evidence for one recorded decision replay.

    The caller retains the verification key separately from this archive. That
    lets replay reject a changed record before it can become an attempted
    action, without placing key material or the seal in objective history.
    This detects modification only while the key remains trusted; it is not a
    provenance claim about a party that controls that key.
    """

    records: tuple[PolicyDecisionRecord, ...]
    integrity_digest: str

    @classmethod
    def seal(
        cls,
        records: tuple[PolicyDecisionRecord, ...],
        *,
        integrity_key: bytes,
    ) -> RecordedDecisionArchive:
        """Create detached replay evidence authenticated by a caller-held key."""
        frozen_records = tuple(records)
        return cls(
            records=frozen_records,
            integrity_digest=_recorded_archive_digest(frozen_records, integrity_key),
        )

    def verify(self, *, integrity_key: bytes) -> None:
        """Fail closed when private replay evidence no longer matches its seal."""
        expected_digest = _recorded_archive_digest(self.records, integrity_key)
        if not hmac.compare_digest(self.integrity_digest, expected_digest):
            raise RecordedDecisionError("recorded decision archive integrity mismatch")


class _InvalidStructuredAttemptError(StructuredChoiceError):
    """A response cannot describe one supported attempted action."""


class ModelDecisionClient(Protocol):
    """Narrow source of one choice from detached restricted model input."""

    def choose(self, model_input: Mapping[str, object]) -> object:
        ...


def _recorded_archive_digest(
    records: tuple[PolicyDecisionRecord, ...], integrity_key: bytes
) -> str:
    if not isinstance(integrity_key, bytes) or not integrity_key:
        raise RecordedDecisionError(
            "recorded decision archive requires a non-empty verification key"
        )
    serialized_records = "[" + ",".join(
        _canonical_record_data(record) for record in records
    ) + "]"
    return hmac.new(
        integrity_key,
        serialized_records.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _canonical_record_data(record: PolicyDecisionRecord) -> str:
    return json.dumps(
        record.to_data(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


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

    @classmethod
    def from_archive(
        cls,
        archive: RecordedDecisionArchive,
        *,
        integrity_key: bytes,
    ) -> RecordedDecisionClient:
        """Construct replay only after its caller-held integrity seal verifies."""
        archive.verify(integrity_key=integrity_key)
        return cls.from_records(archive.records)

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
        if record["status"] == "failed":
            failure_kind = record["failure_kind"]
            failure_type = record["failure_type"]
            if not isinstance(failure_kind, str) or not isinstance(failure_type, str):
                raise RecordedDecisionError(
                    "recorded safe failure is missing failure evidence"
                )
            self._index += 1
            raise _RecordedSafeFailure(
                failure_kind=failure_kind,
                failure_type=failure_type,
                provider_call_attempted=bool(
                    record.get("provider_call_attempted", False)
                ),
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


def _decision_history_data(view: AgentView) -> dict[str, object]:
    """Project recent history plus bounded same-kind continuity entries.

    The recent window gives the model short-term cadence. An older attempted
    action can still explain a current choice. For outcomes, the latest
    completed and latest rejected result of one supported action kind can each
    matter, so retain one of each as an explicit bounded continuity rule. Only
    supported action kinds and these two finite statuses qualify; this cannot
    grow with arbitrary lifetime history data.
    """
    supported_kinds = set(ACTION_PARAMETER_CONTRACTS)
    latest_attempt_index_by_kind: dict[str, int] = {}
    for index, attempt in enumerate(view.action_history):
        if attempt.kind in supported_kinds:
            latest_attempt_index_by_kind[attempt.kind] = index
    included_attempt_indexes = set(
        range(
            max(0, len(view.action_history) - MAX_RETAINED_DECISION_HISTORY_ENTRIES),
            len(view.action_history),
        )
    )
    included_attempt_indexes.update(latest_attempt_index_by_kind.values())
    attempts = tuple(
        attempt
        for index, attempt in enumerate(view.action_history)
        if index in included_attempt_indexes
    )
    latest_result_index_by_kind_and_status: dict[tuple[str, str], int] = {}
    for index, result in enumerate(view.action_results):
        if (
            result.action_kind in supported_kinds
            and result.status in _ACTION_RESULT_CONTINUITY_STATUSES
        ):
            latest_result_index_by_kind_and_status[
                (result.action_kind, result.status)
            ] = index
    included_result_indexes = set(
        range(
            max(0, len(view.action_results) - MAX_RETAINED_DECISION_HISTORY_ENTRIES),
            len(view.action_results),
        )
    )
    included_result_indexes.update(latest_result_index_by_kind_and_status.values())
    results = tuple(
        result
        for index, result in enumerate(view.action_results)
        if index in included_result_indexes
    )
    return {
        "projection": {
            "kind": DECISION_HISTORY_PROJECTION_KIND,
            "maximum_recent_attempts": MAX_RETAINED_DECISION_HISTORY_ENTRIES,
            "maximum_latest_attempts_by_action_kind": (
                MAX_RETAINED_ACTION_ATTEMPT_KIND_SUMMARIES
            ),
            "maximum_attempts": (
                MAX_RETAINED_DECISION_HISTORY_ENTRIES
                + MAX_RETAINED_ACTION_ATTEMPT_KIND_SUMMARIES
            ),
            "maximum_recent_results": MAX_RETAINED_DECISION_HISTORY_ENTRIES,
            "maximum_latest_results_by_action_kind_and_status": (
                MAX_RETAINED_ACTION_RESULT_KIND_SUMMARIES
            ),
            "maximum_results": (
                MAX_RETAINED_DECISION_HISTORY_ENTRIES
                + MAX_RETAINED_ACTION_RESULT_KIND_SUMMARIES
            ),
            "total_attempts": len(view.action_history),
            "total_results": len(view.action_results),
            "omitted_attempts": len(view.action_history) - len(attempts),
            "omitted_results": len(view.action_results) - len(results),
        },
        "last_attempt": _attempt_data(view.last_attempt),
        "attempts": [_attempt_data(attempt) for attempt in attempts],
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
            for result in results
        ],
    }


def _restricted_continuity_view(
    view: AgentView,
) -> tuple[AgentView, dict[str, object]]:
    """Bound fresh evidence while refusing to hide an omitted relevant fact.

    Source-linked canonical understanding is behaviorally relevant: an older
    delivered observation that supports a retained belief, trace, stance, or
    accessible diary entry must stay in the fresh decision input. Older
    delivered material outside that explicit closure is context only, so the
    bounded recent window may omit it. When the required closure itself does
    not fit, the metadata marks the projection incomplete and
    ``ModelFocalPolicy`` returns a safe failure before a provider can receive a
    partial view.
    """

    required_observation_ids = {
        observation_id
        for belief in view.beliefs
        for observation_id in belief.source_observation_ids
    }
    required_observation_ids.update(
        trace.source_observation_id for trace in view.memory_traces
    )
    required_observation_ids.update(
        observation_id
        for entry in view.accessible_diary_entries
        for observation_id in entry.source_observation_ids
    )
    if view.contextual_stance is not None:
        required_observation_ids.update(
            view.contextual_stance.source_observation_ids
        )
    collections = {
        "delivered_observations": view.observations,
        "beliefs": view.beliefs,
        "memory_traces": view.memory_traces,
        "interpreted_claims": view.interpreted_claims,
        "accessible_diary_entries": view.accessible_diary_entries,
    }
    required_observations = tuple(
        observation
        for observation in view.observations
        if observation.observation_id in required_observation_ids
    )
    optional_observations = tuple(
        observation
        for observation in view.observations
        if observation.observation_id not in required_observation_ids
    )
    remaining_observation_capacity = max(
        0,
        MAX_RESTRICTED_CONTINUITY_ENTRIES - len(required_observations),
    )
    recent_optional_observations = (
        optional_observations[-remaining_observation_capacity:]
        if remaining_observation_capacity
        else ()
    )
    included_observation_ids = {
        observation.observation_id
        for observation in (
            required_observations[-MAX_RESTRICTED_CONTINUITY_ENTRIES:]
            + recent_optional_observations
        )
    }
    projected = {
        "delivered_observations": tuple(
            observation
            for observation in view.observations
            if observation.observation_id in included_observation_ids
        ),
        "beliefs": view.beliefs[-MAX_RESTRICTED_CONTINUITY_ENTRIES:],
        "memory_traces": view.memory_traces[-MAX_RESTRICTED_CONTINUITY_ENTRIES:],
        "interpreted_claims": view.interpreted_claims[
            -MAX_RESTRICTED_CONTINUITY_ENTRIES:
        ],
        "accessible_diary_entries": view.accessible_diary_entries[
            -MAX_RESTRICTED_CONTINUITY_ENTRIES:
        ],
    }
    counts = {
        name: {
            "total": len(entries),
            "included": len(projected[name]),
            "omitted": len(entries) - len(projected[name]),
            "required": (
                len(required_observations)
                if name == "delivered_observations"
                else len(entries)
            ),
            "required_omitted": (
                len(required_observations)
                - len(
                    {
                        observation.observation_id
                        for observation in projected["delivered_observations"]
                    }
                    & required_observation_ids
                )
                if name == "delivered_observations"
                else len(entries) - len(projected[name])
            ),
        }
        for name, entries in collections.items()
    }
    delivered_ids = {
        observation.observation_id
        for observation in projected["delivered_observations"]
    }
    trace_ids = {trace.trace_id for trace in projected["memory_traces"]}
    source_links_complete = (
        all(
            set(belief.source_observation_ids).issubset(delivered_ids)
            for belief in projected["beliefs"]
        )
        and all(
            trace.source_observation_id in delivered_ids
            for trace in projected["memory_traces"]
        )
        and all(
            claim.origin_trace_id in trace_ids
            for claim in projected["interpreted_claims"]
        )
        and all(
            set(entry.source_observation_ids).issubset(delivered_ids)
            for entry in projected["accessible_diary_entries"]
        )
        and (
            view.contextual_stance is None
            or (
                view.contextual_stance.source_claim_id
                in {claim.claim_id for claim in projected["interpreted_claims"]}
                and view.contextual_stance.source_trace_id in trace_ids
                and set(
                    view.contextual_stance.source_observation_ids
                ).issubset(delivered_ids)
            )
        )
    )
    complete = (
        all(count["required_omitted"] == 0 for count in counts.values())
        and source_links_complete
    )
    return (
        replace(
            view,
            observations=projected["delivered_observations"],
            beliefs=projected["beliefs"],
            memory_traces=projected["memory_traces"],
            interpreted_claims=projected["interpreted_claims"],
            accessible_diary_entry_count=len(
                projected["accessible_diary_entries"]
            ),
            accessible_diary_entries=projected["accessible_diary_entries"],
        ),
        {
            "kind": RESTRICTED_CONTINUITY_PROJECTION_KIND,
            "maximum_entries_per_collection": MAX_RESTRICTED_CONTINUITY_ENTRIES,
            "complete": complete,
            "source_links_complete": source_links_complete,
            "collections": counts,
        },
    )


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
    affordances = {
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
    if "household" in view.valid_actions:
        affordances["household"] = {
            "currently_applicable": view.household_action_available,
            "parameter_options": {},
        }
    return affordances


def model_input_from_view(view: AgentView) -> dict[str, object]:
    """Serialize only the restricted agent view into detached JSON-like data."""
    continuity_view, continuity_projection = _restricted_continuity_view(view)
    stance = continuity_view.contextual_stance
    affordances = _action_affordances(continuity_view)
    return {
        "tick": continuity_view.tick,
        "character": {
            "agent_id": continuity_view.agent_id,
            "display_name": continuity_view.display_name,
            "role": continuity_view.role,
        },
        "state": {
            "location": continuity_view.location,
            "aim": continuity_view.aim,
            "required_resource_id": continuity_view.required_resource_id,
            "required_units": continuity_view.required_units,
            "resource_holdings": to_plain_data(continuity_view.resource_holdings),
            "remaining_required_units": continuity_view.remaining_required_units,
            "obligations": list(continuity_view.obligations),
        },
        "decision_history": _decision_history_data(continuity_view),
        "continuity_projection": continuity_projection,
        "delivered_observations": [
            {
                "observation_id": observation.observation_id,
                "agent_id": observation.agent_id,
                "event_id": observation.event_id,
                "source": observation.source,
                "delivery_tick": observation.delivery_tick,
                "details": to_plain_data(observation.details),
            }
            for observation in continuity_view.observations
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
                for belief in continuity_view.beliefs
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
                for trace in continuity_view.memory_traces
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
                for claim in continuity_view.interpreted_claims
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
                    "object_id": continuity_view.accessible_diary_id,
                    "entry_count": continuity_view.accessible_diary_entry_count,
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
                        for entry in continuity_view.accessible_diary_entries
                    ],
                }
                if continuity_view.accessible_diary_id is not None
                else None
            ),
            "consultable_official_record_ids": list(
                continuity_view.consultable_official_record_ids
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
        model_input_bytes = restricted_decision_input_size_bytes(recorded_input)
        continuity_projection = model_input["continuity_projection"]
        if not continuity_projection["complete"]:
            if isinstance(self._client, RecordedDecisionClient):
                try:
                    self._client.choose(model_input)
                except _RecordedSafeFailure as error:
                    if (
                        error.failure_kind != "continuity_projection_incomplete"
                        or error.failure_type
                        != "RestrictedContinuityProjectionError"
                    ):
                        raise RecordedDecisionError(
                            "recorded incomplete continuity failure does not match"
                        ) from error
                else:
                    raise RecordedDecisionError(
                        "recorded selected decision has incomplete continuity"
                    )
            return self._safe_failure(
                view,
                recorded_input,
                model_input_bytes,
                "continuity_projection_incomplete",
                "RestrictedContinuityProjectionError",
                provider_call_attempted=False,
            )
        try:
            response = self._client.choose(model_input)
        except _RecordedSafeFailure as error:
            return self._safe_failure(
                view,
                recorded_input,
                model_input_bytes,
                error.failure_kind,
                error.failure_type,
                provider_call_attempted=error.provider_call_attempted,
            )
        except RestrictedInputTooLargeError as error:
            return self._safe_failure(
                view,
                recorded_input,
                model_input_bytes,
                "restricted_input_too_large",
                type(error).__name__,
                provider_call_attempted=True,
            )
        except TimeoutError as error:
            return self._safe_failure(
                view,
                recorded_input,
                model_input_bytes,
                "timeout",
                type(error).__name__,
                provider_call_attempted=True,
            )
        except ModelUnavailableError as error:
            return self._safe_failure(
                view,
                recorded_input,
                model_input_bytes,
                "unavailable_model",
                type(error).__name__,
                provider_call_attempted=True,
            )
        try:
            attempt = structured_choice_to_attempt(view, response)
        except _InvalidStructuredAttemptError as error:
            return self._safe_failure(
                view,
                recorded_input,
                model_input_bytes,
                "invalid_attempt",
                type(error).__name__,
                provider_call_attempted=True,
            )
        except StructuredChoiceError as error:
            return self._safe_failure(
                view,
                recorded_input,
                model_input_bytes,
                "malformed_response",
                type(error).__name__,
                provider_call_attempted=True,
            )
        self._decision_record = PolicyDecisionRecord(
            decision_id=f"model-decision-{view.agent_id}-{view.tick:04d}",
            tick=view.tick,
            agent_id=view.agent_id,
            policy_kind="model",
            configuration_id=self._configuration_id,
            status="selected",
            model_input=recorded_input,
            model_input_bytes=model_input_bytes,
            structured_response=response,
            attempted_action=_attempt_data(attempt) or {},
            attempted_action_kind=attempt.kind,
            authorship_identity=self._authorship_identity,
            provider_call_attempted=True,
        )
        return attempt

    def _safe_failure(
        self,
        view: AgentView,
        model_input: Mapping[str, object],
        model_input_bytes: int,
        failure_kind: str,
        failure_type: str,
        *,
        provider_call_attempted: bool,
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
            model_input_bytes=model_input_bytes,
            structured_response=None,
            attempted_action=_attempt_data(attempt) or {},
            authorship_identity=self._authorship_identity,
            failure_kind=failure_kind,
            failure_type=failure_type,
            provider_call_attempted=provider_call_attempted,
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
        failure_type = record.get("failure_type")
        if (
            kind != "wait"
            or to_plain_data(response["parameters"]) != {}
            or response["explanation"]
            != "wait because no valid model decision is available"
            or not isinstance(failure_kind, str)
            or not failure_kind
            or not isinstance(failure_type, str)
            or not failure_type
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
