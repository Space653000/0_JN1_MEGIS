"""Configuration contract for the optional AI provider boundary."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = ROOT / "config" / "ai" / "provider.json"
CONFIG_SCHEMA_PATH = ROOT / "schemas" / "v3" / "ai-provider-config.schema.json"


@dataclass(frozen=True)
class AiLimits:
    timeout_ms: int
    max_calls_per_run: int
    max_input_tokens: int
    max_output_tokens: int
    max_cost_microunits: int


@dataclass(frozen=True)
class AiConfig:
    enabled: bool
    provider: str
    model_version: str | None
    prompt_version: str
    schema_version: str
    limits: AiLimits


def validate_ai_config(document: Mapping[str, Any]) -> None:
    """Validate a raw AI configuration document against the v3 contract."""

    schema = json.loads(CONFIG_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(document)),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        detail = "; ".join(error.message for error in errors)
        raise ValueError(f"AI provider configuration invalid: {detail}")


def load_ai_config(path: Path = DEFAULT_CONFIG_PATH) -> AiConfig:
    """Load the local configuration; the repository default is always disabled."""

    document = json.loads(path.read_text(encoding="utf-8"))
    validate_ai_config(document)
    limits = document["limits"]
    return AiConfig(
        enabled=document["enabled"],
        provider=document["provider"],
        model_version=document["modelVersion"],
        prompt_version=document["promptVersion"],
        schema_version=document["schemaVersion"],
        limits=AiLimits(
            timeout_ms=limits["timeoutMs"],
            max_calls_per_run=limits["maxCallsPerRun"],
            max_input_tokens=limits["maxInputTokens"],
            max_output_tokens=limits["maxOutputTokens"],
            max_cost_microunits=limits["maxCostMicrounits"],
        ),
    )
