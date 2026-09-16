"""Small downstream consumer proving that Engineering IR is usable data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .validation import validate_engineering_ir


@dataclass(frozen=True)
class EngineeringIrSummary:
    """A deterministic capability-neutral projection of validated IR."""

    design_id: str
    revision: str
    maturity: str
    component_count: int
    domains: tuple[str, ...]
    relationship_count: int
    unsafe_unknown_ids: tuple[str, ...]


def summarize_engineering_ir(document: dict[str, Any]) -> EngineeringIrSummary:
    """Validate IR, then consume its entities into a downstream summary."""

    validate_engineering_ir(document)
    return EngineeringIrSummary(
        design_id=document["designId"],
        revision=document["revision"],
        maturity=document["maturity"],
        component_count=len(document["components"]),
        domains=tuple(sorted({component["domain"] for component in document["components"]})),
        relationship_count=len(document["relationships"]),
        unsafe_unknown_ids=tuple(
            sorted(item["id"] for item in document["unknowns"] if item["unsafeToDefault"])
        ),
    )
