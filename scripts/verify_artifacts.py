from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.contracts import (  # noqa: E402
    canonical_hash,
    load_engineering_ir,
    migrate_engineering_ir,
    rollback_engineering_ir,
    serialize_engineering_ir,
)
from megis.determinism import (  # noqa: E402
    binary_stl_semantic_fingerprint,
    dxf_vector_semantic_fingerprint,
    geometry_semantic_fingerprint,
    manifest_semantic_fingerprint,
)
import cadquery as cq  # noqa: E402


def load_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8-sig"))


def assert_file(relative_path: str, expected_bytes: int, expected_sha256: str) -> None:
    path = ROOT / relative_path
    assert path.is_file(), f"Missing artifact: {relative_path}"
    content = path.read_bytes()
    assert len(content) == expected_bytes, f"Byte count mismatch: {relative_path}"
    assert sha256(content).hexdigest() == expected_sha256, f"SHA-256 mismatch: {relative_path}"


def verify_cad_artifacts() -> int:
    manifest = load_json("artifacts/g0-cad/manifest.json")
    assert manifest["classification"] == "FEASIBILITY_SPIKE"
    assert manifest["maturity"] == "PROTOTYPE"
    assert manifest["engineeringReviewRequired"] is True
    count = 0
    for record in manifest["artifacts"].values():
        assert_file(
            f"artifacts/g0-cad/{record['path']}",
            record["bytes"],
            record["sha256"],
        )
        assert record["byte_sha256"] == record["sha256"]
        count += 1
    step_path = ROOT / "artifacts/g0-cad/reference_case.step"
    stl_path = ROOT / "artifacts/g0-cad/reference_case.stl"
    dxf_path = ROOT / "artifacts/g0-cad/reference_case_section_z10.dxf"
    features = manifest["fingerprints"]["stepGeometry"]["canonical"]["semantic_features"]
    step_shape = cq.importers.importStep(str(step_path)).val()
    assert geometry_semantic_fingerprint(step_shape, features) == manifest["fingerprints"]["stepGeometry"]
    assert binary_stl_semantic_fingerprint(stl_path) == manifest["fingerprints"]["stlMesh"]
    assert dxf_vector_semantic_fingerprint(dxf_path) == manifest["fingerprints"]["dxfVectors"]
    assert manifest_semantic_fingerprint(manifest) == manifest["manifestSemanticFingerprint"]
    return count


def verify_drawing_artifacts() -> int:
    evidence = load_json("artifacts/g0-freecad/verification.json")
    assert evidence["decision"] == "fallback"
    assert evidence["boundary"]["engineeringReviewRequired"] is True
    assert evidence["boundary"]["manufacturingRelease"] is False
    count = 0
    for record in evidence["artifacts"].values():
        assert_file(
            f"artifacts/g0-freecad/{record['path']}",
            record["bytes"],
            record["sha256"],
        )
        count += 1
    return count


def verify_simulation_decision() -> int:
    inventory = load_json("artifacts/g0-sim/inventory.json")
    decision = load_json("environment/comsol.decision.json")
    assert inventory["summary"]["decision"] == "out_of_scope"
    assert inventory["summary"]["blocksCoreGate"] is False
    assert decision["decision"] == inventory["summary"]["decision"]
    assert decision["blocksCoreGate"] is False
    return 2


def verify_golden_contracts() -> int:
    evidence = load_json("artifacts/g1-ir-003/verification.json")
    count = 0
    for record in evidence["goldenInputs"]:
        assert_file(record["path"], record["bytes"], record["sha256"])
        load_engineering_ir(ROOT / record["path"])
        count += 1
    expectations = evidence["expectations"]
    assert_file(expectations["path"], expectations["bytes"], expectations["sha256"])
    assert expectations["artifactsGenerated"] is False
    reference = load_engineering_ir(ROOT / evidence["goldenInputs"][0]["path"])
    canonical = serialize_engineering_ir(reference).encode("utf-8")
    assert len(canonical) == evidence["roundTrip"]["canonicalBytes"]
    assert sha256(canonical).hexdigest() == evidence["roundTrip"]["canonicalSha256"]
    return count + 1


def verify_migration_contracts() -> int:
    evidence = load_json("artifacts/g1-mig-001/verification.json")
    legacy_schema = evidence["legacySchema"]
    legacy_fixture = evidence["legacyFixture"]
    assert_file(legacy_schema["path"], legacy_schema["bytes"], legacy_schema["sha256"])
    assert_file(legacy_fixture["path"], legacy_fixture["bytes"], legacy_fixture["sha256"])
    source = load_json(legacy_fixture["path"])
    assert canonical_hash(source) == legacy_fixture["canonicalSha256"]
    result = migrate_engineering_ir(source)
    assert canonical_hash(result.document) == evidence["migratedDocument"]["canonicalSha256"]
    assert rollback_engineering_ir(result) == source
    return 2


def main() -> None:
    verified = (
        verify_cad_artifacts()
        + verify_drawing_artifacts()
        + verify_simulation_decision()
        + verify_golden_contracts()
        + verify_migration_contracts()
    )
    print(f"Artifact smoke test passed: {verified} records verified")


if __name__ == "__main__":
    main()
