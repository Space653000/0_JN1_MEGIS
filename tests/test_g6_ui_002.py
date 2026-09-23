"""G6-UI-002 corrective tests for truthful guided-flow maturity."""

from __future__ import annotations

from contextlib import contextmanager
from http.client import HTTPConnection
import json
from threading import Thread

import pytest

from megis.api.server import ApiConfigurationError, create_server
from megis.guides.flow import GuidedAnswers, build_ir_draft, evaluate_guided_maturity
from megis.guides.flow import build_ir_via_api


API_PAYLOAD = {
    "width_mm": 120,
    "depth_mm": 80,
    "height_mm": 20,
    "pcb_count": 1,
    "connector": "USB-C",
    "fastener": "M3",
    "cover": "removable",
    "quantity": "prototype",
    "priority": "serviceability",
    "purpose": "固定參考 PCB，供桌上測試與 USB-C 連接",
    "pcb_envelope_mode": "reference_only",
    "pcb_required": False,
}


@contextmanager
def _running_api():
    server = create_server(port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _request(port: int, method: str, path: str, *, body: bytes | None = None, headers=None):
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    request_headers = {"Host": f"127.0.0.1:{port}", **(headers or {})}
    connection.request(method, path, body=body, headers=request_headers)
    response = connection.getresponse()
    payload = response.read()
    result = (response.status, dict(response.getheaders()), payload)
    connection.close()
    return result


def test_guided_draft_maturity_is_computed_by_the_evaluator() -> None:
    answers = GuidedAnswers()
    evaluation = evaluate_guided_maturity(answers)
    document = build_ir_draft(answers)

    assert evaluation.state == "DRAFT"
    assert document["maturity"] == evaluation.state
    assert evaluation.evaluator_version == "megis.maturity@1.0.0"
    assert any("unsafe_to_default" in reason for reason in evaluation.blocking_reasons)


def test_guided_draft_never_claims_prototype_before_execution_evidence() -> None:
    evaluation = evaluate_guided_maturity(GuidedAnswers(pcb_envelope_mode="provided"))

    assert evaluation.state == "DRAFT"
    assert evaluation.achieved_index == 0
    assert "PROTOTYPE" not in {evaluation.state}
    assert any("layout" in reason for reason in evaluation.blocking_reasons)


def test_maturity_digest_changes_when_guided_inputs_change() -> None:
    first = evaluate_guided_maturity(GuidedAnswers(width_mm=120.0))
    second = evaluate_guided_maturity(GuidedAnswers(width_mm=110.0))

    assert first.inputs_digest != second.inputs_digest


def test_api_refuses_non_loopback_bind() -> None:
    with pytest.raises(ApiConfigurationError, match="127.0.0.1"):
        create_server(host="0.0.0.0", port=0)


def test_health_capability_and_questions_are_served_from_backend() -> None:
    with _running_api() as port:
        health = _request(port, "GET", "/api/v1/health")
        capability = _request(port, "GET", "/api/v1/capabilities")
        questions = _request(port, "GET", "/api/v1/questions")

    assert health[0] == 200
    assert json.loads(health[2]) == {
        "schemaVersion": "1.0.0",
        "service": "megis-local-ir-api",
        "status": "ready",
    }
    capability_doc = json.loads(capability[2])
    assert capability_doc["corpusId"] == "megis-capability-manifest@1.0.0"
    assert "geometry" in capability_doc
    question_doc = json.loads(questions[2])
    assert len(question_doc["questions"]) == 11


def test_actual_http_ir_bytes_equal_direct_api_bytes() -> None:
    body = json.dumps(API_PAYLOAD, ensure_ascii=False).encode("utf-8")
    with _running_api() as port:
        status, headers, response_body = _request(
            port,
            "POST",
            "/api/v1/ir-drafts",
            body=body,
            headers={
                "Content-Type": "application/json",
                "Origin": "http://127.0.0.1:4173",
                "X-Correlation-ID": "test-http-equivalence",
            },
        )

    assert status == 200
    assert headers["X-Correlation-ID"] == "test-http-equivalence"
    assert response_body == build_ir_via_api(API_PAYLOAD).encode("utf-8")
    assert json.loads(response_body)["maturity"] == "DRAFT"


@pytest.mark.parametrize(
    ("headers", "expected_status"),
    [
        ({"Host": "evil.example", "Content-Type": "application/json"}, 403),
        (
            {
                "Content-Type": "application/json",
                "Origin": "https://evil.example",
            },
            403,
        ),
        ({"Content-Type": "text/plain"}, 415),
    ],
)
def test_api_rejects_untrusted_request_boundaries(headers, expected_status: int) -> None:
    body = json.dumps(API_PAYLOAD).encode("utf-8")
    with _running_api() as port:
        status, _, response_body = _request(
            port, "POST", "/api/v1/ir-drafts", body=body, headers=headers
        )

    assert status == expected_status
    error = json.loads(response_body)["error"]
    assert error["code"] in {"MEGIS-SCH-001", "MEGIS-SYS-002"}
    assert error["correlation_id"]


def test_api_rejects_oversized_body_before_json_decode() -> None:
    with _running_api() as port:
        status, _, response_body = _request(
            port,
            "POST",
            "/api/v1/ir-drafts",
            body=b"{" + (b" " * 65536) + b"}",
            headers={"Content-Type": "application/json"},
        )

    assert status == 413
    assert json.loads(response_body)["error"]["code"] == "MEGIS-SCH-001"
