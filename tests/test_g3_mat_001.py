"""G3-MAT-001 maturity evaluator table-driven tests (E3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from megis.maturity import (
    ENGINEERING_REVIEWED_INDEX,
    MATURITY_STATES,
    MaturityInput,
    MaturityInputError,
    evaluate_design_run,
    level_index,
    recompute_required,
)
from megis.governance.classification import validate_manifest

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "contracts" / "g3" / "golden" / "maturity-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "maturity-corpus.schema.json"
EVALUATION_SCHEMA_PATH = ROOT / "schemas" / "v3" / "maturity-evaluation.schema.json"


@pytest.fixture(scope="module")
def corpus() -> dict:
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def corpus_schema() -> dict:
    return json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def evaluation_schema() -> dict:
    return json.loads(EVALUATION_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_corpus_validates_against_schema(corpus: dict, corpus_schema: dict) -> None:
    Draft202012Validator.check_schema(corpus_schema)
    errors = list(Draft202012Validator(corpus_schema).iter_errors(corpus))
    assert errors == []
    assert len(corpus["cases"]) >= 18


@pytest.mark.parametrize(
    "case",
    [
        json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["cases"][index]
        for index in range(
            len(json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["cases"])
        )
    ],
    ids=lambda case: case["case_id"],
)
def test_every_corpus_case_matches_golden(
    case: dict,
    evaluation_schema: dict,
) -> None:
    evaluation = evaluate_design_run(MaturityInput.from_dict(case["input"]))
    payload = evaluation.to_dict()
    assert payload["state"] == case["expect"]["state"]
    assert payload["achievedIndex"] == case["expect"]["achievedIndex"]
    for fragment in case["expect"].get("blockingContain", []):
        assert any(fragment in reason for reason in payload["blocking_reasons"])
    for fragment in case["expect"].get("recomputedContain", []):
        assert any(fragment in reason for reason in payload["recomputed_reasons"])
    schema_errors = list(Draft202012Validator(evaluation_schema).iter_errors(payload))
    assert schema_errors == []


def test_every_state_has_positive_and_negative_cases(corpus: dict) -> None:
    positives = {case["case_id"] for case in corpus["cases"] if "-positive" in case["case_id"]}
    negatives = {case["case_id"] for case in corpus["cases"] if "-negative" in case["case_id"]}
    assert positives
    assert negatives
    for state in (
        "draft",
        "concept",
        "prototype",
        "engineered",
        "released",
    ):
        assert any(state in positive for positive in positives), state
        assert any(state in negative for negative in negatives), state


def test_level_ordering_is_monotonic() -> None:
    values = [level_index(state) for state in MATURITY_STATES]
    assert values == [0, 1, 2, 3, 4]
    assert level_index(None) == -1


def test_digest_is_deterministic_and_sensitive() -> None:
    base = MaturityInput.from_dict(
        {
            "requirements_schema_valid": True,
            "ir_schema_valid": True,
            "ir_referential_integrity_ok": True,
            "layout_collision_no_error": True,
            "geometry_kernel_valid": True,
            "rule_packs_executed": True,
            "design_params": {"wall_thickness_mm": 1.2},
        }
    )
    assert base.digest() == base.digest()
    changed = MaturityInput.from_dict({**base.to_dict(), "design_params": {"wall_thickness_mm": 1.3}})
    assert changed.digest() != base.digest()


def test_recompute_required_flags() -> None:
    stable = MaturityInput.from_dict({"requirements_schema_valid": True})
    assert recompute_required(stable) == (False, [])
    changed = MaturityInput.from_dict(
        {"requirements_schema_valid": True, "input_changed": True}
    )
    forced, reasons = recompute_required(changed)
    assert forced and any("輸入已變更" in reason for reason in reasons)
    expired = MaturityInput.from_dict(
        {"requirements_schema_valid": True, "waiver_expired": True}
    )
    forced, reasons = recompute_required(expired)
    assert forced and any("waiver 已到期" in reason for reason in reasons)


def test_evaluator_is_sole_writer_of_maturity() -> None:
    evaluation_manifest = _provenance_manifest()
    assert validate_manifest(evaluation_manifest, ROOT / "manifest.json") == []
    unprovenanced = {
        "classification": "DESIGN_RUN",
        "maturity": "PROTOTYPE",
    }
    issues = validate_manifest(unprovenanced, ROOT / "manifest.json")
    assert any(issue.code == "EVALUATOR_PROVENANCE_MISSING" for issue in issues)


def _provenance_manifest() -> dict:
    evaluation = evaluate_design_run(
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
    return {
        "classification": "DESIGN_RUN",
        "maturity": "PROTOTYPE",
        "maturity_evaluation": evaluation.to_dict(),
    }


def test_invalid_maturity_cap_rejected() -> None:
   design = MaturityInput.from_dict(
       {"requirements_schema_valid": True, "maturity_cap": "RELEASED"}
   )
   with pytest.raises(MaturityInputError):
       evaluate_design_run(design)


def test_prototype_requires_all_gates_even_with_signoff() -> None:
    base = {
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
        "engineering_review_signoff": True,
        "named_engineer_available": True,
        "unresolved_errors": ["MEGIS-VAL-001 collision unresolved"],
    }
    evaluation = evaluate_design_run(MaturityInput.from_dict(base))
    assert evaluation.state == "CONCEPT"
    assert any("未處置的 error" in reason for reason in evaluation.blocking_reasons)


def test_waiver_expiry_invalidates_engineered_reviewed_signoff() -> None:
    base = {
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
        "engineering_review_signoff": True,
        "named_engineer_available": True,
    }
    fresh = evaluate_design_run(MaturityInput.from_dict(base))
    assert fresh.state == "ENGINEERING_REVIEWED"
    assert fresh.achieved_index == ENGINEERING_REVIEWED_INDEX

    expired = MaturityInput.from_dict({**base, "waiver_expired": True})
    recomputed = evaluate_design_run(expired)
    assert recomputed.state == "PROTOTYPE"
    assert any("waiver 已到期" in reason for reason in recomputed.recomputed_reasons)
    assert any("sign-off 已失效" in reason for reason in recomputed.recomputed_reasons)


def test_input_change_digest_provenance_blocks_mismatch() -> None:
   original = MaturityInput.from_dict(
       {
           "requirements_schema_valid": True,
           "design_params": {"wall_thickness_mm": 2.0},
       }
   )
   mutated = MaturityInput.from_dict(
       {
           **original.to_dict(),
           "design_params": {"wall_thickness_mm": 2.5},
       }
   )
   assert mutated.digest() != original.digest()
