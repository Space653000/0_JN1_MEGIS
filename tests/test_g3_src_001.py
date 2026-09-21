"""G3-SRC-001 rule source registry and verification workflow tests (E3)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from megis.errors import MegisError
from megis.rules.sources import (
    RuleSource,
    approve_rule_via_registry,
    ensure_rule_evaluable,
    ensure_source_approved,
    load_sources,
    registry_issues,
    validate_source,
)

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "contracts" / "g3" / "golden" / "rule-governance.json"
REFERENCE = date(2026, 9, 21)


def source(
    source_id: str = "SRC-CNC-DFM-001",
    status: str = "approved",
    review_due: str = "2026-12-31",
    url: str | None = "https://example.net/ref",
    accessed_at: str | None = "2026-09-20",
) -> RuleSource:
    return RuleSource(
        source_id=source_id,
        type="datasheet",
        status=status,
        revision="2026-A",
        owner="mechanical_engineering",
        review_due=date.fromisoformat(review_due),
        url=url,
        accessed_at=date.fromisoformat(accessed_at) if accessed_at else None,
    )


@pytest.fixture(scope="module")
def corpus() -> dict:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def test_real_registry_loads_without_issues() -> None:
    sources = load_sources()
    assert len(sources) >= 7
    assert registry_issues([item.to_dict() for item in load_sources()], at=REFERENCE) == []


def test_approved_source_lapses_to_needs_review_past_due() -> None:
    lapsed = source(review_due="2026-09-15")
    assert lapsed.effective_status(REFERENCE) == "needs_review"
    assert lapsed.effective_status(date(2026, 9, 15)) == "approved"


def test_registry_issues_reports_expired_approved_source() -> None:
    entry = source(review_due="2026-09-15").to_dict()
    issues = registry_issues([entry], at=REFERENCE)
    assert any("review date passed" in issue for issue in issues)


def test_registry_issues_requires_url_and_access_for_approved() -> None:
    entry = source(url=None, accessed_at=None).to_dict()
    issues = registry_issues([entry], at=REFERENCE)
    assert any("without URL/access date" in issue for issue in issues)


def test_registry_issues_rejects_duplicate_ids() -> None:
    first = source().to_dict()
    second = source().to_dict()
    issues = registry_issues([first, second], at=REFERENCE)
    assert any("duplicate registry entry" in issue for issue in issues)


def test_approved_source_does_not_raise() -> None:
    ensure_source_approved("SRC-CNC-DFM-001", [source()], REFERENCE)


def test_unknown_source_raises_rul_004() -> None:
    with pytest.raises(MegisError) as excinfo:
        ensure_source_approved("SRC-NOPE-001", [source()], REFERENCE)
    assert excinfo.value.code.code == "MEGIS-RUL-004"


def test_expired_source_raises_rul_001() -> None:
    with pytest.raises(MegisError) as excinfo:
        ensure_source_approved(
            "SRC-CNC-DFM-001",
            [source(review_due="2026-09-15")],
            REFERENCE,
        )
    assert excinfo.value.code.code == "MEGIS-RUL-001"


def test_validate_source_rejects_missing_owner() -> None:
    raw = source().to_dict()
    del raw["owner"]
    with pytest.raises(ValueError):
        validate_source(raw)


def test_draft_rule_is_not_evaluable(corpus: dict) -> None:
    draft_rule = corpus["rules"][0]
    assert draft_rule["status"] == "draft"
    with pytest.raises(MegisError) as excinfo:
        ensure_rule_evaluable(draft_rule, [source()], REFERENCE)
    assert excinfo.value.code.code == "MEGIS-RUL-001"
    assert "only approved rules" in excinfo.value.error_object.engineer_detail


def test_approve_via_registry_requires_approved_source(corpus: dict) -> None:
    in_review = corpus["rules"][1]
    assert in_review["status"] == "in_review"
    approved = approve_rule_via_registry(
        in_review,
        [source()],
        reviewer="REV-SRC-TEST",
        at=REFERENCE,
    )
    assert approved["status"] == "approved"
    assert approved["reviewed_by"] == "REV-SRC-TEST"


def test_approve_via_registry_unknown_source_raises_rul_004(corpus: dict) -> None:
    in_review = corpus["rules"][1]
    registered = source(source_id="SRC-OTHER-001")
    with pytest.raises(MegisError) as excinfo:
        approve_rule_via_registry(in_review, [registered], reviewer="x", at=REFERENCE)
    assert excinfo.value.code.code == "MEGIS-RUL-004"


def test_approve_via_registry_expired_source_raises_rul_001(corpus: dict) -> None:
    in_review = corpus["rules"][1]
    lapsed = source(review_due="2026-09-15")
    with pytest.raises(MegisError) as excinfo:
        approve_rule_via_registry(in_review, [lapsed], reviewer="x", at=REFERENCE)
    assert excinfo.value.code.code == "MEGIS-RUL-001"
