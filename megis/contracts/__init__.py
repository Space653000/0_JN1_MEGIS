"""Versioned engineering contracts, deterministic codecs, and consumers."""

from .consumer import EngineeringIrSummary, summarize_engineering_ir
from .serialization import (
    deserialize_engineering_ir,
    load_engineering_ir,
    serialize_engineering_ir,
)
from .validation import ContractValidationError, validate_engineering_ir, validate_primitives

__all__ = [
    "ContractValidationError",
    "EngineeringIrSummary",
    "deserialize_engineering_ir",
    "load_engineering_ir",
    "serialize_engineering_ir",
    "summarize_engineering_ir",
    "validate_engineering_ir",
    "validate_primitives",
]
