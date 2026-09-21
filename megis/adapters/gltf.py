"""Deterministic minimal glTF 2.0 export/import bridge (stdlib only).

G2-CAD-004 uses this bridge to prove that the exported binary STL can be
translated into a standard, reloadable glTF 2.0 document without adding an
unapproved third-party dependency. The writer derives vertices from the binary
STL, so glTF bounding-box and triangle-count evidence can be cross-checked
against the STL structural reload within exact tolerance.
"""

from __future__ import annotations

import base64
from hashlib import sha256
import json
import struct
from pathlib import Path
from typing import Any

GENERATOR = "MEGIS G2-CAD-004 glTF bridge 1.0.0"
_COMPONENT_FLOAT = 5126
_COMPONENT_16 = 5123
_COMPONENT_32 = 5125
_ARRAY_BUFFER = 34962
_ELEMENT_ARRAY_BUFFER = 34963
_BBOX_TOLERANCE_MM = 0.001


def _f32_bytes(vertices: list[tuple[float, float, float]]) -> bytes:
    return b"".join(struct.pack("<3f", *vertex) for vertex in vertices)


def write_gltf_from_stl(stl_path: Path, gltf_path: Path) -> dict[str, Any]:
    """Build a minimal deterministic glTF 2.0 document from a binary STL."""
    payload = stl_path.read_bytes()
    if len(payload) < 84:
        raise ValueError("STL is truncated")
    triangle_count = struct.unpack_from("<I", payload, 80)[0]
    if len(payload) != 84 + triangle_count * 50:
        raise ValueError("STL byte length does not match its triangle count")
    if triangle_count == 0:
        raise ValueError("STL contains no triangles")
    vertices: list[tuple[float, float, float]] = []
    vertex_index: dict[bytes, int] = {}
    indices: list[int] = []
    for triangle in range(triangle_count):
        offset = 84 + triangle * 50
        triangle_vertices = [
            struct.unpack_from("<3f", payload, offset + 12),
            struct.unpack_from("<3f", payload, offset + 24),
            struct.unpack_from("<3f", payload, offset + 36),
        ]
        triangle_indices: list[int] = []
        for vertex in triangle_vertices:
            key = struct.pack("<3f", *vertex)
            index = vertex_index.get(key)
            if index is None:
                index = len(vertices)
                vertex_index[key] = index
                vertices.append((float(vertex[0]), float(vertex[1]), float(vertex[2])))
            triangle_indices.append(index)
        indices.extend(triangle_indices)
    position_bytes = _f32_bytes(vertices)
    use_16_bit = len(vertices) <= 65535
    index_component_type = _COMPONENT_16 if use_16_bit else _COMPONENT_32
    index_component_name = "H" if use_16_bit else "I"
    index_bytes = struct.pack(f"<{len(indices)}{index_component_name}", *indices)
    buffer_bytes = position_bytes + index_bytes
    minima = [min(vertex[axis] for vertex in vertices) for axis in range(3)]
    maxima = [max(vertex[axis] for vertex in vertices) for axis in range(3)]
    try:
        encoded = base64.b64encode(buffer_bytes).decode("ascii")
    except Exception as error:
        raise ValueError("glTF buffer encoding failed") from error
    gltf = {
        "asset": {"version": "2.0", "generator": GENERATOR},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [
            {"primitives": [{"attributes": {"POSITION": 0}, "indices": 1, "mode": 4}]}
        ],
        "buffers": [
            {
                "byteLength": len(buffer_bytes),
                "uri": "data:application/octet-stream;base64," + encoded,
            }
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(position_bytes), "target": _ARRAY_BUFFER},
            {"buffer": 0, "byteOffset": len(position_bytes), "byteLength": len(index_bytes), "target": _ELEMENT_ARRAY_BUFFER},
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": _COMPONENT_FLOAT,
                "count": len(vertices),
                "type": "VEC3",
                "min": minima,
                "max": maxima,
            },
            {
                "bufferView": 1,
                "componentType": index_component_type,
                "count": len(indices),
                "type": "SCALAR",
            },
        ],
    }
    gltf_path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(gltf, sort_keys=True, separators=(",", ":")).encode("utf-8")
    gltf_path.write_bytes(raw)
    return {
        "generator": GENERATOR,
        "vertexCount": len(vertices),
        "triangleCount": triangle_count,
        "indexCount": len(indices),
        "indexComponentType": index_component_type,
        "byteLength": len(buffer_bytes),
        "boundingBoxMm": [maxima[i] - minima[i] for i in range(3)],
        "sha256": sha256(raw).hexdigest(),
    }


def _read_buffer(gltf: dict[str, Any], source: Path) -> bytes:
    buffers = gltf.get("buffers") or []
    if not buffers:
        raise ValueError("glTF has no buffers")
    buffer = buffers[0]
    uri = str(buffer.get("uri", ""))
    if uri.startswith("data:") and "," in uri:
        data = base64.b64decode(uri.split(",", 1)[1])
    else:
        data = (source.parent / uri).read_bytes()
    if len(data) != int(buffer.get("byteLength", -1)):
        raise ValueError("glTF buffer byteLength mismatch")
    return data


def reload_gltf(gltf_path: Path) -> dict[str, Any]:
    """Structurally reload a minimal glTF 2.0 document and re-derive geometry."""
    raw = gltf_path.read_bytes()
    try:
        gltf = json.loads(raw.decode("utf-8"))
    except Exception as error:
        raise ValueError("glTF is not valid JSON") from error
    asset = gltf.get("asset") or {}
    if not str(asset.get("version", "")).startswith("2."):
        raise ValueError("glTF asset version is not 2.x")
    if not isinstance(gltf.get("scenes"), list) or not gltf["scenes"]:
        raise ValueError("glTF has no scenes")
    scene_index = int(gltf.get("scene", 0))
    if not (0 <= scene_index < len(gltf["scenes"])):
        raise ValueError("glTF scene index out of bounds")
    accessors = gltf.get("accessors") or []
    buffer_views = gltf.get("bufferViews") or []
    if len(accessors) < 2 or len(buffer_views) < 2:
        raise ValueError("glTF is missing required accessors/bufferViews")
    data = _read_buffer(gltf, gltf_path)

    position_accessor = accessors[0]
    position_view = buffer_views[position_accessor["bufferView"]]
    if (
        position_accessor.get("componentType") != _COMPONENT_FLOAT
        or position_accessor.get("type") != "VEC3"
    ):
        raise ValueError("glTF position accessor is not float32 VEC3")
    vertex_count = int(position_accessor["count"])
    view_offset = int(position_view.get("byteOffset", 0))
    position_bytes = data[view_offset : view_offset + int(position_view["byteLength"])]
    if len(position_bytes) < vertex_count * 12:
        raise ValueError("glTF position buffer is truncated")
    positions = [
        struct.unpack_from("<3f", position_bytes, index * 12)
        for index in range(vertex_count)
    ]
    if vertex_count == 0:
        raise ValueError("glTF has no vertices")
    minima = [min(position[axis] for position in positions) for axis in range(3)]
    maxima = [max(position[axis] for position in positions) for axis in range(3)]
    declared_min = position_accessor.get("min")
    declared_max = position_accessor.get("max")
    if declared_min is not None and declared_max is not None:
        for axis in range(3):
            if abs(float(declared_min[axis]) - minima[axis]) > _BBOX_TOLERANCE_MM:
                raise ValueError("glTF accessor min mismatch")
            if abs(float(declared_max[axis]) - maxima[axis]) > _BBOX_TOLERANCE_MM:
                raise ValueError("glTF accessor max mismatch")

    index_accessor = accessors[1]
    index_view = buffer_views[index_accessor["bufferView"]]
    index_component = int(index_accessor.get("componentType", 0))
    index_size = {_COMPONENT_16: 2, _COMPONENT_32: 4}.get(index_component)
    if index_size is None:
        raise ValueError("glTF index accessor has an unsupported componentType")
    index_offset = int(index_view.get("byteOffset", 0))
    index_bytes = data[index_offset : index_offset + int(index_view["byteLength"])]
    index_count = int(index_accessor["count"])
    if len(index_bytes) < index_count * index_size:
        raise ValueError("glTF index buffer is truncated")
    index_component_name = "H" if index_component == _COMPONENT_16 else "I"
    indices = list(
        struct.unpack(f"<{index_count}{index_component_name}", index_bytes[: index_count * index_size])
    )
    if indices and max(indices) >= vertex_count:
        raise ValueError("glTF index out of range")
    triangle_count = index_count // 3
    if triangle_count == 0:
        raise ValueError("glTF has no triangles")
    return {
        "valid": True,
        "vertexCount": vertex_count,
        "triangleCount": triangle_count,
        "indexCount": index_count,
        "indexComponentType": index_component,
        "boundingBoxMm": [maxima[i] - minima[i] for i in range(3)],
        "assetVersion": str(asset["version"]),
        "sha256": sha256(raw).hexdigest(),
    }
