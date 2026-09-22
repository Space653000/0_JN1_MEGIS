"""Deterministic benchmark runner and KPI math (G3-BEN-001)."""

from .metrics import (
    BenchmarkReport,
    CaseResult,
    DEFAULT_HEALTHY_MATURITY,
    Detection,
    SEVERITY_ORDER,
    run_benchmark,
    wilson_ci,
)

__all__ = [
    "BenchmarkReport",
    "CaseResult",
    "DEFAULT_HEALTHY_MATURITY",
    "Detection",
    "SEVERITY_ORDER",
    "run_benchmark",
    "wilson_ci",
]
