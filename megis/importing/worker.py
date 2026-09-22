"""Isolated import worker (G4-IMP-001).

This module is designed to run as its own subprocess: ``python -m
megis.importing.worker --format STEP --input <path>``.  The parent process
never parses untrusted CAD files itself; it launches this worker under a
timeout and reads back a single JSON document.  The worker only extracts
provable metadata (bounding box, solid/shell/face/edge counts, candidate
holes/planar sections, file unit when a marker exists, parser warnings) and
never invents material, load, supplier or mount-intent values.

Every failure inside the worker is translated to a ``MEGIS-IMP-*`` error
document.  The entity scan is bounded by ``MAX_ENTITY_COUNT`` so a huge or
deeply nested file is rejected before it can consume unbounded resources.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
from typing import Any

from megis.importing.policy import MAX_ENTITY_COUNT

STEP_RECORD_RE = re.compile(r"^#\s*(\d+)\s*=")
STEP_OPEN_MARKER = "ISO-10303-21;"
STEP_DATA_MARKER = "DATA;"
STEP_END_MARKER = "END-ISO-10303-21;"
_DXF_ENTITY_TYPES = {
    "LINE",
    "LWPOLYLINE",
    "CIRCLE",
    "ARC",
    "ELLIPSE",
    "SPLINE",
    "POINT",
    "POLYLINE",
    "HATCH",
}
_UNIT_CODES = {
    "0": None,
    "1": "inch",
    "4": "millimetre",
    "6": "metre",
}


class EntityBudgetError(Exception):
    """Internal marker translated to MEGIS-IMP-004 by the worker boundary."""


class StructuralIntegrityError(Exception):
    """Internal marker translated to MEGIS-IMP-003 by the worker boundary."""


@dataclass(frozen=True)
class StepMetadata:
    bounding_box: dict[str, float] | None
    solids: int
    shells: int
    faces: int
    edges: int
    vertices: int
    candidate_holes: int
    candidate_planar_sections: int
    file_unit: str | None
    parser_warnings: tuple[str, ...]


def extract_step_metadata(payload: str) -> StepMetadata:
    """Scan STEP text for provable metadata without full kernel parsing."""
    coordinates: list[tuple[float, float, float]] = []
    counts = {
        "solids": 0,
        "shells": 0,
        "faces": 0,
        "edges": 0,
        "vertices": 0,
        "cylinders": 0,
        "planes": 0,
    }
    warnings: list[str] = []
    file_unit: str | None = None
    explicit_units: set[str] = set()
    saw_length_unit = False
    in_data = False
    record_re = re.compile(r"^#\d+\s*=\s*([A-Z_]+)\s*\(")

    for line in payload.splitlines():
        stripped = line.strip()
        if stripped == "DATA;":
            in_data = True
            continue
        if stripped in ("ENDSEC;", "END-ISO-10303-21;"):
            continue
        if "SI_UNIT" in stripped:
            saw_length_unit = saw_length_unit or ("LENGTH_UNIT" in stripped)
            if ".MILLI." in stripped and ".METRE." in stripped:
                explicit_units.add("millimetre")
            elif ".METRE." in stripped:
                explicit_units.add("metre")
            elif ".INCH." in stripped:
                explicit_units.add("inch")
        match = record_re.match(stripped)
        if not match or not in_data:
            continue
        entity = match.group(1)
        counts["solids"] += entity == "MANIFOLD_SOLID_BREP"
        counts["shells"] += entity == "CLOSED_SHELL"
        counts["faces"] += entity == "ADVANCED_FACE"
        counts["edges"] += entity == "EDGE_CURVE"
        counts["vertices"] += entity == "VERTEX_POINT"
        counts["cylinders"] += entity == "CYLINDRICAL_SURFACE"
        counts["planes"] += entity == "PLANE"
        if entity == "CARTESIAN_POINT":
            coords = _extract_coordinates(stripped)
            if coords is not None:
                coordinates.append(coords)

    if not coordinates:
        warnings.append("no CARTESIAN_POINT records found; bounding box unavailable")

    if explicit_units == {"millimetre"}:
        file_unit = "millimetre"
    elif explicit_units == {"inch"}:
        file_unit = "inch"
    elif explicit_units == {"metre"}:
        file_unit = "metre"
    elif explicit_units or saw_length_unit:
        file_unit = "unknown"

    return StepMetadata(
        bounding_box=_bounding_box(coordinates),
        solids=counts["solids"],
        shells=counts["shells"],
        faces=counts["faces"],
        edges=counts["edges"],
        vertices=counts["vertices"],
        candidate_holes=counts["cylinders"],
        candidate_planar_sections=counts["planes"],
        file_unit=file_unit,
        parser_warnings=tuple(warnings),
    )


def _extract_coordinates(record: str) -> tuple[float, float, float] | None:
    """Parse a CARTESIAN_POINT('',(x,y,z)) record into a coordinate triple."""
    match = re.search(
        r"\(\s*([+-]?[0-9.eE+-]+)\s*,\s*([+-]?[0-9.eE+-]+)\s*,\s*([+-]?[0-9.eE+-]+)\s*\)",
        record,
    )
    if not match:
        return None
    values: list[float | None] = []
    for group in match.groups():
        parsed = _parse_decimal(group)
        values.append(parsed)
    if None in values:
        return None
    return tuple(values)  # type: ignore[return-value]


def _parse_decimal(value: str) -> float | None:
    cleaned = value.strip().replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _bounding_box(
    coordinates: list[tuple[float, float, float]],
) -> dict[str, float] | None:
    if not coordinates:
        return None
    return {
        "xmin": min(point[0] for point in coordinates),
        "ymin": min(point[1] for point in coordinates),
        "zmin": min(point[2] for point in coordinates),
        "xmax": max(point[0] for point in coordinates),
        "ymax": max(point[1] for point in coordinates),
        "zmax": max(point[2] for point in coordinates),
    }


@dataclass(frozen=True)
class DxfMetadata:
    bounding_box: dict[str, float] | None
    entity_counts: dict[str, int]
    total_entities: int
    file_unit: str | None
    candidate_holes: int
    candidate_planar_sections: int
    parser_warnings: tuple[str, ...]


def extract_dxf_metadata(payload: str) -> DxfMetadata:
    """Scan DXF group-code/value pairs for provable 2D metadata.

    The HEADER unit is only trusted when it directly follows the ``$INSUNITS``
    variable (group code 9), because other ``70`` codes appear all over a DXF
    file.  ENTITIES geometry records coordinate pairs from group codes 10/20.
    """
    lines = payload.splitlines()
    points: list[tuple[float, float]] = []
    entity_counts: dict[str, int] = {}
    section = ""
    current_entity: str | None = None
    current_var: str | None = None
    insunits_pending = False
    file_unit: str | None = None
    warnings: list[str] = []
    pending_point: dict[str, float] = {}
    index = 0
    expect_section_name = False

    def commit_point() -> None:
        nonlocal pending_point
        if len(pending_point) == 2:
            points.append((pending_point["x"], pending_point["y"]))
        pending_point = {}

    while index + 1 < len(lines):
        group = lines[index].strip()
        value = lines[index + 1].strip()
        index += 2

        if group == "0":
            commit_point()
            current_var = None
            if value == "SECTION":
                expect_section_name = True
                current_entity = None
                continue
            if value == "ENDSEC":
                section = ""
                expect_section_name = False
                current_entity = None
                continue
            upper = value.upper()
            if section == "ENTITIES" and upper in _DXF_ENTITY_TYPES:
                current_entity = upper
                entity_counts[upper] = entity_counts.get(upper, 0) + 1
            else:
                current_entity = None
            continue

        if group == "2" and expect_section_name:
            expect_section_name = False
            if value == "HEADER":
                section = "HEADER"
            elif value == "ENTITIES":
                section = "ENTITIES"
            elif value in ("CLASSES", "TABLES", "BLOCKS", "OBJECTS"):
                section = value
            else:
                section = ""
            continue

        if section == "HEADER":
            if group == "9":
                # DXF header variable names use group code 9.
                if value.upper() == "$INSUNITS":
                    insunits_pending = True
                    current_var = value
                else:
                    current_var = value
                    insunits_pending = False
                continue
            if insunits_pending and group == "70":
                unit_seen_value = value
                insunits_pending = False
                candidate = _UNIT_CODES.get(unit_seen_value, "unknown")
                if candidate is not None:
                    file_unit = candidate
                else:
                    file_unit = "unknown"
            continue

        if section != "ENTITIES" or current_entity is None:
            # Coordinates outside the ENTITIES geometry are not provable
            # drawing bounds; keep looping.
            continue

        if group in ("10", "20"):
            number = _parse_decimal(value)
            if number is None:
                continue
            if group == "10":
                commit_point()
                pending_point = {"x": number}
            elif "x" in pending_point:
                pending_point["y"] = number
                commit_point()
            continue

    if not points:
        warnings.append("no coordinate pairs found; bounding box unavailable")

    candidate_holes = entity_counts.get("CIRCLE", 0)
    candidate_planar = sum(
        entity_counts.get(kind, 0) for kind in ("LWPOLYLINE", "POLYLINE", "HATCH")
    )
    return DxfMetadata(
        bounding_box=_bounding_box_2d(points),
        entity_counts=entity_counts,
        total_entities=sum(entity_counts.values()),
        file_unit=file_unit,
        candidate_holes=candidate_holes,
        candidate_planar_sections=candidate_planar,
        parser_warnings=tuple(warnings),
    )


def _bounding_box_2d(points: list[tuple[float, float]]) -> dict[str, float] | None:
    if not points:
        return None
    return {
        "xmin": min(point[0] for point in points),
        "ymin": min(point[1] for point in points),
        "zmin": 0.0,
        "xmax": max(point[0] for point in points),
        "ymax": max(point[1] for point in points),
        "zmax": 0.0,
    }


def count_step_entities(payload: str) -> int:
    """Count STEP data-section records to enforce the entity budget."""
    in_data = False
    count = 0
    for line in payload.splitlines():
        stripped = line.strip()
        if stripped == "DATA;":
            in_data = True
            continue
        if in_data and STEP_RECORD_RE.match(stripped):
            count += 1
    return count


def check_step_structure(payload: str) -> None:
    """Reject a payload that cannot be a well-formed ISO-10303-21 file."""
    non_blank = [line.strip() for line in payload.splitlines() if line.strip()]
    if not non_blank or not non_blank[0].startswith(STEP_OPEN_MARKER):
        raise StructuralIntegrityError(
            "STEP missing ISO-10303-21; opening marker"
        )
    missing = [
        marker
        for marker in (STEP_DATA_MARKER, "ENDSEC;", STEP_END_MARKER)
        if marker not in payload
    ]
    if missing:
        raise StructuralIntegrityError(
            "STEP missing structural markers: " + ", ".join(missing)
        )


def check_dxf_structure(payload: str) -> None:
    """Reject a payload that lacks DXF section framing or a final EOF."""
    stripped_lines = [line.strip() for line in payload.splitlines()]
    if "ENDSEC" not in stripped_lines:
        raise StructuralIntegrityError(
            "DXF missing ENDSEC framing markers"
        )
    if "SECTION" not in stripped_lines:
        raise StructuralIntegrityError(
            "DXF missing SECTION framing markers"
        )
    if "EOF" not in stripped_lines:
        raise StructuralIntegrityError(
            "DXF missing final EOF marker"
        )

def _run() -> int:
    parser = argparse.ArgumentParser(description="MEGIS isolated import worker")
    parser.add_argument("--format", required=True, choices=("STEP", "DXF"))
    parser.add_argument("--input", required=True)
    parser.add_argument("--max-entities", type=int, default=None)
    args = parser.parse_args()
    max_entities = (
        args.max_entities if args.max_entities is not None else MAX_ENTITY_COUNT
    )

    try:
        source = Path(args.input)
        payload = source.read_text(encoding="utf-8", errors="replace")
        if args.format == "STEP":
            check_step_structure(payload)
            if count_step_entities(payload) > max_entities:
                raise EntityBudgetError()
            metadata = extract_step_metadata(payload)
            report: dict[str, Any] = {
                "schemaVersion": "1.0.0",
                "workItem": "G4-IMP-001",
                "importFormat": "STEP",
                "sourcePath": str(source),
                "derivedFromImport": True,
                "capabilityLevel": None,
                "boundingBoxMm": metadata.bounding_box,
                "solids": metadata.solids,
                "shells": metadata.shells,
                "faces": metadata.faces,
                "edges": metadata.edges,
                "candidateHoles": metadata.candidate_holes,
                "candidatePlanarSections": metadata.candidate_planar_sections,
                "fileUnit": metadata.file_unit,
                "parserWarnings": list(metadata.parser_warnings),
            }
        else:
            check_dxf_structure(payload)
            metadata = extract_dxf_metadata(payload)
            if metadata.total_entities > max_entities:
                raise EntityBudgetError()
            report = {
                "schemaVersion": "1.0.0",
                "workItem": "G4-IMP-001",
                "importFormat": "DXF",
                "sourcePath": str(source),
                "derivedFromImport": True,
                "capabilityLevel": None,
                "boundingBoxMm": metadata.bounding_box,
                "solids": None,
                "shells": None,
                "faces": None,
                "edges": metadata.total_entities,
                "candidateHoles": metadata.candidate_holes,
                "candidatePlanarSections": metadata.candidate_planar_sections,
                "fileUnit": metadata.file_unit,
                "parserWarnings": list(metadata.parser_warnings),
            }
    except EntityBudgetError:
        print(json.dumps({"error": {"code": "MEGIS-IMP-004"}}))
        return 0
    except StructuralIntegrityError as error:
        print(json.dumps({"error": {"code": "MEGIS-IMP-003", "detail": str(error)}}))
        return 0
    except Exception as error:  # noqa: BLE001 - worker boundary maps all to IMP-003
        print(json.dumps({"error": {"code": "MEGIS-IMP-003", "detail": str(error)}}))
        return 0

    print(json.dumps({"report": report}))
    return 0


if __name__ == "__main__":
    sys.exit(_run())
