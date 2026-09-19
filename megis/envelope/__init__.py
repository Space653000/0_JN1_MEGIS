"""Supported envelope contracts (G1-ENV-001)."""

from .envelope import (
    ENVELOPE_PATH,
    ENVELOPE_SCHEMA_PATH,
    Envelope,
    EnvelopeDimensions,
    check_within_envelope,
    load_envelope,
)

__all__ = [
    "ENVELOPE_PATH",
    "ENVELOPE_SCHEMA_PATH",
    "Envelope",
    "EnvelopeDimensions",
    "check_within_envelope",
    "load_envelope",
]
