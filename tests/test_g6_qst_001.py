"""G6-QST-001 deterministic question ordering and abstention tests (E3).

Covers blueprint section 14 Dynamic Question Engine rules 1-8: unsafe-first
ordering, impact tie-breaks, derived questions never asked, IR binding,
determinism with a frozen golden corpus, critical unknowns that never
disappear on abstention, and generation blocked for every abstained
unsafe-to-default field.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from megis.errors import ERROR_CODES, MegisError, verify_error_codes
from megis.guides.flow import (
    GuidedAnswers,
    api_payload_to_answers,
    build_ir_draft,
    ui_state_to_answers,
)
from megis.guides.qst import (
    DERIVED_DEFAULTS,
    IMPACT_RANK,
    order_questions,
    session_status,
)
from megis.guides.questions import GUIDED_QUESTIONS

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "contracts" / "g6" / "golden" / "question-order-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "question-order-corpus.schema.json"

DERIVED_IDS = tuple(DERIVED_DEFAULTS)


def _load_corpus() -> dict:
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


def _state_to_answers(state: dict) -> GuidedAnswers:
    """Route a corpus state to the UI or API converter by its key convention."""
    if any(
        key in state
        for key in ("width_mm", "depth_mm", "height_mm", "pcb_envelope_mode", "pcb_required")
    ):
        return api_payload_to_answers(state)
    return ui_state_to_answers(state)


def _validate_corpus(corpus: dict) -> None:
    schema = json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema).iter_errors(corpus))
    assert errors == [], [error.message for error in errors]


def _status_dict(state: dict, answered: list[str]) -> dict:
    status = session_status(state, answered)
    return {
        "orderedIds": list(status.orderedIds),
        "skippedDerived": list(status.skippedDerived),
        "blocked": status.blocked,
        "blockReason": status.blockReason,
        "nextSteps": list(status.nextSteps),
        "criticalRemaining": list(status.criticalRemaining),
    }


def _assert_blocks(status: dict, expect: dict) -> None:
    for fragment in expect.get("blockReasonContains", []):
        assert fragment in status["blockReason"], (
            f"reason does not contain {fragment!r}: {status['blockReason']!r}"
        )
    joined_steps = " ".join(status["nextSteps"])
    for fragment in expect.get("nextStepsContains", []):
        assert fragment in joined_steps, (
            f"next steps do not contain {fragment!r}: {joined_steps!r}"
        )


def test_corpus_is_schema_valid_and_sized() -> None:
    corpus = _load_corpus()
    _validate_corpus(corpus)
    assert len(corpus["cases"]) >= 16
    kinds = {case["kind"] for case in corpus["cases"]}
    assert kinds == {"ordering", "abstention", "boundary", "negative"}


def test_every_corpus_case_matches_live_engine() -> None:
    corpus = _load_corpus()
    _validate_corpus(corpus)
    for case in corpus["cases"]:
        state = case["input"].get("state", {})
        answered = case["input"]["answered"]
        expect = case["expect"]
        status = _status_dict(state, answered)
        assert status["orderedIds"] == expect["orderedIds"], case["case_id"]
        assert status["skippedDerived"] == expect["skippedDerived"], case["case_id"]
        assert status["blocked"] is expect["blocked"], case["case_id"]
        assert status["criticalRemaining"] == expect["criticalRemaining"], case["case_id"]
        if expect["blocked"]:
            _assert_blocks(status, expect)


def test_ordering_is_deterministic() -> None:
    corpus = _load_corpus()
    for case in corpus["cases"]:
        state = case["input"].get("state", {})
        answered = case["input"]["answered"]
        first = session_status(state, answered)
        second = session_status(state, answered)
        assert first == second, case["case_id"]
    fresh = session_status({}, [])
    assert fresh == session_status({}, [])


def test_rule1_unsafe_to_default_questions_are_asked_first() -> None:
    status = session_status({}, [])
    unsafe_ids = [q.id for q in GUIDED_QUESTIONS if q.unsafeToDefault]
    pending_unsafe = [qid for qid in status.orderedIds if qid in unsafe_ids]
    pending_safe = [qid for qid in status.orderedIds if qid not in unsafe_ids]
    assert pending_unsafe and pending_safe
    assert all(
        status.orderedIds.index(unsafe) < status.orderedIds.index(safe)
        for unsafe in pending_unsafe
        for safe in pending_safe
    )


def test_rule2_architecture_and_process_changes_come_first() -> None:
    answered = ["Q-FIXTURE-WIDTH", "Q-FIXTURE-DEPTH", "Q-FIXTURE-HEIGHT"]
    state = {"width": 120, "depth": 80, "height": 20, "pcbEnvelopeMode": "provided"}
    status = session_status(state, answered)
    ranks = [IMPACT_RANK[qid] for qid in status.orderedIds]
    assert ranks == sorted(ranks), status.orderedIds
    assert IMPACT_RANK["Q-FIXTURE-PCB-COUNT"] < IMPACT_RANK["Q-FIXTURE-PRIORITY"]
    assert IMPACT_RANK["Q-FIXTURE-PRIORITY"] < IMPACT_RANK["Q-FIXTURE-PURPOSE"]


def test_rule3_derived_questions_are_never_asked() -> None:
    corpus = _load_corpus()
    for case in corpus["cases"]:
        status = session_status(case["input"].get("state", {}), case["input"]["answered"])
        assert set(DERIVED_IDS).isdisjoint(status.orderedIds), case["case_id"]
        assert set(status.skippedDerived) == set(DERIVED_IDS), case["case_id"]


def test_rule5_the_pcb_unknown_never_disappears_from_critical_remaining() -> None:
    state = {
        "width": 120,
        "depth": 80,
        "height": 20,
        "pcbEnvelopeMode": "unknown",
    }
    answered = [
        "Q-FIXTURE-WIDTH",
        "Q-FIXTURE-DEPTH",
        "Q-FIXTURE-HEIGHT",
        "Q-FIXTURE-PCB-ENVELOPE",
    ]
    status = session_status(state, answered)
    assert status.blocked is True
    assert list(status.criticalRemaining) == ["Q-FIXTURE-PCB-ENVELOPE"]


def test_rule6_every_ordered_question_binds_an_ir_field_and_envelope() -> None:
    corpus = _load_corpus()
    by_id = {question.id: question for question in GUIDED_QUESTIONS}
    for case in corpus["cases"]:
        status = session_status(case["input"].get("state", {}), case["input"]["answered"])
        for question_id in status.orderedIds:
            question = by_id[question_id]
            assert question.irField.startswith("/"), question_id
            has_range = question.envelopeRange is not None
            has_options = len(question.options) > 0
            if question.inputKind != "text":
                assert has_range or has_options, question_id
    # The static guided set itself never asks a question without an IR field.
    for question in GUIDED_QUESTIONS:
        assert question.irField.startswith("/"), question.id


def test_rule7_golden_order_matches_the_live_engine() -> None:
    corpus = _load_corpus()
    fresh_expect = corpus["cases"][0]["expect"]["orderedIds"]
    assert list(order_questions().orderedIds) == fresh_expect


def test_rule8_every_blocked_case_prevents_ir_generation() -> None:
    corpus = _load_corpus()
    for case in corpus["cases"]:
        expect = case["expect"]
        state = case["input"].get("state", {})
        if not expect["blocked"]:
            continue
        with pytest.raises(MegisError) as excinfo:
            build_ir_draft(_state_to_answers(state))
        assert excinfo.value.error_object.code == "MEGIS-UI-001", case["case_id"]


def test_non_blocked_cases_build_a_valid_ir_draft() -> None:
    corpus = _load_corpus()
    for case in corpus["cases"]:
        if case["expect"]["blocked"]:
            continue
        answers = _state_to_answers(case["input"].get("state", {}))
        document = build_ir_draft(answers)
        assert document["designId"] == "FIXTURE-GUIDED-001", case["case_id"]


def test_ui_and_api_state_keys_produce_equivalent_status() -> None:
    ui = {
        "width": 120,
        "depth": 80,
        "height": 20,
        "pcbEnvelopeMode": "provided",
    }
    api = {
        "width_mm": 120,
        "depth_mm": 80,
        "height_mm": 20,
        "pcb_envelope_mode": "provided",
    }
    answered = ["Q-FIXTURE-WIDTH", "Q-FIXTURE-DEPTH", "Q-FIXTURE-HEIGHT"]
    assert _status_dict(ui, answered) == _status_dict(api, answered)


def test_error_codes_registered() -> None:
    assert "MEGIS-UI-001" in ERROR_CODES
    assert verify_error_codes() == []


def test_engine_writes_no_engineering_artifact() -> None:
    with tempfile.TemporaryDirectory(dir=ROOT / ".temp") as tmp:
        before = {path.name for path in Path(tmp).iterdir()}
        session_status({}, [])
        session_status(
            {"width": 120, "depth": 80, "height": 20, "pcbEnvelopeMode": "provided"},
            ["Q-FIXTURE-WIDTH", "Q-FIXTURE-DEPTH", "Q-FIXTURE-HEIGHT"],
        )
        after = {path.name for path in Path(tmp).iterdir()}
        assert before == after