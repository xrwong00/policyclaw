"""Shared Pydantic primitives — enums and citation shape used across domains."""

from __future__ import annotations

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


class ConfidenceBand(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Citation(BaseModel):
    source: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    url: str | None = None


class APIHealth(BaseModel):
    status: Literal["ok"]
    service: Literal["policyclaw-backend"]
