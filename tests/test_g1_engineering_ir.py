from copy import deepcopy
import json
from pathlib import Path

import pytest

from megis.contracts import ContractValidationError, validate_engineering_ir


ROOT = Path(__file__).resolve().parents[1]
VALID = json.loads(
    (ROOT / "contracts" / "g1" / "examples" / "engineering-ir-valid.json").read_text(
        encoding="utf-8"
    )
)


def test_valid_engineering_ir() -> None:
    validate_engineering_ir(VALID)


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (
            lambda doc: doc["components"][0]["dimensions"][0].update(
                dimension="length", quantity={"id": "DIM-WIDTH-001", "unit": "N", "nominal": 120.0}
            ),
            "incompatible with length",
        ),
        (lambda doc: doc["relationships"][0].update(targetId="COMP-MISSING-001"), "dangling reference"),
        (lambda doc: doc["components"][1].update(id="COMP-BASE-001"), "duplicate ID"),
        (
            lambda doc: doc["constraints"][0]["measurement"]["quantity"].update(min=4.0, max=2.0),
            "min must not exceed max",
        ),
        (lambda doc: doc["requirements"][0].update(provenanceIds=["PROV-MISSING-001"]), "dangling reference"),
        (lambda doc: doc["components"][0].update(materialId="MAT-MISSING-001"), "dangling reference"),
        (
            lambda doc: doc["components"][0]["dimensions"][1]["quantity"].update(nominal=90.0),
            "nominal must not exceed max",
        ),
        (lambda doc: doc.update(maturity="PRODUCTION_READY"), "PRODUCTION_READY"),
    ],
)
def test_invalid_engineering_ir_is_rejected(mutate, expected: str) -> None:
    document = deepcopy(VALID)
    mutate(document)
    with pytest.raises(ContractValidationError) as caught:
        validate_engineering_ir(document)
    assert expected in str(caught.value)
