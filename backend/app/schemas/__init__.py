"""Public schemas package — re-exports keep `from app.schemas import X` stable.

Split by domain (common / policy / analyze / clawview / futureclaw / legacy_ai)
so adding or editing one concern doesn't force a giant-file re-read. Import
paths for callers are unchanged.
"""

from app.schemas.analyze import (
    AnalysisCitation,
    AnalyzeResponse,
    HealthScore,
    PolicyVerdict,
    Reason,
    VerdictLabel,
)
from app.schemas.clawview import (
    BoundingBox,
    ClawViewAnnotation,
    ClawViewResponse,
    RiskLevel,
)
from app.schemas.common import (
    APIHealth,
    Citation,
    ConfidenceBand,
    CoverageCategory,
    PolicyType,
)
from app.schemas.futureclaw import (
    LifeEvent,
    LifeEventScenario,
    LifeEventSimulationResponse,
    PremiumSimulationResponse,
    ScenarioProjection,
)
from app.schemas.legacy_ai import (
    BNMRight,
    BNMRightsScannerResponse,
    CitationVaultEntry,
    CitationVaultResponse,
    CoverageZone,
    MultilingualExplanation,
    OverlapMapResponse,
    PolicyXRayResponse,
    VoiceInterrogationResponse,
    VoiceQuery,
)
from app.schemas.policy import (
    ExtractedPolicyProfile,
    ExtractPolicyProfileResponse,
    PolicyClause,
    PolicyInput,
    UploadPolicyResponse,
)

__all__ = [
    # common
    "APIHealth",
    "Citation",
    "ConfidenceBand",
    "CoverageCategory",
    "PolicyType",
    # policy
    "ExtractPolicyProfileResponse",
    "ExtractedPolicyProfile",
    "PolicyClause",
    "PolicyInput",
    "UploadPolicyResponse",
    # analyze
    "AnalysisCitation",
    "AnalyzeResponse",
    "HealthScore",
    "PolicyVerdict",
    "Reason",
    "VerdictLabel",
    # clawview
    "BoundingBox",
    "ClawViewAnnotation",
    "ClawViewResponse",
    "RiskLevel",
    # futureclaw
    "LifeEvent",
    "LifeEventScenario",
    "LifeEventSimulationResponse",
    "PremiumSimulationResponse",
    "ScenarioProjection",
    # legacy /v1/ai/*
    "BNMRight",
    "BNMRightsScannerResponse",
    "CitationVaultEntry",
    "CitationVaultResponse",
    "CoverageZone",
    "MultilingualExplanation",
    "OverlapMapResponse",
    "PolicyXRayResponse",
    "VoiceInterrogationResponse",
    "VoiceQuery",
]
