"""Interactively collect human-authored G6 accessibility audit evidence."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Callable

try:
    from scripts.verify_g6_a11y_manual import (
        EvidenceError,
        KEYBOARD_CHECK_IDS,
        ROOT,
        SCREEN_READER_CHECK_IDS,
        TEMPLATE_PATH,
        _inside_workspace,
        evaluate_document,
    )
except ModuleNotFoundError:  # Direct execution: python scripts/record_g6_a11y_manual.py
    from verify_g6_a11y_manual import (  # type: ignore[no-redef]
        EvidenceError,
        KEYBOARD_CHECK_IDS,
        ROOT,
        SCREEN_READER_CHECK_IDS,
        TEMPLATE_PATH,
        _inside_workspace,
        evaluate_document,
    )


ATTESTATION = "I personally performed this manual accessibility audit."
DEFAULT_OUTPUT = ROOT / "artifacts" / "g6-a11y-001" / "manual-audit.json"
CHECK_LABELS = {
    "keyboard:skip-link": "Skip link 可見、可啟用，且焦點移至主要內容",
    "keyboard:desktop-navigation": "桌面導覽可依預期順序以鍵盤操作",
    "keyboard:mobile-navigation": "行動版導覽可開啟、巡覽與關閉",
    "keyboard:design-form": "設計表單欄位、錯誤與送出流程可用鍵盤完成",
    "keyboard:review-flow": "Review 流程的控制項與焦點狀態可用鍵盤辨識",
    "keyboard:progress-disclosure": "進度頁揭露區塊可用鍵盤操作",
    "screenReader:landmarks": "頁面 landmarks 與標題階層可正確辨識",
    "screenReader:design-form": "設計表單標籤、說明與錯誤訊息可正確朗讀",
    "screenReader:review-unknowns": "Review 未知項目與狀態可正確朗讀",
    "screenReader:run-announcements": "執行狀態變更具可理解的即時宣告",
    "screenReader:results-boundaries": "結果與 Synthetic demo 邊界可正確理解",
    "screenReader:progress-table": "進度表格標題、欄列關係與狀態可辨識",
}


class RecorderError(ValueError):
    """Raised when a manual record cannot be collected or safely written."""


def _required(value: str, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise RecorderError(f"{field} is required")
    return normalized


def _result_keys() -> tuple[str, ...]:
    return tuple(
        [f"keyboard:{check_id}" for check_id in KEYBOARD_CHECK_IDS]
        + [f"screenReader:{check_id}" for check_id in SCREEN_READER_CHECK_IDS]
    )


def build_record(
    *,
    reviewer_name: str,
    performed_at: str,
    operating_system: str,
    browser: str,
    browser_version: str,
    assistive_technology: str,
    assistive_technology_version: str,
    results: dict[str, tuple[str, str]],
) -> dict[str, Any]:
    """Build and validate a complete record from explicit human observations."""

    expected_keys = set(_result_keys())
    actual_keys = set(results)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unexpected = sorted(actual_keys - expected_keys)
        raise RecorderError(f"results must contain the exact 12 checks; missing={missing}, unexpected={unexpected}")

    reviewer = {"name": _required(reviewer_name, "reviewer name"), "attestation": ATTESTATION}
    performed_at = _required(performed_at, "performed at")
    browser_environment = {
        "operatingSystem": _required(operating_system, "operating system"),
        "browser": _required(browser, "browser"),
        "browserVersion": _required(browser_version, "browser version"),
    }
    screen_reader_environment = {
        **browser_environment,
        "assistiveTechnology": _required(assistive_technology, "assistive technology"),
        "assistiveTechnologyVersion": _required(
            assistive_technology_version, "assistive technology version"
        ),
    }

    document = deepcopy(json.loads(TEMPLATE_PATH.read_text(encoding="utf-8")))
    for section_name, environment in (
        ("keyboard", browser_environment),
        ("screenReader", screen_reader_environment),
    ):
        section = document[section_name]
        section["reviewer"] = reviewer.copy()
        section["performedAt"] = performed_at
        section["environment"] = environment
        section_failed = False
        for check in section["checks"]:
            result, notes = results[f"{section_name}:{check['id']}"]
            if result not in {"passed", "failed"}:
                raise RecorderError(f"{section_name}:{check['id']} result must be passed or failed")
            normalized_notes = notes.strip()
            if result == "failed" and not normalized_notes:
                raise RecorderError(f"{section_name}:{check['id']} failed result requires notes")
            check["result"] = result
            check["notes"] = normalized_notes
            section_failed = section_failed or result == "failed"
        section["status"] = "failed" if section_failed else "passed"

    try:
        evaluate_document(document)
    except (EvidenceError, OSError, json.JSONDecodeError) as exc:
        raise RecorderError(str(exc)) from exc
    return document


def _prompt_result(input_fn: Callable[[str], str], key: str) -> tuple[str, str]:
    while True:
        result = input_fn(f"[{key}] {CHECK_LABELS[key]}\n結果（passed/failed）：").strip()
        if result not in {"passed", "failed"}:
            print("請只輸入 passed 或 failed。")
            continue
        notes = input_fn("人工觀察備註（failed 必填）：").strip()
        if result == "failed" and not notes:
            print("failed 結果必須填寫觀察備註。")
            continue
        return result, notes


def collect_record(
    *,
    input_fn: Callable[[str], str] = input,
    now_fn: Callable[[], datetime] = datetime.now,
) -> dict[str, Any]:
    """Collect a record interactively; the operator must accept the attestation."""

    reviewer_name = input_fn("實際執行稽核者姓名：")
    operating_system = input_fn("作業系統與版本：")
    browser = input_fn("瀏覽器名稱：")
    browser_version = input_fn("瀏覽器版本：")
    assistive_technology = input_fn("螢幕閱讀器名稱：")
    assistive_technology_version = input_fn("螢幕閱讀器版本：")
    acceptance = input_fn(
        f"請確認聲明：{ATTESTATION}\n若確為本人執行，請輸入 YES："
    ).strip()
    if acceptance != "YES":
        raise RecorderError("human attestation was not accepted")

    results = {key: _prompt_result(input_fn, key) for key in _result_keys()}
    performed_at = now_fn().astimezone().isoformat(timespec="seconds")
    return build_record(
        reviewer_name=reviewer_name,
        performed_at=performed_at,
        operating_system=operating_system,
        browser=browser,
        browser_version=browser_version,
        assistive_technology=assistive_technology,
        assistive_technology_version=assistive_technology_version,
        results=results,
    )


def write_record(document: dict[str, Any], output_path: Path) -> Path:
    """Write once inside the repository after fail-closed validation."""

    try:
        resolved = _inside_workspace(output_path)
        summary = evaluate_document(document)
    except (EvidenceError, OSError, json.JSONDecodeError) as exc:
        raise RecorderError(str(exc)) from exc
    if summary["pendingChecks"]:
        raise RecorderError("manual audit record must contain all 12 completed checks")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    try:
        with resolved.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(document, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except FileExistsError as exc:
        raise RecorderError(f"output already exists and will not be overwritten: {resolved}") from exc
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    print("G6-A11Y-001 人工稽核紀錄器：僅限實際執行鍵盤與螢幕閱讀器稽核的人員填寫。")
    print("此工具不會產生工程成品，也不會把自動化或 Agent 操作冒充成人工證據。")
    try:
        output_path = write_record(collect_record(), args.output)
    except (RecorderError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"workItem": "G6-A11Y-001", "status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"workItem": "G6-A11Y-001", "status": "recorded", "output": str(output_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
