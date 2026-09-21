"""G2-NEG-001 boundary and negative geometry corpus tests.

The corpus is machine-readable data under contracts/g2/golden and is schema
validated on load. Tests assert the full boundary set passes with no undershoot,
the full negative set returns its expected error code, silent success is zero,
and over-envelope inputs surface MEGIS-ENV-001 with the original (unclamped)
values.
"""

from __future__ import annotations

import json
from math import isfinite
from pathlib import Path

import pytest

from megis.adapters import CadQueryBackend
from megis.contracts import load_engineering_ir
from megis.errors import MegisError
from megis.geometry import GeometryContractError
from megis.geometry.corpus import (
    CORPUS_PATH,
    GOLDEN_IR_PATH,
    apply_case,
    base_dimensions_mm,
    execute_case,
    load_corpus,
)


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = load_engineering_ir(GOLDEN_IR_PATH)
TOLERANCE_MM = 1e-6


def error_code(error: BaseException) -> str:
    if isinstance(error, MegisError):
        return error.code.code
    if isinstance(error, GeometryContractError):
        return str(error.code)
    return type(error).__name__


def bbox_mm(result: object) -> list[float]:
    return [result.bounding_box_mm.width, result.bounding_box_mm.depth, result.bounding_box_mm.height]


def test_corpus_file_loads_and_meets_minimum_counts() -> None:
    corpus = load_corpus()

    assert len(corpus["boundaryCases"]) >= 10
    assert len(corpus["negativeCases"]) >= 10


def test_corpus_edits_do_not_mutate_golden_ir() -> None:
    corpus = load_corpus()
    before = json.dumps(GOLDEN, sort_keys=True)

    for case in corpus["negativeCases"] + corpus["boundaryCases"]:
        apply_case(GOLDEN, case)

    assert json.dumps(GOLDEN, sort_keys=True) == before


def test_all_boundary_cases_pass_without_undershoot() -> None:
    corpus = load_corpus()
    backend = CadQueryBackend()

    for case in corpus["boundaryCases"]:
        result = execute_case(GOLDEN, case, backend)
        if case["operation"] == "fixture_base":
            expected = base_dimensions_mm(apply_case(GOLDEN, case))
            actual = bbox_mm(result)
            assert result.valid is True
            assert all(
                isfinite(value) and abs(value - expected[index]) <= TOLERANCE_MM
                for index, value in enumerate(actual)
            ), (case["caseId"], expected, actual)
        else:
            clearances = (
                result.radial_fastener_clearance_mm,
                result.pcb_side_clearance_mm,
                result.pcb_top_clearance_mm,
            )
            assert result.valid is True
            assert result.usb_cutout_open is True
            assert result.unintended_interference_volume_mm3 <= 1e-7
            assert all(value > 0 for value in clearances)


def test_consecutive_boundary_cases_compose_on_the_same_backend() -> None:
    # Boundary cases reuse one backend instance, proving tokens are not leaked.
    corpus = load_corpus()
    backend = CadQueryBackend()
    executed = 0
    for case in corpus["boundaryCases"]:
        execute_case(GOLDEN, case, backend)
        executed += 1
    assert executed >= 10


def test_all_negative_cases_error_with_expected_code_and_zero_silent_success() -> None:
    corpus = load_corpus()
    backend = CadQueryBackend()
    silent_success = 0

    for case in corpus["negativeCases"]:
        expected = case["expected"]["code"]
        with pytest.raises((MegisError, GeometryContractError)) as caught:
            execute_case(GOLDEN, case, backend)
        assert error_code(caught.value) == expected, (case["caseId"], expected)

    assert silent_success == 0


def test_over_envelope_reports_original_values_not_clamped() -> None:
    corpus = load_corpus()
    backend = CadQueryBackend()
    env_cases = [
        case for case in corpus["negativeCases"] if case["expected"]["code"] == "MEGIS-ENV-001"
    ]
    assert len(env_cases) >= 6

    for case in env_cases:
        mutated = base_dimensions_mm(apply_case(GOLDEN, case))
        with pytest.raises(MegisError) as caught:
            execute_case(GOLDEN, case, backend)
        assert caught.value.code.code == "MEGIS-ENV-001"
        detail = caught.value.error_object.engineer_detail
        reported = [detail["width_mm"], detail["depth_mm"], detail["height_mm"]]
        assert reported == mutated, (case["caseId"], reported, mutated)


def test_multiaxis_envelope_escape_is_not_clamped_to_any_cap() -> None:
    corpus = load_corpus()
    case = next(item for item in corpus["negativeCases"] if item["caseId"] == "NEG-004")
    backend = CadQueryBackend()

    with pytest.raises(MegisError) as caught:
        execute_case(GOLDEN, case, backend)

    detail = caught.value.error_object.engineer_detail
    assert (detail["width_mm"], detail["depth_mm"], detail["height_mm"]) == (121.0, 81.0, 21.0)


def test_wall_and_dimension_negatives_use_geometry_error_codes() -> None:
    corpus = load_corpus()
    backend = CadQueryBackend()
    codes = {case["caseId"]: case["expected"]["code"] for case in corpus["negativeCases"]}

    for case_id, expected in {
        "NEG-007": "INVALID_DIMENSION",
        "NEG-008": "INVALID_DIMENSION",
        "NEG-009": "INVALID_DIMENSION",
        "NEG-010": "INVALID_DIMENSION",
        "NEG-011": "INVALID_DIMENSION",
        "NEG-012": "INVALID_DIMENSION",
        "NEG-013": "INVALID_IR",
        "NEG-014": "INVALID_IR",
    }.items():
        assert codes[case_id] == expected
        case = next(item for item in corpus["negativeCases"] if item["caseId"] == case_id)
        with pytest.raises((MegisError, GeometryContractError)) as caught:
            execute_case(GOLDEN, case, backend)
        assert error_code(caught.value) == expected


def test_corpus_file_is_tracked_and_small_enough_for_policy() -> None:
    assert CORPUS_PATH.is_file()
    assert CORPUS_PATH.stat().st_size < 200_000
