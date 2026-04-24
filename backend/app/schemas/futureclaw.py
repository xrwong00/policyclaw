"""FutureClaw (F6 / Wow 2) — premium projection & life-event scenarios."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import Citation, ConfidenceBand


class ScenarioProjection(BaseModel):
    scenario: Literal["optimistic", "realistic", "pessimistic"]
    annual_inflation_pct: float
    yearly_premium_myr: list[float]
    cumulative_10y_myr: float
    breakpoint_year: int | None


class PremiumSimulationResponse(BaseModel):
    policy_id: str
    scenarios: list[ScenarioProjection]


class LifeEvent(str, Enum):
    CANCER = "cancer"
    HEART_ATTACK = "heart_attack"
    DISABILITY = "disability"
    DEATH = "death"


class LifeEventScenario(BaseModel):
    event: LifeEvent
    total_event_cost_myr: float = Field(ge=0)
    covered_myr: float = Field(ge=0)
    copay_myr: float = Field(ge=0)
    out_of_pocket_myr: float = Field(ge=0)
    months_income_at_risk: float = Field(ge=0)
    alternative_out_of_pocket_myr: float | None = Field(default=None, ge=0)
    narrative_en: str = Field(min_length=1, max_length=500)
    narrative_bm: str = Field(min_length=1, max_length=500)


class LifeEventSimulationResponse(BaseModel):
    policy_id: str
    scenarios: list[LifeEventScenario] = Field(min_length=4, max_length=4)
    data_citations: list[Citation] = Field(min_length=1)
    confidence_score: float = Field(ge=0.0, le=100.0)
    confidence_band: ConfidenceBand
