"""Translate validated Engineering IR into kernel-neutral geometry plans."""

from __future__ import annotations

from typing import Any

from megis.contracts import ContractValidationError, validate_engineering_ir

from .contracts import (
    BoxSpec,
    FixtureAssemblyPlan,
    FixtureAssemblySpec,
    GeometryContractError,
    GeometryErrorCode,
    GeometryPlan,
)
from megis.envelope import check_within_envelope


# Transitional values for the v2 Reference Fixture slice. They are deliberately
# isolated here so V3C/G1-REQ-001 can replace them with researched requirement
# data without changing the adapter contract.
_REFERENCE_ASSEMBLY_DEFAULTS = {
    "cover_thickness_mm": 2.0,
    "pcb_width_mm": 60.0,
    "pcb_depth_mm": 40.0,
    "pcb_thickness_mm": 1.6,
    "pcb_bottom_z_mm": 6.0,
    "usb_cutout_width_mm": 10.0,
    "usb_cutout_height_mm": 4.0,
    "usb_cutout_bottom_z_mm": 6.0,
    "fastener_diameter_mm": 3.0,
    "clearance_hole_diameter_mm": 3.4,
    "counterbore_diameter_mm": 6.5,
    "counterbore_depth_mm": 1.2,
    "fastener_edge_inset_mm": 6.0,
    "fastener_count": 4,
}


def _nominal_mm(component: dict[str, Any], name: str) -> float:
    matches = [item for item in component["dimensions"] if item["name"] == name]
    if len(matches) != 1:
        raise GeometryContractError(
            GeometryErrorCode.INVALID_DIMENSION,
            f"{component['id']} requires exactly one {name!r} dimension",
        )
    measurement = matches[0]
    quantity = measurement["quantity"]
    value = quantity.get("nominal")
    if measurement["dimension"] != "length" or quantity["unit"] != "mm":
        raise GeometryContractError(
            GeometryErrorCode.INVALID_DIMENSION,
            f"{component['id']} {name!r} must use length/mm",
        )
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise GeometryContractError(
            GeometryErrorCode.INVALID_DIMENSION,
            f"{component['id']} {name!r} requires a positive nominal value",
        )
    return float(value)


def plan_fixture_base(document: dict[str, Any]) -> GeometryPlan:
    """Create the first fixture-base plan from a validated golden IR document."""

    try:
        validate_engineering_ir(document)
    except ContractValidationError as error:
        raise GeometryContractError(GeometryErrorCode.INVALID_IR, str(error)) from error

    bases = [item for item in document["components"] if item["componentType"] == "fixture_base"]
    if len(bases) != 1:
        raise GeometryContractError(
            GeometryErrorCode.INVALID_IR,
            "Engineering IR requires exactly one fixture_base component",
        )
    base = bases[0]
    axes = document["coordinateSystem"]["axes"]
    width_mm = _nominal_mm(base, "width")
    depth_mm = _nominal_mm(base, "depth")
    height_mm = _nominal_mm(base, "height")
    # Invariant 18: out-of-envelope parts surface MEGIS-ENV-001 instead of clamping.
    check_within_envelope(width_mm, depth_mm, height_mm, correlation_id=document["designId"])
    return GeometryPlan(
        plan_id=f"PLAN-{document['designId']}-{document['revision']}-BASE",
        design_id=document["designId"],
        revision=document["revision"],
        coordinate_axes=(axes["x"], axes["y"], axes["z"]),
        operations=(
            BoxSpec(
                operation_id="OP-FIXTURE-BASE-BOX",
                component_id=base["id"],
                width_mm=width_mm,
                depth_mm=depth_mm,
                height_mm=height_mm,
            ),
        ),
    )


def _one_component(document: dict[str, Any], component_type: str) -> dict[str, Any]:
    matches = [
        item for item in document["components"] if item["componentType"] == component_type
    ]
    if len(matches) != 1:
        raise GeometryContractError(
            GeometryErrorCode.INVALID_IR,
            f"Engineering IR requires exactly one {component_type} component",
        )
    return matches[0]


def _minimum_wall_mm(document: dict[str, Any]) -> float:
    matches = [
        item
        for item in document["constraints"]
        if item["constraintType"] == "wall"
        and item.get("measurement", {}).get("name") == "minimum wall"
    ]
    if len(matches) != 1:
        raise GeometryContractError(
            GeometryErrorCode.INVALID_DIMENSION,
            "Reference Fixture requires exactly one minimum wall constraint",
        )
    quantity = matches[0]["measurement"]["quantity"]
    value = quantity.get("min")
    if quantity.get("unit") != "mm" or not isinstance(value, (int, float)) or value <= 0:
        raise GeometryContractError(
            GeometryErrorCode.INVALID_DIMENSION,
            "Reference Fixture minimum wall must be a positive length/mm value",
        )
    return float(value)


def plan_fixture_assembly(document: dict[str, Any]) -> FixtureAssemblyPlan:
    """Plan the fixed cover, mounting, PCB envelope and USB-C cutout slice."""

    try:
        validate_engineering_ir(document)
    except ContractValidationError as error:
        raise GeometryContractError(GeometryErrorCode.INVALID_IR, str(error)) from error

    base = _one_component(document, "fixture_base")
    cover = _one_component(document, "cover")
    pcb = _one_component(document, "pcb")
    wall_mm = _minimum_wall_mm(document)
    width_mm = _nominal_mm(base, "width")
    depth_mm = _nominal_mm(base, "depth")
    height_mm = _nominal_mm(base, "height")
    defaults = _REFERENCE_ASSEMBLY_DEFAULTS

    # Invariant 18: an out-of-envelope assembly surfaces MEGIS-ENV-001, not a clamp.
    check_within_envelope(width_mm, depth_mm, height_mm, correlation_id=document["designId"])

    if 2 * wall_mm >= min(width_mm, depth_mm) or wall_mm >= height_mm:
        raise GeometryContractError(
            GeometryErrorCode.INVALID_DIMENSION,
            "Minimum wall leaves no positive fixture cavity",
        )
    if defaults["counterbore_depth_mm"] >= defaults["cover_thickness_mm"]:
        raise GeometryContractError(
            GeometryErrorCode.INVALID_DIMENSION,
            "Counterbore depth must be smaller than cover thickness",
        )

    axes = document["coordinateSystem"]["axes"]
    return FixtureAssemblyPlan(
        plan_id=f"PLAN-{document['designId']}-{document['revision']}-ASSEMBLY",
        design_id=document["designId"],
        revision=document["revision"],
        coordinate_axes=(axes["x"], axes["y"], axes["z"]),
        specification=FixtureAssemblySpec(
            base_component_id=base["id"],
            cover_component_id=cover["id"],
            pcb_component_id=pcb["id"],
            outer_width_mm=width_mm,
            outer_depth_mm=depth_mm,
            base_height_mm=height_mm,
            wall_mm=wall_mm,
            **defaults,
        ),
    )
