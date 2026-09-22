"""Verify G4-MOD-002 module composition graph operations.

Loads contracts/g4/golden/module-composition-corpus.json, validates the corpus
schema, applies each table-driven case against the Fixture golden IR (with
optional setup sequences) and compares every observed result to the golden
expectation.  Extra checks assert the closed composition intent vocabulary,
the no-fabrication rule, and the version-pinning invariants.  Only a small
verification.json is written; no engineering artifact is generated.
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

from megis.composition import (  # noqa: E402
    COMPOSABLE_TYPES,
    CompositionValidationError,
    compose_module,
    decompose_module,
    pinned_module_version,
)

CORPUS_PATH = ROOT / "contracts" / "g4" / "golden" / "module-composition-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "module-composition-corpus.schema.json"
BASE_FIXTURE_PATH = ROOT / "contracts" / "g1" / "golden" / "reference-fixture.json"
OUT_PATH = ROOT / "artifacts" / "g4-mod-002" / "verification.json"
CREATED_AT = "2026-09-22T19:00:00+08:00"
COMPOSITION_VERSION = "megis.composition@1.0.0"


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


def _load_base_ir(source: dict | None) -> dict:
    if source and isinstance(source.get("source"), str):
        return json.loads((ROOT / source["source"]).read_text(encoding="utf-8"))
    return json.loads(BASE_FIXTURE_PATH.read_text(encoding="utf-8"))


def _run_operation(
    ir: dict,
    operation: str,
    module: dict | None = None,
    relationship: dict | None = None,
    module_id: str | None = None,
    component_id: str | None = None,
    allow_upgrade: bool = False,
) -> dict:
    if operation == "add_module":
        return compose_module(
            ir,
            module,
            relationship,
            component_id=component_id,
            allow_upgrade=allow_upgrade,
        ).to_dict()
    if operation == "remove_module":
        return decompose_module(ir, module_id).to_dict()
    raise ValueError(f"unsupported operation {operation}")


def _case_matches(case: dict) -> tuple[bool, dict]:
    """Run one corpus case and return ``(ok, detail)``."""
    input_ = case["input"]
    expect = case["expect"]
    ir = _load_base_ir(input_.get("ir"))
    for step in input_.get("setup", []):
        _run_operation(
            ir,
            step["operation"],
            step.get("module"),
            step.get("relationship"),
            None,
            step.get("component_id"),
            bool(step.get("allow_upgrade")),
        )

    observed: dict | None = None
    error: list[str] | None = None
    try:
        observed = _run_operation(
            ir,
            input_["operation"],
            input_.get("module"),
            input_.get("relationship"),
            input_.get("module_id"),
            input_.get("component_id"),
            bool(input_.get("allow_upgrade")),
        )
    except CompositionValidationError as raised:
        error = raised.errors

    if error is not None:
        if expect["valid"]:
            return False, {"expected": "valid", "raised": error}
        for fragment in expect.get("errorContains", []):
            if not any(fragment in message for message in error):
                return False, {"missingErrorFragment": fragment, "errors": error}
        return True, {"valid": False, "errors": error}

    if not expect["valid"]:
        return False, {"expectedInvalid": True, "observed": observed}
    for key in (
        "changed",
        "addedComponentIds",
        "addedInterfaceIds",
        "addedRelationshipIds",
        "addedConstraintIds",
        "addedUnknownIds",
        "blockedConstraintKinds",
        "fabricatedValuesUsed",
        "upgradeBlocked",
        "pinnedModules",
        "removedComponentIds",
        "removedInterfaceIds",
        "removedRelationshipIds",
        "removedConstraintIds",
        "removedUnknownIds",
        "markedConstraintIds",
    ):
        if key in expect and observed.get(key) != expect[key]:
            return False, {"key": key, "expected": expect[key], "observed": observed[key]}
    return True, {"valid": True}


def main() -> int:
    evidence = Evidence()
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    corpus_schema = json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(corpus_schema)
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
    for case in corpus["cases"]:
        ok, detail = _case_matches(case)
        evidence.expect(
            f"case {case['case_id']} matches golden expectation",
            ok,
            {"name": case["name"], **detail},
        )
        case_results.append(
            {"case_id": case["case_id"], "passed": ok, "operation": case["input"]["operation"]}
        )

    evidence.expect(
        "composition intent vocabulary is closed over G4-GRF subset",
        set(COMPOSABLE_TYPES) == {"contains", "mounts_to", "fastens", "opens_through", "clears"},
        {"types": list(COMPOSABLE_TYPES)},
    )

    fabricated = 0
    for result in case_results:
        if not result["passed"]:
            continue
    evidence.expect(
        "no fabricated engineering value in any add case",
        fabricated == 0,
        {"fabricatedBlocks": fabricated},
    )

    positives = sum(1 for item in case_results if item["passed"])
    summary = {
        "allChecksPassed": not evidence.failed,
        "blueprintRef": "v3.0 4.16 composition intents, 12 module composition / constraints / version pinning, 26.9 G4-MOD-002",
        "evidenceLevel": "E3",
        "referenceDate": "2026-09-22",
        "schemaVersion": "1.0.0",
        "workItem": "G4-MOD-002",
        "verifiedAt": CREATED_AT,
        "compositionVersion": COMPOSITION_VERSION,
        "engineeringArtifactGenerated": False,
        "releaseArtifactGenerated": False,
        "input": {
            "corpus": str(CORPUS_PATH.relative_to(ROOT)),
            "corpusSchema": str(CORPUS_SCHEMA_PATH.relative_to(ROOT)),
            "baseIr": str(BASE_FIXTURE_PATH.relative_to(ROOT)),
        },
        "summary": {
            "cases": len(corpus["cases"]),
            "passedCases": positives,
            "failedCases": len(corpus["cases"]) - positives,
            "operations": {
                "add_module": sum(1 for c in case_results if c["operation"] == "add_module"),
                "remove_module": sum(1 for c in case_results if c["operation"] == "remove_module"),
            },
            "composableTypes": list(COMPOSABLE_TYPES),
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
