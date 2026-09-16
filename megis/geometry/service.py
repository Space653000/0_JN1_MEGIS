"""Geometry application service that depends only on the backend protocol."""

from __future__ import annotations

from math import isfinite
from typing import Any

from .contracts import (
    GeometryBackend,
    GeometryBuildResult,
    GeometryContractError,
    GeometryErrorCode,
    GeometryOperation,
)
from .planning import plan_fixture_base


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
