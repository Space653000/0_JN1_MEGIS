"""G6-UI-002 corrective tests for truthful guided-flow maturity."""

from __future__ import annotations

from megis.guides.flow import GuidedAnswers, build_ir_draft, evaluate_guided_maturity


def test_guided_draft_maturity_is_computed_by_the_evaluator() -> None:
    answers = GuidedAnswers()
    evaluation = evaluate_guided_maturity(answers)
    document = build_ir_draft(answers)

    assert evaluation.state == "DRAFT"
    assert document["maturity"] == evaluation.state
    assert evaluation.evaluator_version == "megis.maturity@1.0.0"
    assert any("unsafe_to_default" in reason for reason in evaluation.blocking_reasons)


def test_guided_draft_never_claims_prototype_before_execution_evidence() -> None:
    evaluation = evaluate_guided_maturity(GuidedAnswers(pcb_envelope_mode="provided"))

    assert evaluation.state == "DRAFT"
    assert evaluation.achieved_index == 0
    assert "PROTOTYPE" not in {evaluation.state}
    assert any("layout" in reason for reason in evaluation.blocking_reasons)


def test_maturity_digest_changes_when_guided_inputs_change() -> None:
    first = evaluate_guided_maturity(GuidedAnswers(width_mm=120.0))
    second = evaluate_guided_maturity(GuidedAnswers(width_mm=110.0))

    assert first.inputs_digest != second.inputs_digest
