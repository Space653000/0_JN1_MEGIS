"""G6-AI-002 schema-bound Intent → Requirement quarantine tests (E3)."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from megis.ai import (
    AiConfig,
    AiLimits,
    AiOrchestrator,
    ProviderResponse,
    RecordedStubProvider,
    build_ir_with_confirmed_proposals,
    confirm_requirement_fields,
    parse_requirement_draft,
)
from megis.contracts.validation import validate_engineering_ir
from megis.errors import MegisError
from megis.guides.flow import GuidedAnswers

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "v3" / "ai-requirement-draft.schema.json"


def _proposal(
    source: str,
    field: str,
    value: object,
    quote: str,
    unit: str | None = None,
) -> dict:
    start = source.index(quote)
    return {
        "field": field,
        "value": value,
        "unit": unit,
        "knowledgeState": "llm_proposed",
        "evidenceSpan": {"start": start, "end": start + len(quote), "quote": quote},
    }


def _document(source: str, proposals: list[dict], unknown: list[str] | None = None) -> dict:
    return {
        "schemaVersion": "1.0.0",
        "sourceSha256": sha256(source.encode("utf-8")).hexdigest(),
        "proposals": proposals,
        "unknownFields": unknown or [],
    }


def _parse(source: str, proposals: list[dict], unknown: list[str] | None = None) -> dict:
    return parse_requirement_draft(
        json.dumps(_document(source, proposals, unknown), ensure_ascii=False), source
    )


def _enabled_config() -> AiConfig:
    return AiConfig(
        enabled=True,
        provider="recorded_stub",
        model_version="recorded-model@1.0.0",
        prompt_version="intent-draft@1.0.0",
        schema_version="1.0.0",
        limits=AiLimits(1000, 2, 4096, 2048, 0),
    )


def test_requirement_draft_schema_is_valid() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)


def test_schema_bound_output_is_accepted_as_llm_proposed() -> None:
    source = "外殼寬度 120 mm，使用 USB-C。"
    draft = _parse(
        source,
        [
            _proposal(source, "width_mm", 120, "120 mm", "mm"),
            _proposal(source, "connector", "USB-C", "USB-C"),
        ],
        ["depth_mm", "height_mm"],
    )
    assert all(item["knowledgeState"] == "llm_proposed" for item in draft["proposals"])
    assert draft["unknownFields"] == ["depth_mm", "height_mm"]


@pytest.mark.parametrize("raw", ["not json", "[]", '"string"', "null"])
def test_non_object_or_malformed_output_is_rejected_without_repair(raw: str) -> None:
    with pytest.raises(MegisError) as raised:
        parse_requirement_draft(raw, "intent")
    assert raised.value.error_object.code == "MEGIS-AI-002"
    assert raised.value.error_object.engineer_detail["accepted"] is False


def test_additional_or_missing_fields_are_rejected_by_schema() -> None:
    source = "寬度 120 mm"
    document = _document(source, [_proposal(source, "width_mm", 120, "120 mm", "mm")])
    document["unexpected"] = True
    with pytest.raises(MegisError) as raised:
        parse_requirement_draft(json.dumps(document), source)
    assert raised.value.error_object.code == "MEGIS-AI-002"


def test_source_hash_must_bind_output_to_exact_intent() -> None:
    source = "寬度 120 mm"
    document = _document(source, [_proposal(source, "width_mm", 120, "120 mm", "mm")])
    document["sourceSha256"] = "0" * 64
    with pytest.raises(MegisError) as raised:
        parse_requirement_draft(json.dumps(document), source)
    assert raised.value.error_object.code == "MEGIS-AI-002"


def test_evidence_span_must_exactly_match_source() -> None:
    source = "寬度 120 mm"
    proposal = _proposal(source, "width_mm", 120, "120 mm", "mm")
    proposal["evidenceSpan"]["end"] -= 1
    with pytest.raises(MegisError) as raised:
        _parse(source, [proposal])
    assert raised.value.error_object.code == "MEGIS-AI-002"


def test_numeric_value_must_exist_in_evidence_span() -> None:
    source = "寬度約一百二十 mm"
    proposal = _proposal(source, "width_mm", 120, "一百二十 mm", "mm")
    with pytest.raises(MegisError) as raised:
        _parse(source, [proposal])
    assert raised.value.error_object.code == "MEGIS-AI-002"


def test_dimension_requires_explicit_unit_in_value_and_evidence() -> None:
    source = "寬度 120"
    proposal = _proposal(source, "width_mm", 120, "120", None)
    with pytest.raises(MegisError) as raised:
        _parse(source, [proposal])
    assert raised.value.error_object.code == "MEGIS-AI-002"


def test_duplicate_proposal_and_proposed_unknown_conflict_are_rejected() -> None:
    source = "寬度 120 mm"
    proposal = _proposal(source, "width_mm", 120, "120 mm", "mm")
    with pytest.raises(MegisError):
        _parse(source, [proposal, proposal])
    with pytest.raises(MegisError):
        _parse(source, [proposal], ["width_mm"])


def test_confirmation_ledger_contains_only_explicitly_confirmed_fields() -> None:
    source = "寬度 110 mm，深度 70 mm。"
    draft = _parse(
        source,
        [
            _proposal(source, "width_mm", 110, "110 mm", "mm"),
            _proposal(source, "depth_mm", 70, "70 mm", "mm"),
        ],
    )
    ledger = confirm_requirement_fields(draft, ["width_mm"])
    assert ledger["confirmedValues"] == {"width_mm": 110}
    assert ledger["unconfirmedFields"] == ["depth_mm"]
    assert "llm_proposed" not in json.dumps(ledger)


def test_confirming_absent_field_is_rejected() -> None:
    source = "寬度 120 mm"
    draft = _parse(source, [_proposal(source, "width_mm", 120, "120 mm", "mm")])
    with pytest.raises(MegisError) as raised:
        confirm_requirement_fields(draft, ["height_mm"])
    assert raised.value.error_object.code == "MEGIS-AI-002"


def test_unconfirmed_value_cannot_enter_confirmed_ir() -> None:
    source = "寬度 110 mm，深度 70 mm。"
    draft = _parse(
        source,
        [
            _proposal(source, "width_mm", 110, "110 mm", "mm"),
            _proposal(source, "depth_mm", 70, "70 mm", "mm"),
        ],
    )
    document = build_ir_with_confirmed_proposals(
        draft, ["width_mm"], GuidedAnswers(width_mm=120, depth_mm=80)
    )
    dimensions = {
        item["name"]: item["quantity"]["nominal"]
        for item in document["components"][0]["dimensions"]
    }
    assert dimensions["width"] == 110
    assert dimensions["depth"] == 80
    assert "llm_proposed" not in json.dumps(document)
    assert any(item["source"] == "engineer_override" for item in document["provenance"])
    validate_engineering_ir(document)


def test_zero_confirmations_leave_form_ir_unchanged() -> None:
    source = "寬度 130 mm"
    draft = _parse(source, [_proposal(source, "width_mm", 130, "130 mm", "mm")])
    document = build_ir_with_confirmed_proposals(draft, [], GuidedAnswers(width_mm=120))
    width = document["components"][0]["dimensions"][0]["quantity"]["nominal"]
    assert width == 120
    assert all(item["id"] != "PROV-GUIDED-AI-CONFIRM" for item in document["provenance"])


def test_recorded_provider_output_flows_through_adapter_then_quarantine() -> None:
    source = "外殼高度 25 mm。"
    content = json.dumps(
        _document(source, [_proposal(source, "height_mm", 25, "25 mm", "mm")]),
        ensure_ascii=False,
    )
    provider = RecordedStubProvider(
        ProviderResponse(content, input_tokens=8, output_tokens=20, cost_microunits=0)
    )
    result = AiOrchestrator(_enabled_config(), provider).assist(source)
    assert result.mode == "ai_assisted" and result.content is not None
    draft = parse_requirement_draft(result.content, source)
    assert draft["proposals"][0]["field"] == "height_mm"


def test_out_of_envelope_value_stays_quarantined_until_confirmation() -> None:
    source = "寬度 999 mm"
    draft = _parse(source, [_proposal(source, "width_mm", 999, "999 mm", "mm")])
    safe = build_ir_with_confirmed_proposals(draft, [], GuidedAnswers(width_mm=120))
    assert safe["components"][0]["dimensions"][0]["quantity"]["nominal"] == 120
    with pytest.raises(MegisError) as raised:
        build_ir_with_confirmed_proposals(draft, ["width_mm"], GuidedAnswers())
    assert raised.value.error_object.code == "MEGIS-ENV-001"
