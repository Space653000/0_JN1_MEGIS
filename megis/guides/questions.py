"""Deterministic, IR-bound guided questions (G6-UI-001).

Every question maps to at least one Engineering IR field plus an envelope
range or a closed option set, so the flow never asks a question that cannot
change the IR (blueprint section 14, rule 6).  The order is fixed and
deterministic; the dynamic ordering/abstention algorithm is G6-QST-001.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class GuidedQuestion:
    id: str
    irField: str
    label: str
    help: str
    inputKind: str
    envelopeRange: dict[str, float] | None
    options: tuple[str, ...]
    unsafeToDefault: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "irField": self.irField,
            "label": self.label,
            "help": self.help,
            "inputKind": self.inputKind,
            "envelopeRange": self.envelopeRange,
            "options": list(self.options),
            "unsafeToDefault": self.unsafeToDefault,
        }


GUIDED_QUESTIONS: tuple[GuidedQuestion, ...] = (
    GuidedQuestion(
        "Q-FIXTURE-WIDTH",
        "/components[fixture_base]/dimensions/width/nominal",
        "外形的寬度 W 是多少？",
        "寬度是治具左右兩側的距離，單位公釐（mm）。",
        "number",
        {"maxMm": 120.0},
        (),
        True,
    ),
    GuidedQuestion(
        "Q-FIXTURE-DEPTH",
        "/components[fixture_base]/dimensions/depth/nominal",
        "外形的深度 D 是多少？",
        "深度是治具前後兩側的距離，單位公釐（mm）。",
        "number",
        {"maxMm": 80.0},
        (),
        True,
    ),
    GuidedQuestion(
        "Q-FIXTURE-HEIGHT",
        "/components[fixture_base]/dimensions/height/nominal",
        "外形的總高度 H 是多少？",
        "高度是治具底部到頂面的距離，單位公釐（mm）。",
        "number",
        {"maxMm": 20.0},
        (),
        True,
    ),
    GuidedQuestion(
        "Q-FIXTURE-PCB-COUNT",
        "/components[pcb]/count",
        "內部要放幾片 PCB？",
        "PCB 是印刷電路板，參考案例支援 1 或 2 片。",
        "choice",
        {"minMm": 1.0, "maxMm": 2.0},
        ("1", "2"),
        False,
    ),
    GuidedQuestion(
        "Q-FIXTURE-CONNECTOR",
        "/interfaces[usb]/interfaceType",
        "需要哪一種外部介面開口？",
        "目前只支援 USB-C 開口。",
        "choice",
        None,
        ("USB-C",),
        False,
    ),
    GuidedQuestion(
        "Q-FIXTURE-FASTENER",
        "/relationships[fastens]/fastenerSize",
        "外殼使用哪一種緊固件？",
        "緊固件是把上蓋固定在底座上的螺絲，目前支援 M3。",
        "choice",
        None,
        ("M3",),
        False,
    ),
    GuidedQuestion(
        "Q-FIXTURE-COVER",
        "/components[cover]/removability",
        "上蓋需要可拆嗎？",
        "可拆上蓋方便維修與更換內部零件。",
        "choice",
        None,
        ("removable",),
        False,
    ),
    GuidedQuestion(
        "Q-FIXTURE-QUANTITY",
        "/requirements[quantity]/value",
        "預計製作多少件？",
        "原型數量影響製程選擇與單價。",
        "choice",
        None,
        ("prototype", "small-batch"),
        False,
    ),
    GuidedQuestion(
        "Q-FIXTURE-PRIORITY",
        "/requirements[priority]/value",
        "你最重視哪一個目標？",
        "目標會影響問題順序與建議方向。",
        "choice",
        None,
        ("serviceability", "machinability", "compactness"),
        False,
    ),
    GuidedQuestion(
        "Q-FIXTURE-PURPOSE",
        "/requirements[0]/statement",
        "用途是一句話描述這個治具要做什麼？",
        "用途會寫進工程需求，讓後續檢視的人知道設計目的。",
        "text",
        None,
        (),
        False,
    ),
    GuidedQuestion(
        "Q-FIXTURE-PCB-ENVELOPE",
        "/unknowns[pcb_envelope]/question",
        "PCB 的外形範圍已經確認了嗎？",
        "若尚未確認，系統不會自行假設尺寸，會保留為待確認問題。",
        "choice",
        None,
        ("reference_only", "provided", "unknown"),
        True,
    ),
)


def guided_questions() -> tuple[dict[str, Any], ...]:
    """Return the deterministic question set as plain dictionaries."""
    return tuple(question.to_dict() for question in GUIDED_QUESTIONS)


__all__ = ["GUIDED_QUESTIONS", "GuidedQuestion", "guided_questions"]
