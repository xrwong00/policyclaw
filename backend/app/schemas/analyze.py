"""/api/analyze pipeline outputs — verdict, health score, aggregated response.

`AnalyzeResponse` uses a forward reference to `HealthScore` so the field can be
optional without importing the concrete type at class-body time. The
`model_rebuild()` call at the bottom resolves the forward ref once the module
finishes loading.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import Citation, ConfidenceBand


class VerdictLabel(str, Enum):
    KEEP = "keep"
    DOWNGRADE = "downgrade"
    SWITCH = "switch"
    DUMP = "dump"


class Reason(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    detail: str = Field(min_length=8)
    citation: Citation


class PolicyVerdict(BaseModel):
    policy_id: str
    verdict: VerdictLabel
    confidence_score: float = Field(ge=0.0, le=100.0)
    confidence_band: ConfidenceBand
    projected_10y_premium_myr: float = Field(ge=0)
    projected_10y_savings_myr: float = Field(ge=0)
    reasons: list[Reason] = Field(min_length=2, max_length=5)
    disclaimer: Literal[
        "Decision support only. PolicyClaw is not a licensed financial advisor."
    ] = "Decision support only. PolicyClaw is not a licensed financial advisor."


class HealthScore(BaseModel):
    overall: int = Field(ge=0, le=100)
    coverage_adequacy: int = Field(ge=0, le=25)
    affordability: int = Field(ge=0, le=25)
    premium_stability: int = Field(ge=0, le=25)
    clarity_trust: int = Field(ge=0, le=25)
    narrative_en: str = Field(min_length=1, max_length=500)
    narrative_bm: str = Field(min_length=1, max_length=500)
    confidence_score: float = Field(ge=0.0, le=100.0)
    confidence_band: ConfidenceBand


class AnalysisCitation(BaseModel):
    source: str = Field(min_length=1)
    page: int = Field(ge=1)
    excerpt: str = Field(min_length=1)


class AnalyzeResponse(BaseModel):
    verdict: VerdictLabel
    projected_savings: float = Field(ge=0)
    overlap_detected: bool
    bnm_rights_detected: bool
    confidence_score: float = Field(ge=0.0, le=100.0)
    summary_reasons: list[str] = Field(min_length=1, max_length=6)
    citations: list[AnalysisCitation] = Field(min_length=1, max_length=12)

    # 3-call /api/analyze pipeline outputs (optional, defaulted for backward compat).
    # ClawView annotations are served by /v1/clawview separately — not carried here.
    reasons: list[Reason] = Field(default_factory=list, max_length=5)
    projected_10y_premium_myr: float = Field(default=0.0, ge=0)
    projected_10y_savings_myr: float = Field(default=0.0, ge=0)
    health_score: "HealthScore | None" = None
    analysis_id: str = ""
    cached: bool = False
    needs_rider: bool = False


# Forward-ref to HealthScore resolves here since both classes live in this module.
AnalyzeResponse.model_rebuild()
