from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    APIHealth,
    ClawViewResponse,
    PolicyInput,
    PolicyVerdict,
    PremiumSimulationResponse,
    ScenarioProjection,
    UploadPolicyResponse,
    PolicyXRayResponse,
    OverlapMapResponse,
    BNMRightsScannerResponse,
    VoiceQuery,
    VoiceInterrogationResponse,
    MultilingualExplanation,
    CitationVaultResponse,
    AnalyzeResponse,
    ExtractPolicyProfileResponse,
)
from app.services.simulation import project_premiums
from app.services.ai_service import (
    analyze_policy_verdict,
    analyze_policy_xray,
    analyze_overlap_map,
    scan_bnm_rights,
    interrogate_policy_voice,
    explain_multilingual,
    vault_citations,
    config as ai_config,
)
from app.services.analyze_service import run_ai_analysis
from app.services.clawview_service import annotate_policy as clawview_annotate_policy
from app.services.profile_extraction_service import extract_policy_profiles

app = FastAPI(title="PolicyClaw Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:3001",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=APIHealth)
def health() -> APIHealth:
    return APIHealth(status="ok", service="policyclaw-backend")


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def api_analyze(
    files: list[UploadFile] = File(...),
    insurer: str | None = Form(None),
    policyholder_name: str | None = Form(None),
    plan_name: str | None = Form(None),
    policy_type: str | None = Form(None),
    annual_premium_myr: float | None = Form(None),
    premium_frequency: str | None = Form(None),
    currency: str | None = Form(None),
    coverage_limit_myr: float | None = Form(None),
    effective_date: str | None = Form(None),
    renewal_date: str | None = Form(None),
    riders: str | None = Form(None),
    age_now: int | None = Form(None),
    projected_income_monthly_myr: float | None = Form(None),
    expected_income_growth_pct: float | None = Form(None),
) -> AnalyzeResponse:
    if not files:
        raise HTTPException(status_code=400, detail="At least one PDF is required")

    parsed_files: list[tuple[str, bytes]] = []
    for file in files:
        filename = Path(file.filename or "policy.pdf").name
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

        payload = await file.read()
        if not payload:
            continue
        parsed_files.append((filename, payload))

    if not parsed_files:
        raise HTTPException(status_code=400, detail="Uploaded PDFs were empty")

    profile = {
        "insurer": insurer,
        "policyholder_name": policyholder_name,
        "plan_name": plan_name,
        "policy_type": policy_type,
        "annual_premium_myr": annual_premium_myr,
        "premium_frequency": premium_frequency,
        "currency": currency,
        "coverage_limit_myr": coverage_limit_myr,
        "effective_date": effective_date,
        "renewal_date": renewal_date,
        "riders": riders,
        "age_now": age_now,
        "projected_income_monthly_myr": projected_income_monthly_myr,
        "expected_income_growth_pct": expected_income_growth_pct,
    }

    try:
        return await run_ai_analysis(parsed_files, profile)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/extract-policy-profile", response_model=ExtractPolicyProfileResponse)
async def api_extract_policy_profile(
    files: list[UploadFile] = File(...),
) -> ExtractPolicyProfileResponse:
    if not files:
        raise HTTPException(status_code=400, detail="At least one PDF is required")

    parsed_files: list[tuple[str, bytes]] = []
    for file in files:
        filename = Path(file.filename or "policy.pdf").name
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

        payload = await file.read()
        if not payload:
            continue
        parsed_files.append((filename, payload))

    if not parsed_files:
        raise HTTPException(status_code=400, detail="Uploaded PDFs were empty")

    try:
        return await extract_policy_profiles(parsed_files)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/v1/clawview", response_model=ClawViewResponse)
async def api_clawview(file: UploadFile = File(...)) -> ClawViewResponse:
    """F4 ClawView: clause-level risk highlights overlaid on the policy PDF."""
    filename = Path(file.filename or "policy.pdf").name
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded PDF was empty")

    return await clawview_annotate_policy(payload, filename, policy_id=str(uuid4()))


@app.post("/v1/policies/upload", response_model=UploadPolicyResponse)
async def upload_policy(file: UploadFile = File(...)) -> UploadPolicyResponse:
    # Metadata-only endpoint for MVP day-1. Storage integration comes next.
    payload = await file.read()
    return UploadPolicyResponse(
        policy_id=str(uuid4()),
        filename=Path(file.filename or "unknown.pdf").name,
        size_bytes=len(payload),
        message="File received. Extraction pipeline will be connected in next slice.",
    )


@app.post("/v1/simulate/premium", response_model=PremiumSimulationResponse)
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


@app.post("/v1/verdict", response_model=PolicyVerdict)
async def get_verdict(policy: PolicyInput) -> PolicyVerdict:
    projections = project_premiums(
        annual_premium_myr=policy.annual_premium_myr,
        monthly_income_myr=policy.projected_income_monthly_myr,
        annual_income_growth_pct=policy.expected_income_growth_pct,
    )
    realistic = next(item for item in projections if item.scenario == "realistic")
    return await analyze_policy_verdict(policy, realistic.cumulative_10y_myr)



# ===== AI-POWERED ENDPOINTS =====


@app.post("/v1/ai/policy-xray", response_model=PolicyXRayResponse)
async def policy_xray(policy: PolicyInput) -> PolicyXRayResponse:
    """
    F1 — Policy X-Ray: Extract and translate policy clauses into plain language.
    Returns mock data in development mode. Calls GLM API when GLM_API_KEY is set.
    """
    policy_id = f"{policy.insurer}-{policy.plan_name}".lower().replace(" ", "-")
    return await analyze_policy_xray(policy, policy_id)


@app.post("/v1/ai/overlap-map", response_model=OverlapMapResponse)
async def overlap_map(policies: list[PolicyInput]) -> OverlapMapResponse:
    """
    F2 — Overlap Map: Detect coverage overlap across multiple policies.
    Returns mock data in development mode. Calls GLM API when GLM_API_KEY is set.
    """
    from uuid import uuid4

    analysis_id = str(uuid4())
    return await analyze_overlap_map(policies, analysis_id)


@app.post("/v1/ai/bnm-rights-scanner", response_model=BNMRightsScannerResponse)
async def bnm_rights_scanner(policy: PolicyInput) -> BNMRightsScannerResponse:
    """
    F4 — BNM Rights Scanner: Check policy eligibility for BNM protections.
    Returns mock data in development mode. Calls GLM API when GLM_API_KEY is set.
    """
    policy_id = f"{policy.insurer}-{policy.plan_name}".lower().replace(" ", "-")
    return await scan_bnm_rights(policy, policy_id)


@app.post("/v1/ai/voice-interrogation", response_model=VoiceInterrogationResponse)
async def voice_interrogation(query: VoiceQuery) -> VoiceInterrogationResponse:
    """
    F7 — Voice Policy Interrogation: Answer questions about policies in multiple languages.
    Returns mock data in development mode. Calls GLM API when GLM_API_KEY is set.
    """
    return await interrogate_policy_voice(
        question=query.transcript,
        language=query.language,
        policy_ids=query.policy_ids,
    )


@app.get("/v1/ai/multilingual-explainer/{subject}")
async def multilingual_explainer(
    subject: str, target_language: str = "en"
) -> MultilingualExplanation:
    """
    F9 — Multi-lingual Explainer: Generate explanations in Bahasa, English, Mandarin, Hokkien.
    Returns mock data in development mode. Calls GLM API when GLM_API_KEY is set.
    """
    return await explain_multilingual(subject, target_language)


@app.get("/v1/ai/citations/{analysis_id}")
async def citations(analysis_id: str, policy_count: int = 1) -> CitationVaultResponse:
    """
    F11 — Citation Vault: Retrieve all citations and confidence scores from an analysis.
    Returns mock data in development mode. Queries database when persistence is enabled.
    """
    return await vault_citations(analysis_id, policy_count)


@app.get("/v1/ai/status")
def ai_status() -> dict:
    """
    Check AI service status and configuration.
    Returns whether GLM is enabled and current operating mode.
    """
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
