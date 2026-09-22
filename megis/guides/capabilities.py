"""Deterministic capability manifest (G6-UI-001).

The manifest is the single source of truth a guided-flow UI may render
from: it lists only capabilities the backend has proven across the G0-G5
contracts.  It is byte-deterministic so the frozen golden in
``contracts/g6/golden/capability-manifest.json`` can be compared on every
build and any drift surfaces as a failed verification instead of a silent
change.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from megis.adapters.cadquery_backend import CadQueryBackend
from megis.envelope import load_envelope
from megis.module.capability import CAPABILITY_LEVELS, policy_for
from megis.relationship.vocabulary import (
    RELATIONSHIP_TYPES,
    REQUIRED_PARAMETERS,
    TYPE_MEANING,
)

def validate_manifest(manifest: dict[str, Any]) -> None:
    """Validate a capability manifest against its v3 schema.

    Raises ``jsonschema.ValidationError`` when the manifest drifts from the
    schema, so a silent shape change of the proven-capability surface fails
    verification instead of passing.
    """
    schema = json.loads(MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(manifest)

ROOT = Path(__file__).resolve().parents[2]
GOLDEN_PATH = ROOT / "contracts" / "g6" / "golden" / "capability-manifest.json"
MANIFEST_SCHEMA_PATH = ROOT / "schemas" / "v3" / "capability-manifest.schema.json"

MANIFEST_ID = "megis-capability-manifest@1.0.0"

CONFIDENCE_LABELS = (
    "Verified",
    "Supported",
    "Partially supported",
    "Unknown",
    "Needs engineering review",
)

MATURITY_TIERS = ("DRAFT", "CONCEPT", "PROTOTYPE", "ENGINEERING_REVIEWED", "RELEASED")


def _canonical(body: dict[str, Any]) -> str:
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def build_manifest() -> dict[str, Any]:
    """Build the deterministic capability manifest from proven backend data."""
    backend = CadQueryBackend().capabilities()
    envelope = load_envelope()

    modules = []
    for level in CAPABILITY_LEVELS:
        policy = policy_for(level)
        modules.append(
            {
                "level": level,
                "uiDisplay": policy.ui_display,
                "layoutAllowed": bool(policy.layout_allowed),
                "geometryAllowed": bool(policy.geometry_allowed),
                "maturityCap": policy.maturity_cap,
                "proven": True,
            }
        )

    relationships = []
    for rel_type in RELATIONSHIP_TYPES:
        relationships.append(
            {
                "type": rel_type,
                "meaning": TYPE_MEANING[rel_type],
                "requiredParameters": list(REQUIRED_PARAMETERS.get(rel_type, ())),
                "proven": True,
            }
        )

    operations = [
        {"id": operation.value, "proven": True}
        for operation in sorted(backend.supported_operations, key=lambda item: item.value)
    ]

    body: dict[str, Any] = {
        "schemaVersion": "1.0.0",
        "corpusId": MANIFEST_ID,
        "designTypes": [
            {
                "id": "fixture-enclosure",
                "label": "治具／電子外殼",
                "proven": True,
            }
        ],
        "geometry": {
            "backendId": backend.backend_id,
            "backendVersion": backend.backend_version,
            "deterministic": bool(backend.deterministic),
            "operations": operations,
            "exportFormats": sorted(backend.export_formats),
        },
        "modules": {
            "capabilityLevels": modules,
        },
        "relationships": relationships,
        "envelope": {
            "envelopeId": envelope.envelope_id,
            "label": envelope.label,
            "verified": bool(envelope.verified),
            "outerDimensionsMm": {
                "widthMm": envelope.outer_dimensions_mm.width_mm,
                "depthMm": envelope.outer_dimensions_mm.depth_mm,
                "heightMm": envelope.outer_dimensions_mm.height_mm,
            },
            "minimumWallMm": envelope.minimum_wall_mm,
            "materials": list(envelope.materials),
            "machining": list(envelope.machining),
            "fixture": {
                "coverCount": envelope.cover_count,
                "fastenerCount": envelope.fastener_count,
            },
            "unsupportedErrorCodes": list(envelope.unsupported_error_codes),
        },
        "confidenceLabels": list(CONFIDENCE_LABELS),
        "maturityTiers": list(MATURITY_TIERS),
    }
    fingerprint = hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()
    body["manifestFingerprint"] = fingerprint
    return body


def serialize_manifest(manifest: dict[str, Any]) -> str:
    """Canonical (non-fingerprint-proof) serialization of a manifest."""
    return _canonical(manifest)


def load_golden(path: Path = GOLDEN_PATH) -> dict[str, Any]:
    """Load the frozen golden manifest as a plain dictionary."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


__all__ = [
    "GOLDEN_PATH",
    "MANIFEST_ID",
    "MANIFEST_SCHEMA_PATH",
    "build_manifest",
    "load_golden",
    "serialize_manifest",
    "validate_manifest",
]
