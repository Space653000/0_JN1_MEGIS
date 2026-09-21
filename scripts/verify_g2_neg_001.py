"""Verify G2-NEG-001 boundary and negative geometry corpus.

Runs every boundary case through the CadQuery backend and asserts kernel-valid
geometry with no undershoot (a cap value must be produced, not silently
clamped). Runs every negative case and asserts it returns the expected error
code with zero silent successes. Over-envelope inputs must surface MEGIS-ENV-001
and must report the original out-of-range values, proving invariant 18
(no silent clamp). No engineering artifacts are exported; geometry stays in
memory, so only verification.json is written under artifacts/g2-neg-001/.
"""

from __future__ import annotations

import json
from math import isfinite
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.adapters import CadQueryBackend  # noqa: E402
from megis.contracts import load_engineering_ir  # noqa: E402
from megis.errors import MegisError  # noqa: E402
from megis.geometry import GeometryContractError  # noqa: E402
from megis.geometry.corpus import (  # noqa: E402
    apply_case,
    base_dimensions_mm,
    execute_case,
    load_corpus,
)

TOLERANCE_MM = 1e-6


class Evidence:
    """Collect check results and keep the record machine-readable."""

    def __init__(self) -> None:
        self.checks: list[dict] = []
        self.failed = False

    def expect(self, name: str, condition: bool, detail: object) -> None:
        if not condition:
            self.failed = True
        self.checks.append(
            {
                "name": name,
                "passed": bool(condition),
                "detail": detail,
            }
        )


def error_code(error: BaseException) -> str:
    if isinstance(error, MegisError):
        return error.code.code
    if isinstance(error, GeometryContractError):
        return str(error.code)
    return type(error).__name__


def bbox_mm(result: object) -> list[float]:
    return [result.bounding_box_mm.width, result.bounding_box_mm.depth, result.bounding_box_mm.height]


def dims_close(actual: list[float], expected: list[float]) -> bool:
    return all(
        isfinite(value) and abs(value - expected[index]) <= TOLERANCE_MM
        for index, value in enumerate(actual)
    )


def verify() -> dict:
    golden_path = ROOT / "contracts/g1/golden/reference-fixture.json"
    golden = load_engineering_ir(golden_path)
    corpus = load_corpus()
    backend = CadQueryBackend()
    evidence = Evidence()

    boundary_records: list[dict] = []
    for case in corpus["boundaryCases"]:
        result = execute_case(golden, case, backend)
        if case["operation"] == "fixture_base":
            expected_dims = base_dimensions_mm(apply_case(golden, case))
            actual_dims = bbox_mm(result)
            passed = bool(result.valid) and dims_close(actual_dims, expected_dims)
            detail = {
                "expectedDimsMm": expected_dims,
                "actualBboxMm": actual_dims,
                "solidCount": result.solid_count,
                "valid": result.valid,
            }
        else:
            clearances = (
                result.radial_fastener_clearance_mm,
                result.pcb_side_clearance_mm,
                result.pcb_top_clearance_mm,
            )
            passed = (
                bool(result.valid)
                and bool(result.usb_cutout_open)
                and result.unintended_interference_volume_mm3 <= 1e-7
                and all(isfinite(value) and value > 0 for value in clearances)
            )
            detail = {
                "valid": result.valid,
                "usbCutoutOpen": result.usb_cutout_open,
                "unintendedInterferenceVolumeMm3": result.unintended_interference_volume_mm3,
                "clearancesMm": list(clearances),
                "solidCount": result.solid_count,
            }
        evidence.expect(
            f"boundary {case['caseId']} {case['label']}",
            passed,
            detail,
        )
        boundary_records.append(
            {
                "caseId": case["caseId"],
                "operation": case["operation"],
                "label": case["label"],
                "passed": passed,
                **detail,
            }
        )

    negative_records: list[dict] = []
    silent_success = 0
    for case in corpus["negativeCases"]:
        expected_code = case["expected"]["code"]
        try:
            execute_case(golden, case, backend)
        except (MegisError, GeometryContractError) as error:
            actual_code = error_code(error)
            not_clamped = False
            reported_input: list[float] | None = None
            if (
                expected_code == "MEGIS-ENV-001"
                and isinstance(error, MegisError)
                and case["expected"].get("notClamped")
            ):
                detail = error.error_object.engineer_detail
                mutated_dims = base_dimensions_mm(apply_case(golden, case))
                reported_input = [
                    float(detail["width_mm"]),
                    float(detail["depth_mm"]),
                    float(detail["height_mm"]),
                ]
                not_clamped = reported_input == mutated_dims
            code_matches = actual_code == expected_code
            evidence.expect(
                f"negative {case['caseId']} {case['label']} -> {expected_code}",
                code_matches and (not_clamped if case["expected"].get("notClamped") else True),
                {
                    "expectedCode": expected_code,
                    "actualCode": actual_code,
                    "notClamped": not_clamped,
                    "reportedInputMm": reported_input,
                },
            )
            negative_records.append(
                {
                    "caseId": case["caseId"],
                    "operation": case["operation"],
                    "label": case["label"],
                    "expectedCode": expected_code,
                    "actualCode": actual_code,
                    "codeMatches": code_matches,
                    "notClamped": not_clamped,
                    "reportedInputMm": reported_input,
                }
            )
        else:
            silent_success += 1
            evidence.expect(
                f"negative {case['caseId']} {case['label']} must not silently succeed",
                False,
                {"expectedCode": expected_code, "actual": "success"},
            )
            negative_records.append(
                {
                    "caseId": case["caseId"],
                    "operation": case["operation"],
                    "label": case["label"],
                    "expectedCode": expected_code,
                    "actualCode": "SUCCESS",
                    "codeMatches": False,
                    "notClamped": False,
                    "reportedInputMm": None,
                }
            )

    boundary_total = len(boundary_records)
    boundary_passed = sum(1 for record in boundary_records if record["passed"])
    negative_total = len(negative_records)
    negative_errored = negative_total - silent_success
    evidence.expect(
        "boundary corpus has at least 10 cases and all pass",
        boundary_total >= 10 and boundary_passed == boundary_total,
        {"total": boundary_total, "passed": boundary_passed},
    )
    evidence.expect(
        "negative corpus has at least 10 cases and all return expected errors",
        negative_total >= 10 and negative_errored == negative_total and silent_success == 0,
        {"total": negative_total, "errored": negative_errored, "silentSuccess": silent_success},
    )
    evidence.expect(
        "over-envelope cases report original values, not clamped caps",
        all(
            record.get("notClamped")
            for record in negative_records
            if record.get("expectedCode") == "MEGIS-ENV-001"
        ),
        {
            "envCases": sum(
                1 for record in negative_records if record.get("expectedCode") == "MEGIS-ENV-001"
            )
        },
    )

    return {
        "schemaVersion": "1.0.0",
        "workItem": "G2-NEG-001",
        "input": {
            "corpus": "contracts/g2/golden/geometry-corpus.json",
            "baseDocument": "contracts/g1/golden/reference-fixture.json",
            "envelope": "config/envelope/envelope.yaml",
        },
        "backend": {
            "backend_id": backend.capabilities().backend_id,
            "backend_version": backend.capabilities().backend_version,
        },
        "summary": {
            "boundaryTotal": boundary_total,
            "boundaryPassed": boundary_passed,
            "negativeTotal": negative_total,
            "negativeErrored": negative_errored,
            "silentSuccess": silent_success,
        },
        "boundary": boundary_records,
        "negative": negative_records,
        "checks": evidence.checks,
        "allChecksPassed": not evidence.failed,
        "engineeringArtifactGenerated": False,
        "releaseArtifactGenerated": False,
    }


if __name__ == "__main__":
    result = verify()
    out = ROOT / "artifacts" / "g2-neg-001" / "verification.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if not result["allChecksPassed"]:
        sys.exit(1)
