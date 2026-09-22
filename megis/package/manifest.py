"""G5-PKG-001: V3 package manifest builder and content hashes.

Builds a deterministic ``PROTOTYPE_PACKAGE`` manifest: every artifact is pinned
with an L1 ``byte_sha256`` (exact bytes) and an L2 ``semantic_fingerprint``
(geometry-normalized for STEP/STL/DXF, canonical JSON for JSON, LF-normalized
text/data otherwise).  Runtime-only fields are carrier metadata and are
excluded from the manifest semantic fingerprint so a clean-environment rebuild
yields the same digest.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import platform
from pathlib import Path
from typing import Any, Iterable, Mapping

from megis.determinism import (
    binary_stl_semantic_fingerprint,
    byte_sha256,
    canonical_json,
    dxf_vector_semantic_fingerprint,
    manifest_semantic_fingerprint,
    normalize_step_text,
)

PACKAGE_BUILDER_VERSION = "megis.package@1.0.0"
FINGERPRINT_POLICY_VERSION = "1.0.0"

_RUNTIME_ONLY_JSON_FIELDS = frozenset(
    {"generated_at", "generatedAt", "verified_at", "verifiedAt", "durationSeconds"}
)


def detect_runtime() -> dict[str, Any]:
    """Return the stable OS/runtime identity for the manifest."""
    return {
        "os": platform.system(),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "emulation": False,
    }


def _drop_runtime_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _drop_runtime_fields(child)
            for key, child in value.items()
            if key not in _RUNTIME_ONLY_JSON_FIELDS
        }
    if isinstance(value, list):
        return [_drop_runtime_fields(child) for child in value]
    return value


def _json_semantic_fingerprint(path: Path) -> str:
    document = json.loads(path.read_text(encoding="utf-8"))
    canonical = _drop_runtime_fields(document)
    return sha256(canonical_json(canonical).encode("utf-8")).hexdigest()


def semantic_fingerprint_for_path(path: Path) -> tuple[str, str]:
    """Return ``(semantic_fingerprint, fingerprint_kind)`` for one artifact.

    Raises ``ValueError`` when the artifact cannot be processed, which the
    caller maps to a package fingerprint mismatch.
    """
    suffix = path.suffix.lower()
    if suffix == ".stl":
        record = binary_stl_semantic_fingerprint(path)
        return record["semanticFingerprint"], "stl_triangles"
    if suffix == ".dxf":
        record = dxf_vector_semantic_fingerprint(path)
        return record["semanticFingerprint"], "dxf_vectors"
    if suffix == ".step":
        normalized = normalize_step_text(path.read_text(encoding="utf-8"))
        return sha256(normalized.encode("utf-8")).hexdigest(), "step_normalized_text"
    if suffix == ".json":
        return _json_semantic_fingerprint(path), "json_canonical"
    raw = path.read_bytes()
    if b"\x00" in raw[:512]:
        return byte_sha256(path), "binary_bytes"
    text = raw.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    return sha256(text.encode("utf-8")).hexdigest(), "utf8_text_lf"


def _normalise_gates(gates: Mapping[str, Iterable[str]] | None) -> dict[str, list[str]]:
    default = {"passed": [], "failed": [], "waived": [], "skipped": []}
    if gates is None:
        return default
    return {key: sorted(set(gates.get(key, []))) for key in default}


def _normalise_ai_involvement(involvement: Mapping[str, Any] | None) -> dict[str, Any]:
    source = dict(involvement) if involvement is not None else {}
    return {
        "ai_used": bool(source.get("ai_used", False)),
        "model": source.get("model"),
        "prompt_versions": list(source.get("prompt_versions", [])),
        "llm_proposed_fields": list(source.get("llm_proposed_fields", [])),
    }


def build_package_manifest(
    *,
    design_id: str,
    revision: str,
    artifact_paths: Mapping[str, Path],
    input_hashes: Mapping[str, str],
    versions: Mapping[str, Any],
    random_seed: str,
    executed_validations: Iterable[str],
    gates: Mapping[str, Iterable[str]] | None = None,
    assumptions: Iterable[str] = (),
    unknowns: Iterable[str] = (),
    human_signoffs: Iterable[Mapping[str, Any]] = (),
    maturity: Mapping[str, Any],
    envelope_ref: str,
    dna_ref: str,
    module_versions: Mapping[str, str] | None = None,
    ai_involvement: Mapping[str, Any] | None = None,
    runtime: Mapping[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic PROTOTYPE_PACKAGE manifest.

    ``artifact_paths`` maps a repository-relative artifact path to its on-disk
    ``Path``; ``input_hashes`` maps an input key to its ``byte_sha256``.
    """
    runtime_identity = dict(runtime) if runtime is not None else detect_runtime()
    input_entries = sorted(
        {"path": key, "byte_sha256": value}
        for key, value in input_hashes.items()
    )
    artifact_entries: list[dict[str, Any]] = []
    for rel, source in sorted(artifact_paths.items()):
        digest, kind = semantic_fingerprint_for_path(source)
        artifact_entries.append(
            {
                "path": rel,
                "bytes": source.stat().st_size,
                "byte_sha256": byte_sha256(source),
                "semantic_fingerprint": digest,
                "fingerprint_kind": kind,
            }
        )

    document: dict[str, Any] = {
        "schemaVersion": "1.0.0",
        "package_kind": "PROTOTYPE_PACKAGE",
        "classification": "DESIGN_RUN",
        "design_id": design_id,
        "revision": revision,
        "generated_at": generated_at
        if generated_at is not None
        else datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "package_builder": PACKAGE_BUILDER_VERSION,
        "fingerprint_policy_version": FINGERPRINT_POLICY_VERSION,
        "input_hashes": input_entries,
        "artifact_hashes": artifact_entries,
        "versions": dict(versions),
        "runtime": dict(runtime_identity),
        "random_seed": random_seed,
        "executed_validations": sorted(set(executed_validations)),
        "gates": _normalise_gates(gates),
        "assumptions": list(assumptions),
        "unknowns": list(unknowns),
        "human_signoffs": [dict(entry) for entry in human_signoffs],
        "maturity": dict(maturity),
        "envelope_ref": envelope_ref,
        "dna_ref": dna_ref,
        "module_versions": dict(module_versions or {}),
        "ai_involvement": _normalise_ai_involvement(ai_involvement),
    }
    document["manifestSemanticFingerprint"] = manifest_semantic_fingerprint(document)
    return document


__all__ = [
    "FINGERPRINT_POLICY_VERSION",
    "PACKAGE_BUILDER_VERSION",
    "build_package_manifest",
    "detect_runtime",
    "semantic_fingerprint_for_path",
]
