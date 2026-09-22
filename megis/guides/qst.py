"""Deterministic question ordering and abstention handling (G6-QST-001).

Implements blueprint section 14 Dynamic Question Engine rules 1-8:

* ``unsafe_to_default`` questions are asked first (rule 1).
* Architecture- or process-changing questions outrank requirement-scoped
  questions (rule 2).
* Values reliably derivable from the proven capability set - the single
  proven interface/fastener/cover options - are never asked (rule 3).
* Ordering is fully deterministic and pinned by a frozen golden corpus
  (rule 7).
* An ``unsafe_to_default`` field the user leaves as "unknown" blocks
  generation with an explicit reason and next steps, and the critical
  unknown never disappears from the pending set (rules 5 and 8).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from megis.guides.questions import GUIDED_QUESTIONS, GuidedQuestion, guided_questions

# Question IDs whose answers are reliably derivable from the proven
# capability set (each has exactly one proven option).  Per rule 3 the
# engine never asks them; the derived value is recorded as the default.
DERIVED_DEFAULTS: dict[str, str] = {
    "Q-FIXTURE-CONNECTOR": "USB-C",
    "Q-FIXTURE-FASTENER": "M3",
    "Q-FIXTURE-COVER": "removable",
}

# Impact classes (rule 2): 0 changes architecture or manufacturing process,
# 1 shapes the recommendation order, 2 carries the free-text requirement
# statement.  Questions absent from this map are treated as impact 9.
IMPACT_RANK: dict[str, int] = {
    "Q-FIXTURE-WIDTH": 0,
    "Q-FIXTURE-DEPTH": 0,
    "Q-FIXTURE-HEIGHT": 0,
    "Q-FIXTURE-PCB-COUNT": 0,
    "Q-FIXTURE-PCB-ENVELOPE": 0,
    "Q-FIXTURE-QUANTITY": 0,
    "Q-FIXTURE-PRIORITY": 1,
    "Q-FIXTURE-PURPOSE": 2,
}

# State keys that hold the three unsafe outer dimensions.  Both the UI-form
# (width) and direct-API (width_mm) conventions are accepted.
DIMENSION_KEYS: dict[str, tuple[str, ...]] = {
    "Q-FIXTURE-WIDTH": ("width", "width_mm"),
    "Q-FIXTURE-DEPTH": ("depth", "depth_mm"),
    "Q-FIXTURE-HEIGHT": ("height", "height_mm"),
}

_DECLARATION_INDEX = {question.id: index for index, question in enumerate(GUIDED_QUESTIONS)}


def _as_question(item: GuidedQuestion | dict[str, Any]) -> GuidedQuestion:
    if isinstance(item, dict):
        return GuidedQuestion(**item)
    return item


def _sort_key(question: GuidedQuestion) -> tuple[int, int, int]:
    safety = 0 if question.unsafeToDefault else 1
    impact = IMPACT_RANK.get(question.id, 9)
    index = _DECLARATION_INDEX.get(question.id, len(_DECLARATION_INDEX))
    return safety, impact, index


def _value(state: dict[str, Any], keys: tuple[str, ...]) -> Any | None:
    for key in keys:
        value = state.get(key)
        if value is not None and value != "":
            return value
    return None


def _pcb_mode(state: dict[str, Any]) -> str:
    value = state.get("pcbEnvelopeMode", state.get("pcb_envelope_mode", "reference_only"))
    return str(value or "reference_only")


@dataclass(frozen=True, slots=True)
class QuestionOrder:
    """Deterministic ordering result for a partially answered flow."""

    orderedIds: tuple[str, ...]
    skippedDerived: tuple[str, ...]


def order_questions(
    questions: Iterable[GuidedQuestion | dict[str, Any]] | None = None,
    answered: Iterable[str] = (),
) -> QuestionOrder:
    """Return pending question IDs in deterministic order.

    ``answered`` holds the question IDs the user has already answered; they
    are excluded from the pending set.  Values that are reliably derivable
    from the proven capability set are never asked.
    """
    source = guided_questions() if questions is None else questions
    normalized = tuple(_as_question(item) for item in source)
    answered_set = frozenset(answered)
    pending = [
        question
        for question in normalized
        if question.id not in DERIVED_DEFAULTS and question.id not in answered_set
    ]
    ordered = sorted(pending, key=_sort_key)
    skipped = tuple(
        question.id for question in normalized if question.id in DERIVED_DEFAULTS
    )
    return QuestionOrder(
        orderedIds=tuple(question.id for question in ordered),
        skippedDerived=skipped,
    )


@dataclass(frozen=True, slots=True)
class Abstention:
    """A blocking unsafe unknown with an actionable next step."""

    question: str
    irField: str
    reason: str
    nextSteps: tuple[str, ...]


def abstention_blocks(state: dict[str, Any]) -> tuple[Abstention, ...]:
    """Enumerate blocking unsafe unknowns in the current state (rules 5, 8)."""
    blocks: list[Abstention] = []
    for question_id, key in DIMENSION_KEYS.items():
        if _value(state, key) is None:
            blocks.append(
                Abstention(
                    question_id,
                    "/components[fixture_base]/dimensions",
                    "缺少不安全的尺寸：系統不會自行假設尺寸。",
                    ("請提供外形尺寸或上傳外形圖。",),
                )
            )
    mode = _pcb_mode(state)
    if mode == "unknown":
        blocks.append(
            Abstention(
                "Q-FIXTURE-PCB-ENVELOPE",
                "/unknowns[pcb_envelope]/question",
                "使用者選擇「不知道」；該欄位為 unsafe_to_default，系統不會自行假設 PCB 外形範圍。",
                ("請提供 PCB 外形範圍或上傳 PCB 外形圖。",),
            )
        )
    if bool(state.get("pcbRequired")) and mode != "provided":
        blocks.append(
            Abstention(
                "Q-FIXTURE-PCB-ENVELOPE",
                "/unknowns[pcb_envelope]/question",
                "PCB 外形範圍是完成此流程的必要項目；僅參考案例不足以生成。",
                ("請切換為已提供外形範圍（provided），或上傳 PCB 外形圖。",),
            )
        )
    return tuple(blocks)


def critical_remaining(state: dict[str, Any], answered: Iterable[str] = ()) -> tuple[str, ...]:
    """Critical unknowns that must stay visible even when the flow proceeds."""
    answered_set = frozenset(answered)
    result: list[str] = []
    for question_id, key in DIMENSION_KEYS.items():
        if _value(state, key) is None and question_id not in answered_set:
            result.append(question_id)
        elif question_id in answered_set:
            # An answered dimension is resolved; nothing to add.
            continue
    if _pcb_mode(state) != "provided":
        result.append("Q-FIXTURE-PCB-ENVELOPE")
    seen: set[str] = set()
    unique: list[str] = []
    for question_id in result:
        if question_id not in seen:
            seen.add(question_id)
            unique.append(question_id)
    return tuple(unique)


@dataclass(frozen=True, slots=True)
class SessionStatus:
    """Combined ordering + abstention status for one guided-flow state."""

    blocked: bool
    blockReason: str | None
    nextSteps: tuple[str, ...]
    orderedIds: tuple[str, ...]
    skippedDerived: tuple[str, ...]
    criticalRemaining: tuple[str, ...]


def session_status(state: dict[str, Any], answered: Iterable[str] = ()) -> SessionStatus:
    """Report whether generation is blocked and what to ask next."""
    order = order_questions(guided_questions(), answered)
    blocks = abstention_blocks(state)
    critical = critical_remaining(state, answered)
    if blocks:
        first = blocks[0]
        return SessionStatus(
            blocked=True,
            blockReason=first.reason,
            nextSteps=first.nextSteps,
            orderedIds=order.orderedIds,
            skippedDerived=order.skippedDerived,
            criticalRemaining=critical,
        )
    return SessionStatus(
        blocked=False,
        blockReason=None,
        nextSteps=(),
        orderedIds=order.orderedIds,
        skippedDerived=order.skippedDerived,
        criticalRemaining=critical,
    )


__all__ = [
    "DERIVED_DEFAULTS",
    "DIMENSION_KEYS",
    "IMPACT_RANK",
    "Abstention",
    "QuestionOrder",
    "SessionStatus",
    "abstention_blocks",
    "critical_remaining",
    "order_questions",
    "session_status",
]
