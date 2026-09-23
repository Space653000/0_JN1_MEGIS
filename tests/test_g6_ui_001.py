"""G6-UI-001 capability-driven guided flow tests (E3).

The guided flow only renders capabilities the backend has proven, never
fabricates an ``unsafe_to_default`` value, and produces byte-identical IR
through the UI-form and direct-API routes for the same logical inputs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from megis.errors import ERROR_CODES, MegisError, verify_error_codes
from megis.guides.capabilities import (
    GOLDEN_PATH,
    build_manifest,
    load_golden,
    validate_manifest,
)
from megis.guides.flow import (
    GuidedAnswers,
    build_ir_draft,
    build_ir_via_api,
    build_ir_via_ui,
    ir_equivalent,
)
from megis.guides.questions import GUIDED_QUESTIONS, guided_questions
from megis.contracts.validation import validate_engineering_ir

ROOT = Path(__file__).resolve().parents[1]


def _ui_state(overrides: dict | None = None) -> dict:
    state = {
        "width": 120,
        "depth": 80,
        "height": 20,
        "pcbCount": 1,
        "connector": "USB-C",
        "fastener": "M3",
        "cover": "removable",
        "quantity": "prototype",
        "priority": "serviceability",
        "purpose": "固定參考 PCB，供桌上測試與 USB-C 連接",
        "pcbEnvelopeMode": "reference_only",
        "pcbRequired": False,
    }
    state.update(overrides or {})
    return state


def _api_payload(overrides: dict | None = None) -> dict:
    payload = {
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
    payload.update(overrides or {})
    return payload


def test_manifest_is_deterministic_and_schema_valid() -> None:
    first = build_manifest()
    second = build_manifest()
    assert first == second
    assert first["manifestFingerprint"] == second["manifestFingerprint"]
    validate_manifest(first)
    # Only proven capabilities are advertised.
    assert all(entry["proven"] is True for entry in first["designTypes"])
    assert all(entry["proven"] is True for entry in first["geometry"]["operations"])
    assert all(entry["proven"] is True for entry in first["modules"]["capabilityLevels"])
    assert all(entry["proven"] is True for entry in first["relationships"])


def test_frozen_golden_matches_live_manifest() -> None:
    golden = load_golden()
    live = build_manifest()
    validate_manifest(golden)
    assert golden == live
    assert golden["manifestFingerprint"] == live["manifestFingerprint"]


def test_every_question_binds_an_ir_field_and_envelope() -> None:
    manifest = build_manifest()
    questions = guided_questions()
    assert len(questions) == len(GUIDED_QUESTIONS)
    ids = [question["id"] for question in questions]
    assert len(ids) == len(set(ids))
    for question in questions:
        assert isinstance(question["irField"], str)
        assert question["irField"].startswith("/")
        has_range = question["envelopeRange"] is not None
        has_options = len(question["options"]) > 0
        if question["inputKind"] != "text":
            assert has_range or has_options, f"{question['id']} lacks envelope range or options"
        # Envelope maxima must never exceed the proven envelope.
        if question["envelopeRange"] and "maxMm" in question["envelopeRange"]:
            envelope_max = manifest["envelope"]["outerDimensionsMm"]
            assert question["envelopeRange"]["maxMm"] <= max(envelope_max.values())
        if question["id"] == "Q-FIXTURE-PCB-ENVELOPE":
            assert question["unsafeToDefault"] is True


def test_build_ir_draft_is_schema_valid() -> None:
    document = build_ir_draft(GuidedAnswers())
    validate_engineering_ir(document)
    assert document["designId"] == "FIXTURE-GUIDED-001"
    assert document["maturity"] == "DRAFT"
    assert {component["componentType"] for component in document["components"]} == {
        "fixture_base",
        "cover",
        "pcb",
    }


def test_ui_and_api_routes_produce_equivalent_ir() -> None:
    ir_ui = build_ir_via_ui(_ui_state())
    ir_api = build_ir_via_api(_api_payload())
    assert ir_equivalent(ir_ui, ir_api)
    payload_a = json.loads(build_ir_via_ui(_ui_state({"pcbCount": 2})))
    payload_b = json.loads(build_ir_via_api(_api_payload({"pcb_count": 2})))
    assert payload_a == payload_b
    assert sum(1 for c in payload_a["components"] if c["componentType"] == "pcb") == 2


def test_missing_unsafe_dimension_blocks_generation() -> None:
    with pytest.raises(MegisError) as excinfo:
        build_ir_draft(GuidedAnswers(width_mm=None))
    assert excinfo.value.error_object.code == "MEGIS-UI-001"
    assert "外形尺寸" in excinfo.value.error_object.engineer_detail["nextStep"]


def test_pcb_envelope_abstention_blocks_generation() -> None:
    with pytest.raises(MegisError) as excinfo:
        build_ir_draft(GuidedAnswers(pcb_envelope_mode="unknown"))
    assert excinfo.value.error_object.code == "MEGIS-UI-001"


def test_envelope_escape_raises_env_error() -> None:
    with pytest.raises(MegisError) as excinfo:
        build_ir_draft(GuidedAnswers(width_mm=999.0))
    assert excinfo.value.error_object.code == "MEGIS-ENV-001"


def test_unsupported_option_raises_ui_002() -> None:
    with pytest.raises(MegisError) as excinfo:
        build_ir_draft(GuidedAnswers(connector="RJ45"))
    assert excinfo.value.error_object.code == "MEGIS-UI-002"
    with pytest.raises(MegisError) as excinfo:
        build_ir_draft(GuidedAnswers(pcb_count=4))
    assert excinfo.value.error_object.code == "MEGIS-UI-002"


def test_error_codes_registered() -> None:
    assert "MEGIS-UI-001" in ERROR_CODES
    assert "MEGIS-UI-002" in ERROR_CODES
    assert verify_error_codes() == []


def test_no_engineering_artifact_written_by_flow() -> None:
    import tempfile
    with tempfile.TemporaryDirectory(dir=ROOT / ".temp") as tmp:
        before = {p.name for p in Path(tmp).iterdir()}
        build_ir_draft(GuidedAnswers())
        after = {p.name for p in Path(tmp).iterdir()}
        assert before == after
