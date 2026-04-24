"""Unit tests for ClawView service (F4, Wow Factor 1) — streaming GLM path.

The mock/heuristic path is exercised implicitly by `annotate_policy` when no key
is set, but that gate short-circuits before reaching `_call_glm_annotate`. These
tests cover the post-streaming-migration JSON parse + bbox merge happy path and
the failure fallback, which are the two behaviors most at risk when the GLM
transport changes.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app.schemas import ConfidenceBand, RiskLevel
from app.services import clawview_service
from app.services.pdf_parser import ClauseWithBBox


def _clause(clause_id: str, text: str = "Sample clause text.") -> ClauseWithBBox:
    return ClauseWithBBox(
        clause_id=clause_id,
        text=text,
        page=1,
        bbox=(48.0, 100.0, 540.0, 160.0),
        source="test",
    )


def test_call_glm_annotate_parses_streaming_json_and_merges_bboxes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`_call_glm_annotate` must POST via `post_glm_with_retry`, parse the
    aggregated JSON content, and merge annotations back onto the provided
    clauses' bounding boxes."""
    clauses = [
        _clause("p1-c0", "Premium rates may be revised at renewal."),
        _clause("p1-c1", "Pre-existing conditions are excluded for 12 months."),
    ]

    canned = json.dumps(
        {
            "annotations": [
                {
                    "clause_id": "p1-c0",
                    "risk_level": "yellow",
                    "plain_explanation_en": "Premium may rise at renewal.",
                    "plain_explanation_bm": "Premium boleh naik semasa pembaharuan.",
                    "why_this_matters": "Repricing is the top reason buyers drop mid-life.",
                },
                {
                    "clause_id": "p1-c1",
                    "risk_level": "red",
                    "plain_explanation_en": "Conditions you already had are not covered.",
                    "plain_explanation_bm": "Keadaan sedia ada tidak dilindungi.",
                    "why_this_matters": "Most common reason claims are denied.",
                },
            ]
        }
    )

    async def fake_post(*, url: str, headers: dict, payload: dict) -> str:  # noqa: ARG001
        assert payload["response_format"] == {"type": "json_object"}
        assert any(m["role"] == "system" for m in payload["messages"])
        return canned

    monkeypatch.setattr(clawview_service, "post_glm_with_retry", fake_post)

    response = asyncio.run(clawview_service._call_glm_annotate(clauses, policy_id="test-policy"))

    assert response.policy_id == "test-policy"
    assert len(response.annotations) == 2
    by_id = {a.clause_id: a for a in response.annotations}
    assert by_id["p1-c0"].risk_level == RiskLevel.YELLOW
    assert by_id["p1-c1"].risk_level == RiskLevel.RED
    # Bboxes come from the input clauses, not the model — validate they stuck.
    assert by_id["p1-c0"].bbox.x0 == pytest.approx(48.0)
    assert by_id["p1-c0"].bbox.y1 == pytest.approx(160.0)
    # Confidence band reflects coverage + signal bonus (full coverage + red/yellow).
    assert response.confidence_band in {ConfidenceBand.MEDIUM, ConfidenceBand.HIGH}


def test_call_glm_annotate_drops_unknown_clause_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    """Annotations that reference clause_ids we never sent must be dropped —
    this is the LLM trust boundary that prevents hallucinated clauses from
    reaching the frontend overlay."""
    clauses = [_clause("p1-c0")]

    canned = json.dumps(
        {
            "annotations": [
                {
                    "clause_id": "p1-c0",
                    "risk_level": "green",
                    "plain_explanation_en": "Benign clause.",
                    "plain_explanation_bm": "Klausa biasa.",
                    "why_this_matters": "",
                },
                {
                    "clause_id": "hallucinated-id",
                    "risk_level": "red",
                    "plain_explanation_en": "Should be dropped.",
                    "plain_explanation_bm": "Patut digugurkan.",
                    "why_this_matters": "",
                },
            ]
        }
    )

    async def fake_post(*, url: str, headers: dict, payload: dict) -> str:  # noqa: ARG001
        return canned

    monkeypatch.setattr(clawview_service, "post_glm_with_retry", fake_post)

    response = asyncio.run(clawview_service._call_glm_annotate(clauses, policy_id="trust-boundary"))

    assert len(response.annotations) == 1
    assert response.annotations[0].clause_id == "p1-c0"


def test_annotate_policy_falls_back_on_glm_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Transport errors from `post_glm_with_retry` must surface as the heuristic
    mock path with degraded confidence, not a 500."""
    # Force the non-mock-mode branch so _call_glm_annotate is reached.
    monkeypatch.setattr(clawview_service.config, "api_key", "fake-key", raising=True)
    monkeypatch.setattr(clawview_service.config, "is_mock_mode", False, raising=True)

    fake_clauses = [
        _clause("p1-c0", "Premium rates may be revised."),
        _clause("p1-c1", "Pre-existing conditions excluded."),
        _clause("p1-c2", "Waiting period applies for 30 days."),
    ]
    monkeypatch.setattr(
        clawview_service,
        "extract_clauses_with_bboxes",
        lambda pdf_bytes, source_name: fake_clauses,
    )

    async def boom(*, url: str, headers: dict, payload: dict) -> str:  # noqa: ARG001
        raise RuntimeError("simulated Ilmu timeout")

    monkeypatch.setattr(clawview_service, "post_glm_with_retry", boom)

    response = asyncio.run(
        clawview_service.annotate_policy(pdf_bytes=b"%PDF-stub", source_name="stub.pdf", policy_id="fb")
    )

    assert response.policy_id == "fb"
    assert response.confidence_score == pytest.approx(45.0)
    assert response.confidence_band == ConfidenceBand.LOW
    assert len(response.annotations) >= 1
