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

import re

from jsonschema import Draft202012Validator

from megis.module.capability import geometry_generator_required

ROOT = Path(__file__).resolve().parents[2]
MODULE_SCHEMA_PATH = ROOT / "schemas" / "v3" / "module.schema.json"


class ModuleValidationError(ValueError):
    """A deterministic list of Module contract violations."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def _path(error_path: Any) -> str:
    parts = [str(part) for part in error_path]
    return "/" + "/".join(parts) if parts else "/"

def _dig(document: Any, path: list[Any]) -> Any:
    """Follow a JSON pointer path into a document, tolerating gaps."""
    current = document
    for part in path:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and isinstance(part, int):
            current = current[part]
        else:
            return None
    return current

def _unexpected_property_names(message: str) -> list[str]:
    """Names reported by an additionalProperties finding."""
    return re.findall(r"'([^']+)' was unexpected", message)

def _schema_findings(document: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """Flatten schema findings into deterministic JSON-pointer entries.

    required and additionalProperties failures carry the containing object's path
    in jsonschema; they are expanded here so every entry names the exact key at
    fault, keeping the aggregate contract unambiguous for consumers.
    """
    findings: list[str] = []
    for error in sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    ):
        path = list(error.absolute_path)
        if error.validator == "required":
            parent = _dig(document, path)
            required = list(error.validator_value)
            missing = [
                name for name in required if not isinstance(parent, dict) or name not in parent
            ] or required
            for name in missing:
                findings.append(f"{_path([*path, name])}: {name} is a required property")
        elif error.validator == "additionalProperties":
            for name in _unexpected_property_names(error.message):
                findings.append(f"{_path([*path, name])}: additional property {name} is not allowed")
        else:
            findings.append(f"{_path(path)}: {error.message}")
    return findings


def validate_module_document(document: dict[str, Any]) -> None:
    """Validate a Module document or raise one stable error set."""

    schema = json.loads(MODULE_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = _schema_findings(document, schema)

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
