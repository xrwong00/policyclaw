"""Production `/api/analyze` and `/api/extract-policy-profile` routes.

These are the two endpoints the demo flow depends on end-to-end. Keep them
boring: read PDFs, forward to the service layer, surface domain errors as
appropriate HTTP statuses.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas import AnalyzeResponse, ExtractPolicyProfileResponse
from app.services.analyze_service import run_ai_analysis
from app.services.profile_extraction_service import extract_policy_profiles

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
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
            raise HTTPException(
                status_code=400, detail="Only PDF uploads are supported"
            )

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


@router.post("/extract-policy-profile", response_model=ExtractPolicyProfileResponse)
async def api_extract_policy_profile(
    files: list[UploadFile] = File(...),
) -> ExtractPolicyProfileResponse:
    if not files:
        raise HTTPException(status_code=400, detail="At least one PDF is required")

    parsed_files: list[tuple[str, bytes]] = []
    for file in files:
        filename = Path(file.filename or "policy.pdf").name
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400, detail="Only PDF uploads are supported"
            )

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
