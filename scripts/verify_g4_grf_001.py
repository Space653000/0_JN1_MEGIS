"""Verify G4-GRF-001 relationship vocabulary semantics.

Loads contracts/g4/golden/relationship-corpus.json, validates the corpus and
every relationship document against the v3 Relationship schemas, runs the
closed eight-type coverage checks from blueprint 4.16 and compares observed
type index to the golden expectations.  Only a small verification.json is
written; no engineering artifact is generated.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.relationship import (  # noqa: E402
    RELATIONSHIP_TYPES,
    RelationshipValidationError,
    TYPE_MEANING,
    relationship_type_index,
    validate_relationship,
)

CORPUS_PATH = ROOT / "contracts" / "g4" / "golden" / "relationship-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "relationship-corpus.schema.json"
RELATIONSHIP_SCHEMA_PATH = ROOT / "schemas" / "v3" / "relationship.schema.json"
OUT_PATH = ROOT / "artifacts" / "g4-grf-001" / "verification.json"
CREATED_AT = "2026-09-22T17:00:00+08:00"
RELATIONSHIP_VERSION = "megis.relationship@1.0.0"


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


def _relationship_errors(document: dict) -> list[str]:
    try:
        validate_relationship(document)
    except RelationshipValidationError as error:
        return error.errors
    return []


def main() -> int:
    evidence = Evidence()
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    corpus_schema = json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))
    relationship_schema = json.loads(RELATIONSHIP_SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(corpus_schema)
    Draft202012Validator.check_schema(relationship_schema)
    corpus_errors = list(Draft202012Validator(corpus_schema).iter_errors(corpus))
    evidence.expect(
        "golden corpus is schema conformant",
        corpus_errors == [],
        {"errors": [str(error.message) for error in corpus_errors]},
    )
    evidence.expect(
        "corpus covers at least 16 table-driven cases",
        len(corpus["cases"]) >= 16,
        {"cases": len(corpus["cases"])},
    )

    case_results: list[dict] = []
    all_ok = True
    for case in corpus["cases"]:
        document = case["input"]
        schema_ok = (
            list(Draft202012Validator(relationship_schema).iter_errors(document)) == []
        )
        semantic_ok = _relationship_errors(document) == []
        valid = schema_ok and semantic_ok
        expect_valid = case["expect"]["valid"]
        expected_type = case["expect"]["type"]
        relationship_type = document.get("type")
        type_ok = (
            relationship_type_index(relationship_type) == -1
            if expected_type == "invalid"
            else relationship_type == expected_type
            and relationship_type_index(relationship_type)
            == case["expect"]["typeIndex"]
        )
        case_ok = valid == expect_valid and type_ok
        all_ok = all_ok and case_ok
        evidence.expect(
            f"case {case['case_id']} matches golden expectation",
            case_ok,
            {
                "name": case["name"],
                "expectValid": expect_valid,
                "valid": valid,
                "schemaConformant": schema_ok,
                "semanticConformant": semantic_ok,
                "type": relationship_type,
                "expectTypeIndex": case["expect"]["typeIndex"],
                "achievedTypeIndex": relationship_type_index(relationship_type),
            },
        )
        case_results.append(
            {
                "case_id": case["case_id"],
                "valid": valid,
                "type": relationship_type,
                "typeIndex": relationship_type_index(relationship_type),
            }
        )

    for relationship_type in RELATIONSHIP_TYPES:
        positive = any(
            item["type"] == relationship_type and item["valid"] for item in case_results
        )
        negative_evidence = any(
            case["expect"]["type"] == relationship_type and not case["expect"]["valid"]
            for case in corpus["cases"]
        )
        evidence.expect(
            f"type {relationship_type} has positive and negative evidence",
            positive and negative_evidence,
            {"positive": positive, "negative": negative_evidence},
        )
        evidence.expect(
            f"type {relationship_type} has a defined meaning",
            relationship_type in TYPE_MEANING and len(TYPE_MEANING[relationship_type]) > 0,
            {"meaning": TYPE_MEANING.get(relationship_type)},
        )

    evidence.expect(
        "closed eight-type vocabulary is stable",
        relationship_type_index("modelled_invented_type") == -1
        and relationship_type_index(None) == -1,
        {"types": list(RELATIONSHIP_TYPES)},
    )

    positives = sum(1 for item in case_results if item["valid"])
    negatives = sum(1 for item in case_results if not item["valid"])
    summary = {
        "allChecksPassed": not evidence.failed,
        "blueprintRef": "v3.0 4.16 relationship vocabulary, 4.16 type meanings, 26.7 G4-GRF-001",
        "evidenceLevel": "E3",
        "referenceDate": "2026-09-22",
        "schemaVersion": "1.0.0",
        "workItem": "G4-GRF-001",
        "verifiedAt": CREATED_AT,
        "relationshipVersion": RELATIONSHIP_VERSION,
        "engineeringArtifactGenerated": False,
        "releaseArtifactGenerated": False,
        "input": {
            "corpus": str(CORPUS_PATH.relative_to(ROOT)),
            "corpusSchema": str(CORPUS_SCHEMA_PATH.relative_to(ROOT)),
            "relationshipSchema": str(RELATIONSHIP_SCHEMA_PATH.relative_to(ROOT)),
        },
        "summary": {
            "cases": len(corpus["cases"]),
            "positiveCases": positives,
            "negativeCases": negatives,
            "relationshipTypes": list(RELATIONSHIP_TYPES),
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
