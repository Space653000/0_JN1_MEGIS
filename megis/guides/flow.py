"""Guided-flow IR draft builder and route equivalence (G6-UI-001).

The guided flow turns a closed set of answered questions into a schema-bound
Engineering IR draft.  It never fabricates an ``unsafe_to_default`` value:
missing outer dimensions, an abstained PCB envelope, or a capability outside
the proven envelope raise ``MEGIS-UI-*`` / ``MEGIS-ENV-001`` instead of a
silent default.  The same logical inputs expressed as a UI-form state or a
direct API payload produce byte-identical IR (blueprint G6 exit criteria:
UI and direct API produce equivalent IR).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from megis.contracts.serialization import serialize_engineering_ir
from megis.contracts.validation import validate_engineering_ir
from megis.envelope import load_envelope
from megis.errors import MegisError
from megis.maturity import MaturityEvaluation, MaturityInput, evaluate_design_run

GUIDED_DESIGN_ID = "FIXTURE-GUIDED-001"
RECORDED_AT = "2026-09-22T00:00:00Z"

_PRIORITY_MAP = {
    "serviceability": "must",
    "machinability": "should",
    "compactness": "could",
}
_QUANTITY_LABEL = {"prototype": "1–5 件原型", "small-batch": "6–50 件小批量"}
_PRIORITY_LABEL = {
    "serviceability": "容易拆裝維修",
    "machinability": "加工穩定",
    "compactness": "體積緊湊",
}
_ALLOWED_CONNECTORS = ("USB-C",)
_ALLOWED_FASTENERS = ("M3",)
_ALLOWED_COVERS = ("removable",)
_ALLOWED_QUANTITIES = ("prototype", "small-batch")
_ALLOWED_PRIORITIES = ("serviceability", "machinability", "compactness")
_ALLOWED_PCB_MODES = ("reference_only", "provided", "unknown")


@dataclass(frozen=True, slots=True)
class GuidedAnswers:
    """Deterministic guided-flow answer set (closed fields)."""

    width_mm: float | None = 120.0
    depth_mm: float | None = 80.0
    height_mm: float | None = 20.0
    pcb_count: int = 1
    connector: str = "USB-C"
    fastener: str = "M3"
    cover: str = "removable"
    quantity: str = "prototype"
    priority: str = "serviceability"
    purpose: str = "固定參考 PCB，供桌上測試與 USB-C 連接"
    pcb_envelope_mode: str = "reference_only"
    pcb_required: bool = False


def _num(value: Any, field: str) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise MegisError(
            "MEGIS-SCH-001",
            engineer_detail={"field": field, "received": repr(value)},
        ) from exc


def validate_answers(answers: GuidedAnswers, *, envelope: Any | None = None) -> None:
    """Raise the appropriate MEGIS error when answers cannot generate IR."""
    active = envelope if envelope is not None else load_envelope()

    missing = [
        field
        for field, value in (
            ("width_mm", answers.width_mm),
            ("depth_mm", answers.depth_mm),
            ("height_mm", answers.height_mm),
        )
        if value is None
    ]
    if missing:
        raise MegisError(
            "MEGIS-UI-001",
            engineer_detail={
                "reason": "missing outer dimensions are unsafe_to_default",
                "fields": missing,
                "nextStep": "請提供外形尺寸或上傳外形圖，系統不會自行假設尺寸。",
            },
        )
    if answers.pcb_envelope_mode not in _ALLOWED_PCB_MODES:
        raise MegisError(
            "MEGIS-UI-002",
            engineer_detail={"field": "pcb_envelope_mode", "value": answers.pcb_envelope_mode},
        )
    if answers.pcb_envelope_mode == "unknown":
        raise MegisError(
            "MEGIS-UI-001",
            engineer_detail={
                "reason": "user abstained on an unsafe_to_default PCB envelope",
                "nextStep": "請提供 PCB 外形範圍或上傳 PCB 外形圖。",
            },
        )
    if answers.pcb_required and answers.pcb_envelope_mode == "reference_only":
        raise MegisError(
            "MEGIS-UI-001",
            engineer_detail={
                "reason": "PCB envelope is required to complete this flow",
                "nextStep": "請切換為已提供外形範圍（provided）。",
            },
        )
    for field, value, allowed in (
        ("connector", answers.connector, _ALLOWED_CONNECTORS),
        ("fastener", answers.fastener, _ALLOWED_FASTENERS),
        ("cover", answers.cover, _ALLOWED_COVERS),
        ("quantity", answers.quantity, _ALLOWED_QUANTITIES),
        ("priority", answers.priority, _ALLOWED_PRIORITIES),
    ):
        if value not in allowed:
            raise MegisError(
                "MEGIS-UI-002",
                engineer_detail={"field": field, "value": value, "allowed": list(allowed)},
            )
    if answers.pcb_count not in (1, 2):
        raise MegisError(
            "MEGIS-UI-002",
            engineer_detail={"field": "pcb_count", "value": answers.pcb_count},
        )
    if not active.is_within(
        float(answers.width_mm),
        float(answers.depth_mm),
        float(answers.height_mm),
    ):
        raise MegisError(
            "MEGIS-ENV-001",
            engineer_detail={
                "reason": "proposed outer dimensions escape the proven envelope",
                "proposedMm": {
                    "width": answers.width_mm,
                    "depth": answers.depth_mm,
                    "height": answers.height_mm,
                },
            },
        )


def evaluate_guided_maturity(answers: GuidedAnswers) -> MaturityEvaluation:
    """Evaluate only the evidence the guided IR-draft stage actually has.

    A schema-valid draft is not a generated prototype.  This stage has not run
    layout/collision, geometry, rule packs, drawing QA, or package
    reproducibility.  It also retains the maximum-load critical unknown (and,
    for the reference-only path, the PCB-envelope unknown), so the shared
    evaluator must keep it at DRAFT.
    """

    critical_unknowns = ["/maximumLoad"]
    if answers.pcb_envelope_mode == "reference_only":
        critical_unknowns.append("/components[pcb]/dimensions")
    return evaluate_design_run(
        MaturityInput(
            requirements_schema_valid=True,
            ir_schema_valid=True,
            ir_referential_integrity_ok=True,
            unresolved_unsafe_to_default=bool(critical_unknowns),
            layout_collision_no_error=False,
            critical_unknowns=tuple(critical_unknowns),
            capabilities_in_envelope=True,
            design_params={
                "width_mm": answers.width_mm,
                "depth_mm": answers.depth_mm,
                "height_mm": answers.height_mm,
                "pcb_count": answers.pcb_count,
                "connector": answers.connector,
                "fastener": answers.fastener,
                "cover": answers.cover,
                "quantity": answers.quantity,
                "priority": answers.priority,
                "purpose": answers.purpose,
                "pcb_envelope_mode": answers.pcb_envelope_mode,
                "pcb_required": answers.pcb_required,
            },
        )
    )


def build_ir_draft(answers: GuidedAnswers) -> dict[str, Any]:
    """Build and validate a schema-bound Engineering IR draft document."""
    validate_answers(answers)
    maturity_evaluation = evaluate_guided_maturity(answers)
    if maturity_evaluation.state is None:
        raise MegisError(
            "MEGIS-SCH-001",
            engineer_detail={"reason": "guided IR does not satisfy DRAFT maturity"},
        )

    base_dims = [
        {
            "name": "width",
            "dimension": "length",
            "quantity": {
                "id": "DIM-GUIDED-WIDTH",
                "unit": "mm",
                "nominal": float(answers.width_mm),
                "tolerance": 0.1,
            },
        },
        {
            "name": "depth",
            "dimension": "length",
            "quantity": {
                "id": "DIM-GUIDED-DEPTH",
                "unit": "mm",
                "nominal": float(answers.depth_mm),
                "tolerance": 0.1,
            },
        },
        {
            "name": "height",
            "dimension": "length",
            "quantity": {
                "id": "DIM-GUIDED-HEIGHT",
                "unit": "mm",
                "nominal": float(answers.height_mm),
                "tolerance": 0.1,
            },
        },
    ]

    components: list[dict[str, Any]] = [
        {
            "id": "COMP-GUIDED-BASE",
            "name": "Guided fixture base",
            "domain": "fixture",
            "componentType": "fixture_base",
            "dimensions": base_dims,
            "materialId": "MAT-GUIDED-AL6061",
            "provenanceIds": ["PROV-GUIDED-001"],
        },
        {
            "id": "COMP-GUIDED-COVER",
            "name": "Guided fixture cover",
            "domain": "fixture",
            "componentType": "cover",
            "dimensions": [],
            "materialId": "MAT-GUIDED-AL6061",
            "provenanceIds": ["PROV-GUIDED-001"],
        },
    ]
    interfaces: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    for index in range(1, int(answers.pcb_count) + 1):
        component_id = f"COMP-GUIDED-PCB-{index}"
        components.append(
            {
                "id": component_id,
                "name": f"Guided PCB {index}",
                "domain": "fixture",
                "componentType": "pcb",
                "dimensions": [],
                "provenanceIds": ["PROV-GUIDED-001"],
            }
        )
        interfaces.append(
            {
                "id": f"INT-GUIDED-PCB-{index}",
                "name": f"PCB {index} mounting interface",
                "interfaceType": "mount",
                "participantIds": ["COMP-GUIDED-BASE", component_id],
            }
        )
        relationships.append(
            {
                "id": f"REL-GUIDED-PCB-{index}",
                "relationshipType": "mounts_to",
                "sourceId": component_id,
                "targetId": "COMP-GUIDED-BASE",
                "constraintIds": ["CON-GUIDED-WALL"],
            }
        )
    interfaces.append(
        {
            "id": "INT-GUIDED-COVER",
            "name": "Cover mounting interface",
            "interfaceType": "mount",
            "participantIds": ["COMP-GUIDED-BASE", "COMP-GUIDED-COVER"],
        }
    )
    relationships.append(
        {
            "id": "REL-GUIDED-COVER",
            "relationshipType": "mounts_to",
            "sourceId": "COMP-GUIDED-COVER",
            "targetId": "COMP-GUIDED-BASE",
            "constraintIds": ["CON-GUIDED-WALL"],
        }
    )

    statement = f"{answers.purpose or '固定參考 PCB，供桌上測試與 USB-C 連接'}"
    requirements = [
        {
            "id": "REQ-GUIDED-001",
            "statement": statement,
            "priority": _PRIORITY_MAP[answers.priority],
            "verificationMethod": "inspection",
            "provenanceIds": ["PROV-GUIDED-001"],
        }
    ]

    assumptions = [
        {
            "id": "ASM-GUIDED-SETUP",
            "subjectId": "COMP-GUIDED-BASE",
            "field": "/manufacturingSetup",
            "status": "defaulted",
            "rationale": "Guided flow uses the fixed three-axis setup from the proven envelope.",
            "provenanceIds": ["PROV-GUIDED-003"],
        },
        {
            "id": "ASM-GUIDED-QUANTITY",
            "subjectId": GUIDED_DESIGN_ID,
            "field": "/requirements[0]/quantity",
            "status": "defaulted",
            "rationale": f"使用者在引導流程選擇數量：{_QUANTITY_LABEL[answers.quantity]}",
            "provenanceIds": ["PROV-GUIDED-003"],
        },
        {
            "id": "ASM-GUIDED-PRIORITY",
            "subjectId": GUIDED_DESIGN_ID,
            "field": "/requirements[0]/priority",
            "status": "defaulted",
            "rationale": f"使用者在引導流程選擇優先目標：{_PRIORITY_LABEL[answers.priority]}",
            "provenanceIds": ["PROV-GUIDED-003"],
        },
    ]

    unknowns: list[dict[str, Any]] = [
        {
            "id": "UNK-GUIDED-LOAD",
            "subjectId": GUIDED_DESIGN_ID,
            "field": "/maximumLoad",
            "unsafeToDefault": True,
            "question": "What maximum applied load must the fixture withstand?",
        }
    ]
    if answers.pcb_envelope_mode == "reference_only":
        unknowns.append(
            {
                "id": "UNK-GUIDED-PCB",
                "subjectId": "COMP-GUIDED-PCB-1",
                "field": "/components[pcb]/dimensions",
                "unsafeToDefault": True,
                "question": "請提供 PCB 外形範圍或上傳外形圖；系統不會自行假設尺寸。",
            }
        )

    provenance = [
        {
            "id": "PROV-GUIDED-001",
            "subjectId": GUIDED_DESIGN_ID,
            "field": "/requirements",
            "source": "user",
            "actor": "guided-flow-user",
            "recordedAt": RECORDED_AT,
        },
        {
            "id": "PROV-GUIDED-002",
            "subjectId": "COMP-GUIDED-BASE",
            "field": "/constraints",
            "source": "derived",
            "sourceRef": "rule:CNC-WALL-MIN@1.0.0",
            "recordedAt": RECORDED_AT,
        },
        {
            "id": "PROV-GUIDED-003",
            "subjectId": "COMP-GUIDED-BASE",
            "field": "/manufacturingSetup",
            "source": "defaulted",
            "rationale": "Guided flow reference baseline",
            "recordedAt": RECORDED_AT,
        },
    ]

    document: dict[str, Any] = {
        "schemaVersion": "2.0.0",
        "designId": GUIDED_DESIGN_ID,
        "revision": "A",
        "maturity": maturity_evaluation.state,
        "unitSystem": {"length": "mm", "angle": "deg", "mass": "kg", "time": "s"},
        "coordinateSystem": {
            "handedness": "right",
            "axes": {"x": "width", "y": "depth", "z": "height"},
        },
        "requirements": requirements,
        "components": components,
        "interfaces": interfaces,
        "relationships": relationships,
        "materials": [
            {
                "id": "MAT-GUIDED-AL6061",
                "name": "Aluminum 6061",
                "designation": "AA 6061",
                "properties": [],
                "provenanceIds": ["PROV-GUIDED-002"],
            }
        ],
        "manufacturing": [
            {
                "id": "MFG-GUIDED-CNC",
                "process": "3_axis_cnc",
                "componentIds": ["COMP-GUIDED-BASE", "COMP-GUIDED-COVER"],
            }
        ],
        "constraints": [
            {
                "id": "CON-GUIDED-WALL",
                "constraintType": "wall",
                "severity": "hard",
                "targetIds": ["COMP-GUIDED-BASE", "COMP-GUIDED-COVER"],
                "measurement": {
                    "name": "minimum wall",
                    "dimension": "length",
                    "quantity": {"id": "DIM-GUIDED-WALL", "unit": "mm", "min": 2.0, "max": 3.0},
                },
                "provenanceIds": ["PROV-GUIDED-002"],
            }
        ],
        "assumptions": assumptions,
        "unknowns": unknowns,
        "provenance": provenance,
    }
    validate_engineering_ir(document)
    return document


def ui_state_to_answers(state: dict[str, Any]) -> GuidedAnswers:
    """Normalize the UI-form state into a closed answer set."""
    return GuidedAnswers(
        width_mm=_num(state.get("width"), "width"),
        depth_mm=_num(state.get("depth"), "depth"),
        height_mm=_num(state.get("height"), "height"),
        pcb_count=int(state.get("pcbCount", 1)),
        connector=str(state.get("connector", "USB-C")),
        fastener=str(state.get("fastener", "M3")),
        cover=str(state.get("cover", "removable")),
        quantity=str(state.get("quantity", "prototype")),
        priority=str(state.get("priority", "serviceability")),
        purpose=str(state.get("purpose", "固定參考 PCB，供桌上測試與 USB-C 連接")),
        pcb_envelope_mode=str(state.get("pcbEnvelopeMode", "reference_only")),
        pcb_required=bool(state.get("pcbRequired", False)),
    )


def api_payload_to_answers(payload: dict[str, Any]) -> GuidedAnswers:
    """Normalize the direct API payload into the same closed answer set."""
    return GuidedAnswers(
        width_mm=_num(payload.get("width_mm"), "width_mm"),
        depth_mm=_num(payload.get("depth_mm"), "depth_mm"),
        height_mm=_num(payload.get("height_mm"), "height_mm"),
        pcb_count=int(payload.get("pcb_count", 1)),
        connector=str(payload.get("connector", "USB-C")),
        fastener=str(payload.get("fastener", "M3")),
        cover=str(payload.get("cover", "removable")),
        quantity=str(payload.get("quantity", "prototype")),
        priority=str(payload.get("priority", "serviceability")),
        purpose=str(payload.get("purpose", "固定參考 PCB，供桌上測試與 USB-C 連接")),
        pcb_envelope_mode=str(payload.get("pcb_envelope_mode", "reference_only")),
        pcb_required=bool(payload.get("pcb_required", False)),
    )


def build_ir_via_ui(state: dict[str, Any]) -> str:
    """Produce canonical IR from a UI-form state (UI route)."""
    return serialize_engineering_ir(build_ir_draft(ui_state_to_answers(state)))


def build_ir_via_api(payload: dict[str, Any]) -> str:
    """Produce canonical IR from a direct API payload (API route)."""
    return serialize_engineering_ir(build_ir_draft(api_payload_to_answers(payload)))


def ir_equivalent(first: str | bytes, second: str | bytes) -> bool:
    """True when two canonical IR payloads are byte-identical."""
    return first == second


__all__ = [
    "GUIDED_DESIGN_ID",
    "GuidedAnswers",
    "api_payload_to_answers",
    "build_ir_draft",
    "build_ir_via_api",
    "build_ir_via_ui",
    "evaluate_guided_maturity",
    "ir_equivalent",
    "ui_state_to_answers",
    "validate_answers",
]
