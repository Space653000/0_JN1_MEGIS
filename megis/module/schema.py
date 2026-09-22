"""Schema-backed validation for Module documents (G4-MOD-001).

The validator combines JSON Schema conformance with the capability semantics:
geometry generator references are only meaningful at geometry_capable or
above, and clearance envelopes must reference declared interfaces.  All
findings are collected into one deterministic, message-list error so that
consumers face a stable contract.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from megis.contracts.schema_findings import schema_findings
from megis.module.capability import geometry_generator_required

ROOT = Path(__file__).resolve().parents[2]
MODULE_SCHEMA_PATH = ROOT / "schemas" / "v3" / "module.schema.json"


class ModuleValidationError(ValueError):
    """A deterministic list of Module contract violations."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def validate_module_document(document: dict[str, Any]) -> None:
    """Validate a Module document or raise one stable error set."""

    schema = json.loads(MODULE_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = schema_findings(document, schema)

    if document.get("schemaVersion") == "1.0.0":
        level = document.get("capability_level")
        generator_ref = document.get("geometry_generator_ref")
        if not geometry_generator_required(level) and generator_ref is not None:
            errors.append(
                "/geometry_generator_ref: capability below geometry_capable must not carry a geometry generator"
            )
        if geometry_generator_required(level) and generator_ref is None:
            errors.append(
                "/geometry_generator_ref: geometry generator is required at or above geometry_capable"
            )

        interfaces = document.get("interfaces", [])
        seen: set[str] = set()
        for index, interface_id in enumerate(interfaces):
            if not isinstance(interface_id, str):
                continue
            if interface_id in seen:
                errors.append(f"/interfaces/{index}: duplicate interface {interface_id}")
            seen.add(interface_id)

        for index, envelope in enumerate(document.get("clearance_envelopes", [])):
            interface_id = envelope.get("interface_id")
            if isinstance(interface_id, str) and interface_id not in set(interfaces):
                errors.append(
                    f"/clearance_envelopes/{index}/interface_id: unknown interface {interface_id}"
                )

    if errors:
        raise ModuleValidationError(sorted(set(errors)))


__all__ = ["ModuleValidationError", "validate_module_document"]
