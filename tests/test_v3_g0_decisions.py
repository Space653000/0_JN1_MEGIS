import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = ROOT / "execution" / "decisions" / "g0-decisions.json"
SCHEMA_PATH = ROOT / "execution" / "schemas" / "g0-decisions.schema.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_decision_register_matches_schema_and_has_exact_d1_through_d9() -> None:
    register = _load(REGISTER_PATH)
    schema = _load(SCHEMA_PATH)

    Draft202012Validator(schema, format_checker=FormatChecker()).validate(register)
    ids = [decision["id"] for decision in register["decisions"]]
    assert ids == [f"D{index}" for index in range(1, 10)]
    assert len(ids) == len(set(ids))


def test_decision_outcomes_match_v3_section_8_1() -> None:
    decisions = {decision["id"]: decision for decision in _load(REGISTER_PATH)["decisions"]}
    assert {decision_id: decision["outcome"] for decision_id, decision in decisions.items()} == {
        "D1": "local_single_user",
        "D2": "out_of_scope",
        "D3": "adapter_no_provider_before_g6",
        "D4": "github_actions_windows_x64_verified_main_push_no_force",
        "D5": "no_customer_company_data_in_repo_or_external_services",
        "D6": "builder_self_review_fresh_session_no_named_engineer",
        "D7": "single_builder_claim_and_same_agent_fresh_session_review",
        "D8": "builder_research_with_citable_public_sources",
        "D9": "design_runs_90_days_golden_permanent",
    }


def test_each_decision_has_an_accepted_adr_and_existing_evidence() -> None:
    for decision in _load(REGISTER_PATH)["decisions"]:
        adr_path = ROOT / decision["adr"]
        assert adr_path.is_file(), decision["id"]
        adr = adr_path.read_text(encoding="utf-8")
        assert f"- 決策 ID：{decision['id']}" in adr
        assert "- 狀態：accepted" in adr
        assert "目的：" in adr
        assert "目前內容：" in adr
        assert "Owner：" in adr
        assert "最後審查 commit：" in adr
        for evidence in decision["evidence"]:
            assert (ROOT / evidence).exists(), f"{decision['id']}: {evidence}"
            assert f"`{evidence}`" in adr, f"{decision['id']}: {evidence}"


def test_decision_index_links_every_adr() -> None:
    index = (ROOT / "docs" / "DECISIONS.md").read_text(encoding="utf-8")
    for decision in _load(REGISTER_PATH)["decisions"]:
        relative = decision["adr"].removeprefix("docs/")
        assert f"({relative})" in index


def test_existing_comsol_and_ci_evidence_agree_with_decisions() -> None:
    decisions = {decision["id"]: decision for decision in _load(REGISTER_PATH)["decisions"]}
    comsol = _load(ROOT / "environment" / "comsol.decision.json")
    workflow = (ROOT / ".github" / "workflows" / "baseline-ci.yml").read_text(encoding="utf-8")

    assert comsol["decision"] == decisions["D2"]["outcome"]
    assert comsol["blocksCoreGate"] is False
    assert "runs-on: windows-latest" in workflow
    assert "branches: [main]" in workflow
    assert "persist-credentials: false" in workflow


def test_policy_only_decisions_do_not_claim_implementation() -> None:
    decisions = {decision["id"]: decision for decision in _load(REGISTER_PATH)["decisions"]}
    assert decisions["D8"]["implementationStatus"] == "policy_only"
    assert "G1-REQ-001" in decisions["D8"]["followUpWorkItems"]
    assert decisions["D9"]["implementationStatus"] == "policy_only"
    assert "V3C-ART-001" in decisions["D9"]["followUpWorkItems"]
