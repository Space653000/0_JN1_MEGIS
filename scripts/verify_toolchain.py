"""Verify the locked G0 toolchain and a minimal CadQuery solid."""

from __future__ import annotations

import importlib.metadata
import json
import platform
from pathlib import Path
import subprocess
import sys

import cadquery as cq


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "environment" / "toolchain.lock.json"


def command_version(command: list[str]) -> str:
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    ).stdout.strip().removeprefix("v")


def main() -> None:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    runtime = lock["runtime"]
    cad = lock["cad"]

    executable = Path(sys.executable).resolve()
    if not executable.is_relative_to(ROOT):
        raise AssertionError(f"Python is outside the repository: {executable}")
    if executable.parent.parent.name != ".venv":
        raise AssertionError(f"Expected repository .venv, got: {executable}")

    assert platform.python_version() == runtime["python"]
    assert platform.machine() == lock["supportedHost"]["pythonArchitecture"]
    assert importlib.metadata.version("pip") == runtime["pip"]
    assert command_version(["node", "--version"]) == runtime["node"]
    npm_command = "npm.cmd" if sys.platform == "win32" else "npm"
    assert command_version([npm_command, "--version"]) == runtime["npm"]
    assert importlib.metadata.version("cadquery") == cad["cadquery"]
    assert importlib.metadata.version("cadquery-ocp") == cad["cadqueryOcpDistribution"]
    assert importlib.metadata.version("vtk") == cad["vtk"]
    assert importlib.metadata.version("jsonschema") == lock["contracts"]["jsonschema"]

    solid = cq.Workplane("XY").box(10, 20, 30).val()
    assert solid.isValid()
    assert len(solid.Solids()) == 1
    assert solid.Volume() == 6000.0

    print(
        json.dumps(
            {
                "status": "passed",
                "python": runtime["python"],
                "node": runtime["node"],
                "cadquery": cad["cadquery"],
                "openCascade": cad["openCascadeModule"],
                "solidValid": True,
                "solidVolume": solid.Volume(),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
