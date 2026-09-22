from copy import deepcopy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
import pytest

from megis.ai import ground_explanation, source_fingerprint
from megis.errors import MegisError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "v3" / "grounded-explanation.schema.json"


def _sources() -> dict:
    return {
        "ir": {
            "sourceType": "engineering_ir",
            "document": {"components": [{"dimensions": [{"quantity": {"nominal": 120, "tolerance": 0.1}}]}]},
        },
        "rules": {
            "sourceType": "rule_result",
            "document": {"results": [{"details": {"required_mm": 2.0, "actual_mm": 2.5}}]},
        },
        "manifest": {
            "sourceType": "manifest",
            "document": {"maturity": {"achieved_index": 2}},
        },
    }


def _output(sources: dict | None = None) -> dict:
    sources = sources or _sources()
    return {
        "schemaVersion": "1.0.0",
        "locale": "zh-TW",
        "sourceFingerprints": {
            key: source_fingerprint(value["document"]) for key, value in sources.items()
        },
        "paragraphs": [{
            "text": "底座寬 120 mm，公差 0.1 mm；最小需求 2.0 mm，實際 2.5 mm；成熟度索引 2。",
            "numericCitations": [
                {"token": "120", "sourceId": "ir", "jsonPointer": "/components/0/dimensions/0/quantity/nominal"},
                {"token": "0.1", "sourceId": "ir", "jsonPointer": "/components/0/dimensions/0/quantity/tolerance"},
                {"token": "2.0", "sourceId": "rules", "jsonPointer": "/results/0/details/required_mm"},
                {"token": "2.5", "sourceId": "rules", "jsonPointer": "/results/0/details/actual_mm"},
                {"token": "2", "sourceId": "manifest", "jsonPointer": "/maturity/achieved_index"},
            ],
        }],
    }


def _run(output: dict, sources: dict | None = None) -> dict:
    return ground_explanation(json.dumps(output, ensure_ascii=False), sources or _sources())


def test_schema_is_valid_draft_2020_12() -> None:
    Draft202012Validator.check_schema(json.loads(SCHEMA.read_text(encoding="utf-8")))


def test_every_number_is_grounded_across_all_three_source_types() -> None:
    result = _run(_output())
    assert result["grounding"] == {
        "groundedNumbers": 5,
        "totalNumbers": 5,
        "rate": 1.0,
        "verifiedSourceTypes": ["engineering_ir", "manifest", "rule_result"],
    }


def test_plain_language_without_numbers_needs_no_citation() -> None:
    output = _output()
    output["paragraphs"] = [{"text": "目前結果需要工程審查。", "numericCitations": []}]
    assert _run(output)["grounding"]["rate"] == 1.0


@pytest.mark.parametrize("mutation", ["missing", "extra", "wrong_value", "bad_pointer", "text_source"])
def test_ungrounded_or_mismatched_numbers_are_rejected(mutation: str) -> None:
    output = _output()
    if mutation == "missing":
        output["paragraphs"][0]["numericCitations"].pop()
    elif mutation == "extra":
        output["paragraphs"][0]["numericCitations"].append(deepcopy(output["paragraphs"][0]["numericCitations"][0]))
    elif mutation == "wrong_value":
        output["paragraphs"][0]["numericCitations"][0]["token"] = "121"
        output["paragraphs"][0]["text"] = output["paragraphs"][0]["text"].replace("120", "121")
    elif mutation == "bad_pointer":
        output["paragraphs"][0]["numericCitations"][0]["jsonPointer"] = "/components/9"
    else:
        output["paragraphs"][0]["numericCitations"][0]["jsonPointer"] = "/components/0/dimensions/0/quantity"
    with pytest.raises(MegisError, match="MEGIS-AI-002"):
        _run(output)


def test_tampered_source_fingerprint_is_rejected() -> None:
    sources = _sources()
    output = _output(sources)
    sources["ir"]["document"]["components"][0]["dimensions"][0]["quantity"]["nominal"] = 121
    with pytest.raises(MegisError, match="MEGIS-AI-002"):
        _run(output, sources)


def test_forged_fingerprint_is_rejected() -> None:
    output = _output()
    output["sourceFingerprints"]["ir"] = "0" * 64
    with pytest.raises(MegisError, match="MEGIS-AI-002"):
        _run(output)


def test_source_set_must_match_exactly() -> None:
    output = _output()
    del output["sourceFingerprints"]["manifest"]
    with pytest.raises(MegisError, match="MEGIS-AI-002"):
        _run(output)


def test_only_three_fact_source_types_are_allowed() -> None:
    sources = _sources()
    sources["ir"]["sourceType"] = "provider_memory"
    with pytest.raises(MegisError, match="MEGIS-AI-002"):
        _run(_output(sources), sources)


def test_invalid_json_and_schema_are_rejected_without_repair() -> None:
    with pytest.raises(MegisError, match="MEGIS-AI-002"):
        ground_explanation("not-json", _sources())
    output = _output()
    output["unexpected"] = True
    with pytest.raises(MegisError, match="MEGIS-AI-002"):
        _run(output)


def test_repeated_number_requires_repeated_citations() -> None:
    sources = _sources()
    output = _output(sources)
    citation = {"token": "120", "sourceId": "ir", "jsonPointer": "/components/0/dimensions/0/quantity/nominal"}
    output["paragraphs"] = [{"text": "寬度 120 mm，確認仍為 120 mm。", "numericCitations": [citation]}]
    with pytest.raises(MegisError, match="MEGIS-AI-002"):
        _run(output, sources)
    output["paragraphs"][0]["numericCitations"].append(deepcopy(citation))
    assert _run(output, sources)["grounding"]["totalNumbers"] == 2


def test_source_fingerprint_is_order_independent_and_value_sensitive() -> None:
    assert source_fingerprint({"a": 1, "b": 2}) == source_fingerprint({"b": 2, "a": 1})
    assert source_fingerprint({"a": 1}) != source_fingerprint({"a": 2})
