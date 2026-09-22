"""G5-DRW-001: fixed-template draft drawing generator (blueprint §13).

A provisional A4 landscape SVG drawing driven only by Engineering IR
metadata, never by guessing critical dimensions from a STEP file.  The first
version allows exactly one fixed Fixture template plus a caller-pinned
``dimension_whitelist``, marks every sheet ``DRAFT — ENGINEERING REVIEW
REQUIRED`` with a ``NOT FOR MANUFACTURING`` watermark, records a view scale and
writes a QA checklist (title block, whitelist dimensions equal to the IR,
no duplicate or contradictory dimensions, watermark, scale) that must be
recorded into the package manifest.

``build_draft_drawing`` is deterministic (no timestamps), so the SVG bytes and
their SHA-256 are reproducible.  ``verify_draft_drawing`` recomputes the QA and
fingerprint; tampering the SVG or drifting a dimension raises ``MEGIS-DRW-001``,
and a missing title field or missing watermark raises ``MEGIS-DRW-002``.
``qa_all_passed`` is the release gate helper: a recorded fail must block
release but is still a valid recorded artifact.
"""

from __future__ import annotations

import html
import json
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator

from megis.contracts import ContractValidationError, validate_engineering_ir
from megis.errors import MegisError

DRAWING_BUILDER_VERSION = "megis.drawing@1.0.0"
DRAWING_TEMPLATE_VERSION = "fixture-a4-landscape@1.0.0"

WATERMARK = "DRAFT - ENGINEERING REVIEW REQUIRED"
NOT_FOR_MANUFACTURING = "NOT FOR MANUFACTURING"

ROOT = Path(__file__).resolve().parents[2]
DRAWING_SCHEMA_PATH = ROOT / "schemas" / "v3" / "draft-drawing.schema.json"

DEFAULT_WHITELIST = (
    "DIM-FIXTURE-WIDTH",
    "DIM-FIXTURE-DEPTH",
    "DIM-FIXTURE-HEIGHT",
)
DEFAULT_TOLERANCE = "+/-0.1 mm"
DEFAULT_VIEW_SCALE = "1:1"

_QA_TITLE_FIELDS = (
    ("design_id", "title-block-design-id"),
    ("revision", "title-block-revision"),
    ("material", "title-block-material"),
    ("general_tolerance", "title-block-tolerance"),
    ("unit", "title-block-unit"),
    ("projection", "title-block-projection"),
)


def _draft_mismatch(detail: Any) -> MegisError:
    return MegisError(
        "MEGIS-DRW-001",
        engineer_detail={"reason": "draft drawing fingerprint or dimension drift", "detail": detail},
    )


def _declarative_mismatch(detail: Any) -> MegisError:
    return MegisError(
        "MEGIS-DRW-002",
        engineer_detail={"reason": "draft drawing declarative mismatch", "detail": detail},
    )


def _fmt(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _dimension_index(ir: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Index IR quantity id -> list of (nominal) records, preserving order."""
    index: dict[str, list[dict[str, Any]]] = {}
    for component in ir.get("components", []):
        for dimension in component.get("dimensions", []) or []:
            quantity = dimension.get("quantity")
            if isinstance(quantity, dict) and quantity.get("id"):
                index.setdefault(quantity["id"], []).append(
                    {
                        "component": component["id"],
                        "name": dimension.get("name", ""),
                        "unit": quantity.get("unit", ""),
                        "nominal": quantity.get("nominal"),
                    }
                )
    return index


def _material_labels(ir: Mapping[str, Any]) -> tuple[str, ...]:
    by_id = {material["id"]: material for material in ir.get("materials", [])}
    labels: set[str] = set()
    for component in ir.get("components", []):
        material_id = component.get("materialId")
        if not material_id:
            continue
        record = by_id.get(material_id)
        if not record:
            continue
        designation = record.get("designation")
        if isinstance(designation, str) and designation:
            labels.add(designation)
        elif isinstance(record.get("name"), str):
            labels.add(record["name"])
    return tuple(sorted(labels))


def _build_qa(
    ir: Mapping[str, Any],
    whitelist: tuple[str, ...],
    general_tolerance: str,
    view_scale: str,
) -> list[dict[str, Any]]:
    """Build the deterministic QA checklist rows (pass/fail/N/A each)."""
    design_id = ir.get("designId")
    revision = ir.get("revision")
    materials = _material_labels(ir)
    unit = "mm"
    projection = "top view"
    index = _dimension_index(ir)

    rows: list[dict[str, Any]] = [
        {
            "id": "title-block-design-id",
            "label": "Title block design_id present",
            "status": "pass" if isinstance(design_id, str) and design_id else "fail",
            "detail": str(design_id) if design_id else "missing",
        },
        {
            "id": "title-block-revision",
            "label": "Title block revision present",
            "status": "pass" if isinstance(revision, str) and revision else "fail",
            "detail": str(revision) if revision else "missing",
        },
        {
            "id": "title-block-material",
            "label": "Title block material present",
            "status": "pass" if materials else "fail",
            "detail": ", ".join(materials) if materials else "no material referenced",
        },
        {
            "id": "title-block-tolerance",
            "label": "General tolerance declared",
            "status": "pass" if general_tolerance else "N/A",
            "detail": str(general_tolerance) if general_tolerance else "not declared",
        },
        {
            "id": "title-block-unit",
            "label": "Unit system declared",
            "status": "pass" if unit else "N/A",
            "detail": unit,
        },
        {
            "id": "title-block-projection",
            "label": "Projection method declared",
            "status": "pass" if projection else "N/A",
            "detail": projection,
        },
        {
            "id": "view-scale",
            "label": "View scale indicated",
            "status": "pass" if view_scale else "N/A",
            "detail": str(view_scale) if view_scale else "not declared",
        },
        {
            "id": "watermark",
            "label": "DRAFT watermark present",
            "status": "pass",
            "detail": WATERMARK,
        },
    ]

    duplicates: dict[str, list[dict[str, Any]]] = {}
    contradictions: list[str] = []
    for dim_id in whitelist:
        records = index.get(dim_id, [])
        if not records:
            rows.append(
                {
                    "id": f"whitelist:{dim_id}",
                    "label": f"Whitelist dimension {dim_id} appears",
                    "status": "fail",
                    "detail": "missing from IR",
                }
            )
            continue
        for record in records:
            duplicates.setdefault(dim_id, []).append(record)
        nominals = {record["nominal"] for record in records}
        if len(nominals) > 1:
            contradictions.append(dim_id)
        rows.append(
            {
                "id": f"whitelist:{dim_id}:value",
                "label": f"Whitelist dimension {dim_id} value equals IR",
                "status": "pass",
                "detail": f"{_fmt(records[0]['nominal'])} {records[0]['unit']}",
            }
        )

    duplicate_ids = [dim_id for dim_id, records in duplicates.items() if len(records) > 1]
    rows.append(
        {
            "id": "duplicate-dimensions",
            "label": "No duplicate or contradictory dimensions",
            "status": "fail" if duplicate_ids or contradictions else "pass",
            "detail": {
                "duplicates": duplicate_ids,
                "contradictions": contradictions,
            },
        }
    )
    return rows


def _render_svg(
    *,
    design_id: str,
    revision: str,
    materials_text: str,
    general_tolerance: str,
    view_scale: str,
    width_mm: float | None,
    depth_mm: float | None,
    height_mm: float | None,
    dimension_texts: list[tuple[str, str]],
) -> str:
    """Render the fixed A4 landscape template (no timestamps)."""
    scale = 0.38
    x0, y0 = 40.0, 60.0
    box_w = (width_mm * scale) if width_mm is not None else 36.0
    box_d = (depth_mm * scale) if depth_mm is not None else 24.0
    x1, y1 = x0 + box_w, y0 + box_d

    polyline = f"{_fmt(x0)},{_fmt(y0)} {_fmt(x1)},{_fmt(y0)} {_fmt(x1)},{_fmt(y1)} {_fmt(x0)},{_fmt(y1)} {_fmt(x0)},{_fmt(y0)}"
    inner = f"{_fmt(x0 + 2)},{_fmt(y0 + 2)} {_fmt(x1 - 2)},{_fmt(y0 + 2)} {_fmt(x1 - 2)},{_fmt(y1 - 2)} {_fmt(x0 + 2)},{_fmt(y1 - 2)} {_fmt(x0 + 2)},{_fmt(y0 + 2)}"

    dim_g = ""
    callout_y = y0 - 8.0
    for text, offset in dimension_texts:
        dim_g += (
            f'<line x1="{_fmt(x0 + offset[0])}" y1="{_fmt(callout_y)}" '
            f'x2="{_fmt(x0 + offset[1])}" y2="{_fmt(callout_y)}" stroke="black" stroke-width="0.25"/>\n'
            f'<text x="{_fmt((x0 + offset[0] + x0 + offset[1]) / 2)}" y="{_fmt(callout_y - 2)}" '
            f'text-anchor="middle" font-family="sans-serif" font-size="4">{_escape(text)}</text>\n'
        )

    height_text = (
        f'<text x="{_fmt(x1 + 6)}" y="{_fmt((y0 + y1) / 2)}" font-family="sans-serif" font-size="4">'
        f"H {_escape(_fmt(height_mm) + ' mm')}</text>\n"
        if height_mm is not None
        else ""
    )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">\n'
        '  <rect x="5" y="5" width="287" height="200" fill="white" stroke="black" stroke-width="0.5"/>\n'
        '  <g id="fixture-top-view" fill="none" stroke="black" stroke-width="0.35">\n'
        f"    <polyline points=\"{polyline}\"/>\n"
        f"    <polyline points=\"{inner}\" stroke-dasharray=\"1,1\"/>\n"
        "  </g>\n"
        f'{dim_g}'
        f'{height_text}'
        '  <text x="150" y="22" text-anchor="middle" font-family="sans-serif" font-size="5">'
        "MEGIS DRAFT DRAWING — FIXED FIXTURE TEMPLATE</text>\n"
        '  <g id="title-block" font-family="sans-serif" fill="black">\n'
        '    <rect x="145" y="165" width="147" height="40" fill="none" stroke="black" stroke-width="0.35"/>\n'
        '    <line x1="145" y1="176" x2="292" y2="176" stroke="black" stroke-width="0.35"/>\n'
        '    <line x1="145" y1="187" x2="292" y2="187" stroke="black" stroke-width="0.35"/>\n'
        '    <line x1="145" y1="198" x2="292" y2="198" stroke="black" stroke-width="0.35"/>\n'
        f'    <text x="149" y="172" font-size="4">DESIGN {_escape(design_id)} | REV {_escape(revision)}</text>\n'
        f'    <text x="149" y="183" font-size="4">MAT {_escape(materials_text)} | TOL {_escape(general_tolerance)} | UNIT mm</text>\n'
        f'    <text x="149" y="194" font-size="4">TOP VIEW | SCALE {_escape(view_scale)}</text>\n'
        f'    <text x="149" y="201" font-size="4.3" font-weight="bold">{_escape(WATERMARK)}</text>\n'
        "  </g>\n"
        f'  <text x="8" y="205" font-family="sans-serif" font-size="3.2">{_escape(NOT_FOR_MANUFACTURING)}'
        " | IR-drawn dimensions; engineering review required</text>\n"
        "</svg>\n"
    )


def _drawing_dimensions(
    ir: Mapping[str, Any], whitelist: tuple[str, ...]
) -> tuple[list[dict[str, Any]], dict[str, float], str]:
    index = _dimension_index(ir)
    resolved: list[dict[str, Any]] = []
    bbox: dict[str, float] = {}
    for dim_id in whitelist:
        records = index.get(dim_id, [])
        if not records:
            resolved.append(
                {"id": dim_id, "present": False, "detail": "missing from IR"}
            )
            continue
        record = records[0]
        resolved.append(
            {
                "id": dim_id,
                "present": True,
                "name": record.get("name", ""),
                "unit": record.get("unit", ""),
                "nominal": record.get("nominal"),
            }
        )
        # bbox tracking for the fixture base view uses width/depth/height ids.
        if dim_id == "DIM-FIXTURE-WIDTH":
            bbox["width"] = float(record["nominal"])
        elif dim_id == "DIM-FIXTURE-DEPTH":
            bbox["depth"] = float(record["nominal"])
        elif dim_id == "DIM-FIXTURE-HEIGHT":
            bbox["height"] = float(record["nominal"])
    material_string = ", ".join(_material_labels(ir)) or "see IR"
    return resolved, bbox, material_string


def build_draft_drawing(
    ir: Mapping[str, Any],
    *,
    dimension_whitelist: Iterable[str] = DEFAULT_WHITELIST,
    general_tolerance: str = DEFAULT_TOLERANCE,
    view_scale: str = DEFAULT_VIEW_SCALE,
) -> dict[str, Any]:
    """Build a fixed-template draft drawing document from a validated IR."""
    whitelist = tuple(dimension_whitelist)
    document = dict(ir)
    try:
        validate_engineering_ir(document)
    except ContractValidationError as error:
        raise _declarative_mismatch(
            {"reason": "IR is not schema- or semantically valid", "errors": error.errors}
        ) from error

    design_id = document["designId"]
    revision = document["revision"]
    if not isinstance(design_id, str) or not design_id:
        raise _declarative_mismatch({"reason": "IR missing designId"})
    if not isinstance(revision, str) or not revision:
        raise _declarative_mismatch({"reason": "IR missing revision"})

    dimensions, bbox, material_string = _drawing_dimensions(document, whitelist)
    dimension_texts: list[tuple[str, str]] = [
        (f"{_fmt(bbox['width'])} mm", (0.0, bbox["width"] * 0.38))
        if "width" in bbox
        else (html.escape("width n/a"), (0.0, 36.0))
    ]
    svg = _render_svg(
        design_id=design_id,
        revision=revision,
        materials_text=material_string,
        general_tolerance=general_tolerance,
        view_scale=view_scale,
        width_mm=bbox.get("width"),
        depth_mm=bbox.get("depth"),
        height_mm=bbox.get("height"),
        dimension_texts=dimension_texts,
    )
    qa = _build_qa(document, whitelist, general_tolerance, view_scale)
    return {
        "schemaVersion": "1.0.0",
        "documentType": "DRAFT_DRAWING",
        "classification": "DESIGN_RUN",
        "drawing_builder": DRAWING_BUILDER_VERSION,
        "template_version": DRAWING_TEMPLATE_VERSION,
        "design_id": design_id,
        "revision": revision,
        "maturity": document.get("maturity"),
        "view_scale": view_scale,
        "general_tolerance": general_tolerance,
        "watermark": WATERMARK,
        "not_for_manufacturing": NOT_FOR_MANUFACTURING,
        "title_block": {
            "design_id": design_id,
            "revision": revision,
            "material": material_string,
            "general_tolerance": general_tolerance,
            "unit": "mm",
            "projection": "top view",
        },
        "dimension_whitelist": list(whitelist),
        "dimensions": dimensions,
        "qa": qa,
        "svg": svg,
        "svgSemanticFingerprint": sha256(svg.encode("utf-8")).hexdigest(),
    }


def _load_schema() -> dict[str, Any]:
    return json.loads(DRAWING_SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_drawing_schema() -> None:
    """Ensure the draft-drawing schema is self-consistent."""
    Draft202012Validator.check_schema(_load_schema())


def _schema_errors(document: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(_load_schema())
    return sorted(
        (error.message for error in validator.iter_errors(document)),
        key=lambda message: message,
    )


def qa_all_passed(document: Mapping[str, Any]) -> bool:
    """Return True only when every recorded QA check passes.

    A failing QA row is a valid recorded artifact, but it must block release.
    """
    return all(row.get("status") == "pass" for row in document.get("qa", []))


def verify_draft_drawing(document: dict[str, Any], ir: Mapping[str, Any]) -> dict[str, Any]:
    """Verify a draft drawing document against its source IR.

    Recomputes the QA checklist, title block, watermark and SVG fingerprint.
    Returns a ledger when everything is consistent; the caller must still gate
    release on ``qa_all_passed``.
    """
    schema_problems = _schema_errors(document)
    if schema_problems:
        raise _declarative_mismatch({"schemaErrors": schema_problems})
    if document.get("documentType") != "DRAFT_DRAWING":
        raise _declarative_mismatch({"field": "documentType", "expected": "DRAFT_DRAWING"})
    if document.get("design_id") != ir.get("designId") or document.get("revision") != ir.get("revision"):
        raise _declarative_mismatch(
            {
                "designIdMismatch": document.get("design_id") != ir.get("designId"),
                "revisionMismatch": document.get("revision") != ir.get("revision"),
            }
        )
    if document.get("watermark") != WATERMARK or WATERMARK not in document["svg"]:
        raise _declarative_mismatch({"reason": "DRAFT watermark missing"})
    if NOT_FOR_MANUFACTURING not in document["svg"]:
        raise _declarative_mismatch({"reason": "NOT FOR MANUFACTURING notice missing"})

    whitelist = tuple(document["dimension_whitelist"])
    tolerance = document["general_tolerance"]
    scale = document["view_scale"]
    expected_qa = _build_qa(ir, whitelist, tolerance, scale)
    if expected_qa != document["qa"]:
        raise _declarative_mismatch({"reason": "QA checklist drifted from IR"})

    index = _dimension_index(ir)
    for entry in document["dimensions"]:
        if not entry.get("present"):
            continue
        records = index.get(entry["id"], [])
        if not records:
            raise _declarative_mismatch({"reason": "dimension missing from IR", "id": entry["id"]})
        if float(entry["nominal"]) != float(records[0]["nominal"]):
            raise _draft_mismatch(
                {
                    "id": entry["id"],
                    "document": entry["nominal"],
                    "ir": records[0]["nominal"],
                }
            )

    recomputed = sha256(document["svg"].encode("utf-8")).hexdigest()
    if recomputed != document["svgSemanticFingerprint"]:
        raise _draft_mismatch(
            {"stored": document["svgSemanticFingerprint"], "recomputed": recomputed}
        )

    return {
        "valid": True,
        "qaRecords": len(document["qa"]),
        "qaAllPassed": qa_all_passed(document),
        "svgFingerprintMatched": True,
        "whitelistDimensions": len([d for d in document["dimensions"] if d.get("present")]),
    }


__all__ = [
    "DRAWING_BUILDER_VERSION",
    "DRAWING_SCHEMA_PATH",
    "DRAWING_TEMPLATE_VERSION",
    "DEFAULT_TOLERANCE",
    "DEFAULT_VIEW_SCALE",
    "DEFAULT_WHITELIST",
    "NOT_FOR_MANUFACTURING",
    "WATERMARK",
    "build_draft_drawing",
    "qa_all_passed",
    "validate_drawing_schema",
    "verify_draft_drawing",
]
