"""Machine-readable supported envelope loader (G1-ENV-001).

Consumers must read config/envelope/envelope.yaml instead of hard-coding
ranges. Escaping the verified envelope surfaces MEGIS-ENV-001 instead of a
silent clamp (blueprint 2.4 / invariant 18).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from megis.errors import MegisError

ROOT = Path(__file__).resolve().parents[2]
ENVELOPE_PATH = ROOT / "config" / "envelope" / "envelope.yaml"
ENVELOPE_SCHEMA_PATH = ROOT / "schemas" / "v3" / "envelope.schema.json"


@dataclass(frozen=True)
class EnvelopeDimensions:
    width_mm: float
    depth_mm: float
    height_mm: float


@dataclass(frozen=True)
class Envelope:
    envelope_id: str
    label: str
    verified: bool
    materials: tuple[str, ...]
    machining: tuple[str, ...]
    outer_dimensions_mm: EnvelopeDimensions
    minimum_wall_mm: float
    cover_count: int
    fastener_count: int
    unsupported_error_codes: tuple[str, ...]
    v3_target_verified: bool

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Envelope":
        outer = raw["dimensions_mm"]["outer"]
        return cls(
            envelope_id=raw["envelope_id"],
            label=raw["label"],
            verified=raw["verified"],
            materials=tuple(raw["materials"]),
            machining=tuple(raw["machining"]),
            outer_dimensions_mm=EnvelopeDimensions(
                width_mm=outer["width"],
                depth_mm=outer["depth"],
                height_mm=outer["height"],
            ),
            minimum_wall_mm=raw["dimensions_mm"]["minimum_wall"],
            cover_count=raw["fixture"]["cover_count"],
            fastener_count=raw["fixture"]["fastener_count"],
            unsupported_error_codes=tuple(raw["unsupported_behaviour"]["error_codes"]),
            v3_target_verified=raw["v3_target"]["verified"],
        )

    def is_within(self, width_mm: float, depth_mm: float, height_mm: float) -> bool:
        return (
            width_mm <= self.outer_dimensions_mm.width_mm
            and depth_mm <= self.outer_dimensions_mm.depth_mm
            and height_mm <= self.outer_dimensions_mm.height_mm
        )


def load_envelope(path: Path = ENVELOPE_PATH) -> Envelope:
    """Load and schema-validate the machine-readable envelope."""

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    schema = json.loads(ENVELOPE_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(raw), key=lambda error: list(error.absolute_path))
    if errors:
        details = "; ".join(f"{list(error.absolute_path)}: {error.message}" for error in errors)
        raise ValueError(f"envelope invalid: {details}")
    return Envelope.from_dict(raw)


def check_within_envelope(
    width_mm: float,
    depth_mm: float,
    height_mm: float,
    *,
    envelope: Envelope | None = None,
    correlation_id: str = "",
) -> None:
    """Raise MEGIS-ENV-001 when a proposed part escapes the verified envelope."""

    active = envelope if envelope is not None else load_envelope()
    if not active.is_within(width_mm, depth_mm, height_mm):
        raise MegisError(
            "MEGIS-ENV-001",
            engineer_detail={
                "width_mm": width_mm,
                "depth_mm": depth_mm,
                "height_mm": height_mm,
                "verified_outer_mm": {
                    "width_mm": active.outer_dimensions_mm.width_mm,
                    "depth_mm": active.outer_dimensions_mm.depth_mm,
                    "height_mm": active.outer_dimensions_mm.height_mm,
                },
            },
            correlation_id=correlation_id,
        )
