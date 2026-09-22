"""Import safety limits and supported formats (G4-IMP-001).

These constants codify blueprint section 12 import policy: a parser runs in
an isolated subprocess, files over ``MAX_FILE_BYTES`` are rejected before any
parsing, the worker is bounded by ``WORKER_TIMEOUT_SECONDS``, and the number
of entities a parser may touch is capped by ``MAX_ENTITY_COUNT``.  Content is
only ever considered safe to inspect after the extension guard has run.
"""

from __future__ import annotations

# Blueprint proposes 50 MB and 60 s; expose both so tests can shrink them.
MAX_FILE_BYTES = 50 * 1024 * 1024
WORKER_TIMEOUT_SECONDS = 60
MAX_ENTITY_COUNT = 250_000

# Accepted extensions per supported import format.
SUPPORTED_FORMATS: dict[str, tuple[str, ...]] = {
    "STEP": (".step", ".stp"),
    "DXF": (".dxf",),
}

# Magic markers used to confirm a file's declared extension before parsing.
STEP_MAGIC = "ISO-10303-21;"
DXF_SECTION_MARKER = "SECTION"
