"""G3-VAL-002 CNC DFM rule pack tests (E3)."""

from __future__ import annotations

import copy
import json
from datetime import date
from pathlib import Path

import pytest

from megis.errors import MegisError
from megis.rules.packs import (
    RulePackError,
    condition_holds,
    evaluate_pack_tests,
    evaluate_rule,
    load_rule_pack,
    run_rule_tests,
)
from megis.rules.sources import load_sources, registry_issues
from megis.rules.lifecycle import validate_rule

ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = ROOT / "contracts" / "g3" / "golden" / "cnc-dfm-rulepack.json"
PACK_SCHEMA_PATH = ROOT / "schemas" / "v3" / "rule-pack.schema.json"
RULE_SCHEMA_PATH = ROOT / "schemas" / "v3" / "rule.schema.json"
REFERENCE = date(2026, 9, 22)


@pytest.fixture(scope="module")
def pack() -> dict:
    return load_rule_pack(PACK_PATH)


@pytest.fixture(scope="module")
def pack_schema() -> dict:
    return json.loads(PACK_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_pack_size_within_blueprint_bounds(pack: dict) -> None:
    assert 20 <= len(pack["rules"]) <= 30
    assert pack["workItem"] == "G3-VAL-002"


def test_pack_schema_is_resolvable(pack_schema: dict) -> None:
    from jsonschema import Draft202012Validator

    Draft202012Validator.check_schema(pack_schema)


@pytest.mark.parametrize(
    "rule",
    [
        json.loads(PACK_PATH.read_text(encoding="utf-8"))["rules"][index]
        for index in range(
            len(json.loads(PACK_PATH.read_text(encoding="utf-8"))["rules"])
        )
    ],
    ids=lambda item: item["rule_id"],
)
def test_every_rule_validates_against_rule_schema(rule: dict) -> None:
    validate_rule(copy.deepcopy(rule))
    assert rule["status"] == "in_review"
    assert rule["reviewed_by"] is None


@pytest.mark.parametrize(
    "rule",
    [
        json.loads(PACK_PATH.read_text(encoding="utf-8"))["rules"][index]
        for index in range(
            len(json.loads(PACK_PATH.read_text(encoding="utf-8"))["rules"])
        )
    ],
    ids=lambda item: item["rule_id"],
)
def test_every_rule_fixture_set_passes(rule: dict) -> None:
    results = run_rule_tests(rule, authority="test")
    assert len(results) >= 3
    failures = [item.test_name for item in results if item.status != "pass"]
    assert not failures


def test_pack_all_fixtures_pass(pack: dict) -> None:
    results = evaluate_pack_tests(pack)
    assert len(results) >= 60
    assert all(item.status == "pass" for item in results)


def test_pack_sources_are_registered(pack: dict) -> None:
    registered = {source.source_id for source in load_sources()}
    for rule in pack["rules"]:
        assert rule["source"] in registered


def test_verified_sources_carry_url_and_access_date() -> None:
    sources = {source.source_id: source for source in load_sources()}
    for source_id in (
        "SRC-ISO-2768-1",
        "SRC-ISO-4762",
        "SRC-USB-TYPEC",
        "SRC-IPC-2221",
        "SRC-CNC-DFM-001",
    ):
        source = sources[source_id]
        assert source.url is not None
        assert source.accessed_at == REFERENCE


def test_registry_has_no_issues_at_reference() -> None:
    entries = [source.to_dict() for source in load_sources()]
    assert registry_issues(entries, at=REFERENCE) == []


def test_release_authority_rejects_in_review_rule(pack: dict) -> None:
    rule = pack["rules"][0]
    with pytest.raises(MegisError) as excinfo:
        run_rule_tests(rule, authority="release")
    assert excinfo.value.code.code == "MEGIS-RUL-001"


def test_guard_release_evaluation_rejects_in_review(pack: dict) -> None:
    from megis.rules.packs import guard_release_evaluation

    with pytest.raises(MegisError) as excinfo:
        guard_release_evaluation(
            pack["rules"][0],
            sources=load_sources(),
            at=REFERENCE,
        )
    assert excinfo.value.code.code == "MEGIS-RUL-001"


def test_load_rule_pack_unknown_source_raises_rul_004(tmp_path: Path) -> None:
    raw = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    bad = copy.deepcopy(raw)
    bad["rules"][0]["source"] = "SRC-NOPE-001"
    target = tmp_path / "bad-pack.json"
    target.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(RulePackError) as excinfo:
        load_rule_pack(target)
    assert "MEGIS-RUL-004" in str(excinfo.value)


def test_condition_vocabulary_gte() -> None:
    condition = {"type": "gte", "field": "x", "limit_mm": 1.0}
    assert condition_holds(condition, {"x": 1.5})[0] is True
    assert condition_holds(condition, {"x": 0.5})[0] is False


def test_condition_vocabulary_lte_with_limit_key() -> None:
    condition = {"type": "lte", "field": "x", "limit": 3}
    assert condition_holds(condition, {"x": 2})[0] is True
    assert condition_holds(condition, {"x": 4})[0] is False


def test_condition_vocabulary_ratio_gte() -> None:
    condition = {"type": "ratio_gte", "numerator": "a", "denominator": "b", "limit": 2}
    assert condition_holds(condition, {"a": 6, "b": 3})[0] is True
    assert condition_holds(condition, {"a": 4, "b": 3})[0] is False


def test_condition_vocabulary_ratio_lte() -> None:
    condition = {"type": "ratio_lte", "numerator": "a", "denominator": "b", "limit": 3}
    assert condition_holds(condition, {"a": 6, "b": 3})[0] is True
    assert condition_holds(condition, {"a": 12, "b": 3})[0] is False


def test_condition_vocabulary_within() -> None:
    condition = {"type": "within", "field": "x", "nominal": 0.0, "tolerance": 0.3}
    assert condition_holds(condition, {"x": 0.2})[0] is True
    assert condition_holds(condition, {"x": 0.6})[0] is False


def test_condition_vocabulary_sum_gte() -> None:
    condition = {"type": "sum_gte", "total": "t", "parts": ["a", "b"]}
    assert condition_holds(condition, {"t": 5, "a": 2, "b": 3})[0] is True
    assert condition_holds(condition, {"t": 4, "a": 2, "b": 3})[0] is False


def test_condition_vocabulary_zero() -> None:
    condition = {"type": "zero", "field": "x"}
    assert condition_holds(condition, {"x": 0})[0] is True
    assert condition_holds(condition, {"x": 1})[0] is False


def test_condition_vocabulary_info() -> None:
    condition = {"type": "info", "note": "informational"}
    assert condition_holds(condition, {})[0] is True


def test_evaluate_rule_reports_expected_status(pack: dict) -> None:
    rule = pack["rules"][0]
    held = evaluate_rule(rule, {"wall_thickness_mm": 1.5})
    assert held.status == "pass"
    violated = evaluate_rule(rule, {"wall_thickness_mm": 0.5})
    assert violated.status == "fail"


def test_every_rule_has_all_three_fixture_kinds(pack: dict) -> None:
    for rule in pack["rules"]:
        for kind in ("positive", "negative", "boundary"):
            fixtures = rule["tests"].get(kind, [])
            assert isinstance(fixtures, list)
            assert len(fixtures) >= 1
            for fixture in fixtures:
                assert set(("name", "inputs", "expect")) <= set(fixture)


def test_rule_ids_are_unique(pack: dict) -> None:
    ids = [rule["rule_id"] for rule in pack["rules"]]
    assert len(ids) == len(set(ids))
