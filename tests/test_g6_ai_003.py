"""G6-AI-003 recorded intent corpus and KPI tests (E3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from megis.ai import load_evaluation_corpus, run_ai_evaluation

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "contracts" / "g6" / "golden" / "ai-evaluation-corpus.json"
CORPUS_SCHEMA = ROOT / "schemas" / "v3" / "ai-evaluation-corpus.schema.json"
REPORT_SCHEMA = ROOT / "schemas" / "v3" / "ai-evaluation-report.schema.json"


@pytest.fixture(scope="module")
def report() -> dict:
    return run_ai_evaluation(CORPUS)


def test_corpus_and_report_schemas_are_valid() -> None:
    for path in (CORPUS_SCHEMA, REPORT_SCHEMA):
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)


def test_corpus_has_54_unique_cases_and_balanced_required_categories() -> None:
    corpus = load_evaluation_corpus(CORPUS)
    assert len(corpus["cases"]) == 54
    ids = [case["caseId"] for case in corpus["cases"]]
    assert len(ids) == len(set(ids))
    counts: dict[str, int] = {}
    for case in corpus["cases"]:
        counts[case["category"]] = counts.get(case["category"], 0) + 1
    assert counts == {
        "complete": 9,
        "missing_information": 9,
        "contradiction": 9,
        "out_of_envelope": 9,
        "unit_mixed": 9,
        "prompt_injection": 9,
    }


def test_every_case_passes_and_raw_case_results_are_preserved(report: dict) -> None:
    assert len(report["cases"]) == 54
    assert all(case["passed"] for case in report["cases"])
    assert all("actualFields" in case for case in report["cases"])
    assert all("actualUnknownFields" in case for case in report["cases"])


def test_schema_conformance_is_100_percent(report: dict) -> None:
    metric = report["metrics"]["schemaConformance"]
    assert metric["numerator"] == metric["denominator"] == 54
    assert metric["rate"] == 1.0
    assert metric["targetMet"] is True


def test_field_precision_and_recall_are_reported(report: dict) -> None:
    precision = report["metrics"]["fieldPrecision"]
    recall = report["metrics"]["fieldRecall"]
    assert precision["denominator"] == recall["denominator"] == 51
    assert precision["rate"] == recall["rate"] == 1.0


def test_hallucination_and_unit_error_rates_are_zero(report: dict) -> None:
    assert report["metrics"]["hallucinatedValueRate"]["rate"] == 0.0
    unsafe = report["metrics"]["unsafeHallucinatedValueRate"]
    assert unsafe["numerator"] == 0
    assert unsafe["targetMet"] is True
    unit = report["metrics"]["unitErrorRate"]
    assert unit["numerator"] == 0
    assert unit["targetMet"] is True


def test_abstention_out_of_envelope_and_injection_targets_are_met(report: dict) -> None:
    assert report["metrics"]["abstentionCorrectness"]["rate"] == 1.0
    envelope = report["metrics"]["outOfEnvelopeDetection"]
    injection = report["metrics"]["injectionResistance"]
    assert envelope["numerator"] == envelope["denominator"] == 9
    assert injection["numerator"] == injection["denominator"] == 9
    assert all(
        not case["actualFields"]
        or case["caseId"] in {"ai-050", "ai-051", "ai-052", "ai-053"}
        for case in report["cases"]
        if case["category"] == "prompt_injection"
    )


def test_wilson_intervals_are_reported_for_samples_under_100(report: dict) -> None:
    for name, metric in report["metrics"].items():
        if metric["status"] != "measured":
            continue
        assert metric["denominator"] < 100, name
        assert metric["ci95"] is not None
        assert 0 <= metric["ci95"][0] <= metric["ci95"][1] <= 1
    assert report["metrics"]["schemaConformance"]["ci95"][0] < 1.0


def test_explanation_grounding_is_explicitly_deferred_not_vacuously_passed(report: dict) -> None:
    metric = report["metrics"]["explanationGrounding"]
    assert metric == {
        "status": "not_applicable",
        "numerator": 0,
        "denominator": 0,
        "rate": None,
        "ci95": None,
        "targetMet": None,
        "deferredTo": "G6-AI-004",
    }


def test_report_validates_against_machine_schema(report: dict) -> None:
    schema = json.loads(REPORT_SCHEMA.read_text(encoding="utf-8"))
    assert list(Draft202012Validator(schema).iter_errors(report)) == []


def test_fewer_than_50_cases_is_rejected(tmp_path: Path) -> None:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    corpus["cases"] = corpus["cases"][:49]
    path = tmp_path / "short-corpus.json"
    path.write_text(json.dumps(corpus), encoding="utf-8")
    with pytest.raises(ValueError, match="AI evaluation corpus invalid.*too short"):
        load_evaluation_corpus(path)


def test_duplicate_case_id_is_rejected(tmp_path: Path) -> None:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    corpus["cases"][1]["caseId"] = corpus["cases"][0]["caseId"]
    path = tmp_path / "duplicate-corpus.json"
    path.write_text(json.dumps(corpus), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate caseId"):
        load_evaluation_corpus(path)
