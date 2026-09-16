"""Kernel-neutral geometry capability contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable


class GeometryOperation(StrEnum):
    BOX = "box"
    PLATE = "plate"
    SHELL = "shell"
    HOLE = "hole"
    POCKET = "pocket"
    BOSS = "boss"
    CUTOUT = "cutout"
    FILLET = "fillet"
    CHAMFER = "chamfer"
    MOUNT = "mount"


class GeometryErrorCode(StrEnum):
    INVALID_IR = "INVALID_IR"
    UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"
    INVALID_DIMENSION = "INVALID_DIMENSION"
    BACKEND_CONTRACT_VIOLATION = "BACKEND_CONTRACT_VIOLATION"


class GeometryContractError(ValueError):
    """Stable geometry-boundary failure with a machine-readable code."""

    def __init__(self, code: GeometryErrorCode, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class GeometryCapabilities:
    backend_id: str
    backend_version: str
    supported_operations: frozenset[GeometryOperation]
    export_formats: frozenset[str]
    deterministic: bool


@dataclass(frozen=True)
class BoxSpec:
    operation_id: str
    component_id: str
    width_mm: float
    depth_mm: float
    height_mm: float


@dataclass(frozen=True)
class GeometryPlan:
    plan_id: str
    design_id: str
    revision: str
    coordinate_axes: tuple[str, str, str]
    operations: tuple[BoxSpec, ...]


@dataclass(frozen=True)
class BoundingBoxMm:
    width: float
    depth: float
    height: float


@dataclass(frozen=True)
class GeometryBuildResult:
    plan_id: str
    component_ids: tuple[str, ...]
    backend_id: str
    backend_version: str
    model_token: str
    solid_count: int
    bounding_box_mm: BoundingBoxMm
    volume_mm3: float
    valid: bool


@runtime_checkable
class GeometryBackend(Protocol):
    """Replaceable adapter seam; no CAD-kernel type crosses this boundary."""

    def capabilities(self) -> GeometryCapabilities: ...

    def build(self, plan: GeometryPlan) -> GeometryBuildResult: ...
