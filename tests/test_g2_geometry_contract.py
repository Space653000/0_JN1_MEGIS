from copy import deepcopy
import inspect
import json
from pathlib import Path

import pytest

from megis.geometry import (
    BoundingBoxMm,
    GeometryBuildResult,
    GeometryCapabilities,
    GeometryContractError,
    GeometryErrorCode,
    GeometryOperation,
    build_fixture_base,
    plan_fixture_base,
)
from megis.geometry import contracts as geometry_contracts


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = json.loads(
    (ROOT / "contracts" / "g1" / "golden" / "reference-fixture.json").read_text(
        encoding="utf-8"
    )
)


class RecordingBackend:
    def __init__(self, operations: frozenset[GeometryOperation] | None = None) -> None:
        self.received = None
        self._operations = operations or frozenset({GeometryOperation.BOX})

    def capabilities(self) -> GeometryCapabilities:
        return GeometryCapabilities(
            backend_id="recording-backend",
            backend_version="1.0.0",
            supported_operations=self._operations,
            export_formats=frozenset(),
            deterministic=True,
        )

    def build(self, plan):
        self.received = plan
        box = plan.operations[0]
        return GeometryBuildResult(
            plan_id=plan.plan_id,
            component_ids=(box.component_id,),
            backend_id="recording-backend",
            backend_version="1.0.0",
            model_token="opaque:model:001",
            solid_count=1,
            bounding_box_mm=BoundingBoxMm(box.width_mm, box.depth_mm, box.height_mm),
            volume_mm3=box.width_mm * box.depth_mm * box.height_mm,
            valid=True,
        )


def test_golden_ir_drives_kernel_neutral_fixture_base_plan() -> None:
    plan = plan_fixture_base(GOLDEN)
    box = plan.operations[0]

    assert plan.design_id == "FIXTURE-REFERENCE-001"
    assert plan.coordinate_axes == ("width", "depth", "height")
    assert box.component_id == "COMP-FIXTURE-BASE"
    assert (box.width_mm, box.depth_mm, box.height_mm) == (120.0, 80.0, 20.0)


def test_application_service_consumes_plan_through_replaceable_backend() -> None:
    backend = RecordingBackend()

    result = build_fixture_base(GOLDEN, backend)

    assert backend.received is not None
    assert result.model_token == "opaque:model:001"
    assert result.volume_mm3 == 192000.0


def test_unsupported_backend_capability_is_rejected_before_build() -> None:
    backend = RecordingBackend(frozenset({GeometryOperation.HOLE}))

    with pytest.raises(GeometryContractError) as caught:
        build_fixture_base(GOLDEN, backend)

    assert caught.value.code == GeometryErrorCode.UNSUPPORTED_OPERATION
    assert backend.received is None


def test_missing_nominal_dimension_is_rejected() -> None:
    document = deepcopy(GOLDEN)
    quantity = document["components"][0]["dimensions"][0]["quantity"]
    del quantity["nominal"]
    quantity.update(min=119.9, max=120.1)

    with pytest.raises(GeometryContractError) as caught:
        plan_fixture_base(document)

    assert caught.value.code == GeometryErrorCode.INVALID_DIMENSION


def test_invalid_ir_is_reported_at_geometry_boundary() -> None:
    document = deepcopy(GOLDEN)
    document["components"][0]["materialId"] = "MAT-MISSING"

    with pytest.raises(GeometryContractError) as caught:
        plan_fixture_base(document)

    assert caught.value.code == GeometryErrorCode.INVALID_IR


def test_geometry_contract_does_not_import_cad_kernel() -> None:
    source = inspect.getsource(geometry_contracts).lower()

    assert "cadquery" not in source
    assert "occ" not in source


def test_backend_contract_violation_is_rejected() -> None:
    class LyingBackend(RecordingBackend):
        def build(self, plan):
            result = super().build(plan)
            return GeometryBuildResult(
                **{**result.__dict__, "plan_id": "PLAN-WRONG"}
            )

    with pytest.raises(GeometryContractError) as caught:
        build_fixture_base(GOLDEN, LyingBackend())

    assert caught.value.code == GeometryErrorCode.BACKEND_CONTRACT_VIOLATION
