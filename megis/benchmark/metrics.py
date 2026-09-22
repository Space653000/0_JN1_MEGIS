"""Deterministic benchmark runner and KPI math (G3-BEN-001).

Detection semantics
--------------------
One detection is one failed check produced by the pipeline for a case:

- every failed validation check (a ``ValidationIssue`` whose status is
  ``fail`` or ``error``) counts once, carrying its own severity; and
- every failed rule evaluation (a ``RuleEvaluation`` whose status is
  ``fail``) counts once, carrying the rule's severity.

A case's observed max severity is the highest severity among its detections
(``error`` > ``warning`` > ``info``), or ``pass`` when nothing was detected.
This check-level definition is what the corpus ``expected_detection`` field
records, so compound cases (several checks at once) count every failed check.

False release
-------------
For every case the runner composes a ``MaturityInput`` from the corpus
``maturity_input``, falling back to a healthy template.  When a defect is
error-grade, the detected error sources are injected into
``unresolved_errors``; the evaluator then proves the pipeline refuses to
reach ``PROTOTYPE`` while errors remain.  A false release happens when the
observed maturity level exceeds the corpus ``expected_maturity_max``.

Consumers: ``scripts/verify_g3_ben_001.py`` and ``tests/test_g3_ben_001.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from megis.maturity import (
    MaturityInput,
    evaluate_design_run,
    level_index,
)
from megis.rules import evaluate_rule, load_rule_pack
from megis.validation import DesignValidationInput, ValidationIssue
from megis.validation import validate_design

BENCHMARK_VERSION = "megis.benchmark@0.1.0"
Z95 = 1.96
WILSON_Z = Z95

ROOT = Path(__file__).resolve().parents[2]
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "benchmark-corpus.schema.json"
RULEPACK_PATH = ROOT / "contracts" / "g3" / "golden" / "cnc-dfm-rulepack.json"

SEVERITY_ORDER = {"pass": -1, "info": 0, "warning": 1, "error": 2}

PASS_DEFINITION = (
    "case passes when observed detection count and max severity match the "
    "oracle, the error grade is consistent, and the observed maturity does "
    "not exceed the oracle maximum unless a false release is expected"
)

# Healthy run-level state used when a corpus case does not ship its own
# ``maturity_input``.  Detected error sources are layered on top so the
# evaluator can demonstrate false-release suppression.
DEFAULT_HEALTHY_MATURITY: dict[str, Any] = {
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


@dataclass(frozen=True)
class Detection:
    """One observed check failure with its source and severity."""

    source: str
    severity: str
    code: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "severity": self.severity,
            "code": self.code,
        }


def wilson_ci(
    successes: int,
    total: int,
    z: float = WILSON_Z,
) -> tuple[float, float]:
    """Return the Wilson score 95% confidence interval for a proportion.

    Degenerate samples (``total == 0``) return ``(0.0, 0.0)``; endpoints are
    clamped to ``[0, 1]``.
    """

    if total <= 0 or successes < 0 or successes > total:
        return (0.0, 0.0)
    proportion = successes / total
    denominator = 1.0 + z * z / total
    centre = (proportion + z * z / (2.0 * total)) / denominator
    half = (
        z
        * (proportion * (1.0 - proportion) / total + z * z / (4.0 * total * total))
        ** 0.5
        / denominator
    )
    return (max(0.0, centre - half), min(1.0, centre + half))


@dataclass(frozen=True)
class CaseResult:
    """One corpus case run through the real validators, rules and evaluator."""

    case_id: str
    bucket: str
    severity_class: str
    expected_detection: int
    expected_max_severity: str
    expected_maturity_max: str
    expect_false_release: bool
    detections: tuple[Detection, ...] = field(default_factory=tuple)
    maturity_state: str | None = None
    maturity_achieved_index: int = -1

    @property
    def observed_detections(self) -> int:
        return len(self.detections)

    @property
    def observed_max_severity(self) -> str:
        if not self.detections:
            return "pass"
        return max(
            (detection.severity for detection in self.detections),
            key=lambda severity: SEVERITY_ORDER[severity],
        )

    @property
    def false_release(self) -> bool:
        return self.maturity_achieved_index > level_index(self.expected_maturity_max)

    @property
    def error_grade(self) -> bool:
        return self.observed_max_severity == "error"

    @property
    def passed(self) -> bool:
        oracle = (
            self.observed_detections == self.expected_detection
            and self.observed_max_severity == self.expected_max_severity
            and self.error_grade == (self.expected_max_severity == "error")
        )
        if self.expect_false_release:
            maturity_ok = self.false_release
        else:
            maturity_ok = not self.false_release
        return oracle and maturity_ok

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "bucket": self.bucket,
            "severityClass": self.severity_class,
            "observedDetections": self.observed_detections,
            "expectedDetection": self.expected_detection,
            "observedMaxSeverity": self.observed_max_severity,
            "expectedMaxSeverity": self.expected_max_severity,
            "maturityState": self.maturity_state,
            "maturityAchievedIndex": self.maturity_achieved_index,
            "expectedMaturityMax": self.expected_maturity_max,
            "expectFalseRelease": self.expect_false_release,
            "falseRelease": self.false_release,
            "errorGrade": self.error_grade,
            "passed": self.passed,
            "detections": [detection.to_dict() for detection in self.detections],
        }


def _validation_detections(
    case: dict[str, Any],
    *,
    validation_id: str,
    created_at: str,
) -> list[Detection]:
    raw = case["validation_input"]
    result = validate_design(
        DesignValidationInput.from_dict(raw),
        validation_id=validation_id,
        design_ref=raw["design_id"],
        created_at=created_at,
    )
    failures = (
        issue
        for issue in result.checks
        if issue.status in ("fail", "error")
    )
    return [
        Detection(
            source=_validation_source(issue),
            severity=issue.severity,
            code=issue.code,
        )
        for issue in failures
    ]


def _validation_source(issue: ValidationIssue) -> str:
    """Collapse the source to ``rule_id`` when a clearance bound carries one."""

    if issue.rule_id:
        return issue.rule_id
    return issue.check_id


def _rule_detections(
    rule_checks: list[dict[str, Any]],
    rule_index: dict[str, dict[str, Any]],
) -> list[Detection]:
    detections: list[Detection] = []
    for check in rule_checks:
        rule = rule_index.get(check["rule_id"])
        if rule is None:
            raise ValueError(
                f"benchmark rule_checks references unknown rule {check['rule_id']!r}"
            )
        evaluation = evaluate_rule(rule, check["inputs"])
        if evaluation.status == "fail":
            detections.append(
                Detection(
                    source=rule["rule_id"],
                    severity=rule["severity"],
                    code=None,
                )
            )
    return detections


def _compose_maturity_input(
    case: dict[str, Any],
    detections: list[Detection],
) -> MaturityInput:
    """Compose the maturity input for a case.

    Error-grade defects inject their detected error sources into
    ``unresolved_errors`` so the evaluator demonstrates false-release
    suppression; warning and clean cases keep the supplied run-level state.
    """

    document = dict(case.get("maturity_input") or DEFAULT_HEALTHY_MATURITY)
    errors = sorted(
        {
            detection.source
            for detection in detections
            if detection.severity == "error"
        }
    )
    document["unresolved_errors"] = errors
    return MaturityInput.from_dict(document)


def run_case(
    case: dict[str, Any],
    *,
    rule_index: dict[str, dict[str, Any]],
    created_at: str,
) -> CaseResult:
    """Run one corpus case against the real pipeline components."""

    oracle = case["oracle"]
    detections: list[Detection] = []
    if "validation_input" in case:
        detections.extend(
            _validation_detections(
                case,
                validation_id=f"bench-{case['case_id']}",
                created_at=created_at,
            )
        )
    if case.get("rule_checks"):
        detections.extend(_rule_detections(case["rule_checks"], rule_index))

    maturity = evaluate_design_run(_compose_maturity_input(case, detections))
    return CaseResult(
        case_id=case["case_id"],
        bucket=case["bucket"],
        severity_class=case["severity_class"],
        expected_detection=oracle["expected_detection"],
        expected_max_severity=oracle["expected_max_severity"],
        expected_maturity_max=oracle["expected_maturity_max"],
        expect_false_release=oracle["expect_false_release"],
        detections=tuple(detections),
        maturity_state=maturity.state,
        maturity_achieved_index=maturity.achieved_index,
    )


@dataclass(frozen=True)
class BenchmarkReport:
    """Machine-readable run of one corpus with aggregate KPI metrics."""

    corpus_id: str
    corpus_version: int
    seed: int
    runtime: str
    timeout_ms: int
    cases: tuple[CaseResult, ...]

    @property
    def defect_cases(self) -> tuple[CaseResult, ...]:
        return tuple(
            case for case in self.cases if case.severity_class == "defect"
        )

    @property
    def clean_cases(self) -> tuple[CaseResult, ...]:
        return tuple(
            case for case in self.cases if case.severity_class == "clean"
        )

    @property
    def true_positives(self) -> int:
        return sum(1 for case in self.defect_cases if case.observed_detections >= 1)

    @property
    def false_negatives(self) -> int:
        return sum(1 for case in self.defect_cases if case.observed_detections == 0)

    @property
    def false_positives(self) -> int:
        return sum(1 for case in self.clean_cases if case.observed_detections >= 1)

    @property
    def true_negatives(self) -> int:
        return sum(1 for case in self.clean_cases if case.observed_detections == 0)

    @property
    def _precision_denominator(self) -> int:
        return self.true_positives + self.false_positives

    @property
    def _recall_denominator(self) -> int:
        return self.true_positives + self.false_negatives

    def _ratio(self, numerator: int, denominator: int) -> float:
        if denominator == 0:
            return 1.0
        return round(numerator / denominator, 6)

    def metrics(self) -> dict[str, Any]:
        precision_ci = wilson_ci(self.true_positives, self._precision_denominator)
        recall_ci = wilson_ci(self.true_positives, self._recall_denominator)
        detection_exact = sum(
            1
            for case in self.defect_cases
            if case.observed_detections == case.expected_detection
        )
        return {
            "defectCases": len(self.defect_cases),
            "cleanCases": len(self.clean_cases),
            "truePositives": self.true_positives,
            "falseNegatives": self.false_negatives,
            "falsePositives": self.false_positives,
            "trueNegatives": self.true_negatives,
            "precision": self._ratio(self.true_positives, self._precision_denominator),
            "precisionCI95": [round(value, 6) for value in precision_ci],
            "recall": self._ratio(self.true_positives, self._recall_denominator),
            "recallCI95": [round(value, 6) for value in recall_ci],
            "falseReleaseCount": sum(1 for case in self.cases if case.false_release),
            "cleanPassRate": self._ratio(self.true_negatives, len(self.clean_cases)),
            "casePassRate": self._ratio(
                sum(1 for case in self.cases if case.passed), len(self.cases)
            ),
            "detectionExactRate": self._ratio(detection_exact, len(self.defect_cases)),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": "1.0.0",
            "workItem": "G3-BEN-001",
            "corpus_id": self.corpus_id,
            "corpus_version": self.corpus_version,
            "seed": self.seed,
            "runtime": self.runtime,
            "timeout_ms": self.timeout_ms,
            "passDefinition": PASS_DEFINITION,
            "metrics": self.metrics(),
            "cases": [case.to_dict() for case in self.cases],
        }


def run_benchmark(
    corpus_path: Path,
    *,
    schema_path: Path = CORPUS_SCHEMA_PATH,
    created_at: str = "2026-09-22T13:00:00+08:00",
) -> BenchmarkReport:
    """Validate a benchmark corpus and run every case deterministically.

    The corpus is checked against ``benchmark-corpus.schema.json`` first; a
    corpus that breaches the contract is rejected with ``ValueError``.
    """

    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema).iter_errors(corpus))
    if errors:
        raise ValueError(
            "benchmark corpus is not schema conformant: "
            + "; ".join(error.message for error in errors)
        )

    rule_index = {rule["rule_id"]: rule for rule in load_rule_pack()["rules"]}
    results = tuple(
        run_case(
            case,
            rule_index=rule_index,
            created_at=created_at,
        )
        for case in corpus["cases"]
    )
    return BenchmarkReport(
        corpus_id=corpus["corpus_id"],
        corpus_version=corpus["corpus_version"],
        seed=corpus["seed"],
        runtime=BENCHMARK_VERSION,
        timeout_ms=corpus["timeout_ms"],
        cases=results,
    )
