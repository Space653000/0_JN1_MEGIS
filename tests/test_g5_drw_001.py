"""G5-DRW-001 fixed-template draft drawing tests (E3/E4-readiness).

``build_draft_drawing`` renders a deterministic A4 Fixture SVG from IR
metadata (never from STEP), fills the title block, pins whitelist dimensions
equal to the IR and records a QA checklist.  ``verify_draft_drawing`` recomputes
QA and the SVG fingerprint; tampering or drift raises ``MEGIS-DRW-001``, missing
title/watermark fields raise ``MEGIS-DRW-002``, and ``qa_all_passed`` is the
explicit release gate (a recorded fail blocks release without invalidating the
artifact).
"""

from __future__ import annotations

import copy
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from megis.errors import ERROR_CODES, MegisError, verify_error_codes
from megis.package import (
    DEFAULT_WHITELIST,
    NOT_FOR_MANUFACTURING,
    WATERMARK,
    build_draft_drawing,
    qa_all_passed,
    validate_drawing_schema,
    verify_draft_drawing,
)

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "contracts" / "g5" / "golden" / "drawing-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "drawing-corpus.schema.json"
REFERENCE_FIXTURE_PATH = ROOT / "contracts" / "g1" / "golden" / "reference-fixture.json"


def _load_ir() -> dict:
    return json.loads(REFERENCE_FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def drawing_corpus() -> dict:
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def drawing_corpus_schema() -> dict:
    return json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))


def _dial_ir(ir: dict, dial: dict | None) -> tuple[dict, dict]:
    """Apply an IR-side dial and return (ir, build_kwargs)."""
    kwargs: dict = {}
    if dial is None:
        return ir, kwargs
    action = dial["action"]
    if action == "whitelist_subset":
        kwargs["dimension_whitelist"] = dial["dim_ids"]
    elif action == "reverse_components":
        ir["components"] = list(reversed(ir["components"]))
    elif action == "unknown_whitelist":
        kwargs["dimension_whitelist"] = list(DEFAULT_WHITELIST) + [dial["id"]]
    return ir, kwargs


def _dial_doc(doc: dict, dial: dict) -> dict:
    action = dial["action"]
    if action == "tamper_svg":
        doc["svg"] = "Z" + doc["svg"][1:]
    elif action == "drift_dimension":
        for entry in doc["dimensions"]:
            if entry["id"] == dial["id"]:
                entry["present"] = True
                entry["nominal"] = dial["nominal"]
    elif action == "remove_watermark":
        doc["svg"] = doc["svg"].replace(WATERMARK, "")
    elif action == "remove_not_for_manufacturing":
        doc["svg"] = doc["svg"].replace(NOT_FOR_MANUFACTURING, "")
    elif action == "drop_title_field":
        doc["title_block"].pop(dial["id"], None)
    elif action == "qa_status_drift":
        for row in doc["qa"]:
            if row["id"] == dial["id"]:
                row["status"] = dial["status"]
    elif action == "set_doc_revision":
        doc["revision"] = dial["revision"]
    return doc


def _run_case(case: dict) -> tuple[str | None, bool, bool | None]:
    ir, kwargs = _dial_ir(copy.deepcopy(_load_ir()), case["dial"])
    try:
        doc = build_draft_drawing(ir, **kwargs)
        if case["dial"] is not None:
            doc = _dial_doc(doc, case["dial"])
        ledger = verify_draft_drawing(doc, ir)
    except MegisError as error:
        return error.error_object.code, False, None
    return None, bool(ledger.get("valid")), qa_all_passed(doc)


def test_drawing_schema_is_stable() -> None:
    validate_drawing_schema()


def test_corpus_validates_against_schema(
    drawing_corpus: dict, drawing_corpus_schema: dict
) -> None:
    Draft202012Validator.check_schema(drawing_corpus_schema)
    errors = list(
        Draft202012Validator(drawing_corpus_schema).iter_errors(drawing_corpus)
    )
    assert errors == []
    assert len(drawing_corpus["cases"]) >= 12


def test_error_codes_registered_and_unique() -> None:
    for code in {"MEGIS-DRW-001", "MEGIS-DRW-002"}:
        assert code in ERROR_CODES
    assert verify_error_codes() == []


def test_build_from_reference_fixture_is_well_formed() -> None:
    doc = build_draft_drawing(_load_ir())
    assert doc["documentType"] == "DRAFT_DRAWING"
    assert doc["classification"] == "DESIGN_RUN"
    assert doc["design_id"] == "FIXTURE-REFERENCE-001"
    assert doc["revision"] == "A"
    assert doc["title_block"] == {
        "design_id": "FIXTURE-REFERENCE-001",
        "revision": "A",
        "material": "AA 6061",
        "general_tolerance": "+/-0.1 mm",
        "unit": "mm",
        "projection": "top view",
    }
    assert doc["watermark"] == WATERMARK
    assert doc["not_for_manufacturing"] == NOT_FOR_MANUFACTURING


def test_svg_is_well_formed_xml_with_watermark() -> None:
    doc = build_draft_drawing(_load_ir())
    root = ET.fromstring(doc["svg"])
    assert root.tag.endswith("svg")
    assert WATERMARK in doc["svg"]
    assert NOT_FOR_MANUFACTURING in doc["svg"]
    assert doc["svg"].startswith('<?xml version="1.0" encoding="UTF-8"?>')


def test_build_is_deterministic_without_timestamps() -> None:
    first = build_draft_drawing(_load_ir())
    second = build_draft_drawing(_load_ir())
    assert first == second
    assert first["svg"] == second["svg"]
    assert first["svgSemanticFingerprint"] == second["svgSemanticFingerprint"]


def test_whitelist_dimension_values_are_pinned_from_ir() -> None:
    doc = build_draft_drawing(_load_ir())
    by_id = {entry["id"]: entry for entry in doc["dimensions"]}
    assert by_id["DIM-FIXTURE-WIDTH"]["nominal"] == 120.0
    assert by_id["DIM-FIXTURE-DEPTH"]["nominal"] == 80.0
    assert by_id["DIM-FIXTURE-HEIGHT"]["nominal"] == 20.0
    for dim in (list(by_id.values())[0],):
        assert dim["unit"] == "mm"


def test_qa_all_passed_by_default() -> None:
    doc = build_draft_drawing(_load_ir())
    assert qa_all_passed(doc) is True
    ledger = verify_draft_drawing(doc, _load_ir())
    assert ledger["valid"] is True
    assert ledger["qaAllPassed"] is True
    assert ledger["whitelistDimensions"] == len(DEFAULT_WHITELIST)
    assert ledger["svgFingerprintMatched"] is True


def test_unknown_whitelist_records_fail_but_artifact_is_valid() -> None:
    doc = build_draft_drawing(_load_ir(), dimension_whitelist=list(DEFAULT_WHITELIST) + ["DIM-NOPE"])
    assert qa_all_passed(doc) is False
    assert any(row["id"] == "whitelist:DIM-NOPE" for row in doc["qa"])
    ledger = verify_draft_drawing(doc, _load_ir())
    assert ledger["valid"] is True
    assert ledger["qaAllPassed"] is False


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
def test_every_corpus_case_matches_golden(case: dict) -> None:
    code, valid, qa_pass = _run_case(case)
    expect = case["expect"]
    if not expect["valid"]:
        assert valid is False, case["case_id"]
        assert code == expect["error_code"], case["case_id"]
        return
    assert valid is True, case["case_id"]
    assert code is None, case["case_id"]
    if expect["qa_pass"] is not None:
        assert qa_pass is expect["qa_pass"], case["case_id"]
