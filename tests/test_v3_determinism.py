from copy import deepcopy
import json
from pathlib import Path
import struct

from jsonschema import Draft202012Validator

from megis.determinism import (
    binary_stl_semantic_fingerprint,
    byte_sha256,
    geometry_semantic_fingerprint,
    manifest_semantic_fingerprint,
    normalize_step_text,
)
from spikes.g0_cad.reference_case import (
    ARTIFACT_NAMES,
    SEMANTIC_FEATURES,
    build_reference_case,
    generate_and_verify,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "fingerprint" / "policy-1.0.0.json"
POLICY_SCHEMA_PATH = ROOT / "schemas" / "v3" / "fingerprint-policy.schema.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_fingerprint_policy_is_versioned_and_schema_valid() -> None:
    policy = _load(POLICY_PATH)
    Draft202012Validator(_load(POLICY_SCHEMA_PATH)).validate(policy)

    assert policy["fingerprintPolicyVersion"] == "1.0.0"
    assert policy["rounding"] == {
        "mode": "ROUND_HALF_EVEN",
        "lengthMm": "0.001",
        "areaMm2": "0.01",
        "volumeMm3": "0.01",
    }
    assert policy["informationalFields"] == []
    assert policy["stl"]["encoding"] == "binary"


def test_geometry_fingerprint_is_canonical_and_feature_order_independent() -> None:
    shape = build_reference_case()
    forward = geometry_semantic_fingerprint(shape, SEMANTIC_FEATURES)
    reverse = geometry_semantic_fingerprint(shape, reversed(SEMANTIC_FEATURES))

    assert forward == reverse
    assert forward["canonical"] == {
        "fingerprint_policy_version": "1.0.0",
        "solids": 1,
        "shells": 1,
        "faces": 15,
        "edges": 36,
        "vertices": 24,
        "volume_mm3": "44999.37",
        "area_mm2": "45884.82",
        "bbox_mm": ["120.000", "80.000", "35.000"],
        "center_of_mass_mm": ["0.000", "0.000", "11.061"],
        "semantic_features": sorted(SEMANTIC_FEATURES),
    }
    assert len(forward["semanticFingerprint"]) == 64


def test_step_normalization_removes_runtime_and_identity_metadata() -> None:
    first = "FILE_NAME('one.step','2026-09-17T01:02:03',('Alice'),('Org'),'p','o','a');"
    second = "FILE_NAME('two.step','2040-01-01T04:05:06',('Bob'),('Other'),'x','y','z');"

    assert normalize_step_text(first) == normalize_step_text(second)
    assert "1970-01-01T00:00:00" in normalize_step_text(first)
    assert "Alice" not in normalize_step_text(first)


def test_two_replays_have_equal_byte_and_semantic_fingerprints(tmp_path: Path) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first = generate_and_verify(first_dir)
    second = generate_and_verify(second_dir)

    for kind, filename in ARTIFACT_NAMES.items():
        first_path = first_dir / filename
        second_path = second_dir / filename
        assert byte_sha256(first_path) == byte_sha256(second_path), kind
        assert first["artifacts"][kind]["byte_sha256"] == second["artifacts"][kind]["byte_sha256"]

    assert first["fingerprints"] == second["fingerprints"]
    assert first["manifestSemanticFingerprint"] == second["manifestSemanticFingerprint"]
    assert first["fingerprints"]["sourceGeometry"]["semanticFingerprint"] == first["fingerprints"]["stepGeometry"]["semanticFingerprint"]

    stl = (first_dir / ARTIFACT_NAMES["stl"]).read_bytes()
    assert stl[:80].rstrip() == b"MEGIS BINARY STL | policy 1.0.0"
    triangle_count = struct.unpack_from("<I", stl, 80)[0]
    assert len(stl) == 84 + (triangle_count * 50)
    dxf = (first_dir / ARTIFACT_NAMES["dxf"]).read_text(encoding="utf-8")
    assert "2461300" not in dxf
    assert "{00000000-0000-0000-0000-000000000001}" in dxf


def test_l1_integrity_and_l2_semantics_are_independent(tmp_path: Path) -> None:
    output = tmp_path / "run"
    generate_and_verify(output)
    source = output / ARTIFACT_NAMES["stl"]
    header_changed = output / "header-changed.stl"
    header_changed.write_bytes(b"different header".ljust(80, b" ") + source.read_bytes()[80:])

    assert byte_sha256(source) != byte_sha256(header_changed)
    assert binary_stl_semantic_fingerprint(source) == binary_stl_semantic_fingerprint(header_changed)

    geometry_changed = output / "geometry-changed.stl"
    payload = bytearray(source.read_bytes())
    struct.pack_into("<f", payload, 96, 999.0)
    geometry_changed.write_bytes(payload)
    assert binary_stl_semantic_fingerprint(source) != binary_stl_semantic_fingerprint(geometry_changed)


def test_manifest_fingerprint_ignores_runtime_fields_but_not_engineering_values() -> None:
    first = {
        "generated_at": "2026-09-17T00:00:00Z",
        "verifiedAt": "2026-09-17T00:01:00Z",
        "specification": {"width_mm": "120.000"},
    }
    second = deepcopy(first)
    second["generated_at"] = "2040-01-01T00:00:00Z"
    second["verifiedAt"] = "2040-01-01T00:01:00Z"

    assert manifest_semantic_fingerprint(first) == manifest_semantic_fingerprint(second)
    second["specification"]["width_mm"] = "121.000"
    assert manifest_semantic_fingerprint(first) != manifest_semantic_fingerprint(second)


def test_v3c_det_evidence_matches_tracked_reference_artifacts() -> None:
    manifest = _load(ROOT / "artifacts" / "g0-cad" / "manifest.json")
    evidence = _load(ROOT / "artifacts" / "v3c-det-001" / "verification.json")
    recorded = evidence["referenceArtifactFingerprints"]

    assert recorded["stepByteSha256"] == manifest["artifacts"]["step"]["byte_sha256"]
    assert recorded["stlByteSha256"] == manifest["artifacts"]["stl"]["byte_sha256"]
    assert recorded["dxfByteSha256"] == manifest["artifacts"]["dxf"]["byte_sha256"]
    assert recorded["geometrySemanticFingerprint"] == manifest["fingerprints"]["sourceGeometry"]["semanticFingerprint"]
    assert recorded["stlSemanticFingerprint"] == manifest["fingerprints"]["stlMesh"]["semanticFingerprint"]
    assert recorded["dxfSemanticFingerprint"] == manifest["fingerprints"]["dxfVectors"]["semanticFingerprint"]
    assert recorded["manifestSemanticFingerprint"] == manifest["manifestSemanticFingerprint"]["semanticFingerprint"]
