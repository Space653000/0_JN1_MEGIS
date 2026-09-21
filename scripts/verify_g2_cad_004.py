"""Verify G2-CAD-004 export and reload pipeline with cross-checked evidence.

Exports the Reference Fixture assembly components to STEP, STL, and DXF,
reloads each artifact through the CadQuery backend, and cross-checks the
mesh/reload geometry against kernel-derived metrics. A stdlib-only glTF
bridge translates the binary STL into a reloadable glTF 2.0 document.

All engineering artifacts are written under artifacts/g2-cad-004/ and are
git-ignored; only verification.json is committed.
"""

from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.adapters import CadQueryBackend  # noqa: E402
from megis.adapters.gltf import write_gltf_from_stl  # noqa: E402
from megis.contracts import load_engineering_ir  # noqa: E402
from megis.determinism.normalization import (  # noqa: E402
    dxf_vector_semantic_fingerprint,
    normalize_dxf_file,
    normalize_step_file,
    normalize_stl_file,
)
from megis.geometry import build_fixture_assembly  # noqa: E402


class Evidence:
    """Collect check results and keep the record machine-readable."""

    def __init__(self) -> None:
        self.checks: list[dict] = []
        self.failed = False

    def expect(self, name: str, condition: bool, detail: object) -> None:
        if not condition:
            self.failed = True
        self.checks.append(
            {
                "name": name,
                "passed": bool(condition),
                "detail": detail,
            }
        )


def bbox_tuple(value: object | None) -> list[float] | None:
    if value is None:
        return None
    return [value.width, value.depth, value.height]


def bbox_close(value: object, reference: list[float], tolerance: float) -> bool:
    dimensions = [value.width, value.depth, value.height]
    return all(
        abs(dimension - reference[index]) <= tolerance
        for index, dimension in enumerate(dimensions)
    )


def verify() -> dict:
    document = load_engineering_ir(ROOT / "contracts/g1/golden/reference-fixture.json")
    backend = CadQueryBackend()
    capabilities = backend.capabilities()
    assembly = build_fixture_assembly(document, backend)
    out_dir = ROOT / "artifacts" / "g2-cad-004"
    out_dir.mkdir(parents=True, exist_ok=True)

    components = {
        "base": assembly.base_model_token,
        "cover": assembly.cover_model_token,
        "pcb": assembly.pcb_envelope_model_token,
    }
    evidence = Evidence()
    component_evidence: dict[str, dict] = {}

    for name, token in components.items():
        step_path = out_dir / f"{name}.step"
        stl_path = out_dir / f"{name}.stl"
        dxf_path = out_dir / f"{name}.dxf"

        step_export = backend.export_model(token, step_path, "STEP")
        step_reload = backend.reload_model(step_path, "STEP")
        backend.reload_model(step_path, "STEP")
        step_normalized_twice = normalize_step_file(step_path)

        stl_export = backend.export_model(token, stl_path, "STL")
        stl_reload = backend.reload_model(stl_path, "STL")
        stl_normalized_twice = normalize_stl_file(stl_path)

        dxf_export = backend.export_model(token, dxf_path, "DXF")
        dxf_reload = backend.reload_model(dxf_path, "DXF")
        dxf_normalized_twice = normalize_dxf_file(dxf_path)
        dxf_fingerprint = dxf_vector_semantic_fingerprint(dxf_path)

        expected_volume = step_reload.volume_mm3 or 0.0
        volume_tolerance = max(1.0, expected_volume * 0.001)
        step_volume_delta = abs((step_export.volume_mm3 or 0.0) - expected_volume)
        stl_volume_delta = abs((stl_reload.volume_mm3 or 0.0) - expected_volume)

        evidence.expect(
            f"{name} STEP reloads twice with non-empty geometry",
            step_reload.valid
            and step_reload.solids >= 1
            and bool(step_reload.volume_mm3 and step_reload.volume_mm3 > 0),
            asdict(step_reload),
        )
        evidence.expect(
            f"{name} STEP reload equals export volume",
            step_volume_delta <= 1e-6,
            {
                "exportVolumeMm3": step_export.volume_mm3,
                "reloadVolumeMm3": step_reload.volume_mm3,
            },
        )
        evidence.expect(
            f"{name} STEP normalization is idempotent",
            step_normalized_twice["changed"] is False,
            {"changed": step_normalized_twice["changed"]},
        )
        evidence.expect(
            f"{name} STL reload has triangles and bbox",
            stl_reload.valid
            and stl_reload.topology.faces > 0
            and stl_reload.bounding_box_mm is not None,
            asdict(stl_reload),
        )
        evidence.expect(
            f"{name} STL mesh volume within tolerance",
            stl_volume_delta <= volume_tolerance,
            {
                "meshVolumeMm3": stl_reload.volume_mm3,
                "stepVolumeMm3": expected_volume,
                "toleranceMm3": volume_tolerance,
                "deltaMm3": stl_volume_delta,
            },
        )
        evidence.expect(
            f"{name} STL normalization is idempotent",
            stl_normalized_twice["changed"] is False,
            {"changed": stl_normalized_twice["changed"]},
        )
        evidence.expect(
            f"{name} DXF reload has vector entities",
            dxf_reload.valid and dxf_reload.topology.edges > 0,
            asdict(dxf_reload),
        )
        evidence.expect(
            f"{name} DXF fingerprint is stable",
            dxf_fingerprint["semanticFingerprint"]
            == dxf_reload.metrics["semanticFingerprint"],
            {"edgeCount": dxf_reload.topology.edges},
        )
        evidence.expect(
            f"{name} DXF normalization is idempotent",
            dxf_normalized_twice["changed"] is False,
            {"changed": dxf_normalized_twice["changed"]},
        )

        component_evidence[name] = {
            "step": {
                "byteCount": step_export.byte_count,
                "sha256": step_export.sha256,
                "normalizedSha256": sha256(step_path.read_bytes()).hexdigest(),
                "volumeMm3": step_reload.volume_mm3,
                "boundingBoxMm": bbox_tuple(step_reload.bounding_box_mm),
                "topology": asdict(step_reload.topology),
            },
            "stl": {
                "byteCount": stl_export.byte_count,
                "sha256": stl_export.sha256,
                "normalizedSha256": sha256(stl_path.read_bytes()).hexdigest(),
                "meshVolumeMm3": stl_reload.volume_mm3,
                "triangles": stl_reload.topology.faces,
                "vertices": stl_reload.topology.vertices,
                "boundingBoxMm": bbox_tuple(stl_reload.bounding_box_mm),
            },
            "dxf": {
                "byteCount": dxf_export.byte_count,
                "sha256": dxf_export.sha256,
                "normalizedSha256": sha256(dxf_path.read_bytes()).hexdigest(),
                "edges": dxf_reload.topology.edges,
                "semanticFingerprint": dxf_reload.metrics["semanticFingerprint"],
            },
        }

    # glTF bridge: translate the normalized base STL and structurally reload it.
    gltf_writer = write_gltf_from_stl(out_dir / "base.stl", out_dir / "base.gltf")
    gltf_path = out_dir / "base.gltf"
    gltf_reload = backend.reload_model(gltf_path, "GLTF")
    base_stl_bbox = component_evidence["base"]["stl"]["boundingBoxMm"]
    expected_volume = component_evidence["base"]["step"]["volumeMm3"] or 0.0
    volume_tolerance = max(1.0, expected_volume * 0.001)
    evidence.expect(
        "glTF reload matches STL triangle count",
        gltf_reload.topology.faces == component_evidence["base"]["stl"]["triangles"],
        {
            "stlTriangles": component_evidence["base"]["stl"]["triangles"],
            "gltfTriangles": gltf_reload.topology.faces,
        },
    )
    evidence.expect(
        "glTF bbox matches STL mesh bbox",
        gltf_reload.bounding_box_mm is not None
        and bbox_close(gltf_reload.bounding_box_mm, base_stl_bbox, volume_tolerance),
        {
            "stlBboxMm": base_stl_bbox,
            "gltfBboxMm": bbox_tuple(gltf_reload.bounding_box_mm),
            "toleranceMm3": volume_tolerance,
            "gltfWriter": gltf_writer,
        },
    )
    evidence.expect(
        "glTF writer and reload shas agree",
        gltf_writer["sha256"] == gltf_reload.metrics.get("sha256"),
        {
            "writerSha256": gltf_writer["sha256"],
            "reloadSha256": gltf_reload.metrics.get("sha256"),
        },
    )

    return {
        "schemaVersion": "1.0.0",
        "workItem": "G2-CAD-004",
        "input": "contracts/g1/golden/reference-fixture.json",
        "backend": {
            "backend_id": capabilities.backend_id,
            "backend_version": capabilities.backend_version,
            "export_formats": sorted(capabilities.export_formats),
        },
        "assembly": asdict(assembly),
        "components": component_evidence,
        "gltfBridge": {
            "generator": gltf_writer["generator"],
            "vertexCount": gltf_writer["vertexCount"],
            "triangleCount": gltf_writer["triangleCount"],
            "indexCount": gltf_writer["indexCount"],
            "boundingBoxMm": gltf_writer["boundingBoxMm"],
        },
        "checks": evidence.checks,
        "allChecksPassed": not evidence.failed,
        "engineeringArtifactGenerated": True,
        "releaseArtifactGenerated": False,
    }


if __name__ == "__main__":
    result = verify()
    out = ROOT / "artifacts" / "g2-cad-004" / "verification.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if not result["allChecksPassed"]:
        sys.exit(1)
