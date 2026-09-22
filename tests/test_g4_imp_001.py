"""G4-IMP-001 safe STEP/DXF metadata extraction tests (E3).

The blueprint section 12 import policy is exercised end to end through the
public ``extract_import_metadata`` API: a worker subprocess is launched under
a timeout, bounded by size and an injectable entity budget, and a malformed or
mislabeled file is rejected before any report is accepted.  Unit tests pin the
provable fields (bounding box, counts, file unit incl. inch) and the
truthfulness contract (no material/supplier/capability fabrication).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import json
from jsonschema import Draft202012Validator

from megis.errors import MegisError
from megis.importing import (
    extract_dxf_metadata,
    extract_import_metadata,
    extract_step_metadata,
    validate_import_report,
    validate_report_schema,
)

STEP_MM = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION((''),'2;1');
FILE_NAME('box.step','2026-09-22T00:00:00',('u'),('o'),'','','');
FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 3 1 1 }'));
ENDSEC;
DATA;
#1=(LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.));
#2=CARTESIAN_POINT('p1',(0.0,0.0,0.0));
#3=CARTESIAN_POINT('p2',(10.0,20.0,30.0));
#4=MANIFOLD_SOLID_BREP('box',#5);
#5=CLOSED_SHELL('s',(#6));
#6=ADVANCED_FACE('f',(#7),#8,.T.);
#10=EDGE_CURVE('e',#2,#3,#11,.T.);
#11=VERTEX_POINT('v',#2);
#12=CYLINDRICAL_SURFACE('c',#2,#14);
#13=PLANE('p',#2);
ENDSEC;
END-ISO-10303-21;
"""

STEP_ZERO = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION((''),'2;1');
FILE_NAME('empty.step','2026-09-22T00:00:00',('u'),('o'),'','','');
FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 3 1 1 }'));
ENDSEC;
DATA;
ENDSEC;
END-ISO-10303-21;
"""

DXF_INCH = """0
SECTION
2
HEADER
9
$INSUNITS
70
1
0
ENDSEC
0
SECTION
2
ENTITIES
0
LINE
10
0.0
20
0.0
10
10.0
20
10.0
0
CIRCLE
10
5.0
20
5.0
40
2.0
0
ENDSEC
0
EOF
"""

DXF_MM = """0
SECTION
2
HEADER
9
$INSUNITS
70
4
0
ENDSEC
0
SECTION
2
ENTITIES
0
LINE
10
0.0
20
0.0
10
10.0
20
10.0
0
CIRCLE
10
5.0
20
5.0
40
2.0
0
ENDSEC
0
EOF
"""


ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "contracts" / "g4" / "golden" / "import-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "import-corpus.schema.json"


def _write(tmp_path: Path, name: str, content: str) -> Path:
    target = tmp_path / name
    target.write_text(content, encoding="utf-8")
    return target


def test_step_valid_extraction_via_public_api(tmp_path: Path) -> None:
    source = _write(tmp_path, "box.step", STEP_MM)
    report = extract_import_metadata(source)

    assert report.derived_from_import is True
    assert report.capability_level is None
    assert report.solids == 1
    assert report.shells == 1
    assert report.faces == 1
    assert report.edges == 1
    assert report.candidate_holes == 1
    assert report.candidate_planar_sections == 1
    assert report.file_unit == "millimetre"
    assert report.bounding_box_mm is not None
    assert report.bounding_box_mm.to_dict() == {
        "xmin": 0.0,
        "ymin": 0.0,
        "zmin": 0.0,
        "xmax": 10.0,
        "ymax": 20.0,
        "zmax": 30.0,
    }

    as_dict = report.to_dict()
    assert as_dict["derivedFromImport"] is True
    assert as_dict["capabilityLevel"] is None
    assert "material" not in as_dict
    assert "supplier" not in as_dict


def test_step_inch_unit_detected() -> None:
    payload = STEP_MM.replace(
        "#1=(LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.));",
        "#1=(LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.INCH.));",
    )
    metadata = extract_step_metadata(payload)
    assert metadata.file_unit == "inch"
    assert metadata.bounding_box is not None


def test_step_unit_unknown_when_only_unrecognised_si_unit() -> None:
    payload = STEP_MM.replace(
        "#1=(LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.));",
        "#1=(LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.RADIAN.));",
    )
    metadata = extract_step_metadata(payload)
    assert metadata.file_unit == "unknown"
    assert metadata.solids == 1


def test_step_zero_entity_is_valid_but_reports_no_geometry(tmp_path: Path) -> None:
    source = _write(tmp_path, "empty.step", STEP_ZERO)
    report = extract_import_metadata(source)
    assert report.bounding_box_mm is None
    assert report.solids == 0
    assert report.file_unit is None
    assert any("bounding box unavailable" in item for item in report.parser_warnings)


def test_dxf_valid_extraction_via_public_api(tmp_path: Path) -> None:
    source = _write(tmp_path, "part.dxf", DXF_INCH)
    report = extract_import_metadata(source)

    assert report.import_format == "DXF"
    assert report.file_unit == "inch"
    assert report.edges == 2
    assert report.candidate_holes == 1
    assert report.candidate_planar_sections == 0
    assert report.bounding_box_mm is not None
    assert report.bounding_box_mm.to_dict() == {
        "xmin": 0.0,
        "ymin": 0.0,
        "zmin": 0.0,
        "xmax": 10.0,
        "ymax": 10.0,
        "zmax": 0.0,
    }


def test_dxf_unit_level_counts(tmp_path: Path) -> None:
    metadata = extract_dxf_metadata(DXF_INCH)
    assert metadata.total_entities == 2
    assert metadata.entity_counts == {"LINE": 1, "CIRCLE": 1}
    assert metadata.file_unit == "inch"
    assert metadata.candidate_holes == 1


def test_step_truncated_is_rejected_as_imp_003(tmp_path: Path) -> None:
    fragment = STEP_MM.split("DATA;")[0] + "DATA;\n#2=CARTESIAN_POINT('p',(0,0,0));\n"
    source = _write(tmp_path, "truncated.step", fragment)
    with pytest.raises(MegisError) as raised:
        extract_import_metadata(source)
    assert raised.value.error_object.code == "MEGIS-IMP-003"
    detail = raised.value.error_object.engineer_detail
    assert "STEP missing structural markers" in detail["workerDetail"]


def test_dxf_missing_eof_is_rejected_as_imp_003(tmp_path: Path) -> None:
    no_eof = DXF_INCH.rsplit("0\nEOF", 1)[0]
    source = _write(tmp_path, "truncated.dxf", no_eof)
    with pytest.raises(MegisError) as raised:
        extract_import_metadata(source)
    assert raised.value.error_object.code == "MEGIS-IMP-003"
    detail = raised.value.error_object.engineer_detail
    assert "DXF missing final EOF marker" in detail["workerDetail"]


def test_bad_magic_is_rejected_as_imp_002(tmp_path: Path) -> None:
    source = _write(tmp_path, "fake.step", "this is not a STEP file\n")
    with pytest.raises(MegisError) as raised:
        extract_import_metadata(source)
    assert raised.value.error_object.code == "MEGIS-IMP-002"


def test_wrong_extension_is_rejected_as_imp_002(tmp_path: Path) -> None:
    source = _write(tmp_path, "box.dxf", STEP_MM)
    with pytest.raises(MegisError) as raised:
        extract_import_metadata(source)
    assert raised.value.error_object.code == "MEGIS-IMP-002"


def test_oversized_file_is_rejected_as_imp_001(tmp_path: Path) -> None:
    source = _write(tmp_path, "big.step", STEP_MM)
    with pytest.raises(MegisError) as raised:
        extract_import_metadata(source, max_bytes=10)
    assert raised.value.error_object.code == "MEGIS-IMP-001"


def test_entity_budget_is_injectable_for_step(tmp_path: Path) -> None:
    source = _write(tmp_path, "box.step", STEP_MM)
    with pytest.raises(MegisError) as raised:
        extract_import_metadata(source, max_entities=2)
    assert raised.value.error_object.code == "MEGIS-IMP-004"


def test_entity_budget_is_injectable_for_dxf(tmp_path: Path) -> None:
    source = _write(tmp_path, "part.dxf", DXF_INCH)
    with pytest.raises(MegisError) as raised:
        extract_import_metadata(source, max_entities=1)
    assert raised.value.error_object.code == "MEGIS-IMP-004"


def test_import_report_schema_is_stable() -> None:
    validate_report_schema()


def test_sample_report_passes_schema(tmp_path: Path) -> None:
    source = _write(tmp_path, "box.step", STEP_MM)
    report = extract_import_metadata(source)
    validate_import_report(report.to_dict())


@pytest.fixture(scope="module")
def import_corpus() -> dict:
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def import_corpus_schema() -> dict:
    return json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))


def _build_source(tmp_path: Path, case: dict) -> tuple[Path, dict]:
    spec = case["input"]["sample"]
    fmt = case["input"]["format"]
    kind = spec["kind"]
    expect = case["expect"]

    if fmt == "STEP":
        if kind == "valid":
            if expect.get("fileUnit") == "inch":
                content = STEP_MM.replace(
                    "#1=(LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.));",
                    "#1=(LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.INCH.));",
                )
            elif expect.get("fileUnit") == "metre":
                content = STEP_MM.replace(
                    "#1=(LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.));",
                    "#1=(LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.METRE.));",
                )
            else:
                content = STEP_MM
            return _write(tmp_path, "sample.step", content), {}
        if kind == "zero_entities":
            return _write(tmp_path, "empty.step", STEP_ZERO), {}
        if kind == "oversized":
            return (
                _write(tmp_path, "big.step", STEP_MM),
                {"max_bytes": spec.get("maxBytes", 10)},
            )
        if kind == "truncated":
            fragment = (
                STEP_MM.split("DATA;")[0]
                + "DATA;\n#2=CARTESIAN_POINT('p',(0,0,0));\n"
            )
            return _write(tmp_path, "trunc.step", fragment), {}
        if kind == "deeply_nested":
            return _write(tmp_path, "deep.step", STEP_MM), {"max_entities": 1}
        if kind == "wrong_extension":
            return _write(tmp_path, "sample.dxf", STEP_MM), {}
        if kind == "bad_magic":
            return _write(tmp_path, "fake.step", "not a STEP file\n"), {}

    if fmt == "DXF":
        if kind == "valid":
            content = DXF_INCH if expect.get("fileUnit") == "inch" else DXF_MM
            return _write(tmp_path, "sample.dxf", content), {}
        if kind == "oversized":
            return (
                _write(tmp_path, "big.dxf", DXF_INCH),
                {"max_bytes": spec.get("maxBytes", 10)},
            )
        if kind == "truncated":
            no_eof = DXF_INCH.rsplit("0\nEOF", 1)[0]
            return _write(tmp_path, "trunc.dxf", no_eof), {}
        if kind == "deeply_nested":
            return _write(tmp_path, "deep.dxf", DXF_INCH), {"max_entities": 1}
        if kind == "wrong_extension":
            return _write(tmp_path, "sample.stp", DXF_INCH), {}
        if kind == "bad_magic":
            return _write(tmp_path, "fake.dxf", "0\nEOF\n"), {}

    raise ValueError(f"unsupported corpus case {case['case_id']}")


def test_import_corpus_validates_against_schema(
    import_corpus: dict, import_corpus_schema: dict
) -> None:
    Draft202012Validator.check_schema(import_corpus_schema)
    errors = list(Draft202012Validator(import_corpus_schema).iter_errors(import_corpus))
    assert errors == []
    assert len(import_corpus["cases"]) >= 16


@pytest.mark.parametrize(
    "case",
    [
        json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["cases"][index]
        for index in range(
            len(json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["cases"])
        )
    ],
    ids=lambda case: case["case_id"],
)
def test_every_corpus_case_matches_golden(case: dict, tmp_path: Path) -> None:
    source, kwargs = _build_source(tmp_path, case)
    expect = case["expect"]

    if not expect["valid"]:
        with pytest.raises(MegisError) as raised:
            extract_import_metadata(source, **kwargs)
        assert raised.value.error_object.code == expect["errorCode"]
        return

    report = extract_import_metadata(source, **kwargs)
    if "boundingBoxMm" in expect:
        assert report.bounding_box_mm is not None
        assert report.bounding_box_mm.to_dict() == expect["boundingBoxMm"]
    for key, field in (
        ("solids", "solids"),
        ("shells", "shells"),
        ("edges", "edges"),
        ("candidateHoles", "candidate_holes"),
        ("candidatePlanarSections", "candidate_planar_sections"),
        ("fileUnit", "file_unit"),
    ):
        if key in expect:
            assert getattr(report, field) == expect[key], key
