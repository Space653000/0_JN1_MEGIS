"""Schema-backed validation for Relationship documents (G4-GRF-001).

The validator combines JSON Schema conformance with the type semantics from
blueprint 4.16: relationship type vocabulary is closed, every parameter entry
carries provenance, and each type's required references plus numerical and
text invariants are enforced.  All findings are collected into one
deterministic, message-list error for consumers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from megis.contracts.schema_findings import schema_findings
from megis.relationship.vocabulary import (
    LENGTH_PARAMETERS,
    REFERENCE_PARAMETERS,
    STRICTLY_POSITIVE_LENGTH_PARAMETERS,
    TEXT_PARAMETERS,
    relationship_type_index,
)

ROOT = Path(__file__).resolve().parents[2]
RELATIONSHIP_SCHEMA_PATH = ROOT / "schemas" / "v3" / "relationship.schema.json"


class RelationshipValidationError(ValueError):
    """A deterministic list of Relationship contract violations."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def _parameter_findings(parameters: Any) -> list[str]:
    """Semantic invariants for the values already present in parameters."""
    findings: list[str] = []
    if not isinstance(parameters, dict):
        return findings
    for key, entry in parameters.items():
        if not isinstance(entry, dict) or "value" not in entry:
            continue
        value = entry["value"]
        if key in REFERENCE_PARAMETERS:
            if not isinstance(value, str) or not value:
                findings.append(
                    f"/parameters/{key}: reference parameter must be a non-empty string"
                )
        if key in LENGTH_PARAMETERS:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                findings.append(
                    f"/parameters/{key}: length parameter must be a number"
                )
            elif value < 0:
                findings.append(
                    f"/parameters/{key}: length parameter must not be negative"
                )
            elif key in STRICTLY_POSITIVE_LENGTH_PARAMETERS and value <= 0:
                findings.append(
                    f"/parameters/{key}: length parameter must be strictly positive"
                )
        if key in TEXT_PARAMETERS:
            if not isinstance(value, str) or not value:
                findings.append(
                    f"/parameters/{key}: text parameter must be a non-empty string"
                )
    return findings


def validate_relationship(document: dict[str, Any]) -> None:
    """Validate a Relationship document or raise one stable error set."""

    schema = json.loads(RELATIONSHIP_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = schema_findings(document, schema)

    if document.get("schemaVersion") == "1.0.0":
        relationship_type = document.get("type")
        source = document.get("source")
        target = document.get("target")
        if relationship_type_index(relationship_type) >= 0:
            if isinstance(source, str) and source == target:
                errors.append(
                    "/target: relationship cannot relate an entity to itself"
                )
            errors.extend(_parameter_findings(document.get("parameters")))

    if errors:
        raise RelationshipValidationError(sorted(set(errors)))


__all__ = ["RelationshipValidationError", "validate_relationship"]
