"""Artifact classification and maturity boundary enforcement.

This module deliberately does not calculate Design Run maturity.  The G3
``megis.maturity`` evaluator remains the only planned writer of that value.
It only rejects repository manifests that violate the v3 classification
contract or cannot prove evaluator provenance for a Design Run maturity.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Iterable


ARTIFACT_CLASSIFICATIONS = frozenset(
    {
        "DESIGN_RUN",
        "FEASIBILITY_SPIKE",
        "UX_DEMO",
        "BENCHMARK_CASE",
        "TEST_FIXTURE",
    }
)
MATURITY_STATES = frozenset(
    {"DRAFT", "CONCEPT", "PROTOTYPE", "ENGINEERING_REVIEWED", "RELEASED"}
)
NON_DESIGN_CLASSIFICATIONS = ARTIFACT_CLASSIFICATIONS - {"DESIGN_RUN"}
IGNORED_DIRECTORIES = frozenset(
    {".git", ".venv", ".temp", ".cache", ".pytest_cache", "node_modules", "dist"}
)


@dataclass(frozen=True)
class ManifestIssue:
    path: Path
    code: str
    message: str

    def render(self, root: Path | None = None) -> str:
        display_path = self.path
        if root is not None:
            try:
                display_path = self.path.relative_to(root)
            except ValueError:
                pass
        return f"{display_path.as_posix()}: [{self.code}] {self.message}"


def discover_manifests(root: Path) -> list[Path]:
    """Find every repository ``manifest.json`` without following links."""

    root = root.resolve()
    manifests: list[Path] = []
    for current, directories, filenames in os.walk(root, followlinks=False):
        directories[:] = sorted(
            name
            for name in directories
            if name not in IGNORED_DIRECTORIES
            and not (Path(current) / name).is_symlink()
        )
        if "manifest.json" in filenames:
            manifests.append(Path(current) / "manifest.json")
    return sorted(manifests)


def _issue(path: Path, code: str, message: str) -> ManifestIssue:
    return ManifestIssue(path=path.resolve(), code=code, message=message)


def validate_manifest(document: Any, path: Path) -> list[ManifestIssue]:
    """Validate the v3 classification/maturity contract for one manifest."""

    if not isinstance(document, dict):
        return [_issue(path, "MANIFEST_NOT_OBJECT", "manifest 根節點必須是 JSON object")]

    issues: list[ManifestIssue] = []
    if "classification" not in document:
        issues.append(_issue(path, "CLASSIFICATION_MISSING", "缺少 classification"))
        return issues

    classification = document["classification"]
    if classification not in ARTIFACT_CLASSIFICATIONS:
        issues.append(
            _issue(
                path,
                "CLASSIFICATION_UNKNOWN",
                f"classification 必須是已核准值，實際為 {classification!r}",
            )
        )
        return issues

    if "maturity" not in document:
        issues.append(_issue(path, "MATURITY_MISSING", "缺少明確的 maturity 欄位"))
        return issues

    maturity = document["maturity"]
    if classification in NON_DESIGN_CLASSIFICATIONS:
        if maturity is not None:
            issues.append(
                _issue(
                    path,
                    "NON_DESIGN_MATURITY",
                    f"{classification} 不可具有工程成熟度；maturity 必須為 null",
                )
            )
        if "maturity_evaluation" in document:
            issues.append(
                _issue(
                    path,
                    "NON_DESIGN_EVALUATION",
                    f"{classification} 不可宣稱 maturity evaluator 結果",
                )
            )
        return issues

    if maturity not in MATURITY_STATES:
        issues.append(
            _issue(
                path,
                "DESIGN_RUN_MATURITY_INVALID",
                "DESIGN_RUN maturity 必須是正式成熟度狀態且不可為 null",
            )
        )

    evaluation = document.get("maturity_evaluation")
    if not isinstance(evaluation, dict):
        issues.append(
            _issue(
                path,
                "EVALUATOR_PROVENANCE_MISSING",
                "DESIGN_RUN 必須附 maturity_evaluation，證明成熟度由 evaluator 計算",
            )
        )
    else:
        if not isinstance(evaluation.get("evaluator_version"), str) or not evaluation.get(
            "evaluator_version"
        ):
            issues.append(
                _issue(path, "EVALUATOR_VERSION_MISSING", "缺少非空 evaluator_version")
            )
        digest = evaluation.get("inputs_digest")
        if not isinstance(digest, str) or len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            issues.append(
                _issue(path, "EVALUATOR_INPUT_DIGEST_INVALID", "inputs_digest 必須是 64 位小寫 SHA-256")
            )
        if not isinstance(evaluation.get("blocking_reasons"), list):
            issues.append(
                _issue(path, "BLOCKING_REASONS_INVALID", "blocking_reasons 必須是 array")
            )
    return issues


def verify_repository_manifests(root: Path) -> tuple[list[Path], list[ManifestIssue]]:
    manifests = discover_manifests(root)
    issues: list[ManifestIssue] = []
    for path in manifests:
        try:
            document = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            issues.append(_issue(path, "MANIFEST_UNREADABLE", str(error)))
            continue
        issues.extend(validate_manifest(document, path))
    return manifests, issues


def render_issues(issues: Iterable[ManifestIssue], root: Path) -> str:
    return "\n".join(issue.render(root) for issue in issues)
