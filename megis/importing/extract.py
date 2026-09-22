"""Safe import public API (G4-IMP-001).

``extract_import_metadata`` is the only entry point the rest of MEGIS uses to
pull metadata from an untrusted STEP or DXF file.  It runs the guard in this
process, then spawns the isolated worker in a separate subprocess under a
hard timeout.  Timeouts and worker failures are translated to ``MEGIS-IMP-*``
errors; a successful run returns an ``ImportReport`` whose schema only admits
provable fields and always marks ``derivedFromImport``.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from megis.errors import MegisError

from .guard import guard_format_and_size
from .policy import MAX_FILE_BYTES, MAX_ENTITY_COUNT, WORKER_TIMEOUT_SECONDS
from .report import ImportReport, validate_import_report


def extract_import_metadata(
    source: str | Path,
    *,
    expected_format: str | None = None,
    max_bytes: int = MAX_FILE_BYTES,
    timeout_seconds: float = WORKER_TIMEOUT_SECONDS,
    max_entities: int = MAX_ENTITY_COUNT,
) -> ImportReport:
    """Run the safe metadata extraction pipeline for an untrusted CAD file.

    Raises ``MegisError`` with a ``MEGIS-IMP-*`` code on any rejection,
    timeout or parser failure.  A successful call returns only provable
    metadata and never fabricates values or raises a module's capability.
    """
    path = Path(source)
    detected = guard_format_and_size(
        path, max_bytes=max_bytes, expected_format=expected_format
    )

    root = Path(__file__).resolve().parents[2]
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "megis.importing.worker",
                "--format",
                detected,
                "--input",
                str(path),
                "--max-entities",
                str(max_entities),
            ],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            env=None,
        )
    except subprocess.TimeoutExpired as error:
        raise MegisError(
            "MEGIS-IMP-004",
            engineer_detail={
                "subject": str(path),
                "format": detected,
                "timeout_seconds": timeout_seconds,
            },
        ) from error

    if completed.returncode != 0:
        raise MegisError(
            "MEGIS-IMP-003",
            engineer_detail={
                "subject": str(path),
                "format": detected,
                "returncode": completed.returncode,
                "stderr": (completed.stderr or "")[-500:],
            },
        )

    try:
        payload = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as error:
        raise MegisError(
            "MEGIS-IMP-003",
            engineer_detail={
                "subject": str(path),
                "format": detected,
                "detail": "worker returned invalid JSON",
            },
        ) from error

    if "error" in payload:
        code = payload["error"].get("code", "MEGIS-IMP-003")
        detail = payload["error"].get("detail")
        raise MegisError(
            code,
            engineer_detail={
                "subject": str(path),
                "format": detected,
                "workerDetail": detail,
            },
        )

    report = payload.get("report")
    if not isinstance(report, dict):
        raise MegisError(
            "MEGIS-IMP-003",
            engineer_detail={"subject": str(path), "detail": "worker returned no report"},
        )

    validate_import_report(report)
    return ImportReport.from_worker(report)


__all__ = ["extract_import_metadata"]
