from pathlib import Path

import pytest

from spikes.g0_cad.reference_case import ARTIFACT_NAMES, SPEC, generate_and_verify


def test_reference_case_exports_and_reloads_all_formats(tmp_path: Path) -> None:
    manifest = generate_and_verify(tmp_path)

    assert manifest["classification"] == "FEASIBILITY_SPIKE"
    assert manifest["maturity"] == "PROTOTYPE"
    assert manifest["engineeringReviewRequired"] is True
    assert manifest["source"]["valid"] is True
    assert manifest["source"]["solids"] == 1
    assert manifest["source"]["boundingBoxMm"] == {
        "xlen": SPEC.length_mm,
        "ylen": SPEC.width_mm,
        "zlen": SPEC.height_mm,
    }

    for kind, filename in ARTIFACT_NAMES.items():
        assert (tmp_path / filename).is_file()
        assert manifest["verification"][kind]["valid"] is True
        assert manifest["artifacts"][kind]["bytes"] > 0
        assert len(manifest["artifacts"][kind]["sha256"]) == 64

    assert manifest["verification"]["step"]["volumeMm3"] == pytest.approx(
        manifest["source"]["volumeMm3"], abs=1e-6
    )
    assert manifest["verification"]["dxf"]["edges"] == 8
    assert manifest["verification"]["dxf"]["wires"] == 2
    assert manifest["verification"]["dxf"]["wireBoundingBoxesMm"] == [
        {"xlen": 120.0, "ylen": 80.0},
        {"xlen": 116.0, "ylen": 76.0},
    ]
