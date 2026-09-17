"""Verify G2-CAD-003 in memory without exporting engineering artifacts."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.adapters import CadQueryBackend  # noqa: E402
from megis.contracts import load_engineering_ir  # noqa: E402
from megis.geometry import build_fixture_assembly, plan_fixture_assembly  # noqa: E402


def verify() -> dict:
    source = ROOT / "contracts/g1/golden/reference-fixture.json"
    document = load_engineering_ir(source)
    plan = plan_fixture_assembly(document)
    backend = CadQueryBackend()
    result = build_fixture_assembly(document, backend)
    tokens = (
        result.base_model_token,
        result.cover_model_token,
        result.pcb_envelope_model_token,
        *result.fastener_model_tokens,
    )
    return {
        "schemaVersion": "1.0.0",
        "workItem": "G2-CAD-003",
        "input": source.relative_to(ROOT).as_posix(),
        "plan": asdict(plan),
        "result": asdict(result),
        "topology": [asdict(backend.inspect_topology(token)) for token in tokens],
        "transitionalAssumptions": [
            "PCB envelope and USB-C opening use isolated v2 Reference Fixture defaults.",
            "V3 G1-REQ-001 must replace those defaults with researched parameters.",
        ],
        "geometryGeneratedInMemory": True,
        "engineeringArtifactGenerated": False,
        "releaseArtifactGenerated": False,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, sort_keys=True))

