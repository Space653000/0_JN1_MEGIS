"""Format-specific deterministic normalization for STEP, DXF, and STL."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
import struct
from typing import Any

from .fingerprint import FINGERPRINT_POLICY_VERSION, canonical_json


STEP_FILE_NAME = (
    "FILE_NAME('MEGIS','1970-01-01T00:00:00',('MEGIS'),('MEGIS'),"
    "'MEGIS STEP processor','MEGIS','');"
)
STL_HEADER = b"MEGIS BINARY STL | policy 1.0.0"
_DXF_HEADER_VALUES = {
    "$LASTSAVEDBY": ("1", "MEGIS"),
    "$TDCREATE": ("40", "2440587.5"),
    "$TDUCREATE": ("40", "0.0"),
    "$TDUPDATE": ("40", "2440587.5"),
    "$TDUUPDATE": ("40", "0.0"),
    "$TDINDWG": ("40", "0.0"),
    "$TDUSRTIMER": ("40", "0.0"),
    "$HANDSEED": ("5", "FFFF"),
    "$FINGERPRINTGUID": ("2", "{00000000-0000-0000-0000-000000000001}"),
    "$VERSIONGUID": ("2", "{00000000-0000-0000-0000-000000000002}"),
}


def _sort_dxf_classes(lines: list[str]) -> tuple[list[str], int]:
    """Sort DXF CLASS records whose source registry order varies by process."""

    pairs = [(lines[index], lines[index + 1]) for index in range(0, len(lines), 2)]
    section_start: int | None = None
    section_end: int | None = None
    for index in range(len(pairs) - 1):
        if pairs[index][0].strip() == "0" and pairs[index][1].strip() == "SECTION":
            if pairs[index + 1][0].strip() == "2" and pairs[index + 1][1].strip() == "CLASSES":
                section_start = index + 2
                break
    if section_start is None:
        raise ValueError("DXF CLASSES section is missing")
    for index in range(section_start, len(pairs)):
        if pairs[index][0].strip() == "0" and pairs[index][1].strip() == "ENDSEC":
            section_end = index
            break
    if section_end is None:
        raise ValueError("DXF CLASSES section is truncated")

    records: list[list[tuple[str, str]]] = []
    cursor = section_start
    while cursor < section_end:
        if pairs[cursor][0].strip() != "0" or pairs[cursor][1].strip() != "CLASS":
            raise ValueError("DXF CLASSES section contains an unexpected record")
        record_end = cursor + 1
        while record_end < section_end and pairs[record_end][0].strip() != "0":
            record_end += 1
        records.append(pairs[cursor:record_end])
        cursor = record_end

    def class_key(record: list[tuple[str, str]]) -> tuple[str, str]:
        class_name = next(
            (value.strip() for code, value in record if code.strip() == "1"), ""
        )
        cpp_name = next((value.strip() for code, value in record if code.strip() == "2"), "")
        return class_name, cpp_name

    ordered = sorted(records, key=class_key)
    sorted_pairs = pairs[:section_start]
    for record in ordered:
        sorted_pairs.extend(record)
    sorted_pairs.extend(pairs[section_end:])
    return [line for pair in sorted_pairs for line in pair], len(records)


def normalize_step_text(payload: str) -> str:
    """Replace the STEP FILE_NAME record with policy-controlled metadata."""

    normalized, count = re.subn(
        r"FILE_NAME\s*\(.*?\);",
        STEP_FILE_NAME,
        payload,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        raise ValueError("STEP payload must contain exactly one FILE_NAME record")
    normalized = re.sub(
        r"Open CASCADE STEP translator ([0-9.]+) [0-9]+",
        r"Open CASCADE STEP translator \1 0",
        normalized,
    )
    return normalized.replace("\r\n", "\n").replace("\r", "\n")


def normalize_step_file(path: Path) -> dict[str, Any]:
    before = path.read_bytes()
    normalized = normalize_step_text(before.decode("utf-8"))
    path.write_text(normalized, encoding="utf-8", newline="\n")
    return {
        "format": "STEP",
        "policyVersion": FINGERPRINT_POLICY_VERSION,
        "changed": before != path.read_bytes(),
        "fileNameTimestamp": "1970-01-01T00:00:00",
        "author": "MEGIS",
        "organization": "MEGIS",
    }


def normalize_dxf_file(path: Path) -> dict[str, Any]:
    """Normalize runtime DXF header variables without changing entities."""

    before = path.read_bytes()
    lines = before.decode("utf-8").splitlines()
    if len(lines) % 2:
        raise ValueError("DXF must contain complete group-code/value pairs")
    found: set[str] = set()
    for index, line in enumerate(lines):
        variable = line.strip()
        if variable not in _DXF_HEADER_VALUES:
            continue
        if index + 2 >= len(lines):
            raise ValueError(f"DXF header variable is truncated: {variable}")
        expected_group, value = _DXF_HEADER_VALUES[variable]
        if lines[index + 1].strip() != expected_group:
            raise ValueError(f"DXF header group mismatch for {variable}")
        lines[index + 2] = value
        found.add(variable)
    missing = sorted(set(_DXF_HEADER_VALUES) - found)
    if missing:
        raise ValueError(f"DXF header variables missing: {', '.join(missing)}")
    metadata_records = 0
    for index, line in enumerate(lines):
        match = re.fullmatch(r"([0-9]+\.[0-9]+\.[0-9]+) @ .+", line.strip())
        if match:
            lines[index] = f"{match.group(1)} @ 1970-01-01T00:00:00+00:00"
            metadata_records += 1
    lines, class_records = _sort_dxf_classes(lines)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return {
        "format": "DXF",
        "policyVersion": FINGERPRINT_POLICY_VERSION,
        "changed": before != path.read_bytes(),
        "normalizedVariables": sorted(found),
        "normalizedMetadataRecords": metadata_records,
        "sortedClassRecords": class_records,
    }


def normalize_stl_file(path: Path) -> dict[str, Any]:
    """Require binary STL and replace its 80-byte header deterministically."""

    payload = bytearray(path.read_bytes())
    if len(payload) < 84:
        raise ValueError("Binary STL must contain an 80-byte header and triangle count")
    triangle_count = struct.unpack_from("<I", payload, 80)[0]
    expected_bytes = 84 + (triangle_count * 50)
    if len(payload) != expected_bytes:
        raise ValueError("STL is not a structurally valid binary STL")
    fixed_header = STL_HEADER.ljust(80, b" ")
    changed = bytes(payload[:80]) != fixed_header
    payload[:80] = fixed_header
    path.write_bytes(payload)
    return {
        "format": "STL",
        "policyVersion": FINGERPRINT_POLICY_VERSION,
        "binary": True,
        "changed": changed,
        "triangleCount": triangle_count,
        "header": fixed_header.decode("ascii").rstrip(),
    }


def binary_stl_semantic_fingerprint(path: Path) -> dict[str, Any]:
    """Hash sorted, rounded triangle geometry independent of binary ordering."""

    payload = path.read_bytes()
    if len(payload) < 84:
        raise ValueError("STL is truncated")
    triangle_count = struct.unpack_from("<I", payload, 80)[0]
    if len(payload) != 84 + (triangle_count * 50):
        raise ValueError("STL byte length does not match its triangle count")
    triangles: list[list[list[str]]] = []
    for index in range(triangle_count):
        values = struct.unpack_from("<12fH", payload, 84 + (index * 50))
        vertices = []
        for offset in (3, 6, 9):
            vertices.append([f"{values[offset + axis]:.3f}" for axis in range(3)])
        triangles.append(sorted(vertices))
    triangles.sort()
    triangle_payload = canonical_json(triangles).encode("utf-8")
    canonical = {
        "fingerprint_policy_version": FINGERPRINT_POLICY_VERSION,
        "format": "binary_stl",
        "triangle_count": triangle_count,
        "triangles_sha256": sha256(triangle_payload).hexdigest(),
    }
    return {
        "fingerprintPolicyVersion": FINGERPRINT_POLICY_VERSION,
        "canonical": canonical,
        "semanticFingerprint": sha256(canonical_json(canonical).encode("utf-8")).hexdigest(),
    }


def dxf_vector_semantic_fingerprint(path: Path) -> dict[str, Any]:
    """Hash the sorted set of rounded DXF line-segment endpoints."""

    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) % 2 != 0:
        raise ValueError("DXF must contain complete group-code pairs")
    pairs = [
        (lines[index].strip(), lines[index + 1].strip())
        for index in range(0, len(lines), 2)
    ]
    segments: list[list[list[str]]] = []
    in_entities = False
    index = 0
    while index < len(pairs):
        code, value = pairs[index]
        if code == "0" and value == "SECTION" and index + 1 < len(pairs):
            in_entities = pairs[index + 1] == ("2", "ENTITIES")
            index += 2
            continue
        if in_entities and code == "0" and value == "ENDSEC":
            in_entities = False
        if not (in_entities and code == "0" and value == "LINE"):
            index += 1
            continue
        entity: dict[str, str] = {}
        index += 1
        while index < len(pairs) and pairs[index][0] != "0":
            entity.setdefault(pairs[index][0], pairs[index][1])
            index += 1
        required = ("10", "20", "11", "21")
        if any(group not in entity for group in required):
            raise ValueError("DXF LINE entity is missing endpoint coordinates")
        points = [
            [f"{float(entity['10']):.3f}", f"{float(entity['20']):.3f}"],
            [f"{float(entity['11']):.3f}", f"{float(entity['21']):.3f}"],
        ]
        segments.append(sorted(points))
    if not segments:
        raise ValueError("DXF contains no LINE entities")
    segments.sort()
    canonical = {
        "fingerprint_policy_version": FINGERPRINT_POLICY_VERSION,
        "format": "dxf_vector_elements",
        "edge_count": len(segments),
        "segments": segments,
    }
    return {
        "fingerprintPolicyVersion": FINGERPRINT_POLICY_VERSION,
        "canonical": canonical,
        "semanticFingerprint": sha256(canonical_json(canonical).encode("utf-8")).hexdigest(),
    }
