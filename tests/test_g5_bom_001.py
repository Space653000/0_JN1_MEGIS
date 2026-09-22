"""G5-BOM-001 BOM exporter tests (E3).

``build_bom`` turns a validated Engineering IR into a deterministic UTF-8 /
LF CSV BOM (twelve §13 columns, rows sorted by ``item`` ascending, quantity
defaults to 1 per IR component), then ``verify_bom`` recomputes the CSV and
cross-checks row coverage, quantity, material and revision against the IR.
The corpus pins the contract: valid IRs pass, and any tampered row quantity
(``MEGIS-PKG-003``), row drift or invalid IR field (``MEGIS-BOM-002``), or CSV
tampering (``MEGIS-BOM-001``) must fail with the structured code.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from megis.errors import ERROR_CODES, MegisError, verify_error_codes
from megis.package import (
    BOM_COLUMNS,
    build_bom,
    validate_bom_schema,
    verify_bom,
)
from megis.package.bom import _read_quantity

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "contracts" / "g5" / "golden" / "bom-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "bom-corpus.schema.json"
REFERENCE_FIXTURE_PATH = ROOT / "contracts" / "g1" / "golden" / "reference-fixture.json"


def _load_ir() -> dict:
    return json.loads(REFERENCE_FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def bom_corpus() -> dict:
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def bom_corpus_schema() -> dict:
    return json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))


def _apply_ir_dial(ir: dict, dial: dict | None) -> dict:
    if dial is None:
        return ir
    action = dial["action"]
    if action == "add_module_provenance":
        part_id = dial["part_id"]
        provenance_id = f"PROV-MOD-{part_id}"
        for component in ir["components"]:
            if component["id"] == part_id:
                component.setdefault("provenanceIds", []).append(provenance_id)
        ir["provenance"].append(
            {
                "id": provenance_id,
                "subjectId": part_id,
                "field": f"/components/{part_id}",
                "source": "derived",
                "sourceRef": f"module:{dial['module_id']}@{dial['version']}",
                "recordedAt": "2026-09-22T00:00:00Z",
            }
        )
    elif action == "reverse_components":
        ir["components"] = list(reversed(ir["components"]))
    elif action == "set_ir_material_id":
        for component in ir["components"]:
            if component["id"] == dial["part_id"]:
                component["materialId"] = dial["material_id"]
    return ir


def _apply_bom_dial(bom: dict, dial: dict) -> dict:
    action = dial["action"]
    if action == "tamper_row_quantity":
        for row in bom["rows"]:
            if row["part_id"] == dial["part_id"]:
                row["quantity"] = dial["quantity"]
    elif action == "drop_row":
        bom["rows"] = [row for row in bom["rows"] if row["part_id"] != dial["part_id"]]
    elif action == "add_row":
        bom["rows"].append(
            {
                "item": len(bom["rows"]) + 1,
                "part_id": dial["part_id"],
                "description": "unknown extra part",
                "quantity": 1,
                "material": "",
                "finish": "",
                "standard": "",
                "size": "",
                "module_ref": "",
                "module_version": "",
                "revision": bom["revision"],
                "provenance": "",
            }
        )
    elif action == "tamper_csv":
        bom["csv"] = "I" + bom["csv"][1:]
    elif action == "set_bom_revision":
        bom["revision"] = dial["revision"]
    elif action == "set_row_material":
        for row in bom["rows"]:
            if row["part_id"] == dial["part_id"]:
                row["material"] = dial["material"]
    return bom


def _run_case(case: dict) -> tuple[str, bool, str | None]:
    ir = _apply_ir_dial(copy.deepcopy(_load_ir()), case["dial"])
    try:
        bom = build_bom(ir)
        if case["dial"] is not None:
            bom = _apply_bom_dial(bom, case["dial"])
        ledger = verify_bom(bom, ir)
    except MegisError as error:
        return False, False, error.error_object.code
    return True, bool(ledger.get("valid")), None


def test_bom_schema_is_stable() -> None:
    validate_bom_schema()


def test_corpus_validates_against_schema(
    bom_corpus: dict, bom_corpus_schema: dict
) -> None:
    Draft202012Validator.check_schema(bom_corpus_schema)
    errors = list(
        Draft202012Validator(bom_corpus_schema).iter_errors(bom_corpus)
    )
    assert errors == []
    assert len(bom_corpus["cases"]) >= 12


def test_error_codes_registered_and_unique() -> None:
    for code in {"MEGIS-PKG-003", "MEGIS-BOM-001", "MEGIS-BOM-002"}:
        assert code in ERROR_CODES
    assert verify_error_codes() == []


def test_build_from_reference_fixture_is_well_formed() -> None:
    bom = build_bom(_load_ir())
    assert bom["documentType"] == "BOM"
    assert bom["classification"] == "DESIGN_RUN"
    assert bom["design_id"] == "FIXTURE-REFERENCE-001"
    assert bom["revision"] == "A"
    assert list(bom["columns"]) == list(BOM_COLUMNS)
    assert len(bom["rows"]) == 3
    assert bom["totals"] == {"rows": 3, "totalQuantity": 3}


def test_rows_sorted_by_item_ascending() -> None:
    bom = build_bom(_load_ir())
    item_numbers = [row["item"] for row in bom["rows"]]
    assert item_numbers == sorted(item_numbers)
    part_ids = [row["part_id"] for row in bom["rows"]]
    assert part_ids == sorted(part_ids)
    assert part_ids == ["COMP-FIXTURE-BASE", "COMP-FIXTURE-COVER", "COMP-FIXTURE-PCB"]


def test_csv_is_utf8_lf_with_header() -> None:
    bom = build_bom(_load_ir())
    assert bom["csv"].startswith("item,part_id,description,quantity,material,")
    assert "\r\n" not in bom["csv"]
    csv_lines = bom["csv"].split("\n")
    assert csv_lines[0].split(",") == list(BOM_COLUMNS)
    assert len(csv_lines) == 5  # header + 3 rows + empty tail after final LF
    assert csv_lines[-1] == ""


def test_build_is_deterministic() -> None:
    first = build_bom(_load_ir())
    second = build_bom(_load_ir())
    assert first == second
    assert first["csvSemanticFingerprint"] == second["csvSemanticFingerprint"]


def test_material_lookup_from_ir_is_truthful() -> None:
    bom = build_bom(_load_ir())
    by_part = {row["part_id"]: row for row in bom["rows"]}
    assert by_part["COMP-FIXTURE-BASE"]["material"] == "AA 6061"
    assert by_part["COMP-FIXTURE-COVER"]["material"] == "AA 6061"
    # PCB has no materialId in the IR; the BOM must never invent one.
    assert by_part["COMP-FIXTURE-PCB"]["material"] == ""


def test_module_provenance_is_carried_into_rows() -> None:
    ir = _apply_ir_dial(
        copy.deepcopy(_load_ir()),
        {
            "action": "add_module_provenance",
            "part_id": "COMP-FIXTURE-PCB",
            "module_id": "mod.pcb",
            "version": "1.2.0",
        },
    )
    bom = build_bom(ir)
    pcb = next(row for row in bom["rows"] if row["part_id"] == "COMP-FIXTURE-PCB")
    assert pcb["module_ref"] == "mod.pcb"
    assert pcb["module_version"] == "1.2.0"
    base = next(row for row in bom["rows"] if row["part_id"] == "COMP-FIXTURE-BASE")
    assert base["module_ref"] == ""


def test_quantity_defaults_to_one_per_component() -> None:
    bom = build_bom(_load_ir())
    for row in bom["rows"]:
        assert row["quantity"] == 1


def test_quantity_guard_rejects_fabricated_or_invalid_counts() -> None:
    for bad in (0, -1, 2.5, True, "two"):
        with pytest.raises(MegisError) as raised:
            _read_quantity({"id": "C", "quantity": bad})
        assert raised.value.error_object.code == "MEGIS-BOM-002"
    assert _read_quantity({"id": "C"}) == 1
    assert _read_quantity({"id": "C", "quantity": 1}) == 1
    assert _read_quantity({"id": "C", "quantity": 120}) == 120


def test_verify_valid_returns_check_ledger() -> None:
    ir = _load_ir()
    bom = build_bom(ir)
    ledger = verify_bom(bom, ir)
    assert ledger["valid"] is True
    assert ledger["rowsChecked"] == 3
    assert ledger["totalQuantity"] == 3
    assert ledger["quantityMatchedIr"] is True
    assert ledger["csvFingerprintMatched"] is True


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
    _, valid, code = _run_case(case)
    expect = case["expect"]
    if not expect["valid"]:
        assert valid is False, case["case_id"]
        assert code == expect["error_code"], case["case_id"]
        return
    assert valid is True, case["case_id"]
    assert code is None, case["case_id"]


def test_extra_row_and_unknown_part_id_rejected() -> None:
    ir = _load_ir()
    bom = build_bom(ir)
    with pytest.raises(MegisError) as raised:
        verify_bom(_apply_bom_dial(bom, {"action": "add_row", "part_id": "COMP-NOPE"}), ir)
    assert raised.value.error_object.code == "MEGIS-BOM-002"
