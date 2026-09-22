from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from scripts.record_g6_a11y_manual import (
    RecorderError,
    build_record,
    collect_record,
    write_record,
)
from scripts.verify_g6_a11y_manual import (
    KEYBOARD_CHECK_IDS,
    ROOT,
    SCREEN_READER_CHECK_IDS,
    evaluate_document,
)


def _results(value: str = "passed") -> dict[str, tuple[str, str]]:
    notes = "人工觀察完成。" if value == "passed" else "發現焦點問題。"
    return {
        **{f"keyboard:{check_id}": (value, notes) for check_id in KEYBOARD_CHECK_IDS},
        **{f"screenReader:{check_id}": (value, notes) for check_id in SCREEN_READER_CHECK_IDS},
    }


def _record(results: dict[str, tuple[str, str]] | None = None) -> dict:
    return build_record(
        reviewer_name="Human Reviewer",
        performed_at="2026-09-23T06:00:00+08:00",
        operating_system="Windows 11",
        browser="Chrome",
        browser_version="140.0",
        assistive_technology="NVDA",
        assistive_technology_version="2026.1",
        results=results or _results(),
    )


def test_all_passed_record_is_schema_valid_and_closure_eligible() -> None:
    record = _record()
    summary = evaluate_document(record)
    assert summary["closureEligible"] is True
    assert record["keyboard"]["status"] == "passed"
    assert record["screenReader"]["status"] == "passed"


def test_failure_is_preserved_and_prevents_closure() -> None:
    results = _results()
    results["keyboard:skip-link"] = ("failed", "Enter did not move focus.")
    record = _record(results)
    summary = evaluate_document(record)
    assert summary["closureEligible"] is False
    assert summary["failedChecks"] == 1
    assert record["keyboard"]["status"] == "failed"


@pytest.mark.parametrize("result", ["pending", "yes", "", "PASSED"])
def test_recorder_rejects_noncanonical_results(result: str) -> None:
    results = _results()
    results["keyboard:skip-link"] = (result, "note")
    with pytest.raises(RecorderError, match="passed or failed"):
        _record(results)


def test_failed_result_requires_human_notes() -> None:
    results = _results()
    results["keyboard:skip-link"] = ("failed", "  ")
    with pytest.raises(RecorderError, match="requires notes"):
        _record(results)


def test_writer_rejects_paths_outside_workspace() -> None:
    with pytest.raises(RecorderError, match="outside workspace"):
        write_record(_record(), ROOT.parent / "manual-audit.json")


def test_writer_refuses_to_overwrite_existing_record(tmp_path: Path) -> None:
    output = tmp_path / "manual-audit.json"
    write_record(_record(), output)
    assert json.loads(output.read_text(encoding="utf-8"))["evidenceType"] == "human_manual_audit"
    with pytest.raises(RecorderError, match="already exists"):
        write_record(_record(), output)


def test_interactive_collection_requires_explicit_human_attestation() -> None:
    responses = iter(["Human Reviewer", "Windows 11", "Chrome", "140", "NVDA", "2026.1", "NO"])
    with pytest.raises(RecorderError, match="attestation was not accepted"):
        collect_record(input_fn=lambda _: next(responses), now_fn=lambda: datetime.now(timezone.utc))
