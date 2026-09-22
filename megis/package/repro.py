"""G5-REP-001: clean-environment reproducible prototype build.

The reproducibility contract for the G5 prototype package (blueprint §26.8)
is the *semantic fingerprint*: STEP -> normalized text, STL -> triangles,
DXF -> vectors, BOM CSV -> UTF-8/LF text, draft drawing -> SVG text.  A
clean rebuild must reproduce the exact hashes frozen in
``contracts/g5/golden/repro-fingerprints.json``.

``byte_sha256`` is additionally byte-stable for ``bom.csv``,
``draft_drawing.svg`` and ``reference_case.stl``.  The STEP and DXF
exporters embed run metadata (e.g. STEP ``FILE_NAME`` timestamps), so their
bytes legitimately differ between runs while the semantic fingerprint stays
identical; that exporter delta is documented, not an ADR-worthy content
difference.

Any *semantic* drift between a clean rebuild and the frozen golden
fingerprints raises ``MEGIS-REP-001`` and requires an ADR before acceptance.
"""

from __future__ import annotations

import importlib.metadata
import json
from hashlib import sha256
import platform
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from megis.determinism import canonical_json, byte_sha256
from megis.errors import MegisError
from megis.package.bom import build_bom
from megis.package.drawing import DEFAULT_WHITELIST, build_draft_drawing
from megis.package.manifest import semantic_fingerprint_for_path
from spikes.g0_cad.reference_case import export_artifacts

REPRO_BUILDER_VERSION = "megis.repro@1.0.0"
FINGERPRINT_POLICY_VERSION = "1.0.0"

ROOT = Path(__file__).resolve().parents[2]
REPRO_GOLDEN_SCHEMA_PATH = ROOT / "schemas" / "v3" / "repro-fingerprints.schema.json"
REPRO_DEFAULT_GOLDEN_PATH = (
    ROOT / "contracts" / "g5" / "golden" / "repro-fingerprints.json"
)
REPRO_DEFAULT_IR_PATH = ROOT / "contracts" / "g1" / "golden" / "reference-fixture.json"

# Basename -> whether byte_sha256 must be stable across clean rebuilds.
REPRO_BYTE_STABLE: Mapping[str, bool] = {
    "reference_case.step": False,
    "reference_case.stl": True,
    "reference_case_section_z10.dxf": False,
    "bom.csv": True,
    "draft_drawing.svg": True,
}
REPRO_ARTIFACT_NAMES = tuple(REPRO_BYTE_STABLE)


def _drift(detail: Any) -> MegisError:
    return MegisError(
        "MEGIS-REP-001",
        engineer_detail={"reason": "clean-environment rebuild fingerprint drift", "detail": detail},
    )


def rebuild_prototype_outputs(
    output_dir: Path,
    ir_path: Path | None = None,
) -> dict[str, Any]:
    """Rebuild the five prototype artifacts and return a fingerprint report.

    Outputs are written to ``output_dir``.  The report only pins content
    guarantees (semantic fingerprints for every artifact, byte_sha256 for
    byte-stable artifacts), so two rebuilds in the same locked environment
    produce identical reports while STEP/DXF bytes may carry exporter metadata.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ir_doc = json.loads(
        (ir_path if ir_path is not None else REPRO_DEFAULT_IR_PATH).read_text(encoding="utf-8")
    )

    bom = build_bom(ir_doc)
    (output_dir / "bom.csv").write_text(bom["csv"], encoding="utf-8", newline="")

    drawing = build_draft_drawing(ir_doc, dimension_whitelist=DEFAULT_WHITELIST)
    (output_dir / "draft_drawing.svg").write_text(drawing["svg"], encoding="utf-8", newline="")

    export_artifacts(output_dir)  # reference_case.step / .stl / section dxf

    return build_fingerprint_report(output_dir)


def build_fingerprint_report(output_dir: Path) -> dict[str, Any]:
    """Compute the deterministic fingerprint report for a rebuilt output dir."""
    output_dir = Path(output_dir)
    artifacts: dict[str, Any] = {}
    for name in REPRO_ARTIFACT_NAMES:
        path = output_dir / name
        if not path.is_file():
            raise _drift({"missing": name, "outputDir": str(output_dir)})
        fingerprint, kind = semantic_fingerprint_for_path(path)
        record: dict[str, Any] = {
            "path": name,
            "bytes": path.stat().st_size,
            "semanticFingerprint": fingerprint,
            "fingerprintKind": kind,
        }
        if REPRO_BYTE_STABLE[name]:
            record["byte_sha256"] = byte_sha256(path)
        artifacts[name] = record

    report = {
        "schemaVersion": "1.0.0",
        "builderVersion": REPRO_BUILDER_VERSION,
        "artifacts": artifacts,
    }
    report["reportFingerprint"] = _report_fingerprint(report)
    return report


def _report_fingerprint(report: Mapping[str, Any]) -> str:
    """Stable digest of the report: semantic fingerprints plus stable bytes."""
    payload = {
        "artifacts": {
            name: {key: value for key, value in record.items() if key != "bytes"}
            for name, record in report["artifacts"].items()
        }
    }
    return sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def compare_to_golden(report: Mapping[str, Any], golden: Mapping[str, Any]) -> dict[str, Any]:
    """Compare a rebuilt report to the frozen golden fingerprints.

    Returns ``{"identical": bool, "differences": [...]}``.  Every semantic
    fingerprint must match; byte_sha256 must match only for byte-stable
    artifacts.  A non-empty difference list is a ``MEGIS-REP-001`` drift that
    needs an ADR.
    """
    differences: list[dict[str, Any]] = []
    rebuilt_artifacts = report.get("artifacts", {})
    golden_artifacts = golden.get("artifacts", {})
    for name in REPRO_ARTIFACT_NAMES:
        rebuilt = rebuilt_artifacts.get(name, {})
        expected = golden_artifacts.get(name, {})
        for field in ("semanticFingerprint", "fingerprintKind"):
            if rebuilt.get(field) != expected.get(field):
                differences.append(
                    {
                        "artifact": name,
                        "field": field,
                        "rebuilt": rebuilt.get(field),
                        "golden": expected.get(field),
                    }
                )
        if REPRO_BYTE_STABLE[name] and rebuilt.get("byte_sha256") != expected.get("byte_sha256"):
            differences.append(
                {
                    "artifact": name,
                    "field": "byte_sha256",
                    "rebuilt": rebuilt.get("byte_sha256"),
                    "golden": expected.get("byte_sha256"),
                }
            )
    if report.get("reportFingerprint") != golden.get("reportFingerprint"):
        differences.append(
            {
                "artifact": "*",
                "field": "reportFingerprint",
                "rebuilt": report.get("reportFingerprint"),
                "golden": golden.get("reportFingerprint"),
            }
        )
    return {"identical": not differences, "differences": differences}


def validate_golden(golden: Mapping[str, Any]) -> None:
    """Ensure a frozen golden document is schema-conformant."""
    Draft202012Validator.check_schema(_load_golden_schema())
    validator = Draft202012Validator(_load_golden_schema())
    errors = sorted(
        validator.iter_errors(golden),
        key=lambda error: str(list(error.absolute_path)),
    )
    if errors:
        messages = "; ".join(error.message for error in errors)
        raise ValueError(f"repro fingerprint golden invalid: {messages}")


def _load_golden_schema() -> dict[str, Any]:
    return json.loads(REPRO_GOLDEN_SCHEMA_PATH.read_text(encoding="utf-8"))


def _toolchain() -> dict[str, Any]:
    return {
        "os": platform.system(),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "cadquery": importlib.metadata.version("cadquery"),
        "cadqueryOcp": importlib.metadata.version("cadquery-ocp"),
        "fingerprintPolicyVersion": FINGERPRINT_POLICY_VERSION,
    }


def freeze_golden(report: Mapping[str, Any], out_path: Path) -> dict[str, Any]:
    """Freeze a rebuilt report as the canonical golden fingerprints."""
    golden = {
        "schemaVersion": "1.0.0",
        "corpusId": "g5-repro-fingerprints@1.0.0",
        "builderVersion": REPRO_BUILDER_VERSION,
        "freezeNote": (
            "Frozen by G5-REP-001. Any clean-environment semantic fingerprint "
            "drift raises MEGIS-REP-001 and requires an ADR before acceptance."
        ),
        "toolchain": _toolchain(),
        "artifacts": report["artifacts"],
        "reportFingerprint": report["reportFingerprint"],
    }
    validate_golden(golden)
    out_path.write_text(json.dumps(golden, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return golden
