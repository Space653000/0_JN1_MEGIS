"""Kernel-neutral geometry, collision and clearance validators (G3-VAL-001).

The validators operate on axis-aligned bounding boxes expressed in
millimetres so the same layer can run against CAD-exported AABBs without
depending on a CAD kernel.  Semantics:

- geometry: a component box must be finite, non-inverted and have positive
  volume before it can participate in placement checks.
- collision: two boxes collide when they overlap with positive volume in all
  three orthogonal axes; touching faces are not a collision.
- clearance: the axis gap is the largest positive orthogonal separation.
  When boxes overlap on every axis the gap becomes the smallest overlap depth
  with a negative sign.  A required gap is satisfied when ``gap >= min_gap``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .results import CheckType, ValidationIssue, ValidationResult

VAL_CODE_GEOMETRY = "MEGIS-VAL-003"
VAL_CODE_COLLISION = "MEGIS-VAL-001"
VAL_CODE_CLEARANCE = "MEGIS-VAL-002"


@dataclass(frozen=True)
class BoundingBox:
    """Axis-aligned box in millimetres."""

    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float

    @classmethod
    def from_list(cls, raw_min: list[float], raw_max: list[float]) -> "BoundingBox":
        return cls(
            min_x=float(raw_min[0]),
            min_y=float(raw_min[1]),
            min_z=float(raw_min[2]),
            max_x=float(raw_max[0]),
            max_y=float(raw_max[1]),
            max_z=float(raw_max[2]),
        )

    @property
    def _values(self) -> tuple[float, float, float, float, float, float]:
        return (self.min_x, self.min_y, self.min_z, self.max_x, self.max_y, self.max_z)

    def is_finite(self) -> bool:
        return all(math.isfinite(value) for value in self._values)

    def is_inverted(self) -> bool:
        return any(
            maximum < minimum
            for minimum, maximum in (
                (self.min_x, self.max_x),
                (self.min_y, self.max_y),
                (self.min_z, self.max_z),
            )
        )

    def volume(self) -> float:
        if self.is_inverted() or not self.is_finite():
            return 0.0
        return (
            (self.max_x - self.min_x)
            * (self.max_y - self.min_y)
            * (self.max_z - self.min_z)
        )

    def _axes(self) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
        return (
            (self.min_x, self.max_x),
            (self.min_y, self.max_y),
            (self.min_z, self.max_z),
        )


@dataclass(frozen=True)
class ComponentBox:
    """A named component with an axis-aligned box."""

    component_id: str
    box: BoundingBox

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ComponentBox":
        raw_box = raw["box"]
        return cls(
            component_id=raw["component_id"],
            box=BoundingBox.from_list(raw_box["min"], raw_box["max"]),
        )


@dataclass(frozen=True)
class ClearanceRequirement:
    """A required minimum gap between two named components."""

    first_id: str
    second_id: str
    min_gap_mm: float
    rule_id: str | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ClearanceRequirement":
        return cls(
            first_id=raw["first_id"],
            second_id=raw["second_id"],
            min_gap_mm=float(raw["min_gap_mm"]),
            rule_id=raw.get("rule_id"),
        )


@dataclass(frozen=True)
class DesignValidationInput:
    """Kernel-neutral design geometry handed to the validators."""

    design_id: str
    components: tuple[ComponentBox, ...]
    clearances: tuple[ClearanceRequirement, ...] = ()

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "DesignValidationInput":
        return cls(
            design_id=raw["design_id"],
            components=tuple(
                ComponentBox.from_dict(item) for item in raw["components"]
            ),
            clearances=tuple(
                ClearanceRequirement.from_dict(item)
                for item in raw.get("clearances", [])
            ),
        )


def _geometry_issues(component: ComponentBox) -> list[ValidationIssue]:
    box = component.box
    issues: list[ValidationIssue] = []
    check_id = f"geometry-{component.component_id}"
    if not box.is_finite():
        issues.append(
            ValidationIssue(
                check_id=check_id,
                check_type=CheckType.GEOMETRY,
                status="fail",
                severity="error",
                code=VAL_CODE_GEOMETRY,
                message_zh_tw="驗證輸入幾何包含非有限數值。",
                engineer_detail="geometry contains non-finite coordinate values",
                entity_refs=(component.component_id,),
                retryable=False,
                details={"kind": "non_finite"},
            )
        )
        return issues
    if box.is_inverted():
        issues.append(
            ValidationIssue(
                check_id=check_id,
                check_type=CheckType.GEOMETRY,
                status="fail",
                severity="error",
                code=VAL_CODE_GEOMETRY,
                message_zh_tw="驗證輸入幾何無效（最小大於最大）。",
                engineer_detail="box minimum exceeds maximum on at least one axis",
                entity_refs=(component.component_id,),
                retryable=False,
                details={"kind": "inverted"},
            )
        )
        return issues
    if box.volume() <= 0.0:
        issues.append(
            ValidationIssue(
                check_id=check_id,
                check_type=CheckType.GEOMETRY,
                status="fail",
                severity="error",
                code=VAL_CODE_GEOMETRY,
                message_zh_tw="驗證輸入幾何無效（體積為零）。",
                engineer_detail="box must have positive volume",
                entity_refs=(component.component_id,),
                retryable=False,
                details={"kind": "zero_volume", "volume_mm3": box.volume()},
            )
        )
    return issues


def _overlap_extents(a: BoundingBox, b: BoundingBox) -> list[float]:
    """Positive overlap depth per axis; zero or negative means no overlap."""

    extents: list[float] = []
    for (a_min, a_max), (b_min, b_max) in zip(a._axes(), b._axes()):
        overlap = min(a_max, b_max) - max(a_min, b_min)
        extents.append(overlap if overlap > 0.0 else 0.0)
    return extents


def _collides(a: BoundingBox, b: BoundingBox) -> bool:
    return all(extent > 0.0 for extent in _overlap_extents(a, b))


def _axis_gap_mm(a: BoundingBox, b: BoundingBox) -> float:
    """Largest positive axis separation, or negative overlap depth when nested."""

    separations: list[float] = []
    for (a_min, a_max), (b_min, b_max) in zip(a._axes(), b._axes()):
        if a_max <= b_min:
            separations.append(b_min - a_max)
        elif b_max <= a_min:
            separations.append(a_min - b_max)
        else:
            separations.append(0.0)
    largest = max(separations)
    if largest > 0.0:
        return largest
    extents = _overlap_extents(a, b)
    return -min(extents) if extents else 0.0


def _collision_issues(
    components: tuple[ComponentBox, ...],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for index, first in enumerate(components):
        for second in components[index + 1 :]:
            if _collides(first.box, second.box):
                issues.append(
                    ValidationIssue(
                        check_id=f"collision-{first.component_id}-{second.component_id}",
                        check_type=CheckType.COLLISION,
                        status="fail",
                        severity="error",
                        code=VAL_CODE_COLLISION,
                        message_zh_tw="檢測到碰撞或佈局衝突。",
                        engineer_detail=f"{first.component_id} and {second.component_id} overlap",
                        entity_refs=(first.component_id, second.component_id),
                        retryable=False,
                        details={
                            "overlap_mm3": min(
                                _overlap_extents(first.box, second.box)
                            )
                            * 1.0,
                        },
                    )
                )
    return issues


def _clearance_issues(
    components: tuple[ComponentBox, ...],
    clearances: tuple[ClearanceRequirement, ...],
) -> list[ValidationIssue]:
    by_id = {component.component_id: component.box for component in components}
    issues: list[ValidationIssue] = []
    for index, requirement in enumerate(clearances):
        if requirement.first_id not in by_id or requirement.second_id not in by_id:
            issues.append(
                ValidationIssue(
                    check_id=f"clearance-{index}",
                    check_type=CheckType.CLEARANCE,
                    status="error",
                    severity="error",
                    code=VAL_CODE_GEOMETRY,
                    message_zh_tw="驗證輸入無效（餘隙定義參照未知元件）。",
                    engineer_detail="clearance requirement references unknown component",
                    entity_refs=(requirement.first_id, requirement.second_id),
                    retryable=False,
                    details={"kind": "dangling_component_ref"},
                )
            )
            continue
        first_box = by_id[requirement.first_id]
        second_box = by_id[requirement.second_id]
        gap = _axis_gap_mm(first_box, second_box)
        if gap < requirement.min_gap_mm:
            issues.append(
                ValidationIssue(
                    check_id=(
                        f"clearance-{requirement.first_id}-{requirement.second_id}"
                    ),
                    check_type=CheckType.CLEARANCE,
                    status="fail",
                    severity="error",
                    code=VAL_CODE_CLEARANCE,
                    message_zh_tw="元件間餘隙不足。",
                    engineer_detail=(
                        f"gap {gap:.3f} mm below required {requirement.min_gap_mm} mm"
                    ),
                    entity_refs=(requirement.first_id, requirement.second_id),
                    retryable=False,
                    rule_id=requirement.rule_id,
                    details={
                        "gap_mm": gap,
                        "required_mm": requirement.min_gap_mm,
                    },
                )
            )
    return issues


def validate_design(
    input_data: DesignValidationInput,
    validation_id: str,
    design_ref: str,
    created_at: str,
) -> ValidationResult:
    """Run geometry, collision and clearance checks over a design.

    Placement checks are skipped whenever any component's geometry is invalid,
    because a degenerate box cannot produce a meaningful overlap result.
    """

    geometry = [
        issue
        for component in input_data.components
        for issue in _geometry_issues(component)
    ]
    if geometry:
        return ValidationResult(
            validation_id=validation_id,
            design_ref=design_ref,
            created_at=created_at,
            checks=tuple(geometry),
        )
    collisions = _collision_issues(input_data.components)
    clearances = _clearance_issues(input_data.components, input_data.clearances)
    return ValidationResult(
        validation_id=validation_id,
        design_ref=design_ref,
        created_at=created_at,
        checks=tuple(collisions + clearances),
    )
