import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_comsol_out_of_scope_decision_matches_inventory() -> None:
    inventory = json.loads(
        (ROOT / "artifacts" / "g0-sim" / "inventory.json").read_text(encoding="utf-8-sig")
    )
    decision = json.loads(
        (ROOT / "environment" / "comsol.decision.json").read_text(encoding="utf-8")
    )

    assert inventory["workItem"] == "G0-SIM-001"
    assert inventory["scope"] == "read_only_local_inventory"
    assert inventory["summary"] == {
        "installationDetected": False,
        "licenseConfigurationDetected": False,
        "batchExecutableDetected": False,
        "decision": "out_of_scope",
        "blocksCoreGate": False,
    }
    assert not any(item["found"] for item in inventory["commands"])
    assert not any(item["exists"] for item in inventory["standardPaths"])
    assert not any(item["exists"] for item in inventory["registryKeys"])
    assert not any(item["present"] for item in inventory["environmentVariables"])
    assert inventory["privacy"]["environmentVariableValuesCaptured"] is False
    assert inventory["privacy"]["licenseContentsCaptured"] is False

    assert decision["decision"] == inventory["summary"]["decision"]
    assert decision["blocksCoreGate"] is False
    assert len(decision["prohibitedClaims"]) == 3

