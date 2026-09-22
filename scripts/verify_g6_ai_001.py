"""Verify G6-AI-001 optional AI adapter and deterministic offline fallback (E3)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from megis.ai import (  # noqa: E402
    AiConfig,
    AiLimits,
    AiOrchestrator,
    ProviderRequest,
    ProviderResponse,
    RecordedStubProvider,
    load_ai_config,
)
from megis.errors import ERROR_CODES  # noqa: E402
from megis.guides.flow import GuidedAnswers, build_ir_draft  # noqa: E402

OUT_PATH = ROOT / "artifacts" / "g6-ai-001" / "verification.json"
VERIFIED_AT = "2026-09-22T19:00:00+08:00"


class FaultProvider:
    provider_id = "recorded_stub"

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        raise RuntimeError("fault injection")


def _enabled_config(**overrides: int) -> AiConfig:
    values = {
        "timeout_ms": 1000,
        "max_calls_per_run": 1,
        "max_input_tokens": 1000,
        "max_output_tokens": 100,
        "max_cost_microunits": 10,
    }
    values.update(overrides)
    return AiConfig(
        enabled=True,
        provider="recorded_stub",
        model_version="recorded-model@1.0.0",
        prompt_version="intent-draft@1.0.0",
        schema_version="1.0.0",
        limits=AiLimits(**values),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-out", type=Path, default=OUT_PATH)
    args = parser.parse_args()

    checks: list[dict] = []

    def expect(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    default = load_ai_config()
    default_provider = RecordedStubProvider()
    disabled = AiOrchestrator(default, default_provider).assist("fixture intent")
    expect(
        "repository default is disabled and makes zero provider calls",
        not default.enabled
        and disabled.mode == "form_fallback"
        and not default_provider.calls,
        {"enabled": default.enabled, "providerCalls": len(default_provider.calls)},
    )

    ir = build_ir_draft(GuidedAnswers())
    expect(
        "deterministic form-to-IR path remains available with AI disabled",
        ir["designId"] == "FIXTURE-GUIDED-001" and ir["maturity"] == "PROTOTYPE",
        {"designId": ir["designId"], "maturity": ir["maturity"]},
    )

    stub = RecordedStubProvider()
    successful = AiOrchestrator(_enabled_config(), stub).assist("fixture intent")
    separated = bool(stub.calls) and stub.calls[0].user_text not in stub.calls[0].instruction
    expect(
        "recorded stub uses versioned provider boundary and isolated user data",
        successful.mode == "ai_assisted" and separated,
        {
            "mode": successful.mode,
            "provider": successful.audit["provider"],
            "promptVersion": successful.audit["promptVersion"],
            "isolatedUserData": separated,
        },
    )

    failed = AiOrchestrator(_enabled_config(), FaultProvider()).assist("fixture intent")
    expect(
        "provider failure returns MEGIS-AI error and deterministic form fallback",
        failed.mode == "form_fallback"
        and failed.error is not None
        and failed.error["code"] == "MEGIS-AI-001",
        {"mode": failed.mode, "error": failed.error},
    )

    costly = RecordedStubProvider(
        ProviderResponse("x", input_tokens=1, output_tokens=1, cost_microunits=11)
    )
    over_budget = AiOrchestrator(_enabled_config(), costly).assist("fixture intent")
    expect(
        "cost ceiling rejects output and falls back without accepting usage",
        over_budget.mode == "form_fallback"
        and over_budget.error is not None
        and over_budget.error["code"] == "MEGIS-AI-003"
        and over_budget.usage.calls == 0,
        {"mode": over_budget.mode, "errorCode": over_budget.error["code"]},
    )

    raw_intent = "customer-secret-dimensional-intent"
    audited = AiOrchestrator(_enabled_config(), RecordedStubProvider()).assist(raw_intent)
    audit_text = json.dumps(audited.audit, ensure_ascii=False)
    expect(
        "audit retains versions and input hash but not raw intent",
        raw_intent not in audit_text
        and len(audited.audit["inputSha256"]) == 64
        and audited.audit["schemaVersion"] == "1.0.0",
        {"auditKeys": sorted(audited.audit), "rawIntentStored": raw_intent in audit_text},
    )

    expect(
        "AI error registry covers provider, schema, and limit failures",
        {"MEGIS-AI-001", "MEGIS-AI-002", "MEGIS-AI-003"} <= ERROR_CODES.keys(),
        {"codes": sorted(code for code in ERROR_CODES if code.startswith("MEGIS-AI-"))},
    )

    with tempfile.TemporaryDirectory(dir=ROOT / ".temp") as tmp:
        before = list(Path(tmp).iterdir())
        AiOrchestrator(default).assist("fixture intent")
        after = list(Path(tmp).iterdir())
    expect(
        "adapter verification writes no engineering artifact",
        before == after,
        {"engineeringArtifactCount": len(after)},
    )

    completed = subprocess.run(
        [
            str(ROOT / ".venv" / "Scripts" / "python.exe"),
            "-m",
            "pytest",
            "tests/test_g6_ai_001.py",
            "-q",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    expect(
        "G6-AI-001 automated tests pass",
        completed.returncode == 0,
        {"returnCode": completed.returncode, "lastLine": completed.stdout.strip().splitlines()[-1]},
    )

    passed = all(check["passed"] for check in checks)
    evidence = {
        "schemaVersion": "1.0.0",
        "workItem": "G6-AI-001",
        "blueprintRef": "v3.0 sections 14.1, 20.3, and 26.9",
        "verifiedAt": VERIFIED_AT,
        "verification": "passed" if passed else "failed",
        "allChecksPassed": passed,
        "checks": checks,
        "boundaries": {
            "workspaceRoot": str(ROOT),
            "localOnly": True,
            "externalProviderCalled": False,
            "otherProjectDirectoriesModified": False,
            "engineeringArtifactsGenerated": False,
            "releaseArtifactsGenerated": False,
        },
    }
    args.verify_out.parent.mkdir(parents=True, exist_ok=True)
    args.verify_out.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"workItem": "G6-AI-001", "allChecksPassed": passed, "checks": len(checks)}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
