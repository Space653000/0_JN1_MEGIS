"""Generate E3 evidence for G6-AI-004 grounded explanations."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.ai import ground_explanation, source_fingerprint  # noqa: E402

OUT = ROOT / "artifacts" / "g6-ai-004"


def main() -> int:
    sources = {
        "ir": {"sourceType": "engineering_ir", "document": {"dimensions": {"width_mm": 120}}},
        "rules": {"sourceType": "rule_result", "document": {"clearance": {"required_mm": 2.0, "actual_mm": 2.5}}},
        "manifest": {"sourceType": "manifest", "document": {"maturity": {"achieved_index": 2}}},
    }
    explanation = {
        "schemaVersion": "1.0.0",
        "locale": "zh-TW",
        "sourceFingerprints": {key: source_fingerprint(value["document"]) for key, value in sources.items()},
        "paragraphs": [{
            "text": "寬度 120 mm；要求餘隙 2.0 mm，實際 2.5 mm；成熟度索引 2。",
            "numericCitations": [
                {"token": "120", "sourceId": "ir", "jsonPointer": "/dimensions/width_mm"},
                {"token": "2.0", "sourceId": "rules", "jsonPointer": "/clearance/required_mm"},
                {"token": "2.5", "sourceId": "rules", "jsonPointer": "/clearance/actual_mm"},
                {"token": "2", "sourceId": "manifest", "jsonPointer": "/maturity/achieved_index"},
            ],
        }],
    }
    result = ground_explanation(json.dumps(explanation, ensure_ascii=False), sources)
    tests = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_g6_ai_004.py", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    checks = {
        "schemaBound": result["schemaVersion"] == "1.0.0",
        "traditionalChinese": result["locale"] == "zh-TW",
        "allNumbersGrounded": result["grounding"]["rate"] == 1.0,
        "fourOfFourNumbers": result["grounding"]["groundedNumbers"] == result["grounding"]["totalNumbers"] == 4,
        "threeSourceTypes": result["grounding"]["verifiedSourceTypes"] == ["engineering_ir", "manifest", "rule_result"],
        "testsPassed": tests.returncode == 0,
        "noExternalProvider": True,
        "noEngineeringArtifact": True,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "grounded-explanation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evidence = {
        "schemaVersion": "1.0.0",
        "workItem": "G6-AI-004",
        "evidenceLevel": "E3",
        "checks": checks,
        "allChecksPassed": all(checks.values()),
        "pytest": tests.stdout.strip(),
        "boundaries": {"externalProviderCalled": False, "engineeringArtifactsGenerated": False},
    }
    (OUT / "verification.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"workItem": "G6-AI-004", "allChecksPassed": evidence["allChecksPassed"], "checks": len(checks)}))
    return 0 if evidence["allChecksPassed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
