"""Liveness probe — zero-dep endpoint used by CI smoke and Docker healthchecks."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas import APIHealth

router = APIRouter(tags=["health"])


@router.get("/health", response_model=APIHealth)
def health() -> APIHealth:
    return APIHealth(status="ok", service="policyclaw-backend")
