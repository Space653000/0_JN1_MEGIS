"""Validation entry points for versioned MEGIS contract documents."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[2]
PRIMITIVES_SCHEMA_PATH = ROOT / "schemas" / "v2" / "primitives.schema.json"
ENGINEERING_IR_SCHEMA_PATH = ROOT / "schemas" / "v2" / "engineering-ir.schema.json"

DIMENSION_UNITS = {
    "length": {"mm"},
    "angle": {"deg"},
    "mass": {"kg"},
    "time": {"s"},
    "force": {"N"},
    "torque": {"N_mm"},
    "pressure": {"Pa"},
    "frequency": {"Hz"},
    "sound_pressure_level": {"dB"},
    "speed": {"m_s"},
    "voltage": {"V"},
    "current": {"A"},
    "power": {"W"},
}


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


def _measurement_errors(measurement: dict[str, Any], path: str) -> list[str]:
    errors: list[str] = []
    dimension = measurement.get("dimension")
    quantity = measurement.get("quantity", {})
    unit = quantity.get("unit")
    if dimension in DIMENSION_UNITS and unit not in DIMENSION_UNITS[dimension]:
        errors.append(f"{path}/quantity/unit: {unit} is incompatible with {dimension}")
    minimum = quantity.get("min")
    maximum = quantity.get("max")
    nominal = quantity.get("nominal")
    if minimum is not None and maximum is not None and minimum > maximum:
        errors.append(f"{path}/quantity: min must not exceed max")
    if nominal is not None and minimum is not None and nominal < minimum:
        errors.append(f"{path}/quantity: nominal must not be below min")
    if nominal is not None and maximum is not None and nominal > maximum:
        errors.append(f"{path}/quantity: nominal must not exceed max")
    return errors


def validate_engineering_ir(document: dict[str, Any]) -> None:
    """Validate the full V2 Engineering IR structure and semantic references."""

    primitives_schema = json.loads(PRIMITIVES_SCHEMA_PATH.read_text(encoding="utf-8"))
    ir_schema = json.loads(ENGINEERING_IR_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(primitives_schema)
    Draft202012Validator.check_schema(ir_schema)
    registry = Registry().with_resource(
        primitives_schema["$id"], Resource.from_contents(primitives_schema)
    )
    validator = Draft202012Validator(
        ir_schema,
        registry=registry,
        format_checker=FormatChecker(),
    )
    errors = [
        f"{_path(error.absolute_path)}: {error.message}"
        for error in sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path))
    ]

    entity_collections = (
        "requirements",
        "components",
        "interfaces",
        "relationships",
        "materials",
        "manufacturing",
        "constraints",
        "assumptions",
        "unknowns",
        "provenance",
    )
    seen: dict[str, str] = {}
    design_id = document.get("designId")
    if isinstance(design_id, str):
        seen[design_id] = "/designId"
    for collection in entity_collections:
        for index, entity in enumerate(document.get(collection, [])):
            entity_id = entity.get("id")
            if not isinstance(entity_id, str):
                continue
            path = f"/{collection}/{index}/id"
            if entity_id in seen:
                errors.append(f"{path}: duplicate ID {entity_id}; first declared at {seen[entity_id]}")
            else:
                seen[entity_id] = path

    known_ids = set(seen)
    provenance_ids = {item.get("id") for item in document.get("provenance", [])}
    component_ids = {item.get("id") for item in document.get("components", [])}
    material_ids = {item.get("id") for item in document.get("materials", [])}
    constraint_ids = {item.get("id") for item in document.get("constraints", [])}

    def require_refs(refs: list[Any], path: str, allowed: set[str] = known_ids) -> None:
        for index, reference in enumerate(refs):
            if isinstance(reference, str) and reference not in allowed:
                errors.append(f"{path}/{index}: dangling reference {reference}")

    for collection in ("requirements", "components", "materials", "constraints", "assumptions"):
        for index, entity in enumerate(document.get(collection, [])):
            require_refs(
                entity.get("provenanceIds", []),
                f"/{collection}/{index}/provenanceIds",
                provenance_ids,
            )
    for index, component in enumerate(document.get("components", [])):
        material_id = component.get("materialId")
        if material_id is not None:
            require_refs([material_id], f"/components/{index}/material", material_ids)
    for index, interface in enumerate(document.get("interfaces", [])):
        require_refs(
            interface.get("participantIds", []),
            f"/interfaces/{index}/participantIds",
            component_ids,
        )
    for index, relationship in enumerate(document.get("relationships", [])):
        require_refs(
            [relationship.get("sourceId"), relationship.get("targetId")],
            f"/relationships/{index}/endpoints",
        )
        require_refs(
            relationship.get("constraintIds", []),
            f"/relationships/{index}/constraintIds",
            constraint_ids,
        )
    for index, process in enumerate(document.get("manufacturing", [])):
        require_refs(
            process.get("componentIds", []),
            f"/manufacturing/{index}/componentIds",
            component_ids,
        )
    for collection in ("constraints",):
        for index, entity in enumerate(document.get(collection, [])):
            require_refs(entity.get("targetIds", []), f"/{collection}/{index}/targetIds")
    for collection in ("assumptions", "unknowns", "provenance"):
        for index, entity in enumerate(document.get(collection, [])):
            subject_id = entity.get("subjectId")
            require_refs([subject_id], f"/{collection}/{index}/subject")

    for component_index, component in enumerate(document.get("components", [])):
        for measurement_index, measurement in enumerate(component.get("dimensions", [])):
            errors.extend(
                _measurement_errors(
                    measurement,
                    f"/components/{component_index}/dimensions/{measurement_index}",
                )
            )
    for material_index, material in enumerate(document.get("materials", [])):
        for property_index, measurement in enumerate(material.get("properties", [])):
            errors.extend(
                _measurement_errors(
                    measurement,
                    f"/materials/{material_index}/properties/{property_index}",
                )
            )
    for constraint_index, constraint in enumerate(document.get("constraints", [])):
        if "measurement" in constraint:
            errors.extend(
                _measurement_errors(
                    constraint["measurement"],
                    f"/constraints/{constraint_index}/measurement",
                )
            )

    for index, record in enumerate(document.get("provenance", [])):
        recorded_at = record.get("recordedAt")
        if isinstance(recorded_at, str):
            try:
                parsed = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    raise ValueError("timezone is required")
            except ValueError:
                errors.append(f"/provenance/{index}/recordedAt: invalid RFC 3339 date-time")

    if errors:
        raise ContractValidationError(sorted(set(errors)))
