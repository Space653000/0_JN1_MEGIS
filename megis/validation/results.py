"""Validation result contracts (G3-VAL-001).

Validation results are stable, serializable outputs produced by the
geometry, collision and clearance validators.  A failed check carries a
stable ``MEGIS-VAL-*`` code and both user and engineer copy so callers can
route it back to the blueprint error taxonomy instead of parsing prose.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ValidationStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


class CheckType(StrEnum):
    GEOMETRY = "geometry"
    COLLISION = "collision"
    CLEARANCE = "clearance"


@dataclass(frozen=True)
class ValidationIssue:
    """One deterministic check result inside a ValidationResult."""

    check_id: str
    check_type: str
    status: str
    severity: str
    code: str | None
    message_zh_tw: str
    engineer_detail: str
    entity_refs: tuple[str, ...]
    retryable: bool = False
    rule_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "check_type": self.check_type,
            "status": self.status,
            "severity": self.severity,
            "code": self.code,
            "retryable": self.retryable,
            "user_message_zh_tw": self.message_zh_tw,
            "engineer_detail": self.engineer_detail,
            "entity_refs": list(self.entity_refs),
            "rule_id": self.rule_id,
            "details": self.details,
        }


@dataclass(frozen=True)
class ValidationResult:
    """Serializable validation run against a kernel-neutral design."""

    validation_id: str
    design_ref: str
    created_at: str
    checks: tuple[ValidationIssue, ...]

    @property
    def status(self) -> str:
        if any(
            issue.status in (ValidationStatus.FAIL, ValidationStatus.ERROR)
            for issue in self.checks
        ):
            return ValidationStatus.FAIL if any(
                issue.status == ValidationStatus.FAIL for issue in self.checks
            ) else ValidationStatus.ERROR
        return ValidationStatus.PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": "1.0.0",
            "workItem": "G3-VAL-001",
            "validation_id": self.validation_id,
            "design_ref": self.design_ref,
            "created_at": self.created_at,
            "status": self.status,
            "summary": {
                "checks": len(self.checks),
                "passed": sum(
                    1 for issue in self.checks if issue.status == ValidationStatus.PASS
                ),
                "failed": sum(
                    1
                    for issue in self.checks
                    if issue.status in (ValidationStatus.FAIL, ValidationStatus.ERROR)
                ),
            },
            "results": [issue.to_dict() for issue in self.checks],
        }
