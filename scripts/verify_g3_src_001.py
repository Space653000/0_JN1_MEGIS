"""Verify G3-SRC-001 rule source registry and verification workflow.

Loads config/rule-sources/sources.yaml, validates every entry against the v3
schema, checks that approved sources lapse to needs_review once their review
date passes, rejects unknown or expired sources, blocks draft rules from being
evaluated as approved, and exercises the registry-backed approval path.  Only a
small verification.json is written; no engineering artifact is generated.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.errors import MegisError  # noqa: E402
from megis.rules.sources import (  # noqa: E402
    RuleSource,
    approve_rule_via_registry,
    ensure_rule_evaluable,
    ensure_source_approved,
    load_sources,
    registry_issues,
    validate_source,
)

GOLDEN_PATH = ROOT / "contracts" / "g3" / "golden" / "rule-governance.json"
REFERENCE_DATE = date(2026, 9, 21)


class Evidence:
    """Collect check results and keep the record machine-readable."""

    def __init__(self) -> None:
        self.checks: list[dict] = []
        self.failed = False

    def expect(self, name: str, condition: bool, detail: object) -> None:
        if not condition:
            self.failed = True
        self.checks.append(
            {
                "name": name,
                "passed": bool(condition),
                "detail": detail,
            }
        )


def fixture_source() -> RuleSource:
    return RuleSource(
        source_id="SRC-CNC-DFM-001",
        type="internal",
        status="approved",
        revision="2026-A",
        owner="mechanical_engineering",
        review_due=date(2026, 12, 31),
        url="https://example.net/machining-guide",
        accessed_at=date(2026, 9, 20),
    )


def verify() -> dict:
    corpus = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    rules = {item["rule_id"]: item for item in corpus["rules"]}
    registered = load_sources()
    evidence = Evidence()

    for entry in registered:
        try:
            validate_source(entry.to_dict())
            evidence.expect(
                f"registry schema valid {entry.source_id}",
                True,
                {"status": entry.status},
            )
        except ValueError as error:
            evidence.expect(
                f"registry schema valid {entry.source_id}",
                False,
                {"error": str(error)},
            )

    issues = registry_issues([entry.to_dict() for entry in registered], at=REFERENCE_DATE)
    evidence.expect(
        "real registry has no governance issues at reference date",
        issues == [],
        {"issues": issues},
    )
    evidence.expect(
        "real registry currently has no approved source (conservative state)",
        all(entry.effective_status(REFERENCE_DATE) != "approved" for entry in registered),
        {
            "statuses": {
                entry.source_id: entry.effective_status(REFERENCE_DATE)
                for entry in registered
            }
        },
    )

    fixture = fixture_source()
    ensure_source_approved("SRC-CNC-DFM-001", [fixture], REFERENCE_DATE)
    evidence.expect(
        "approved fixture source passes approval gate",
        True,
        {"sourceId": fixture.source_id},
    )

    lapsed_source = RuleSource(
        source_id=fixture.source_id,
        type=fixture.type,
        status=fixture.status,
        revision=fixture.revision,
        owner=fixture.owner,
        review_due=date(2026, 9, 15),
        url=fixture.url,
        accessed_at=fixture.accessed_at,
        notes=fixture.notes,
    )
    evidence.expect(
        "approved source lapses to needs_review after review date",
        lapsed_source.effective_status(REFERENCE_DATE) == "needs_review",
        {"effectiveStatus": lapsed_source.effective_status(REFERENCE_DATE)},
    )

    try:
        ensure_source_approved("SRC-UNKNOWN-001", [fixture], REFERENCE_DATE)
        evidence.expect("unknown source rejected", False, {})
    except MegisError as error:
        evidence.expect(
            "unknown source rejected",
            error.code.code == "MEGIS-RUL-004",
            {"errorCode": error.code.code},
        )

    try:
        ensure_source_approved("SRC-CNC-DFM-001", [lapsed_source], REFERENCE_DATE)
        evidence.expect("expired source rejected", False, {})
    except MegisError as error:
        evidence.expect(
            "expired source rejected",
            error.code.code == "MEGIS-RUL-001",
            {"errorCode": error.code.code},
        )

    draft_rule = rules["CNC_MIN_WALL_001"]
    try:
        ensure_rule_evaluable(draft_rule, [fixture], REFERENCE_DATE)
        evidence.expect("draft rule never evaluated as approved", False, {})
    except MegisError as error:
        evidence.expect(
            "draft rule never evaluated as approved",
            error.code.code == "MEGIS-RUL-001"
            and "only approved rules" in error.error_object.engineer_detail,
            {"errorCode": error.code.code},
        )

    in_review = rules["CNC_TAP_BLIND_001"]
    approved = approve_rule_via_registry(
        in_review,
        [fixture],
        reviewer="REV-SRC-2026",
        at=REFERENCE_DATE,
    )
    evidence.expect(
        "registry-backed approval succeeds with reviewed_by",
        approved["status"] == "approved"
        and approved["reviewed_by"] == "REV-SRC-2026",
        {"status": approved["status"], "reviewedBy": approved["reviewed_by"]},
    )

    summary = {
        "registeredSources": len(registered),
        "approvedSources": sum(
            1 for entry in registered if entry.effective_status(REFERENCE_DATE) == "approved"
        ),
        "registryGovernanceIssues": len(issues),
    }

    return {
        "schemaVersion": "1.0.0",
        "workItem": "G3-SRC-001",
        "verifiedAt": "2026-09-21T21:00:00+08:00",
        "blueprintRef": "v3.0 §19.1、G3-SRC-001、invariant 7",
        "evidenceLevel": "E3",
        "input": {
            "registry": "config/rule-sources/sources.yaml",
            "schema": "schemas/v3/rule-source.schema.json",
            "goldenCorpus": "contracts/g3/golden/rule-governance.json",
        },
        "referenceDate": REFERENCE_DATE.isoformat(),
        "summary": summary,
        "checks": evidence.checks,
        "allChecksPassed": not evidence.failed,
        "engineeringArtifactGenerated": False,
        "releaseArtifactGenerated": False,
    }


if __name__ == "__main__":
    result = verify()
    out = ROOT / "artifacts" / "g3-src-001" / "verification.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if not result["allChecksPassed"]:
        sys.exit(1)
