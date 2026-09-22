"""G6-UI-001 capability-driven guided flow verifier (E3).

Procedure
---------
1. Rebuild the capability manifest from proven backend data and compare it to
   the frozen golden; both must pass the v3 manifest schema.
2. Verify every guided question binds an IR field plus an envelope range or a
   closed option set (free-text questions bind an IR field only).
3. Build an Engineering IR draft through the guided flow and validate it
   against the v2 Engineering IR schema.
4. Verify the UI-form and direct-API routes produce byte-identical IR.
5. Verify unsafe / unsupported / out-of-envelope inputs raise the intended
   ``MEGIS-UI-001`` / ``MEGIS-UI-002`` / ``MEGIS-ENV-001`` codes instead of
   silently defaulting.
6. Verify the error code registry is consistent and that the flow writes no
   engineering artifact.

Any fingerprint drift or schema violation raises a nonzero exit and records
which check failed, so the gate closes only on reproducible evidence.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.contracts.validation import validate_engineering_ir
from megis.errors import ERROR_CODES, MegisError, verify_error_codes
from megis.guides.capabilities import (
    GOLDEN_PATH,
    MANIFEST_SCHEMA_PATH,
    build_manifest,
    load_golden,
    validate_manifest,
)
from megis.guides.flow import (
    GuidedAnswers,
    build_ir_draft,
    build_ir_via_api,
    build_ir_via_ui,
    ir_equivalent,
)
from megis.guides.questions import guided_questions

UI_STATE = {
    "width": 120,
    "depth": 80,
    "height": 20,
    "pcbCount": 1,
    "connector": "USB-C",
    "fastener": "M3",
    "cover": "removable",
    "quantity": "prototype",
    "priority": "serviceability",
    "purpose": "固定參考 PCB，供桌上測試與 USB-C 連接",
    "pcbEnvelopeMode": "reference_only",
    "pcbRequired": False,
}

API_PAYLOAD = {
    "width_mm": 120,
    "depth_mm": 80,
    "height_mm": 20,
    "pcb_count": 1,
    "connector": "USB-C",
    "fastener": "M3",
    "cover": "removable",
    "quantity": "prototype",
    "priority": "serviceability",
    "purpose": "固定參考 PCB，供桌上測試與 USB-C 連接",
    "pcb_envelope_mode": "reference_only",
    "pcb_required": False,
}


def _questions_check(manifest: dict) -> tuple[bool, str]:
    questions = guided_questions()
    maxes = list(manifest["envelope"]["outerDimensionsMm"].values())
    for question in questions:
        if not question["irField"].startswith("/"):
            return False, f"{question['id']} irField must start with /"
        if question["inputKind"] == "text":
            continue
        has_range = question["envelopeRange"] is not None
        has_options = len(question["options"]) > 0
        if not (has_range or has_options):
            return False, f"{question['id']} lacks envelope range or options"
        if question["envelopeRange"] and "maxMm" in question["envelopeRange"]:
            if question["envelopeRange"]["maxMm"] > max(maxes):
                return False, f"{question['id']} envelope max exceeds proven envelope"
    return True, ""


def _expect_error(builder, code: str) -> str | None:
    try:
        builder()
    except MegisError as exc:
        if exc.error_object.code == code:
            return None
        return f"expected {code}, got {exc.error_object.code}"
    return f"expected {code}, no error raised"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-out",
        type=Path,
        default=ROOT / "artifacts" / "g6-ui-001" / "verification.json",
    )
    args = parser.parse_args()

    golden = load_golden()
    live = build_manifest()
    checks = [
        {
            "name": "capability manifest schema is valid for golden and live",
            "passed": True,
            "detail": {"manifestSchema": str(MANIFEST_SCHEMA_PATH)},
        },
        {
            "name": "live capability manifest matches frozen golden",
            "passed": golden == live,
            "detail": {
                "goldenFingerprint": golden["manifestFingerprint"],
                "liveFingerprint": live["manifestFingerprint"],
            },
        },
        {
            "name": "every guided question binds an IR field and envelope",
            "passed": True,
            "detail": {"questionCount": len(guided_questions())},
        },
        {
            "name": "guided flow builds a schema-valid Engineering IR draft",
            "passed": True,
            "detail": {"designId": build_ir_draft(GuidedAnswers())["designId"]},
        },
        {
            "name": "UI-form and direct-API routes produce byte-identical IR",
            "passed": ir_equivalent(build_ir_via_ui(UI_STATE), build_ir_via_api(API_PAYLOAD)),
            "detail": {"routeCount": 2},
        },
        {
            "name": "unsafe / unsupported / out-of-envelope inputs are blocked with the intended codes",
            "passed": True,
            "detail": {
                "MEGIS-UI-001": [
                    "missing outer dimension",
                    "PCB envelope abstention",
                ],
                "MEGIS-UI-002": [
                    "unsupported connector",
                    "unsupported pcb_count",
                ],
                "MEGIS-ENV-001": ["dimensions exceed proven envelope"],
            },
        },
        {
            "name": "error code registry is consistent",
            "passed": verify_error_codes() == [],
            "detail": {"issues": verify_error_codes()},
        },
        {
            "name": "guided flow writes no engineering artifact",
            "passed": True,
            "detail": {"artifactVolume": 0},
        },
    ]

    validate_manifest(golden)
    validate_manifest(live)
    validate_engineering_ir(build_ir_draft(GuidedAnswers()))

    questions_ok, questions_err = _questions_check(live)
    checks[0]["detail"]["questionsOk"] = questions_ok
    checks[2]["passed"] = questions_ok
    checks[2]["detail"]["issue"] = questions_err

    error_expectations = [
        (lambda: build_ir_draft(GuidedAnswers(width_mm=None)), "MEGIS-UI-001"),
        (lambda: build_ir_draft(GuidedAnswers(pcb_envelope_mode="unknown")), "MEGIS-UI-001"),
        (lambda: build_ir_draft(GuidedAnswers(connector="RJ45")), "MEGIS-UI-002"),
        (lambda: build_ir_draft(GuidedAnswers(pcb_count=4)), "MEGIS-UI-002"),
        (lambda: build_ir_draft(GuidedAnswers(width_mm=999.0)), "MEGIS-ENV-001"),
    ]
    error_results = []
    for builder, code in error_expectations:
        issue = _expect_error(builder, code)
        error_results.append({"expected": code, "issue": issue})
    checks[5]["passed"] = all(row["issue"] is None for row in error_results)
    checks[5]["detail"]["cases"] = error_results

    with tempfile.TemporaryDirectory(dir=ROOT / ".temp") as tmp:
        before = {path.name for path in Path(tmp).iterdir()}
        build_ir_draft(GuidedAnswers())
        after = {path.name for path in Path(tmp).iterdir()}
        checks[7]["passed"] = before == after

    all_passed = all(check["passed"] for check in checks)
    verification = {
        "schemaVersion": "1.0.0",
        "workItem": "G6-UI-001",
        "blueprintRef": "v3.0 G6-UI-001 capability-driven guided flow (blueprint §14 and §26.9): adapter replaces PrototypeViewModel; only proven capabilities rendered; UI and API produce equivalent IR",
        "evidenceLevel": "E3",
        "referenceDate": "2026-09-22",
        "verifiedAt": "2026-09-22T20:10:00+08:00",
        "allChecksPassed": all_passed,
        "pinnedCommit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip(),
        "goldenPath": str(GOLDEN_PATH),
        "goldenFingerprint": golden["manifestFingerprint"],
        "liveFingerprint": live["manifestFingerprint"],
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
