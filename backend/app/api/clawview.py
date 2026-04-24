"""POST /v1/clawview — ClawView (F4 / Wow 1) clause-level risk overlay."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas import ClawViewResponse
from app.services.clawview_service import annotate_policy

router = APIRouter(prefix="/v1", tags=["clawview"])


@router.post("/clawview", response_model=ClawViewResponse)
async def api_clawview(file: UploadFile = File(...)) -> ClawViewResponse:
    """Clause-level risk highlights overlaid on the uploaded policy PDF."""
    filename = Path(file.filename or "policy.pdf").name
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded PDF was empty")

    return await annotate_policy(payload, filename, policy_id=str(uuid4()))
