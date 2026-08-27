"""Public composition facade for one model-backed Mara decision."""

from __future__ import annotations

from policies.mara_decision_request import DecisionAuthorshipIdentity
from policies.model_focal_policy import (
    ModelDecisionClient,
    ModelFocalPolicy,
    RecordedDecisionArchive,
    RecordedDecisionClient,
)
from policies.ollama_client import OllamaDecisionClient
from simulation.actions import ActionAttempt
from simulation.agents import AgentView, PolicyDecisionRecord


RECORDED_MARA_CONFIGURATION_ID = "recorded:mara-harness-v0"


class MaraHarness:
    """Compose Mara's existing chooser collaborators behind one policy seam.

    The harness receives only an ``AgentView`` and returns one attempted action.
    It owns no world, scheduling, validation, consequence, or character state.
    """

    __slots__ = ("_policy", "_provider_kind")

    def __init__(self, policy: ModelFocalPolicy, *, provider_kind: str) -> None:
        self._policy = policy
        self._provider_kind = provider_kind

    @classmethod
    def from_ollama(
        cls,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float = 60,
    ) -> MaraHarness:
        """Construct model-backed Mara with the existing Ollama adapter."""
        client = OllamaDecisionClient(
            base_url=base_url,
            model=model,
            timeout_seconds=timeout_seconds,
        )
        return cls.from_ollama_client(client)

    @classmethod
    def from_ollama_client(
        cls,
        client: OllamaDecisionClient,
    ) -> MaraHarness:
        """Construct from the concrete adapter while retaining its provenance."""
        if not isinstance(client, OllamaDecisionClient):
            raise TypeError("client must be OllamaDecisionClient")
        return cls._from_model_client(
            client,
            configuration_id=client.configuration_id,
            authorship_identity=client.authorship_identity,
            provider_kind="ollama",
        )

    @classmethod
    def from_client(
        cls,
        client: ModelDecisionClient,
        *,
        configuration_id: str,
        authorship_identity: DecisionAuthorshipIdentity | None = None,
    ) -> MaraHarness:
        """Construct Mara around one injected restricted decision client."""
        return cls._from_model_client(
            client,
            configuration_id=configuration_id,
            authorship_identity=authorship_identity,
            provider_kind="injected",
        )

    @classmethod
    def _from_model_client(
        cls,
        client: ModelDecisionClient,
        *,
        configuration_id: str,
        authorship_identity: DecisionAuthorshipIdentity | None,
        provider_kind: str,
    ) -> MaraHarness:
        return cls(
            ModelFocalPolicy(
                client,
                configuration_id=configuration_id,
                authorship_identity=authorship_identity,
            ),
            provider_kind=provider_kind,
        )

    @classmethod
    def from_recorded_archive(
        cls,
        archive: RecordedDecisionArchive,
        *,
        integrity_key: bytes,
    ) -> MaraHarness:
        """Replay sealed private evidence after checking its caller-held key."""
        return cls._from_model_client(
            RecordedDecisionClient.from_archive(
                archive,
                integrity_key=integrity_key,
            ),
            configuration_id=RECORDED_MARA_CONFIGURATION_ID,
            authorship_identity=None,
            provider_kind="recorded",
        )

    @property
    def provider_kind(self) -> str:
        """Identify the concrete provider boundary without exposing config."""
        return self._provider_kind

    def choose(self, view: AgentView) -> ActionAttempt:
        """Return one attempt without validating, resolving, or applying it."""
        return self._policy.choose(view)

    def take_decision_record(self) -> PolicyDecisionRecord | None:
        """Take the latest private decision evidence, if one was produced."""
        return self._policy.take_decision_record()
