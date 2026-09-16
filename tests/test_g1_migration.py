from copy import deepcopy
import json
from pathlib import Path

import pytest

from megis.contracts import (
    MigrationError,
    canonical_hash,
    migrate_engineering_ir,
    rollback_engineering_ir,
    validate_engineering_ir,
)


ROOT = Path(__file__).resolve().parents[1]
LEGACY_PATH = ROOT / "contracts" / "g1" / "migrations" / "reference-fixture-v1.json"
CURRENT_PATH = ROOT / "contracts" / "g1" / "golden" / "reference-fixture.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v1_fixture_migrates_to_exact_current_golden_ir() -> None:
    result = migrate_engineering_ir(load(LEGACY_PATH))

    validate_engineering_ir(result.document)
    assert result.document == load(CURRENT_PATH)
    assert result.receipt.source_version == "1.0.0"
    assert result.receipt.target_version == "2.0.0"


def test_migration_is_deterministic() -> None:
    first = migrate_engineering_ir(load(LEGACY_PATH))
    second = migrate_engineering_ir(load(LEGACY_PATH))

    assert canonical_hash(first.document) == canonical_hash(second.document)
    assert first.receipt == second.receipt


def test_rollback_restores_exact_v1_fixture() -> None:
    source = load(LEGACY_PATH)

    assert rollback_engineering_ir(migrate_engineering_ir(source)) == source


def test_rollback_rejects_tampered_migrated_document() -> None:
    result = migrate_engineering_ir(load(LEGACY_PATH))
    result.document["revision"] = "B"

    with pytest.raises(MigrationError, match="changed after receipt"):
        rollback_engineering_ir(result)


@pytest.mark.parametrize("version", ("0.9.0", "2.0.0", "3.0.0", None))
def test_unknown_or_directionless_version_is_rejected(version: str | None) -> None:
    source = deepcopy(load(LEGACY_PATH))
    source["schemaVersion"] = version

    with pytest.raises(MigrationError, match="No explicit migration path"):
        migrate_engineering_ir(source)
