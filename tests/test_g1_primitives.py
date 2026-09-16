from copy import deepcopy
import json
from pathlib import Path

import pytest

from megis.contracts import ContractValidationError, validate_primitives


ROOT = Path(__file__).resolve().parents[1]
VALID = json.loads(
    (ROOT / "contracts" / "g1" / "examples" / "primitives-valid.json").read_text(
        encoding="utf-8"
    )
)


def test_valid_primitives_contract() -> None:
    validate_primitives(VALID)


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (lambda doc: doc["quantities"][0].pop("unit"), "unit"),
        (lambda doc: doc["coordinateSystem"].update(handedness="left"), "right"),
        (lambda doc: doc["coordinateSystem"]["axes"].update(y="width"), "semantics must be distinct"),
        (lambda doc: doc["entityIds"].append("PROJECT-0001"), "non-unique"),
        (lambda doc: doc["provenance"][0].update(source="model_guess"), "model_guess"),
        (lambda doc: doc["knowledgeStates"][1].update(value=100), "should not be valid"),
        (lambda doc: doc["provenance"][1].pop("sourceRef"), "sourceRef"),
        (lambda doc: doc["provenance"][0].update(recordedAt="not-a-time"), "date-time"),
        (lambda doc: doc["entityIds"].append("bad id"), "does not match"),
        (lambda doc: doc["quantities"][0].update(id="DIM-MISSING-001"), "undeclared entity ID"),
        (lambda doc: doc["provenance"][0].update(subjectId="MISSING-001"), "dangling entity reference"),
        (lambda doc: doc["quantities"][1].update(min=4.0, max=2.0), "min must not exceed max"),
    ],
)
def test_invalid_primitives_are_rejected(mutate, expected: str) -> None:
    document = deepcopy(VALID)
    mutate(document)
    with pytest.raises(ContractValidationError) as caught:
        validate_primitives(document)
    assert expected in str(caught.value)
