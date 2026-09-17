from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import pytest

from megis.adapters import CadQueryBackend
from megis.geometry import (
    GeometryContractError,
    GeometryErrorCode,
    GeometryOperation,
    build_fixture_assembly,
    plan_fixture_assembly,
)


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = json.loads(
    (ROOT / "contracts" / "g1" / "golden" / "reference-fixture.json").read_text(
        encoding="utf-8"
    )
)


def test_plan_derives_fixture_envelope_and_relationship_components() -> None:
    plan = plan_fixture_assembly(GOLDEN)
    spec = plan.specification

    assert plan.coordinate_axes == ("width", "depth", "height")
    assert (spec.outer_width_mm, spec.outer_depth_mm, spec.base_height_mm) == (
        120.0,
        80.0,
        20.0,
    )
    assert spec.wall_mm == 2.0
    assert (
        spec.base_component_id,
        spec.cover_component_id,
        spec.pcb_component_id,
    ) == (
        "COMP-FIXTURE-BASE",
        "COMP-FIXTURE-COVER",
        "COMP-FIXTURE-PCB",
    )


def test_cadquery_builds_valid_cover_fasteners_cutout_and_clearances() -> None:
    backend = CadQueryBackend()

    result = build_fixture_assembly(GOLDEN, backend)

    assert result.valid is True
    assert result.solid_count == 7
    assert result.usb_cutout_open is True
    assert result.radial_fastener_clearance_mm == pytest.approx(0.2)
    assert result.pcb_side_clearance_mm == pytest.approx(18.0)
    assert result.pcb_top_clearance_mm == pytest.approx(12.4)
    assert result.unintended_interference_volume_mm3 == pytest.approx(0.0, abs=1e-7)
    assert len(result.fastener_model_tokens) == 4

    for token in (
        result.base_model_token,
        result.cover_model_token,
        result.pcb_envelope_model_token,
        *result.fastener_model_tokens,
    ):
        topology = backend.inspect_topology(token)
        assert topology.valid is True
        assert topology.solids == 1


def test_same_ir_produces_same_assembly_tokens_and_metrics() -> None:
    first = build_fixture_assembly(GOLDEN, CadQueryBackend())
    second = build_fixture_assembly(GOLDEN, CadQueryBackend())

    assert first == second


def test_assembly_capabilities_are_declared() -> None:
    operations = CadQueryBackend().capabilities().supported_operations

    assert {
        GeometryOperation.SHELL,
        GeometryOperation.PLATE,
        GeometryOperation.HOLE,
        GeometryOperation.CUTOUT,
        GeometryOperation.COUNTERBORE,
        GeometryOperation.FASTENER,
        GeometryOperation.PCB_ENVELOPE,
        GeometryOperation.MOUNT,
    } <= operations


def test_impossible_wall_is_rejected_without_clamping() -> None:
    document = deepcopy(GOLDEN)
    wall = document["constraints"][0]["measurement"]["quantity"]
    wall["min"] = 40.0
    wall["max"] = 41.0

    with pytest.raises(GeometryContractError) as caught:
        plan_fixture_assembly(document)

    assert caught.value.code == GeometryErrorCode.INVALID_DIMENSION
    assert "no positive fixture cavity" in str(caught.value)


def test_backend_interference_contract_violation_is_rejected() -> None:
    class InterferingBackend(CadQueryBackend):
        def build_fixture_assembly(self, plan):
            result = super().build_fixture_assembly(plan)
            return replace(result, unintended_interference_volume_mm3=1.0)

    with pytest.raises(GeometryContractError) as caught:
        build_fixture_assembly(GOLDEN, InterferingBackend())

    assert caught.value.code == GeometryErrorCode.BACKEND_CONTRACT_VIOLATION
