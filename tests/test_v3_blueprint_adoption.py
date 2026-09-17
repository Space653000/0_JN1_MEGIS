from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "scripts" / "verify-control-plane.mjs"


def _load_queue() -> dict:
    return json.loads((ROOT / "execution" / "WORK_QUEUE.yaml").read_text(encoding="utf-8"))


def _write_fixture(root: Path, queue: dict) -> None:
    copies = [
        "AGENTS.md",
        "docs/DECISIONS.md",
        "docs/FINGERPRINT_POLICY.md",
        "docs/UI0_ACCEPTANCE.md",
        "docs/decisions/ADR-0001-adopt-v3-blueprint.md",
        "execution/BLOCKERS.yaml",
        "execution/schemas/work-queue.schema.json",
        "execution/schemas/agent-claim.schema.json",
        "execution/schemas/g0-decisions.schema.json",
        "execution/schemas/v3-required-work-items.json",
        "execution/decisions/g0-decisions.json",
        "config/fingerprint/policy-1.0.0.json",
        "schemas/v3/fingerprint-policy.schema.json",
        "execution/AGENT_CLAIM.json",
        "execution/V3_MIGRATION.json",
        "execution/PROJECT_STATE.md",
        "README.md",
    ]
    for relative in copies:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / relative).read_bytes())

    (root / "execution" / "WORK_QUEUE.yaml").write_text(
        json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for relative in (
        "execution/LAST_VERIFICATION.json",
        "MEGIS_Blueprint/MEGIS_Mechanical Engineering Generative Intelligence System — v3.0-claude-code.md",
    ):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("fixture\n", encoding="utf-8")

    evidence_paths = {
        path
        for item in queue["workItems"]
        for path in (
            item["evidence"]
            + [
                evidence
                for result in item["acceptanceResults"]
                for evidence in result["evidence"]
            ]
        )
    }
    for relative in evidence_paths:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = ROOT / relative
        if source.is_file() and source.suffix.lower() == ".md":
            destination.write_bytes(source.read_bytes())
        else:
            destination.touch()


def _run_verifier(root: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["MEGIS_REPO_ROOT"] = str(root)
    environment["MEGIS_SKIP_GIT_HISTORY_CHECK"] = "1"
    return subprocess.run(
        ["node", str(VERIFIER)],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_v3_required_work_item_manifest_matches_queue() -> None:
    queue = _load_queue()
    required = json.loads(
        (ROOT / "execution" / "schemas" / "v3-required-work-items.json").read_text(
            encoding="utf-8"
        )
    )

    assert len(required["requiredWorkItemIds"]) == 74
    assert set(required["requiredWorkItemIds"]) == {
        item["id"] for item in queue["workItems"]
    }
    assert queue["schemaVersion"] == "1.1.0"


def test_verifier_accepts_current_v3_migration_state(tmp_path: Path) -> None:
    _write_fixture(tmp_path, _load_queue())

    result = _run_verifier(tmp_path)

    assert result.returncode == 0, result.stderr
    assert "74 work items" in result.stdout


def test_control_plane_schema_1_1_is_backward_compatible() -> None:
    queue = _load_queue()
    schema = json.loads(
        (ROOT / "execution" / "schemas" / "work-queue.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validator = Draft202012Validator(schema)

    validator.validate(queue)
    legacy = deepcopy(queue)
    legacy["schemaVersion"] = "1.0.0"
    for item in legacy["workItems"]:
        for field in (
            "owner_role",
            "requires_user_decision",
            "evidence_level_required",
            "review",
            "risk_refs",
            "blueprint_ref",
        ):
            item.pop(field, None)
    validator.validate(legacy)


def test_agent_claim_matches_current_work_item_and_schema() -> None:
    queue = _load_queue()
    claim = json.loads(
        (ROOT / "execution" / "AGENT_CLAIM.json").read_text(encoding="utf-8")
    )
    schema = json.loads(
        (ROOT / "execution" / "schemas" / "agent-claim.schema.json").read_text(
            encoding="utf-8"
        )
    )

    Draft202012Validator(schema).validate(claim)
    assert claim["work_item"] == queue["currentWorkItem"]


def test_verifier_rejects_a_missing_v3_work_item(tmp_path: Path) -> None:
    queue = deepcopy(_load_queue())
    queue["workItems"] = [
        item for item in queue["workItems"] if item["id"] != "G6-AI-004"
    ]
    _write_fixture(tmp_path, queue)

    result = _run_verifier(tmp_path)

    assert result.returncode == 1
    assert "Missing blueprint work item: G6-AI-004" in result.stderr


def test_verifier_rejects_reopening_a_completed_v2_item(tmp_path: Path) -> None:
    queue = deepcopy(_load_queue())
    migration = next(item for item in queue["workItems"] if item["id"] == "G1-MIG-001")
    migration["status"] = "planned"
    _write_fixture(tmp_path, queue)

    result = _run_verifier(tmp_path)

    assert result.returncode == 1
    assert "G1-MIG-001 changed after v3 adoption baseline" in result.stderr


def test_verifier_rejects_claim_mismatch(tmp_path: Path) -> None:
    queue = _load_queue()
    _write_fixture(tmp_path, queue)
    claim_path = tmp_path / "execution" / "AGENT_CLAIM.json"
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    claim["work_item"] = "G2-CAD-004"
    claim_path.write_text(json.dumps(claim), encoding="utf-8")

    result = _run_verifier(tmp_path)

    assert result.returncode == 1
    assert "AGENT_CLAIM work_item does not match currentWorkItem" in result.stderr


def test_verifier_rejects_dependency_cycle(tmp_path: Path) -> None:
    queue = deepcopy(_load_queue())
    solver = next(item for item in queue["workItems"] if item["id"] == "G7-SOL-001")
    solver["dependsOn"] = ["G7-REV-001"]
    _write_fixture(tmp_path, queue)

    result = _run_verifier(tmp_path)

    assert result.returncode == 1
    assert "Work item dependency cycle" in result.stderr


def test_document_deferral_expires_when_owner_is_done(tmp_path: Path) -> None:
    queue = deepcopy(_load_queue())
    document_item = next(
        item for item in queue["workItems"] if item["id"] == "V3C-DOC-001"
    )
    document_item["status"] = "done"
    document_item["acceptanceResults"][0]["status"] = "passed"
    document_item["acceptanceResults"][0]["evidence"] = ["README.md"]
    document_item["evidence"] = ["README.md"]
    document_item["verification"] = "passed"
    document_item["commitSha"] = "d8a6ed9598a437a0f7d7cb533f52cf90a8e451c3"
    _write_fixture(tmp_path, queue)

    result = _run_verifier(tmp_path)

    assert result.returncode == 1
    assert "Missing or empty required file: docs/PRODUCT.md" in result.stderr


def test_accepted_gate_deferrals_cannot_become_permanent(tmp_path: Path) -> None:
    queue = _load_queue()
    _write_fixture(tmp_path, queue)
    migration_path = tmp_path / "execution" / "V3_MIGRATION.json"
    migration = json.loads(migration_path.read_text(encoding="utf-8"))
    migration["temporaryDeferrals"]["acceptedGateRetrospectiveReview"] = "V3C-BCR-001"
    migration["temporaryDeferrals"]["acceptedGateSignoff"] = "V3C-BCR-001"
    migration_path.write_text(json.dumps(migration), encoding="utf-8")

    result = _run_verifier(tmp_path)

    assert result.returncode == 1
    assert "G0 is accepted with unfinished work items" in result.stderr
    assert "UI-0A lacks an ACCEPTANCE.md review/sign-off entry" in result.stderr


def test_done_item_cannot_skip_a_required_review(tmp_path: Path) -> None:
    queue = deepcopy(_load_queue())
    adoption = next(
        item for item in queue["workItems"] if item["id"] == "V3C-BCR-001"
    )
    adoption["review"] = {"required": True, "status": "pending", "report": None}
    _write_fixture(tmp_path, queue)

    result = _run_verifier(tmp_path)

    assert result.returncode == 1
    assert "V3C-BCR-001 is done without a passed required review" in result.stderr


def test_done_item_commit_shas_exist_in_repository_history() -> None:
    queue = _load_queue()

    for item in queue["workItems"]:
        if item["status"] != "done":
            continue
        result = subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "-e", f"{item['commitSha']}^{{commit}}"],
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, item["id"]


def test_required_v3_document_inventory_is_present() -> None:
    required = [
        "CLAUDE.md",
        "docs/PRODUCT.md",
        "docs/ARCHITECTURE.md",
        "docs/DECISIONS.md",
        "docs/SUPPORTED_ENVELOPE.md",
        "docs/ACCEPTANCE.md",
        "docs/RISKS.md",
        "docs/OPERATIONS.md",
        "docs/ERROR_CODES.md",
        "docs/RULE_SOURCES.md",
        "docs/research/README.md",
        "execution/handoffs/README.md",
        "execution/reviews/README.md",
        "execution/signoffs/README.md",
        "config/envelope/README.md",
        "tests/golden/README.md",
    ]

    assert [path for path in required if not (ROOT / path).is_file()] == []
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "AGENTS.md" in claude


def test_verifier_rejects_document_without_governance_metadata(tmp_path: Path) -> None:
    _write_fixture(tmp_path, _load_queue())
    decisions = tmp_path / "docs" / "DECISIONS.md"
    decisions.write_text(
        decisions.read_text(encoding="utf-8").replace("Owner：", "Maintainer："),
        encoding="utf-8",
    )

    result = _run_verifier(tmp_path)

    assert result.returncode == 1
    assert "docs/DECISIONS.md lacks documentation governance field: owner" in result.stderr
