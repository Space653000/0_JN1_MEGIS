from __future__ import annotations

import json
from pathlib import Path
import re

from jsonschema import Draft202012Validator
import pytest

from megis.errors import (
    ERROR_CODES,
    ERROR_SCHEMA_PATH,
    LEGACY_GEO_MAPPING,
    ErrorDomain,
    MegisError,
    validate_error_object,
    verify_error_codes,
)
from megis.geometry import GeometryErrorCode


ROOT = Path(__file__).resolve().parents[1]


def _load_schema() -> dict:
    return json.loads(ERROR_SCHEMA_PATH.read_text(encoding="utf-8"))


def _valid_object() -> dict:
    return {
        "code": "MEGIS-GEO-001",
        "severity": "error",
        "retryable": False,
        "user_message_zh_tw": "幾何輸入資料無效。",
        "engineer_detail": "invalid geometry IR input",
        "entity_refs": ["fixture.base.main"],
        "correlation_id": "run-0001",
    }


def test_error_code_registry_is_unique_and_format_conforms() -> None:
    codes = list(ERROR_CODES)
    assert len(codes) == len(set(codes))
    for code in codes:
        assert re.fullmatch(r"MEGIS-[A-Z]{2,4}-[0-9]{3}", code), code
        entry = ERROR_CODES[code]
        expected = f"MEGIS-{entry.domain.value}-{entry.number:03d}"
        assert code == expected, f"{code} does not match {expected}"
        assert entry.user_message_zh_tw
        assert entry.engineer_detail


def test_error_code_numbers_are_contiguous_per_domain() -> None:
    by_domain: dict[str, list[int]] = {}
    for entry in ERROR_CODES.values():
        by_domain.setdefault(entry.domain.value, []).append(entry.number)
    for domain, numbers in by_domain.items():
        assert numbers == list(range(1, len(numbers) + 1)), domain


def test_error_object_validates_against_v3_schema() -> None:
    validator = Draft202012Validator(_load_schema())
    assert list(validator.iter_errors(_valid_object())) == []
    boundary = dict(_valid_object(), entity_refs=[])
    assert list(validator.iter_errors(boundary)) == []


def test_error_object_rejects_missing_required_field() -> None:
    obj = dict(_valid_object())
    del obj["correlation_id"]
    with pytest.raises(ValueError):
        validate_error_object(obj)


def test_error_object_rejects_unknown_severity() -> None:
    obj = dict(_valid_object(), severity="exploded")
    validator = Draft202012Validator(_load_schema())
    assert list(validator.iter_errors(obj))


def test_megis_error_emits_schema_conformant_object() -> None:
    error = MegisError(
        "MEGIS-GEO-003",
        entity_refs=("fixture.base.main",),
        correlation_id="run-0002",
    )
    payload = error.error_object.to_dict()
    assert payload["code"] == "MEGIS-GEO-003"
    assert payload["severity"] == "error"
    assert list(Draft202012Validator(_load_schema()).iter_errors(payload)) == []
    assert str(error) == "MEGIS-GEO-003"


def test_legacy_geometry_mapping_covers_every_current_value() -> None:
    current = {code.value for code in GeometryErrorCode}
    assert set(LEGACY_GEO_MAPPING) == current
    for v3_code in LEGACY_GEO_MAPPING.values():
        assert v3_code in ERROR_CODES
        assert ERROR_CODES[v3_code].domain is ErrorDomain.GEO


def test_unknown_code_lookup_is_rejected() -> None:
    with pytest.raises(KeyError):
        MegisError("MEGIS-GEO-999")


def test_verify_error_codes_reports_no_issues() -> None:
    assert verify_error_codes() == []
