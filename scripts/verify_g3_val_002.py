"""Verify G3-VAL-002 CNC DFM rule pack.

Loads contracts/g3/golden/cnc-dfm-rulepack.json through the pack loader (which
validates the pack envelope, every rule against rule.schema.json and every
source against the registered source registry), runs every embedded
positive/negative/boundary fixture, and confirms the release governance gate
rejects evaluation while no source is approved (MEGIS-RUL-001).  Only a small
verification.json is written; no engineering artifact is generated.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from datetime import date  # noqa: E402

from megis.errors import MegisError  # noqa: E402
from megis.rules.packs import (  # noqa: E402
    evaluate_pack_tests,
    guard_release_evaluation,
    load_rule_pack,
    run_rule_tests,
)
from megis.rules.sources import (  # noqa: E402
    load_sources,
    registry_issues,
    source_by_id,
)

PACK_PATH = ROOT / "contracts" / "g3" / "golden" / "cnc-dfm-rulepack.json"
PACK_SCHEMA_PATH = ROOT / "schemas" / "v3" / "rule-pack.schema.json"
RULE_SCHEMA_PATH = ROOT / "schemas" / "v3" / "rule.schema.json"
OUT_PATH = ROOT / "artifacts" / "g3-val-002" / "verification.json"
CREATED_AT = "2026-09-22T10:00:00+08:00"
REFERENCE = date(2026, 9, 22)
VERIFIED_SOURCES = (
    "SRC-ISO-2768-1",
    "SRC-ISO-4762",
    "SRC-USB-TYPEC",
    "SRC-IPC-2221",
    "SRC-CNC-DFM-001",
)


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


def main() -> int:
    evidence = Evidence()
    pack = load_rule_pack(PACK_PATH)
    evidence.expect(
        "rule pack loads and validates",
        len(pack["rules"]) >= 20,
        {
            "rules": len(pack["rules"]),
            "packSchema": str(PACK_SCHEMA_PATH.relative_to(ROOT)),
            "ruleSchema": str(RULE_SCHEMA_PATH.relative_to(ROOT)),
            "workItem": pack["workItem"],
        },
    )

    statuses = {rule["status"] for rule in pack["rules"]}
    evidence.expect(
        "no rule claims approval while sources are unapproved",
        statuses == {"in_review"},
        {"statuses": sorted(statuses)},
    )

    results = evaluate_pack_tests(pack)
    failures = [item.test_name for item in results if item.status != "pass"]
    evidence.expect(
        "all embedded rule fixtures pass",
        not failures,
        {
            "fixtures": len(results),
            "rules": len(pack["rules"]),
            "failures": failures,
        },
    )

    release_rejected = False
    try:
        run_rule_tests(pack["rules"][0], authority="release")
    except MegisError as error:
        release_rejected = error.code.code == "MEGIS-RUL-001"
    evidence.expect(
        "release governance gate rejects unapproved rules",
        release_rejected,
        {"code": "MEGIS-RUL-001", "reason": "no approved rule / source yet"},
    )

    sources = load_sources()
    entries = [source.to_dict() for source in sources]
    evidence.expect(
        "registry has no issues at reference date",
        registry_issues(entries, at=REFERENCE) == [],
        {"issues": registry_issues(entries, at=REFERENCE)},
    )

    verified = [
        source.source_id
        for source in sources
        if source.url and source.accessed_at == REFERENCE
    ]
    evidence.expect(
        "verified public sources carry URL and access date",
        set(VERIFIED_SOURCES) <= set(verified),
        {
            "verified": sorted(verified),
            "expected": list(VERIFIED_SOURCES),
        },
    )

    unregistered = source_by_id(sources, "SRC-NOPE-001")
    evidence.expect(
        "unregistered sources are detected",
        unregistered is None,
        {"probe": "SRC-NOPE-001"},
    )

    works = True
    try:
        guard_release_evaluation(pack["rules"][0], sources=sources, at=REFERENCE)
    except MegisError as error:
        works = error.code.code == "MEGIS-RUL-001"
    evidence.expect(
        "guard_release_evaluation is conservative while unapproved",
        works,
        {"code": "MEGIS-RUL-001"},
    )

    summary = {
        "allChecksPassed": not evidence.failed,
        "blueprintRef": "v3.0 11.1 rule governance, 11.2 first rule set, 26.6 G3-VAL-002",
        "evidenceLevel": "E3",
        "referenceDate": "2026-09-22",
        "schemaVersion": "1.0.0",
        "workItem": "G3-VAL-002",
        "verifiedAt": CREATED_AT,
        "engineeringArtifactGenerated": False,
        "releaseArtifactGenerated": False,
        "input": {
            "pack": str(PACK_PATH.relative_to(ROOT)),
            "packSchema": str(PACK_SCHEMA_PATH.relative_to(ROOT)),
            "ruleSchema": str(RULE_SCHEMA_PATH.relative_to(ROOT)),
            "sources": "config/rule-sources/sources.yaml",
        },
        "summary": {
            "rules": len(pack["rules"]),
            "fixtures": len(results),
            "fixtureFailures": len(failures),
            "sourceCount": len(sources),
            "verifiedSourceCount": len(verified),
        },
        "checks": evidence.checks,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if not evidence.failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
