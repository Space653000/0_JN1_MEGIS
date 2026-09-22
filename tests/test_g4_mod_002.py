"""G4-MOD-002 module composition graph tests (E3).

Composing PCB / USB-C / M3 modules into the Fixture golden IR derives only
*proven* engineering constraints, clears or marks dependent constraints on
remove, never invents missing values, and pins module versions.  The golden
corpus drives one parameterised test per case; dedicated tests assert the
IR-level truthfulness contract (nominal/tolerance from provenance, module
marker, idempotence and upgrade pinning).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from megis.composition import (
    COMPOSABLE_TYPES,
    CompositionValidationError,
    compose_module,
    decompose_module,
    module_component_ids,
    pinned_module_version,
)

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "contracts" / "g4" / "golden" / "module-composition-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "module-composition-corpus.schema.json"
BASE_FIXTURE_PATH = ROOT / "contracts" / "g1" / "golden" / "reference-fixture.json"


@pytest.fixture(scope="module")
def corpus() -> dict:
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def corpus_schema() -> dict:
    return json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))


def _load_base_ir(source: dict | None) -> dict:
    if source and isinstance(source.get("source"), str):
        return json.loads((ROOT / source["source"]).read_text(encoding="utf-8"))
    return json.loads(BASE_FIXTURE_PATH.read_text(encoding="utf-8"))


def _run_operation(
    ir: dict,
    operation: str,
    module: dict | None = None,
    relationship: dict | None = None,
    module_id: str | None = None,
    component_id: str | None = None,
    allow_upgrade: bool = False,
) -> dict:
    if operation == "add_module":
        return compose_module(
            ir,
            module,
            relationship,
            component_id=component_id,
            allow_upgrade=allow_upgrade,
        ).to_dict()
    if operation == "remove_module":
        return decompose_module(ir, module_id).to_dict()
    raise ValueError(f"unsupported operation {operation}")


def test_corpus_validates_against_schema(corpus: dict, corpus_schema: dict) -> None:
    Draft202012Validator.check_schema(corpus_schema)
    errors = list(Draft202012Validator(corpus_schema).iter_errors(corpus))
    assert errors == []
    assert len(corpus["cases"]) >= 16


@pytest.mark.parametrize(
    "case",
    [
        json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["cases"][index]
        for index in range(
            len(json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["cases"])
        )
    ],
    ids=lambda case: case["case_id"],
)
def test_every_corpus_case_matches_golden(case: dict) -> None:
    input_ = case["input"]
    expect = case["expect"]
    ir = _load_base_ir(input_.get("ir"))

    for step in input_.get("setup", []):
        _run_operation(
            ir,
            step["operation"],
            step.get("module"),
            step.get("relationship"),
            None,
            step.get("component_id"),
            bool(step.get("allow_upgrade")),
        )

    if not expect["valid"]:
        with pytest.raises(CompositionValidationError) as raised:
            _run_operation(
                ir,
                input_["operation"],
                input_.get("module"),
                input_.get("relationship"),
                input_.get("module_id"),
                input_.get("component_id"),
                bool(input_.get("allow_upgrade")),
            )
        for fragment in expect.get("errorContains", []):
            assert any(fragment in message for message in raised.value.errors), fragment
        return

    observed = _run_operation(
        ir,
        input_["operation"],
        input_.get("module"),
        input_.get("relationship"),
        input_.get("module_id"),
        input_.get("component_id"),
        bool(input_.get("allow_upgrade")),
    )
    for key in (
        "changed",
        "addedComponentIds",
        "addedInterfaceIds",
        "addedRelationshipIds",
        "addedConstraintIds",
        "addedUnknownIds",
        "blockedConstraintKinds",
        "fabricatedValuesUsed",
        "upgradeBlocked",
        "pinnedModules",
        "removedComponentIds",
        "removedInterfaceIds",
        "removedRelationshipIds",
        "removedConstraintIds",
        "removedUnknownIds",
        "markedConstraintIds",
    ):
        if key in expect:
            assert observed[key] == expect[key], f"{key}: {expect[key]} != {observed[key]}"


def test_composable_types_is_closed_over_g4_grf_subset() -> None:
    assert set(COMPOSABLE_TYPES) == {
        "contains",
        "mounts_to",
        "fastens",
        "opens_through",
        "clears",
    }


def test_derived_mount_constraint_uses_proven_values_only() -> None:
    ir = json.loads(BASE_FIXTURE_PATH.read_text(encoding="utf-8"))
    module = _pcb_module("1.0.0")
    relationship = _mounts_relationship(proven=True)
    compose_module(ir, module, relationship)

    constraints = [item for item in ir["constraints"] if item["id"] == "CON-COMP-PCB-MOUNT"]
    assert len(constraints) == 1
    quantity = constraints[0]["measurement"]["quantity"]
    assert quantity["nominal"] == 4.0
    assert quantity["tolerance"] == 0.1
    assert quantity["unit"] == "mm"

    provenance = {item["id"]: item for item in ir["provenance"]}
    constraint_prov = provenance[constraints[0]["provenanceIds"][0]]
    assert constraint_prov["source"] == "derived"
    assert constraint_prov["sourceRef"] == "module:mod.pcb@1.0.0"
    assert constraints[0]["targetIds"][0] in {"COMP-PCB", "COMP-FIXTURE-BASE"}


def test_unproven_value_records_unknown_without_fabrication() -> None:
    ir = json.loads(BASE_FIXTURE_PATH.read_text(encoding="utf-8"))
    module = _pcb_module("1.0.0")
    relationship = _mounts_relationship(proven=False)
    result = compose_module(ir, module, relationship)

    assert result.added_constraint_ids == ()
    assert result.blocked_constraint_kinds == ("mount",)
    assert result.fabricated_values_used is False
    unknown = [item for item in ir["unknowns"] if item["id"] == "UNK-COMP-PCB-MOUNT"]
    assert len(unknown) == 1
    assert unknown[0]["unsafeToDefault"] is True
    assert "Proven value missing" in unknown[0]["question"]
    assert pinned_module_version(ir, "mod.pcb") == "1.0.0"


def test_recompose_same_version_is_idempotent() -> None:
    ir = json.loads(BASE_FIXTURE_PATH.read_text(encoding="utf-8"))
    module = _pcb_module("1.0.0")
    relationship = _mounts_relationship(proven=True)
    first = compose_module(ir, module, relationship)
    second = compose_module(ir, module, relationship)
    assert first.changed is True
    assert second.changed is False
    assert second.added_component_ids == ()
    assert second.added_constraint_ids == ()
    assert module_component_ids(ir, "mod.pcb") == ("COMP-PCB",)


def test_newer_version_is_pinned_without_allow_upgrade() -> None:
    ir = json.loads(BASE_FIXTURE_PATH.read_text(encoding="utf-8"))
    compose_module(ir, _pcb_module("1.0.0"), _mounts_relationship(proven=True))
    blocked = compose_module(ir, _pcb_module("1.1.0"), _mounts_relationship(proven=True))
    assert blocked.changed is False
    assert blocked.upgrade_blocked is True
    assert blocked.pinned_modules == (("mod.pcb", "1.0.0"),)
    assert pinned_module_version(ir, "mod.pcb") == "1.0.0"


def test_allow_upgrade_replaces_pinned_version() -> None:
    ir = json.loads(BASE_FIXTURE_PATH.read_text(encoding="utf-8"))
    compose_module(ir, _pcb_module("1.0.0"), _mounts_relationship(proven=True))
    upgraded = compose_module(
        ir, _pcb_module("1.1.0"), _mounts_relationship(proven=True), allow_upgrade=True
    )
    assert upgraded.changed is True
    assert pinned_module_version(ir, "mod.pcb") == "1.1.0"
    assert module_component_ids(ir, "mod.pcb") == ("COMP-PCB",)
    assert any(item["id"] == "CON-COMP-PCB-MOUNT" for item in ir["constraints"])


def test_remove_clears_and_marks_dependent_constraints() -> None:
    ir = json.loads(BASE_FIXTURE_PATH.read_text(encoding="utf-8"))
    compose_module(ir, _pcb_module("1.0.0"), _mounts_relationship(proven=True))
    removed = decompose_module(ir, "mod.pcb")
    assert removed.changed is True
    assert removed.removed_component_ids == ("COMP-PCB",)
    assert removed.removed_constraint_ids == ("CON-COMP-PCB-MOUNT",)
    assert removed.marked_constraint_ids == ("CON-COMP-PCB-MOUNT",)
    assert "COMP-FIXTURE-PCB" in [item["id"] for item in ir["components"]]
    assert all(
        item["id"] not in removed.removed_constraint_ids
        for item in ir["constraints"]
    )


def test_remove_unknown_module_is_rejected() -> None:
    ir = json.loads(BASE_FIXTURE_PATH.read_text(encoding="utf-8"))
    with pytest.raises(CompositionValidationError) as raised:
        decompose_module(ir, "mod.ghost")
    assert any("unknown module mod.ghost" in message for message in raised.value.errors)


def _pcb_module(version: str) -> dict:
    return {
        "schemaVersion": "1.0.0",
        "module_id": "mod.pcb",
        "version": version,
        "capability_level": "geometry_capable",
        "interfaces": ["board_outline"],
        "clearance_envelopes": [],
        "geometry_generator_ref": f"cad.pcb@{version}",
        "metadata": {},
        "rule_refs": [],
        "datasheet_refs": [],
    }


def _mounts_relationship(*, proven: bool) -> dict:
    provenance = ["datasheet.iso4762@2026-09-22"] if proven else []
    return {
        "schemaVersion": "1.0.0",
        "relationship_id": "rel.pcb_mounts_base",
        "type": "mounts_to",
        "source": "COMP-PCB",
        "target": "COMP-FIXTURE-BASE",
        "parameters": {
            "fastener_ref": {"value": "mod.m3@2.0.0", "provenance": ["spec.pcb@x"]},
            "boss_ref": {"value": "face.base_mount", "provenance": ["spec.pcb@x"]},
            "engagement_length_mm": {"value": 4.0, "provenance": provenance},
            "hole_alignment_tolerance_mm": {
                "value": 0.1,
                "provenance": ["datasheet.iso4762@2026-09-22"],
            },
        },
        "provenance": ["spec.pcb@2026-09-22"],
    }
