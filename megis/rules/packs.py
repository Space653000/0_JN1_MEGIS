"""CNC DFM rule pack loading and evaluation (G3-VAL-002).

A rule pack is a versioned container of rules that each satisfy
``schemas/v3/rule.schema.json`` and reference a registered source in
``config/rule-sources/sources.yaml``.  Condition evaluation is table-driven
over a small, documented vocabulary; every rule ships its own positive,
negative and boundary test fixtures, which ``run_rule_tests`` executes for
test coverage while ``guard_release_evaluation`` enforces the governance gate
(only approved rules with approved sources may drive release decisions).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from megis.errors import MegisError
from megis.rules.lifecycle import validate_rule
from megis.rules.sources import (
    ensure_rule_evaluable,
    load_sources,
)

ROOT = Path(__file__).resolve().parents[2]
PACK_SCHEMA_PATH = ROOT / "schemas" / "v3" / "rule-pack.schema.json"
RULEPACK_PATH = ROOT / "contracts" / "g3" / "golden" / "cnc-dfm-rulepack.json"

# Absorption threshold for floating point representation error in comparisons.
EPSILON = 1e-9


class RulePackError(ValueError):
    """A rule pack that cannot be loaded deterministically."""


@dataclass(frozen=True)
class RuleEvaluation:
    """One evaluated rule/test pair with user and engineer copy."""

    rule_id: str
    test_name: str
    status: str
    severity: str
    expected: str | None
    message_zh_tw: str
    engineer_detail: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "test_name": self.test_name,
            "status": self.status,
            "severity": self.severity,
            "expected": self.expected,
            "user_message_zh_tw": self.message_zh_tw,
            "engineer_detail": self.engineer_detail,
            "details": self.details,
        }


def load_rule_pack(path: Path = RULEPACK_PATH) -> dict[str, Any]:
    """Load and fully validate a rule pack.

    Raises RulePackError on envelope or rule schema violations, or when a rule
    references an unregistered source (MEGIS-RUL-004 semantics).
    """

    raw = json.loads(path.read_text(encoding="utf-8"))
    pack_schema = json.loads(PACK_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(pack_schema)
    errors = sorted(
        (
            f"/{'/'.join(map(str, error.absolute_path))}: {error.message}"
            if error.absolute_path
            else error.message
        )
        for error in Draft202012Validator(pack_schema).iter_errors(raw)
    )
    if errors:
        raise RulePackError("; ".join(errors))

    registered = {source.source_id for source in load_sources()}
    for index, rule in enumerate(raw["rules"]):
        try:
            validate_rule(rule)
        except ValueError as error:
            raise RulePackError(f"rule[{index}] {rule.get('rule_id', '?')}: {error}") from error
        if rule["source"] not in registered:
            raise RulePackError(
                f"rule[{index}] {rule['rule_id']}: unknown source "
                f"{rule['source']!r} (MEGIS-RUL-004)"
            )
    return raw


def condition_holds(condition: dict[str, Any], inputs: dict[str, Any]) -> tuple[bool, str]:
    """Evaluate a documented condition type against named inputs.

    Supported types: ``gte``, ``lte``, ``ratio_gte``, ``ratio_lte``,
    ``within``, ``sum_gte``, ``zero`` and informational ``info``.
    """

    ctype = condition["type"]
    if ctype == "info":
        return True, condition.get("note", "informational rule, no numeric gate")
    if ctype == "gte":
        value = inputs[condition["field"]]
        limit = _limit(condition)
        return value >= limit - EPSILON, f"{value} >= {limit}"
    if ctype == "lte":
        value = inputs[condition["field"]]
        limit = _limit(condition)
        return value <= limit + EPSILON, f"{value} <= {limit}"
    if ctype == "ratio_gte":
        numerator = inputs[condition["numerator"]]
        denominator = inputs[condition["denominator"]]
        ratio = numerator / denominator
        limit = condition["limit"]
        return ratio >= limit - EPSILON, f"{ratio:.3f} >= {limit}"
    if ctype == "ratio_lte":
        numerator = inputs[condition["numerator"]]
        denominator = inputs[condition["denominator"]]
        ratio = numerator / denominator
        limit = condition["limit"]
        return ratio <= limit + EPSILON, f"{ratio:.3f} <= {limit}"
    if ctype == "within":
        value = inputs[condition["field"]]
        nominal = condition["nominal"]
        tolerance = condition["tolerance"]
        gap = abs(value - nominal)
        return gap <= tolerance, f"|{value} - {nominal}| = {gap:.3f} <= {tolerance}"
    if ctype == "sum_gte":
        total = inputs[condition["total"]]
        parts_sum = sum(inputs[part] for part in condition["parts"])
        return total >= parts_sum, f"{total} >= {parts_sum}"
    if ctype == "zero":
        value = inputs[condition["field"]]
        return value == 0, f"{value} == 0"
    raise RulePackError(f"unsupported condition type {ctype!r}")


def _limit(condition: dict[str, Any]) -> float:
    """Return the numeric limit from ``limit_mm`` when present, else ``limit``."""

    if "limit_mm" in condition:
        return condition["limit_mm"]
    return condition["limit"]


def severity_message(severity: str) -> str:
    return {
        "error": "規則違反，需修正後才可繼續。",
        "warning": "規則提示，建議檢視後再決定。",
        "info": "資訊性規則，僅供紀錄。",
    }[severity]


def evaluate_rule(rule: dict[str, Any], inputs: dict[str, Any]) -> RuleEvaluation:
    """Evaluate one rule against one input snapshot (test mode, no governance gate)."""

    holds, detail = condition_holds(rule["condition"], inputs)
    status = "pass" if holds else "fail"
    return RuleEvaluation(
        rule_id=rule["rule_id"],
        test_name="direct_evaluation",
        status=status,
        severity=rule["severity"],
        expected=None,
        message_zh_tw=severity_message(rule["severity"]),
        engineer_detail=(
            f"{rule['rule_id']}: {rule['source_clause']} "
            f"-> {detail} [not verified as approved; test mode]"
        ),
        details={"condition": rule["condition"]},
    )


def run_rule_tests(
    rule: dict[str, Any],
    *,
    authority: str = "test",
    sources: list[Any] | None = None,
    at: date | None = None,
) -> list[RuleEvaluation]:
    """Run the rule's positive/negative/boundary fixtures.

    In ``test`` authority the condition logic is exercised directly; in
    ``release`` authority each fixture first passes through the governance gate
    (only approved rules with approved sources may be evaluated).
    """

    results: list[RuleEvaluation] = []
    for kind in ("positive", "negative", "boundary"):
        for fixture in rule["tests"].get(kind, []):
            inputs = fixture["inputs"]
            if authority == "release":
                guard_release_evaluation(rule, sources=sources, at=at)
            holds, detail = condition_holds(rule["condition"], inputs)
            expected = fixture["expect"]
            status = "pass" if holds == (expected == "pass") else "fail"
            results.append(
                RuleEvaluation(
                    rule_id=rule["rule_id"],
                    test_name=f"{kind}:{fixture['name']}",
                    status=status,
                    severity=rule["severity"],
                    expected=expected,
                    message_zh_tw=severity_message(rule["severity"]),
                    engineer_detail=(
                        f"{rule['rule_id']} [{kind}] expected {expected}, "
                        f"got {'pass' if holds else 'fail'} ({detail})"
                    ),
                    details={"inputs": inputs},
                )
            )
    return results


def guard_release_evaluation(
    rule: dict[str, Any],
    *,
    sources: list[Any] | None = None,
    at: date | None = None,
) -> None:
    """Enforce that only approved rules with approved sources are evaluated."""

    ensure_rule_evaluable(rule, sources if sources is not None else load_sources(), at or date.today())


def evaluate_pack_tests(pack: dict[str, Any]) -> list[RuleEvaluation]:
    """Run every embedded fixture for every rule in the pack."""

    results: list[RuleEvaluation] = []
    for rule in pack["rules"]:
        results.extend(run_rule_tests(rule))
    return results
