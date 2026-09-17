import json
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "artifact-policy" / "policy-1.0.0.json"
SCHEMA_PATH = ROOT / "schemas" / "v3" / "artifact-policy.schema.json"


def test_artifact_policy_is_versioned_and_schema_valid() -> None:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator(schema).validate(policy)
    assert policy["genericTrackedFileMaxBytes"] == 1024 * 1024
    assert policy["evidenceJson"]["maxFileBytes"] == 50 * 1024
    assert policy["golden"]["maxFileBytes"] == 200 * 1024
    assert policy["golden"]["maxTotalBytes"] == 5 * 1024 * 1024
    assert len(policy["legacyHeavyArtifactAllowlist"]) == 5


def test_artifact_policy_cli_accepts_current_repository() -> None:
    result = subprocess.run(
        ["node", "scripts/verify-artifact-policy.mjs"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Artifact policy passed" in result.stdout
    assert '"heavyArtifactCount":5' in result.stdout
