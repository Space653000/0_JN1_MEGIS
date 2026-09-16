"""Kernel-neutral geometry planning and adapter contracts."""

from .contracts import (
    BoundingBoxMm,
    BoxSpec,
    GeometryBackend,
    GeometryBuildResult,
    GeometryCapabilities,
    GeometryContractError,
    GeometryErrorCode,
    GeometryOperation,
    GeometryPlan,
)
from .planning import plan_fixture_base
from .service import build_fixture_base

__all__ = [
    "BoundingBoxMm",
    "BoxSpec",
    "GeometryBackend",
    "GeometryBuildResult",
    "GeometryCapabilities",
    "GeometryContractError",
    "GeometryErrorCode",
    "GeometryOperation",
    "GeometryPlan",
    "build_fixture_base",
    "plan_fixture_base",
]
