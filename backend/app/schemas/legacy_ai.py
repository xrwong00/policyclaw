"""Scaffolded /v1/ai/* endpoint schemas — F1/F2/F4/F7/F9/F11.

Several of these are partially or fully mock-backed today (see `backend/app/main.py`
and CLAUDE.md §58). Kept in a dedicated module so the core analyze/clawview/
futureclaw schemas aren't mixed with unfinished features.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import (
    Citation,
    ConfidenceBand,
    CoverageCategory,
    PolicyType,
)
from app.schemas.policy import PolicyClause


# ===== F1 POLICY X-RAY =====
class PolicyXRayResponse(BaseModel):
    policy_id: str
    insurer: str
    plan_name: str
    policy_type: PolicyType
    extracted_fields: dict[str, str | float | int] = Field(default_factory=dict)
    key_clauses: list[PolicyClause] = Field(min_length=1, max_length=20)
    gotcha_count: int = Field(ge=0)
    confidence_score: float = Field(ge=0.0, le=100.0)
    confidence_band: ConfidenceBand


# ===== F2 OVERLAP MAP =====
class CoverageZone(BaseModel):
    coverage_type: CoverageCategory
    policies_involved: list[str] = Field(min_length=2)
    duplicate_premium_yearly_myr: float = Field(ge=0)
    covered_amount_myr: float = Field(ge=0)
    severity: Literal["low", "medium", "high"]


class OverlapMapResponse(BaseModel):
    analysis_id: str
    total_policies: int
    overlap_zones: list[CoverageZone]
    total_duplicate_premium_yearly_myr: float = Field(ge=0)
    total_potential_savings_yearly_myr: float = Field(ge=0)
    consolidation_recommendation: str = Field(min_length=10, max_length=500)
    confidence_score: float = Field(ge=0.0, le=100.0)
    confidence_band: ConfidenceBand


# ===== F4 BNM RIGHTS SCANNER =====
class BNMRight(BaseModel):
    rule_id: str
    title: str
    description: str
    eligible: bool
    currently_applied: bool
    potential_savings_myr: float = Field(ge=0)
    demand_letter_text_en: str = Field(default="")
    demand_letter_text_bm: str = Field(default="")
    bnm_circular_reference: str


class BNMRightsScannerResponse(BaseModel):
    policy_id: str
    applicable_rights: list[BNMRight]
    total_unapplied_savings_myr: float = Field(ge=0)
    recommended_actions: list[str] = Field(min_length=1, max_length=5)
    confidence_score: float = Field(ge=0.0, le=100.0)
    confidence_band: ConfidenceBand


# ===== F7 VOICE POLICY INTERROGATION =====
class VoiceQuery(BaseModel):
    transcript: str = Field(min_length=1, max_length=500)
    language: Literal["bm", "en", "zh", "hokkien"] = "en"
    policy_ids: list[str] = Field(default_factory=list)


class VoiceInterrogationResponse(BaseModel):
    question_transcript: str
    answer_text: str = Field(min_length=1)
    answer_language: Literal["bm", "en", "zh", "hokkien"]
    citations: list[Citation] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=100.0)
    audio_url: str = Field(
        default="", description="URL to synthesized audio (future)"
    )


# ===== F9 MULTI-LINGUAL EXPLAINER =====
class MultilingualExplanation(BaseModel):
    subject: str = Field(max_length=200)
    explanation_en: str = Field(min_length=10)
    explanation_bm: str = Field(min_length=10)
    explanation_zh: str = Field(min_length=10)
    explanation_hokkien: str = Field(
        default="", description="Best-effort Hokkien"
    )
    target_audience: Literal["policyholder", "agent", "regulator"] = "policyholder"


# ===== F11 CITATION VAULT + CONFIDENCE =====
class CitationVaultEntry(BaseModel):
    citation_id: str
    claim: str = Field(min_length=5)
    source_document: str
    source_page: int = Field(ge=1)
    quote: str = Field(min_length=1)
    timestamp_utc: str
    claim_type: Literal["extraction", "verdict", "simulation", "regulation"]
    confidence_score: float = Field(ge=0.0, le=100.0)


class CitationVaultResponse(BaseModel):
    analysis_id: str
    total_citations: int
    entries: list[CitationVaultEntry]
    avg_confidence_score: float = Field(ge=0.0, le=100.0)
    low_confidence_claims: list[str] = Field(default_factory=list)
