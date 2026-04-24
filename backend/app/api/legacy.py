"""Scaffolded / legacy endpoints: `/v1/policies/upload`, `/v1/simulate/premium`,
`/v1/verdict`, and the `/v1/ai/*` family (F1/F2/F4/F7/F9/F11).

Several of the `/v1/ai/*` handlers return mock data — this is documented on each
endpoint and in CLAUDE.md. Kept together in one module so the production routes
(analyze / clawview / futureclaw) stay uncluttered.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile

from app.core.glm_client import config as ai_config
from app.schemas import (
    BNMRightsScannerResponse,
    CitationVaultResponse,
    MultilingualExplanation,
    OverlapMapResponse,
    PolicyInput,
    PolicyVerdict,
    PolicyXRayResponse,
    PremiumSimulationResponse,
    ScenarioProjection,
    UploadPolicyResponse,
    VoiceInterrogationResponse,
    VoiceQuery,
)
from app.services.ai_service import (
    analyze_overlap_map,
    analyze_policy_verdict,
    analyze_policy_xray,
    explain_multilingual,
    interrogate_policy_voice,
    scan_bnm_rights,
    vault_citations,
)
from app.services.simulation import project_premiums

router = APIRouter(tags=["legacy"])


@router.post("/v1/policies/upload", response_model=UploadPolicyResponse)
async def upload_policy(file: UploadFile = File(...)) -> UploadPolicyResponse:
    # Metadata-only endpoint — storage integration is post-MVP.
    payload = await file.read()
    return UploadPolicyResponse(
        policy_id=str(uuid4()),
        filename=Path(file.filename or "unknown.pdf").name,
        size_bytes=len(payload),
        message="File received. Extraction pipeline will be connected in next slice.",
    )


@router.post("/v1/simulate/premium", response_model=PremiumSimulationResponse)
def simulate_premium(policy: PolicyInput) -> PremiumSimulationResponse:
    projections = project_premiums(
        annual_premium_myr=policy.annual_premium_myr,
        monthly_income_myr=policy.projected_income_monthly_myr,
        annual_income_growth_pct=policy.expected_income_growth_pct,
    )

    return PremiumSimulationResponse(
        policy_id=f"{policy.insurer}-{policy.plan_name}".lower().replace(" ", "-"),
        scenarios=[
            ScenarioProjection(
                scenario=item.scenario,
                annual_inflation_pct=item.annual_inflation_pct,
                yearly_premium_myr=item.yearly_premium_myr,
                cumulative_10y_myr=item.cumulative_10y_myr,
                breakpoint_year=item.breakpoint_year,
            )
            for item in projections
        ],
    )


@router.post("/v1/verdict", response_model=PolicyVerdict)
async def get_verdict(policy: PolicyInput) -> PolicyVerdict:
    projections = project_premiums(
        annual_premium_myr=policy.annual_premium_myr,
        monthly_income_myr=policy.projected_income_monthly_myr,
        annual_income_growth_pct=policy.expected_income_growth_pct,
    )
    realistic = next(item for item in projections if item.scenario == "realistic")
    return await analyze_policy_verdict(policy, realistic.cumulative_10y_myr)


# ===== AI-POWERED ENDPOINTS (F1/F2/F4/F7/F9/F11 — some return mock data) =====


@router.post("/v1/ai/policy-xray", response_model=PolicyXRayResponse)
async def policy_xray(policy: PolicyInput) -> PolicyXRayResponse:
    """F1 — Policy X-Ray: extract and translate clauses into plain language."""
    policy_id = f"{policy.insurer}-{policy.plan_name}".lower().replace(" ", "-")
    return await analyze_policy_xray(policy, policy_id)


@router.post("/v1/ai/overlap-map", response_model=OverlapMapResponse)
async def overlap_map(policies: list[PolicyInput]) -> OverlapMapResponse:
    """F2 — Overlap Map: detect coverage overlap across multiple policies."""
    analysis_id = str(uuid4())
    return await analyze_overlap_map(policies, analysis_id)


@router.post("/v1/ai/bnm-rights-scanner", response_model=BNMRightsScannerResponse)
async def bnm_rights_scanner(policy: PolicyInput) -> BNMRightsScannerResponse:
    """F4 — BNM Rights Scanner: check policy eligibility for BNM protections."""
    policy_id = f"{policy.insurer}-{policy.plan_name}".lower().replace(" ", "-")
    return await scan_bnm_rights(policy, policy_id)


@router.post("/v1/ai/voice-interrogation", response_model=VoiceInterrogationResponse)
async def voice_interrogation(query: VoiceQuery) -> VoiceInterrogationResponse:
    """F7 — Voice Policy Interrogation: answer questions about policies."""
    return await interrogate_policy_voice(
        question=query.transcript,
        language=query.language,
        policy_ids=query.policy_ids,
    )


@router.get("/v1/ai/multilingual-explainer/{subject}")
async def multilingual_explainer(
    subject: str, target_language: str = "en"
) -> MultilingualExplanation:
    """F9 — Multi-lingual Explainer: generate explanations in BM/EN/ZH/Hokkien."""
    return await explain_multilingual(subject, target_language)


@router.get("/v1/ai/citations/{analysis_id}")
async def citations(analysis_id: str, policy_count: int = 1) -> CitationVaultResponse:
    """F11 — Citation Vault: retrieve citations and confidence scores."""
    return await vault_citations(analysis_id, policy_count)


@router.get("/v1/ai/status")
def ai_status() -> dict:
    """Report whether GLM is configured and which model is active."""
    return {
        "ai_enabled": ai_config.enabled,
        "mode": "GLM API" if ai_config.enabled else "Mock Data",
        "model": ai_config.model if ai_config.enabled else "N/A",
        "features": [
            "policy_xray (F1)",
            "overlap_map (F2)",
            "bnm_rights_scanner (F4)",
            "voice_interrogation (F7)",
            "multilingual_explainer (F9)",
            "citations (F11)",
        ],
    }
