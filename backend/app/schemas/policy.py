"""Policy-facing inputs and extracted-profile shapes."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import PolicyType


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


class PolicyClause(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    original_text: str = Field(min_length=1)
    plain_language_en: str = Field(min_length=1)
    plain_language_bm: str = Field(min_length=1)
    gotcha_flag: bool = Field(default=False)
    source_page: int = Field(ge=1)


class ExtractedPolicyProfile(BaseModel):
    option_id: str
    display_label: str
    insurer_name: str | None = None
    policyholder_name: str | None = None
    plan_name: str | None = None
    policy_type: Literal[
        "medical", "life", "critical_illness", "takaful", "other"
    ] | None = None
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


class UploadPolicyResponse(BaseModel):
    policy_id: str
    filename: str
    size_bytes: int
    message: str
