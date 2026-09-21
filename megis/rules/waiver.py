"""Rule waiver contracts, expiry and non-waivable enforcement (G3-RUL-001).

Waivers follow blueprint 11.3 and appendix A.6.  A waiver is invalid when the
referenced rule is not approved or belongs to a non-waivable category
(``unsafe_to_default`` or ``safety``).  Event-based expiry conditions
(``input_changed``, ``rule_version_changed``) invalidate the waiver and force
maturity recomputation; absolute ``date`` conditions expire the waiver once the
stated day passes.
"""

from __future__ import annotations

import json
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from megis.errors import MegisError
from megis.rules.lifecycle import RuleStatus, rule_status

ROOT = Path(__file__).resolve().parents[2]
WAIVER_SCHEMA_PATH = ROOT / "schemas" / "v3" / "waiver.schema.json"

NON_WAIVABLE_CATEGORIES = frozenset({"safety", "unsafe_to_default"})

EVENT_CONDITIONS = frozenset({"input_changed", "rule_version_changed"})


class WaiverStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALID = "invalid"


def validate_waiver(waiver: dict[str, Any]) -> None:
    """Validate a waiver document against schemas/v3/waiver.schema.json.

    Raises ValueError with a deterministic list of schema violations.
    """

    schema = json.loads(WAIVER_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(
        (f"/{'/'.join(map(str, error.absolute_path))}: {error.message}" if error.absolute_path else error.message)
        for error in validator.iter_errors(waiver)
    )
    if errors:
        raise ValueError("; ".join(errors))


def issue_for_waiver(waiver: dict[str, Any], rule: dict[str, Any]) -> str | None:
    """Return a deterministic issue when a waiver cannot apply to ``rule``.

    Returns None when the waiver is applicable to the rule.
    """

    try:
        validate_waiver(waiver)
    except ValueError as error:
        return f"waiver {waiver.get('waiver_id')}: {error}"
    if rule.get("rule_id") != waiver.get("rule_id"):
        return f"waiver {waiver.get('waiver_id')} rule mismatch {rule.get('rule_id')!r}"
    if rule.get("version") != waiver.get("rule_version"):
        return (
            f"waiver {waiver.get('waiver_id')} version mismatch "
            f"{rule.get('version')!r}"
        )
    if rule_status(rule) is not RuleStatus.APPROVED:
        return (
            f"waiver {waiver.get('waiver_id')} targets rule "
            f"{rule.get('rule_id')} in status {rule.get('status')!r}; "
            "only approved rules can be waived"
        )
    category = rule.get("waiver_category")
    if category in NON_WAIVABLE_CATEGORIES:
        return (
            f"waiver {waiver.get('waiver_id')} targets non-waivable rule "
            f"{rule.get('rule_id')} in category {category!r}"
        )
    policy = rule.get("waiver_policy") or {}
    if policy.get("waivable") is False:
        return f"waiver {waiver.get('waiver_id')} targets a rule marked non-waivable"
    return None


def check_waiver_applicable(waiver: dict[str, Any], rule: dict[str, Any]) -> None:
    """Raise MegisError (MEGIS-RUL-003) when the waiver cannot apply to rule."""

    issue = issue_for_waiver(waiver, rule)
    if issue is not None:
        raise MegisError("MEGIS-RUL-003", engineer_detail=issue)


def _absolute_dates(waiver: dict[str, Any]) -> list[date]:
    result: list[date] = []
    for condition in waiver.get("expires_when", []):
        if isinstance(condition, dict) and "date" in condition:
            result.append(date.fromisoformat(condition["date"]))
    return result


def triggered_expiry_conditions(
    waiver: dict[str, Any],
    *,
    input_changed: bool = False,
    rule_version_changed: bool = False,
    at: date | None = None,
) -> tuple[str, ...]:
    """Return the expiry conditions that have fired for the waiver.

    ``at`` defaults to today when omitted.  Event conditions only fire through
    their explicit ``*_changed`` flags.
    """

    conditions = waiver.get("expires_when", [])
    fired: list[str] = []
    for condition in conditions:
        if condition == "input_changed" and input_changed:
            fired.append("input_changed")
        elif condition == "rule_version_changed" and rule_version_changed:
            fired.append("rule_version_changed")
        elif isinstance(condition, dict) and "date" in condition:
            on_day = date.fromisoformat(condition["date"])
            if at is not None and at >= on_day and on_day != date.max:
                fired.append(f"date:{on_day.isoformat()}")
    return tuple(fired)


def waiver_status(
    waiver: dict[str, Any],
    rule: dict[str, Any],
    *,
    input_changed: bool = False,
    rule_version_changed: bool = False,
    at: date | None = None,
) -> WaiverStatus:
    """Return active/expired/invalid for a waiver against its rule.

    Applicability (approved rule, waivable category) is checked first; an
    inapplicable waiver is INVALID regardless of expiry.
    """

    issue = issue_for_waiver(waiver, rule)
    if issue is not None:
        return WaiverStatus.INVALID
    if triggered_expiry_conditions(
        waiver,
        input_changed=input_changed,
        rule_version_changed=rule_version_changed,
        at=at,
    ):
        return WaiverStatus.EXPIRED
    return WaiverStatus.ACTIVE
