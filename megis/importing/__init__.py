"""Safe STEP / DXF metadata extraction (G4-IMP-001).

This package implements the blueprint section 12 import policy: untrusted CAD
files are only parsed inside an isolated subprocess worker, bounded by file
size, timeout and entity-count limits, and the public API only admits provable
metadata that is marked ``derived_from_import`` and never elevates a module's
capability level.
"""

from .extract import extract_import_metadata
from .policy import (
    MAX_ENTITY_COUNT,
    MAX_FILE_BYTES,
    SUPPORTED_FORMATS,
    WORKER_TIMEOUT_SECONDS,
)
from .report import (
    BoundingBoxMm,
    ImportReport,
    validate_import_report,
    validate_report_schema,
)
from .worker import (
    DxfMetadata,
    EntityBudgetError,
    StepMetadata,
    count_step_entities,
    extract_dxf_metadata,
    extract_step_metadata,
)

__all__ = [
    "BoundingBoxMm",
    "DxfMetadata",
    "EntityBudgetError",
    "StructuralIntegrityError",
    "ImportReport",
    "MAX_ENTITY_COUNT",
    "MAX_FILE_BYTES",
    "StepMetadata",
    "SUPPORTED_FORMATS",
    "WORKER_TIMEOUT_SECONDS",
    "count_step_entities",
    "check_dxf_structure",
    "check_step_structure",
    "extract_dxf_metadata",
    "extract_import_metadata",
    "extract_step_metadata",
    "validate_report_schema",
    "validate_import_report",
]
