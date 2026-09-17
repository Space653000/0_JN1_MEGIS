"""Geometry application service that depends only on the backend protocol."""

from __future__ import annotations

from math import isfinite
from typing import Any

from .contracts import (
    FixtureAssemblyBuildResult,
    GeometryBackend,
    GeometryBuildResult,
    GeometryContractError,
    GeometryErrorCode,
    GeometryOperation,
)
from .planning import plan_fixture_assembly, plan_fixture_base


def build_fixture_base(
    document: dict[str, Any],
    backend: GeometryBackend,
) -> GeometryBuildResult:
    """Plan from IR, negotiate capability, then verify the adapter response."""

    plan = plan_fixture_base(document)
    capabilities = backend.capabilities()
    if GeometryOperation.BOX not in capabilities.supported_operations:
        raise GeometryContractError(
            GeometryErrorCode.UNSUPPORTED_OPERATION,
            f"Backend {capabilities.backend_id} does not support box",
        )
    result = backend.build(plan)
    expected_components = tuple(operation.component_id for operation in plan.operations)
    if (
        result.plan_id != plan.plan_id
        or result.backend_id != capabilities.backend_id
        or result.backend_version != capabilities.backend_version
        or result.component_ids != expected_components
        or result.solid_count < 1
        or not result.model_token
        or not result.valid
        or not isfinite(result.volume_mm3)
        or result.volume_mm3 <= 0
        or min(
            result.bounding_box_mm.width,
            result.bounding_box_mm.depth,
            result.bounding_box_mm.height,
        ) <= 0
    ):
        raise GeometryContractError(
            GeometryErrorCode.BACKEND_CONTRACT_VIOLATION,
            "Backend result does not match the negotiated plan and capability identity",
        )
    return result


def build_fixture_assembly(
    document: dict[str, Any],
    backend: GeometryBackend,
) -> FixtureAssemblyBuildResult:
    """Build and validate the fixed Reference Fixture assembly slice."""

    plan = plan_fixture_assembly(document)
    capabilities = backend.capabilities()
    required = {
        GeometryOperation.SHELL,
        GeometryOperation.PLATE,
        GeometryOperation.HOLE,
        GeometryOperation.CUTOUT,
        GeometryOperation.COUNTERBORE,
        GeometryOperation.FASTENER,
        GeometryOperation.PCB_ENVELOPE,
        GeometryOperation.MOUNT,
    }
    missing = required - capabilities.supported_operations
    if missing:
        names = ", ".join(sorted(item.value for item in missing))
        raise GeometryContractError(
            GeometryErrorCode.UNSUPPORTED_OPERATION,
            f"Backend {capabilities.backend_id} lacks assembly operations: {names}",
        )

    result = backend.build_fixture_assembly(plan)
    spec = plan.specification
    expected_components = (
        spec.base_component_id,
        spec.cover_component_id,
        spec.pcb_component_id,
    )
    numeric_values = (
        result.radial_fastener_clearance_mm,
        result.pcb_side_clearance_mm,
        result.pcb_top_clearance_mm,
        result.unintended_interference_volume_mm3,
    )
    if (
        result.plan_id != plan.plan_id
        or result.backend_id != capabilities.backend_id
        or result.backend_version != capabilities.backend_version
        or result.component_ids != expected_components
        or not result.valid
        or not result.usb_cutout_open
        or result.solid_count != 3 + spec.fastener_count
        or len(result.fastener_model_tokens) != spec.fastener_count
        or not all(
            (
                result.base_model_token,
                result.cover_model_token,
                result.pcb_envelope_model_token,
                *result.fastener_model_tokens,
            )
        )
        or not all(isfinite(value) for value in numeric_values)
        or min(
            result.radial_fastener_clearance_mm,
            result.pcb_side_clearance_mm,
            result.pcb_top_clearance_mm,
        )
        <= 0
        or result.unintended_interference_volume_mm3 > 1e-7
    ):
        raise GeometryContractError(
            GeometryErrorCode.BACKEND_CONTRACT_VIOLATION,
            "Backend assembly result violates required identity, clearance or validity",
        )
    return result
