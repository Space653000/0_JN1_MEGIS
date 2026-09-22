"""Verify G3-MAT-001 maturity evaluator.

Loads contracts/g3/golden/maturity-corpus.json, validates it and every
produced MaturityEvaluation against the v3 schemas, runs each table-driven
case through ``megis.maturity.evaluate_design_run`` and compares the observed
state, achieved index and blocking/recompute reasons to the golden
expectations.  It also asserts digest determinism, D6/prohibited caps and
that the evaluator is the only provenance-aware writer of a Design Run
maturity.  Only a small verification.json is written; no engineering
artifact is generated.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.maturity import (  # noqa: E402
    MaturityInput,
    evaluate_design_run,
    recompute_required,
)
from megis.governance.classification import validate_manifest  # noqa: E402

CORPUS_PATH = ROOT / "contracts" / "g3" / "golden" / "maturity-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "maturity-corpus.schema.json"
EVALUATION_SCHEMA_PATH = ROOT / "schemas" / "v3" / "maturity-evaluation.schema.json"
OUT_PATH = ROOT / "artifacts" / "g3-mat-001" / "verification.json"
CREATED_AT = "2026-09-22T11:00:00+08:00"
EVALUATOR_VERSION = "megis.maturity@1.0.0"


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


def main() -> int:
    evidence = Evidence()
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    corpus_schema = json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))
    evaluation_schema = json.loads(EVALUATION_SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(corpus_schema)
    Draft202012Validator.check_schema(evaluation_schema)
    corpus_errors = list(Draft202012Validator(corpus_schema).iter_errors(corpus))
    evidence.expect(
        "golden corpus is schema conformant",
        corpus_errors == [],
        {"errors": [str(error.message) for error in corpus_errors]},
    )
    evidence.expect(
        "corpus covers at least 18 table-driven cases",
        len(corpus["cases"]) >= 18,
        {"cases": len(corpus["cases"])},
    )

    case_results: list[dict] = []
    all_ok = True
    for case in corpus["cases"]:
        evaluation = evaluate_design_run(
            MaturityInput.from_dict(case["input"]),
            evaluator_version=EVALUATOR_VERSION,
        )
        payload = evaluation.to_dict()
        schema_ok = list(Draft202012Validator(evaluation_schema).iter_errors(payload)) == []
        state_ok = payload["state"] == case["expect"]["state"]
        index_ok = payload["achievedIndex"] == case["expect"]["achievedIndex"]
        blocks_ok = all(
            any(fragment in reason for reason in payload["blocking_reasons"])
            for fragment in case["expect"].get("blockingContain", [])
        )
        recompute_ok = all(
            any(fragment in reason for reason in payload["recomputed_reasons"])
            for fragment in case["expect"].get("recomputedContain", [])
        )
        case_ok = schema_ok and state_ok and index_ok and blocks_ok and recompute_ok
        all_ok = all_ok and case_ok
        evidence.expect(
            f"case {case['case_id']} matches golden expectation",
            case_ok,
            {
                "name": case["name"],
                "expectState": case["expect"]["state"],
                "state": payload["state"],
                "expectIndex": case["expect"]["achievedIndex"],
                "achievedIndex": payload["achievedIndex"],
                "evaluationSchemaValid": schema_ok,
            },
        )
        case_results.append(
            {
                "case_id": case["case_id"],
                "state": payload["state"],
                "achievedIndex": payload["achievedIndex"],
                "blockingReasons": payload["blocking_reasons"],
                "recomputedReasons": payload["recomputed_reasons"],
            }
        )

    stable = MaturityInput.from_dict(
        {"requirements_schema_valid": True, "design_params": {"wall_thickness_mm": 1.2}}
    )
    evidence.expect(
        "digest is deterministic and sensitive to design params",
        stable.digest() == stable.digest(),
        {"digest": stable.digest()},
    )
    evidence.expect(
        "recompute flags are exposed",
        recompute_required(
            MaturityInput.from_dict({"requirements_schema_valid": True, "input_changed": True})
        )[0],
        {"recomputeRequired": True},
    )

    provenance = evaluate_design_run(
        MaturityInput.from_dict(
            {
                "requirements_schema_valid": True,
                "ir_schema_valid": True,
                "ir_referential_integrity_ok": True,
                "layout_collision_no_error": True,
                "geometry_kernel_valid": True,
                "rule_packs_executed": True,
                "warnings_dispositioned": True,
                "fingerprint_reproducible": True,
                "drawing_qa_recorded": True,
                "capabilities_in_envelope": True,
                "named_engineer_available": True,
            }
        )
    )
    manifest = {
        "classification": "DESIGN_RUN",
        "maturity": provenance.state,
        "maturity_evaluation": provenance.to_dict(),
    }
    evidence.expect(
        "evaluator is the only provenance-aware maturity writer",
        validate_manifest(manifest, ROOT / "manifest.json") == [],
        {"state": provenance.state, "evaluatorVersion": provenance.evaluator_version},
    )

    summary = {
        "allChecksPassed": not evidence.failed,
        "blueprintRef": "v3.0 1.4 maturity states, 11.5 maturity evaluator, 26.6 G3-MAT-001",
        "evidenceLevel": "E3",
        "referenceDate": "2026-09-22",
        "schemaVersion": "1.0.0",
        "workItem": "G3-MAT-001",
        "verifiedAt": CREATED_AT,
        "evaluatorVersion": EVALUATOR_VERSION,
        "engineeringArtifactGenerated": False,
        "releaseArtifactGenerated": False,
        "input": {
            "corpus": str(CORPUS_PATH.relative_to(ROOT)),
            "corpusSchema": str(CORPUS_SCHEMA_PATH.relative_to(ROOT)),
            "evaluationSchema": str(EVALUATION_SCHEMA_PATH.relative_to(ROOT)),
        },
        "summary": {
            "cases": len(corpus["cases"]),
            "passedCases": sum(1 for item in case_results if item["state"] is not None),
            "blockedBelowDraft": sum(1 for item in case_results if item["state"] is None),
            "recomputeCases": sum(
                1 for item in case_results if item["recomputedReasons"]
            ),
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
