"""Unit tests for the /api/analyze orchestrator — PDF grounding, cache keys,
citation dedupe, and the overlap flag."""

from __future__ import annotations

import asyncio
import io
from datetime import date

import pytest
from pypdf import PdfWriter

from app.schemas import AnalysisCitation, PolicyInput, PolicyType
from app.services import analyze_service
from app.services.analyze_service import (
    _bnm_rights_detected,
    _dedupe_citations,
    _needs_rider_flag,
    run_ai_analysis,
)


def _build_tiny_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_blank_page(width=612, height=792)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _sample_profile() -> dict:
    return {
        "insurer": "TestInsurer",
        "plan_name": "TestPlan Gold",
        "policy_type": "medical",
        "annual_premium_myr": 3600.0,
        "coverage_limit_myr": 500_000.0,
        "effective_date": "2024-01-01",
        "age_now": 38,
        "projected_income_monthly_myr": 6000.0,
        "expected_income_growth_pct": 4.0,
    }


# ---------- citation dedupe ----------


@pytest.mark.unit
def test_dedupe_keeps_distinct_excerpts_on_same_page() -> None:
    """Two clauses on the same page with different excerpts must both survive."""
    citations = [
        AnalysisCitation(source="TestInsurer", page=3, excerpt="Hospitalization clause A"),
        AnalysisCitation(source="TestInsurer", page=3, excerpt="Hospitalization clause B"),
    ]
    result = _dedupe_citations(citations)
    assert len(result) == 2


@pytest.mark.unit
def test_dedupe_collapses_exact_duplicates() -> None:
    citations = [
        AnalysisCitation(source="TestInsurer", page=3, excerpt="Same text"),
        AnalysisCitation(source="testinsurer", page=3, excerpt="Same Text"),  # case + whitespace diff
    ]
    result = _dedupe_citations(citations)
    assert len(result) == 1


@pytest.mark.unit
def test_dedupe_caps_at_twelve() -> None:
    citations = [
        AnalysisCitation(source=f"Source{i}", page=i + 1, excerpt=f"Excerpt {i}")
        for i in range(20)
    ]
    result = _dedupe_citations(citations)
    assert len(result) == 12


# ---------- BNM detection ----------


@pytest.mark.unit
def test_bnm_detection_fires_on_repricing_language() -> None:
    from app.schemas import PolicyClause, PolicyXRayResponse, ConfidenceBand

    xray = PolicyXRayResponse(
        policy_id="x",
        insurer="TestInsurer",
        plan_name="Gold",
        policy_type=PolicyType.MEDICAL,
        key_clauses=[
            PolicyClause(
                title="Premium Reprice Clause",
                original_text="Premiums may be repriced annually.",
                plain_language_en="Premium may be repriced.",
                plain_language_bm="Premium boleh dinaikkan.",
                gotcha_flag=True,
                source_page=3,
            )
        ],
        gotcha_count=1,
        confidence_score=70.0,
        confidence_band=ConfidenceBand.MEDIUM,
    )
    assert _bnm_rights_detected(xray) is True


@pytest.mark.unit
def test_bnm_detection_quiet_on_unrelated_clauses() -> None:
    from app.schemas import PolicyClause, PolicyXRayResponse, ConfidenceBand

    xray = PolicyXRayResponse(
        policy_id="x",
        insurer="TestInsurer",
        plan_name="Gold",
        policy_type=PolicyType.MEDICAL,
        key_clauses=[
            PolicyClause(
                title="Waiting Period",
                original_text="30 day waiting period.",
                plain_language_en="First 30 days excluded.",
                plain_language_bm="30 hari pertama dikecualikan.",
                gotcha_flag=False,
                source_page=2,
            )
        ],
        gotcha_count=0,
        confidence_score=70.0,
        confidence_band=ConfidenceBand.MEDIUM,
    )
    assert _bnm_rights_detected(xray) is False


# ---------- orchestrator end-to-end (mock mode) ----------


@pytest.mark.unit
def test_run_ai_analysis_produces_valid_response_in_mock_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end smoke test of the 3-stage orchestrator with the LLM disabled.
    Verifies the extended AnalyzeResponse fields are populated and the
    overlap_detected flag is honest (False, not len(files)>=2)."""
    monkeypatch.setenv("OPENAI_API_KEY", "")
    import app.services.ai_service as ai_service_module

    ai_service_module.config = ai_service_module.AIServiceConfig()

    files = [("policy1.pdf", _build_tiny_pdf()), ("policy2.pdf", _build_tiny_pdf())]
    response = asyncio.run(run_ai_analysis(files, _sample_profile()))

    assert response.verdict.value in {"keep", "downgrade", "switch", "dump"}
    assert response.health_score is not None
    assert 0 <= response.health_score.overall <= 100
    assert response.projected_10y_premium_myr > 0
    assert response.analysis_id  # non-empty UUID
    assert response.reasons, "structured reasons must be populated"
    assert response.citations, "citations must be populated (even fallback)"
    # overlap_detected must be False — multi-policy overlap is /v1/ai/overlap-map's job.
    assert response.overlap_detected is False
    # needs_rider is only true on KEEP+prefix — heuristic fallback doesn't prefix, so False.
    assert response.needs_rider is False


@pytest.mark.unit
def test_run_ai_analysis_handles_garbage_pdfs_gracefully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-PDF upload must not crash the orchestrator — it should still
    produce a valid response using profile fields only."""
    monkeypatch.setenv("OPENAI_API_KEY", "")
    import app.services.ai_service as ai_service_module

    ai_service_module.config = ai_service_module.AIServiceConfig()

    files = [("junk.pdf", b"not a pdf")]
    response = asyncio.run(run_ai_analysis(files, _sample_profile()))

    assert response.verdict.value in {"keep", "downgrade", "switch", "dump"}
    assert response.health_score is not None


@pytest.mark.unit
def test_run_ai_analysis_rejects_empty_file_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    import app.services.ai_service as ai_service_module

    ai_service_module.config = ai_service_module.AIServiceConfig()

    with pytest.raises(ValueError, match="At least one PDF"):
        asyncio.run(run_ai_analysis([], _sample_profile()))
