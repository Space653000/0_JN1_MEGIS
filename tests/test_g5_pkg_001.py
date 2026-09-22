"""G5-PKG-001 package manifest and content hashes tests (E3).

The manifest is built by ``build_package_manifest`` (L1 byte hash + L2
semantic fingerprint per artifact), then ``verify_package_manifest`` rechecks
every declared artifact against the files on disk.  A table-driven corpus pins
the acceptance contract: valid packages pass, and any tampered byte, missing
declared artifact, production-ready note, RELEASED maturity, non-PROTOTYPE
kind or unregistered fingerprint policy must fail with a structured ``PKG``
error.
"""

from __future__ import annotations

import json
import struct
from hashlib import sha256
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from megis.errors import MegisError
from megis.package import (
    build_package_manifest,
    detect_runtime,
    validate_manifest_schema,
    verify_package_manifest,
)

STEP = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION((''),'2;1');
FILE_NAME('base.step','2026-09-22T00:00:00',('u'),('o'),'','','');
FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 3 1 1 }'));
ENDSEC;
DATA;
#1=(LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.));
#2=CARTESIAN_POINT('p1',(0.0,0.0,0.0));
#3=CARTESIAN_POINT('p2',(10.0,20.0,30.0));
#4=MANIFOLD_SOLID_BREP('base',#5);
#5=CLOSED_SHELL('s',(#6));
#6=ADVANCED_FACE('f',(#7),#8,.T.);
#10=EDGE_CURVE('e',#2,#3,#11,.T.);
#11=VERTEX_POINT('v',#2);
#12=CYLINDRICAL_SURFACE('c',#2,#14);
#13=PLANE('p',#2);
ENDSEC;
END-ISO-10303-21;
"""

DXF = """0
SECTION
2
ENTITIES
0
LINE
10
0.0
20
0.0
11
10.0
21
10.0
0
ENDSEC
0
EOF
"""

JSON_DOC = '{"schemaVersion":"1.0.0","tolerance_mm":0.1,"material":"Al6061"}'

TEXT = "MEGIS PROTOTYPE PACKAGE\nDo not ship as production.\n"


def _binary_stl() -> bytes:
    header = ("MEGIS BINARY STL | policy 1.0.0".ljust(80, " ")).encode("ascii")
    payload = struct.pack("<I", 1)
    payload += struct.pack("<12fH", 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0)
    return header + payload


KIND_TO_FILE = {
    "step": "base.step",
    "stl_binary": "pcb.stl",
    "dxf": "cover.dxf",
    "json": "notes.json",
    "text": "readme.txt",
}


def _write_samples(tmp_path: Path, kinds: list[str]) -> dict[str, Path]:
    written: dict[str, Path] = {}
    for kind in kinds:
        name = KIND_TO_FILE[kind]
        target = tmp_path / name
        if kind == "step":
            target.write_text(STEP, encoding="utf-8")
        elif kind == "stl_binary":
            target.write_bytes(_binary_stl())
        elif kind == "dxf":
            target.write_text(DXF, encoding="utf-8")
        elif kind == "json":
            target.write_text(JSON_DOC, encoding="utf-8")
        else:
            target.write_text(TEXT, encoding="utf-8")
        written[name] = target
    return written


def _base_kwargs(artifact_paths: dict[str, Path]) -> dict:
    return {
        "design_id": "fixture-001",
        "revision": "A",
        "artifact_paths": artifact_paths,
        "input_hashes": {"requirement.yaml": "1" * 64},
        "versions": {
            "schema": "1.0.0",
            "engine": "cadquery-backend@1.0.0",
            "libraries": {"cadquery": "2.8.0", "ocp": "7.9.3.1.1"},
            "rules": "cnc-dfm@1.0.0",
            "models": "none",
            "solvers": "none",
        },
        "random_seed": "seed-0001",
        "executed_validations": ["geometry-valid", "collision-check"],
        "gates": {"passed": ["G0", "G1"], "failed": [], "waived": [], "skipped": []},
        "assumptions": ["Aluminum 6061 assumed for prototyping"],
        "unknowns": [],
        "human_signoffs": [
            {
                "signoff_id": "SO-0005",
                "reviewer": "codex",
                "recorded_at": "2026-09-22T16:05:00+08:00",
            }
        ],
        "maturity": {
            "state": "PROTOTYPE",
            "achieved_index": 2,
            "blocking_reasons": [],
            "inputs_digest": "2" * 64,
            "evaluator_version": "megis.maturity@1.0.0",
        },
        "envelope_ref": "envelope/fixture@1.0.0",
        "dna_ref": "dna/fixture@1.0.0",
        "module_versions": {"mod.pcb": "1.0.0"},
        "ai_involvement": {"ai_used": False},
        "runtime": {"os": "test", "python": "3.11", "machine": "AMD64", "emulation": False},
    }


def _apply_tamper(tmp_path: Path, name: str, mode: str) -> None:
    path = tmp_path / name
    raw = bytearray(path.read_bytes())
    if mode == "flip_byte":
        raw[0] ^= 0xFF
    elif mode == "append_byte":
        raw.append(0x41)
    elif mode == "truncate":
        del raw[len(raw) // 2 :]
    else:
        raise ValueError(f"unknown tamper mode {mode}")
    path.write_bytes(bytes(raw))


def _apply_dial(manifest: dict, dial: dict, tmp_path: Path) -> dict:
    action = dial["action"]
    if action == "set_manifest_field":
        manifest[dial["field"]] = dial["value"]
    elif action == "drop_manifest_field":
        manifest.pop(dial["field"])
    elif action == "set_package_kind":
        manifest["package_kind"] = "RELEASE_PACKAGE"
    elif action == "released_maturity":
        manifest["maturity"]["state"] = "RELEASED"
    elif action == "production_ready_note":
        manifest["assumptions"] = ["This package is PRODUCTION READY."]
    elif action == "unregistered_fingerprint_policy":
        manifest["fingerprint_policy_version"] = "9.9.9"
    elif action == "rename_artifact_file":
        (tmp_path / "notes.json").rename(tmp_path / "notes-moved.json")
    else:
        raise ValueError(f"unsupported dial action {action}")
    return manifest


ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "contracts" / "g5" / "golden" / "manifest-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "manifest-corpus.schema.json"


@pytest.fixture(scope="module")
def manifest_corpus() -> dict:
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def manifest_corpus_schema() -> dict:
    return json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_package_manifest_schema_is_stable() -> None:
    validate_manifest_schema()


def test_corpus_validates_against_schema(
    manifest_corpus: dict, manifest_corpus_schema: dict
) -> None:
    Draft202012Validator.check_schema(manifest_corpus_schema)
    errors = list(Draft202012Validator(manifest_corpus_schema).iter_errors(manifest_corpus))
    assert errors == []
    assert len(manifest_corpus["cases"]) >= 16


def test_build_is_reproducible_with_same_inputs(tmp_path: Path) -> None:
    samples = _write_samples(tmp_path, ["step", "json", "text"])
    kwargs = _base_kwargs(samples)
    first = build_package_manifest(**kwargs, generated_at="2026-09-22T00:00:00+00:00")
    second = build_package_manifest(**kwargs, generated_at="2026-09-22T12:00:00+00:00")
    assert first["manifestSemanticFingerprint"]["semanticFingerprint"] == second[
        "manifestSemanticFingerprint"
    ]["semanticFingerprint"]


def test_build_records_truthful_content_hashes(tmp_path: Path) -> None:
    samples = _write_samples(tmp_path, ["stl_binary", "dxf", "json", "text"])
    manifest = build_package_manifest(**_base_kwargs(samples))
    assert manifest["package_kind"] == "PROTOTYPE_PACKAGE"
    assert manifest["classification"] == "DESIGN_RUN"
    assert len(manifest["artifact_hashes"]) == len(samples)
    for entry in manifest["artifact_hashes"]:
        source = tmp_path / entry["path"]
        assert entry["bytes"] == source.stat().st_size
        assert entry["byte_sha256"] == _sha256_hex(source)
        assert entry["semantic_fingerprint"]
        assert entry["fingerprint_kind"]
    assert manifest["runtime"] == {
        "os": "test",
        "python": "3.11",
        "machine": "AMD64",
        "emulation": False,
    }
    assert manifest["gates"] == {
        "passed": ["G0", "G1"],
        "failed": [],
        "waived": [],
        "skipped": [],
    }
    assert manifest["ai_involvement"]["ai_used"] is False


def test_verify_valid_returns_check_ledger(tmp_path: Path) -> None:
    samples = _write_samples(tmp_path, ["step", "stl_binary", "dxf", "json", "text"])
    manifest = build_package_manifest(**{**_base_kwargs(samples)})
    result = verify_package_manifest(manifest, tmp_path)
    assert result["valid"] is True
    assert result["checkedArtifacts"] == 5
    assert result["manifestFingerprintMatched"] is True
    for entry in result["artifactLedger"]:
        assert entry["byte_sha256"] == _sha256_hex(tmp_path / entry["path"])


def test_runtime_detected_by_default(tmp_path: Path) -> None:
    samples = _write_samples(tmp_path, ["text"])
    kwargs = _base_kwargs(samples)
    kwargs.pop("runtime", None)
    manifest = build_package_manifest(**kwargs)
    runtime = manifest["runtime"]
    assert runtime["machine"] == detect_runtime()["machine"]
    assert runtime["emulation"] is False


def test_generated_at_is_excluded_from_fingerprint(tmp_path: Path) -> None:
    samples = _write_samples(tmp_path, ["text"])
    manifest = build_package_manifest(**{**_base_kwargs(samples)})
    manifest["generated_at"] = "2099-01-01T00:00:00+00:00"
    result = verify_package_manifest(manifest, tmp_path)
    assert result["valid"] is True


@pytest.mark.parametrize(
    "case",
    [
        json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["cases"][index]
        for index in range(len(json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["cases"]))
    ],
    ids=lambda case: case["case_id"],
)
def test_every_corpus_case_matches_golden(case: dict, tmp_path: Path) -> None:
    samples = _write_samples(tmp_path, case["artifact_kinds"])
    manifest = build_package_manifest(**{**_base_kwargs(samples)})
    dial = case.get("dial")
    if dial is not None:
        manifest = _apply_dial(manifest, dial, tmp_path)
    tamper = case.get("tamper")
    if tamper is not None:
        _apply_tamper(tmp_path, tamper["file"], tamper["mode"])

    expect = case["expect"]
    if not expect["valid"]:
        with pytest.raises(MegisError) as raised:
            verify_package_manifest(manifest, tmp_path)
        assert raised.value.error_object.code == expect["error_code"], case["case_id"]
        return

    result = verify_package_manifest(manifest, tmp_path)
    assert result["valid"] is True, case["case_id"]
    assert result["checkedArtifacts"] == len(samples), case["case_id"]
    assert result["manifestFingerprintMatched"] is True, case["case_id"]


def _sha256_hex(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()
