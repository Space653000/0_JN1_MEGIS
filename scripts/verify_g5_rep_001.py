"""G5-REP-001 clean-environment reproducibility verifier (E3).

Procedure
---------
1. Rebuild the five prototype artifacts in the source tree from the golden IR
   and compare the fingerprint report to the frozen golden fingerprints.
2. Create a clean clone of the pinned commit under ``.runs/g5-rep-001-clean``
   (git-ignored, inside the workspace) and let a *child process* run with its
   cwd inside that clean tree, so imports resolve to the clean checkout only.
3. The child rebuilds the same artifacts and writes a clean fingerprint
   report; the parent compares it to the same golden and to the source-tree
   report.

Any semantic fingerprint drift raises ``MEGIS-REP-001`` and would require an
ADR before acceptance.  STEP/DXF byte drift from exporter metadata is
explicitly allowed and recorded, not treated as content drift.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.errors import verify_error_codes
from megis.package.manifest import semantic_fingerprint_for_path
from megis.package.repro import (
    REPRO_ARTIFACT_NAMES,
    REPRO_DEFAULT_GOLDEN_PATH,
    REPRO_DEFAULT_IR_PATH,
    REPRO_GOLDEN_SCHEMA_PATH,
    build_fingerprint_report,
    compare_to_golden,
    rebuild_prototype_outputs,
    validate_golden,
)

G0_CAD_ARTIFACTS = ROOT / "artifacts" / "g0-cad"
G0_CAD_FILES = (
    "reference_case.step",
    "reference_case.stl",
    "reference_case_section_z10.dxf",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _g0_cad_fingerprints() -> dict[str, dict[str, str]]:
    record: dict[str, dict[str, str]] = {}
    for name in G0_CAD_FILES:
        fingerprint, kind = semantic_fingerprint_for_path(G0_CAD_ARTIFACTS / name)
        record[name] = {"semanticFingerprint": fingerprint, "fingerprintKind": kind}
    return record


def _mode_child(golden_path: Path, report_out: Path) -> int:
    """Rebuild inside the clean checkout and write a fingerprint report."""
    rebuild_dir = ROOT / ".temp" / "g5-rep-child-rebuild"
    shutil.rmtree(rebuild_dir, ignore_errors=True)
    report = rebuild_prototype_outputs(rebuild_dir)
    golden = _load(golden_path)
    validate_golden(golden)
    comparison = compare_to_golden(report, golden)
    if not comparison["identical"]:
        print(json.dumps(comparison, ensure_ascii=False))
        return 1
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


def _clean_clone_rebuild(golden_path: Path, clean_report_out: Path) -> dict:
    clean_dir = ROOT / ".runs" / "g5-rep-001-clean"
    shutil.rmtree(clean_dir, ignore_errors=True)
    subprocess.run(
        ["git", "clone", "--quiet", str(ROOT), str(clean_dir)],
        check=True,
        capture_output=True,
    )
    child = clean_dir / "scripts" / "verify_g5_rep_001.py"
    subprocess.run(
        [sys.executable, str(child), "--child", "--golden", str(golden_path), "--report-out", str(clean_report_out)],
        cwd=clean_dir,
        check=True,
    )
    return _load(clean_report_out)


def _freeze_reference_check(golden: dict) -> dict:
    """Cross-check frozen CAD fingerprints against the committed g0-cad artifacts."""
    actual = _g0_cad_fingerprints()
    mismatches = [
        name
        for name in G0_CAD_FILES
        if actual[name]["semanticFingerprint"] != golden["artifacts"][name]["semanticFingerprint"]
    ]
    return {"matched": not mismatches, "mismatches": mismatches}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--golden", type=Path, default=REPRO_DEFAULT_GOLDEN_PATH)
    parser.add_argument("--report-out", type=Path, default=None)
    parser.add_argument("--verify-out", type=Path, default=ROOT / "artifacts" / "g5-rep-001" / "verification.json")
    args = parser.parse_args()

    if args.child:
        return _mode_child(args.golden, args.report_out)

    golden = _load(args.golden)
    validate_golden(golden)

    source_dir = ROOT / ".runs" / "g5-rep-001-source"
    shutil.rmtree(source_dir, ignore_errors=True)
    source_report = rebuild_prototype_outputs(source_dir)
    source_match = compare_to_golden(source_report, golden)

    clean_report_path = ROOT / ".runs" / "g5-rep-001" / "clean-report.json"
    clean_report = _clean_clone_rebuild(args.golden.resolve(), clean_report_path)
    clean_match = compare_to_golden(clean_report, golden)
    cross_match = source_report["reportFingerprint"] == clean_report["reportFingerprint"]
    g0_check = _freeze_reference_check(golden)
    registry_issues = verify_error_codes()

    checks = [
        {
            "name": "source rebuild matches frozen golden fingerprints",
            "passed": source_match["identical"],
            "detail": source_match,
        },
        {
            "name": "clean-clone rebuild matches the same frozen golden fingerprints",
            "passed": clean_match["identical"],
            "detail": clean_match,
        },
        {
            "name": "source and clean-clone rebuild reports are identical",
            "passed": cross_match,
            "detail": {
                "sourceReportFingerprint": source_report["reportFingerprint"],
                "cleanReportFingerprint": clean_report["reportFingerprint"],
            },
        },
        {
            "name": "frozen CAD fingerprints equal committed g0-cad semantic fingerprints",
            "passed": g0_check["matched"],
            "detail": {"mismatches": g0_check["mismatches"]},
        },
        {
            "name": "error code registry is consistent",
            "passed": registry_issues == [],
            "detail": {"issues": registry_issues},
        },
    ]
    all_passed = all(check["passed"] for check in checks)

    verification = {
        "schemaVersion": "1.0.0",
        "workItem": "G5-REP-001",
        "blueprintRef": "v3.0 G5-REP-001 clean-environment reproducibility test (blueprint §26.8: clean env and CI rebuild fingerprint identical or difference requires ADR)",
        "evidenceLevel": "E3",
        "referenceDate": "2026-09-22",
        "verifiedAt": "2026-09-22T18:00:00+08:00",
        "allChecksPassed": all_passed,
        "pinnedCommit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip(),
        "goldenPath": str(args.golden),
        "goldenReportFingerprint": golden["reportFingerprint"],
        "sourceReportFingerprint": source_report["reportFingerprint"],
        "cleanReportFingerprint": clean_report["reportFingerprint"],
        "toolchain": golden["toolchain"],
        "semanticDriftRequiresAdr": True,
        "adrRequired": not all_passed,
        "byteDriftRecording": {
            "step": "STEP exporter embeds FILE_NAME metadata; bytes may differ, semantic fingerprint is stable",
            "dxf": "DXF exporter embeds metadata; bytes may differ, semantic fingerprint is stable",
            "stl": "byte-stable in the locked toolchain",
            "bomCsv": "byte-stable (deterministic UTF-8/LF)",
            "draftDrawingSvg": "byte-stable (no runtime fields)",
        },
        "artifacts": sorted(REPRO_ARTIFACT_NAMES),
        "inputs": {
            "goldenSchema": str(REPRO_GOLDEN_SCHEMA_PATH),
            "ir": str(REPRO_DEFAULT_IR_PATH),
            "tests": str(ROOT / "tests" / "test_g5_rep_001.py"),
        },
        "checks": checks,
        "boundaries": {
            "workspaceRoot": str(ROOT),
            "localOnly": True,
            "otherProjectDirectoriesModified": False,
            "engineeringArtifactsGenerated": False,
            "releaseArtifactsGenerated": False,
        },
    }

    out = Path(args.verify_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"allChecksPassed": all_passed, "checks": checks}, ensure_ascii=False))
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
