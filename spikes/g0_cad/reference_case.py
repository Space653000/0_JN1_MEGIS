"""Generate and verify the fixed G0 CadQuery Reference Case artifacts."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
from typing import Any

import cadquery as cq
from OCP.StlAPI import StlAPI_Reader
from OCP.TopoDS import TopoDS_Shape


@dataclass(frozen=True)
class ReferenceCaseSpec:
    length_mm: float = 120.0
    width_mm: float = 80.0
    height_mm: float = 35.0
    minimum_wall_mm: float = 2.0
    m3_clearance_diameter_mm: float = 3.4
    material: str = "Aluminum 6061"
    process: str = "3-axis CNC"
    section_height_mm: float = 10.0


SPEC = ReferenceCaseSpec()
ARTIFACT_NAMES = {
    "step": "reference_case.step",
    "stl": "reference_case.stl",
    "dxf": "reference_case_section_z10.dxf",
}


def build_reference_case(spec: ReferenceCaseSpec = SPEC) -> cq.Shape:
    """Build an open-top enclosure envelope with a 2 mm floor/wall and M3 holes."""

    outer = cq.Workplane("XY").box(
        spec.length_mm,
        spec.width_mm,
        spec.height_mm,
        centered=(True, True, False),
    )
    inner = (
        cq.Workplane("XY")
        .box(
            spec.length_mm - (2 * spec.minimum_wall_mm),
            spec.width_mm - (2 * spec.minimum_wall_mm),
            spec.height_mm,
            centered=(True, True, False),
        )
        .translate((0, 0, spec.minimum_wall_mm))
    )
    hole_centers = [(-50, -30), (-50, 30), (50, -30), (50, 30)]
    holes = (
        cq.Workplane("XY")
        .pushPoints(hole_centers)
        .circle(spec.m3_clearance_diameter_mm / 2)
        .extrude(spec.minimum_wall_mm + 2)
        .translate((0, 0, -1))
    )
    shape = outer.cut(inner).cut(holes).val()
    if not isinstance(shape, cq.Shape):
        raise TypeError("Reference Case did not produce a CadQuery shape")
    return shape


def bounding_box(shape: cq.Shape) -> dict[str, float]:
    box = shape.BoundingBox()
    return {"xlen": box.xlen, "ylen": box.ylen, "zlen": box.zlen}


def assert_dimensions(shape: cq.Shape, spec: ReferenceCaseSpec = SPEC, tolerance: float = 1e-6) -> None:
    dimensions = bounding_box(shape)
    expected = {"xlen": spec.length_mm, "ylen": spec.width_mm, "zlen": spec.height_mm}
    for axis, value in expected.items():
        if abs(dimensions[axis] - value) > tolerance:
            raise AssertionError(f"{axis} expected {value}, got {dimensions[axis]}")


def export_artifacts(output_dir: Path, spec: ReferenceCaseSpec = SPEC) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {kind: output_dir / name for kind, name in ARTIFACT_NAMES.items()}
    shape = build_reference_case(spec)
    section = cq.Workplane(obj=shape).section(height=spec.section_height_mm)

    cq.exporters.export(shape, str(paths["step"]), exportType="STEP")
    shape.exportStl(str(paths["stl"]), tolerance=0.01, angularTolerance=0.1, ascii=True)
    cq.exporters.exportDXF(section, str(paths["dxf"]), tolerance=0.001)
    return paths


def verify_step(path: Path, spec: ReferenceCaseSpec = SPEC) -> dict[str, Any]:
    imported = cq.importers.importStep(str(path))
    solids = imported.solids().vals()
    if len(solids) != 1 or not solids[0].isValid():
        raise AssertionError("STEP reload did not produce one valid solid")
    assert_dimensions(solids[0], spec)
    expected_volume = build_reference_case(spec).Volume()
    if abs(solids[0].Volume() - expected_volume) > 1e-6:
        raise AssertionError("STEP reload changed the Reference Case volume")
    return {
        "valid": True,
        "solids": 1,
        "volumeMm3": solids[0].Volume(),
        "boundingBoxMm": bounding_box(solids[0]),
    }


def verify_stl(path: Path, spec: ReferenceCaseSpec = SPEC) -> dict[str, Any]:
    occ_shape = TopoDS_Shape()
    if not StlAPI_Reader().Read(occ_shape, str(path)):
        raise AssertionError("OCP STL reader rejected the artifact")
    shape = cq.Shape.cast(occ_shape)
    if shape.isNull() or not shape.isValid():
        raise AssertionError("STL reload produced an invalid shape")
    assert_dimensions(shape, spec, tolerance=0.05)
    return {"valid": True, "faces": len(shape.Faces()), "boundingBoxMm": bounding_box(shape)}


def verify_dxf(path: Path, spec: ReferenceCaseSpec = SPEC) -> dict[str, Any]:
    imported = cq.importers.importDXF(str(path))
    edges = imported.edges().vals()
    wires = imported.wires().vals()
    if len(edges) != 8 or len(wires) != 2:
        raise AssertionError("DXF reload did not produce two four-edge closed wires")
    box = imported.val().BoundingBox()
    if abs(box.xlen - spec.length_mm) > 1e-6 or abs(box.ylen - spec.width_mm) > 1e-6:
        raise AssertionError(f"DXF section dimensions are {box.xlen} x {box.ylen}")
    wire_dimensions = sorted(
        ({"xlen": wire.BoundingBox().xlen, "ylen": wire.BoundingBox().ylen} for wire in wires),
        key=lambda dimensions: dimensions["xlen"],
        reverse=True,
    )
    expected_wires = [
        {"xlen": spec.length_mm, "ylen": spec.width_mm},
        {
            "xlen": spec.length_mm - (2 * spec.minimum_wall_mm),
            "ylen": spec.width_mm - (2 * spec.minimum_wall_mm),
        },
    ]
    if wire_dimensions != expected_wires:
        raise AssertionError(f"DXF section wires are {wire_dimensions}")
    return {
        "valid": True,
        "edges": len(edges),
        "wires": len(wires),
        "wireBoundingBoxesMm": wire_dimensions,
        "boundingBoxMm": {"xlen": box.xlen, "ylen": box.ylen, "zlen": box.zlen},
    }


def file_evidence(path: Path) -> dict[str, Any]:
    content = path.read_bytes()
    return {"path": path.name, "bytes": len(content), "sha256": sha256(content).hexdigest()}


def generate_and_verify(output_dir: Path) -> dict[str, Any]:
    paths = export_artifacts(output_dir)
    source_shape = build_reference_case()
    if not source_shape.isValid() or len(source_shape.Solids()) != 1:
        raise AssertionError("Source model is not one valid solid")
    assert_dimensions(source_shape)

    verification = {
        "step": verify_step(paths["step"]),
        "stl": verify_stl(paths["stl"]),
        "dxf": verify_dxf(paths["dxf"]),
    }
    manifest = {
        "schemaVersion": "1.0.0",
        "workItem": "G0-CAD-001",
        "classification": "FEASIBILITY_SPIKE",
        "maturity": "PROTOTYPE",
        "engineeringReviewRequired": True,
        "specification": asdict(SPEC),
        "toolchain": {
            "cadquery": importlib.metadata.version("cadquery"),
            "cadqueryOcp": importlib.metadata.version("cadquery-ocp"),
        },
        "source": {
            "valid": True,
            "solids": len(source_shape.Solids()),
            "volumeMm3": source_shape.Volume(),
            "boundingBoxMm": bounding_box(source_shape),
        },
        "verification": verification,
        "artifacts": {kind: file_evidence(path) for kind, path in paths.items()},
        "limitations": [
            "This spike proves export and reload feasibility only.",
            "It is not the G2 production geometry backend or a manufacturing release.",
            "Material and process are declared Reference Case metadata, not solver-verified properties.",
        ],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/g0-cad"))
    args = parser.parse_args()
    manifest = generate_and_verify(args.output_dir.resolve())
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
