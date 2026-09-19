import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFICATION_PATH = ROOT / "artifacts" / "g0-det-001" / "verification.json"
MANIFEST_PATH = ROOT / "artifacts" / "g0-cad" / "manifest.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_g0_det_001_verification_record_is_e3_and_complete() -> None:
    record = _load(VERIFICATION_PATH)
    assert record["schemaVersion"] == "1.0.0"
    assert record["workItem"] == "G0-DET-001"
    assert record["evidenceLevel"] == "E3"
    assert record["handoffFrom"]["workItem"] == "V3C-DET-001"
    assert record["fingerprintPolicy"]["version"] == "1.0.0"


def test_g0_det_001_replay_and_normalization_flags_are_true() -> None:
    record = _load(VERIFICATION_PATH)
    replay = record["replay"]
    assert replay["isolatedRuns"] == 2
    for flag in [
        "stepNormalizedByteHashEqual",
        "dxfNormalizedByteHashEqual",
        "stlNormalizedByteHashEqual",
        "allSemanticFingerprintsEqual",
        "sourceAndStepGeometryEqual",
    ]:
        assert replay[flag] is True
    for section in ("step", "dxf", "stl"):
        assert record["normalization"][section]["reloadValid"] is True


def test_g0_det_001_record_matches_tracked_reference_artifacts() -> None:
    record = _load(VERIFICATION_PATH)
    manifest = _load(MANIFEST_PATH)
    recorded = record["referenceArtifactFingerprints"]
    assert recorded["stepByteSha256"] == manifest["artifacts"]["step"]["byte_sha256"]
    assert recorded["stlByteSha256"] == manifest["artifacts"]["stl"]["byte_sha256"]
    assert recorded["dxfByteSha256"] == manifest["artifacts"]["dxf"]["byte_sha256"]
    assert recorded["geometrySemanticFingerprint"] == manifest["fingerprints"]["sourceGeometry"]["semanticFingerprint"]
    assert recorded["stlSemanticFingerprint"] == manifest["fingerprints"]["stlMesh"]["semanticFingerprint"]
    assert recorded["dxfSemanticFingerprint"] == manifest["fingerprints"]["dxfVectors"]["semanticFingerprint"]
    assert recorded["manifestSemanticFingerprint"] == manifest["manifestSemanticFingerprint"]["semanticFingerprint"]


def test_g0_det_001_maturity_scan_active_and_spike_maturity_null() -> None:
    record = _load(VERIFICATION_PATH)
    manifest = _load(MANIFEST_PATH)
    assert record["maturityScan"]["active"] is True
    assert record["maturityScan"]["spikeManifestsMaturityNull"] is True
    assert manifest["maturity"] is None
