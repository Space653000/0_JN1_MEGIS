"""Verify G4-MOD-001 module capability levels.

Loads contracts/g4/golden/module-corpus.json, validates the corpus and every
module document against the v3 Module schemas, runs the capability policy
checks for the closed four-level vocabulary and compares observed index and
geometry-generator requirements to the golden expectations.  Only a small
verification.json is written; no engineering artifact is generated.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.module import (  # noqa: E402
    CAPABILITY_LEVELS,
    GEOMETRY_CAPABLE_INDEX,
    ModuleValidationError,
    capability_index,
    geometry_generator_required,
    policy_for,
    validate_module_document,
)

CORPUS_PATH = ROOT / "contracts" / "g4" / "golden" / "module-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "module-corpus.schema.json"
MODULE_SCHEMA_PATH = ROOT / "schemas" / "v3" / "module.schema.json"
OUT_PATH = ROOT / "artifacts" / "g4-mod-001" / "verification.json"
CREATED_AT = "2026-09-22T15:30:00+08:00"
MODULE_VERSION = "megis.module@1.0.0"


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


def _module_errors(document: dict) -> list[str]:
    try:
        validate_module_document(document)
    except ModuleValidationError as error:
        return error.errors
    return []


def main() -> int:
    evidence = Evidence()
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    corpus_schema = json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))
    module_schema = json.loads(MODULE_SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(corpus_schema)
    Draft202012Validator.check_schema(module_schema)
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
        schema_ok = list(Draft202012Validator(module_schema).iter_errors(document)) == []
        semantic_ok = _module_errors(document) == []
        valid = schema_ok and semantic_ok
        expect_valid = case["expect"]["valid"]
        expected_level = case["expect"]["capabilityLevel"]
        level = document.get("capability_level")
        level_ok = (
            capability_index(level) == -1
            if expected_level == "invalid"
            else level == expected_level and capability_index(level) == case["expect"]["index"]
        )
        generator_ok = (
            geometry_generator_required(level) == case["expect"]["geometryGeneratorRequired"]
        )
        case_ok = valid == expect_valid and level_ok and generator_ok
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
                "capabilityLevel": level,
                "expectIndex": case["expect"]["index"],
                "achievedIndex": capability_index(level),
                "geometryGeneratorRequired": geometry_generator_required(level),
            },
        )
        case_results.append(
            {
                "case_id": case["case_id"],
                "valid": valid,
                "capabilityLevel": level,
                "index": capability_index(level),
            }
        )

    evidence.expect(
        "closed four-level vocabulary has monotonic ordering",
        [capability_index(level) for level in CAPABILITY_LEVELS] == [0, 1, 2, 3],
        {"levels": list(CAPABILITY_LEVELS)},
    )

    policy_checks = {
        "metadata_only": (False, False, "DRAFT"),
        "layout_capable": (True, False, "CONCEPT"),
        "geometry_capable": (True, True, "PROTOTYPE"),
        "validated": (True, True, "PROTOTYPE"),
    }
    for level, (layout, geometry, maturity_cap) in policy_checks.items():
        policy = policy_for(level)
        evidence.expect(
            f"policy for {level} matches blueprint",
            policy.layout_allowed is layout
            and policy.geometry_allowed is geometry
            and policy.maturity_cap == maturity_cap
            and bool((policy.validation or ()))
            != (level == "metadata_only"),
            {
                "layout": policy.layout_allowed,
                "geometry": policy.geometry_allowed,
                "maturity_cap": policy.maturity_cap,
                "validation": list(policy.validation),
            },
        )

    geometry_requirement = {
        level: geometry_generator_required(level) for level in CAPABILITY_LEVELS
    }
    evidence.expect(
        "geometry_generator_required only from geometry_capable",
        geometry_requirement
        == {
            "metadata_only": False,
            "layout_capable": False,
            "geometry_capable": True,
            "validated": True,
        },
        geometry_requirement,
    )
    evidence.expect(
        "geometry_capable index gate is enforced",
        GEOMETRY_CAPABLE_INDEX == 2,
        {"gateIndex": GEOMETRY_CAPABLE_INDEX},
    )

    positives = sum(1 for item in case_results if item["valid"])
    negatives = sum(1 for item in case_results if not item["valid"])
    summary = {
        "allChecksPassed": not evidence.failed,
        "blueprintRef": "v3.0 4.16 module fields and levels, 12 capability restrictions, 26.7 G4-MOD-001",
        "evidenceLevel": "E3",
        "referenceDate": "2026-09-22",
        "schemaVersion": "1.0.0",
        "workItem": "G4-MOD-001",
        "verifiedAt": CREATED_AT,
        "moduleVersion": MODULE_VERSION,
        "engineeringArtifactGenerated": False,
        "releaseArtifactGenerated": False,
        "input": {
            "corpus": str(CORPUS_PATH.relative_to(ROOT)),
            "corpusSchema": str(CORPUS_SCHEMA_PATH.relative_to(ROOT)),
            "moduleSchema": str(MODULE_SCHEMA_PATH.relative_to(ROOT)),
        },
        "summary": {
            "cases": len(corpus["cases"]),
            "positiveCases": positives,
            "negativeCases": negatives,
            "capabilityLevels": list(CAPABILITY_LEVELS),
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
