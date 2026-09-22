from copy import deepcopy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
import pytest

from scripts.verify_g6_a11y_manual import EvidenceError, evaluate_document


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "v3" / "accessibility-manual-audit.schema.json"
TEMPLATE = ROOT / "contracts" / "g6" / "templates" / "accessibility-manual-audit.template.json"


def _template() -> dict:
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


def _completed() -> dict:
    document = _template()
    for section_name in ("keyboard", "screenReader"):
        section = document[section_name]
        section["status"] = "passed"
        section["reviewer"] = {
            "name": "Human Reviewer",
            "attestation": "I personally performed this manual accessibility audit.",
        }
        section["performedAt"] = "2026-09-22T23:50:00+08:00"
        section["environment"].update({
            "operatingSystem": "Windows 11",
            "browser": "Chrome",
            "browserVersion": "140.0",
        })
        for check in section["checks"]:
            check["result"] = "passed"
            check["notes"] = "Observed manually."
    document["screenReader"]["environment"].update({
        "assistiveTechnology": "NVDA",
        "assistiveTechnologyVersion": "2026.1",
    })
    return document


def test_schema_is_valid_draft_2020_12() -> None:
    Draft202012Validator.check_schema(json.loads(SCHEMA.read_text(encoding="utf-8")))


def test_pending_template_is_valid_but_not_closure_eligible() -> None:
    result = evaluate_document(_template())
    assert result["schemaValid"] is True
    assert result["closureEligible"] is False
    assert result["pendingChecks"] == 12


def test_completed_human_record_is_closure_eligible() -> None:
    result = evaluate_document(_completed())
    assert result["closureEligible"] is True
    assert result["passedChecks"] == 12
    assert result["failedChecks"] == 0


@pytest.mark.parametrize("section", ["keyboard", "screenReader"])
def test_duplicate_check_id_is_rejected(section: str) -> None:
    document = _template()
    document[section]["checks"][1]["id"] = document[section]["checks"][0]["id"]
    with pytest.raises(EvidenceError, match="exact required check IDs"):
        evaluate_document(document)


def test_unknown_check_id_is_rejected() -> None:
    document = _template()
    document["keyboard"]["checks"][0]["id"] = "invented-check"
    with pytest.raises(EvidenceError, match="exact required check IDs"):
        evaluate_document(document)


def test_passed_section_cannot_contain_pending_result() -> None:
    document = _completed()
    document["keyboard"]["checks"][0]["result"] = "pending"
    with pytest.raises(EvidenceError, match="passed section requires every check to pass"):
        evaluate_document(document)


def test_failed_check_requires_notes_and_prevents_closure() -> None:
    document = _completed()
    document["keyboard"]["status"] = "failed"
    document["keyboard"]["checks"][0]["result"] = "failed"
    document["keyboard"]["checks"][0]["notes"] = ""
    with pytest.raises(EvidenceError, match="failed check requires notes"):
        evaluate_document(document)
    document["keyboard"]["checks"][0]["notes"] = "Focus was not visible."
    result = evaluate_document(document)
    assert result["closureEligible"] is False
    assert result["failedChecks"] == 1


def test_completed_section_requires_human_identity_and_environment() -> None:
    document = _completed()
    document["screenReader"]["reviewer"] = None
    with pytest.raises(EvidenceError, match="schema validation failed"):
        evaluate_document(document)


def test_extra_fields_are_rejected_without_repair() -> None:
    document = _template()
    document["agentFilled"] = True
    with pytest.raises(EvidenceError, match="schema validation failed"):
        evaluate_document(document)


def test_wrong_work_item_is_rejected() -> None:
    document = _template()
    document["workItem"] = "G6-USE-001"
    with pytest.raises(EvidenceError, match="schema validation failed"):
        evaluate_document(document)


def test_evaluation_does_not_mutate_human_record() -> None:
    document = _completed()
    before = deepcopy(document)
    evaluate_document(document)
    assert document == before
