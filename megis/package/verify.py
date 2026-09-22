"""G5-PKG-001: package manifest verification over on-disk artifacts.

``verify_package_manifest`` revalidates the manifest, refuses any declared
non-PROTOTYPE / production-ready content, recomputes every L1 byte hash and L2
semantic fingerprint against the files on disk, and recomputes the manifest
semantic fingerprint.  Any drift raises a structured ``MEGIS-PKG-001``
(fingerprint mismatch) or ``MEGIS-PKG-002`` (declarative mismatch) error so a
tampered artifact can never silently pass.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from megis.determinism import byte_sha256, manifest_semantic_fingerprint
from megis.errors import MegisError

from .manifest import semantic_fingerprint_for_path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_MANIFEST_SCHEMA_PATH = ROOT / "schemas" / "v3" / "package-manifest.schema.json"

_FORBIDDEN_READINESS_TOKENS = ("PRODUCTION READY", "PRODUCTION_READY")


def _load_schema() -> dict[str, Any]:
    return json.loads(PACKAGE_MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_manifest_schema() -> None:
    """Ensure the package manifest schema is self-consistent."""
    Draft202012Validator.check_schema(_load_schema())


def _schema_errors(document: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(_load_schema())
    return sorted(
        (error.message for error in validator.iter_errors(document)),
        key=lambda message: message,
    )


def _declarative_mismatch(detail: Any) -> MegisError:
    return MegisError(
        "MEGIS-PKG-002",
        engineer_detail={"reason": "manifest declarative mismatch", "detail": detail},
    )


def _fingerprint_mismatch(detail: Any) -> MegisError:
    return MegisError(
        "MEGIS-PKG-001",
        engineer_detail={"reason": "fingerprint mismatch", "detail": detail},
    )


def verify_package_manifest(manifest: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    """Verify a package manifest against artifacts under ``base_dir``.

    Raises ``MegisError`` on the first mismatch; returns a check ledger when
    every declared artifact and fingerprint still matches.
    """
    schema_problems = _schema_errors(manifest)
    if schema_problems:
        raise _declarative_mismatch({"schemaErrors": schema_problems})
    if manifest.get("package_kind") != "PROTOTYPE_PACKAGE":
        raise _declarative_mismatch(
            {"field": "package_kind", "expected": "PROTOTYPE_PACKAGE"}
        )
    if manifest.get("classification") != "DESIGN_RUN":
        raise _declarative_mismatch({"field": "classification", "expected": "DESIGN_RUN"})

    serialized = json.dumps(manifest, ensure_ascii=False, sort_keys=True).upper()
    detected = [token for token in _FORBIDDEN_READINESS_TOKENS if token in serialized]
    if detected:
        raise _declarative_mismatch(
            {"reason": "production-ready declaration is not allowed", "tokens": detected}
        )

    maturity_state = (manifest.get("maturity") or {}).get("state")
    if maturity_state == "RELEASED":
        raise _declarative_mismatch(
            {"reason": "PROTOTYPE package must not declare RELEASED maturity"}
        )

    checked: list[dict[str, Any]] = []
    for entry in manifest["artifact_hashes"]:
        relative = entry["path"]
        source = (base_dir / relative).resolve()
        if not source.is_file():
            raise _declarative_mismatch(
                {"reason": "declared artifact missing", "path": relative}
            )
        recomputed_sha = byte_sha256(source)
        recomputed_bytes = source.stat().st_size
        if recomputed_sha != entry["byte_sha256"] or recomputed_bytes != entry["bytes"]:
            raise _fingerprint_mismatch(
                {
                    "path": relative,
                    "byteSha256Mismatch": recomputed_sha != entry["byte_sha256"],
                    "bytesMismatch": recomputed_bytes != entry["bytes"],
                }
            )
        try:
            recomputed_semantic, kind = semantic_fingerprint_for_path(source)
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise _fingerprint_mismatch(
                {
                    "path": relative,
                    "reason": f"artifact cannot be fingerprinted: {error}",
                }
            ) from error
        if recomputed_semantic != entry["semantic_fingerprint"] or kind != entry["fingerprint_kind"]:
            raise _fingerprint_mismatch(
                {
                    "path": relative,
                    "semanticFingerprintMismatch": recomputed_semantic
                    != entry["semantic_fingerprint"],
                    "fingerprintKindMismatch": kind != entry["fingerprint_kind"],
                }
            )
        checked.append(
            {
                "path": relative,
                "bytes": recomputed_bytes,
                "byte_sha256": recomputed_sha,
                "semantic_fingerprint": recomputed_semantic,
                "fingerprint_kind": kind,
            }
        )

    recomputed_manifest = manifest_semantic_fingerprint(manifest)
    stored_manifest_fingerprint = (manifest.get("manifestSemanticFingerprint") or {}).get(
        "semanticFingerprint"
    )
    if stored_manifest_fingerprint != recomputed_manifest["semanticFingerprint"]:
        raise _fingerprint_mismatch(
            {
                "path": "manifestSemanticFingerprint",
                "stored": stored_manifest_fingerprint,
                "recomputed": recomputed_manifest["semanticFingerprint"],
            }
        )

    return {
        "valid": True,
        "checkedArtifacts": len(checked),
        "artifactLedger": checked,
        "manifestFingerprintMatched": True,
    }


__all__ = [
    "PACKAGE_MANIFEST_SCHEMA_PATH",
    "validate_manifest_schema",
    "verify_package_manifest",
]
