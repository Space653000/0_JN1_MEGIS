"""CadQuery implementation of the kernel-neutral geometry backend contract."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import importlib.metadata
import json

import cadquery as cq

from megis.geometry import (
    BoundingBoxMm,
    GeometryBuildResult,
    GeometryCapabilities,
    GeometryContractError,
    GeometryErrorCode,
    GeometryOperation,
    GeometryPlan,
)


@dataclass(frozen=True)
class TopologyInspection:
    valid: bool
    solids: int
    shells: int
    faces: int
    edges: int
    vertices: int


class CadQueryBackend:
    """Own CadQuery shapes internally and expose only contract metadata and tokens."""

    def __init__(self) -> None:
        self._models: dict[str, cq.Shape] = {}

    def capabilities(self) -> GeometryCapabilities:
        return GeometryCapabilities(
            backend_id="cadquery",
            backend_version=importlib.metadata.version("cadquery"),
            supported_operations=frozenset({GeometryOperation.BOX}),
            export_formats=frozenset({"STEP", "STL"}),
            deterministic=True,
        )

    def build(self, plan: GeometryPlan) -> GeometryBuildResult:
        if len(plan.operations) != 1:
            raise GeometryContractError(
                GeometryErrorCode.UNSUPPORTED_OPERATION,
                "CadQuery fixture-base slice requires exactly one box operation",
            )
        operation = plan.operations[0]
        shape = cq.Workplane("XY").box(
            operation.width_mm,
            operation.depth_mm,
            operation.height_mm,
            centered=(True, True, False),
        ).val()
        if not isinstance(shape, cq.Shape) or shape.isNull() or not shape.isValid():
            raise GeometryContractError(
                GeometryErrorCode.BACKEND_CONTRACT_VIOLATION,
                "CadQuery did not produce one valid shape",
            )
        plan_payload = json.dumps(
            {
                "planId": plan.plan_id,
                "componentId": operation.component_id,
                "dimensionsMm": [operation.width_mm, operation.depth_mm, operation.height_mm],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        token = f"cadquery:{sha256(plan_payload).hexdigest()[:24]}"
        self._models[token] = shape
        box = shape.BoundingBox()
        capability = self.capabilities()
        return GeometryBuildResult(
            plan_id=plan.plan_id,
            component_ids=(operation.component_id,),
            backend_id=capability.backend_id,
            backend_version=capability.backend_version,
            model_token=token,
            solid_count=len(shape.Solids()),
            bounding_box_mm=BoundingBoxMm(box.xlen, box.ylen, box.zlen),
            volume_mm3=shape.Volume(),
            valid=shape.isValid(),
        )

    def inspect_topology(self, model_token: str) -> TopologyInspection:
        try:
            shape = self._models[model_token]
        except KeyError as error:
            raise GeometryContractError(
                GeometryErrorCode.BACKEND_CONTRACT_VIOLATION,
                f"Unknown model token {model_token}",
            ) from error
        return TopologyInspection(
            valid=shape.isValid(),
            solids=len(shape.Solids()),
            shells=len(shape.Shells()),
            faces=len(shape.Faces()),
            edges=len(shape.Edges()),
            vertices=len(shape.Vertices()),
        )
