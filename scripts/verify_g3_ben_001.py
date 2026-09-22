"""Verify G3-BEN-001 benchmark runner and metrics.

Validates both the dev corpus and the sealed holdout corpus against the v3
benchmark schemas, verifies the holdout SHA-256 still matches the value sealed
in ``docs/ACCEPTANCE.md`` (R-AGT-002), runs every case through the real
validation, rule and maturity components, then checks that the produced KPI
metrics reach the G3-BEN-001 target (recall 1.0, precision 1.0, zero false
positives, zero false releases).  Only a small verification.json is written;
no engineering artifact is generated.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.benchmark import run_benchmark  # noqa: E402
from megis.benchmark.metrics import BENCHMARK_VERSION  # noqa: E402

DEV_CORPUS_PATH = ROOT / "contracts" / "g3" / "golden" / "benchmark-corpus.json"
HOLDOUT_CORPUS_PATH = ROOT / "contracts" / "g3" / "holdout" / "holdout-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "benchmark-corpus.schema.json"
REPORT_SCHEMA_PATH = ROOT / "schemas" / "v3" / "benchmark-report.schema.json"
OUT_PATH = ROOT / "artifacts" / "g3-ben-001" / "verification.json"
CREATED_AT = "2026-09-22T13:00:00+08:00"
SEALED_HOLDOUT_SHA256 = (
    "73a25950c4b45d904daa6bab963a16ae11599f6bfa660966582ba0d60ed5a96b"
)


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


def _unique(cases: list[dict]) -> bool:
    ids = [case["case_id"] for case in cases]
    return len(ids) == len(set(ids))


def _oracle_coherent(corpus: dict) -> bool:
    for case in corpus["cases"]:
        oracle = case["oracle"]
        if oracle["error_grade"] != (oracle["expected_max_severity"] == "error"):
            return False
        if oracle["expect_false_release"] and oracle["expected_max_severity"] == "pass":
            return False
    return True


def _report_schema_errors(corpus_path: Path, schema_path: Path) -> list[str]:
    report_schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(report_schema)
    payload = run_benchmark(corpus_path).to_dict()
    return [
        str(error.message)
        for error in Draft202012Validator(report_schema).iter_errors(payload)
    ]


def main() -> int:
    evidence = Evidence()
    dev_corpus = json.loads(DEV_CORPUS_PATH.read_text(encoding="utf-8"))
    holdout_corpus = json.loads(HOLDOUT_CORPUS_PATH.read_text(encoding="utf-8"))
    corpus_schema = json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))
    report_schema = json.loads(REPORT_SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(corpus_schema)
    Draft202012Validator.check_schema(report_schema)

    dev_schema_errors = list(
        Draft202012Validator(corpus_schema).iter_errors(dev_corpus)
    )
    holdout_schema_errors = list(
        Draft202012Validator(corpus_schema).iter_errors(holdout_corpus)
    )
    evidence.expect(
        "dev corpus is schema conformant",
        dev_schema_errors == [],
        {"errors": [str(error.message) for error in dev_schema_errors]},
    )
    evidence.expect(
        "holdout corpus is schema conformant",
        holdout_schema_errors == [],
        {"errors": [str(error.message) for error in holdout_schema_errors]},
    )
    evidence.expect(
        "case ids are unique across corpora",
        _unique(dev_corpus["cases"]) and _unique(holdout_corpus["cases"]),
        {"dev": len(dev_corpus["cases"]), "holdout": len(holdout_corpus["cases"])},
    )
    evidence.expect(
        "oracles are internally coherent",
        _oracle_coherent(dev_corpus) and _oracle_coherent(holdout_corpus),
        {},
    )

    dev_defect = sum(
        1 for case in dev_corpus["cases"] if case["severity_class"] == "defect"
    )
    dev_clean = sum(
        1 for case in dev_corpus["cases"] if case["severity_class"] == "clean"
    )
    evidence.expect(
        "dev corpus reaches G3-BEN-001 scale (defect >= 30, clean >= 10)",
        dev_defect >= 30 and dev_clean >= 10,
        {"defect": dev_defect, "clean": dev_clean},
    )

    holdout_digest = sha256(HOLDOUT_CORPUS_PATH.read_bytes()).hexdigest()
    holdout_defect = sum(
        1 for case in holdout_corpus["cases"] if case["severity_class"] == "defect"
    )
    holdout_clean = sum(
        1 for case in holdout_corpus["cases"] if case["severity_class"] == "clean"
    )
    evidence.expect(
        "holdout corpus hash matches the sealed oracle (R-AGT-002)",
        holdout_digest == SEALED_HOLDOUT_SHA256,
        {
            "sha256": holdout_digest,
            "sealed": SEALED_HOLDOUT_SHA256,
            "defect": holdout_defect,
            "clean": holdout_clean,
        },
    )

    dev_report = run_benchmark(DEV_CORPUS_PATH, created_at=CREATED_AT)
    dev_payload = dev_report.to_dict()
    dev_metrics = dev_report.metrics()

    dev_cases_passed = all(case.passed for case in dev_report.cases)
    evidence.expect(
        "every dev corpus case passes its oracle",
        dev_cases_passed,
        {
            "cases": len(dev_report.cases),
            "failed": [
                case.case_id
                for case in dev_report.cases
                if not case.passed
            ],
        },
    )
    evidence.expect(
        "dev benchmark recall and precision reach 1.0",
        dev_metrics["recall"] == 1.0 and dev_metrics["precision"] == 1.0,
        {
            "recall": dev_metrics["recall"],
            "recallCI95": dev_metrics["recallCI95"],
            "precision": dev_metrics["precision"],
            "precisionCI95": dev_metrics["precisionCI95"],
        },
    )
    evidence.expect(
        "dev benchmark reports zero false positives and zero false releases",
        dev_metrics["falsePositives"] == 0
        and dev_metrics["falseReleaseCount"] == 0,
        {
            "falsePositives": dev_metrics["falsePositives"],
            "falseReleases": dev_metrics["falseReleaseCount"],
        },
    )
    evidence.expect(
        "dev benchmark report is report-schema conformant",
        _report_schema_errors(DEV_CORPUS_PATH, REPORT_SCHEMA_PATH) == [],
        {},
    )

    holdout_report = run_benchmark(HOLDOUT_CORPUS_PATH, created_at=CREATED_AT)
    holdout_payload = holdout_report.to_dict()
    holdout_metrics = holdout_report.metrics()
    holdout_cases_passed = all(case.passed for case in holdout_report.cases)
    evidence.expect(
        "every holdout case passes its sealed oracle",
        holdout_cases_passed,
        {
            "cases": len(holdout_report.cases),
            "failed": [
                case.case_id
                for case in holdout_report.cases
                if not case.passed
            ],
        },
    )
    evidence.expect(
        "holdout benchmark reports zero false positives and zero false releases",
        holdout_metrics["falsePositives"] == 0
        and holdout_metrics["falseReleaseCount"] == 0,
        {
            "falsePositives": holdout_metrics["falsePositives"],
            "falseReleases": holdout_metrics["falseReleaseCount"],
        },
    )
    evidence.expect(
        "holdout benchmark report is report-schema conformant",
        _report_schema_errors(HOLDOUT_CORPUS_PATH, REPORT_SCHEMA_PATH) == [],
        {},
    )

    summary = {
        "schemaVersion": "1.0.0",
        "workItem": "G3-BEN-001",
        "runtime": BENCHMARK_VERSION,
        "createdAt": CREATED_AT,
        "blueprintRef": "v3.0 1.3 reference case, 11.6 validation gate, 26.7 G3-BEN-001",
        "evidenceLevel": "E3",
        "allChecksPassed": not evidence.failed,
        "engineeringArtifactGenerated": False,
        "releaseArtifactGenerated": False,
        "inputs": {
            "devCorpus": str(DEV_CORPUS_PATH.relative_to(ROOT)),
            "holdoutCorpus": str(HOLDOUT_CORPUS_PATH.relative_to(ROOT)),
            "corpusSchema": str(CORPUS_SCHEMA_PATH.relative_to(ROOT)),
            "reportSchema": str(REPORT_SCHEMA_PATH.relative_to(ROOT)),
            "holdoutSha256": SEALED_HOLDOUT_SHA256,
        },
        "dev": {
            "corpusId": dev_payload["corpus_id"],
            "cases": len(dev_report.cases),
            "defectCases": dev_metrics["defectCases"],
            "cleanCases": dev_metrics["cleanCases"],
            "metrics": dev_metrics,
            "allCasesPassed": dev_cases_passed,
        },
        "holdout": {
            "corpusId": holdout_payload["corpus_id"],
            "cases": len(holdout_report.cases),
            "sha256": holdout_digest,
            "metrics": holdout_metrics,
            "allCasesPassed": holdout_cases_passed,
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
