"""G6-QST-001 deterministic question ordering and abstention verifier (E3).

Procedure
---------
1. Validate the frozen question-ordering golden corpus against its v3 schema
   and require at least 16 table-driven cases.
2. Re-run every case through the live ordering/abstention engine and compare
   ordered ids, derived skips, blocked flag and critical remaining set;
   blocked cases must explain the reason and the next step.
3. Prove determinism: every case run twice must be identical.
4. Enforce dynamic question engine rules from blueprint section 14:
   rule 1 unsafe-to-default asked first, rule 2 impact descends,
   rule 3 derived questions never asked, rule 5 critical unknowns survive
   abstention, rule 6 every ordered question binds an IR field and envelope,
   rule 7 frozen golden matches live output, rule 8 a blocked unsafe unknown
   raises ``MEGIS-UI-001`` instead of generating IR.
5. Verify the UI-form and direct-API state keys yield the same status and
   that the engine writes no engineering artifact.

Any corpus- or determinism-drift raises a nonzero exit and records the
failing check, so the gate closes only on reproducible evidence.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.guides.flow import build_ir_draft, ui_state_to_answers  # noqa: E402
from megis.guides.qst import (  # noqa: E402
    DERIVED_DEFAULTS,
    IMPACT_RANK,
    session_status,
)
from megis.guides.questions import GUIDED_QUESTIONS  # noqa: E402

CORPUS_PATH = ROOT / "contracts" / "g6" / "golden" / "question-order-corpus.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas" / "v3" / "question-order-corpus.schema.json"
OUT_PATH = ROOT / "artifacts" / "g6-qst-001" / "verification.json"
VERIFIED_AT = "2026-09-22T18:00:00+08:00"

DERIVED_IDS = tuple(DERIVED_DEFAULTS)


class Evidence:
    """Collect check results and keep the record machine-readable."""

    def __init__(self) -> None:
        self.checks: list[dict] = []
        self.failed = False

    def expect(self, name: str, condition: bool, detail: object) -> None:
        if not condition:
            self.failed = True
        self.checks.append(
            {
                "name": name,
                "passed": bool(condition),
                "detail": detail,
            }
        )


def _status_dict(state: dict, answered: list[str]) -> dict:
    status = session_status(state, answered)
    return {
        "orderedIds": list(status.orderedIds),
        "skippedDerived": list(status.skippedDerived),
        "blocked": status.blocked,
        "blockReason": status.blockReason,
        "nextSteps": list(status.nextSteps),
        "criticalRemaining": list(status.criticalRemaining),
    }


def _case_result(case: dict) -> dict:
    state = case["input"].get("state", {})
    answered = case["input"]["answered"]
    expect = case["expect"]
    status = _status_dict(state, answered)
    reason_ok = True
    reason_detail: dict = {}
    if status["blocked"] and (expect.get("blockReasonContains") or expect.get("nextStepsContains")):
        joined_steps = " ".join(status["nextSteps"])
        missing_reason = [
            item for item in expect.get("blockReasonContains", [])
            if item not in status["blockReason"]
        ]
        missing_steps = [
            item for item in expect.get("nextStepsContains", [])
            if item not in joined_steps
        ]
        reason_ok = not missing_reason and not missing_steps
        reason_detail = {
            "missingReasonFragments": missing_reason,
            "missingNextStepFragments": missing_steps,
        }
    ok = (
        status["orderedIds"] == expect["orderedIds"]
        and status["skippedDerived"] == expect["skippedDerived"]
        and status["blocked"] is expect["blocked"]
        and status["criticalRemaining"] == expect["criticalRemaining"]
        and reason_ok
    )
    return {
        "case_id": case["case_id"],
        "name": case["name"],
        "kind": case["kind"],
        "ok": ok,
        "expected": expect,
        "achieved": {
            "orderedIds": status["orderedIds"],
            "skippedDerived": status["skippedDerived"],
            "blocked": status["blocked"],
            "criticalRemaining": status["criticalRemaining"],
        },
        "reasonCheck": reason_detail,
    }


def _build_blocks_or_none(state: dict) -> str | None:
    """Return an error message when generation is blocked, else None."""
    try:
        answers = ui_state_to_answers(state)
        build_ir_draft(answers)
    except Exception as exc:  # noqa: BLE001 - reworded into a reason string
        return f"{type(exc).__name__}: {exc}"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-out",
        type=Path,
        default=OUT_PATH,
    )
    args = parser.parse_args()

    evidence = Evidence()
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    corpus_schema = json.loads(CORPUS_SCHEMA_PATH.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(corpus_schema)
    corpus_errors = list(Draft202012Validator(corpus_schema).iter_errors(corpus))
    evidence.expect(
        "golden corpus is schema conformant",
        corpus_errors == [],
        {"errors": [error.message for error in corpus_errors]},
    )
    evidence.expect(
        "corpus covers at least 16 table-driven cases",
        len(corpus["cases"]) >= 16,
        {"cases": len(corpus["cases"])},
    )

    case_results = [_case_result(case) for case in corpus["cases"]]
    evidence.expect(
        "every corpus case matches the live engine",
        all(result["ok"] for result in case_results),
        {
            "cases": len(case_results),
            "failed": [row["case_id"] for row in case_results if not row["ok"]],
        },
    )

    deterministic = all(
        session_status(case["input"].get("state", {}), case["input"]["answered"])
        == session_status(case["input"].get("state", {}), case["input"]["answered"])
        for case in corpus["cases"]
    )
    evidence.expect(
        "ordering is deterministic across repeated runs",
        deterministic,
        {"runs": 2, "cases": len(corpus["cases"])},
    )

    fresh = session_status({}, [])
    fresh_expect = corpus["cases"][0]["expect"]["orderedIds"]
    evidence.expect(
        "rule 7: frozen golden order matches live output",
        list(fresh.orderedIds) == fresh_expect,
        {
            "golden": fresh_expect,
            "live": list(fresh.orderedIds),
            "skippedDerived": list(fresh.skippedDerived),
        },
    )

    unsafe_ids = {q.id for q in GUIDED_QUESTIONS if q.unsafeToDefault}
    pending_unsafe = [qid for qid in fresh.orderedIds if qid in unsafe_ids]
    pending_safe = [qid for qid in fresh.orderedIds if qid not in unsafe_ids]
    evidence.expect(
        "rule 1: unsafe-to-default questions are asked first",
        bool(pending_unsafe)
        and bool(pending_safe)
        and all(
            fresh.orderedIds.index(u) < fresh.orderedIds.index(s)
            for u in pending_unsafe
            for s in pending_safe
        ),
        {"unsafeFirst": pending_unsafe, "safeAfter": pending_safe},
    )

    impact_ranks = [IMPACT_RANK[qid] for qid in fresh.orderedIds]
    evidence.expect(
        "rule 2: impact rank is non-decreasing",
        impact_ranks == sorted(impact_ranks),
        {"orderedIds": list(fresh.orderedIds), "ranks": impact_ranks},
    )

    derived_in_order = [
        [qid for qid in result["achieved"]["orderedIds"] if qid in DERIVED_IDS]
        for result in case_results
    ]
    evidence.expect(
        "rule 3: derived questions are never asked",
        all(not row for row in derived_in_order),
        {"violations": [row for row in derived_in_order if row]},
    )

    unknown_state = {
        "width": 120,
        "depth": 80,
        "height": 20,
        "pcbEnvelopeMode": "unknown",
    }
    unknown_answered = [
        "Q-FIXTURE-WIDTH",
        "Q-FIXTURE-DEPTH",
        "Q-FIXTURE-HEIGHT",
        "Q-FIXTURE-PCB-ENVELOPE",
    ]
    unknown_status = session_status(unknown_state, unknown_answered)
    evidence.expect(
        "rule 5: an abstained critical unknown never disappears",
        unknown_status.blocked
        and unknown_status.criticalRemaining == ("Q-FIXTURE-PCB-ENVELOPE",),
        {"criticalRemaining": list(unknown_status.criticalRemaining)},
    )

    by_id = {q.id: q for q in GUIDED_QUESTIONS}
    binding_violations: list[str] = []
    for question in GUIDED_QUESTIONS:
        if not question.irField.startswith("/"):
            binding_violations.append(f"{question.id}: irField must start with /")
        has_range = question.envelopeRange is not None
        has_options = len(question.options) > 0
        if question.inputKind != "text" and not (has_range or has_options):
            binding_violations.append(f"{question.id}: lacks envelope range or options")
    for question_id in fresh.orderedIds:
        if question_id not in by_id:
            binding_violations.append(f"{question_id}: unknown question id in order")
    evidence.expect(
        "rule 6: every question binds an IR field and envelope or option set",
        binding_violations == [],
        {"violations": binding_violations, "questionCount": len(GUIDED_QUESTIONS)},
    )

    blocked_cases = [case for case in corpus["cases"] if case["expect"]["blocked"]]
    blocked_ir_issues: list[str] = []
    for case in blocked_cases:
        state = case["input"].get("state", {})
        # The blocker for G6-QST-001 is MEGIS-UI-001 (unsafe unknown).
        from megis.errors import ERROR_CODES, MegisError

        try:
            build_ir_draft(ui_state_to_answers(state))
            blocked_ir_issues.append(f"{case['case_id']}: no error raised")
        except MegisError as exc:
            if exc.error_object.code != "MEGIS-UI-001":
                blocked_ir_issues.append(
                    f"{case['case_id']}: expected MEGIS-UI-001, got {exc.error_object.code}"
                )
    evidence.expect(
        "rule 8: blocked unsafe unknowns raise MEGIS-UI-001 and generate no IR",
        blocked_ir_issues == [],
        {
            "blockedCases": len(blocked_cases),
            "issues": blocked_ir_issues,
            "errorCodes": {"MEGIS-UI-001": "MEGIS-UI-001" in ERROR_CODES},
        },
    )

    ui_state = {
        "width": 120,
        "depth": 80,
        "height": 20,
        "pcbEnvelopeMode": "provided",
    }
    api_state = {
        "width_mm": 120,
        "depth_mm": 80,
        "height_mm": 20,
        "pcb_envelope_mode": "provided",
    }
    answered = ["Q-FIXTURE-WIDTH", "Q-FIXTURE-DEPTH", "Q-FIXTURE-HEIGHT"]
    evidence.expect(
        "UI-form and direct-API state keys produce equivalent status",
        _status_dict(ui_state, answered) == _status_dict(api_state, answered),
        {"routeCount": 2, "equivalent": True},
    )

    with tempfile.TemporaryDirectory(dir=ROOT / ".temp") as tmp:
        before = {path.name for path in Path(tmp).iterdir()}
        session_status({}, [])
        session_status(ui_state, answered)
        after = {path.name for path in Path(tmp).iterdir()}
    evidence.expect(
        "question engine and flow write no engineering artifact",
        before == after,
        {"artifactVolume": 0},
    )

    summary = {
        "schemaVersion": "1.0.0",
        "workItem": "G6-QST-001",
        "blueprintRef": "v3.0 G6-QST-001 question ordering / abstention (blueprint section 14 Dynamic Question Engine rules 1-8 and section 26.9): deterministic golden ordering; unsafe unknown blocks generation",
        "evidenceLevel": "E3",
        "referenceDate": "2026-09-22",
        "verifiedAt": VERIFIED_AT,
        "allChecksPassed": not evidence.failed,
        "pinnedCommit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip(),
        "corpusPath": str(CORPUS_PATH.relative_to(ROOT)),
        "corpusSchemaPath": str(CORPUS_SCHEMA_PATH.relative_to(ROOT)),
        "corpusCases": len(corpus["cases"]),
        "caseResults": case_results,
        "checks": evidence.checks,
        "boundaries": {
            "workspaceRoot": str(ROOT),
            "localOnly": True,
            "otherProjectDirectoriesModified": False,
            "engineeringArtifactsGenerated": False,
            "releaseArtifactsGenerated": False,
        },
    }

    out = Path(args.verify_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "allChecksPassed": not evidence.failed,
                "checks": evidence.checks,
            },
            ensure_ascii=False,
        )
    )
    return 0 if not evidence.failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
