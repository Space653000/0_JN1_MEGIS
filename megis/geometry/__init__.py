"""Kernel-neutral geometry planning and adapter contracts."""

from .contracts import (
    BoundingBoxMm,
    BoxSpec,
    FixtureAssemblyBuildResult,
    FixtureAssemblyPlan,
    FixtureAssemblySpec,
    GeometryBackend,
    GeometryBuildResult,
    GeometryCapabilities,
    GeometryContractError,
    GeometryErrorCode,
    GeometryOperation,
    GeometryPlan,
)
from .planning import plan_fixture_assembly, plan_fixture_base
from .service import build_fixture_assembly, build_fixture_base

__all__ = [
    "BoundingBoxMm",
    "BoxSpec",
    "FixtureAssemblyBuildResult",
    "FixtureAssemblyPlan",
    "FixtureAssemblySpec",
    "GeometryBackend",
    "GeometryBuildResult",
    "GeometryCapabilities",
    "GeometryContractError",
    "GeometryErrorCode",
    "GeometryOperation",
    "GeometryPlan",
    "build_fixture_assembly",
    "build_fixture_base",
    "plan_fixture_assembly",
    "plan_fixture_base",
]
