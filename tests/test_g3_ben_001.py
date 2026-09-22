"""G3-BEN-001 benchmark runner and KPI table-driven tests (E3)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from megis.benchmark import run_benchmark, wilson_ci
from megis.benchmark.metrics import BENCHMARK_VERSION, SEVERITY_ORDER

ROOT = Path(__file__).resolve().parents[1]
DEV_CORPUS_PATH = ROOT / "contracts" / "g3" / "golden" / "benchmark-corpus.json"
HOLDOUT_CORPUS_PATH = ROOT / "contracts" / "g3" / "holdout" / "holdout-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "benchmark-corpus.schema.json"
REPORT_SCHEMA_PATH = ROOT / "schemas" / "v3" / "benchmark-report.schema.json"
# Sealed by docs/ACCEPTANCE.md R-AGT-002 before any metrics were implemented.
SEALED_HOLDOUT_SHA256 = (
    "73a25950c4b45d904daa6bab963a16ae11599f6bfa660966582ba0d60ed5a96b"
)


@pytest.fixture(scope="module")
def corpus_schema() -> dict:
    return json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def report_schema() -> dict:
    return json.loads(REPORT_SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def dev_corpus() -> dict:
    return json.loads(DEV_CORPUS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def holdout_corpus() -> dict:
    return json.loads(HOLDOUT_CORPUS_PATH.read_text(encoding="utf-8"))


def _assert_report_schema_conformant(report: dict, report_schema: dict) -> None:
    Draft202012Validator.check_schema(report_schema)
    errors = list(Draft202012Validator(report_schema).iter_errors(report))
    assert errors == []


def test_corpora_validate_against_schema(
    dev_corpus: dict,
    holdout_corpus: dict,
    corpus_schema: dict,
) -> None:
    Draft202012Validator.check_schema(corpus_schema)
    for corpus in (dev_corpus, holdout_corpus):
        errors = list(Draft202012Validator(corpus_schema).iter_errors(corpus))
        assert errors == []
        assert len(corpus["cases"]) >= 1


def test_dev_corpus_meets_required_scale(dev_corpus: dict) -> None:
    defect = [
        case for case in dev_corpus["cases"] if case["severity_class"] == "defect"
    ]
    clean = [
        case for case in dev_corpus["cases"] if case["severity_class"] == "clean"
    ]
    assert len(defect) >= 30
    assert len(clean) >= 10


def test_case_ids_are_unique(dev_corpus: dict, holdout_corpus: dict) -> None:
    for corpus in (dev_corpus, holdout_corpus):
        ids = [case["case_id"] for case in corpus["cases"]]
        assert len(ids) == len(set(ids))


def test_holdout_is_sealed_and_unmodified() -> None:
    digest = hashlib.sha256(HOLDOUT_CORPUS_PATH.read_bytes()).hexdigest()
    assert digest == SEALED_HOLDOUT_SHA256
    corpus = json.loads(HOLDOUT_CORPUS_PATH.read_text(encoding="utf-8"))
    assert len(corpus["cases"]) == 10
    assert sum(
        case["severity_class"] == "defect" for case in corpus["cases"]
    ) == 7
    assert sum(
        case["severity_class"] == "clean" for case in corpus["cases"]
    ) == 3


def test_dev_benchmark_reaches_full_metrics(
    report_schema: dict,
) -> None:
    report = run_benchmark(DEV_CORPUS_PATH)
    payload = report.to_dict()
    _assert_report_schema_conformant(payload, report_schema)
    assert report.runtime == BENCHMARK_VERSION

    for case in report.cases:
        assert case.passed, (
            f"{case.case_id}: detections={case.observed_detections}/"
            f"{case.expected_detection} severity={case.observed_max_severity}/"
            f"{case.expected_max_severity} falseRelease={case.false_release}"
        )
    metrics = report.metrics()
    assert metrics["truePositives"] >= 30
    assert metrics["falseNegatives"] == 0
    assert metrics["falsePositives"] == 0
    assert metrics["trueNegatives"] >= 10
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["falseReleaseCount"] == 0
    assert metrics["cleanPassRate"] == 1.0
    assert metrics["casePassRate"] == 1.0
    assert metrics["detectionExactRate"] == 1.0


def test_holdout_benchmark_stays_clean(
    report_schema: dict,
) -> None:
    report = run_benchmark(HOLDOUT_CORPUS_PATH)
    payload = report.to_dict()
    _assert_report_schema_conformant(payload, report_schema)
    for case in report.cases:
        assert case.passed, (
            f"{case.case_id}: detections={case.observed_detections}/"
            f"{case.expected_detection} severity={case.observed_max_severity}/"
            f"{case.expected_max_severity} falseRelease={case.false_release}"
        )
    metrics = report.metrics()
    assert metrics["falsePositives"] == 0
    assert metrics["falseNegatives"] == 0
    assert metrics["falseReleaseCount"] == 0
    assert metrics["casePassRate"] == 1.0


def test_wilson_reference_values() -> None:
    assert wilson_ci(30, 30) == pytest.approx((0.886483, 1.0), abs=1e-5)
    assert wilson_ci(0, 10) == pytest.approx((0.0, 0.27754), abs=1e-5)
    assert wilson_ci(2, 4) == pytest.approx((0.150036, 0.849964), abs=1e-5)
    assert wilson_ci(3, 30) == pytest.approx((0.034599, 0.256214), abs=1e-5)
    assert wilson_ci(1, 2) == pytest.approx((0.094529, 0.905471), abs=1e-5)


def test_wilson_degenerate_samples() -> None:
    assert wilson_ci(0, 0) == (0.0, 0.0)
    assert wilson_ci(5, 2) == (0.0, 0.0)


def test_severity_ordering_is_monotonic() -> None:
    assert [SEVERITY_ORDER[level] for level in ("pass", "info", "warning", "error")] == [
        -1,
        0,
        1,
        2,
    ]


def _synthetic_corpus_for_metrics() -> dict:
    return {
        "schemaVersion": "1.0.0",
        "corpus_id": "benchmark-g3-synthetic@0.0.1",
        "corpus_version": 1,
        "workItem": "G3-BEN-001",
        "seed": 1,
        "runtime": "megis.benchmark@0.1.0",
        "timeout_ms": 5000,
        "cases": [
            {
                "case_id": "SYN-DEF-OK",
                "bucket": "golden",
                "severity_class": "defect",
                "title_zh": "真陽性：偵測到薄壁缺陷",
                "reviewer": "test-only",
                "oracle": {
                    "expected_detection": 1,
                    "expected_max_severity": "error",
                    "error_grade": True,
                    "expected_maturity_max": "CONCEPT",
                    "expect_false_release": False,
                },
                "rule_checks": [
                    {
                        "rule_id": "CNC_MIN_WALL_001",
                        "inputs": {"wall_thickness_mm": 0.5},
                    }
                ],
            },
            {
                "case_id": "SYN-DEF-MISS",
                "bucket": "golden",
                "severity_class": "defect",
                "title_zh": "假陰性：漏報分離元件",
                "reviewer": "test-only",
                "oracle": {
                    "expected_detection": 1,
                    "expected_max_severity": "error",
                    "error_grade": True,
                    "expected_maturity_max": "CONCEPT",
                    "expect_false_release": False,
                },
                "validation_input": {
                    "design_id": "synthetic-separated-miss",
                    "components": [
                        {
                            "component_id": "a",
                            "box": {"min": [0, 0, 0], "max": [10, 10, 10]},
                        },
                        {
                            "component_id": "b",
                            "box": {"min": [20, 20, 20], "max": [30, 30, 30]},
                        },
                    ],
                },
            },
            {
                "case_id": "SYN-CL-FP",
                "bucket": "golden",
                "severity_class": "clean",
                "title_zh": "假陽性：乾淨視為碰撞",
                "reviewer": "test-only",
                "oracle": {
                    "expected_detection": 0,
                    "expected_max_severity": "pass",
                    "error_grade": False,
                    "expected_maturity_max": "PROTOTYPE",
                    "expect_false_release": False,
                },
                "validation_input": {
                    "design_id": "synthetic-colliding-fp",
                    "components": [
                        {
                            "component_id": "a",
                            "box": {"min": [0, 0, 0], "max": [10, 10, 10]},
                        },
                        {
                            "component_id": "b",
                            "box": {"min": [5, 5, 5], "max": [15, 15, 15]},
                        },
                    ],
                },
            },
            {
                "case_id": "SYN-CL-OK",
                "bucket": "golden",
                "severity_class": "clean",
                "title_zh": "真陰性：分離元件",
                "reviewer": "test-only",
                "oracle": {
                    "expected_detection": 0,
                    "expected_max_severity": "pass",
                    "error_grade": False,
                    "expected_maturity_max": "PROTOTYPE",
                    "expect_false_release": False,
                },
                "validation_input": {
                    "design_id": "synthetic-separated-ok",
                    "components": [
                        {
                            "component_id": "a",
                            "box": {"min": [0, 0, 0], "max": [10, 10, 10]},
                        },
                        {
                            "component_id": "b",
                            "box": {"min": [20, 20, 20], "max": [30, 30, 30]},
                        },
                    ],
                },
            },
        ],
    }


def test_synthetic_corpus_kpi(tmp_path: Path) -> None:
    corpus = _synthetic_corpus_for_metrics()
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
    report = run_benchmark(path)

    metrics = report.metrics()
    assert metrics["defectCases"] == 2
    assert metrics["cleanCases"] == 2
    assert metrics["truePositives"] == 1
    assert metrics["falseNegatives"] == 1
    assert metrics["falsePositives"] == 1
    assert metrics["trueNegatives"] == 1
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    # The missed error-grade defect is no longer blocked by the evaluator, so
    # the benchmark correctly flags one false release while real configs stay at 0.
    assert metrics["falseReleaseCount"] == 1

    by_id = {result.case_id: result for result in report.cases}
    assert by_id["SYN-DEF-OK"].observed_detections == 1
    assert by_id["SYN-DEF-MISS"].observed_detections == 0
    assert by_id["SYN-CL-FP"].observed_detections == 1
    assert by_id["SYN-CL-OK"].observed_detections == 0
    assert by_id["SYN-CL-FP"].false_release is False
    assert by_id["SYN-DEF-MISS"].false_release is True


def test_unknown_rule_is_rejected(tmp_path: Path) -> None:
    corpus = _synthetic_corpus_for_metrics()
    corpus["cases"][0]["rule_checks"][0]["rule_id"] = "NO_SUCH_RULE_999"
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="NO_SUCH_RULE_999"):
        run_benchmark(path)


def test_invalid_corpus_is_rejected(tmp_path: Path) -> None:
    corpus = _synthetic_corpus_for_metrics()
    corpus["cases"].clear()
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="schema conformant"):
        run_benchmark(path)
