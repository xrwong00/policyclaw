"""ClawView (F4 / Wow 1) — clause-level risk overlay schema."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.common import ConfidenceBand


class BoundingBox(BaseModel):
    page: int = Field(ge=1)
    x0: float = Field(ge=0)
    y0: float = Field(ge=0)
    x1: float = Field(gt=0)
    y1: float = Field(gt=0)


class RiskLevel(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class ClawViewAnnotation(BaseModel):
    clause_id: str = Field(min_length=1)
    bbox: BoundingBox
    risk_level: RiskLevel
    plain_explanation_en: str = Field(min_length=1, max_length=600)
    plain_explanation_bm: str = Field(min_length=1, max_length=600)
    why_this_matters: str = Field(default="", max_length=400)
    source_page: int = Field(ge=1)


class ClawViewResponse(BaseModel):
    policy_id: str
    annotations: list[ClawViewAnnotation] = Field(min_length=1)
    red_count: int = Field(ge=0)
    yellow_count: int = Field(ge=0)
    green_count: int = Field(ge=0)
    confidence_score: float = Field(ge=0.0, le=100.0)
    confidence_band: ConfidenceBand
