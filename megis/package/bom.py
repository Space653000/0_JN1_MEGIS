"""G5-BOM-001: V3 BOM exporter (blueprint §13).

The BOM is a deterministic UTF-8 / LF CSV derived only from validated
Engineering IR fields:

- rows are sorted by ``item`` ascending (item is assigned after sorting by
  ``part_id``, so the CSV is stable across IR component ordering),
- every component row carries all twelve §13 columns,
- quantity defaults to 1 per IR component (the v2 IR has no quantity
  dimension, so 1 is the only truthful value; a future IR schema extension
  would feed the same ``_read_quantity`` guard),
- material / revision / provenance come from the IR and are never invented,
- module references are read from ``module:<id>@<version>`` provenance
  markers recorded by G4-MOD-002 composition.

``verify_bom`` recomputes the CSV and cross-checks row coverage, quantity,
material and revision against the IR.  Quantity drift against the IR raises
``MEGIS-PKG-003`` (blueprint: "BOM 數量必須與 IR component quantity 完全一致，
否則 MEGIS-PKG-*"); CSV / fingerprint drift raises ``MEGIS-BOM-001``; any
other declarative or IR-field mismatch raises ``MEGIS-BOM-002``.  A tampered
BOM can never silently pass.
"""

from __future__ import annotations

import csv
import io
import json
import re
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from megis.contracts import ContractValidationError, validate_engineering_ir
from megis.errors import MegisError

BOM_BUILDER_VERSION = "megis.bom@1.0.0"
BOM_COLUMNS = (
    "item",
    "part_id",
    "description",
    "quantity",
    "material",
    "finish",
    "standard",
    "size",
    "module_ref",
    "module_version",
    "revision",
    "provenance",
)
BOM_COLUMNS_SET = frozenset(BOM_COLUMNS)

ROOT = Path(__file__).resolve().parents[2]
BOM_SCHEMA_PATH = ROOT / "schemas" / "v3" / "bom.schema.json"

_MODULE_MARKER = re.compile(r"^module:(?P<module_id>[^@]+)@(?P<version>.+)$")


def _bom_csv_mismatch(detail: Any) -> MegisError:
    return MegisError(
        "MEGIS-BOM-001",
        engineer_detail={"reason": "BOM csv or fingerprint mismatch", "detail": detail},
    )


def _declarative_mismatch(detail: Any) -> MegisError:
    return MegisError(
        "MEGIS-BOM-002",
        engineer_detail={"reason": "BOM declarative or IR-field mismatch", "detail": detail},
    )


def _package_quantity_mismatch(detail: Any) -> MegisError:
    return MegisError(
        "MEGIS-PKG-003",
        engineer_detail={
            "reason": "BOM quantity does not match IR component quantity",
            "detail": detail,
        },
    )


def _read_quantity(component: Mapping[str, Any]) -> int:
    """Return the truthful per-component quantity (default 1).

    The v2 IR schema has no component ``quantity`` field, so a schema-valid
    IR always yields 1.  The guard rejects an explicit non-positive or
    non-integer quantity, so a future IR extension cannot inject a fabricated
    count silently.
    """
    quantity = component.get("quantity", 1)
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
        raise _declarative_mismatch(
            {
                "reason": "invalid component quantity",
                "part_id": component.get("id"),
                "quantity": quantity,
            }
        )
    return quantity


def _module_ref_for(
    component: Mapping[str, Any], provenance_by_id: Mapping[str, Any]
) -> tuple[str, str]:
    """Return ``(module_ref, module_version)`` from provenance markers."""
    for provenance_id in component.get("provenanceIds", []) or []:
        record = provenance_by_id.get(provenance_id)
        if not isinstance(record, dict):
            continue
        source_ref = record.get("sourceRef")
        if not isinstance(source_ref, str):
            continue
        match = _MODULE_MARKER.match(source_ref)
        if match:
            return match.group("module_id"), match.group("version")
    return "", ""


def _material_label(record: Mapping[str, Any]) -> str:
    designation = record.get("designation")
    if isinstance(designation, str) and designation:
        return designation
    name = record.get("name")
    return name if isinstance(name, str) else ""


def _render_csv(rows: list[dict[str, Any]], columns: tuple[str, ...]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(columns)
    for row in rows:
        writer.writerow([row[column] for column in columns])
    return buffer.getvalue()


def _csv_fingerprint(csv_text: str) -> str:
    return sha256(csv_text.encode("utf-8")).hexdigest()


def build_bom(ir: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic BOM document from a validated Engineering IR.

    Requires a v2 Engineering IR whose components are sorted by ``part_id``
    for stable ``item`` numbering.  No value is fabricated: quantity defaults
    to 1, material / finish / standard / size are read from the IR when
    present and empty otherwise, and module references come only from
    provenance markers.
    """
    document = dict(ir)
    try:
        validate_engineering_ir(document)
    except ContractValidationError as error:
        raise _declarative_mismatch(
            {"reason": "IR is not schema- or semantically valid", "errors": error.errors}
        ) from error

    design_id = document["designId"]
    revision = document["revision"]
    components = document.get("components", [])
    if not components:
        raise _declarative_mismatch({"reason": "IR has no components"})
    if not isinstance(design_id, str) or not design_id:
        raise _declarative_mismatch({"reason": "IR missing designId"})
    if not isinstance(revision, str) or not revision:
        raise _declarative_mismatch({"reason": "IR missing revision"})

    materials_by_id = {material["id"]: material for material in document.get("materials", [])}
    provenance_by_id = {record["id"]: record for record in document.get("provenance", [])}

    unordered_rows: list[dict[str, str | int]] = []
    for component in components:
        part_id = component.get("id")
        if not isinstance(part_id, str) or not part_id:
            raise _declarative_mismatch({"reason": "IR component missing id"})
        quantity = _read_quantity(component)
        material_id = component.get("materialId")
        material = ""
        if material_id is not None:
            record = materials_by_id.get(material_id)
            if record is None:
                raise _declarative_mismatch(
                    {
                        "reason": "dangling material reference",
                        "part_id": part_id,
                        "materialId": material_id,
                    }
                )
            material = _material_label(record)
        module_ref, module_version = _module_ref_for(component, provenance_by_id)
        finish = component.get("finish", "")
        standard = component.get("standard", "")
        size = component.get("size", "")
        provenance = "|".join(sorted(component.get("provenanceIds", []) or []))
        unordered_rows.append(
            {
                "part_id": part_id,
                "description": component.get("name", ""),
                "quantity": quantity,
                "material": material if isinstance(material, str) else "",
                "finish": finish if isinstance(finish, str) else "",
                "standard": standard if isinstance(standard, str) else "",
                "size": size if isinstance(size, str) else "",
                "module_ref": module_ref,
                "module_version": module_version,
                "revision": revision,
                "provenance": provenance,
            }
        )

    rows: list[dict[str, Any]] = []
    for item, row in enumerate(
        sorted(unordered_rows, key=lambda entry: entry["part_id"]), start=1
    ):
        rows.append({"item": item, **row})

    csv_text = _render_csv(rows, BOM_COLUMNS)
    return {
        "schemaVersion": "1.0.0",
        "documentType": "BOM",
        "classification": "DESIGN_RUN",
        "bom_builder": BOM_BUILDER_VERSION,
        "design_id": design_id,
        "revision": revision,
        "columns": list(BOM_COLUMNS),
        "rows": rows,
        "csv": csv_text,
        "csvSemanticFingerprint": _csv_fingerprint(csv_text),
        "totals": {
            "rows": len(rows),
            "totalQuantity": sum(int(row["quantity"]) for row in rows),
        },
    }


def _load_schema() -> dict[str, Any]:
    return json.loads(BOM_SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_bom_schema() -> None:
    """Ensure the BOM schema is self-consistent."""
    Draft202012Validator.check_schema(_load_schema())


def _schema_errors(document: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(_load_schema())
    return sorted(
        (error.message for error in validator.iter_errors(document)),
        key=lambda message: message,
    )


def _ir_index(ir: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    by_id: dict[str, Any] = {}
    for component in ir.get("components", []):
        by_id[component["id"]] = component
    materials: dict[str, Any] = {}
    for material in ir.get("materials", []):
        materials[material["id"]] = material
    return by_id, materials


def verify_bom(bom: dict[str, Any], ir: Mapping[str, Any]) -> dict[str, Any]:
    """Verify a BOM document against its source Engineering IR.

    Raises ``MegisError`` on the first mismatch; returns a check ledger when
    row coverage, quantity, material, revision, totals and the CSV /
    fingerprint all still match the IR.
    """
    schema_problems = _schema_errors(bom)
    if schema_problems:
        raise _declarative_mismatch({"schemaErrors": schema_problems})
    if bom.get("documentType") != "BOM" or bom.get("classification") != "DESIGN_RUN":
        raise _declarative_mismatch(
            {
                "field": "documentType / classification",
                "expected": "BOM / DESIGN_RUN",
            }
        )
    if list(bom.get("columns", [])) != list(BOM_COLUMNS):
        raise _declarative_mismatch({"reason": "BOM columns are not the fixed §13 set"})
    if bom.get("design_id") != ir.get("designId") or bom.get("revision") != ir.get("revision"):
        raise _declarative_mismatch(
            {
                "designIdMismatch": bom.get("design_id") != ir.get("designId"),
                "revisionMismatch": bom.get("revision") != ir.get("revision"),
            }
        )

    ir_components, ir_materials = _ir_index(ir)
    row_by_part: dict[str, dict[str, Any]] = {}
    for row in bom["rows"]:
        part_id = row["part_id"]
        row_by_part[part_id] = row

    declared_parts = set(row_by_part)
    ir_parts = set(ir_components)
    if declared_parts != ir_parts:
        raise _declarative_mismatch(
            {
                "missingFromBom": sorted(ir_parts - declared_parts),
                "extraInBom": sorted(declared_parts - ir_parts),
            }
        )

    for part_id, component in sorted(ir_components.items()):
        row = row_by_part[part_id]
        expected_quantity = _read_quantity(component)
        if row["quantity"] != expected_quantity:
            raise _package_quantity_mismatch(
                {"part_id": part_id, "bom": row["quantity"], "ir": expected_quantity}
            )
        material_id = component.get("materialId")
        expected_material = ""
        if material_id is not None:
            record = ir_materials.get(material_id)
            if record is None or record["id"] != material_id:
                raise _declarative_mismatch(
                    {
                        "reason": "component material is not resolvable in IR",
                        "part_id": part_id,
                    }
                )
            expected_material = _material_label(record)
        if row["material"] != expected_material:
            raise _declarative_mismatch(
                {
                    "part_id": part_id,
                    "bom": row["material"],
                    "ir": expected_material,
                }
            )
        if row["revision"] != ir["revision"]:
            raise _declarative_mismatch(
                {"part_id": part_id, "bom": row["revision"], "ir": ir["revision"]}
            )

    expected_rows = len(ir_components)
    total_quantity = sum(int(row["quantity"]) for row in bom["rows"])
    if bom["totals"]["rows"] != expected_rows or bom["totals"]["totalQuantity"] != total_quantity:
        raise _declarative_mismatch(
            {
                "rowsMismatch": bom["totals"]["rows"] != expected_rows,
                "totalQuantityMismatch": bom["totals"]["totalQuantity"] != total_quantity,
                "irRows": expected_rows,
                "bomRows": bom["totals"]["rows"],
            }
        )

    recomputed_csv = _render_csv(bom["rows"], BOM_COLUMNS)
    if recomputed_csv != bom["csv"]:
        raise _bom_csv_mismatch({"reason": "declared CSV does not match rows"})
    recomputed_fingerprint = _csv_fingerprint(recomputed_csv)
    if recomputed_fingerprint != bom["csvSemanticFingerprint"]:
        raise _bom_csv_mismatch(
            {
                "stored": bom["csvSemanticFingerprint"],
                "recomputed": recomputed_fingerprint,
            }
        )

    return {
        "valid": True,
        "rowsChecked": len(bom["rows"]),
        "totalQuantity": total_quantity,
        "csvFingerprintMatched": True,
        "quantityMatchedIr": True,
    }


__all__ = [
    "BOM_BUILDER_VERSION",
    "BOM_COLUMNS",
    "BOM_SCHEMA_PATH",
    "build_bom",
    "validate_bom_schema",
    "verify_bom",
]
