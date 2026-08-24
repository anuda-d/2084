"""One native Ollama chat adapter for Mara's structured decisions."""

from __future__ import annotations

from dataclasses import dataclass
from http.client import HTTPConnection, HTTPException, RemoteDisconnected
from ipaddress import ip_address, ip_network
import json
import math
import socket
from threading import Event, Timer
from time import monotonic
from typing import Mapping, Protocol
from urllib.error import URLError
from urllib.parse import urlsplit

from policies.mara_decision_request import (
    DecisionAuthorshipIdentity,
    MAX_RESTRICTED_DECISION_INPUT_BYTES,
    compose_mara_decision_prompt,
    decision_authorship_identity,
    load_choose_next_action_skill,
    load_mara_profile,
)
from policies.model_focal_policy import (
    ModelUnavailableError,
    RestrictedInputTooLargeError,
)


OLLAMA_ADAPTER_VERSION = "ollama-chat-v0"
OLLAMA_TEMPERATURE = 0
OLLAMA_NUM_PREDICT = 256
OLLAMA_NUM_CTX = 16_384
OLLAMA_MAX_TIMEOUT_SECONDS = 3_600
OLLAMA_MAX_RESPONSE_BYTES = 1_048_576
_PRIVATE_OLLAMA_NETWORKS = tuple(
    ip_network(network)
    for network in (
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "fc00::/7",
        "::1/128",
    )
)


@dataclass(frozen=True)
class OllamaHttpResponse:
    status: int
    body: bytes
    body_too_large: bool = False


class OllamaHttpTransport(Protocol):
    """Injectable byte transport; provider semantics stay in the adapter."""

    def post_json(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: float,
    ) -> OllamaHttpResponse:
        ...


class _IpLiteralHTTPConnection(HTTPConnection):
    """Connect to an already validated IP literal without resolver work."""

    def connect(self) -> None:
        parsed_ip = ip_address(self.host)
        family = socket.AF_INET6 if parsed_ip.version == 6 else socket.AF_INET
        address = (
            (str(parsed_ip), self.port, 0, 0)
            if parsed_ip.version == 6
            else (str(parsed_ip), self.port)
        )
        active_socket = socket.socket(family, socket.SOCK_STREAM)
        active_socket.settimeout(self.timeout)
        if self.source_address:
            active_socket.bind(self.source_address)
        self.sock = active_socket
        try:
            active_socket.connect(address)
        except BaseException:
            self.close()
            raise


class _StandardLibraryOllamaTransport:
    def post_json(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: float,
    ) -> OllamaHttpResponse:
        parsed = urlsplit(url)
        connection = _IpLiteralHTTPConnection(
            parsed.hostname,
            port=parsed.port,
            timeout=timeout_seconds,
        )
        request_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        deadline = monotonic() + timeout_seconds
        deadline_expired = Event()

        def abort_at_deadline() -> None:
            deadline_expired.set()
            active_socket = connection.sock
            if active_socket is None:
                return
            try:
                active_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            active_socket.close()

        watchdog = Timer(timeout_seconds, abort_at_deadline)
        watchdog.daemon = True
        watchdog.start()
        try:
            connection.request(
                "POST",
                parsed.path,
                body=request_body,
                headers=dict(headers),
            )
            response = connection.getresponse()
            content_length = response.getheader("Content-Length")
            if content_length is not None:
                try:
                    if int(content_length) > OLLAMA_MAX_RESPONSE_BYTES:
                        return OllamaHttpResponse(
                            status=response.status,
                            body=b"",
                            body_too_large=True,
                        )
                except ValueError:
                    pass

            body = bytearray()
            while True:
                remaining = deadline - monotonic()
                if deadline_expired.is_set() or remaining <= 0:
                    raise TimeoutError("Ollama response exceeded its deadline")
                if connection.sock is not None:
                    connection.sock.settimeout(remaining)
                chunk = response.read1(
                    min(
                        65_536,
                        OLLAMA_MAX_RESPONSE_BYTES + 1 - len(body),
                    )
                )
                if not chunk:
                    break
                body.extend(chunk)
                if len(body) > OLLAMA_MAX_RESPONSE_BYTES:
                    return OllamaHttpResponse(
                        status=response.status,
                        body=b"",
                        body_too_large=True,
                    )
            if deadline_expired.is_set() or monotonic() > deadline:
                raise TimeoutError("Ollama response exceeded its deadline")
            return OllamaHttpResponse(
                status=response.status,
                body=bytes(body),
            )
        except (TimeoutError, socket.timeout):
            raise TimeoutError("Ollama response exceeded its deadline") from None
        except (HTTPException, OSError):
            if deadline_expired.is_set() or monotonic() >= deadline:
                raise TimeoutError("Ollama response exceeded its deadline") from None
            raise
        finally:
            watchdog.cancel()
            connection.close()


def _normalized_base_url(base_url: str) -> str:
    if not isinstance(base_url, str) or not base_url.strip():
        raise ValueError("Ollama base URL must be a non-empty string")
    parsed = urlsplit(base_url.strip())
    if parsed.scheme != "http" or not parsed.hostname:
        raise ValueError("Ollama base URL must be a private HTTP server origin")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Ollama base URL must not contain credentials")
    try:
        parsed_ip = ip_address(parsed.hostname)
    except ValueError as error:
        raise ValueError("Ollama base URL host must be an IP address") from error
    if getattr(parsed_ip, "scope_id", None) is not None:
        raise ValueError("Ollama base URL must not use a scoped IPv6 address")
    if not any(parsed_ip in network for network in _PRIVATE_OLLAMA_NETWORKS):
        raise ValueError("Ollama base URL must use a private IP address")
    try:
        parsed.port
    except ValueError as error:
        raise ValueError("Ollama base URL has an invalid port") from error
    if parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
        raise ValueError("Ollama base URL must not contain a path, query, or fragment")
    return f"{parsed.scheme}://{parsed.netloc}"


def _timeout_value(timeout_seconds: float) -> float:
    if (
        not isinstance(timeout_seconds, (int, float))
        or isinstance(timeout_seconds, bool)
    ):
        raise ValueError("Ollama timeout must be a positive number")
    timeout = float(timeout_seconds)
    if (
        not math.isfinite(timeout)
        or timeout <= 0
        or timeout > OLLAMA_MAX_TIMEOUT_SECONDS
    ):
        raise ValueError(
            "Ollama timeout must be a positive finite number no greater than "
            f"{OLLAMA_MAX_TIMEOUT_SECONDS} seconds"
        )
    return timeout


class OllamaDecisionClient:
    """Adapt one restricted model input to one native ``/api/chat`` call."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float = 60,
        transport: OllamaHttpTransport | None = None,
    ) -> None:
        if not isinstance(model, str) or not model.strip():
            raise ValueError("Ollama model must be a non-empty string")
        self._base_url = _normalized_base_url(base_url)
        self._model = model.strip()
        self._timeout_seconds = _timeout_value(timeout_seconds)
        self._transport = transport or _StandardLibraryOllamaTransport()
        self._profile = load_mara_profile()
        self._skill = load_choose_next_action_skill()
        self._authorship_identity = decision_authorship_identity(
            self._profile,
            (self._skill,),
        )

    @property
    def configuration_id(self) -> str:
        timeout = repr(self._timeout_seconds)
        return (
            f"{OLLAMA_ADAPTER_VERSION}:model={self._model}:temperature="
            f"{OLLAMA_TEMPERATURE}:num_ctx={OLLAMA_NUM_CTX}:num_predict="
            f"{OLLAMA_NUM_PREDICT}:timeout_seconds={timeout}"
        )

    @property
    def authorship_identity(self) -> DecisionAuthorshipIdentity:
        return self._authorship_identity

    def choose(self, model_input: Mapping[str, object]) -> object:
        prompt = compose_mara_decision_prompt(
            model_input,
            profile=self._profile,
            skill=self._skill,
        )
        if prompt.restricted_input_bytes > MAX_RESTRICTED_DECISION_INPUT_BYTES:
            raise RestrictedInputTooLargeError(
                "restricted decision input exceeds the approved byte ceiling"
            )
        payload = {
            "model": self._model,
            "messages": prompt.messages_data(),
            "stream": False,
            "think": False,
            "format": prompt.response_schema_data(),
            "options": {
                "temperature": OLLAMA_TEMPERATURE,
                "num_predict": OLLAMA_NUM_PREDICT,
                "num_ctx": OLLAMA_NUM_CTX,
            },
        }
        try:
            response = self._transport.post_json(
                url=self._base_url + "/api/chat",
                headers={"Content-Type": "application/json"},
                payload=payload,
                timeout_seconds=self._timeout_seconds,
            )
        except (TimeoutError, socket.timeout):
            raise TimeoutError("Ollama decision timed out") from None
        except URLError as error:
            if isinstance(error.reason, (TimeoutError, socket.timeout)):
                raise TimeoutError("Ollama decision timed out") from None
            raise ModelUnavailableError("Ollama model is unavailable") from None
        except RemoteDisconnected:
            raise ModelUnavailableError("Ollama model is unavailable") from None
        except HTTPException:
            return None
        except OSError:
            raise ModelUnavailableError("Ollama model is unavailable") from None

        if not isinstance(response, OllamaHttpResponse):
            return None
        if response.status != 200:
            raise ModelUnavailableError("Ollama model is unavailable")
        if response.body_too_large:
            return None
        try:
            envelope = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError):
            return None
        if not isinstance(envelope, dict):
            return None
        if "error" in envelope:
            raise ModelUnavailableError("Ollama model is unavailable")
        message = envelope.get("message")
        if (
            envelope.get("model") != self._model
            or envelope.get("done") is not True
            or not isinstance(message, dict)
            or message.get("role") != "assistant"
            or not isinstance(message.get("content"), str)
        ):
            return None
        try:
            return json.loads(message["content"])
        except (ValueError, RecursionError):
            return None
