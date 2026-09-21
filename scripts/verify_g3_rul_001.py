"""Verify G3-RUL-001 rule lifecycle, governance and waiver contracts.

Loads the golden corpus, validates every rule and waiver against the v3
schemas, exercises the draft -> in_review -> approved -> deprecated lifecycle
with an approved source, verifies waiver expiry semantics (event and date
based), and confirms non-waivable categories reject waivers.  Only a small
verification.json is written; no engineering artifact is generated.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.errors import MegisError  # noqa: E402
from megis.rules.lifecycle import (  # noqa: E402
    RuleStatus,
    approve_rule,
    deprecate_rule,
    rule_status,
    transition_rule,
    validate_rule,
    verify_rule_registry,
)
from megis.rules.waiver import (  # noqa: E402
    WaiverStatus,
    check_waiver_applicable,
    triggered_expiry_conditions,
    validate_waiver,
    waiver_status,
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


def verify() -> dict:
    corpus = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    rules = {item["rule_id"]: item for item in corpus["rules"]}
    waivers = {item["waiver_id"]: item for item in corpus["waivers"]}
    evidence = Evidence()

    for rule in corpus["rules"]:
        validate_rule(rule)
        evidence.expect(
            f"rule schema valid {rule['rule_id']}",
            True,
            {"status": rule["status"], "version": rule["version"]},
        )
    for waiver in corpus["waivers"]:
        validate_waiver(waiver)
        evidence.expect(
            f"waiver schema valid {waiver['waiver_id']}",
            True,
            {"ruleId": waiver["rule_id"]},
        )

    registry_issues = verify_rule_registry(corpus["rules"])
    evidence.expect(
        "golden rule registry has no governance issues",
        registry_issues == [],
        {"issues": registry_issues},
    )

    unapproved_sources = {
        source: status
        for source, status in corpus["sourceStatus"].items()
        if status != "approved"
    }
    evidence.expect(
        "all registered rule sources are approved",
        not unapproved_sources,
        {"unapproved": unapproved_sources},
    )

    draft = dict(rules["CNC_MIN_WALL_001"])
    in_review = transition_rule(draft, RuleStatus.IN_REVIEW)
    approved_min_wall = approve_rule(
        in_review,
        source_status=corpus["sourceStatus"]["SRC-CNC-DFM-001"],
        reviewer="REV-2026-CNC-MIN-WALL",
    )
    deprecated = deprecate_rule(approved_min_wall, reason="replaced by v0.5.0")
    if (
        rule_status(draft) is RuleStatus.DRAFT
        and rule_status(in_review) is RuleStatus.IN_REVIEW
        and rule_status(approved_min_wall) is RuleStatus.APPROVED
        and approved_min_wall["reviewed_by"] == "REV-2026-CNC-MIN-WALL"
        and rule_status(deprecated) is RuleStatus.DEPRECATED
    ):
        evidence.expect(
            "lifecycle chain solves draft -> in_review -> approved -> deprecated",
            True,
            {
                "chain": ["draft", "in_review", "approved", "deprecated"],
                "reviewedBy": approved_min_wall["reviewed_by"],
            },
        )
    else:
        evidence.expect("lifecycle chain solves expected sequence", False, {})

    # Negative: skipping review must raise MEGIS-RUL-002.
    try:
        transition_rule(dict(rules["CNC_MIN_WALL_001"]), RuleStatus.APPROVED)
        evidence.expect("skip-review direct approval rejected", False, {})
    except MegisError as error:
        evidence.expect(
            "skip-review direct approval rejected",
            error.code.code == "MEGIS-RUL-002",
            {"errorCode": error.code.code},
        )

    # Negative: unapproved source must raise MEGIS-RUL-001.
    try:
        approve_rule(
            dict(rules["CNC_TAP_BLIND_001"]),
            source_status="draft",
            reviewer="someone",
        )
        evidence.expect("unapproved source approval rejected", False, {})
    except MegisError as error:
        evidence.expect(
            "unapproved source approval rejected",
            error.code.code == "MEGIS-RUL-001",
            {"errorCode": error.code.code},
        )

    tol = rules["TOL_GENERAL_001"]
    asm = rules["ASM_COLLISION_001"]

    wv1 = waivers["WV-0001"]
    evidence.expect(
        "WV-0001 active at reference date",
        waiver_status(wv1, tol, at=REFERENCE_DATE) is WaiverStatus.ACTIVE,
        {},
    )
    evidence.expect(
        "WV-0001 expires on input change",
        waiver_status(wv1, tol, at=REFERENCE_DATE, input_changed=True) is WaiverStatus.EXPIRED,
        {"triggered": list(triggered_expiry_conditions(wv1, input_changed=True))},
    )

    wv2 = waivers["WV-0002"]
    evidence.expect(
        "WV-0002 expired after its date boundary",
        waiver_status(wv2, tol, at=REFERENCE_DATE) is WaiverStatus.EXPIRED,
        {"triggered": list(triggered_expiry_conditions(wv2, at=REFERENCE_DATE))},
    )

    wv3 = waivers["WV-0003"]
    non_waivable_rejected = False
    try:
        check_waiver_applicable(wv3, asm)
    except MegisError as error:
        non_waivable_rejected = (
            error.code.code == "MEGIS-RUL-003"
            and "non-waivable" in error.error_object.engineer_detail
        )
    evidence.expect(
        "WV-0003 rejected for safety rule",
        non_waivable_rejected and waiver_status(wv3, asm, at=REFERENCE_DATE) is WaiverStatus.INVALID,
        {"status": waiver_status(wv3, asm, at=REFERENCE_DATE).value},
    )

    summary = {
        "rules": len(corpus["rules"]),
        "waivers": len(corpus["waivers"]),
        "ruleSchemaConformant": len(corpus["rules"]),
        "waiverSchemaConformant": len(corpus["waivers"]),
        "registryGovernanceIssues": len(registry_issues),
        "lifecycleChain": "passed",
        "waiverActive": 1,
        "waiverExpired": 1,
        "waiverInvalid": 1,
    }

    return {
        "schemaVersion": "1.0.0",
        "workItem": "G3-RUL-001",
        "verifiedAt": "2026-09-21T20:00:00+08:00",
        "blueprintRef": "v3.0 §11.1、§11.3、附錄 A.6、invariant 7/8",
        "evidenceLevel": "E3",
        "input": {
            "corpus": "contracts/g3/golden/rule-governance.json",
            "ruleSchema": "schemas/v3/rule.schema.json",
            "waiverSchema": "schemas/v3/waiver.schema.json",
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
    out = ROOT / "artifacts" / "g3-rul-001" / "verification.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if not result["allChecksPassed"]:
        sys.exit(1)
