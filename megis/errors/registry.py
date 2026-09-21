"""V3 error taxonomy contract for the errors core module.

Codes follow MEGIS-<DOMAIN>-<NNN> and every code is registered in
docs/ERROR_CODES.md. This module has no external dependency so other core
modules can rely on it without risking import cycles.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ERROR_SCHEMA_PATH = ROOT / "schemas" / "v3" / "error.schema.json"

CODE_PATTERN = re.compile(r"^MEGIS-(?P<domain>[A-Z]{2,4})-(?P<number>[0-9]{3})$")


class ErrorSeverity(StrEnum):
    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ErrorDomain(StrEnum):
    SCH = "SCH"
    REF = "REF"
    ENV = "ENV"
    GEO = "GEO"
    VAL = "VAL"
    RUL = "RUL"
    PKG = "PKG"
    JOB = "JOB"
    AI = "AI"
    IMP = "IMP"
    SYS = "SYS"


@dataclass(frozen=True)
class ErrorCode:
    """Registry entry: stable identity plus user and engineer copy."""

    code: str
    domain: ErrorDomain
    number: int
    severity: ErrorSeverity
    retryable: bool
    user_message_zh_tw: str
    engineer_detail: str


_ERROR_CODES: list[ErrorCode] = [
    ErrorCode("MEGIS-SCH-001", ErrorDomain.SCH, 1, ErrorSeverity.ERROR, False, "輸入的單位或型別不符合定義。", "schema or type mismatch (e.g. unit mismatch)"),
    ErrorCode("MEGIS-REF-001", ErrorDomain.REF, 1, ErrorSeverity.ERROR, False, "參照的物件不存在。", "dangling reference or missing entity"),
    ErrorCode("MEGIS-ENV-001", ErrorDomain.ENV, 1, ErrorSeverity.ERROR, False, "輸入超出支援範圍。", "dimension or requirement out of supported envelope"),
    ErrorCode("MEGIS-GEO-001", ErrorDomain.GEO, 1, ErrorSeverity.ERROR, False, "幾何輸入資料無效。", "invalid geometry IR input"),
    ErrorCode("MEGIS-GEO-002", ErrorDomain.GEO, 2, ErrorSeverity.ERROR, False, "不支援此幾何操作。", "unsupported geometry operation"),
    ErrorCode("MEGIS-GEO-003", ErrorDomain.GEO, 3, ErrorSeverity.ERROR, False, "幾何尺寸無效。", "invalid dimension for geometry operation"),
    ErrorCode("MEGIS-GEO-004", ErrorDomain.GEO, 4, ErrorSeverity.FATAL, False, "幾何後端違反契約。", "backend contract violation"),
    ErrorCode("MEGIS-VAL-001", ErrorDomain.VAL, 1, ErrorSeverity.ERROR, False, "檢測到碰撞或佈局衝突。", "collision or layout conflict detected"),
    ErrorCode("MEGIS-VAL-002", ErrorDomain.VAL, 2, ErrorSeverity.ERROR, False, "元件間餘隙不足。", "clearance below required minimum gap"),
    ErrorCode("MEGIS-VAL-003", ErrorDomain.VAL, 3, ErrorSeverity.ERROR, False, "驗證輸入幾何無效。", "invalid geometry for validation"),
    ErrorCode("MEGIS-RUL-001", ErrorDomain.RUL, 1, ErrorSeverity.ERROR, False, "規則來源未經核准。", "rule source not approved"),
    ErrorCode("MEGIS-RUL-002", ErrorDomain.RUL, 2, ErrorSeverity.ERROR, False, "規則狀態轉換無效。", "invalid rule lifecycle transition"),
    ErrorCode("MEGIS-RUL-003", ErrorDomain.RUL, 3, ErrorSeverity.ERROR, False, "規則不可豁免或豁免條件無效。", "rule waiver disallowed or invalid"),
    ErrorCode("MEGIS-RUL-004", ErrorDomain.RUL, 4, ErrorSeverity.ERROR, False, "規則來源登錄無效或不存在。", "rule source registry entry missing or invalid"),
    ErrorCode("MEGIS-PKG-001", ErrorDomain.PKG, 1, ErrorSeverity.ERROR, False, "套件指紋不符。", "package fingerprint mismatch"),
    ErrorCode("MEGIS-JOB-001", ErrorDomain.JOB, 1, ErrorSeverity.ERROR, True, "工作逾時。", "job timeout"),
    ErrorCode("MEGIS-AI-001", ErrorDomain.AI, 1, ErrorSeverity.ERROR, True, "AI 輸出格式無效。", "schema-invalid AI model output"),
    ErrorCode("MEGIS-IMP-001", ErrorDomain.IMP, 1, ErrorSeverity.ERROR, False, "輸入檔案超出限制。", "import file exceeds size or structural limit"),
    ErrorCode("MEGIS-SYS-001", ErrorDomain.SYS, 1, ErrorSeverity.FATAL, False, "本機工具鏈版本不符。", "toolchain or environment version mismatch"),
]

ERROR_CODES: dict[str, ErrorCode] = {entry.code: entry for entry in _ERROR_CODES}

if len(ERROR_CODES) != len(_ERROR_CODES):
    raise RuntimeError("duplicate error code registered; docs/ERROR_CODES.md must stay unique")

# Maps the v2 GeometryErrorCode enum values to their v3 GEO codes.
LEGACY_GEO_MAPPING: dict[str, str] = {
    "INVALID_IR": "MEGIS-GEO-001",
    "UNSUPPORTED_OPERATION": "MEGIS-GEO-002",
    "INVALID_DIMENSION": "MEGIS-GEO-003",
    "BACKEND_CONTRACT_VIOLATION": "MEGIS-GEO-004",
}


@dataclass(frozen=True)
class ErrorObject:
    """Runtime error instance; satisfies schemas/v3/error.schema.json."""

    code: str
    severity: str
    retryable: bool
    user_message_zh_tw: str
    engineer_detail: Any
    entity_refs: tuple[str, ...] = ()
    correlation_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "retryable": self.retryable,
            "user_message_zh_tw": self.user_message_zh_tw,
            "engineer_detail": self.engineer_detail,
            "entity_refs": list(self.entity_refs),
            "correlation_id": self.correlation_id,
        }


class MegisError(Exception):
    """Structured failure carrying a registered V3 error code."""

    def __init__(
        self,
        code: ErrorCode | str,
        *,
        engineer_detail: Any = None,
        entity_refs: tuple[str, ...] = (),
        correlation_id: str = "",
    ) -> None:
        if isinstance(code, str):
            code = ERROR_CODES[code]
        self.code = code
        self.error_object = ErrorObject(
            code=code.code,
            severity=code.severity.value,
            retryable=code.retryable,
            user_message_zh_tw=code.user_message_zh_tw,
            engineer_detail=engineer_detail if engineer_detail is not None else code.engineer_detail,
            entity_refs=entity_refs,
            correlation_id=correlation_id,
        )
        super().__init__(code.code)


def validate_error_object(obj: dict[str, Any]) -> None:
    """Validate a dict against the v3 error schema or raise ContractValidationError."""

    from jsonschema import Draft202012Validator

    schema = json.loads(ERROR_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(obj),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        messages = "; ".join(error.message for error in errors)
        raise ValueError(f"error object invalid: {messages}")


def verify_error_codes(schema_path: Path = ERROR_SCHEMA_PATH) -> list[str]:
    """Return a deterministically ordered list of registry consistency issues."""

    from jsonschema import Draft202012Validator

    issues: list[str] = []
    for entry in _ERROR_CODES:
        match = CODE_PATTERN.match(entry.code)
        if not match:
            issues.append(f"{entry.code}: invalid MEGIS-<DOMAIN>-<NNN> format")
            continue
        expected = f"MEGIS-{entry.domain.value}-{entry.number:03d}"
        if entry.code != expected:
            issues.append(f"{entry.code}: does not match {expected}")
        if not entry.user_message_zh_tw or not entry.engineer_detail:
            issues.append(f"{entry.code}: missing user or engineer message")

    domains: dict[str, list[int]] = {}
    for entry in _ERROR_CODES:
        domains.setdefault(entry.domain.value, []).append(entry.number)
    for domain, numbers in domains.items():
        if numbers != list(range(1, len(numbers) + 1)):
            issues.append(f"{domain}: numbers must be contiguous from 001, got {numbers}")

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for entry in _ERROR_CODES:
        sample: dict[str, Any] = ErrorObject(
            code=entry.code,
            severity=entry.severity.value,
            retryable=entry.retryable,
            user_message_zh_tw=entry.user_message_zh_tw,
            engineer_detail=entry.engineer_detail,
        ).to_dict()
        if list(validator.iter_errors(sample)):
            issues.append(f"{entry.code}: failed v3 error schema")

    for legacy, v3_code in LEGACY_GEO_MAPPING.items():
        if v3_code not in ERROR_CODES:
            issues.append(f"legacy {legacy} maps to unregistered {v3_code}")

    return issues
