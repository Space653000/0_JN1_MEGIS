"""G4-GRF-001 relationship vocabulary semantics tests (E3).

The closed eight-type vocabulary from blueprint 4.16 is consumed by the
Relationship JSON Schema and by the type semantics evaluator; every type has a
positive case and a counterexample, and the aggregation contract is asserted
against the golden corpus.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from megis.relationship import (
    RELATIONSHIP_TYPES,
    RelationshipValidationError,
    TYPE_MEANING,
    relationship_type_index,
    validate_relationship,
)

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "contracts" / "g4" / "golden" / "relationship-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "relationship-corpus.schema.json"
RELATIONSHIP_SCHEMA_PATH = ROOT / "schemas" / "v3" / "relationship.schema.json"


@pytest.fixture(scope="module")
def corpus() -> dict:
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def corpus_schema() -> dict:
    return json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def relationship_schema() -> dict:
    return json.loads(RELATIONSHIP_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_corpus_validates_against_schema(corpus: dict, corpus_schema: dict) -> None:
    Draft202012Validator.check_schema(corpus_schema)
    errors = list(Draft202012Validator(corpus_schema).iter_errors(corpus))
    assert errors == []
    assert len(corpus["cases"]) >= 16


def _relationship_errors(document: dict) -> list[str]:
    try:
        validate_relationship(document)
    except RelationshipValidationError as error:
        return error.errors
    return []


@pytest.mark.parametrize(
    "case",
    [
        json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["cases"][index]
        for index in range(
            len(json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["cases"])
        )
    ],
    ids=lambda case: case["case_id"],
)
def test_every_corpus_case_matches_golden(
    case: dict,
    relationship_schema: dict,
) -> None:
    Draft202012Validator.check_schema(relationship_schema)
    schema_errors = list(
        Draft202012Validator(relationship_schema).iter_errors(case["input"])
    )
    contract_errors = _relationship_errors(case["input"])

    if case["expect"]["valid"]:
        assert schema_errors == []
        assert contract_errors == []
    else:
        for fragment in case["expect"].get("schemaErrorContains", []):
            assert any(fragment in message for message in contract_errors), fragment
        for fragment in case["expect"].get("semanticErrorContains", []):
            assert any(fragment in message for message in contract_errors), fragment
        for fragment in case["expect"].get("errorContains", []):
            assert any(fragment in message for message in contract_errors), fragment

    document = case["input"]
    relationship_type = document.get("type")
    expected_type = case["expect"]["type"]
    if expected_type == "invalid":
        assert relationship_type_index(relationship_type) == -1
    else:
        assert relationship_type == expected_type
        assert relationship_type_index(relationship_type) == case["expect"]["typeIndex"]


def test_every_type_has_positive_and_negative_evidence(corpus: dict) -> None:
    positives = {case["case_id"] for case in corpus["cases"] if case["expect"]["valid"]}
    negatives = {case["case_id"] for case in corpus["cases"] if not case["expect"]["valid"]}
    assert positives
    assert negatives
    for relationship_type in RELATIONSHIP_TYPES:
        assert any(
            case["expect"]["type"] == relationship_type and case["expect"]["valid"]
            for case in corpus["cases"]
        ), relationship_type
        assert any(
            case["expect"]["type"] == relationship_type and not case["expect"]["valid"]
            for case in corpus["cases"]
        ), relationship_type


def test_vocabulary_is_closed_and_meaning_complete() -> None:
    assert len(RELATIONSHIP_TYPES) == 8
    assert set(RELATIONSHIP_TYPES) == {
        "contains",
        "mounts_to",
        "fastens",
        "opens_through",
        "clears",
        "aligns",
        "covers",
        "removable_along",
    }
    for relationship_type in RELATIONSHIP_TYPES:
        assert TYPE_MEANING[relationship_type]


def test_type_index_of_unknown_is_minus_one() -> None:
    assert relationship_type_index("made_up") == -1
    assert relationship_type_index(None) == -1


def test_self_relationship_is_rejected_semantically() -> None:
    document = {
        "schemaVersion": "1.0.0",
        "relationship_id": "rel.self",
        "type": "contains",
        "source": "mod.x",
        "target": "mod.x",
        "parameters": {
            "envelope_ref": {"value": "env.x@1.0.0", "provenance": ["spec.x"]},
            "cavity_ref": {"value": "cav.x@1.0.0", "provenance": ["spec.x"]},
        },
        "provenance": ["spec.x"],
    }
    with pytest.raises(RelationshipValidationError) as raised:
        validate_relationship(document)
    assert any(
        "/target" in message and "cannot relate" in message
        for message in raised.value.errors
    )


def test_relationship_validation_aggregates_schema_and_semantic_errors() -> None:
    missing_required = {
        "schemaVersion": "1.0.0",
        "relationship_id": "rel.bad",
        "type": "clears",
        "source": "mod.pcb",
        "target": "face.bracket_inner",
        "parameters": {},
        "provenance": ["spec.layout@2026-09-22"],
    }
    with pytest.raises(RelationshipValidationError) as raised:
        validate_relationship(missing_required)
    assert any("/parameters/minimum_distance_mm" in message for message in raised.value.errors)
