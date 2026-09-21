"""Geometry, collision and clearance validators (G3-VAL-001)."""

from .geometry import (
    VAL_CODE_CLEARANCE,
    VAL_CODE_COLLISION,
    VAL_CODE_GEOMETRY,
    BoundingBox,
    ClearanceRequirement,
    ComponentBox,
    DesignValidationInput,
    validate_design,
)
from .results import (
    CheckType,
    ValidationIssue,
    ValidationResult,
    ValidationStatus,
)

__all__ = [
    "BoundingBox",
    "CheckType",
    "ClearanceRequirement",
    "ComponentBox",
    "DesignValidationInput",
    "VAL_CODE_CLEARANCE",
    "VAL_CODE_COLLISION",
    "VAL_CODE_GEOMETRY",
    "ValidationIssue",
    "ValidationResult",
    "ValidationStatus",
    "validate_design",
]
