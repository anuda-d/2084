import json
from http.client import BadStatusLine, IncompleteRead, RemoteDisconnected
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
import socket
import threading
import time
import unittest
from unittest.mock import patch
from urllib.error import URLError

from observer.inspector import render_inspector
from observer.terminal import render_terminal
from policies.model_focal_policy import ModelFocalPolicy, model_input_from_view
from policies.ollama_client import (
    OLLAMA_NUM_CTX,
    OLLAMA_MAX_TIMEOUT_SECONDS,
    OLLAMA_MAX_RESPONSE_BYTES,
    OLLAMA_NUM_PREDICT,
    OLLAMA_TEMPERATURE,
    OllamaDecisionClient,
    OllamaHttpResponse,
)
from scenarios.first_day import FOCAL_AGENT_ID, build_first_day


TEST_BASE_URL = "http://10.255.255.1:11434"


class FakeOllamaTransport:
    def __init__(self, *results):
        self.results = results
        self.calls = []

    def post_json(self, **call):
        self.calls.append(call)
        result = self.results[len(self.calls) - 1]
        if isinstance(result, BaseException):
            raise result
        return result


def ollama_response(content, *, model="qwen3:4b-instruct"):
    return OllamaHttpResponse(
        status=200,
        body=json.dumps(
            {
                "model": model,
                "created_at": "2026-08-22T12:00:00Z",
                "message": {
                    "role": "assistant",
                    "content": content,
                    "thinking": "must never be retained",
                },
                "done": True,
                "done_reason": "stop",
            }
        ).encode(),
    )


def valid_wait_content():
    return json.dumps(
        {
            "kind": "wait",
            "parameters": {},
            "explanation": "I will remain here briefly.",
            "decision_reason": "The immediate obligations allow a short pause.",
        }
    )


class OllamaDecisionClientTests(unittest.TestCase):
    def test_exact_native_chat_request_returns_one_candidate_choice(self):
        transport = FakeOllamaTransport(ollama_response(valid_wait_content()))
        client = OllamaDecisionClient(
            base_url=TEST_BASE_URL + "/",
            model="qwen3:4b-instruct",
            transport=transport,
        )
        simulation = build_first_day(seed=42)
        view = simulation.agent_view(FOCAL_AGENT_ID)
        model_input = model_input_from_view(view)

        choice = client.choose(model_input)

        self.assertEqual(choice["kind"], "wait")
        self.assertEqual(len(transport.calls), 1)
        call = transport.calls[0]
        self.assertEqual(call["url"], TEST_BASE_URL + "/api/chat")
        self.assertEqual(call["headers"], {"Content-Type": "application/json"})
        self.assertEqual(call["timeout_seconds"], 60.0)
        payload = call["payload"]
        self.assertEqual(
            set(payload),
            {"model", "messages", "stream", "think", "format", "options"},
        )
        self.assertEqual(payload["model"], "qwen3:4b-instruct")
        self.assertFalse(payload["stream"])
        self.assertFalse(payload["think"])
        self.assertEqual(
            payload["options"],
            {
                "temperature": OLLAMA_TEMPERATURE,
                "num_predict": OLLAMA_NUM_PREDICT,
                "num_ctx": OLLAMA_NUM_CTX,
            },
        )
        self.assertEqual([item["role"] for item in payload["messages"]], ["system", "user"])
        self.assertEqual(len(payload["format"]["oneOf"]), 8)
        json.dumps(payload)
        self.assertNotIn("10.255.255.1", client.configuration_id)
        self.assertIn("model=qwen3:4b-instruct", client.configuration_id)
        self.assertIn("temperature=0", client.configuration_id)
        self.assertIn("num_ctx=16384", client.configuration_id)
        self.assertIn("num_predict=256", client.configuration_id)
        self.assertIn("timeout_seconds=60.0", client.configuration_id)

    def test_policy_uses_extracted_choice_and_records_no_provider_envelope(self):
        secret_marker = "private-provider-thinking-marker"
        response = ollama_response(valid_wait_content())
        envelope = json.loads(response.body)
        envelope["message"]["thinking"] = secret_marker
        transport = FakeOllamaTransport(
            OllamaHttpResponse(status=200, body=json.dumps(envelope).encode())
        )
        client = OllamaDecisionClient(
            base_url=TEST_BASE_URL,
            model="qwen3:4b-instruct",
            transport=transport,
        )
        simulation = build_first_day(
            seed=42,
            focal_policy=ModelFocalPolicy(
                client,
                configuration_id=client.configuration_id,
            ),
        )

        snapshot = simulation.step()

        focal_attempt = next(
            event
            for event in simulation.events
            if event.kind == "action_attempted" and event.actor_id == FOCAL_AGENT_ID
        )
        record = simulation.decision_records[0]
        self.assertEqual(focal_attempt.details["action_kind"], "wait")
        self.assertEqual(snapshot.current_action, "I will remain here briefly.")
        self.assertEqual(
            snapshot.explanation,
            "The immediate obligations allow a short pause.",
        )
        self.assertEqual(record.structured_response["kind"], "wait")
        self.assertNotIn(secret_marker, json.dumps(record.to_data()))
        self.assertNotIn(secret_marker, render_terminal((snapshot,)))
        self.assertNotIn(secret_marker, render_inspector(simulation))

    def test_empty_query_or_fragment_suffix_cannot_change_chat_path(self):
        simulation = build_first_day(seed=42)
        model_input = model_input_from_view(simulation.agent_view(FOCAL_AGENT_ID))
        for suffix in ("?", "#"):
            with self.subTest(suffix=suffix):
                transport = FakeOllamaTransport(
                    ollama_response(valid_wait_content())
                )
                client = OllamaDecisionClient(
                    base_url=TEST_BASE_URL + suffix,
                    model="qwen3:4b-instruct",
                    transport=transport,
                )

                client.choose(model_input)

                self.assertEqual(
                    transport.calls[0]["url"],
                    TEST_BASE_URL + "/api/chat",
                )

    def test_each_call_is_fresh_stateless_and_never_retried(self):
        transport = FakeOllamaTransport(
            ollama_response(valid_wait_content()),
            ollama_response(valid_wait_content()),
        )
        client = OllamaDecisionClient(
            base_url=TEST_BASE_URL,
            model="qwen3:4b-instruct",
            transport=transport,
        )
        simulation = build_first_day(seed=42)

        first = model_input_from_view(simulation.agent_view(FOCAL_AGENT_ID))
        client.choose(first)
        simulation.step()
        second = model_input_from_view(simulation.agent_view(FOCAL_AGENT_ID))
        client.choose(second)

        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(
            [len(call["payload"]["messages"]) for call in transport.calls],
            [2, 2],
        )
        self.assertNotEqual(
            transport.calls[0]["payload"]["messages"][1]["content"],
            transport.calls[1]["payload"]["messages"][1]["content"],
        )

        failing = FakeOllamaTransport(ConnectionRefusedError("private address"))
        failed_client = OllamaDecisionClient(
            base_url=TEST_BASE_URL,
            model="qwen3:4b-instruct",
            transport=failing,
        )
        failed_simulation = build_first_day(
            seed=42,
            focal_policy=ModelFocalPolicy(
                failed_client,
                configuration_id=failed_client.configuration_id,
            ),
        )
        failed_simulation.step()
        self.assertEqual(len(failing.calls), 1)
        self.assertEqual(
            failed_simulation.decision_records[0].failure_kind,
            "unavailable_model",
        )

    def test_real_transport_rejects_redirect_without_following_it(self):
        requests = []

        class RedirectHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                requests.append((self.command, self.path))
                self.send_response(302)
                self.send_header("Location", "/redirected")
                self.end_headers()

            def do_GET(self):
                requests.append((self.command, self.path))
                response = ollama_response(valid_wait_content())
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response.body)))
                self.end_headers()
                self.wfile.write(response.body)

            def log_message(self, format, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), RedirectHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        try:
            client = OllamaDecisionClient(
                base_url=f"http://127.0.0.1:{server.server_port}",
                model="qwen3:4b-instruct",
                timeout_seconds=2,
            )
            simulation = build_first_day(
                seed=42,
                focal_policy=ModelFocalPolicy(
                    client,
                    configuration_id=client.configuration_id,
                ),
            )

            simulation.step()
        finally:
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=2)

        self.assertEqual(requests, [("POST", "/api/chat")])
        self.assertEqual(
            simulation.decision_records[0].failure_kind,
            "unavailable_model",
        )
        self.assertNotIn(
            str(server.server_port),
            json.dumps(simulation.decision_records[0].to_data()),
        )

    def test_real_transport_disables_environment_http_proxies(self):
        origin_requests = []
        proxy_requests = []
        response = ollama_response(valid_wait_content())

        def handler_for(requests):
            class Handler(BaseHTTPRequestHandler):
                def do_POST(self):
                    requests.append((self.command, self.path))
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(response.body)))
                    self.end_headers()
                    self.wfile.write(response.body)

                def log_message(self, format, *args):
                    pass

            return Handler

        origin = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(origin_requests))
        proxy = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(proxy_requests))
        origin_thread = threading.Thread(target=origin.serve_forever, daemon=True)
        proxy_thread = threading.Thread(target=proxy.serve_forever, daemon=True)
        origin_thread.start()
        proxy_thread.start()
        proxy_url = f"http://127.0.0.1:{proxy.server_port}"
        try:
            with patch.dict(
                os.environ,
                {
                    "http_proxy": proxy_url,
                    "HTTP_PROXY": proxy_url,
                    "no_proxy": "",
                    "NO_PROXY": "",
                },
            ):
                client = OllamaDecisionClient(
                    base_url=f"http://127.0.0.1:{origin.server_port}",
                    model="qwen3:4b-instruct",
                    timeout_seconds=2,
                )
                simulation = build_first_day(seed=42)
                choice = client.choose(
                    model_input_from_view(simulation.agent_view(FOCAL_AGENT_ID))
                )
        finally:
            origin.shutdown()
            proxy.shutdown()
            origin.server_close()
            proxy.server_close()
            origin_thread.join(timeout=2)
            proxy_thread.join(timeout=2)

        self.assertEqual(choice["kind"], "wait")
        self.assertEqual(origin_requests, [("POST", "/api/chat")])
        self.assertEqual(proxy_requests, [])

    def test_real_transport_bypasses_name_resolution_for_validated_ip(self):
        requests = []
        response = ollama_response(valid_wait_content())

        class DirectHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                requests.append((self.command, self.path))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response.body)))
                self.end_headers()
                self.wfile.write(response.body)

            def log_message(self, format, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), DirectHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        def forbidden_resolution(*args, **kwargs):
            time.sleep(0.3)
            raise AssertionError("numeric Ollama origin must not use getaddrinfo")

        try:
            with patch("socket.getaddrinfo", side_effect=forbidden_resolution):
                client = OllamaDecisionClient(
                    base_url=f"http://127.0.0.1:{server.server_port}",
                    model="qwen3:4b-instruct",
                    timeout_seconds=0.2,
                )
                simulation = build_first_day(seed=42)
                started = time.monotonic()
                choice = client.choose(
                    model_input_from_view(simulation.agent_view(FOCAL_AGENT_ID))
                )
                elapsed = time.monotonic() - started
        finally:
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=2)

        self.assertEqual(choice["kind"], "wait")
        self.assertEqual(requests, [("POST", "/api/chat")])
        self.assertLess(elapsed, 0.2)

    def test_real_transport_enforces_total_deadline_during_slow_body(self):
        requests = []
        response = ollama_response(valid_wait_content())

        class SlowHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                requests.append((self.command, self.path))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response.body)))
                self.end_headers()
                chunk_size = max(1, len(response.body) // 20)
                for start in range(0, len(response.body), chunk_size):
                    try:
                        self.wfile.write(response.body[start : start + chunk_size])
                        self.wfile.flush()
                    except OSError:
                        break
                    time.sleep(0.04)

            def log_message(self, format, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), SlowHandler)
        server.daemon_threads = True
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        try:
            client = OllamaDecisionClient(
                base_url=f"http://127.0.0.1:{server.server_port}",
                model="qwen3:4b-instruct",
                timeout_seconds=0.1,
            )
            simulation = build_first_day(
                seed=42,
                focal_policy=ModelFocalPolicy(
                    client,
                    configuration_id=client.configuration_id,
                ),
            )
            started = time.monotonic()

            simulation.step()

            elapsed = time.monotonic() - started
        finally:
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=2)

        self.assertEqual(requests, [("POST", "/api/chat")])
        self.assertLess(elapsed, 0.5)
        self.assertEqual(simulation.decision_records[0].failure_kind, "timeout")

    def test_real_transport_maps_close_before_status_to_unavailable(self):
        requests = []

        class ClosingHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                requests.append((self.command, self.path))
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()

            def log_message(self, format, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), ClosingHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        try:
            client = OllamaDecisionClient(
                base_url=f"http://127.0.0.1:{server.server_port}",
                model="qwen3:4b-instruct",
                timeout_seconds=2,
            )
            simulation = build_first_day(
                seed=42,
                focal_policy=ModelFocalPolicy(
                    client,
                    configuration_id=client.configuration_id,
                ),
            )

            simulation.step()
        finally:
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=2)

        self.assertEqual(requests, [("POST", "/api/chat")])
        self.assertEqual(
            simulation.decision_records[0].failure_kind,
            "unavailable_model",
        )

    def test_real_transport_caps_success_and_error_response_bodies(self):
        for status, expected_failure in (
            (200, "malformed_response"),
            (500, "unavailable_model"),
        ):
            with self.subTest(status=status):
                requests = []

                class OversizedHandler(BaseHTTPRequestHandler):
                    def do_POST(self):
                        requests.append((self.command, self.path))
                        self.send_response(status)
                        self.send_header("Content-Type", "application/json")
                        self.send_header(
                            "Content-Length",
                            str(OLLAMA_MAX_RESPONSE_BYTES + 1),
                        )
                        self.end_headers()

                    def log_message(self, format, *args):
                        pass

                server = ThreadingHTTPServer(("127.0.0.1", 0), OversizedHandler)
                server_thread = threading.Thread(
                    target=server.serve_forever,
                    daemon=True,
                )
                server_thread.start()
                try:
                    client = OllamaDecisionClient(
                        base_url=f"http://127.0.0.1:{server.server_port}",
                        model="qwen3:4b-instruct",
                        timeout_seconds=2,
                    )
                    simulation = build_first_day(
                        seed=42,
                        focal_policy=ModelFocalPolicy(
                            client,
                            configuration_id=client.configuration_id,
                        ),
                    )

                    simulation.step()
                finally:
                    server.shutdown()
                    server.server_close()
                    server_thread.join(timeout=2)

                self.assertEqual(requests, [("POST", "/api/chat")])
                self.assertEqual(
                    simulation.decision_records[0].failure_kind,
                    expected_failure,
                )

    def test_timeout_and_unavailable_failures_map_to_existing_policy_paths(self):
        cases = (
            (TimeoutError("private timeout"), "timeout", "private timeout"),
            (
                socket.timeout("private socket timeout"),
                "timeout",
                "private socket timeout",
            ),
            (
                URLError(TimeoutError("private nested timeout")),
                "timeout",
                "private nested timeout",
            ),
            (
                URLError(ConnectionRefusedError("private host")),
                "unavailable_model",
                "private host",
            ),
            (OSError("private route"), "unavailable_model", "private route"),
            (
                RemoteDisconnected("private no response"),
                "unavailable_model",
                "private no response",
            ),
            (
                OllamaHttpResponse(404, b'{"error":"model not found"}'),
                "unavailable_model",
                "model not found",
            ),
            (
                OllamaHttpResponse(500, b'{"error":"service failed"}'),
                "unavailable_model",
                "service failed",
            ),
            (
                ollama_response(valid_wait_content()),
                None,
                "must never be retained",
            ),
        )
        for result, expected_failure, private_marker in cases:
            with self.subTest(result=result, expected_failure=expected_failure):
                transport = FakeOllamaTransport(result)
                client = OllamaDecisionClient(
                    base_url=TEST_BASE_URL,
                    model="qwen3:4b-instruct",
                    transport=transport,
                )
                simulation = build_first_day(
                    seed=42,
                    focal_policy=ModelFocalPolicy(
                        client,
                        configuration_id=client.configuration_id,
                    ),
                )

                simulation.step()

                self.assertEqual(len(transport.calls), 1)
                self.assertEqual(
                    simulation.decision_records[0].failure_kind,
                    expected_failure,
                )
                encoded = json.dumps(simulation.decision_records[0].to_data())
                self.assertNotIn(private_marker, encoded)
                self.assertNotIn("10.255.255.1", encoded)

    def test_malformed_provider_data_reaches_existing_malformed_path(self):
        deeply_nested_json = "[" * 2_000 + "0" + "]" * 2_000
        oversized_integer_json = "9" * 5_000
        oversized_envelope = (
            '{"model":"qwen3:4b-instruct","done":true,'
            '"provider_metadata":'
            + oversized_integer_json
            + ',"message":{"role":"assistant","content":"{}"}}'
        )
        malformed_results = (
            (OllamaHttpResponse(200, b"not-json"), "not-json"),
            (OllamaHttpResponse(200, b"[]"), None),
            (
                OllamaHttpResponse(
                    200,
                    b'{"model":"qwen3:4b-instruct","done":true}',
                ),
                None,
            ),
            (ollama_response("not decision json"), "not decision json"),
            (ollama_response("[]"), None),
            (ollama_response(json.dumps({"kind": "wait"})), None),
            (
                ollama_response(
                    valid_wait_content(),
                    model="different-model:latest",
                ),
                "different-model:latest",
            ),
            (IncompleteRead(b"private truncated provider body"), "private truncated"),
            (BadStatusLine("private malformed status line"), "private malformed"),
            (
                OllamaHttpResponse(200, deeply_nested_json.encode()),
                None,
            ),
            (ollama_response(deeply_nested_json), None),
            (OllamaHttpResponse(200, oversized_envelope.encode()), None),
            (ollama_response(oversized_integer_json), None),
        )
        for result, private_marker in malformed_results:
            with self.subTest(result=result):
                transport = FakeOllamaTransport(result)
                client = OllamaDecisionClient(
                    base_url=TEST_BASE_URL,
                    model="qwen3:4b-instruct",
                    transport=transport,
                )
                simulation = build_first_day(
                    seed=42,
                    focal_policy=ModelFocalPolicy(
                        client,
                        configuration_id=client.configuration_id,
                    ),
                )

                simulation.step()

                self.assertEqual(len(transport.calls), 1)
                self.assertEqual(
                    simulation.decision_records[0].failure_kind,
                    "malformed_response",
                )
                if private_marker is not None:
                    self.assertNotIn(
                        private_marker,
                        json.dumps(simulation.decision_records[0].to_data()),
                    )

    def test_structurally_invalid_choice_remains_invalid_attempt(self):
        content = json.dumps(
            {
                "kind": "travel",
                "parameters": {},
                "explanation": "I will travel.",
                "decision_reason": "The workplace obligation is current.",
            }
        )
        transport = FakeOllamaTransport(ollama_response(content))
        client = OllamaDecisionClient(
            base_url=TEST_BASE_URL,
            model="qwen3:4b-instruct",
            transport=transport,
        )
        simulation = build_first_day(
            seed=42,
            focal_policy=ModelFocalPolicy(
                client,
                configuration_id=client.configuration_id,
            ),
        )

        simulation.step()

        self.assertEqual(
            simulation.decision_records[0].failure_kind,
            "invalid_attempt",
        )

    def test_configuration_rejects_credentials_and_non_origin_urls(self):
        invalid_urls = (
            "",
            "ollama.invalid:11434",
            "ftp://ollama.invalid",
            "http://user:secret@ollama.invalid:11434",
            "http://ollama.invalid:11434/api",
            "http://ollama.invalid:11434?token=secret",
            "http://ollama.invalid:not-a-port",
            "http://ollama.invalid:70000",
            "http://ollama.invalid:11434",
            "https://127.0.0.1:11434",
            "http://[fe80::1%lo0]:11434",
            "http://[fe80::1%25lo0]:11434",
            "http://8.8.8.8:11434",
            "http://[2001:4860:4860::8888]:11434",
        )
        for base_url in invalid_urls:
            with self.subTest(base_url=base_url):
                with self.assertRaises(ValueError):
                    OllamaDecisionClient(
                        base_url=base_url,
                        model="qwen3:4b-instruct",
                    )

        with self.assertRaises(ValueError):
            OllamaDecisionClient(
                base_url=TEST_BASE_URL,
                model="",
            )
        for timeout_seconds in (
            0,
            float("nan"),
            float("inf"),
            float("-inf"),
            OLLAMA_MAX_TIMEOUT_SECONDS + 1,
            1e308,
        ):
            with self.subTest(timeout_seconds=timeout_seconds):
                with self.assertRaises(ValueError):
                    OllamaDecisionClient(
                        base_url=TEST_BASE_URL,
                        model="qwen3:4b-instruct",
                        timeout_seconds=timeout_seconds,
                    )

        first = OllamaDecisionClient(
            base_url=TEST_BASE_URL,
            model="qwen3:4b-instruct",
            timeout_seconds=60,
        )
        second = OllamaDecisionClient(
            base_url=TEST_BASE_URL,
            model="qwen3:4b-instruct",
            timeout_seconds=60.000001,
        )
        self.assertNotEqual(first.configuration_id, second.configuration_id)


if __name__ == "__main__":
    unittest.main()
