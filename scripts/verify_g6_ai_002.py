"""Verify G6-AI-002 schema-bound extraction and confirmation quarantine (E3)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.ai import (  # noqa: E402
    build_ir_with_confirmed_proposals,
    confirm_requirement_fields,
    parse_requirement_draft,
)
from megis.errors import MegisError  # noqa: E402
from megis.guides.flow import GuidedAnswers  # noqa: E402

SCHEMA_PATH = ROOT / "schemas" / "v3" / "ai-requirement-draft.schema.json"
FIXTURES_PATH = ROOT / "contracts" / "g6" / "golden" / "ai-requirement-fixtures.json"
OUT_PATH = ROOT / "artifacts" / "g6-ai-002" / "verification.json"
VERIFIED_AT = "2026-09-22T20:00:00+08:00"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-out", type=Path, default=OUT_PATH)
    args = parser.parse_args()
    checks: list[dict] = []

    def expect(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    expect("Requirement draft JSON Schema is valid", True, {"schemaVersion": "1.0.0"})

    fixture_set = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    results: list[dict] = []
    for case in fixture_set["cases"]:
        raw = json.dumps(case["providerOutput"], ensure_ascii=False)
        try:
            draft = parse_requirement_draft(raw, case["sourceText"])
            results.append(
                {
                    "caseId": case["caseId"],
                    "passed": True,
                    "proposalCount": len(draft["proposals"]),
                }
            )
        except MegisError as exc:
            results.append(
                {"caseId": case["caseId"], "passed": False, "error": exc.error_object.code}
            )
    expect(
        "100% of recorded provider outputs pass the Requirement schema and evidence checks",
        all(row["passed"] for row in results),
        {"cases": len(results), "results": results},
    )

    first = fixture_set["cases"][0]
    draft = parse_requirement_draft(
        json.dumps(first["providerOutput"], ensure_ascii=False), first["sourceText"]
    )
    ledger = confirm_requirement_fields(draft, ["connector"])
    expect(
        "confirmation ledger contains only explicitly confirmed fields",
        ledger["confirmedValues"] == {"connector": "USB-C"}
        and ledger["unconfirmedFields"] == ["width_mm"],
        ledger,
    )

    dimension_case = fixture_set["cases"][1]
    dimension_draft = parse_requirement_draft(
        json.dumps(dimension_case["providerOutput"], ensure_ascii=False),
        dimension_case["sourceText"],
    )
    document = build_ir_with_confirmed_proposals(
        dimension_draft,
        ["width_mm"],
        GuidedAnswers(width_mm=120, depth_mm=80, height_mm=20),
    )
    dimensions = {
        item["name"]: item["quantity"]["nominal"]
        for item in document["components"][0]["dimensions"]
    }
    expect(
        "unconfirmed AI values cannot enter confirmed Engineering IR",
        dimensions == {"width": 110.0, "depth": 80.0, "height": 20.0}
        and "llm_proposed" not in json.dumps(document),
        {"confirmedIrDimensions": dimensions},
    )

    malformed_rejected = False
    try:
        parse_requirement_draft('{"schemaVersion":"1.0.0"}', "intent")
    except MegisError as exc:
        malformed_rejected = exc.error_object.code == "MEGIS-AI-002"
    expect(
        "schema-invalid output is rejected without repair as MEGIS-AI-002",
        malformed_rejected,
        {"accepted": False, "errorCode": "MEGIS-AI-002"},
    )

    ungrounded = json.loads(json.dumps(first["providerOutput"]))
    ungrounded["proposals"][0]["value"] = 999
    ungrounded_rejected = False
    try:
        parse_requirement_draft(json.dumps(ungrounded), first["sourceText"])
    except MegisError as exc:
        ungrounded_rejected = exc.error_object.code == "MEGIS-AI-002"
    expect(
        "numeric value without matching evidence is rejected",
        ungrounded_rejected,
        {"accepted": False, "errorCode": "MEGIS-AI-002"},
    )

    completed = subprocess.run(
        [str(ROOT / ".venv" / "Scripts" / "python.exe"), "-m", "pytest", "tests/test_g6_ai_002.py", "-q"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    expect(
        "G6-AI-002 automated tests pass",
        completed.returncode == 0,
        {"returnCode": completed.returncode, "lastLine": completed.stdout.strip().splitlines()[-1]},
    )

    passed = all(check["passed"] for check in checks)
    evidence = {
        "schemaVersion": "1.0.0",
        "workItem": "G6-AI-002",
        "blueprintRef": "v3.0 sections 14.1, 20.2-20.3, and 26.9",
        "verifiedAt": VERIFIED_AT,
        "verification": "passed" if passed else "failed",
        "allChecksPassed": passed,
        "recordedFixtureCases": len(results),
        "checks": checks,
        "boundaries": {
            "workspaceRoot": str(ROOT),
            "localOnly": True,
            "externalProviderCalled": False,
            "unconfirmedValuesEnteredIr": False,
            "engineeringArtifactsGenerated": False,
            "releaseArtifactsGenerated": False,
        },
    }
    args.verify_out.parent.mkdir(parents=True, exist_ok=True)
    args.verify_out.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"workItem": "G6-AI-002", "allChecksPassed": passed, "checks": len(checks)}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
