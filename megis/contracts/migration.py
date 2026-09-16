"""Explicit, deterministic Engineering IR migration and rollback contracts."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .validation import ContractValidationError, validate_engineering_ir


ROOT = Path(__file__).resolve().parents[2]
LEGACY_V1_SCHEMA_PATH = ROOT / "schemas" / "v1" / "engineering-ir.schema.json"
CURRENT_SCHEMA_VERSION = "2.0.0"


class MigrationError(ValueError):
    """A migration cannot be selected, verified, or rolled back safely."""


def canonical_hash(document: dict[str, Any]) -> str:
    """Return a stable SHA-256 for a JSON object independent of key order."""

    payload = json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(payload).hexdigest()


@dataclass(frozen=True)
class MigrationReceipt:
    source_version: str
    target_version: str
    source_sha256: str
    target_sha256: str
    source_document: dict[str, Any]


@dataclass(frozen=True)
class MigrationResult:
    document: dict[str, Any]
    receipt: MigrationReceipt


def _validate_v1(document: dict[str, Any]) -> None:
    schema = json.loads(LEGACY_V1_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
    if errors:
        rendered = [f"/{'/'.join(map(str, error.absolute_path))}: {error.message}" for error in errors]
        raise ContractValidationError(rendered)


def _migrate_reference_fixture_v1(document: dict[str, Any]) -> dict[str, Any]:
    size = document["sizeMm"]
    recorded_at = document["recordedAt"]
    design_id = document["designId"]
    revision = document["revision"]
    minimum_wall = document["minimumWallMm"]
    return {
        "schemaVersion": CURRENT_SCHEMA_VERSION,
        "designId": design_id,
        "revision": revision,
        "maturity": "PROTOTYPE",
        "unitSystem": {"length": "mm", "angle": "deg", "mass": "kg", "time": "s"},
        "coordinateSystem": {
            "handedness": "right",
            "axes": {"x": "width", "y": "depth", "z": "height"},
        },
        "requirements": [
            {
                "id": "REQ-FIXTURE-001",
                "statement": "Locate and protect the reference PCB within the supported CNC envelope.",
                "priority": "must",
                "verificationMethod": "inspection",
                "provenanceIds": ["PROV-FIXTURE-001"],
            }
        ],
        "components": [
            {
                "id": "COMP-FIXTURE-BASE",
                "name": "Fixture base",
                "domain": "fixture",
                "componentType": "fixture_base",
                "dimensions": [
                    {"name": "width", "dimension": "length", "quantity": {"id": "DIM-FIXTURE-WIDTH", "unit": "mm", "nominal": size["width"], "tolerance": 0.1}},
                    {"name": "depth", "dimension": "length", "quantity": {"id": "DIM-FIXTURE-DEPTH", "unit": "mm", "nominal": size["depth"], "tolerance": 0.1}},
                    {"name": "height", "dimension": "length", "quantity": {"id": "DIM-FIXTURE-HEIGHT", "unit": "mm", "nominal": size["height"], "tolerance": 0.1}},
                ],
                "materialId": "MAT-FIXTURE-AL6061",
                "provenanceIds": ["PROV-FIXTURE-001"],
            },
            {"id": "COMP-FIXTURE-COVER", "name": "Fixture cover", "domain": "fixture", "componentType": "cover", "dimensions": [], "materialId": "MAT-FIXTURE-AL6061", "provenanceIds": ["PROV-FIXTURE-001"]},
            {"id": "COMP-FIXTURE-PCB", "name": "Reference PCB", "domain": "fixture", "componentType": "pcb", "dimensions": [], "provenanceIds": ["PROV-FIXTURE-001"]},
        ],
        "interfaces": [
            {"id": "INT-FIXTURE-PCB", "name": "PCB mounting interface", "interfaceType": "mount", "participantIds": ["COMP-FIXTURE-BASE", "COMP-FIXTURE-PCB"]},
            {"id": "INT-FIXTURE-COVER", "name": "Cover mounting interface", "interfaceType": "mount", "participantIds": ["COMP-FIXTURE-BASE", "COMP-FIXTURE-COVER"]},
        ],
        "relationships": [
            {"id": "REL-FIXTURE-PCB", "relationshipType": "mounts_to", "sourceId": "COMP-FIXTURE-PCB", "targetId": "COMP-FIXTURE-BASE", "constraintIds": ["CON-FIXTURE-WALL"]},
            {"id": "REL-FIXTURE-COVER", "relationshipType": "mounts_to", "sourceId": "COMP-FIXTURE-COVER", "targetId": "COMP-FIXTURE-BASE", "constraintIds": ["CON-FIXTURE-WALL"]},
        ],
        "materials": [
            {"id": "MAT-FIXTURE-AL6061", "name": "Aluminum 6061", "designation": document["material"], "properties": [], "provenanceIds": ["PROV-FIXTURE-002"]}
        ],
        "manufacturing": [
            {"id": "MFG-FIXTURE-CNC", "process": document["manufacturingProcess"], "componentIds": ["COMP-FIXTURE-BASE", "COMP-FIXTURE-COVER"]}
        ],
        "constraints": [
            {"id": "CON-FIXTURE-WALL", "constraintType": "wall", "severity": "hard", "targetIds": ["COMP-FIXTURE-BASE", "COMP-FIXTURE-COVER"], "measurement": {"name": "minimum wall", "dimension": "length", "quantity": {"id": "DIM-FIXTURE-WALL", "unit": "mm", "min": minimum_wall, "max": minimum_wall + 1.0}}, "provenanceIds": ["PROV-FIXTURE-002"]}
        ],
        "assumptions": [
            {"id": "ASM-FIXTURE-SETUP", "subjectId": "COMP-FIXTURE-BASE", "field": "/manufacturingSetup", "status": "defaulted", "rationale": "Golden case uses the fixed three-axis setup.", "provenanceIds": ["PROV-FIXTURE-003"]}
        ],
        "unknowns": [
            {"id": "UNK-FIXTURE-LOAD", "subjectId": design_id, "field": "/maximumLoad", "unsafeToDefault": True, "question": "What maximum applied load must the fixture withstand?"}
        ],
        "provenance": [
            {"id": "PROV-FIXTURE-001", "subjectId": design_id, "field": "/requirements", "source": "user", "actor": "golden-case-owner", "recordedAt": recorded_at},
            {"id": "PROV-FIXTURE-002", "subjectId": "COMP-FIXTURE-BASE", "field": "/constraints", "source": "derived", "sourceRef": "rule:CNC-WALL-MIN@1.0.0", "recordedAt": recorded_at},
            {"id": "PROV-FIXTURE-003", "subjectId": "COMP-FIXTURE-BASE", "field": "/manufacturingSetup", "source": "defaulted", "rationale": "Reference Fixture baseline", "recordedAt": recorded_at},
        ],
    }


def migrate_engineering_ir(document: dict[str, Any]) -> MigrationResult:
    """Migrate one supported prior-version document to the current IR version."""

    source = deepcopy(document)
    version = source.get("schemaVersion")
    if version != "1.0.0":
        raise MigrationError(f"No explicit migration path from {version!r} to {CURRENT_SCHEMA_VERSION}")
    _validate_v1(source)
    migrated = _migrate_reference_fixture_v1(source)
    validate_engineering_ir(migrated)
    receipt = MigrationReceipt(
        source_version=version,
        target_version=CURRENT_SCHEMA_VERSION,
        source_sha256=canonical_hash(source),
        target_sha256=canonical_hash(migrated),
        source_document=deepcopy(source),
    )
    return MigrationResult(document=migrated, receipt=receipt)


def rollback_engineering_ir(result: MigrationResult) -> dict[str, Any]:
    """Restore the exact source only when receipt and migrated document still match."""

    if canonical_hash(result.document) != result.receipt.target_sha256:
        raise MigrationError("Migrated document changed after receipt creation")
    source = deepcopy(result.receipt.source_document)
    if canonical_hash(source) != result.receipt.source_sha256:
        raise MigrationError("Rollback source does not match its receipt")
    _validate_v1(source)
    return source
