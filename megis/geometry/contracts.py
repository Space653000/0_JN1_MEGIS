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
    COUNTERBORE = "counterbore"
    FASTENER = "fastener"
    PCB_ENVELOPE = "pcb_envelope"


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
class FixtureAssemblySpec:
    """Kernel-neutral dimensions for the fixed Reference Fixture assembly slice."""

    base_component_id: str
    cover_component_id: str
    pcb_component_id: str
    outer_width_mm: float
    outer_depth_mm: float
    base_height_mm: float
    wall_mm: float
    cover_thickness_mm: float
    pcb_width_mm: float
    pcb_depth_mm: float
    pcb_thickness_mm: float
    pcb_bottom_z_mm: float
    usb_cutout_width_mm: float
    usb_cutout_height_mm: float
    usb_cutout_bottom_z_mm: float
    fastener_diameter_mm: float
    clearance_hole_diameter_mm: float
    counterbore_diameter_mm: float
    counterbore_depth_mm: float
    fastener_edge_inset_mm: float
    fastener_count: int


@dataclass(frozen=True)
class GeometryPlan:
    plan_id: str
    design_id: str
    revision: str
    coordinate_axes: tuple[str, str, str]
    operations: tuple[BoxSpec, ...]


@dataclass(frozen=True)
class FixtureAssemblyPlan:
    plan_id: str
    design_id: str
    revision: str
    coordinate_axes: tuple[str, str, str]
    specification: FixtureAssemblySpec


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


@dataclass(frozen=True)
class FixtureAssemblyBuildResult:
    plan_id: str
    component_ids: tuple[str, ...]
    backend_id: str
    backend_version: str
    base_model_token: str
    cover_model_token: str
    pcb_envelope_model_token: str
    fastener_model_tokens: tuple[str, ...]
    solid_count: int
    valid: bool
    usb_cutout_open: bool
    radial_fastener_clearance_mm: float
    pcb_side_clearance_mm: float
    pcb_top_clearance_mm: float
    unintended_interference_volume_mm3: float


@runtime_checkable
class GeometryBackend(Protocol):
    """Replaceable adapter seam; no CAD-kernel type crosses this boundary."""

    def capabilities(self) -> GeometryCapabilities: ...

    def build(self, plan: GeometryPlan) -> GeometryBuildResult: ...

    def build_fixture_assembly(
        self, plan: FixtureAssemblyPlan
    ) -> FixtureAssemblyBuildResult: ...
