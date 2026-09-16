from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8-sig"))


def assert_file(relative_path: str, expected_bytes: int, expected_sha256: str) -> None:
    path = ROOT / relative_path
    assert path.is_file(), f"Missing artifact: {relative_path}"
    content = path.read_bytes()
    assert len(content) == expected_bytes, f"Byte count mismatch: {relative_path}"
    assert sha256(content).hexdigest() == expected_sha256, f"SHA-256 mismatch: {relative_path}"


def verify_cad_artifacts() -> int:
    manifest = load_json("artifacts/g0-cad/manifest.json")
    assert manifest["classification"] == "FEASIBILITY_SPIKE"
    assert manifest["maturity"] == "PROTOTYPE"
    assert manifest["engineeringReviewRequired"] is True
    count = 0
    for record in manifest["artifacts"].values():
        assert_file(
            f"artifacts/g0-cad/{record['path']}",
            record["bytes"],
            record["sha256"],
        )
        count += 1
    return count


def verify_drawing_artifacts() -> int:
    evidence = load_json("artifacts/g0-freecad/verification.json")
    assert evidence["decision"] == "fallback"
    assert evidence["boundary"]["engineeringReviewRequired"] is True
    assert evidence["boundary"]["manufacturingRelease"] is False
    count = 0
    for record in evidence["artifacts"].values():
        assert_file(
            f"artifacts/g0-freecad/{record['path']}",
            record["bytes"],
            record["sha256"],
        )
        count += 1
    return count


def verify_simulation_decision() -> int:
    inventory = load_json("artifacts/g0-sim/inventory.json")
    decision = load_json("environment/comsol.decision.json")
    assert inventory["summary"]["decision"] == "out_of_scope"
    assert inventory["summary"]["blocksCoreGate"] is False
    assert decision["decision"] == inventory["summary"]["decision"]
    assert decision["blocksCoreGate"] is False
    return 2


def main() -> None:
    verified = verify_cad_artifacts() + verify_drawing_artifacts() + verify_simulation_decision()
    print(f"Artifact smoke test passed: {verified} records verified")


if __name__ == "__main__":
    main()
