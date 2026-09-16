"""Validation entry points for versioned MEGIS contract documents."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
PRIMITIVES_SCHEMA_PATH = ROOT / "schemas" / "v2" / "primitives.schema.json"


class ContractValidationError(ValueError):
    """A deterministic list of contract violations."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def _path(error_path: Any) -> str:
    parts = [str(part) for part in error_path]
    return "/" + "/".join(parts) if parts else "/"


def validate_primitives(document: dict[str, Any]) -> None:
    """Validate a G1 primitive-contract document or raise one stable error set."""

    schema = json.loads(PRIMITIVES_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = [
        f"{_path(error.absolute_path)}: {error.message}"
        for error in sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path))
    ]

    axes = document.get("coordinateSystem", {}).get("axes", {})
    axis_semantics = [axes.get(axis) for axis in ("x", "y", "z")]
    if all(isinstance(value, str) for value in axis_semantics) and len(set(axis_semantics)) != 3:
        errors.append("/coordinateSystem/axes: x, y, and z semantics must be distinct")

    known_ids = set(document.get("entityIds", []))
    for index, quantity in enumerate(document.get("quantities", [])):
        quantity_id = quantity.get("id")
        if isinstance(quantity_id, str) and quantity_id not in known_ids:
            errors.append(f"/quantities/{index}/id: undeclared entity ID {quantity_id}")
        minimum = quantity.get("min")
        maximum = quantity.get("max")
        nominal = quantity.get("nominal")
        if minimum is not None and maximum is not None and minimum > maximum:
            errors.append(f"/quantities/{index}: min must not exceed max")
        if nominal is not None and minimum is not None and nominal < minimum:
            errors.append(f"/quantities/{index}: nominal must not be below min")
        if nominal is not None and maximum is not None and nominal > maximum:
            errors.append(f"/quantities/{index}: nominal must not exceed max")

    for index, record in enumerate(document.get("provenance", [])):
        recorded_at = record.get("recordedAt")
        if isinstance(recorded_at, str):
            try:
                parsed = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    raise ValueError("timezone is required")
            except ValueError:
                errors.append(f"/provenance/{index}/recordedAt: invalid RFC 3339 date-time")

    for collection in ("provenance", "knowledgeStates"):
        for index, record in enumerate(document.get(collection, [])):
            subject_id = record.get("subjectId")
            if isinstance(subject_id, str) and subject_id not in known_ids:
                errors.append(f"/{collection}/{index}/subjectId: dangling entity reference {subject_id}")

    if errors:
        raise ContractValidationError(sorted(set(errors)))
