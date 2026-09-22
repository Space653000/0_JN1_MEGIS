"""Provider-neutral request/response types and an offline recorded stub."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderRequest:
    """Minimal provider payload with instructions and user data kept separate."""

    prompt_version: str
    model_version: str
    instruction: str
    user_text: str
    timeout_ms: int
    max_output_tokens: int


@dataclass(frozen=True)
class ProviderResponse:
    content: str
    input_tokens: int
    output_tokens: int
    cost_microunits: int


class AiProvider(Protocol):
    """Replaceable boundary; production providers must implement this protocol."""

    provider_id: str

    def invoke(self, request: ProviderRequest) -> ProviderResponse: ...


class RecordedStubProvider:
    """Network-free provider used by CI and G6 recorded-fixture verification."""

    provider_id = "recorded_stub"

    def __init__(self, response: ProviderResponse | None = None) -> None:
        self.response = response or ProviderResponse(
            content='{"status":"recorded_stub"}',
            input_tokens=8,
            output_tokens=4,
            cost_microunits=0,
        )
        self.calls: list[ProviderRequest] = []

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        self.calls.append(request)
        return self.response
