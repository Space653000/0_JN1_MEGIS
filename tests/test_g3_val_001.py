"""G3-VAL-001 geometry / collision / clearance validators tests (E3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from megis.errors import ERROR_CODES
from megis.validation import (
    BoundingBox,
    ClearanceRequirement,
    ComponentBox,
    DesignValidationInput,
    validate_design,
)

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "contracts" / "g3" / "golden" / "validation-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "validation-corpus.schema.json"
RESULT_SCHEMA_PATH = ROOT / "schemas" / "v3" / "validation-result.schema.json"


def box(component_id: str, min_: tuple, max_: tuple) -> ComponentBox:
    return ComponentBox(component_id=component_id, box=BoundingBox(*min_, *max_))


@pytest.fixture(scope="module")
def corpus() -> dict:
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def corpus_schema() -> dict:
    return json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def result_schema() -> dict:
    return json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))


def codes_of(result) -> list[str]:
    return sorted(
        {issue.code for issue in result.checks if issue.code is not None}
    )


def test_corpus_validates_against_schema(corpus: dict, corpus_schema: dict) -> None:
    Draft202012Validator.check_schema(corpus_schema)
    validator = Draft202012Validator(corpus_schema)
    errors = list(validator.iter_errors(corpus))
    assert errors == []
    assert len(corpus["cases"]) >= 15


@pytest.mark.parametrize(
    "case",
    [
        json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["cases"][index]
        for index in range(
            len(json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["cases"])
        )
    ],
    ids=lambda item: item["case_id"],
)
def test_golden_case_matches_expected(case: dict) -> None:
    result = validate_design(
        DesignValidationInput.from_dict(case["input"]),
        validation_id=f"val-{case['case_id']}",
        design_ref=case["input"]["design_id"],
        created_at="2026-09-21T21:30:00+08:00",
    )
    assert result.status == case["expectStatus"], case["case_id"]
    assert codes_of(result) == sorted(case["expectCodes"]), case["case_id"]


def test_validation_result_is_schema_conformant(
    corpus: dict, result_schema: dict
) -> None:
    Draft202012Validator.check_schema(result_schema)
    validator = Draft202012Validator(result_schema)
    for case in corpus["cases"]:
        result = validate_design(
            DesignValidationInput.from_dict(case["input"]),
            validation_id=f"val-{case['case_id']}",
            design_ref=case["input"]["design_id"],
            created_at="2026-09-21T21:30:00+08:00",
        )
        payload = result.to_dict()
        assert list(validator.iter_errors(payload)) == [], case["case_id"]


def test_touching_faces_are_not_collisions() -> None:
    assert _collide(box("a", (0, 0, 0), (10, 10, 10)), box("b", (10, 0, 0), (20, 10, 10))) is False


def test_positive_overlap_is_collision() -> None:
    assert _collide(box("a", (0, 0, 0), (10, 10, 10)), box("b", (5, 5, 5), (15, 15, 15))) is True


def test_clearance_boundary_is_inclusive() -> None:
    design = DesignValidationInput(
        design_id="boundary",
        components=(
            box("base", (0, 0, 0), (10, 10, 10)),
            box("top", (0, 0, 14), (10, 10, 20)),
        ),
        clearances=(ClearanceRequirement("base", "top", 4.0),),
    )
    result = validate_design(
        design, validation_id="v", design_ref="d", created_at="now"
    )
    assert result.status == "pass"
    assert codes_of(result) == []


def test_clearance_violation_carries_rule_reference() -> None:
    design = DesignValidationInput(
        design_id="violated",
        components=(
            box("base", (0, 0, 0), (10, 10, 10)),
            box("top", (0, 0, 13), (10, 10, 20)),
        ),
        clearances=(
            ClearanceRequirement("base", "top", 4.0, rule_id="PCB_TOP_CLEAR_001"),
        ),
    )
    result = validate_design(
        design, validation_id="v", design_ref="d", created_at="now"
    )
    issue = result.checks[0]
    assert issue.code == "MEGIS-VAL-002"
    assert issue.rule_id == "PCB_TOP_CLEAR_001"
    assert issue.entity_refs == ("base", "top")


def test_invalid_geometry_skips_placement_checks() -> None:
    design = DesignValidationInput(
        design_id="invalid",
        components=(box("flat", (0, 0, 0), (10, 10, 0)),),
    )
    result = validate_design(
        design, validation_id="v", design_ref="d", created_at="now"
    )
    assert result.status == "fail"
    assert codes_of(result) == ["MEGIS-VAL-003"]
    assert all(issue.check_type == "geometry" for issue in result.checks)


def test_issue_carries_user_and_engineer_copy() -> None:
    result = validate_design(
        DesignValidationInput.from_dict(
            {
                "design_id": "d",
                "components": [
                    {"component_id": "a", "box": {"min": [0, 0, 0], "max": [10, 10, 10]}},
                    {"component_id": "b", "box": {"min": [5, 5, 5], "max": [15, 15, 15]}},
                ],
            }
        ),
        validation_id="v",
        design_ref="d",
        created_at="now",
    )
    payload = result.to_dict()
    issue = payload["results"][0]
    assert issue["user_message_zh_tw"]
    assert issue["engineer_detail"]
    assert issue["code"] == "MEGIS-VAL-001"


def test_validation_error_codes_are_registered() -> None:
    for code in ("MEGIS-VAL-001", "MEGIS-VAL-002", "MEGIS-VAL-003"):
        assert code in ERROR_CODES


def _collide(first: ComponentBox, second: ComponentBox) -> bool:
    from megis.validation.geometry import _collides

    return _collides(first.box, second.box)
