"""CadQuery implementation of the kernel-neutral geometry backend contract."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import importlib.metadata
import json

import cadquery as cq

from megis.geometry import (
    BoundingBoxMm,
    FixtureAssemblyBuildResult,
    FixtureAssemblyPlan,
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
            supported_operations=frozenset(
                {
                    GeometryOperation.BOX,
                    GeometryOperation.PLATE,
                    GeometryOperation.SHELL,
                    GeometryOperation.HOLE,
                    GeometryOperation.CUTOUT,
                    GeometryOperation.COUNTERBORE,
                    GeometryOperation.FASTENER,
                    GeometryOperation.PCB_ENVELOPE,
                    GeometryOperation.MOUNT,
                }
            ),
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

    @staticmethod
    def _token(plan_id: str, role: str, dimensions: object) -> str:
        payload = json.dumps(
            {"planId": plan_id, "role": role, "dimensions": dimensions},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return f"cadquery:{sha256(payload).hexdigest()[:24]}"

    def _store(self, token: str, shape: cq.Shape) -> None:
        if shape.isNull() or not shape.isValid() or len(shape.Solids()) != 1:
            raise GeometryContractError(
                GeometryErrorCode.BACKEND_CONTRACT_VIOLATION,
                f"CadQuery produced an invalid {token} model",
            )
        self._models[token] = shape

    def build_fixture_assembly(
        self, plan: FixtureAssemblyPlan
    ) -> FixtureAssemblyBuildResult:
        spec = plan.specification
        inner_width = spec.outer_width_mm - 2 * spec.wall_mm
        inner_depth = spec.outer_depth_mm - 2 * spec.wall_mm
        cavity_height = spec.base_height_mm - spec.wall_mm

        outer = cq.Workplane("XY").box(
            spec.outer_width_mm,
            spec.outer_depth_mm,
            spec.base_height_mm,
            centered=(True, True, False),
        ).val()
        cavity = cq.Workplane("XY").box(
            inner_width,
            inner_depth,
            cavity_height,
            centered=(True, True, False),
        ).translate((0, 0, spec.wall_mm)).val()
        base_before_cutout = outer.cut(cavity)
        cutout = cq.Workplane("XY").box(
            spec.usb_cutout_width_mm,
            spec.wall_mm * 2,
            spec.usb_cutout_height_mm,
            centered=(True, True, False),
        ).translate(
            (
                0,
                -spec.outer_depth_mm / 2,
                spec.usb_cutout_bottom_z_mm,
            )
        ).val()
        cutout_touched_wall = base_before_cutout.intersect(cutout).Volume() > 0
        base = base_before_cutout.cut(cutout)
        usb_cutout_open = (
            cutout_touched_wall and base.intersect(cutout).Volume() <= 1e-7
        )

        cover = cq.Workplane("XY").box(
            spec.outer_width_mm,
            spec.outer_depth_mm,
            spec.cover_thickness_mm,
            centered=(True, True, False),
        ).translate((0, 0, spec.base_height_mm)).val()
        fastener_xy = (
            (
                x_sign * (spec.outer_width_mm / 2 - spec.fastener_edge_inset_mm),
                y_sign * (spec.outer_depth_mm / 2 - spec.fastener_edge_inset_mm),
            )
            for x_sign, y_sign in ((-1, -1), (-1, 1), (1, -1), (1, 1))
        )
        positions = tuple(fastener_xy)
        if len(positions) != spec.fastener_count:
            raise GeometryContractError(
                GeometryErrorCode.INVALID_DIMENSION,
                "Reference Fixture assembly requires four fasteners",
            )
        for x_pos, y_pos in positions:
            clearance_hole = (
                cq.Workplane("XY")
                .circle(spec.clearance_hole_diameter_mm / 2)
                .extrude(spec.cover_thickness_mm)
                .translate((x_pos, y_pos, spec.base_height_mm))
                .val()
            )
            counterbore = (
                cq.Workplane("XY")
                .circle(spec.counterbore_diameter_mm / 2)
                .extrude(spec.counterbore_depth_mm)
                .translate(
                    (
                        x_pos,
                        y_pos,
                        spec.base_height_mm
                        + spec.cover_thickness_mm
                        - spec.counterbore_depth_mm,
                    )
                )
                .val()
            )
            cover = cover.cut(clearance_hole).cut(counterbore)

        pcb = cq.Workplane("XY").box(
            spec.pcb_width_mm,
            spec.pcb_depth_mm,
            spec.pcb_thickness_mm,
            centered=(True, True, False),
        ).translate((0, 0, spec.pcb_bottom_z_mm)).val()
        fastener_shapes = tuple(
            cq.Workplane("XY")
            .circle(spec.fastener_diameter_mm / 2)
            .extrude(spec.cover_thickness_mm + 4.0)
            .translate((x_pos, y_pos, spec.base_height_mm - 4.0))
            .val()
            for x_pos, y_pos in positions
        )

        base_token = self._token(plan.plan_id, "base-shell-cutout", spec.__dict__)
        cover_token = self._token(plan.plan_id, "cover-counterbores", spec.__dict__)
        pcb_token = self._token(plan.plan_id, "pcb-envelope", spec.__dict__)
        fastener_tokens = tuple(
            self._token(plan.plan_id, f"fastener-{index}", position)
            for index, position in enumerate(positions, start=1)
        )
        self._store(base_token, base)
        self._store(cover_token, cover)
        self._store(pcb_token, pcb)
        for token, shape in zip(fastener_tokens, fastener_shapes, strict=True):
            self._store(token, shape)

        unintended_interference = sum(
            pair[0].intersect(pair[1]).Volume()
            for pair in ((base, cover), (base, pcb), (cover, pcb))
        )
        capability = self.capabilities()
        return FixtureAssemblyBuildResult(
            plan_id=plan.plan_id,
            component_ids=(
                spec.base_component_id,
                spec.cover_component_id,
                spec.pcb_component_id,
            ),
            backend_id=capability.backend_id,
            backend_version=capability.backend_version,
            base_model_token=base_token,
            cover_model_token=cover_token,
            pcb_envelope_model_token=pcb_token,
            fastener_model_tokens=fastener_tokens,
            solid_count=3 + len(fastener_shapes),
            valid=all(
                shape.isValid()
                for shape in (base, cover, pcb, *fastener_shapes)
            ),
            usb_cutout_open=usb_cutout_open,
            radial_fastener_clearance_mm=(
                spec.clearance_hole_diameter_mm - spec.fastener_diameter_mm
            )
            / 2,
            pcb_side_clearance_mm=min(
                (inner_width - spec.pcb_width_mm) / 2,
                (inner_depth - spec.pcb_depth_mm) / 2,
            ),
            pcb_top_clearance_mm=(
                spec.base_height_mm
                - spec.pcb_bottom_z_mm
                - spec.pcb_thickness_mm
            ),
            unintended_interference_volume_mm3=unintended_interference,
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
