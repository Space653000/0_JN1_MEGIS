"""Pre-parse safety guard for untrusted CAD imports (G4-IMP-001).

The guard runs in the parent process before any parser code sees the file:
it validates the extension, confirms the file's declared format against magic
markers, and enforces the size budget.  No content parsing happens here, so a
malicious payload cannot reach the parser by passing this layer.
"""

from __future__ import annotations

from pathlib import Path

from megis.errors import MegisError

from .policy import SUPPORTED_FORMATS

_STEP_MARKER = "ISO-10303-21;"
_DXF_SECTION_MARKERS = ("SECTION",)


def _first_nonempty_lines(path: Path, count: int) -> tuple[str, ...]:
    """Return a bounded number of non-empty lines from the file head."""
    lines: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        for raw in handle:
            line = raw.strip()
            if line:
                lines.append(line)
                if len(lines) >= count:
                    break
    return tuple(lines)


def guard_format_and_size(
    source: Path,
    *,
    max_bytes: int,
    expected_format: str | None = None,
) -> str:
    """Validate an import file's extension, size and content marker.

    Returns the normalised import format (``STEP`` or ``DXF``).  Raises
    ``MegisError`` with a ``MEGIS-IMP-*`` code when the file cannot be
    accepted.  ``expected_format`` may be supplied to require one specific
    format regardless of extension.
    """
    if not source.is_file():
        raise MegisError(
            "MEGIS-IMP-003",
            engineer_detail=f"import file does not exist: {source}",
        )

    size = source.stat().st_size
    if size > max_bytes:
        raise MegisError(
            "MEGIS-IMP-001",
            engineer_detail={
                "subject": str(source),
                "size_bytes": size,
                "limit_bytes": max_bytes,
            },
        )

    extension = source.suffix.lower()
    if expected_format is None:
        candidates = [
            fmt for fmt, extensions in SUPPORTED_FORMATS.items() if extension in extensions
        ]
        if not candidates:
            raise MegisError(
                "MEGIS-IMP-002",
                engineer_detail=f"unsupported extension '{extension}' for {source}",
            )
        detected = candidates[0]
    else:
        detected = expected_format.upper()
        if detected not in SUPPORTED_FORMATS:
            raise MegisError(
                "MEGIS-IMP-002",
                engineer_detail=f"unsupported format '{expected_format}'",
            )
        if extension not in SUPPORTED_FORMATS[detected]:
            raise MegisError(
                "MEGIS-IMP-002",
                engineer_detail=f"extension '{extension}' does not match {detected}",
            )

    head = _first_nonempty_lines(source, 8)

    if detected == "STEP":
        if not head or not head[0].startswith(_STEP_MARKER):
            raise MegisError(
                "MEGIS-IMP-002",
                engineer_detail=f"STEP magic marker missing in {source}",
            )
        return detected

    # DXF is a series of group-code/value pairs; require a SECTION tag in the
    # file head to distinguish a real DXF from arbitrary text.
    if not any(line in _DXF_SECTION_MARKERS for line in head):
        raise MegisError(
            "MEGIS-IMP-002",
            engineer_detail=f"DXF SECTION marker missing in {source}",
        )
    return detected


__all__ = ["guard_format_and_size"]
