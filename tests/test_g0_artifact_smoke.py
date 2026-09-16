from scripts.verify_artifacts import (
    verify_cad_artifacts,
    verify_drawing_artifacts,
    verify_simulation_decision,
)


def test_versioned_g0_artifacts_match_their_manifests() -> None:
    assert verify_cad_artifacts() == 3
    assert verify_drawing_artifacts() == 2
    assert verify_simulation_decision() == 2
