"""Machine-readable G2 boundary/negative corpus loader and runner helpers.

The corpus lives at contracts/g2/golden/geometry-corpus.json and is validated
against schemas/v2/geometry-corpus.schema.json. Each case edits the golden IR
through a small set of structured operations (never free-form string paths in
product code), so boundary and negative expectations are fully reproducible.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CORPUS_PATH = ROOT / "contracts" / "g2" / "golden" / "geometry-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v2" / "geometry-corpus.schema.json"
GOLDEN_IR_PATH = ROOT / "contracts" / "g1" / "golden" / "reference-fixture.json"


class CorpusError(ValueError):
    """A corpus that cannot be applied deterministically."""


def load_corpus(path: Path = CORPUS_PATH) -> dict[str, Any]:
    """Load and schema-validate the G2 corpus."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(raw), key=lambda error: list(error.absolute_path))
    if errors:
        details = "; ".join(
            f"{list(error.absolute_path)}: {error.message}" for error in errors
        )
        raise CorpusError(f"corpus invalid: {details}")
    return raw


def _component(document: dict[str, Any], component_type: str) -> dict[str, Any]:
    matches = [
        item for item in document["components"] if item["componentType"] == component_type
    ]
    if len(matches) != 1:
        raise CorpusError(
            f"corpus references {component_type!r} but IR has {len(matches)} components"
        )
    return matches[0]


def _dimension(component: dict[str, Any], dimension: str) -> dict[str, Any]:
    matches = [item for item in component["dimensions"] if item["name"] == dimension]
    if len(matches) != 1:
        raise CorpusError(
            f"corpus references {dimension!r} but component has {len(matches)} dimensions"
        )
    return matches[0]


def _wall_constraint(document: dict[str, Any]) -> dict[str, Any]:
    matches = [
        item
        for item in document["constraints"]
        if item["constraintType"] == "wall"
        and item.get("measurement", {}).get("name") == "minimum wall"
    ]
    if len(matches) != 1:
        raise CorpusError(f"corpus references wall but IR has {len(matches)} constraints")
    return matches[0]


def _apply_edit(document: dict[str, Any], edit: dict[str, Any]) -> None:
    operation = edit["op"]
    if operation == "set_dimensions":
        component = _component(document, edit["component"])
        for dimension, value in edit["values"].items():
            _dimension(component, dimension)["quantity"]["nominal"] = value
        return
    if operation == "set_wall":
        quantity = _wall_constraint(document)["measurement"]["quantity"]
        quantity["min"] = edit["min"]
        quantity["max"] = edit["max"]
        quantity.pop("nominal", None)
        return
    if operation == "delete_dimension":
        component = _component(document, edit["component"])
        component["dimensions"] = [
            item for item in component["dimensions"] if item["name"] != edit["dimension"]
        ]
        return
    if operation == "add_dimension":
        component = _component(document, edit["component"])
        component["dimensions"].append(
            {
                "name": edit["dimension"],
                "dimension": "length",
                "quantity": {
                    "id": f"DIM-CORPUS-{edit['dimension'].upper()}",
                    "unit": "mm",
                    "nominal": edit["nominal"],
                },
            }
        )
        return
    if operation == "set_path":
        target: Any = document
        for key in edit["path"][:-1]:
            target = target[key]
        target[edit["path"][-1]] = edit["value"]
        return
    raise CorpusError(f"unsupported corpus edit operation {operation!r}")


def apply_case(base: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    """Deep-copy the golden IR and apply every structured edit in order."""
    document = deepcopy(base)
    for edit in case["edits"]:
        _apply_edit(document, edit)
    return document


def base_dimensions_mm(document: dict[str, Any]) -> list[float]:
    """Return the mutated fixture-base outer dimensions in width/depth/height order."""
    component = _component(document, "fixture_base")
    return [
        float(_dimension(component, name)["quantity"]["nominal"])
        for name in ("width", "depth", "height")
    ]


def execute_case(base: dict[str, Any], case: dict[str, Any], backend: object) -> object:
    """Apply a corpus case and run it through the requested geometry slice."""
    from .service import build_fixture_assembly, build_fixture_base

    document = apply_case(base, case)
    if case["operation"] == "fixture_base":
        return build_fixture_base(document, backend)
    return build_fixture_assembly(document, backend)
