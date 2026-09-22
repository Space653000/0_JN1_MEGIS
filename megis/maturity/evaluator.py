"""Maturity evaluator implementing blueprint section 1.4 (G3-MAT-001).

The evaluator is the only writer of a Design Run``s ``maturity`` value.  It
computes the highest state whose necessary-and-sufficient conditions all
hold, applies the D6 named-engineer cap and the prohibited-category caps,
and returns a stable serializable record carrying an input digest and the
blocking reasons so any downstream manifest can keep provenance.  Recompute
rules follow the blueprint: input, rule, engine or waiver changes force a
recalculation, and a stale ``ENGINEERING_REVIEWED`` sign-off falls back to
the recomputed result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any

MATURITY_STATES = (
    "DRAFT",
    "CONCEPT",
    "PROTOTYPE",
    "ENGINEERING_REVIEWED",
    "RELEASED",
)
DRAFT_INDEX = 0
CONCEPT_INDEX = 1
PROTOTYPE_INDEX = 2
ENGINEERING_REVIEWED_INDEX = 3
RELEASED_INDEX = 4
_CAP_VALUES = frozenset({"CONCEPT", "PROTOTYPE"})

_STATE_INDEX = {level: index for index, level in enumerate(MATURITY_STATES)}


def level_index(state: str | None) -> int:
    """Return the ordering index for a state, or -1 when below DRAFT."""
    return -1 if state is None else _STATE_INDEX[state]


class MaturityInputError(ValueError):
    """Maturity evaluation input that cannot be serialized or classified."""


# Each condition is (field, expected_truthiness, blocking_message_zh_tw).
# ``expected True`` means the value must be truthy / non-empty, ``False``
# means it must be falsy / empty, covering booleans, tuples and optionals.
_CONDITIONS: tuple[tuple[str, tuple[tuple[str, bool, str], ...]], ...] = (
    (
        "DRAFT",
        (
            ("requirements_schema_valid", True, "需求未通過 schema 驗證。"),
        ),
    ),
    (
        "CONCEPT",
        (
            ("ir_schema_valid", True, "Engineering IR 未通過 schema 驗證。"),
            ("ir_referential_integrity_ok", True, "Engineering IR 參照完整性未通過。"),
            ("unresolved_unsafe_to_default", False, "存在未解決的 unsafe_to_default。"),
            ("layout_collision_no_error", True, "layout／collision 檢查未執行或存在 error。"),
        ),
    ),
    (
        "PROTOTYPE",
        (
            ("geometry_kernel_valid", True, "幾何未通過 kernel 有效性檢查。"),
            ("rule_packs_executed", True, "適用 rule packs 未全部執行。"),
            ("unresolved_errors", False, "存在未處置的 error。"),
            ("warnings_dispositioned", True, "warning 未全部 disposition。"),
            ("critical_unknowns", False, "存在 critical unknown。"),
            ("fingerprint_reproducible", True, "package semantic fingerprint 不可重現。"),
            ("drawing_qa_recorded", True, "drawing QA 結果未記錄。"),
            ("capabilities_in_envelope", True, "所有 capability 均在 supported envelope 內。"),
        ),
    ),
    (
        "ENGINEERING_REVIEWED",
        (
            ("engineering_review_signoff", True, "缺少具名 Mechanical Engineering Reviewer 的 sign-off。"),
        ),
    ),
    (
        "RELEASED",
        (
            ("release_record_ref", True, "缺少外部組織放行紀錄 reference。"),
        ),
    ),
)


@dataclass(frozen=True)
class MaturityInput:
    """All evaluation conditions for one Design Run.

    ``input_changed`` and ``waiver_expired`` are recompute/meta flags; they do
    not form part of the design digest but they invalidate a stale
    ``ENGINEERING_REVIEWED`` sign-off and force a recalculation.
    """

    requirements_schema_valid: bool
    ir_schema_valid: bool = False
    ir_referential_integrity_ok: bool = False
    unresolved_unsafe_to_default: bool = False
    layout_collision_no_error: bool = False
    geometry_kernel_valid: bool = False
    rule_packs_executed: bool = False
    unresolved_errors: tuple[str, ...] = ()
    warnings_dispositioned: bool = False
    critical_unknowns: tuple[str, ...] = ()
    fingerprint_reproducible: bool = False
    drawing_qa_recorded: bool = False
    capabilities_in_envelope: bool = False
    engineering_review_signoff: bool = False
    release_record_ref: str | None = None
    maturity_cap: str | None = None
    named_engineer_available: bool = False
    design_params: dict[str, Any] = field(default_factory=dict)
    input_changed: bool = False
    waiver_expired: bool = False

    @classmethod
    def from_dict(cls, document: dict[str, Any]) -> MaturityInput:
        return cls(
            requirements_schema_valid=document.get("requirements_schema_valid", False),
            ir_schema_valid=document.get("ir_schema_valid", False),
            ir_referential_integrity_ok=document.get("ir_referential_integrity_ok", False),
            unresolved_unsafe_to_default=document.get("unresolved_unsafe_to_default", False),
            layout_collision_no_error=document.get("layout_collision_no_error", False),
            geometry_kernel_valid=document.get("geometry_kernel_valid", False),
            rule_packs_executed=document.get("rule_packs_executed", False),
            unresolved_errors=tuple(document.get("unresolved_errors", [])),
            warnings_dispositioned=document.get("warnings_dispositioned", False),
            critical_unknowns=tuple(document.get("critical_unknowns", [])),
            fingerprint_reproducible=document.get("fingerprint_reproducible", False),
            drawing_qa_recorded=document.get("drawing_qa_recorded", False),
            capabilities_in_envelope=document.get("capabilities_in_envelope", False),
            engineering_review_signoff=document.get("engineering_review_signoff", False),
            release_record_ref=document.get("release_record_ref"),
            maturity_cap=document.get("maturity_cap"),
            named_engineer_available=document.get("named_engineer_available", False),
            design_params=dict(document.get("design_params", {})),
            input_changed=document.get("input_changed", False),
            waiver_expired=document.get("waiver_expired", False),
        )

    def _design_document(self) -> dict[str, Any]:
        """Materialize all digest-relevant fields in a stable order."""
        raw = self.to_dict()
        raw.pop("input_changed", None)
        raw.pop("waiver_expired", None)
        return raw

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirements_schema_valid": self.requirements_schema_valid,
            "ir_schema_valid": self.ir_schema_valid,
            "ir_referential_integrity_ok": self.ir_referential_integrity_ok,
            "unresolved_unsafe_to_default": self.unresolved_unsafe_to_default,
            "layout_collision_no_error": self.layout_collision_no_error,
            "geometry_kernel_valid": self.geometry_kernel_valid,
            "rule_packs_executed": self.rule_packs_executed,
            "unresolved_errors": list(self.unresolved_errors),
            "warnings_dispositioned": self.warnings_dispositioned,
            "critical_unknowns": list(self.critical_unknowns),
            "fingerprint_reproducible": self.fingerprint_reproducible,
            "drawing_qa_recorded": self.drawing_qa_recorded,
            "capabilities_in_envelope": self.capabilities_in_envelope,
            "engineering_review_signoff": self.engineering_review_signoff,
            "release_record_ref": self.release_record_ref,
            "maturity_cap": self.maturity_cap,
            "named_engineer_available": self.named_engineer_available,
            "design_params": self._canonicalize(self.design_params),
            "input_changed": self.input_changed,
            "waiver_expired": self.waiver_expired,
        }

    def digest(self) -> str:
        """SHA-256 over the canonical JSON of design-relevant fields."""
        canonical = json.dumps(
            self._design_document(),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _canonicalize(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: MaturityInput._canonicalize(value[key]) for key in sorted(value)}
        if isinstance(value, (list, tuple)):
            return [MaturityInput._canonicalize(item) for item in value]
        return value


@dataclass(frozen=True)
class MaturityEvaluation:
    """Deterministic evaluator output for one Design Run.

    ``state`` is ``None`` when the Design Run does not even reach DRAFT; a
    real manifest writer must then refuse to record a formal maturity.
    """

    state: str | None
    achieved_index: int
    blocking_reasons: tuple[str, ...]
    recomputed_reasons: tuple[str, ...]
    inputs_digest: str
    evaluator_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": "1.0.0",
            "workItem": "G3-MAT-001",
            "state": self.state,
            "achievedIndex": self.achieved_index,
            "blocking_reasons": list(self.blocking_reasons),
            "recomputed_reasons": list(self.recomputed_reasons),
            "inputs_digest": self.inputs_digest,
            "evaluator_version": self.evaluator_version,
        }


def recompute_required(design_input: MaturityInput) -> tuple[bool, list[str]]:
    """Return whether a recalculation is forced and for which reasons."""
    reasons: list[str] = []
    if design_input.input_changed:
        reasons.append("輸入已變更，必須重新計算成熟度。")
    if design_input.waiver_expired:
        reasons.append("waiver 已到期，必須重新計算成熟度。")
    return bool(reasons), reasons


def evaluate_design_run(
    design_input: MaturityInput,
    *,
    evaluator_version: str = "megis.maturity@1.0.0",
) -> MaturityEvaluation:
    """Compute the maturity state for a Design Run.

    The evaluator is the only writer of the ``maturity`` value: callers get a
    provenance-bearing record here and must not set maturity by hand.
    """
    security = _require_maturity_input(design_input)
    recompute, recompute_reasons = recompute_required(design_input)
    if recompute:
        security = _with_effective_signoff(security, recompute_reasons)

    achieved_index, failures = _highest_satisfied_level(security)
    achieved_index, cap_reasons = _apply_caps(achieved_index, security)
    reasons = list(failures) + cap_reasons
    state: str | None = None if achieved_index < DRAFT_INDEX else MATURITY_STATES[achieved_index]

    record = MaturityEvaluation(
        state=state,
        achieved_index=achieved_index,
        blocking_reasons=tuple(reasons),
        recomputed_reasons=tuple(recompute_reasons),
        inputs_digest=security.digest(),
        evaluator_version=evaluator_version,
    )
    return record


def _require_maturity_input(design_input: MaturityInput) -> MaturityInput:
    """Reject maturity inputs that cannot be classified deterministically."""
    for key, value in design_input._design_document().items():
        try:
            json.dumps(value)
        except (TypeError, ValueError) as error:
            raise MaturityInputError(f"{key}: not JSON-serializable ({error})") from error
    if design_input.maturity_cap not in _CAP_VALUES and design_input.maturity_cap is not None:
        raise MaturityInputError(
            f"maturity_cap must be one of {sorted(_CAP_VALUES)!r}, got {design_input.maturity_cap!r}"
        )
    return design_input


def _with_effective_signoff(
    design_input: MaturityInput,
    reasons: list[str],
) -> MaturityInput:
    """Drop a stale ENGINEERING_REVIEWED sign-off when recalculation is forced."""
    if not design_input.engineering_review_signoff:
        return design_input
    reasons.append("既有 ENGINEERING_REVIEWED sign-off 已失效，結果回到重新計算值。")
    return MaturityInput(**{**design_input.to_dict(), "engineering_review_signoff": False})


def _highest_satisfied_level(
    design_input: MaturityInput,
) -> tuple[int, list[str]]:
    """Return (highest satisfied level index, blocking reasons at next level)."""
    document = design_input.to_dict()
    achieved = DRAFT_INDEX - 1
    for index, (_name, probes) in enumerate(_CONDITIONS):
        failures = [
            message
            for product_field, expected, message in probes
            if not _condition_holds(document.get(product_field), expected)
        ]
        if failures:
            return achieved, failures
        achieved = index
    return achieved, []


def _condition_holds(value: Any, expected: bool) -> bool:
    if expected:
        return bool(value)
    return not bool(value)


def _apply_caps(
    achieved: int,
    design_input: MaturityInput,
) -> tuple[int, list[str]]:
    """Clamp the achieved level by D6 and prohibited-category caps."""
    reasons: list[str] = []
    cap = RELEASED_INDEX
    if not design_input.named_engineer_available:
        cap = min(cap, PROTOTYPE_INDEX)
    if design_input.maturity_cap == "CONCEPT":
        cap = min(cap, CONCEPT_INDEX)
        reasons.append("禁止類別上限：JavaRobot／Robot 類別最高為 CONCEPT。")
    elif design_input.maturity_cap == "PROTOTYPE":
        cap = min(cap, PROTOTYPE_INDEX)
        reasons.append("禁止類別上限：此類別最高為 PROTOTYPE。")
    if not design_input.named_engineer_available and achieved > PROTOTYPE_INDEX:
        reasons.append("D6：目前未指定具名工程師，成熟度最多為 PROTOTYPE。")
    return min(achieved, cap), reasons
