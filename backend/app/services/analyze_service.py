"""PolicyClaw /api/analyze orchestrator — 3-stage backend pipeline.

Stages (PRD §8.4, CLAUDE.md §66-§73):
    1. Extract   — `analyze_policy_xray` (GLM Call 1 — F1)
    2. Score     — `analyze_health_score` (GLM Call 3 — F5, new in this worktree)
    3. Recommend — `analyze_policy_verdict` (GLM Call 4 — F5)

The 4th GLM call (Annotate for ClawView) is served by `POST /v1/clawview` and is
triggered by the frontend after `/api/analyze` returns. Total 4 GLM calls per
analysis, split across two endpoints.

All three stages already handle GLM failures internally (heuristic / mock
fallback) and wire demo_cache read-through. This orchestrator therefore never
raises from a GLM problem — the user always sees a valid `AnalyzeResponse`.
"""

from __future__ import annotations

import hashlib
from datetime import date
from typing import Any
from uuid import uuid4

# Importing `app.core.glm_client` has the side effect of loading backend/.env.
from app.core import glm_client as _glm_client  # noqa: F401
from app.schemas import (
    AnalysisCitation,
    AnalyzeResponse,
    HealthScore,
    PolicyInput,
    PolicyType,
    PolicyVerdict,
    PolicyXRayResponse,
    Reason,
)
from app.services import demo_cache
from app.services.ai_service import (
    analyze_health_score,
    analyze_policy_verdict,
    analyze_policy_xray,
    config as ai_config,
)
from app.services.pdf_parser import parse_pdf_chunks
from app.services.rag import build_context, retrieve_relevant_chunks
from app.services.simulation import project_premiums


# ---------- profile → PolicyInput ----------


def _coerce_date(value: Any, fallback: date) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return fallback
    return fallback


def _coerce_policy_type(value: Any) -> PolicyType:
    if isinstance(value, PolicyType):
        return value
    raw = str(value or "medical").lower()
    try:
        return PolicyType(raw)
    except ValueError:
        return PolicyType.MEDICAL


def _build_policy_input(profile: dict[str, Any]) -> PolicyInput:
    """Assemble a validated PolicyInput from the user-supplied profile + safe defaults."""

    def _as_float(key: str, default: float) -> float:
        raw = profile.get(key)
        if raw in (None, ""):
            return default
        try:
            return float(raw)
        except (TypeError, ValueError):
            return default

    def _as_int(key: str, default: int) -> int:
        raw = profile.get(key)
        if raw in (None, ""):
            return default
        try:
            return int(float(raw))
        except (TypeError, ValueError):
            return default

    insurer = (profile.get("insurer") or "Unknown Insurer").strip() or "Unknown Insurer"
    plan_name = (profile.get("plan_name") or "Unknown Plan").strip() or "Unknown Plan"

    return PolicyInput(
        insurer=insurer[:120],
        plan_name=plan_name[:160],
        policy_type=_coerce_policy_type(profile.get("policy_type")),
        annual_premium_myr=max(_as_float("annual_premium_myr", 3600.0), 1.0),
        coverage_limit_myr=max(_as_float("coverage_limit_myr", 500_000.0), 1.0),
        effective_date=_coerce_date(profile.get("effective_date"), date.today()),
        age_now=max(18, min(100, _as_int("age_now", 38))),
        projected_income_monthly_myr=max(_as_float("projected_income_monthly_myr", 6000.0), 1.0),
        expected_income_growth_pct=max(0.0, min(20.0, _as_float("expected_income_growth_pct", 3.0))),
    )


# ---------- composition helpers ----------


BNM_TOKENS = ("bnm", "repricing", "premium cap", "10%", "10 %", "premium increase", "reprice")


def _bnm_rights_detected(xray: PolicyXRayResponse) -> bool:
    for clause in xray.key_clauses:
        blob = f"{clause.title} {clause.plain_language_en} {clause.original_text}".lower()
        if any(token in blob for token in BNM_TOKENS):
            return True
    return False


def _needs_rider_flag(verdict: PolicyVerdict) -> bool:
    """The `_call_glm_policy_verdict` helper prefixes the first reason title with
    'Add rider:' when the GLM output has `needs_rider=true` and verdict=keep.
    Detect that exact prefix (with colon) here so the frontend can render the
    ADD RIDER pill. Matching the colon keeps this check, the writer in
    ai_service.py, and `_summary_reasons` below all in lock-step.
    """
    if verdict.verdict.value != "keep":
        return False
    if not verdict.reasons:
        return False
    return verdict.reasons[0].title.lower().startswith("add rider:")


def _xray_citations(xray: PolicyXRayResponse) -> list[AnalysisCitation]:
    out: list[AnalysisCitation] = []
    for clause in xray.key_clauses[:4]:
        out.append(
            AnalysisCitation(
                source=f"{xray.insurer} — {xray.plan_name}",
                page=clause.source_page,
                excerpt=f"{clause.title}: {clause.plain_language_en[:400]}",
            )
        )
    return out


def _verdict_citations(verdict: PolicyVerdict) -> list[AnalysisCitation]:
    out: list[AnalysisCitation] = []
    for reason in verdict.reasons:
        page = 1
        locator_lower = (reason.citation.locator or "").lower()
        for token in locator_lower.replace(":", " ").replace(",", " ").split():
            # Skip date-shaped tokens like "2024-12-31" or "2024/12/31" —
            # they'd otherwise collapse to an absurd page number (20241231).
            if sum(1 for ch in token if ch in "-/.") >= 2:
                continue
            digits = "".join(ch for ch in token if ch.isdigit())
            # Cap at 4 digits (real policies rarely exceed 9999 pages).
            if digits and len(digits) <= 4:
                try:
                    candidate = int(digits)
                    if 1 <= candidate <= 9999:
                        page = candidate
                        break
                except ValueError:
                    continue
        out.append(
            AnalysisCitation(
                source=reason.citation.source,
                page=page,
                excerpt=reason.citation.quote[:400],
            )
        )
    return out


def _dedupe_citations(citations: list[AnalysisCitation]) -> list[AnalysisCitation]:
    """Dedupe on (source, page, excerpt prefix) so distinct clauses on the same
    page don't silently collapse into one citation.
    """
    seen: set[tuple[str, int, str]] = set()
    out: list[AnalysisCitation] = []
    for c in citations:
        excerpt_key = (c.excerpt or "").strip().lower()[:120]
        key = (c.source.lower(), c.page, excerpt_key)
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out[:12]


def _summary_reasons(verdict: PolicyVerdict) -> list[str]:
    out: list[str] = []
    for reason in verdict.reasons:
        title = reason.title
        # Strip the "Add rider: " prefix for the flat summary list so the
        # reader sees the human-facing reason, not the structural marker.
        if title.lower().startswith("add rider:"):
            title = title.split(":", 1)[1].strip() or title
        out.append(f"{title}: {reason.detail}")
    if not out:
        out.append("Analysis produced no structured reasons.")
    return out[:6]


# ---------- orchestrator ----------


async def run_ai_analysis(
    files: list[tuple[str, bytes]],
    profile: dict[str, str | float | int],
) -> AnalyzeResponse:
    """Run Extract → Score → Recommend and compose the extended AnalyzeResponse.

    PDF text is parsed via `parse_pdf_chunks`, retrieved via lexical RAG, and
    passed as `context` to the Extract stage so clauses are paraphrased from
    the real document instead of invented. File bytes are also hashed into the
    cache key so two different PDFs sharing the same profile don't collide.

    ClawView bbox annotation is handled separately by `POST /v1/clawview`
    (called by the frontend); this orchestrator does not produce bbox data.
    """
    if not files:
        raise ValueError("At least one PDF is required")

    policy_input = _build_policy_input(dict(profile))
    policy_id = f"{policy_input.insurer}-{policy_input.plan_name}".lower().replace(" ", "-")

    # Parse all uploaded PDFs and build a retrieval context. Empty-text PDFs
    # (e.g. scans without OCR) yield no chunks — Extract still runs, just
    # without grounding, which matches the pre-PR behavior.
    all_chunks: list = []
    digest = hashlib.sha256()
    for source_name, content in files:
        digest.update(content)
        try:
            all_chunks.extend(parse_pdf_chunks(content, source_name))
        except Exception:
            # Individual PDF parse failures don't kill the pipeline; we still
            # have the user-supplied profile fields and can return a verdict.
            continue
    file_digest = digest.hexdigest()

    context: str | None = None
    if all_chunks:
        query = (
            f"{policy_input.insurer} {policy_input.plan_name} "
            f"{policy_input.policy_type.value} premium coverage exclusions "
            "waiting period co-payment repricing"
        )
        selected = retrieve_relevant_chunks(all_chunks, query=query, k=8)
        if selected:
            context = build_context(selected)

    # 10-year realistic premium envelope feeds Recommend's MYR impact.
    projections = project_premiums(
        annual_premium_myr=policy_input.annual_premium_myr,
        monthly_income_myr=policy_input.projected_income_monthly_myr,
        annual_income_growth_pct=policy_input.expected_income_growth_pct,
    )
    realistic = next((p for p in projections if p.scenario == "realistic"), projections[0])
    realistic_10y_cost_myr = float(realistic.cumulative_10y_myr)

    # Cache detection: any stage returning a key that already exists on disk.
    cached_any = False

    def _cache_probe(stage: str, *parts: Any) -> bool:
        return demo_cache.get(demo_cache.make_key(stage, *parts)) is not None

    extract_probe = _cache_probe(
        "extract",
        policy_id,
        policy_input.model_dump(mode="json"),
        file_digest,
        bool(context),
    )

    # Stage 1 — Extract (grounded in the uploaded PDF when we have chunks).
    xray: PolicyXRayResponse = await analyze_policy_xray(
        policy_input, policy_id, context=context, file_digest=file_digest
    )
    cached_any = cached_any or extract_probe

    # Stage 2 — Score
    score_probe = _cache_probe(
        "score",
        policy_input.model_dump(mode="json"),
        xray.model_dump(mode="json"),
    )
    health: HealthScore = await analyze_health_score(policy_input, xray)
    cached_any = cached_any or score_probe

    # Stage 3 — Recommend
    recommend_probe = _cache_probe(
        "recommend",
        policy_id,
        policy_input.model_dump(mode="json"),
        round(realistic_10y_cost_myr, 2),
        xray.model_dump(mode="json"),
        health.model_dump(mode="json"),
    )
    verdict: PolicyVerdict = await analyze_policy_verdict(
        policy_input, realistic_10y_cost_myr, xray=xray, health=health
    )
    cached_any = cached_any or recommend_probe

    # Compose extended response. Legacy flat fields are derived from structured ones
    # so any consumer reading the old shape keeps working.
    citations = _dedupe_citations(_xray_citations(xray) + _verdict_citations(verdict))
    if not citations:
        citations.append(
            AnalysisCitation(
                source=xray.insurer or "Uploaded policy document",
                page=1,
                excerpt="No structured citation produced by this analysis.",
            )
        )

    return AnalyzeResponse(
        verdict=verdict.verdict,
        projected_savings=verdict.projected_10y_savings_myr,
        # Overlap detection is a multi-policy concern; /api/analyze looks at
        # one policy slice. Real overlap-map lives at /v1/ai/overlap-map.
        overlap_detected=False,
        bnm_rights_detected=_bnm_rights_detected(xray),
        confidence_score=verdict.confidence_score,
        summary_reasons=_summary_reasons(verdict),
        citations=citations,
        reasons=list(verdict.reasons)[:5],
        projected_10y_premium_myr=realistic_10y_cost_myr,
        projected_10y_savings_myr=verdict.projected_10y_savings_myr,
        health_score=health,
        analysis_id=str(uuid4()),
        cached=cached_any and ai_config.enabled,
        needs_rider=_needs_rider_flag(verdict),
    )
