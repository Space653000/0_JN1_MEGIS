"""Import report contract (G4-IMP-001).

The import report only carries information the blueprint's section 12 import
policy allows to be *proven* from an untrusted STEP/DXF file: bounding box,
solid/shell count, candidate holes and planar sections, file unit when
present, and parser warnings.  Material, loads, supplier, electrical/acoustic
properties and mount intent are never invented here; they must come from a
datasheet or a human with provenance, so the report schema has no place for
them.  Every import report is marked ``derived_from_import`` and never raises
a module's capability level.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
REPORT_SCHEMA_PATH = ROOT / "schemas" / "v3" / "import-report.schema.json"


@dataclass(frozen=True)
class BoundingBoxMm:
    """Axis-aligned bounds in millimetres as reported by the trusted worker."""

    xmin: float
    ymin: float
    zmin: float
    xmax: float
    ymax: float
    zmax: float

    def to_dict(self) -> dict[str, float]:
        return {
            "xmin": self.xmin,
            "ymin": self.ymin,
            "zmin": self.zmin,
            "xmax": self.xmax,
            "ymax": self.ymax,
            "zmax": self.zmax,
        }


@dataclass(frozen=True)
class ImportReport:
    """Safe metadata extraction result from a trusted subprocess worker."""

    schema_version: str
    work_item: str
    import_format: str
    source_path: str
    derived_from_import: bool
    capability_level: str | None
    bounding_box_mm: BoundingBoxMm | None
    solids: int | None
    shells: int | None
    faces: int | None
    edges: int | None
    candidate_holes: int | None
    candidate_planar_sections: int | None
    file_unit: str | None
    parser_warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "workItem": self.work_item,
            "importFormat": self.import_format,
            "sourcePath": self.source_path,
            "derivedFromImport": self.derived_from_import,
            "capabilityLevel": self.capability_level,
            "boundingBoxMm": (
                self.bounding_box_mm.to_dict() if self.bounding_box_mm else None
            ),
            "solids": self.solids,
            "shells": self.shells,
            "faces": self.faces,
            "edges": self.edges,
            "candidateHoles": self.candidate_holes,
            "candidatePlanarSections": self.candidate_planar_sections,
            "fileUnit": self.file_unit,
            "parserWarnings": list(self.parser_warnings),
        }

    @classmethod
    def from_worker(cls, report: dict[str, Any]) -> "ImportReport":
        """Build a report from the JSON dict emitted by the isolated worker."""
        bbox = report.get("boundingBoxMm")
        return cls(
            schema_version=report.get("schemaVersion", "1.0.0"),
            work_item=report.get("workItem", "G4-IMP-001"),
            import_format=report["importFormat"],
            source_path=report["sourcePath"],
            derived_from_import=bool(report.get("derivedFromImport", True)),
            capability_level=report.get("capabilityLevel"),
            bounding_box_mm=(
                BoundingBoxMm(
                    xmin=bbox["xmin"],
                    ymin=bbox["ymin"],
                    zmin=bbox["zmin"],
                    xmax=bbox["xmax"],
                    ymax=bbox["ymax"],
                    zmax=bbox["zmax"],
                )
                if bbox
                else None
            ),
            solids=report.get("solids"),
            shells=report.get("shells"),
            faces=report.get("faces"),
            edges=report.get("edges"),
            candidate_holes=report.get("candidateHoles"),
            candidate_planar_sections=report.get("candidatePlanarSections"),
            file_unit=report.get("fileUnit"),
            parser_warnings=tuple(report.get("parserWarnings", ())),
        )


def validate_import_report(report: dict[str, Any]) -> None:
    """Validate a serialised import report against the v3 schema."""
    schema = json.loads(REPORT_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(report),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        messages = "; ".join(error.message for error in errors)
        raise ValueError(f"import report invalid: {messages}")


def validate_report_schema() -> None:
    """Standalone schema sanity check for the import report contract."""
    schema = json.loads(REPORT_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    sample = ImportReport(
        schema_version="1.0.0",
        work_item="G4-IMP-001",
        import_format="STEP",
        source_path="in.step",
        derived_from_import=True,
        capability_level=None,
        bounding_box_mm=BoundingBoxMm(0.0, 0.0, 0.0, 1.0, 1.0, 1.0),
        solids=1,
        shells=1,
        faces=6,
        edges=12,
        candidate_holes=0,
        candidate_planar_sections=1,
        file_unit="millimetre",
        parser_warnings=(),
    ).to_dict()
    if list(validator.iter_errors(sample)):
        raise AssertionError("import report sample failed the v3 schema")
