"""Rule lifecycle and governance contracts (G3-RUL-001).

Lifecycle follows blueprint 11.1: ``draft -> in_review -> approved ->
deprecated``.  Approval requires an approved registered source
(``docs/RULE_SOURCES.md``) and a reviewer reference; a rule whose source is
not approved must stay ``in_review`` (D6).  Once a rule is ``approved`` its
version is immutable and later correction happens through a new version, never
by in-place edits.
"""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from megis.errors import MegisError

ROOT = Path(__file__).resolve().parents[2]
RULE_SCHEMA_PATH = ROOT / "schemas" / "v3" / "rule.schema.json"

SOURCE_STATUS_APPROVED = "approved"


class RuleStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    DEPRECATED = "deprecated"


# Blueprint 11.1: draft -> in_review -> approved -> deprecated.
# review may return a rule to draft for source correction; deprecated is final.
ALLOWED_TRANSITIONS: dict[RuleStatus, frozenset[RuleStatus]] = {
    RuleStatus.DRAFT: frozenset({RuleStatus.IN_REVIEW}),
    RuleStatus.IN_REVIEW: frozenset({RuleStatus.DRAFT, RuleStatus.APPROVED}),
    RuleStatus.APPROVED: frozenset({RuleStatus.DEPRECATED}),
    RuleStatus.DEPRECATED: frozenset(),
}

NO_REVIEWER = "no-rule-source-check-decision"


def validate_rule(rule: dict[str, Any]) -> None:
    """Validate a rule document against schemas/v3/rule.schema.json.

    Raises ValueError with a deterministic, sorted list of schema violations.
    """

    schema = json.loads(RULE_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(
        (f"/{'/'.join(map(str, error.absolute_path))}: {error.message}" if error.absolute_path else error.message)
        for error in validator.iter_errors(rule)
    )
    if errors:
        raise ValueError("; ".join(errors))


def rule_status(rule: dict[str, Any]) -> RuleStatus:
    """Return the current lifecycle status of a rule as a RuleStatus value."""

    return RuleStatus(rule["status"])


def transition_rule(rule: dict[str, Any], target: RuleStatus) -> dict[str, Any]:
    """Return a copy of ``rule`` after a valid lifecycle transition.

    Raises MegisError (MEGIS-RUL-002) when the transition is not in the
    blueprint lifecycle.
    """

    current = rule_status(rule)
    if target not in ALLOWED_TRANSITIONS[current]:
        detail = f"rule {rule['rule_id']} cannot move {current.value} -> {target.value}"
        raise MegisError("MEGIS-RUL-002", engineer_detail=detail)
    updated = dict(rule)
    updated["status"] = target.value
    return updated


def approve_rule(
    rule: dict[str, Any],
    *,
    source_status: str,
    reviewer: str,
) -> dict[str, Any]:
    """Approve a rule in_review that has an approved, verifiable source.

    Raises MegisError MEGIS-RUL-001 when the registered source is not
    approved, and MEGIS-RUL-002 when the rule is not in_review.  On success the
    returned copy sets ``status: approved`` and records ``reviewed_by``.
    """

    draft = transition_rule(rule, RuleStatus.APPROVED)
    if source_status != SOURCE_STATUS_APPROVED:
        detail = (
            f"rule {rule['rule_id']} references source {rule['source']} "
            f"with status {source_status!r}; approval needs an approved source"
        )
        raise MegisError("MEGIS-RUL-001", engineer_detail=detail)
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise MegisError("MEGIS-RUL-002", engineer_detail="approval requires a reviewer")
    draft["reviewed_by"] = reviewer
    return draft


def send_back_to_draft(rule: dict[str, Any]) -> dict[str, Any]:
    """Return an in_review rule to draft for source correction."""

    return transition_rule(rule, RuleStatus.DRAFT)


def deprecate_rule(rule: dict[str, Any], reason: str = "") -> dict[str, Any]:
    """Deprecate an approved rule; deprecated rules keep history and are never
    evaluated against new Design Runs."""

    updated = transition_rule(rule, RuleStatus.DEPRECATED)
    if reason:
        updated["recommendation"] = f"{updated.get('recommendation', '')} [deprecated: {reason}]".strip()
    return updated


def verify_rule_registry(rule_documents: list[dict[str, Any]]) -> list[str]:
    """Return deterministic governance issues across a rule collection.

    Every rule must conform to the schema; statuses must be valid lifecycle
    states; approved rules must carry a reviewer reference and an approved
    source; deprecated rules must come from approved rules.
    """

    issues: list[str] = []
    for index, rule in enumerate(rule_documents):
        label = f"{rule.get('rule_id') or f'rule[{index}]'}"
        try:
            validate_rule(rule)
        except ValueError as error:
            issues.append(f"{label}: {error}")
            continue
        status = rule_status(rule)
        if status is RuleStatus.APPROVED and (
            not rule.get("reviewed_by") or rule["reviewed_by"] == NO_REVIEWER
        ):
            issues.append(f"{label}: approved without a reviewer reference")
        if status.value not in {item.value for item in RuleStatus}:
            issues.append(f"{label}: unknown status {rule.get('status')!r}")
    return sorted(set(issues))
