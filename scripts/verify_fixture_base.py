"""Build and report the G2 Reference Fixture base without exporting release artifacts."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.adapters import CadQueryBackend  # noqa: E402
from megis.contracts import load_engineering_ir  # noqa: E402
from megis.geometry import build_fixture_base  # noqa: E402


def verify() -> dict:
    document = load_engineering_ir(ROOT / "contracts/g1/golden/reference-fixture.json")
    backend = CadQueryBackend()
    capabilities = backend.capabilities()
    result = build_fixture_base(document, backend)
    topology = backend.inspect_topology(result.model_token)
    return {
        "schemaVersion": "1.0.0",
        "workItem": "G2-CAD-002",
        "input": "contracts/g1/golden/reference-fixture.json",
        "backend": {
            "backend_id": capabilities.backend_id,
            "backend_version": capabilities.backend_version,
            "supported_operations": sorted(item.value for item in capabilities.supported_operations),
            "export_formats": sorted(capabilities.export_formats),
            "deterministic": capabilities.deterministic,
        },
        "result": asdict(result),
        "topology": asdict(topology),
        "engineeringArtifactGenerated": False,
        "releaseArtifactGenerated": False,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, default=list, sort_keys=True))
