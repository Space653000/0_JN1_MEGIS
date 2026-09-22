"""G6-AI-004: reject any explanation number not grounded in trusted sources."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from megis.errors import MegisError

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "v3" / "grounded-explanation.schema.json"
ALLOWED_SOURCE_TYPES = frozenset({"engineering_ir", "rule_result", "manifest"})
NUMBER_PATTERN = re.compile(r"(?<![A-Za-z0-9_.])-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?![A-Za-z0-9_.])")


def source_fingerprint(document: Mapping[str, Any]) -> str:
    """Return a stable digest for one trusted JSON source document."""
    encoded = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def ground_explanation(
    raw_output: str,
    sources: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate provider output and return it only when every number is grounded."""
    try:
        explanation = json.loads(raw_output)
    except (json.JSONDecodeError, TypeError) as exc:
        raise _invalid("provider explanation is not valid JSON") from exc
    if not isinstance(explanation, dict):
        raise _invalid("provider explanation must be a JSON object")

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(explanation),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise _invalid("schema-invalid grounded explanation", {"errors": [e.message for e in errors]})

    trusted = _validate_sources(sources)
    claimed = explanation["sourceFingerprints"]
    if set(claimed) != set(trusted):
        raise _invalid("source fingerprint set does not match trusted sources")
    for source_id, source in trusted.items():
        if claimed[source_id] != source["fingerprint"]:
            raise _invalid("source fingerprint mismatch", {"sourceId": source_id})

    grounded = 0
    total = 0
    for index, paragraph in enumerate(explanation["paragraphs"]):
        tokens = NUMBER_PATTERN.findall(paragraph["text"])
        citations = paragraph["numericCitations"]
        cited_tokens = [item["token"] for item in citations]
        if Counter(tokens) != Counter(cited_tokens):
            raise _invalid(
                "every numeric occurrence requires exactly one citation",
                {"paragraph": index, "numbers": tokens, "citations": cited_tokens},
            )
        for citation in citations:
            source_id = citation["sourceId"]
            if source_id not in trusted:
                raise _invalid("citation references an untrusted source", {"sourceId": source_id})
            value = _resolve_pointer(trusted[source_id]["document"], citation["jsonPointer"])
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise _invalid("citation does not resolve to a numeric source value")
            if float(citation["token"]) != float(value):
                raise _invalid(
                    "explanation number does not match its cited source value",
                    {"token": citation["token"], "sourceValue": value},
                )
            grounded += 1
        total += len(tokens)

    return {
        **explanation,
        "grounding": {
            "groundedNumbers": grounded,
            "totalNumbers": total,
            "rate": 1.0,
            "verifiedSourceTypes": sorted({source["sourceType"] for source in trusted.values()}),
        },
    }


def _validate_sources(sources: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    if not sources:
        raise _invalid("at least one trusted source is required")
    trusted: dict[str, dict[str, Any]] = {}
    for source_id, source in sources.items():
        source_type = source.get("sourceType")
        document = source.get("document")
        if source_type not in ALLOWED_SOURCE_TYPES or not isinstance(document, dict):
            raise _invalid("source must be an Engineering IR, rule result, or manifest")
        trusted[source_id] = {
            "sourceType": source_type,
            "document": document,
            "fingerprint": source_fingerprint(document),
        }
    return trusted


def _resolve_pointer(document: Any, pointer: str) -> Any:
    current = document
    try:
        for raw in pointer.split("/")[1:]:
            token = raw.replace("~1", "/").replace("~0", "~")
            current = current[int(token)] if isinstance(current, list) else current[token]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise _invalid("citation JSON Pointer does not resolve", {"jsonPointer": pointer}) from exc
    return current


def _invalid(reason: str, details: dict[str, Any] | None = None) -> MegisError:
    return MegisError(
        "MEGIS-AI-002",
        engineer_detail={"reason": reason, "accepted": False, **(details or {})},
    )


__all__ = ["ALLOWED_SOURCE_TYPES", "ground_explanation", "source_fingerprint"]
