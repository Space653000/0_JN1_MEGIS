"""G2-CAD-004: exported artifacts are reloadable and geometry is never empty."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from megis.adapters import CadQueryBackend
from megis.adapters.gltf import write_gltf_from_stl
from megis.determinism.normalization import (
    binary_stl_semantic_fingerprint,
    dxf_vector_semantic_fingerprint,
    normalize_stl_file,
)
from megis.geometry import (
    GeometryContractError,
    GeometryErrorCode,
    build_fixture_assembly,
)


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = json.loads(
    (ROOT / "contracts" / "g1" / "golden" / "reference-fixture.json").read_text(
        encoding="utf-8"
    )
)


@pytest.fixture(scope="module")
def backend() -> CadQueryBackend:
    return CadQueryBackend()


@pytest.fixture(scope="module")
def assembly(backend: CadQueryBackend):
    return build_fixture_assembly(GOLDEN, backend)


@pytest.fixture()
def base_token(assembly) -> str:
    return assembly.base_model_token


def test_capabilities_declare_step_stl_dxf(backend: CadQueryBackend) -> None:
    assert {"STEP", "STL", "DXF"} <= backend.capabilities().export_formats


def test_step_export_and_reload_preserves_volume(
    backend: CadQueryBackend, base_token: str, tmp_path: Path
) -> None:
    step_path = tmp_path / "base.step"
    step_export = backend.export_model(base_token, step_path, "STEP")
    step_reload = backend.reload_model(step_path, "STEP")

    assert step_path.is_file() and step_export.byte_count > 0
    assert step_reload.valid is True
    assert step_reload.solids == 1
    assert step_reload.volume_mm3 == pytest.approx(step_export.volume_mm3, abs=1e-6)
    assert step_reload.topology.faces > 0


def test_stl_reload_reports_mesh_topology(
    backend: CadQueryBackend, base_token: str, tmp_path: Path
) -> None:
    stl_path = tmp_path / "base.stl"
    step_path = tmp_path / "base.step"
    stl_export = backend.export_model(base_token, stl_path, "STL")
    step_reload = backend.reload_model(
        backend.export_model(base_token, step_path, "STEP").output_path, "STEP"
    )
    stl_reload = backend.reload_model(stl_path, "STL")

    assert stl_export.byte_count > 0
    assert stl_reload.valid is True
    assert stl_reload.bounding_box_mm is not None
    assert stl_reload.topology.faces > 0
    assert stl_reload.topology.vertices > 0
    assert stl_reload.volume_mm3 == pytest.approx(step_reload.volume_mm3, rel=0.001)


def test_dxf_reload_reports_vector_edges(
    backend: CadQueryBackend, base_token: str, tmp_path: Path
) -> None:
    dxf_path = tmp_path / "base.dxf"
    dxf_export = backend.export_model(base_token, dxf_path, "DXF")
    dxf_reload = backend.reload_model(dxf_path, "DXF")

    assert dxf_export.byte_count > 0
    assert dxf_reload.valid is True
    assert dxf_reload.topology.edges > 0
    assert dxf_reload.volume_mm3 is None
    assert dxf_reload.metrics["semanticFingerprint"] == dxf_vector_semantic_fingerprint(
        dxf_path
    )["semanticFingerprint"]


def test_gltf_round_trip_matches_stl(
    backend: CadQueryBackend, base_token: str, tmp_path: Path
) -> None:
    stl_path = tmp_path / "base.stl"
    gltf_path = tmp_path / "base.gltf"
    backend.export_model(base_token, stl_path, "STL")
    normalize_stl_file(stl_path)
    writer = write_gltf_from_stl(stl_path, gltf_path)
    reloaded = backend.reload_model(gltf_path, "GLTF")

    assert reloaded.valid is True
    assert reloaded.topology.faces == writer["triangleCount"]
    reloaded_bbox = reloaded.bounding_box_mm
    assert reloaded_bbox is not None
    assert reloaded_bbox.width == pytest.approx(writer["boundingBoxMm"][0], abs=0.001)
    assert reloaded_bbox.depth == pytest.approx(writer["boundingBoxMm"][1], abs=0.001)
    assert reloaded_bbox.height == pytest.approx(writer["boundingBoxMm"][2], abs=0.001)


def test_same_ir_produces_stable_stl_semantic_fingerprint(
    backend: CadQueryBackend, tmp_path: Path
) -> None:
    first = backend.export_model(
        build_fixture_assembly(GOLDEN, backend).base_model_token,
        tmp_path / "first.stl",
        "STL",
    )
    second = backend.export_model(
        build_fixture_assembly(GOLDEN, backend).base_model_token,
        tmp_path / "second.stl",
        "STL",
    )
    normalize_stl_file(Path(first.output_path))
    normalize_stl_file(Path(second.output_path))

    assert binary_stl_semantic_fingerprint(Path(first.output_path)) == (
        binary_stl_semantic_fingerprint(Path(second.output_path))
    )


def test_unknown_model_token_is_rejected(
    backend: CadQueryBackend, tmp_path: Path
) -> None:
    with pytest.raises(GeometryContractError) as caught:
        backend.export_model("cadquery:missing-token", tmp_path / "out.step", "STEP")

    assert caught.value.code == GeometryErrorCode.BACKEND_CONTRACT_VIOLATION


def test_unsupported_export_format_is_rejected(
    backend: CadQueryBackend, base_token: str, tmp_path: Path
) -> None:
    with pytest.raises(GeometryContractError) as caught:
        backend.export_model(base_token, tmp_path / "out.gltf", "GLTF")

    assert caught.value.code == GeometryErrorCode.UNSUPPORTED_OPERATION


def test_unsupported_reload_format_is_rejected(
    backend: CadQueryBackend, base_token: str, tmp_path: Path
) -> None:
    step_path = tmp_path / "base.step"
    backend.export_model(base_token, step_path, "STEP")

    with pytest.raises(GeometryContractError) as caught:
        backend.reload_model(step_path, "OBJ")

    assert caught.value.code == GeometryErrorCode.UNSUPPORTED_OPERATION


def test_reload_missing_file_is_rejected(backend: CadQueryBackend) -> None:
    with pytest.raises(GeometryContractError) as caught:
        backend.reload_model(Path("does-not-exist.step"), "STEP")

    assert caught.value.code == GeometryErrorCode.BACKEND_CONTRACT_VIOLATION


def test_empty_step_reload_is_rejected(
    backend: CadQueryBackend, tmp_path: Path
) -> None:
    empty = tmp_path / "empty.step"
    empty.write_bytes(b"")

    with pytest.raises(GeometryContractError) as caught:
        backend.reload_model(empty, "STEP")

    assert caught.value.code == GeometryErrorCode.BACKEND_CONTRACT_VIOLATION


def test_truncated_stl_reload_is_rejected(
    backend: CadQueryBackend, tmp_path: Path
) -> None:
    truncated = tmp_path / "truncated.stl"
    truncated.write_bytes(b"x" * 20)

    with pytest.raises(GeometryContractError) as caught:
        backend.reload_model(truncated, "STL")

    assert caught.value.code == GeometryErrorCode.BACKEND_CONTRACT_VIOLATION
