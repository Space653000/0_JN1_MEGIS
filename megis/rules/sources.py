"""Rule source registry, expiry and approval workflow (G3-SRC-001).

Sources live in the machine-readable ``config/rule-sources/sources.yaml``
registry and are mirrored in ``docs/RULE_SOURCES.md``.  A source can underpin
an approved rule only while it is registered with status ``approved`` and its
``review_due`` date has not passed; an expired approved source automatically
returns to ``needs_review``.  Draft or unapproved rules can never be evaluated
as approved.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from megis.errors import MegisError
from megis.rules.lifecycle import (
    RuleStatus,
    approve_rule,
    rule_status,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCES_PATH = ROOT / "config" / "rule-sources" / "sources.yaml"
SOURCE_SCHEMA_PATH = ROOT / "schemas" / "v3" / "rule-source.schema.json"

SOURCE_STATUS_APPROVED = "approved"
SOURCE_STATUS_NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class RuleSource:
    """A validated rule source registry entry."""

    source_id: str
    type: str
    status: str
    revision: str
    owner: str
    review_due: date
    url: str | None
    accessed_at: date | None
    notes: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RuleSource":
        return cls(
            source_id=raw["source_id"],
            type=raw["type"],
            status=raw["status"],
            revision=raw["revision"],
            owner=raw["owner"],
            review_due=date.fromisoformat(raw["review_due"]),
            url=raw.get("url"),
            accessed_at=(
                date.fromisoformat(raw["accessed_at"]) if raw.get("accessed_at") else None
            ),
            notes=raw.get("notes", ""),
        )

    def effective_status(self, at: date) -> str:
        """Approved sources lapse to needs_review once review_due passes."""

        if self.status == SOURCE_STATUS_APPROVED and at > self.review_due:
            return SOURCE_STATUS_NEEDS_REVIEW
        return self.status

    def to_dict(self) -> dict[str, Any]:
        """Return a schema-valid raw dictionary with ISO dates."""

        return {
            "source_id": self.source_id,
            "type": self.type,
            "status": self.status,
            "revision": self.revision,
            "owner": self.owner,
            "review_due": self.review_due.isoformat(),
            "url": self.url,
            "accessed_at": self.accessed_at.isoformat() if self.accessed_at else None,
            "notes": self.notes,
        }


def validate_source(raw: dict[str, Any]) -> None:
    """Validate a source registry entry against rule-source.schema.json."""

    schema = json.loads(SOURCE_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(
        (f"/{'/'.join(map(str, error.absolute_path))}: {error.message}" if error.absolute_path else error.message)
        for error in validator.iter_errors(raw)
    )
    if errors:
        raise ValueError("; ".join(errors))


def load_sources(path: Path = SOURCES_PATH) -> list[RuleSource]:
    """Load and parse the machine-readable source registry."""

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [RuleSource.from_dict(entry) for entry in raw["sources"]]


def registry_issues(entries: list[dict[str, Any]], at: date) -> list[str]:
    """Return deterministic validation and expiry issues for registry entries.

    Every entry must conform to the schema, source IDs must be unique, and
    approved entries with no URL/access date or a lapsed review date are
    reported as needs-review problems rather than silently trusted.
    """

    issues: list[str] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        source_id = entry.get("source_id", f"source[{index}]")
        try:
            validate_source(entry)
        except ValueError as error:
            issues.append(f"{source_id}: {error}")
            continue
        if source_id in seen:
            issues.append(f"{source_id}: duplicate registry entry")
        seen.add(source_id)
        status = entry["status"]
        if status == SOURCE_STATUS_APPROVED:
            if not entry.get("url") or not entry.get("accessed_at"):
                issues.append(f"{source_id}: approved without URL/access date")
            review_due = date.fromisoformat(entry["review_due"])
            if at > review_due:
                issues.append(f"{source_id}: review date passed; must return to needs_review")
    return sorted(set(issues))


def source_by_id(sources: list[RuleSource], source_id: str) -> RuleSource | None:
    """Return the registry entry for a source ID, or None when unregistered."""

    for source in sources:
        if source.source_id == source_id:
            return source
    return None


def ensure_source_approved(source_id: str, sources: list[RuleSource], at: date) -> None:
    """Raise when a source is not currently usable to back approved rules.

    MEGIS-RUL-004 for unknown or invalid entries, MEGIS-RUL-001 when the
    source is unapproved or its review date has lapsed.
    """

    source = source_by_id(sources, source_id)
    if source is None:
        raise MegisError(
            "MEGIS-RUL-004",
            engineer_detail=f"source {source_id!r} is not registered",
        )
    if source.effective_status(at) != SOURCE_STATUS_APPROVED:
        raise MegisError(
            "MEGIS-RUL-001",
            engineer_detail=(
                f"source {source_id!r} has status {source.effective_status(at)!r} "
                f"at {at.isoformat()} and cannot back an approved rule"
            ),
        )


def ensure_rule_evaluable(
    rule: dict[str, Any],
    sources: list[RuleSource],
    at: date,
) -> None:
    """Raise when a rule cannot be evaluated.

    Draft, in_review and deprecated rules are never evaluated as approved
    (MEGIS-RUL-001); an approved rule also needs its source to be approved.
    """

    status = rule_status(rule)
    if status is not RuleStatus.APPROVED:
        raise MegisError(
            "MEGIS-RUL-001",
            engineer_detail=(
                f"rule {rule['rule_id']} is {status.value!r}; "
                "only approved rules can be evaluated"
            ),
        )
    ensure_source_approved(rule["source"], sources, at)


def approve_rule_via_registry(
    rule: dict[str, Any],
    sources: list[RuleSource],
    reviewer: str,
    at: date,
) -> dict[str, Any]:
    """Approve an in_review rule whose source is approved in the registry."""

    ensure_source_approved(rule["source"], sources, at)
    return approve_rule(rule, source_status=SOURCE_STATUS_APPROVED, reviewer=reviewer)
