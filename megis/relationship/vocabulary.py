"""Relationship vocabulary semantics (G4-GRF-001).

Implements the closed eight-type relationship vocabulary from blueprint 4.16:
every type has a defined meaning, the parameters needed to satisfy its
``必要驗證`` column, and the quantitative/text invariants a valid relationship
must honour.  The vocabulary is closed: adding a type requires a MINOR schema
version plus a semantic test.
"""

from __future__ import annotations

RELATIONSHIP_TYPES = (
    "contains",
    "mounts_to",
    "fastens",
    "opens_through",
    "clears",
    "aligns",
    "covers",
    "removable_along",
)

TYPE_MEANING = {
    "contains": "A 的內腔容納 B；B 的 clearance envelope 完全在 A 內腔內",
    "mounts_to": "B 以 fastener 固定於 A；孔位對齊、boss 存在、嚙合長度",
    "fastens": "fastener 連接 A 與 B；螺絲長度、通孔、內螺紋",
    "opens_through": "介面 B 穿過 A 的壁面；開口存在、開口 ≥ 介面 envelope + 間隙",
    "clears": "A 與 B 最小距離 ≥ d；距離計算",
    "aligns": "A 與 B 在指定軸對齊；軸向偏差 ≤ 容差",
    "covers": "A 覆蓋 B 的開口；配合面與干涉檢查",
    "removable_along": "A 可沿方向移除；掃掠干涉檢查",
}

REQUIRED_PARAMETERS = {
    "contains": ("envelope_ref", "cavity_ref"),
    "mounts_to": (
        "fastener_ref",
        "boss_ref",
        "engagement_length_mm",
        "hole_alignment_tolerance_mm",
    ),
    "fastens": ("screw_length_mm", "through_hole_ref", "thread_ref"),
    "opens_through": ("opening_ref", "interface_envelope_ref", "clearance_gap_mm"),
    "clears": ("minimum_distance_mm",),
    "aligns": ("axis", "tolerance_mm"),
    "covers": ("opening_ref", "mating_face_ref", "interference_check_ref"),
    "removable_along": ("direction", "sweep_check_ref"),
}

# Reference keys that name an envelope, cavity, boss, opening or geometry
# feature; they must be non-empty strings so a relationship never points at
# nothing.
REFERENCE_PARAMETERS = {
    "envelope_ref",
    "cavity_ref",
    "fastener_ref",
    "boss_ref",
    "through_hole_ref",
    "thread_ref",
    "opening_ref",
    "interface_envelope_ref",
    "mating_face_ref",
    "interference_check_ref",
    "sweep_check_ref",
}

# Lengths/gaps in millimetres and angular/positional tolerances must never be
# negative; the proven engineering values are strictly positive.
LENGTH_PARAMETERS = {
    "engagement_length_mm",
    "hole_alignment_tolerance_mm",
    "screw_length_mm",
    "clearance_gap_mm",
    "minimum_distance_mm",
    "tolerance_mm",
}

STRICTLY_POSITIVE_LENGTH_PARAMETERS = {
    "engagement_length_mm",
    "screw_length_mm",
    "clearance_gap_mm",
    "minimum_distance_mm",
    "tolerance_mm",
}

# Free-text parameters (axis name or removal direction) that must be non-empty.
TEXT_PARAMETERS = {"axis", "direction"}


def relationship_type_index(relationship_type: str | None) -> int:
    """Return the ordering index for a relationship type, or -1 when invalid."""
    if relationship_type is None:
        return -1
    try:
        return RELATIONSHIP_TYPES.index(relationship_type)
    except ValueError:
        return -1


__all__ = [
    "LENGTH_PARAMETERS",
    "REFERENCE_PARAMETERS",
    "RELATIONSHIP_TYPES",
    "REQUIRED_PARAMETERS",
    "STRICTLY_POSITIVE_LENGTH_PARAMETERS",
    "TEXT_PARAMETERS",
    "TYPE_MEANING",
    "relationship_type_index",
]
