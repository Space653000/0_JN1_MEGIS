import json
from pathlib import Path

import pytest

from megis.adapters import CadQueryBackend
from megis.geometry import GeometryContractError, build_fixture_base


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = json.loads(
    (ROOT / "contracts" / "g1" / "golden" / "reference-fixture.json").read_text(
        encoding="utf-8"
    )
)


def test_cadquery_builds_valid_fixture_base_from_golden_ir() -> None:
    backend = CadQueryBackend()

    result = build_fixture_base(GOLDEN, backend)
    topology = backend.inspect_topology(result.model_token)

    assert result.valid is True
    assert result.solid_count == 1
    assert result.bounding_box_mm.width == pytest.approx(120.0)
    assert result.bounding_box_mm.depth == pytest.approx(80.0)
    assert result.bounding_box_mm.height == pytest.approx(20.0)
    assert result.volume_mm3 == pytest.approx(192000.0)
    assert topology.valid is True
    assert topology.solids == 1
    assert topology.shells == 1
    assert topology.faces == 6
    assert topology.edges == 12
    assert topology.vertices == 8


def test_same_ir_produces_same_model_token_and_metrics() -> None:
    first = build_fixture_base(GOLDEN, CadQueryBackend())
    second = build_fixture_base(GOLDEN, CadQueryBackend())

    assert first == second


def test_unknown_model_token_is_rejected() -> None:
    with pytest.raises(GeometryContractError, match="Unknown model token"):
        CadQueryBackend().inspect_topology("cadquery:missing")


def test_adapter_capability_identity_is_locked() -> None:
    capability = CadQueryBackend().capabilities()

    assert capability.backend_id == "cadquery"
    assert capability.backend_version == "2.8.0"
    assert capability.deterministic is True
