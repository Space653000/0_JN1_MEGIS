"""Module composition graph operations (G4-MOD-002).

Implements the composition behaviours required by blueprint section 12:

- add: dragging a module into the fixture graph materialises the module as an
  IR component plus its relationship and derives only *proven* engineering
  constraints (mount / clearance / opening / fastener).  A value that is
  required for a constraint but missing or unproven is never invented: the
  engine records an ``unsafeToDefault`` unknown and blocks that constraint
  kind instead.
- remove: removing a module clears every dependent interface, relationship,
  constraint, unknown and provenance entry that points at it.  Cleared
  dependent constraints are explicitly listed in the removal report so the
  decision is auditable rather than silent.
- version: every composed component records ``module:<id>@<version>`` in its
  provenance.  Recomposing a module whose pinned version differs never
  silently upgrades: without ``allow_upgrade`` the run stays pinned to the
  recorded version and reports ``upgrade_blocked``.

The engines operate on a validated V2 Engineering IR document and consume a
v3 Module document plus a v3 Relationship document (the assembly intent).
All failure branches run before any graph mutation, and every report and
error list is deterministic and sorted.  ``compose_module`` and
``decompose_module`` mutate the IR document in place; the returned result
reports exactly what changed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from megis.contracts import (
    ContractValidationError,
    validate_engineering_ir,
)
from megis.module.schema import ModuleValidationError, validate_module_document
from megis.relationship.schema import RelationshipValidationError, validate_relationship

DEFAULT_RECORDED_AT = "2026-09-22T00:00:00Z"
MODULE_MARKER_PREFIX = "module:"

# Composition intents closed over the G4-GRF-001 relationship vocabulary.  The
# other three vocabulary types (aligns / covers / removable_along) describe
# positioning or access semantics that need geometry solvers and are not
# materialisable as constraints at this stage.
COMPOSABLE_TYPES = ("contains", "mounts_to", "fastens", "opens_through", "clears")

# Closed composition recipes reusing the G4-GRF-001 relationship vocabulary.
# Each recipe maps a relationship type onto the IR relationshipType, an
# optional IR interfaceType, the derived constraint kind/type, and the proven
# parameters that may produce a constraint.  ``clears`` is a distance bound,
# not an interface, so it carries no interface_type.  ``contains`` carries no
# numeric constraint at this level.
_CONSTRAINT_RECIPES: dict[str, dict[str, Any]] = {
    "contains": {
        "ir_relationship_type": "contains",
        "interface_type": None,
        "constraint_kind": None,
        "constraint_type": None,
        "parameters": (),
    },
    "mounts_to": {
        "ir_relationship_type": "mounts_to",
        "interface_type": "mount",
        "constraint_kind": "mount",
        "constraint_type": "interface",
        "parameters": ("engagement_length_mm", "hole_alignment_tolerance_mm"),
    },
    "fastens": {
        "ir_relationship_type": "fastened_by",
        "interface_type": "mount",
        "constraint_kind": "fastener",
        "constraint_type": "interface",
        "parameters": ("screw_length_mm",),
    },
    "opens_through": {
        "ir_relationship_type": "connects_to",
        "interface_type": "opening",
        "constraint_kind": "opening",
        "constraint_type": "clearance",
        "parameters": ("clearance_gap_mm",),
    },
    "clears": {
        "ir_relationship_type": "clearance_to",
        "interface_type": None,
        "constraint_kind": "clearance",
        "constraint_type": "clearance",
        "parameters": ("minimum_distance_mm",),
    },
}

_CONSTRAINT_LABELS: dict[str, str] = {
    "mount": "mount engagement",
    "fastener": "fastener length",
    "opening": "opening clearance",
    "clearance": "minimum clearance",
}

_ASSEMBLY_EXPRESSIONS: dict[str, str] = {
    "mount": "proven engagement length with proven hole alignment tolerance",
    "fastener": "proven screw length",
    "opening": "proven clearance gap between interface envelope and wall opening",
    "clearance": "proven minimum distance between the composed entities",
}


class CompositionValidationError(ValueError):
    """A deterministic list of module-composition contract violations."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def _slug(value: str) -> str:
    """Deterministic uppercase entity-id slug from an arbitrary module token."""
    return re.sub(r"[^A-Z0-9]+", "-", value.upper()).strip("-")


def _component_id_for(module_id: str) -> str:
    """Derive the default IR component id for a ``mod.<name>`` module id."""
    suffix = module_id.split(".", 1)[-1]
    return f"COMP-{_slug(suffix)}"


def _interface_id_for(component_id: str, target_id: str, kind: str) -> str:
    return f"INT-{component_id}-{target_id}-{_slug(kind)}"


def _relationship_id_for(component_id: str, target_id: str, label: str) -> str:
    """Relationship id with a deterministic singular-or-plural suffix."""
    stem = _slug(label)
    if not stem.endswith("S"):
        stem += "S"
    return f"REL-{component_id}-{target_id}-{stem}"


def _constraint_id_for(component_id: str, kind: str) -> str:
    return f"CON-{component_id}-{_slug(kind)}"


def _dimension_id_for(component_id: str, kind: str) -> str:
    return f"DIM-{component_id}-{_slug(kind)}"


def _unknown_id_for(component_id: str, kind: str) -> str:
    return f"UNK-{component_id}-{_slug(kind)}"


def _provenance_id_for(component_id: str, label: str) -> str:
    return f"PROV-{component_id}-{_slug(label)}"


@dataclass(frozen=True)
class CompositionResult:
    """The auditable effect of one add-module (or pinned re-compose) operation."""

    changed: bool
    added_component_ids: tuple[str, ...] = ()
    added_interface_ids: tuple[str, ...] = ()
    added_relationship_ids: tuple[str, ...] = ()
    added_constraint_ids: tuple[str, ...] = ()
    added_unknown_ids: tuple[str, ...] = ()
    blocked_constraint_kinds: tuple[str, ...] = ()
    fabricated_values_used: bool = False
    upgrade_blocked: bool = False
    pinned_modules: tuple[tuple[str, str], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed": self.changed,
            "addedComponentIds": list(self.added_component_ids),
            "addedInterfaceIds": list(self.added_interface_ids),
            "addedRelationshipIds": list(self.added_relationship_ids),
            "addedConstraintIds": list(self.added_constraint_ids),
            "addedUnknownIds": list(self.added_unknown_ids),
            "blockedConstraintKinds": list(self.blocked_constraint_kinds),
            "fabricatedValuesUsed": self.fabricated_values_used,
            "upgradeBlocked": self.upgrade_blocked,
            "pinnedModules": [list(pair) for pair in self.pinned_modules],
        }


@dataclass(frozen=True)
class DecompositionResult:
    """The auditable effect of one remove-module operation."""

    changed: bool
    removed_component_ids: tuple[str, ...] = ()
    removed_interface_ids: tuple[str, ...] = ()
    removed_relationship_ids: tuple[str, ...] = ()
    removed_constraint_ids: tuple[str, ...] = ()
    removed_unknown_ids: tuple[str, ...] = ()
    marked_constraint_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed": self.changed,
            "removedComponentIds": list(self.removed_component_ids),
            "removedInterfaceIds": list(self.removed_interface_ids),
            "removedRelationshipIds": list(self.removed_relationship_ids),
            "removedConstraintIds": list(self.removed_constraint_ids),
            "removedUnknownIds": list(self.removed_unknown_ids),
            "markedConstraintIds": list(self.marked_constraint_ids),
        }


def _module_marker(module_id: str, version: str) -> str:
    return f"{MODULE_MARKER_PREFIX}{module_id}@{version}"


def _module_marker_prefix(module_id: str) -> str:
    return f"{MODULE_MARKER_PREFIX}{module_id}@"


def _flatten_validation(source: str, errors: list[str], prefix: str) -> None:
    """Raise one aggregate CompositionValidationError from a failing validator."""
    raise CompositionValidationError(
        sorted(set(f"{source} {prefix} {message}" for message in errors))
    )


def _validate_inputs(
    ir: dict[str, Any],
    module: dict[str, Any] | None,
    relationship: dict[str, Any] | None,
) -> None:
    """Validate all documents into one deterministic CompositionValidationError."""
    try:
        validate_engineering_ir(ir)
    except ContractValidationError as error:
        _flatten_validation("engineering-ir:", error.errors, "")
    if module is not None:
        try:
            validate_module_document(module)
        except ModuleValidationError as error:
            _flatten_validation("module:", error.errors, "")
    if relationship is not None:
        try:
            validate_relationship(relationship)
        except RelationshipValidationError as error:
            _flatten_validation("relationship:", error.errors, "")


def _parameter_value(
    relationship: dict[str, Any], name: str
) -> tuple[Any, bool]:
    """Return ``(value, proven)`` for a relationship parameter.

    A parameter is proven only when its entry carries a non-empty provenance
    list.  A missing or unproven value is never defaulted to an invented
    engineering number.
    """
    parameters = relationship.get("parameters", {})
    entry = parameters.get(name)
    if not isinstance(entry, dict) or "value" not in entry:
        return None, False
    provenance = entry.get("provenance", [])
    if not isinstance(provenance, list) or not provenance:
        return entry["value"], False
    return entry["value"], True


def _existing_component_ids(ir: dict[str, Any]) -> set[str]:
    return {component["id"] for component in ir.get("components", [])}


def module_component_ids(ir: dict[str, Any], module_id: str) -> tuple[str, ...]:
    """Return the IR component ids composed from ``module_id``, sorted."""
    prefix = _module_marker_prefix(module_id)
    provenance_by_id = {item["id"]: item for item in ir.get("provenance", [])}
    matches: set[str] = set()
    for component in ir.get("components", []):
        for provenance_id in component.get("provenanceIds", []):
            record = provenance_by_id.get(provenance_id)
            if record and isinstance(record.get("sourceRef"), str):
                if record["sourceRef"].startswith(prefix):
                    matches.add(component["id"])
    return tuple(sorted(matches))


def pinned_module_version(ir: dict[str, Any], module_id: str) -> str | None:
    """Return the version pinned in the IR for a module, or None when absent.

    The pinned version comes only from an explicit ``module:<id>@<version>``
    provenance record, so a later module version can never silently replace an
    existing Design Run.
    """
    prefix = _module_marker_prefix(module_id)
    for record in ir.get("provenance", []):
        source_ref = record.get("sourceRef")
        if isinstance(source_ref, str) and source_ref.startswith(prefix):
            return source_ref[len(prefix):]
    return None


def _module_id_for_provenance(ir: dict[str, Any], component_id: str) -> str:
    """Return the module id recorded on a composed component, or ''."""
    provenance_by_id = {item["id"]: item for item in ir.get("provenance", [])}
    for component in ir.get("components", []):
        if component["id"] != component_id:
            continue
        for provenance_id in component.get("provenanceIds", []):
            record = provenance_by_id.get(provenance_id)
            if record and isinstance(record.get("sourceRef"), str):
                if record["sourceRef"].startswith(MODULE_MARKER_PREFIX):
                    body = record["sourceRef"][len(MODULE_MARKER_PREFIX):]
                    return body.split("@", 1)[0]
    return ""


def _add_provenance(
    ir: dict[str, Any],
    provenance_id: str,
    subject_id: str,
    field: str,
    source_ref: str,
    recorded_at: str,
) -> None:
    ir["provenance"].append(
        {
            "id": provenance_id,
            "subjectId": subject_id,
            "field": field,
            "source": "derived",
            "sourceRef": source_ref,
            "recordedAt": recorded_at,
        }
    )


def _make_quantity(quantity_id: str, value: float, tolerance: float) -> dict[str, Any]:
    """A strictly truthful quantity: nominal is the proven value.

    ``tolerance`` is 0.0 unless a proven tolerance is supplied; the engine
    never invents a ``max`` because deriving an upper bound would be a
    fabricated engineering value.
    """
    return {"id": quantity_id, "unit": "mm", "nominal": value, "tolerance": tolerance}


def _make_constraint(
    ir: dict[str, Any],
    component_id: str,
    target_id: str,
    kind: str,
    constraint_type: str,
    value: float,
    tolerance: float,
    provenance_id: str,
) -> dict[str, Any]:
    return {
        "id": _constraint_id_for(component_id, kind),
        "constraintType": constraint_type,
        "severity": "hard",
        "targetIds": sorted({component_id, target_id}),
        "measurement": {
            "name": _CONSTRAINT_LABELS[kind],
            "dimension": "length",
            "quantity": _make_quantity(
                _dimension_id_for(component_id, kind), value, tolerance
            ),
        },
        "expression": _ASSEMBLY_EXPRESSIONS[kind],
        "provenanceIds": [provenance_id],
    }


def _use_recipe_value(
    ir: dict[str, Any],
    relationship: dict[str, Any],
    recipe: dict[str, Any],
    component_id: str,
    target: str,
    source_ref: str,
    recorded_at: str,
) -> dict[str, Any]:
    """Derive a constraint from proven recipe parameters without invention.

    Returns a constraint dict when every required parameter is proven and
    numerically usable; otherwise appends an ``unsafeToDefault`` unknown and
    returns None.  Fabricated values are never emitted.
    """
    kind = recipe["constraint_kind"]
    values: list[float] = []
    missing: list[str] = []
    for name in recipe["parameters"]:
        value, proven = _parameter_value(relationship, name)
        if not proven:
            missing.append(name)
            continue
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            missing.append(name)
            continue
        values.append(float(value))
    if missing:
        unknown_id = _unknown_id_for(component_id, kind)
        ir["unknowns"].append(
            {
                "id": unknown_id,
                "subjectId": component_id,
                "field": f"/constraints/{kind}",
                "unsafeToDefault": True,
                "question": (
                    f"Proven value missing for {', '.join(sorted(missing))}; "
                    f"composition cannot derive the {kind} constraint."
                ),
            }
        )
        return {"created": False, "unknown_id": unknown_id}

    provenance_id = _provenance_id_for(component_id, f"CON-{kind}")
    _add_provenance(
        ir,
        provenance_id,
        component_id,
        f"/constraints/{kind}",
        source_ref,
        recorded_at,
    )
    tolerance = values[1] if len(values) > 1 else 0.0
    constraint = _make_constraint(
        ir,
        component_id,
        target,
        kind,
        recipe["constraint_type"],
        values[0],
        tolerance,
        provenance_id,
    )
    ir["constraints"].append(constraint)
    return {"created": True, "constraint": constraint}


def _materialize_relationship_and_constraints(
    ir: dict[str, Any],
    module: dict[str, Any],
    relationship: dict[str, Any],
    component_id: str,
    recorded_at: str,
) -> dict[str, Any]:
    """Append the module's interfaces, relationship and derived constraints."""
    module_id = module["module_id"]
    version = module["version"]
    source_ref = _module_marker(module_id, version)
    relationship_type = relationship["type"]
    recipe = _CONSTRAINT_RECIPES[relationship_type]
    target = relationship["target"]

    added_interfaces: list[str] = []
    added_constraints: list[str] = []
    added_unknowns: list[str] = []
    blocked_kinds: list[str] = []

    interface_type = recipe["interface_type"]
    if interface_type is not None:
        interface_id = _interface_id_for(component_id, target, interface_type)
        provenance_id = _provenance_id_for(component_id, f"INT-{interface_type}")
        _add_provenance(
            ir,
            provenance_id,
            component_id,
            f"/interfaces/{interface_id}",
            source_ref,
            recorded_at,
        )
        ir["interfaces"].append(
            {
                "id": interface_id,
                "name": f"{interface_type} interface",
                "interfaceType": interface_type,
                "participantIds": sorted({component_id, target}),
            }
        )
        added_interfaces.append(interface_id)

    kind = recipe["constraint_kind"]
    if kind is not None:
        derivation = _use_recipe_value(
            ir,
            relationship,
            recipe,
            component_id,
            target,
            source_ref,
            recorded_at,
        )
        if derivation["created"]:
            constraint = derivation["constraint"]
            added_constraints.append(constraint["id"])
        else:
            blocked_kinds.append(kind)
            added_unknowns.append(derivation["unknown_id"])

    label = kind if kind is not None else relationship_type
    relationship_id = _relationship_id_for(component_id, target, label)
    provenance_id = _provenance_id_for(component_id, f"REL-{label}")
    _add_provenance(
        ir,
        provenance_id,
        component_id,
        f"/relationships/{relationship_id}",
        source_ref,
        recorded_at,
    )
    ir["relationships"].append(
        {
            "id": relationship_id,
            "relationshipType": recipe["ir_relationship_type"],
            "sourceId": component_id,
            "targetId": target,
            "constraintIds": sorted(added_constraints),
        }
    )
    return {
        "addedInterfaces": added_interfaces,
        "addedConstraints": added_constraints,
        "addedUnknowns": added_unknowns,
        "blockedKinds": blocked_kinds,
    }


def _add_component(
    ir: dict[str, Any],
    module: dict[str, Any],
    component_id: str,
    recorded_at: str,
) -> None:
    """Materialise the module as a new IR component with its version pin."""
    module_id = module["module_id"]
    provenance_id = _provenance_id_for(component_id, "MODULE")
    _add_provenance(
        ir,
        provenance_id,
        component_id,
        f"/components/{component_id}",
        _module_marker(module_id, module["version"]),
        recorded_at,
    )
    ir["components"].append(
        {
            "id": component_id,
            "name": module_id,
            "domain": "shared",
            "componentType": module_id.split(".", 1)[-1],
            "dimensions": [],
            "provenanceIds": [provenance_id],
        }
    )


def compose_module(
    ir: dict[str, Any],
    module: dict[str, Any],
    relationship: dict[str, Any],
    *,
    component_id: str | None = None,
    recorded_at: str = DEFAULT_RECORDED_AT,
    allow_upgrade: bool = False,
) -> CompositionResult:
    """Materialise one module plus assembly intent into a validated IR.

    All validation and intent checks run before any graph mutation.  On
    success the IR is mutated in place and the result reports every added
    entity.  Constraints are derived only from proven relationship parameters;
    missing or unproven values produce an ``unsafeToDefault`` unknown and a
    blocked constraint kind.  Recomposing a module id whose recorded version
    differs is pinned by default.
    """
    _validate_inputs(ir, module, relationship)

    module_id = module["module_id"]
    version = module["version"]
    relationship_type = relationship["type"]
    if relationship_type not in _CONSTRAINT_RECIPES:
        raise CompositionValidationError(
            [
                f"/relationship/type: {relationship_type} is not a supported composition intent type"
            ]
        )

    resolved_component_id = component_id or _component_id_for(module_id)
    if relationship.get("source") != resolved_component_id:
        raise CompositionValidationError(
            [
                f"/relationship/source: expected {resolved_component_id} for module {module_id}, got {relationship.get('source')}"
            ]
        )

    existing_ids = _existing_component_ids(ir)
    target = relationship.get("target")
    if (
        not isinstance(target, str)
        or target == resolved_component_id
        or target not in existing_ids
    ):
        raise CompositionValidationError(
            [
                f"/relationship/target: composition target {target} must exist in the IR and differ from the source"
            ]
        )

    pinned = pinned_module_version(ir, module_id)
    if pinned is not None and pinned != version and not allow_upgrade:
        return CompositionResult(
            changed=False,
            upgrade_blocked=True,
            pinned_modules=((module_id, pinned),),
        )

    if pinned is not None and pinned != version:
        for existing_id in module_component_ids(ir, module_id):
            ir = _strip_module_entities(ir, module_id, existing_id)
        pinned = None

    if resolved_component_id in _existing_component_ids(ir):
        owner = _module_id_for_provenance(ir, resolved_component_id)
        if module_id != owner:
            raise CompositionValidationError(
                [
                    f"/components/{resolved_component_id}: component id already exists and is not composed from {module_id}"
                ]
            )
        return CompositionResult(
            changed=False,
            pinned_modules=((module_id, version),),
        )

    _add_component(ir, module, resolved_component_id, recorded_at)
    materialized = _materialize_relationship_and_constraints(
        ir, module, relationship, resolved_component_id, recorded_at
    )
    _validate_inputs(ir, None, None)

    return CompositionResult(
        changed=True,
        added_component_ids=(resolved_component_id,),
        added_interface_ids=tuple(sorted(materialized["addedInterfaces"])),
        added_relationship_ids=tuple(
            sorted(
                [
                    _relationship_id_for(
                        resolved_component_id, target, recipe_label(relationship_type)
                    )
                ]
            )
        ),
        added_constraint_ids=tuple(sorted(materialized["addedConstraints"])),
        added_unknown_ids=tuple(sorted(materialized["addedUnknowns"])),
        blocked_constraint_kinds=tuple(sorted(materialized["blockedKinds"])),
        fabricated_values_used=False,
        pinned_modules=((module_id, version),),
    )


def recipe_label(relationship_type: str) -> str:
    """Return the deterministic relationship suffix label for a composition type."""
    recipe = _CONSTRAINT_RECIPES[relationship_type]
    return (
        recipe["constraint_kind"]
        if recipe["constraint_kind"] is not None
        else relationship_type
    )


def _strip_module_entities(
    ir: dict[str, Any], module_id: str, component_id: str
) -> dict[str, Any]:
    """Remove every module-derived entity for one composed component.

    Relationships, interfaces, constraints, unknowns and provenance entries
    that reference the composed component are dropped.  Everything else is
    preserved unchanged.
    """
    marker = _module_marker_prefix(module_id)

    ir["relationships"] = [
        item
        for item in ir.get("relationships", [])
        if not (item["sourceId"] == component_id or item["targetId"] == component_id)
    ]
    ir["constraints"] = [
        item
        for item in ir.get("constraints", [])
        if component_id not in item.get("targetIds", [])
    ]
    ir["interfaces"] = [
        item
        for item in ir.get("interfaces", [])
        if component_id not in item.get("participantIds", [])
    ]
    ir["unknowns"] = [
        item
        for item in ir.get("unknowns", [])
        if item.get("subjectId") != component_id
    ]
    ir["provenance"] = [
        item
        for item in ir.get("provenance", [])
        if item.get("subjectId") != component_id
        and not str(item.get("sourceRef", "")).startswith(marker)
    ]
    ir["components"] = [
        item
        for item in ir.get("components", [])
        if item["id"] != component_id
    ]
    return ir


def decompose_module(
    ir: dict[str, Any], module_id: str
) -> DecompositionResult:
    """Remove a composed module and every dependent entity from a validated IR.

    Any interface, relationship, constraint, unknown or provenance entry that
    points at a composed component is cleared.  Cleared dependent constraints
    are enumerated in ``marked_constraint_ids`` so the removal decision is
    explicit, never silent.
    """
    _validate_inputs(ir, None, None)

    removed_component_ids = module_component_ids(ir, module_id)
    if not removed_component_ids:
        raise CompositionValidationError(
            [f"/components: unknown module {module_id}; nothing composed to remove"]
        )
    removed_set = set(removed_component_ids)
    marker = _module_marker_prefix(module_id)

    removed_interfaces = [
        item["id"]
        for item in ir.get("interfaces", [])
        if set(item.get("participantIds", [])) & removed_set
    ]
    removed_relationships = [
        item["id"]
        for item in ir.get("relationships", [])
        if item.get("sourceId") in removed_set or item.get("targetId") in removed_set
    ]
    removed_constraints = [
        item["id"]
        for item in ir.get("constraints", [])
        if set(item.get("targetIds", [])) & removed_set
    ]
    removed_unknowns = [
        item["id"]
        for item in ir.get("unknowns", [])
        if item.get("subjectId") in removed_set
    ]
    removed_provenance = [
        item["id"]
        for item in ir.get("provenance", [])
        if item.get("subjectId") in removed_set
        or str(item.get("sourceRef", "")).startswith(marker)
    ]

    removed_interface_set = set(removed_interfaces)
    removed_relationship_set = set(removed_relationships)
    removed_constraint_set = set(removed_constraints)
    removed_unknown_set = set(removed_unknowns)
    removed_provenance_set = set(removed_provenance)

    ir["interfaces"] = [
        item
        for item in ir.get("interfaces", [])
        if item["id"] not in removed_interface_set
    ]
    ir["relationships"] = [
        item
        for item in ir.get("relationships", [])
        if item["id"] not in removed_relationship_set
    ]
    ir["constraints"] = [
        item
        for item in ir.get("constraints", [])
        if item["id"] not in removed_constraint_set
    ]
    ir["unknowns"] = [
        item for item in ir.get("unknowns", []) if item["id"] not in removed_unknown_set
    ]
    ir["provenance"] = [
        item
        for item in ir.get("provenance", [])
        if item["id"] not in removed_provenance_set
    ]
    ir["components"] = [
        item for item in ir.get("components", []) if item["id"] not in removed_set
    ]

    _validate_inputs(ir, None, None)
    return DecompositionResult(
        changed=True,
        removed_component_ids=tuple(sorted(removed_component_ids)),
        removed_interface_ids=tuple(sorted(removed_interfaces)),
        removed_relationship_ids=tuple(sorted(removed_relationships)),
        removed_constraint_ids=tuple(sorted(removed_constraints)),
        removed_unknown_ids=tuple(sorted(removed_unknowns)),
        marked_constraint_ids=tuple(sorted(removed_constraints)),
    )


__all__ = [
    "COMPOSABLE_TYPES",
    "CompositionResult",
    "CompositionValidationError",
    "DecompositionResult",
    "compose_module",
    "decompose_module",
    "module_component_ids",
    "pinned_module_version",
]
