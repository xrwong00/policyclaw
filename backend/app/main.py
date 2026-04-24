from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field

from app.schemas import (
    APIHealth,
    Citation,
    ClawViewResponse,
    LifeEventScenario,
    LifeEventSimulationResponse,
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
from app.services.simulation import (
    compute_life_event_confidence,
    monte_carlo_affordability,
    project_premiums,
    simulate_life_events,
)
from app.services.futureclaw_narrative import generate_life_event_narratives
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


# ===== F6 FUTURECLAW SIMULATOR =====


def _policy_id(policy: PolicyInput) -> str:
    return f"{policy.insurer}-{policy.plan_name}".lower().replace(" ", "-")


class AffordabilitySimRequest(BaseModel):
    profile: PolicyInput
    medical_inflation_pct: float = Field(ge=3.0, le=20.0)
    income_growth_pct: float = Field(ge=0.0, le=8.0)
    policy_id: str | None = None


class LifeEventSimRequest(BaseModel):
    profile: PolicyInput
    alternative_coverage_limit_myr: float | None = Field(default=None, gt=0)
    policy_id: str | None = None


@app.post("/v1/simulate/affordability", response_model=PremiumSimulationResponse)
def simulate_affordability(request: AffordabilitySimRequest) -> PremiumSimulationResponse:
    """F6 Affordability mode — 1000-run Monte Carlo premium projection.

    Returns 3 ScenarioProjection entries (optimistic / realistic / pessimistic)
    derived from the 10th / 50th / 90th percentile of yearly premiums across runs.
    No GLM — numpy-only so this is safe to call on every slider release.
    """
    projections = monte_carlo_affordability(
        annual_premium_myr=request.profile.annual_premium_myr,
        monthly_income_myr=request.profile.projected_income_monthly_myr,
        medical_inflation_pct=request.medical_inflation_pct,
        income_growth_pct=request.income_growth_pct,
    )
    return PremiumSimulationResponse(
        policy_id=request.policy_id or _policy_id(request.profile),
        scenarios=projections,
    )


@app.post("/v1/simulate/life-event", response_model=LifeEventSimulationResponse)
async def simulate_life_event(request: LifeEventSimRequest) -> LifeEventSimulationResponse:
    """F6 Life Event mode — 4 scenarios with GLM-generated narratives.

    One GLM call per invocation fills narratives for all 4 scenarios.
    Alternative-policy toggle re-hits this endpoint with an elevated coverage limit.
    """
    raw = simulate_life_events(
        monthly_income_myr=request.profile.projected_income_monthly_myr,
        coverage_limit_myr=request.profile.coverage_limit_myr,
        alternative_coverage_limit_myr=request.alternative_coverage_limit_myr,
    )
    narratives = await generate_life_event_narratives(request.profile, raw)

    scenarios: list[LifeEventScenario] = []
    citations: list[Citation] = []
    seen_sources: set[str] = set()
    for raw_item, (narrative_en, narrative_bm) in zip(raw, narratives, strict=True):
        scenarios.append(
            LifeEventScenario(
                event=raw_item.event,
                total_event_cost_myr=raw_item.total_event_cost_myr,
                covered_myr=raw_item.covered_myr,
                copay_myr=raw_item.copay_myr,
                out_of_pocket_myr=raw_item.out_of_pocket_myr,
                months_income_at_risk=raw_item.months_income_at_risk,
                alternative_out_of_pocket_myr=raw_item.alternative_out_of_pocket_myr,
                narrative_en=narrative_en,
                narrative_bm=narrative_bm,
            )
        )
        if raw_item.citation_source not in seen_sources:
            citations.append(
                Citation(
                    source=raw_item.citation_source,
                    quote=raw_item.citation_quote,
                    locator=raw_item.citation_locator,
                )
            )
            seen_sources.add(raw_item.citation_source)

    score, band = compute_life_event_confidence(raw)
    return LifeEventSimulationResponse(
        policy_id=request.policy_id or _policy_id(request.profile),
        scenarios=scenarios,
        data_citations=citations,
        confidence_score=score,
        confidence_band=band,
    )


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
