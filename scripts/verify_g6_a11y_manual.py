"""Validate human-authored G6 accessibility evidence without inventing it."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "v3" / "accessibility-manual-audit.schema.json"
TEMPLATE_PATH = ROOT / "contracts" / "g6" / "templates" / "accessibility-manual-audit.template.json"

KEYBOARD_CHECK_IDS = (
    "skip-link",
    "desktop-navigation",
    "mobile-navigation",
    "design-form",
    "review-flow",
    "progress-disclosure",
)
SCREEN_READER_CHECK_IDS = (
    "landmarks",
    "design-form",
    "review-unknowns",
    "run-announcements",
    "results-boundaries",
    "progress-table",
)


class EvidenceError(ValueError):
    """Raised when manual evidence is invalid or internally inconsistent."""


def _canonical_fingerprint(document: dict[str, Any]) -> str:
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _format_error(error: Any) -> str:
    location = "/" + "/".join(str(part) for part in error.absolute_path)
    return f"schema validation failed at {location}: {error.message}"


def _validate_section(section_name: str, section: dict[str, Any], expected_ids: tuple[str, ...]) -> None:
    actual_ids = tuple(check["id"] for check in section["checks"])
    if actual_ids != expected_ids:
        raise EvidenceError(f"{section_name} must contain the exact required check IDs in canonical order")

    results = [check["result"] for check in section["checks"]]
    status = section["status"]
    if status == "pending" and any(result != "pending" for result in results):
        raise EvidenceError(f"{section_name} pending section requires every check to remain pending")
    if status == "passed" and any(result != "passed" for result in results):
        raise EvidenceError(f"{section_name} passed section requires every check to pass")
    if status == "failed":
        if "pending" in results or "failed" not in results:
            raise EvidenceError(f"{section_name} failed section requires completed checks and at least one failure")

    for check in section["checks"]:
        if check["result"] == "failed" and not check["notes"].strip():
            raise EvidenceError(f"{section_name} failed check requires notes: {check['id']}")


def evaluate_document(document: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic summary or fail closed on malformed evidence."""

    validator = Draft202012Validator(_schema(), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
    if errors:
        raise EvidenceError(_format_error(errors[0]))

    _validate_section("keyboard", document["keyboard"], KEYBOARD_CHECK_IDS)
    _validate_section("screenReader", document["screenReader"], SCREEN_READER_CHECK_IDS)

    all_checks = document["keyboard"]["checks"] + document["screenReader"]["checks"]
    counts = {
        result: sum(check["result"] == result for check in all_checks)
        for result in ("passed", "failed", "pending")
    }
    closure_eligible = (
        document["keyboard"]["status"] == "passed"
        and document["screenReader"]["status"] == "passed"
        and counts == {"passed": 12, "failed": 0, "pending": 0}
    )
    return {
        "schemaVersion": "1.0.0",
        "workItem": "G6-A11Y-001",
        "evidenceType": "human_manual_audit_verification",
        "schemaValid": True,
        "recordFingerprint": _canonical_fingerprint(document),
        "keyboardStatus": document["keyboard"]["status"],
        "screenReaderStatus": document["screenReader"]["status"],
        "passedChecks": counts["passed"],
        "failedChecks": counts["failed"],
        "pendingChecks": counts["pending"],
        "closureEligible": closure_eligible,
        "boundaries": {
            "humanIdentityRequiredForCompletion": True,
            "agentGeneratedHumanEvidence": False,
            "engineeringArtifactsGenerated": False,
        },
    }


def _inside_workspace(path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError as exc:
        raise EvidenceError(f"path is outside workspace: {resolved}") from exc
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=TEMPLATE_PATH)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()

    try:
        input_path = _inside_workspace(args.input)
        document = json.loads(input_path.read_text(encoding="utf-8"))
        result = evaluate_document(document)
        if args.require_complete and not result["closureEligible"]:
            raise EvidenceError("manual audit is valid but incomplete; closure remains ineligible")
        if args.output:
            output_path = _inside_workspace(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (EvidenceError, json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"workItem": "G6-A11Y-001", "status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
