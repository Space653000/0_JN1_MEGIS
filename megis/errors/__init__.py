"""V3 error taxonomy public surface (G1-ERR-001)."""

from .registry import (
    ERROR_CODES,
    ERROR_SCHEMA_PATH,
    CODE_PATTERN,
    LEGACY_GEO_MAPPING,
    ErrorCode,
    ErrorDomain,
    ErrorObject,
    ErrorSeverity,
    MegisError,
    validate_error_object,
    verify_error_codes,
)

__all__ = [
    "CODE_PATTERN",
    "ERROR_CODES",
    "ERROR_SCHEMA_PATH",
    "LEGACY_GEO_MAPPING",
    "ErrorCode",
    "ErrorDomain",
    "ErrorObject",
    "ErrorSeverity",
    "MegisError",
    "validate_error_object",
    "verify_error_codes",
]
