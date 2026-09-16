import hashlib
import json
from pathlib import Path

import pytest

from megis.contracts import (
    deserialize_engineering_ir,
    load_engineering_ir,
    serialize_engineering_ir,
    summarize_engineering_ir,
    validate_engineering_ir,
)


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "contracts" / "g1" / "golden"
GOLDEN_CASES = (
    "reference-fixture.json",
    "acoustic-schema-only.json",
    "robot-schema-only.json",
)


@pytest.mark.parametrize("filename", GOLDEN_CASES)
def test_golden_case_validates(filename: str) -> None:
    document = load_engineering_ir(GOLDEN / filename)
    validate_engineering_ir(document)


def test_reference_fixture_round_trip_is_lossless_and_stable() -> None:
    document = load_engineering_ir(GOLDEN / "reference-fixture.json")
    first = serialize_engineering_ir(document)
    restored = deserialize_engineering_ir(first)
    second = serialize_engineering_ir(restored)

    assert restored == document
    assert second == first
    assert hashlib.sha256(second.encode("utf-8")).hexdigest() == hashlib.sha256(
        first.encode("utf-8")
    ).hexdigest()


def test_downstream_consumer_reads_reference_fixture_ir() -> None:
    summary = summarize_engineering_ir(load_engineering_ir(GOLDEN / "reference-fixture.json"))

    assert summary.design_id == "FIXTURE-REFERENCE-001"
    assert summary.maturity == "PROTOTYPE"
    assert summary.component_count == 3
    assert summary.domains == ("fixture",)
    assert summary.relationship_count == 2
    assert summary.unsafe_unknown_ids == ("UNK-FIXTURE-LOAD",)


@pytest.mark.parametrize("filename", ("acoustic-schema-only.json", "robot-schema-only.json"))
def test_schema_only_cases_remain_concept_with_unsafe_unknowns(filename: str) -> None:
    summary = summarize_engineering_ir(load_engineering_ir(GOLDEN / filename))

    assert summary.maturity == "CONCEPT"
    assert summary.unsafe_unknown_ids


def test_reference_fixture_expectations_match_consumed_ir() -> None:
    document = load_engineering_ir(GOLDEN / "reference-fixture.json")
    expectations = json.loads(
        (GOLDEN / "reference-fixture-expectations.json").read_text(encoding="utf-8")
    )

    assert expectations["designId"] == document["designId"]
    assert expectations["expectedGraph"]["componentIds"] == sorted(
        component["id"] for component in document["components"]
    )
    assert expectations["expectedGraph"]["relationshipIds"] == sorted(
        relationship["id"] for relationship in document["relationships"]
    )
    assert expectations["expectedArtifactMetadata"]["artifactsGenerated"] is False
