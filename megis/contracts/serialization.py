"""Deterministic serialization for validated Engineering IR documents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .validation import validate_engineering_ir


def serialize_engineering_ir(document: dict[str, Any]) -> str:
    """Validate and encode an Engineering IR document in canonical JSON form."""

    validate_engineering_ir(document)
    return json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def deserialize_engineering_ir(payload: str | bytes) -> dict[str, Any]:
    """Decode and validate one Engineering IR JSON payload."""

    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    document = json.loads(payload)
    if not isinstance(document, dict):
        raise TypeError("Engineering IR root must be an object")
    validate_engineering_ir(document)
    return document


def load_engineering_ir(path: Path) -> dict[str, Any]:
    """Load a UTF-8 Engineering IR file through the validated decoder."""

    return deserialize_engineering_ir(path.read_bytes())
