from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "scripts" / "verify-control-plane.mjs"


def _load_queue() -> dict:
    return json.loads((ROOT / "execution" / "WORK_QUEUE.yaml").read_text(encoding="utf-8"))


def _write_fixture(root: Path, queue: dict) -> None:
    copies = [
        "execution/BLOCKERS.yaml",
        "execution/schemas/work-queue.schema.json",
        "execution/schemas/v3-required-work-items.json",
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
        "docs/UI0_ACCEPTANCE.md",
        "docs/decisions/ADR-0001-adopt-v3-blueprint.md",
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
        destination.touch()


def _run_verifier(root: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["MEGIS_REPO_ROOT"] = str(root)
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

