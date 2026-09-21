"""G3-RUL-001 rule lifecycle, governance and waiver tests (E3 evidence)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from megis.errors import MegisError
from megis.rules.lifecycle import (
    NO_REVIEWER,
    RuleStatus,
    approve_rule,
    deprecate_rule,
    rule_status,
    send_back_to_draft,
    transition_rule,
    validate_rule,
    verify_rule_registry,
)
from megis.rules.waiver import (
    WaiverStatus,
    check_waiver_applicable,
    issue_for_waiver,
    triggered_expiry_conditions,
    validate_waiver,
    waiver_status,
)

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "contracts" / "g3" / "golden" / "rule-governance.json"


@pytest.fixture(scope="module")
def corpus() -> dict:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def rules(corpus: dict) -> dict[str, dict]:
    return {item["rule_id"]: item for item in corpus["rules"]}


@pytest.fixture(scope="module")
def waivers(corpus: dict) -> dict[str, dict]:
    return {item["waiver_id"]: item for item in corpus["waivers"]}


def test_golden_corpus_rules_and_waivers_conform_to_schemas(corpus: dict) -> None:
    for rule in corpus["rules"]:
        validate_rule(rule)
    for waiver in corpus["waivers"]:
        validate_waiver(waiver)


def test_lifecycle_full_chain_draft_to_deprecated(rules: dict[str, dict]) -> None:
    rule = dict(rules["CNC_MIN_WALL_001"])
    assert rule_status(rule) is RuleStatus.DRAFT

    in_review = transition_rule(rule, RuleStatus.IN_REVIEW)
    assert in_review["status"] == "in_review"

    returned = send_back_to_draft(in_review)
    assert returned["status"] == "draft"

    re_review = transition_rule(returned, RuleStatus.IN_REVIEW)
    approved = approve_rule(
        re_review,
        source_status="approved",
        reviewer="REV-2026-CNC-MIN-WALL",
    )
    assert approved["status"] == "approved"
    assert approved["reviewed_by"] == "REV-2026-CNC-MIN-WALL"

    deprecated = deprecate_rule(approved, reason="replaced by CNC_MIN_WALL_002")
    assert deprecated["status"] == "deprecated"


def test_skip_review_direct_to_approved_raises_rul_002(rules: dict[str, dict]) -> None:
    with pytest.raises(MegisError) as excinfo:
        transition_rule(dict(rules["CNC_MIN_WALL_001"]), RuleStatus.APPROVED)
    assert excinfo.value.code.code == "MEGIS-RUL-002"


def test_approval_requires_approved_source(rules: dict[str, dict]) -> None:
    in_review = dict(rules["CNC_TAP_BLIND_001"])
    with pytest.raises(MegisError) as excinfo:
        approve_rule(in_review, source_status="draft", reviewer="someone")
    assert excinfo.value.code.code == "MEGIS-RUL-001"


def test_approval_requires_non_empty_reviewer(rules: dict[str, dict]) -> None:
    in_review = dict(rules["CNC_TAP_BLIND_001"])
    with pytest.raises(MegisError) as excinfo:
        approve_rule(in_review, source_status="approved", reviewer="  ")
    assert excinfo.value.code.code == "MEGIS-RUL-002"


def test_deprecation_requires_approved(rules: dict[str, dict]) -> None:
    with pytest.raises(MegisError) as excinfo:
        deprecate_rule(dict(rules["CNC_MIN_WALL_001"]))
    assert excinfo.value.code.code == "MEGIS-RUL-002"


def test_approved_without_reviewer_is_reported(rules: dict[str, dict]) -> None:
    broken = dict(rules["CON_USBC_OPEN_001"])
    broken["reviewed_by"] = NO_REVIEWER
    issues = verify_rule_registry([broken])
    assert any("approved without a reviewer" in issue for issue in issues)


def test_rule_schema_rejects_unknown_severity(rules: dict[str, dict]) -> None:
    broken = dict(rules["CNC_MIN_WALL_001"])
    broken["severity"] = "blocking"
    with pytest.raises(ValueError):
        validate_rule(broken)


def test_rule_schema_rejects_missing_source(rules: dict[str, dict]) -> None:
    broken = dict(rules["CNC_MIN_WALL_001"])
    del broken["source"]
    with pytest.raises(ValueError):
        validate_rule(broken)


def test_active_waiver_expires_on_input_and_rule_version_change(
    rules: dict[str, dict],
    waivers: dict[str, dict],
) -> None:
    tol = rules["TOL_GENERAL_001"]
    waiver = waivers["WV-0001"]
    assert waiver_status(waiver, tol) is WaiverStatus.ACTIVE
    assert waiver_status(waiver, tol, input_changed=True) is WaiverStatus.EXPIRED
    assert waiver_status(waiver, tol, rule_version_changed=True) is WaiverStatus.EXPIRED
    assert triggered_expiry_conditions(waiver, input_changed=True) == ("input_changed",)


def test_waiver_date_expiry_boundary(
    rules: dict[str, dict],
    waivers: dict[str, dict],
) -> None:
    tol = rules["TOL_GENERAL_001"]
    waiver = waivers["WV-0002"]
    assert waiver_status(waiver, tol, at=date(2026, 8, 31)) is WaiverStatus.ACTIVE
    assert waiver_status(waiver, tol, at=date(2026, 9, 1)) is WaiverStatus.EXPIRED
    assert triggered_expiry_conditions(waiver, at=date(2026, 9, 1)) == (
        "date:2026-09-01",
    )


def test_safety_rule_waiver_is_invalid(
    rules: dict[str, dict],
    waivers: dict[str, dict],
) -> None:
    asm = rules["ASM_COLLISION_001"]
    waiver = waivers["WV-0003"]
    assert waiver_status(waiver, asm) is WaiverStatus.INVALID
    with pytest.raises(MegisError) as excinfo:
        check_waiver_applicable(waiver, asm)
    assert excinfo.value.code.code == "MEGIS-RUL-003"
    assert "non-waivable" in excinfo.value.error_object.engineer_detail


def test_waiver_for_draft_rule_is_invalid(
    rules: dict[str, dict],
    waivers: dict[str, dict],
) -> None:
    draft_rule = rules["CNC_MIN_WALL_001"]
    waiver = waivers["WV-0001"]
    waiver = dict(waivers["WV-0001"])
    waiver["rule_id"] = draft_rule["rule_id"]
    waiver["rule_version"] = draft_rule["version"]
    with pytest.raises(MegisError) as excinfo:
        check_waiver_applicable(waiver, draft_rule)
    assert excinfo.value.code.code == "MEGIS-RUL-003"
    assert "only approved rules" in excinfo.value.error_object.engineer_detail


def test_waiver_rule_id_mismatch_is_invalid(
    rules: dict[str, dict],
    waivers: dict[str, dict],
) -> None:
    waiver = dict(waivers["WV-0001"])
    other_rule = rules["CON_USBC_OPEN_001"]
    assert issue_for_waiver(waiver, other_rule) is not None
    assert waiver_status(waiver, other_rule) is WaiverStatus.INVALID
