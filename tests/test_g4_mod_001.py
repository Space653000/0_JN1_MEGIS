"""G4-MOD-001 module capability level tests (E3).

The closed four-level vocabulary is consumed both by the Module JSON Schema and
by the capability policy evaluator; every capability-to-behaviour restriction
from blueprint section 12 is asserted directly and through the golden corpus.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from megis.module import (
    CAPABILITY_LEVELS,
    GEOMETRY_CAPABLE_INDEX,
    ModuleValidationError,
    capability_index,
    geometry_generator_required,
    policy_for,
    validate_module_document,
)

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "contracts" / "g4" / "golden" / "module-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "module-corpus.schema.json"
MODULE_SCHEMA_PATH = ROOT / "schemas" / "v3" / "module.schema.json"


@pytest.fixture(scope="module")
def corpus() -> dict:
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def corpus_schema() -> dict:
    return json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def module_schema() -> dict:
    return json.loads(MODULE_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_corpus_validates_against_schema(corpus: dict, corpus_schema: dict) -> None:
    Draft202012Validator.check_schema(corpus_schema)
    errors = list(Draft202012Validator(corpus_schema).iter_errors(corpus))
    assert errors == []
    assert len(corpus["cases"]) >= 16


def _module_errors(document: dict) -> list[str]:
    try:
        validate_module_document(document)
    except ModuleValidationError as error:
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
    module_schema: dict,
) -> None:
    Draft202012Validator.check_schema(module_schema)
    schema_errors = list(Draft202012Validator(module_schema).iter_errors(case["input"]))
    # validate_module_document aggregates schema and semantic findings into one
    # deterministic, JSON-pointer formatted error list; that list is the public contract.
    contract_errors = _module_errors(case["input"])

    if case["expect"]["valid"]:
        assert schema_errors == []
        assert contract_errors == []
    else:
        for fragment in case["expect"].get("schemaErrorContains", []):
            assert any(fragment in message for message in contract_errors), fragment
        for fragment in case["expect"].get("semanticErrorContains", []):
            assert any(fragment in message for message in contract_errors), fragment

    document = case["input"]
    level = document.get("capability_level")
    expected_level = case["expect"]["capabilityLevel"]
    if expected_level == "invalid":
        assert capability_index(level) == -1
    else:
        assert level == expected_level
        assert capability_index(level) == case["expect"]["index"]
    assert (
        geometry_generator_required(level) == case["expect"]["geometryGeneratorRequired"]
    )


def test_every_level_has_positive_and_negative_evidence(corpus: dict) -> None:
    positives = {case["case_id"] for case in corpus["cases"] if case["expect"]["valid"]}
    negatives = {case["case_id"] for case in corpus["cases"] if not case["expect"]["valid"]}
    assert positives
    assert negatives
    for level in CAPABILITY_LEVELS:
        assert any(
            case["expect"]["capabilityLevel"] == level and case["expect"]["valid"]
            for case in corpus["cases"]
        ), level
        assert any(
            case["expect"]["capabilityLevel"] == level and not case["expect"]["valid"]
            for case in corpus["cases"]
        ), level


@pytest.mark.parametrize(
    "level,index",
    [
        ("metadata_only", 0),
        ("layout_capable", 1),
        ("geometry_capable", 2),
        ("validated", 3),
    ],
)
def test_capability_ordering_is_monotonic(level: str, index: int) -> None:
    assert capability_index(level) == index
    assert geometry_generator_required(level) == (index >= GEOMETRY_CAPABLE_INDEX)


def test_capability_index_of_unknown_is_minus_one() -> None:
    assert capability_index("made_up_level") == -1
    assert capability_index(None) == -1


def test_policy_table_matches_blueprint_restrictions() -> None:
    expectations = [
        ("metadata_only", "僅資料", False, False, "DRAFT"),
        ("layout_capable", "可放置 envelope", True, False, "CONCEPT"),
        ("geometry_capable", "可放置", True, True, "PROTOTYPE"),
        ("validated", "可放置", True, True, "PROTOTYPE"),
    ]
    for level, ui_display, layout, geometry, maturity_cap in expectations:
        policy = policy_for(level)
        assert policy.ui_display == ui_display
        assert policy.layout_allowed is layout
        assert policy.geometry_allowed is geometry
        assert policy.maturity_cap == maturity_cap


def test_capability_level_restricts_validation_kinds() -> None:
    assert policy_for("metadata_only").validation == ()
    assert "clearance" in policy_for("layout_capable").validation
    assert "geometry_rules" in policy_for("geometry_capable").validation
    assert "golden" in policy_for("validated").validation
    assert policy_for("metadata_only").maturity_cap == "DRAFT"
    assert policy_for("layout_capable").maturity_cap == "CONCEPT"
    assert policy_for("geometry_capable").maturity_cap == "PROTOTYPE"
    assert policy_for("validated").maturity_cap == "PROTOTYPE"


def test_module_validation_aggregates_schema_and_semantic_errors(
    module_schema: dict,
) -> None:
    duplicate_interfaces = {
        "schemaVersion": "1.0.0",
        "module_id": "mod.dup",
        "version": "1.0.0",
        "capability_level": "layout_capable",
        "interfaces": ["mount_face", "mount_face"],
        "clearance_envelopes": [],
        "metadata": {},
        "rule_refs": [],
        "datasheet_refs": [],
    }
    with pytest.raises(ModuleValidationError) as raised:
        validate_module_document(duplicate_interfaces)
    assert any("duplicate interface" in message for message in raised.value.errors)

    missing_required = {
        "schemaVersion": "1.0.0",
        "module_id": "mod.badpcb",
        "version": "1.0.0",
        "capability_level": "validated",
        "interfaces": [],
        "clearance_envelopes": [],
        "metadata": {},
        "rule_refs": [],
        "datasheet_refs": [],
    }
    with pytest.raises(ModuleValidationError) as raised:
        validate_module_document(missing_required)
    assert any("/geometry_generator_ref" in message for message in raised.value.errors)
