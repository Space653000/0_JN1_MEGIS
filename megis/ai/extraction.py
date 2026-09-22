"""Schema-bound Intent → Requirement draft quarantine.

AI output remains ``llm_proposed`` until the user confirms individual fields.
The functions in this module never repair malformed provider JSON and never
write proposed values directly into Engineering IR.
"""

from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator

from megis.contracts.validation import validate_engineering_ir
from megis.errors import MegisError
from megis.guides.flow import GuidedAnswers, build_ir_draft

ROOT = Path(__file__).resolve().parents[2]
DRAFT_SCHEMA_PATH = ROOT / "schemas" / "v3" / "ai-requirement-draft.schema.json"

NUMERIC_FIELDS = {"width_mm", "depth_mm", "height_mm", "pcb_count"}
DIMENSION_FIELDS = {"width_mm", "depth_mm", "height_mm"}
FIELD_TO_ANSWER = {
    "width_mm": "width_mm",
    "depth_mm": "depth_mm",
    "height_mm": "height_mm",
    "pcb_count": "pcb_count",
    "pcb_envelope_mode": "pcb_envelope_mode",
    "purpose": "purpose",
    "priority": "priority",
    "quantity": "quantity",
    "connector": "connector",
    "fastener": "fastener",
    "cover": "cover",
}


def parse_requirement_draft(raw_output: str, source_text: str) -> dict[str, Any]:
    """Reject malformed/unsubstantiated AI output and return a quarantined draft."""

    try:
        document = json.loads(raw_output)
    except (json.JSONDecodeError, TypeError) as exc:
        raise _invalid("provider output is not valid JSON") from exc
    if not isinstance(document, dict):
        raise _invalid("provider output must be a JSON object")

    schema = json.loads(DRAFT_SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise _invalid(
            "schema-invalid AI model output",
            details={"errors": [error.message for error in errors]},
        )

    expected_hash = sha256(source_text.encode("utf-8")).hexdigest()
    if document["sourceSha256"] != expected_hash:
        raise _invalid("source hash does not match the user intent")

    seen: set[str] = set()
    for proposal in document["proposals"]:
        field = proposal["field"]
        if field in seen:
            raise _invalid("duplicate proposed field", details={"field": field})
        seen.add(field)
        if field in document["unknownFields"]:
            raise _invalid(
                "a field cannot be both proposed and unknown", details={"field": field}
            )
        _validate_evidence(proposal, source_text)
        _validate_field_value(proposal)
    return document


def confirm_requirement_fields(
    draft: Mapping[str, Any], confirmed_fields: Iterable[str]
) -> dict[str, Any]:
    """Return only explicitly confirmed proposal values plus a confirmation ledger."""

    confirmed = set(confirmed_fields)
    proposals = {item["field"]: item for item in draft["proposals"]}
    unknown_confirmations = sorted(confirmed - proposals.keys())
    if unknown_confirmations:
        raise _invalid(
            "confirmation references a field absent from the draft",
            details={"fields": unknown_confirmations},
        )
    values = {field: proposals[field]["value"] for field in sorted(confirmed)}
    return {
        "schemaVersion": "1.0.0",
        "sourceSha256": draft["sourceSha256"],
        "confirmedValues": values,
        "confirmedFields": sorted(confirmed),
        "unconfirmedFields": sorted(proposals.keys() - confirmed),
    }


def build_ir_with_confirmed_proposals(
    draft: Mapping[str, Any],
    confirmed_fields: Iterable[str],
    form_answers: GuidedAnswers,
) -> dict[str, Any]:
    """Build IR from form answers plus only fields the user explicitly confirmed."""

    ledger = confirm_requirement_fields(draft, confirmed_fields)
    updates = {
        FIELD_TO_ANSWER[field]: value
        for field, value in ledger["confirmedValues"].items()
    }
    answers = replace(form_answers, **updates)
    document = build_ir_draft(answers)
    if ledger["confirmedFields"]:
        document["provenance"].append(
            {
                "id": "PROV-GUIDED-AI-CONFIRM",
                "subjectId": document["designId"],
                "field": "/requirements",
                "source": "engineer_override",
                "sourceRef": f"intent:{ledger['sourceSha256']}",
                "actor": "guided-flow-user",
                "recordedAt": "2026-09-22T00:00:00Z",
                "rationale": "User explicitly confirmed selected AI-proposed fields.",
            }
        )
    validate_engineering_ir(document)
    return document


def _validate_evidence(proposal: Mapping[str, Any], source_text: str) -> None:
    span = proposal["evidenceSpan"]
    start, end, quote = span["start"], span["end"], span["quote"]
    if end <= start or end > len(source_text) or source_text[start:end] != quote:
        raise _invalid(
            "evidence span does not exactly match the user intent",
            details={"field": proposal["field"]},
        )

    if proposal["field"] in NUMERIC_FIELDS:
        rendered = _render_number(proposal["value"])
        if rendered not in quote:
            raise _invalid(
                "numeric proposal is not present in its evidence span",
                details={"field": proposal["field"]},
            )
        if proposal["field"] in DIMENSION_FIELDS:
            if proposal["unit"] != "mm" or "mm" not in quote.lower():
                raise _invalid(
                    "dimension proposal lacks an explicit mm unit in evidence",
                    details={"field": proposal["field"]},
                )


def _validate_field_value(proposal: Mapping[str, Any]) -> None:
    field, value, unit = proposal["field"], proposal["value"], proposal["unit"]
    if field in NUMERIC_FIELDS and (not isinstance(value, (int, float)) or isinstance(value, bool)):
        raise _invalid("numeric field has a non-numeric value", details={"field": field})
    if field in DIMENSION_FIELDS and unit != "mm":
        raise _invalid("dimension field must use mm", details={"field": field})
    if field == "pcb_count" and (not isinstance(value, int) or unit is not None):
        raise _invalid("pcb_count must be a unitless integer")
    if field not in NUMERIC_FIELDS and unit is not None:
        raise _invalid("non-numeric field must not declare a unit", details={"field": field})
    if field not in NUMERIC_FIELDS and not isinstance(value, str):
        raise _invalid("text field has a non-string value", details={"field": field})


def _render_number(value: int | float) -> str:
    if isinstance(value, int) or float(value).is_integer():
        return str(int(value))
    return format(float(value), "g")


def _invalid(message: str, *, details: dict[str, Any] | None = None) -> MegisError:
    return MegisError(
        "MEGIS-AI-002",
        engineer_detail={"reason": message, **(details or {}), "accepted": False},
    )


__all__ = [
    "build_ir_with_confirmed_proposals",
    "confirm_requirement_fields",
    "parse_requirement_draft",
]
