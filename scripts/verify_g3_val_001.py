"""Verify G3-VAL-001 geometry / collision / clearance validators.

Loads contracts/g3/golden/validation-corpus.json, validates it and every
produced Validation Result against the v3 schemas, runs each known pass/fail
case through the kernel-neutral AABBs validators and compares the observed
status and MEGIS-VAL-* codes to the golden expectations.  Only a small
verification.json is written; no engineering artifact is generated.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.errors import ERROR_CODES  # noqa: E402
from megis.validation import (  # noqa: E402
    DesignValidationInput,
    ValidationResult,
    validate_design,
)

CORPUS_PATH = ROOT / "contracts" / "g3" / "golden" / "validation-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "validation-corpus.schema.json"
RESULT_SCHEMA_PATH = ROOT / "schemas" / "v3" / "validation-result.schema.json"
OUT_PATH = ROOT / "artifacts" / "g3-val-001" / "verification.json"
CREATED_AT = "2026-09-21T21:30:00+08:00"


class Evidence:
    """Collect check results and keep the record machine-readable."""

    def __init__(self) -> None:
        self.checks: list[dict] = []
        self.failed = False

    def expect(self, name: str, condition: bool, detail: object) -> None:
        if not condition:
            self.failed = True
        self.checks.append(
            {
                "name": name,
                "passed": bool(condition),
                "detail": detail,
            }
        )


def codes_of(result: ValidationResult) -> list[str]:
    return sorted({issue.code for issue in result.checks if issue.code is not None})


def main() -> int:
    evidence = Evidence()
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    corpus_schema = json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))
    result_schema = json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(corpus_schema)
    Draft202012Validator.check_schema(result_schema)
    corpus_errors = list(Draft202012Validator(corpus_schema).iter_errors(corpus))
    evidence.expect(
        "golden corpus is schema conformant",
        corpus_errors == [],
        {"errors": [str(error.message) for error in corpus_errors]},
    )

    registered = {code: code in ERROR_CODES for code in (
        "MEGIS-VAL-001",
        "MEGIS-VAL-002",
        "MEGIS-VAL-003",
    )}
    evidence.expect(
        "validation error codes registered",
        all(registered.values()),
        registered,
    )

    case_results: list[dict] = []
    all_ok = True
    for case in corpus["cases"]:
        result = validate_design(
            DesignValidationInput.from_dict(case["input"]),
            validation_id=f"val-{case['case_id']}",
            design_ref=case["input"]["design_id"],
            created_at=CREATED_AT,
        )
        payload = result.to_dict()
        schema_ok = list(Draft202012Validator(result_schema).iter_errors(payload)) == []
        status_ok = result.status == case["expectStatus"]
        codes_ok = codes_of(result) == sorted(case["expectCodes"])
        case_ok = schema_ok and status_ok and codes_ok
        all_ok = all_ok and case_ok
        evidence.expect(
            f"case {case['case_id']} matches golden expectation",
            case_ok,
            {
                "expectStatus": case["expectStatus"],
                "status": result.status,
                "expectCodes": sorted(case["expectCodes"]),
                "codes": codes_of(result),
                "resultSchemaValid": schema_ok,
            },
        )
        case_results.append(
            {
                "case_id": case["case_id"],
                "status": result.status,
                "codes": codes_of(result),
                "checks": payload["summary"]["checks"],
            }
        )

    summary = {
        "allChecksPassed": not evidence.failed,
        "blueprintRef": "v3.0 26.6 G3-VAL-001、4.10 MEGIS-VAL",
        "evidenceLevel": "E3",
        "referenceDate": "2026-09-21",
        "schemaVersion": "1.0.0",
        "workItem": "G3-VAL-001",
        "verifiedAt": CREATED_AT,
        "engineeringArtifactGenerated": False,
        "releaseArtifactGenerated": False,
        "input": {
            "corpus": str(CORPUS_PATH.relative_to(ROOT)),
            "corpusSchema": str(CORPUS_SCHEMA_PATH.relative_to(ROOT)),
            "resultSchema": str(RESULT_SCHEMA_PATH.relative_to(ROOT)),
        },
        "summary": {
            "cases": len(corpus["cases"]),
            "passedCases": sum(1 for item in case_results if item["status"] == "pass"),
            "failedCases": sum(1 for item in case_results if item["status"] != "pass"),
        },
        "checks": evidence.checks,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if not evidence.failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
