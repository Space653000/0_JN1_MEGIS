import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_locked_toolchain_and_cadquery_smoke() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_toolchain.py")],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    evidence = json.loads(result.stdout)
    assert evidence["status"] == "passed"
    assert evidence["solidValid"] is True
    assert evidence["solidVolume"] == 6000.0
