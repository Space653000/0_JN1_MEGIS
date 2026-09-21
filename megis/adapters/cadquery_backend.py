"""CadQuery implementation of the kernel-neutral geometry backend contract."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import importlib.metadata
import json
from math import isfinite
from pathlib import Path
import struct

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
    GeometryExportResult,
    GeometryReloadResult,
    TopologyMetrics,
)

from megis.adapters.gltf import reload_gltf
from megis.determinism.normalization import (
    dxf_vector_semantic_fingerprint,
    normalize_dxf_file,
    normalize_step_file,
    normalize_stl_file,
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
            export_formats=frozenset({"STEP", "STL", "DXF"}),
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

    def export_model(
        self, model_token: str, output_path: str | Path, export_format: str
    ) -> GeometryExportResult:
        try:
            shape = self._models[model_token]
        except KeyError as error:
            raise GeometryContractError(
                GeometryErrorCode.BACKEND_CONTRACT_VIOLATION,
                f"Unknown model token {model_token}",
            ) from error
        normalized_format = export_format.upper()
        if normalized_format not in self.capabilities().export_formats:
            raise GeometryContractError(
                GeometryErrorCode.UNSUPPORTED_OPERATION,
                f"Unsupported export format {export_format!r}",
            )
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        export_type = {
            "STEP": cq.exporters.ExportTypes.STEP,
            "STL": cq.exporters.ExportTypes.STL,
            "DXF": cq.exporters.ExportTypes.DXF,
        }[normalized_format]
        cq.exporters.export(shape, str(target), exportType=export_type)
        if not target.is_file() or target.stat().st_size == 0:
            raise GeometryContractError(
                GeometryErrorCode.BACKEND_CONTRACT_VIOLATION,
                f"Export for {normalized_format} produced an empty artifact",
            )
        payload = target.read_bytes()
        bounds = shape.BoundingBox()
        return GeometryExportResult(
            export_format=normalized_format,
            output_path=str(target),
            byte_count=len(payload),
            sha256=sha256(payload).hexdigest(),
            volume_mm3=shape.Volume(),
            topology=self._topology(shape),
            metrics={
                "widthMm": bounds.xlen,
                "depthMm": bounds.ylen,
                "heightMm": bounds.zlen,
            },
        )

    def reload_model(
        self, input_path: str | Path, import_format: str
    ) -> GeometryReloadResult:
        source = Path(input_path)
        normalized_format = import_format.upper()
        if not source.is_file():
            raise GeometryContractError(
                GeometryErrorCode.BACKEND_CONTRACT_VIOLATION,
                f"Reload input does not exist: {source}",
            )
        reloaders = {
            "STEP": self._reload_step,
            "STL": self._reload_stl,
            "DXF": self._reload_dxf,
            "GLTF": self._reload_gltf,
        }
        try:
            reloader = reloaders[normalized_format]
        except KeyError as error:
            raise GeometryContractError(
                GeometryErrorCode.UNSUPPORTED_OPERATION,
                f"Unsupported reload format {import_format!r}",
            ) from error
        return reloader(source)

    def _topology(self, shape: object) -> TopologyMetrics:
        return TopologyMetrics(
            valid=shape.isValid(),
            solids=len(shape.Solids()),
            shells=len(shape.Shells()),
            faces=len(shape.Faces()),
            edges=len(shape.Edges()),
            vertices=len(shape.Vertices()),
        )

    def _reload_step(self, source: Path) -> GeometryReloadResult:
        try:
            shape = cq.importers.importStep(str(source)).val()
        except Exception as error:
            raise GeometryContractError(
                GeometryErrorCode.BACKEND_CONTRACT_VIOLATION,
                "STEP reload failed",
            ) from error
        if shape.isNull() or not shape.isValid():
            raise GeometryContractError(
                GeometryErrorCode.BACKEND_CONTRACT_VIOLATION,
                "STEP reload produced a null or invalid shape",
            )
        volume = shape.Volume()
        if not isfinite(volume) or volume <= 0:
            raise GeometryContractError(
                GeometryErrorCode.BACKEND_CONTRACT_VIOLATION,
                "STEP reload produced zero or invalid volume",
            )
        bounds = shape.BoundingBox()
        normalized = normalize_step_file(source)
        return GeometryReloadResult(
            import_format="STEP",
            input_path=str(source),
            valid=True,
            solids=len(shape.Solids()),
            volume_mm3=volume,
            bounding_box_mm=BoundingBoxMm(bounds.xlen, bounds.ylen, bounds.zlen),
            topology=self._topology(shape),
            metrics={"normalization": normalized},
        )

    def _reload_stl(self, source: Path) -> GeometryReloadResult:
        payload = source.read_bytes()
        if len(payload) < 84:
            raise GeometryContractError(
                GeometryErrorCode.BACKEND_CONTRACT_VIOLATION,
                "STL reload input is truncated",
            )
        triangle_count = struct.unpack_from("<I", payload, 80)[0]
        expected_bytes = 84 + triangle_count * 50
        if len(payload) != expected_bytes:
            raise GeometryContractError(
                GeometryErrorCode.BACKEND_CONTRACT_VIOLATION,
                "STL reload input is not a structurally valid binary STL",
            )
        if triangle_count == 0:
            raise GeometryContractError(
                GeometryErrorCode.BACKEND_CONTRACT_VIOLATION,
                "STL reload input contains no triangles",
            )
        vertices: set[tuple[float, float, float]] = set()
        min_values = [float("inf"), float("inf"), float("inf")]
        max_values = [float("-inf"), float("-inf"), float("-inf")]
        signed_volume = 0.0
        for triangle_index in range(triangle_count):
            base_offset = 84 + triangle_index * 50
            values = struct.unpack_from("<12fH", payload, base_offset)
            triangle = [
                (
                    values[vertex_offset],
                    values[vertex_offset + 1],
                    values[vertex_offset + 2],
                )
                for vertex_offset in (3, 6, 9)
            ]
            for vertex in triangle:
                vertices.add(vertex)
                for axis in range(3):
                    min_values[axis] = min(min_values[axis], vertex[axis])
                    max_values[axis] = max(max_values[axis], vertex[axis])
            first, second, third = triangle
            signed_volume += (
                first[0] * (second[1] * third[2] - second[2] * third[1])
                + second[0] * (third[1] * first[2] - third[2] * first[1])
                + third[0] * (first[1] * second[2] - first[2] * second[1])
            ) / 6.0
        normalized = normalize_stl_file(source)
        return GeometryReloadResult(
            import_format="STL",
            input_path=str(source),
            valid=True,
            solids=1,
            volume_mm3=abs(signed_volume),
            bounding_box_mm=BoundingBoxMm(
                max_values[0] - min_values[0],
                max_values[1] - min_values[1],
                max_values[2] - min_values[2],
            ),
            topology=TopologyMetrics(
                valid=True,
                solids=1,
                shells=0,
                faces=triangle_count,
                edges=0,
                vertices=len(vertices),
            ),
            metrics={
                "triangleCount": triangle_count,
                "vertexCount": len(vertices),
                "normalization": normalized,
            },
        )

    def _reload_dxf(self, source: Path) -> GeometryReloadResult:
        normalized = normalize_dxf_file(source)
        fingerprint = dxf_vector_semantic_fingerprint(source)
        edge_count = int(fingerprint["canonical"]["edge_count"])
        if edge_count == 0:
            raise GeometryContractError(
                GeometryErrorCode.BACKEND_CONTRACT_VIOLATION,
                "DXF reload input contains no vector entities",
            )
        return GeometryReloadResult(
            import_format="DXF",
            input_path=str(source),
            valid=True,
            solids=0,
            volume_mm3=None,
            bounding_box_mm=None,
            topology=TopologyMetrics(
                valid=True,
                solids=0,
                shells=0,
                faces=0,
                edges=edge_count,
                vertices=0,
            ),
            metrics={
                "edgeCount": edge_count,
                "semanticFingerprint": fingerprint["semanticFingerprint"],
                "normalization": normalized,
            },
        )

    def _reload_gltf(self, source: Path) -> GeometryReloadResult:
        try:
            reloaded = reload_gltf(source)
        except Exception as error:
            raise GeometryContractError(
                GeometryErrorCode.BACKEND_CONTRACT_VIOLATION,
                "glTF reload failed",
            ) from error
        bbox = reloaded["boundingBoxMm"]
        return GeometryReloadResult(
            import_format="GLTF",
            input_path=str(source),
            valid=bool(reloaded["valid"]),
            solids=0,
            volume_mm3=None,
            bounding_box_mm=BoundingBoxMm(bbox[0], bbox[1], bbox[2]),
            topology=TopologyMetrics(
                valid=True,
                solids=0,
                shells=0,
                faces=int(reloaded["triangleCount"]),
                edges=0,
                vertices=int(reloaded["vertexCount"]),
            ),
            metrics={
                "vertexCount": reloaded["vertexCount"],
                "triangleCount": reloaded["triangleCount"],
                "indexCount": reloaded["indexCount"],
                "indexComponentType": reloaded["indexComponentType"],
                "assetVersion": reloaded["assetVersion"],
                "sha256": reloaded["sha256"],
            },
        )
