"""Bounded, optional AI adapter surface for the guided MEGIS workflow."""

from .config import AiConfig, AiLimits, load_ai_config, validate_ai_config
from .extraction import (
    build_ir_with_confirmed_proposals,
    confirm_requirement_fields,
    parse_requirement_draft,
)
from .provider import AiProvider, ProviderRequest, ProviderResponse, RecordedStubProvider
from .service import AiAssistanceResult, AiOrchestrator, AiUsage

__all__ = [
    "AiAssistanceResult",
    "AiConfig",
    "AiLimits",
    "AiOrchestrator",
    "AiProvider",
    "AiUsage",
    "ProviderRequest",
    "ProviderResponse",
    "RecordedStubProvider",
    "build_ir_with_confirmed_proposals",
    "confirm_requirement_fields",
    "load_ai_config",
    "parse_requirement_draft",
    "validate_ai_config",
]
