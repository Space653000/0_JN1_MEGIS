"""Module capability levels and the behaviour each level permits (G4-MOD-001).

Implements the closed four-level vocabulary from blueprint 4.16 and the
capability-to-behaviour restriction table from section 12.  The vocabulary is
closed: adding a level requires a MINOR schema version plus a semantic test.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CAPABILITY_LEVELS = (
    "metadata_only",
    "layout_capable",
    "geometry_capable",
    "validated",
)
METADATA_ONLY_INDEX = 0
LAYOUT_CAPABLE_INDEX = 1
GEOMETRY_CAPABLE_INDEX = 2
VALIDATED_INDEX = 3

_CAPABILITY_INDEX = {level: index for index, level in enumerate(CAPABILITY_LEVELS)}

_UI_DISPLAY = {
    "metadata_only": "僅資料",
    "layout_capable": "可放置 envelope",
    "geometry_capable": "可放置",
    "validated": "可放置",
}


@dataclass(frozen=True)
class CapabilityPolicy:
    """Behaviour a capability level permits and its maturity ceiling."""

    level: str
    ui_display: str
    layout_allowed: bool
    geometry_allowed: bool
    validation: tuple[str, ...]
    maturity_cap: str


_POLICY_TABLE: dict[str, CapabilityPolicy] = {
    "metadata_only": CapabilityPolicy(
        level="metadata_only",
        ui_display=_UI_DISPLAY["metadata_only"],
        layout_allowed=False,
        geometry_allowed=False,
        validation=(),
        maturity_cap="DRAFT",
    ),
    "layout_capable": CapabilityPolicy(
        level="layout_capable",
        ui_display=_UI_DISPLAY["layout_capable"],
        layout_allowed=True,
        geometry_allowed=False,
        validation=("collision", "clearance"),
        maturity_cap="CONCEPT",
    ),
    "geometry_capable": CapabilityPolicy(
        level="geometry_capable",
        ui_display=_UI_DISPLAY["geometry_capable"],
        layout_allowed=True,
        geometry_allowed=True,
        validation=("geometry_rules",),
        maturity_cap="PROTOTYPE",
    ),
    "validated": CapabilityPolicy(
        level="validated",
        ui_display=_UI_DISPLAY["validated"],
        layout_allowed=True,
        geometry_allowed=True,
        validation=("all_applicable_rules", "golden"),
        maturity_cap="PROTOTYPE",
    ),
}


def capability_index(level: str | None) -> int:
    """Return the ordering index for a capability level, or -1 when invalid."""
    return -1 if level is None else _CAPABILITY_INDEX.get(level, -1)


def policy_for(level: str) -> CapabilityPolicy:
    """Return the capability policy row for a level."""
    return _POLICY_TABLE[level]


def geometry_generator_required(level: str | None) -> bool:
    """A geometry generator reference is mandatory at or above geometry_capable."""
    return capability_index(level) >= GEOMETRY_CAPABLE_INDEX


def resolve_capability(raw: dict[str, Any]) -> str | None:
    """Extract a validated capability level from a module document, or None."""
    return raw.get("capability_level")


__all__ = [
    "CAPABILITY_LEVELS",
    "GEOMETRY_CAPABLE_INDEX",
    "LAYOUT_CAPABLE_INDEX",
    "METADATA_ONLY_INDEX",
    "VALIDATED_INDEX",
    "CapabilityPolicy",
    "capability_index",
    "geometry_generator_required",
    "policy_for",
    "resolve_capability",
]
