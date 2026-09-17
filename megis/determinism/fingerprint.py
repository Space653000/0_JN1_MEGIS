"""V3 fingerprint policy 1.0.0 canonicalization primitives."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_EVEN
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable


FINGERPRINT_POLICY_VERSION = "1.0.0"
_RUNTIME_MANIFEST_FIELDS = frozenset(
    {
        "generated_at",
        "generatedAt",
        "manifestSemanticFingerprint",
        "verified_at",
        "verifiedAt",
        "durationSeconds",
    }
)


def canonical_json(document: Any) -> str:
    """Encode canonical UTF-8 JSON without insignificant whitespace."""

    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def byte_sha256(path: Path) -> str:
    """Return the L1 integrity digest of the exact file bytes."""

    return sha256(path.read_bytes()).hexdigest()


def _rounded(value: float, quantum: str) -> str:
    rounded = Decimal(str(value)).quantize(Decimal(quantum), rounding=ROUND_HALF_EVEN)
    if rounded == 0:
        rounded = abs(rounded)
    return format(rounded, "f")


def _vector_values(vector: Any) -> tuple[float, float, float]:
    return (float(vector.x), float(vector.y), float(vector.z))


def _without_informational_fields(
    record: dict[str, Any], informational_fields: Iterable[str]
) -> dict[str, Any]:
    excluded = set(informational_fields)
    return {key: value for key, value in record.items() if key not in excluded}


def _fingerprint_record(
    canonical: dict[str, Any], informational_fields: Iterable[str] = ()
) -> dict[str, Any]:
    informational = sorted(set(informational_fields))
    payload = _without_informational_fields(canonical, informational)
    return {
        "fingerprintPolicyVersion": FINGERPRINT_POLICY_VERSION,
        "canonical": canonical,
        "informationalFields": informational,
        "semanticFingerprint": sha256(canonical_json(payload).encode("utf-8")).hexdigest(),
    }


def geometry_semantic_fingerprint(
    shape: Any,
    semantic_features: Iterable[str] = (),
    informational_fields: Iterable[str] = (),
) -> dict[str, Any]:
    """Build the L2 geometry fingerprint without importing a CAD kernel."""

    box = shape.BoundingBox()
    center = _vector_values(shape.Center())
    canonical = {
        "fingerprint_policy_version": FINGERPRINT_POLICY_VERSION,
        "solids": len(shape.Solids()),
        "shells": len(shape.Shells()),
        "faces": len(shape.Faces()),
        "edges": len(shape.Edges()),
        "vertices": len(shape.Vertices()),
        "volume_mm3": _rounded(float(shape.Volume()), "0.01"),
        "area_mm2": _rounded(float(shape.Area()), "0.01"),
        "bbox_mm": [
            _rounded(float(box.xlen), "0.001"),
            _rounded(float(box.ylen), "0.001"),
            _rounded(float(box.zlen), "0.001"),
        ],
        "center_of_mass_mm": [_rounded(value, "0.001") for value in center],
        "semantic_features": sorted(set(semantic_features)),
    }
    return _fingerprint_record(canonical, informational_fields)


def _drop_runtime_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _drop_runtime_fields(child)
            for key, child in value.items()
            if key not in _RUNTIME_MANIFEST_FIELDS
        }
    if isinstance(value, list):
        return [_drop_runtime_fields(child) for child in value]
    return value


def manifest_semantic_fingerprint(manifest: dict[str, Any]) -> dict[str, Any]:
    """Fingerprint manifest semantics while excluding runtime-only metadata."""

    canonical = _drop_runtime_fields(deepcopy(manifest))
    return {
        "fingerprintPolicyVersion": FINGERPRINT_POLICY_VERSION,
        "excludedRuntimeFields": sorted(_RUNTIME_MANIFEST_FIELDS),
        "semanticFingerprint": sha256(
            canonical_json(canonical).encode("utf-8")
        ).hexdigest(),
    }
