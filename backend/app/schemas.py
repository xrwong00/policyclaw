from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class PolicyType(str, Enum):
    MEDICAL = "medical"
    LIFE = "life"
    CRITICAL_ILLNESS = "critical_illness"
    TAKAFUL = "takaful"
    OTHER = "other"


class CoverageCategory(str, Enum):
    HOSPITALIZATION = "hospitalization"
    CRITICAL_ILLNESS = "critical_illness"
    DEATH_BENEFIT = "death_benefit"
    DISABILITY = "disability"
    OUTPATIENT = "outpatient"
    DENTAL = "dental"
    MATERNITY = "maternity"


class PolicyInput(BaseModel):
    insurer: str = Field(min_length=1, max_length=120)
    plan_name: str = Field(min_length=1, max_length=160)
    policy_type: PolicyType = PolicyType.MEDICAL
    annual_premium_myr: float = Field(gt=0)
    coverage_limit_myr: float = Field(gt=0)
    effective_date: date
    age_now: int = Field(ge=18, le=100)
    projected_income_monthly_myr: float = Field(gt=0)
    expected_income_growth_pct: float = Field(default=3.0, ge=0.0, le=20.0)


class Citation(BaseModel):
    source: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    locator: str = Field(min_length=1)


class ConfidenceBand(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Reason(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    detail: str = Field(min_length=8)
    citation: Citation


class VerdictLabel(str, Enum):
    KEEP = "keep"
    DOWNGRADE = "downgrade"
    SWITCH = "switch"
    DUMP = "dump"


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


class ScenarioProjection(BaseModel):
    scenario: Literal["optimistic", "realistic", "pessimistic"]
    annual_inflation_pct: float
    yearly_premium_myr: list[float]
    cumulative_10y_myr: float
    breakpoint_year: int | None


class PremiumSimulationResponse(BaseModel):
    policy_id: str
    scenarios: list[ScenarioProjection]


class UploadPolicyResponse(BaseModel):
    policy_id: str
    filename: str
    size_bytes: int
    message: str


class APIHealth(BaseModel):
    status: Literal["ok"]
    service: Literal["policyclaw-backend"]


# ===== F1 POLICY X-RAY =====
class PolicyClause(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    original_text: str = Field(min_length=1)
    plain_language_en: str = Field(min_length=1)
    plain_language_bm: str = Field(min_length=1)
    gotcha_flag: bool = Field(default=False)
    source_page: int = Field(ge=1)


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
    audio_url: str = Field(default="", description="URL to synthesized audio (future)")


# ===== F9 MULTI-LINGUAL EXPLAINER =====
class MultilingualExplanation(BaseModel):
    subject: str = Field(max_length=200)
    explanation_en: str = Field(min_length=10)
    explanation_bm: str = Field(min_length=10)
    explanation_zh: str = Field(min_length=10)
    explanation_hokkien: str = Field(default="", description="Best-effort Hokkien")
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


class ExtractedPolicyProfile(BaseModel):
    option_id: str
    display_label: str
    insurer_name: str | None = None
    policyholder_name: str | None = None
    plan_name: str | None = None
    policy_type: Literal["medical", "life", "critical_illness", "takaful", "other"] | None = None
    premium_amount: float | None = Field(default=None, ge=0)
    premium_frequency: Literal["monthly", "annual"] | None = None
    currency: str | None = None
    effective_date: str | None = None
    renewal_date: str | None = None
    coverage_limit: float | None = Field(default=None, ge=0)
    riders: list[str] = Field(default_factory=list)
    source_pages: list[int] = Field(default_factory=list)
    confidence_score: float | None = Field(default=None, ge=0.0, le=100.0)


class ExtractPolicyProfileResponse(BaseModel):
    profiles: list[ExtractedPolicyProfile] = Field(min_length=1, max_length=8)
    detected_count: int = Field(ge=1)
    notes: list[str] = Field(default_factory=list)
