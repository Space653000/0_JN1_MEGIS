"""Module composition graph operations (G4-MOD-002)."""

from .module_graph import (
    COMPOSABLE_TYPES,
    CompositionResult,
    CompositionValidationError,
    DecompositionResult,
    compose_module,
    decompose_module,
    module_component_ids,
    pinned_module_version,
)

__all__ = [
    "COMPOSABLE_TYPES",
    "CompositionResult",
    "CompositionValidationError",
    "DecompositionResult",
    "compose_module",
    "decompose_module",
    "module_component_ids",
    "pinned_module_version",
]
