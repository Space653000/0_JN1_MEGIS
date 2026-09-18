import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFICATION_PATH = ROOT / "artifacts" / "g0-dec-001" / "verification.json"
REGISTER_PATH = ROOT / "execution" / "decisions" / "g0-decisions.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_g0_dec_001_verification_record_lists_all_decisions() -> None:
    record = _load(VERIFICATION_PATH)
    assert record["schemaVersion"] == "1.0.0"
    assert record["workItem"] == "G0-DEC-001"
    assert record["evidenceLevel"] == "E4"
    assert record["decisionRegister"]["decisionIds"] == [f"D{index}" for index in range(1, 10)]
    assert record["decisionRegister"]["adrCount"] == 9
    assert record["decisionRegister"]["evidencePathsExist"] is True


def test_g0_dec_001_verification_matches_decision_register() -> None:
    record = _load(VERIFICATION_PATH)
    register = _load(REGISTER_PATH)
    register_ids = [decision["id"] for decision in register["decisions"]]
    assert record["decisionRegister"]["decisionIds"] == register_ids
    for decision in register["decisions"]:
        entry = next(
            (item for item in record["perDecision"] if item["id"] == decision["id"]),
            None,
        )
        assert entry is not None, decision["id"]
        assert entry["adr"] == decision["adr"]
        assert entry["evidenceCount"] == len(decision["evidence"])


def test_g0_dec_001_verification_states_honest_implementation_boundary() -> None:
    record = _load(VERIFICATION_PATH)
    boundary = record["honestImplementationBoundary"]
    assert set(boundary["enforced"]) == {"D1", "D2", "D4", "D7"}
    assert set(boundary["partiallyEnforced"]) == {"D3", "D5", "D6"}
    assert set(boundary["policyOnly"]) == {"D8", "D9"}
    assert boundary["decisionsDoNotCloseFollowUpWorkItems"] is True
