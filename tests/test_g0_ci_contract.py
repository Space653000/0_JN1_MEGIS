import json
from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_baseline_workflow_is_read_only_and_pinned() -> None:
    workflow_path = ROOT / ".github" / "workflows" / "baseline-ci.yml"
    text = workflow_path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)

    assert isinstance(workflow, dict)
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["jobs"]["verify"]["runs-on"] == "windows-latest"
    assert workflow["jobs"]["verify"]["timeout-minutes"] == 35
    assert "persist-credentials: false" in text
    action_refs = re.findall(r"uses: actions/[^@]+@([^\s]+)", text)
    assert len(action_refs) == 3
    assert all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in action_refs)
    assert "github.workspace" in text
    assert "python -m venv .venv" in text
    assert "-PythonExecutable .\\.venv\\Scripts\\python.exe" in text
    assert "run-baseline-ci.ps1" in text


def test_local_baseline_evidence_is_green() -> None:
    evidence = json.loads(
        (ROOT / "artifacts" / "g0-ci" / "baseline-verification.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["workItem"] == "G0-CI-001"
    assert evidence["toolchain"] == {
        "python": "3.11.9",
        "node": "24.17.0",
        "pip": "26.2.1",
        "npm": "11.13.0",
    }
    assert all(
        result == "passed" or result["status"] == "passed"
        for result in evidence["results"].values()
    )
    assert evidence["engineeringRelease"] is False
