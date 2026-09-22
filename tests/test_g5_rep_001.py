"""G5-REP-001 clean-environment reproducibility tests (E3).

The reproducibility contract is the semantic fingerprint: a clean rebuild of
the golden IR with the locked toolchain must reproduce the frozen hashes in
``contracts/g5/golden/repro-fingerprints.json`` for every prototype artifact.
``bom.csv`` / ``draft_drawing.svg`` / ``reference_case.stl`` are additionally
byte-stable; the STEP/DXF exporters embed run metadata, so their bytes may
differ between runs while the semantic fingerprints stay identical.
"""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path


from megis.errors import ERROR_CODES, verify_error_codes
from megis.package import (
    REPRO_ARTIFACT_NAMES,
    REPRO_BYTE_STABLE,
    REPRO_BUILDER_VERSION,
    build_fingerprint_report,
    compare_to_golden,
    rebuild_prototype_outputs,
    validate_golden,
)
from megis.package.manifest import semantic_fingerprint_for_path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "contracts" / "g5" / "golden" / "repro-fingerprints.json"
G0_CAD_FILES = {
    "reference_case.step": "reference_case.step",
    "reference_case.stl": "reference_case.stl",
    "reference_case_section_z10.dxf": "reference_case_section_z10.dxf",
}

def _load_golden() -> dict:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))

def test_golden_is_schema_conformant() -> None:
    golden = _load_golden()
    validate_golden(golden)
    assert golden["corpusId"] == "g5-repro-fingerprints@1.0.0"
    assert golden["builderVersion"] == REPRO_BUILDER_VERSION
    assert set(golden["artifacts"]) == set(REPRO_ARTIFACT_NAMES)

def test_rebuild_is_deterministic_and_matches_golden(tmp_path: Path) -> None:
    golden = _load_golden()
    first = rebuild_prototype_outputs(tmp_path / "run-1")
    second = rebuild_prototype_outputs(tmp_path / "run-2")

    # Every semantic fingerprint matches; byte-stable artifacts byte-identical.
    comparison = compare_to_golden(second, golden)
    assert comparison["identical"], comparison["differences"]
    assert first["reportFingerprint"] == second["reportFingerprint"]
    assert first["reportFingerprint"] == golden["reportFingerprint"]

    for name in REPRO_ARTIFACT_NAMES:
        assert (
            first["artifacts"][name]["semanticFingerprint"]
            == second["artifacts"][name]["semanticFingerprint"]
            == golden["artifacts"][name]["semanticFingerprint"]
        )

def test_text_outputs_are_byte_identical_across_runs(tmp_path: Path) -> None:
    first_dir = tmp_path / "run-a"
    second_dir = tmp_path / "run-b"
    rebuild_prototype_outputs(first_dir)
    rebuild_prototype_outputs(second_dir)

    for name in ("bom.csv", "draft_drawing.svg"):
        left = (first_dir / name).read_bytes()
        right = (second_dir / name).read_bytes()
        assert left == right
        assert sha256(left).hexdigest() == _load_golden()["artifacts"][name]["byte_sha256"]

def test_step_dxf_byte_drift_is_semantic_only(tmp_path: Path) -> None:
    """STEP/DXF bytes may carry exporter metadata; semantic fingerprints must stay fixed."""
    first_dir = tmp_path / "run-a"
    second_dir = tmp_path / "run-b"
    rebuild_prototype_outputs(first_dir)
    rebuild_prototype_outputs(second_dir)
    first_report = build_fingerprint_report(first_dir)
    second_report = build_fingerprint_report(second_dir)

    for name in ("reference_case.step", "reference_case_section_z10.dxf"):
        assert REPRO_BYTE_STABLE[name] is False
        assert (
            first_report["artifacts"][name]["semanticFingerprint"]
            == second_report["artifacts"][name]["semanticFingerprint"]
        )
    # The report fingerprint ignores byte-level exporter metadata drift.
    assert first_report["reportFingerprint"] == second_report["reportFingerprint"]

def test_committed_g0_cad_semantic_fingerprints_match_golden() -> None:
    """Clean rebuilds must reproduce the delivered CAD content fingerprints."""
    golden = _load_golden()
    g0_dir = ROOT / "artifacts" / "g0-cad"
    for golden_name, file_name in G0_CAD_FILES.items():
        fingerprint, _ = semantic_fingerprint_for_path(g0_dir / file_name)
        assert fingerprint == golden["artifacts"][golden_name]["semanticFingerprint"]

def test_drift_detection_and_error_code(tmp_path: Path) -> None:
    golden = _load_golden()

    tampered = tmp_path / "tampered"
    rebuild_prototype_outputs(tampered)
    # Mutate the BOM bytes; the rebuilt report must no longer match the golden.
    bom_path = tampered / "bom.csv"
    bom_path.write_text(bom_path.read_text(encoding="utf-8") + "extra,line\n", encoding="utf-8")
    drifted = build_fingerprint_report(tampered)

    comparison = compare_to_golden(drifted, golden)
    assert comparison["identical"] is False
    assert any(item["artifact"] == "bom.csv" for item in comparison["differences"])

    assert "MEGIS-REP-001" in ERROR_CODES
    assert verify_error_codes() == []
    assert ERROR_CODES["MEGIS-REP-001"].domain.value == "REP"
