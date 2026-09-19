from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from megis.envelope import (
    ENVELOPE_PATH,
    ENVELOPE_SCHEMA_PATH,
    check_within_envelope,
    load_envelope,
)
from megis.errors import MegisError


ROOT = Path(__file__).resolve().parents[1]


def test_envelope_loads_and_matches_schema() -> None:
    envelope = load_envelope()
    assert envelope.verified is True
    assert envelope.materials == ("AL6061",)
    assert envelope.machining == ("3-axis CNC",)
    assert (envelope.cover_count, envelope.fastener_count) == (1, 4)
    assert envelope.minimum_wall_mm == 2.0
    assert tuple(envelope.unsupported_error_codes) == ("MEGIS-ENV-001",)
    assert envelope.v3_target_verified is False


def test_machine_envelope_matches_human_doc() -> None:
    human = (ROOT / "docs" / "SUPPORTED_ENVELOPE.md").read_text(encoding="utf-8")
    envelope = load_envelope()

    assert "120 × 80 × 20 mm" in human
    assert envelope.outer_dimensions_mm.width_mm == 120.0
    assert envelope.outer_dimensions_mm.depth_mm == 80.0
    assert envelope.outer_dimensions_mm.height_mm == 20.0
    assert "2 mm" in human and envelope.minimum_wall_mm == 2.0
    assert "AL6061" in human and "3-axis CNC" in human
    assert "四 fastener" in human and envelope.fastener_count == 4
    assert "USB-C" in human

    assert "120 × 80 × 35 mm" in human
    assert envelope.v3_target_verified is False


def test_exact_boundary_is_within_envelope() -> None:
    envelope = load_envelope()
    check_within_envelope(120.0, 80.0, 20.0, envelope=envelope)  # must not raise


def test_over_envelope_raises_megis_env_001() -> None:
    envelope = load_envelope()
    with pytest.raises(MegisError) as exc_info:
        check_within_envelope(121.0, 80.0, 20.0, envelope=envelope)
    assert exc_info.value.code.code == "MEGIS-ENV-001"


def test_each_axis_escape_is_rejected() -> None:
    envelope = load_envelope()
    cases = [(120.0, 81.0, 20.0), (120.0, 80.0, 20.1), (120.0, 80.0, 30.0)]
    for case in cases:
        with pytest.raises(MegisError):
            check_within_envelope(*case, envelope=envelope)


def test_invalid_envelope_is_rejected(tmp_path: Path) -> None:
    broken = {
        "schemaVersion": "1.0.0",
        "envelope_id": "broken",
        "label": "broken",
        "verified": True,
        "unsupported_behaviour": {"silent_clamp": True},
    }
    path = tmp_path / "broken.yaml"
    path.write_text(yaml.safe_dump(broken, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ValueError):
        load_envelope(path)


def test_envelope_files_exist_and_are_consumed_by_loader() -> None:
    assert ENVELOPE_PATH.is_file()
    assert ENVELOPE_SCHEMA_PATH.is_file()
    # parser round trip proves the machine file is structurally loadable
    raw = yaml.safe_load(ENVELOPE_PATH.read_text(encoding="utf-8"))
    assert raw["schemaVersion"] == "1.0.0"
