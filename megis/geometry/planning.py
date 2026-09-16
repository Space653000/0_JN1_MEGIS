"""Translate validated Engineering IR into kernel-neutral geometry plans."""

from __future__ import annotations

from typing import Any

from megis.contracts import ContractValidationError, validate_engineering_ir

from .contracts import (
    BoxSpec,
    GeometryContractError,
    GeometryErrorCode,
    GeometryPlan,
)


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
    return GeometryPlan(
        plan_id=f"PLAN-{document['designId']}-{document['revision']}-BASE",
        design_id=document["designId"],
        revision=document["revision"],
        coordinate_axes=(axes["x"], axes["y"], axes["z"]),
        operations=(
            BoxSpec(
                operation_id="OP-FIXTURE-BASE-BOX",
                component_id=base["id"],
                width_mm=_nominal_mm(base, "width"),
                depth_mm=_nominal_mm(base, "depth"),
                height_mm=_nominal_mm(base, "height"),
            ),
        ),
    )
