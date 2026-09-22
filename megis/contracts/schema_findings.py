"""Deterministic JSON-pointer schema findings shared by v3 validators.

jsonschema reports ``required`` and ``additionalProperties`` failures at the
containing object's path.  This helper flattens every finding into a
deterministic ``/path: message`` entry that names the exact key at fault, so
all MEGIS validators expose one unambiguous aggregate contract.
"""

from __future__ import annotations

import re
from typing import Any

from jsonschema import Draft202012Validator


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


def schema_findings(document: dict[str, Any], schema: dict[str, Any]) -> list[str]:
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


__all__ = ["schema_findings"]
