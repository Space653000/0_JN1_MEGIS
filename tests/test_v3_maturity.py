import json
from pathlib import Path

from jsonschema import Draft202012Validator
import pytest

from megis.governance import discover_manifests, validate_manifest, verify_repository_manifests


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "v3" / "artifact-classification.schema.json"


def _codes(document: object) -> set[str]:
    return {issue.code for issue in validate_manifest(document, Path("manifest.json"))}


def test_repository_manifests_satisfy_classification_contract() -> None:
    manifests, issues = verify_repository_manifests(ROOT)

    assert [path.relative_to(ROOT).as_posix() for path in manifests] == [
        "artifacts/g0-cad/manifest.json"
    ]
    assert issues == []

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    for manifest in manifests:
        validator.validate(json.loads(manifest.read_text(encoding="utf-8-sig")))


@pytest.mark.parametrize("classification", ["FEASIBILITY_SPIKE", "UX_DEMO", "BENCHMARK_CASE", "TEST_FIXTURE"])
def test_non_design_artifacts_must_have_null_maturity(classification: str) -> None:
    assert _codes({"classification": classification, "maturity": None}) == set()
    assert _codes({"classification": classification, "maturity": "PROTOTYPE"}) == {
        "NON_DESIGN_MATURITY"
    }


def test_missing_and_unknown_classification_are_rejected() -> None:
    assert _codes({"maturity": None}) == {"CLASSIFICATION_MISSING"}
    assert _codes({"classification": "GOLDEN_EXPECTATION_ONLY", "maturity": None}) == {
        "CLASSIFICATION_UNKNOWN"
    }


def test_design_run_requires_evaluator_provenance() -> None:
    assert _codes({"classification": "DESIGN_RUN", "maturity": "PROTOTYPE"}) == {
        "EVALUATOR_PROVENANCE_MISSING"
    }
    valid = {
        "classification": "DESIGN_RUN",
        "maturity": "DRAFT",
        "maturity_evaluation": {
            "evaluator_version": "3.0.0",
            "inputs_digest": "a" * 64,
            "blocking_reasons": ["G3 evaluator is not implemented in this fixture"],
        },
    }
    assert _codes(valid) == set()


def test_design_run_rejects_null_maturity_and_invalid_provenance() -> None:
    document = {
        "classification": "DESIGN_RUN",
        "maturity": None,
        "maturity_evaluation": {
            "evaluator_version": "",
            "inputs_digest": "not-a-sha",
            "blocking_reasons": "none",
        },
    }
    assert _codes(document) == {
        "DESIGN_RUN_MATURITY_INVALID",
        "EVALUATOR_VERSION_MISSING",
        "EVALUATOR_INPUT_DIGEST_INVALID",
        "BLOCKING_REASONS_INVALID",
    }


def test_scanner_finds_nested_manifests_and_ignores_cache_directories(tmp_path: Path) -> None:
    good = tmp_path / "artifacts" / "case" / "manifest.json"
    good.parent.mkdir(parents=True)
    good.write_text('{"classification":"TEST_FIXTURE","maturity":null}', encoding="utf-8")
    ignored = tmp_path / "node_modules" / "package" / "manifest.json"
    ignored.parent.mkdir(parents=True)
    ignored.write_text("not json", encoding="utf-8")

    runs_ignored = tmp_path / ".runs" / "clean-checkout" / "manifest.json"
    runs_ignored.parent.mkdir(parents=True)
    runs_ignored.write_text("not json", encoding="utf-8")

    assert discover_manifests(tmp_path) == [good]
    manifests, issues = verify_repository_manifests(tmp_path)
    assert manifests == [good]
    assert issues == []


def test_scanner_reports_unreadable_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{", encoding="utf-8")

    _, issues = verify_repository_manifests(tmp_path)
    assert [issue.code for issue in issues] == ["MANIFEST_UNREADABLE"]
