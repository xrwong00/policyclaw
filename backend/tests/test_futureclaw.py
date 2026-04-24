"""Unit tests for FutureClaw simulation + narrative services (F6, Wow Factor 2).

These cover the pure-math layer that drives the Affordability and Life Event modes,
plus the deterministic mock path of the GLM narrative service (so tests run without
a GLM_API_KEY).
"""

from __future__ import annotations

import asyncio
import json
from datetime import date

import pytest

from app.schemas import ConfidenceBand, LifeEvent, PolicyInput
from app.services import futureclaw_narrative
from app.services.simulation import (
    LifeEventRaw,
    compute_life_event_confidence,
    monte_carlo_affordability,
    simulate_life_events,
)


YEARS = 10


def _make_profile(
    *,
    annual_premium_myr: float = 3600.0,
    coverage_limit_myr: float = 100_000.0,
    monthly_income_myr: float = 6000.0,
) -> PolicyInput:
    return PolicyInput(
        insurer="Great Eastern",
        plan_name="Smart Medic Premier",
        policy_type="medical",
        annual_premium_myr=annual_premium_myr,
        coverage_limit_myr=coverage_limit_myr,
        effective_date=date(2024, 1, 1),
        age_now=32,
        projected_income_monthly_myr=monthly_income_myr,
        expected_income_growth_pct=3.0,
    )


# ---------- monte_carlo_affordability ----------


def test_monte_carlo_returns_three_scenarios_with_ten_years() -> None:
    scenarios = monte_carlo_affordability(
        annual_premium_myr=3600.0,
        monthly_income_myr=6000.0,
        medical_inflation_pct=13.5,
        income_growth_pct=3.0,
    )

    assert [s.scenario for s in scenarios] == ["optimistic", "realistic", "pessimistic"]
    for scenario in scenarios:
        assert len(scenario.yearly_premium_myr) == YEARS
        # Cumulative equals the sum of yearly, within rounding.
        assert scenario.cumulative_10y_myr == pytest.approx(sum(scenario.yearly_premium_myr), abs=0.5)
        # Premiums are strictly increasing under positive inflation (monotonic compounding).
        assert all(
            later > earlier
            for earlier, later in zip(scenario.yearly_premium_myr, scenario.yearly_premium_myr[1:])
        )


def test_monte_carlo_breakpoint_flags_when_premium_exceeds_10pct_income() -> None:
    # Premium starts at 12% of annual income (7200 / 60000 = 12%) — breakpoint must be year 1.
    scenarios = monte_carlo_affordability(
        annual_premium_myr=7200.0,
        monthly_income_myr=5000.0,
        medical_inflation_pct=13.5,
        income_growth_pct=3.0,
    )
    realistic = next(s for s in scenarios if s.scenario == "realistic")
    assert realistic.breakpoint_year == 1


def test_monte_carlo_breakpoint_is_none_when_premium_safely_under_threshold() -> None:
    # Premium at 0.4% of annual income (480 / 120000) stays well under 10% across 10 years.
    scenarios = monte_carlo_affordability(
        annual_premium_myr=480.0,
        monthly_income_myr=10_000.0,
        medical_inflation_pct=3.0,
        income_growth_pct=5.0,
    )
    realistic = next(s for s in scenarios if s.scenario == "realistic")
    assert realistic.breakpoint_year is None


def test_monte_carlo_bands_are_ordered_optimistic_cheapest_pessimistic_costliest() -> None:
    scenarios = monte_carlo_affordability(
        annual_premium_myr=3600.0,
        monthly_income_myr=6000.0,
        medical_inflation_pct=13.5,
        income_growth_pct=3.0,
    )
    by_name = {s.scenario: s for s in scenarios}
    # Pessimistic year-10 premium is at or above realistic, which is at or above optimistic.
    opt = by_name["optimistic"].yearly_premium_myr[-1]
    real = by_name["realistic"].yearly_premium_myr[-1]
    pess = by_name["pessimistic"].yearly_premium_myr[-1]
    assert opt <= real <= pess


# ---------- simulate_life_events ----------


def test_simulate_life_events_returns_four_events_in_enum_order() -> None:
    results = simulate_life_events(
        monthly_income_myr=6000.0,
        coverage_limit_myr=100_000.0,
    )
    assert [r.event for r in results] == list(LifeEvent)
    assert len(results) == 4


def test_simulate_life_events_coverage_math_holds_under_limit_and_over_limit() -> None:
    # Coverage limit RM50k — cancer (median ~180k) will exceed it, so covered=50k, oop>0.
    low_limit = simulate_life_events(monthly_income_myr=6000.0, coverage_limit_myr=50_000.0)
    # Coverage limit RM1M — every event will be fully covered.
    high_limit = simulate_life_events(monthly_income_myr=6000.0, coverage_limit_myr=1_000_000.0)

    for result in low_limit:
        # Covered is capped at the coverage limit.
        assert result.covered_myr <= 50_000.0
        # Out-of-pocket is non-negative.
        assert result.out_of_pocket_myr >= 0.0
        # Months-of-income reflects OOP / monthly income, within rounding.
        assert result.months_income_at_risk == pytest.approx(result.out_of_pocket_myr / 6000.0, abs=0.05)

    for result in high_limit:
        # High coverage: covered == total cost, leaving only copay as OOP.
        assert result.covered_myr == pytest.approx(result.total_event_cost_myr, abs=0.5)
        assert result.out_of_pocket_myr == pytest.approx(result.copay_myr, abs=0.5)


def test_simulate_life_events_alternative_policy_lowers_out_of_pocket() -> None:
    results = simulate_life_events(
        monthly_income_myr=6000.0,
        coverage_limit_myr=100_000.0,
        alternative_coverage_limit_myr=500_000.0,
    )
    for r in results:
        assert r.alternative_out_of_pocket_myr is not None
        # A larger coverage limit can only reduce or equal the out-of-pocket burden.
        assert r.alternative_out_of_pocket_myr <= r.out_of_pocket_myr


def test_simulate_life_events_alt_is_none_when_not_requested() -> None:
    results = simulate_life_events(monthly_income_myr=6000.0, coverage_limit_myr=100_000.0)
    assert all(r.alternative_out_of_pocket_myr is None for r in results)


# ---------- compute_life_event_confidence ----------


def _raw(event: LifeEvent, total: float, covered: float) -> LifeEventRaw:
    return LifeEventRaw(
        event=event,
        total_event_cost_myr=total,
        covered_myr=covered,
        copay_myr=0.0,
        out_of_pocket_myr=max(total - covered, 0.0),
        months_income_at_risk=0.0,
        alternative_out_of_pocket_myr=None,
        citation_source="x",
        citation_quote="x",
        citation_locator="x",
    )


def test_confidence_high_when_coverage_ratio_at_least_80_percent() -> None:
    results = [_raw(LifeEvent.CANCER, total=100.0, covered=85.0)]
    score, band = compute_life_event_confidence(results)
    assert band == ConfidenceBand.HIGH
    assert score >= 80.0


def test_confidence_medium_when_coverage_ratio_between_50_and_80() -> None:
    results = [_raw(LifeEvent.CANCER, total=100.0, covered=65.0)]
    _, band = compute_life_event_confidence(results)
    assert band == ConfidenceBand.MEDIUM


def test_confidence_low_when_coverage_ratio_under_50() -> None:
    results = [_raw(LifeEvent.CANCER, total=100.0, covered=30.0)]
    _, band = compute_life_event_confidence(results)
    assert band == ConfidenceBand.LOW


def test_confidence_medium_when_total_cost_is_zero() -> None:
    results = [_raw(LifeEvent.CANCER, total=0.0, covered=0.0)]
    _, band = compute_life_event_confidence(results)
    assert band == ConfidenceBand.MEDIUM


# ---------- generate_life_event_narratives (mock-mode path) ----------


def test_narrative_mock_path_returns_four_tuples_within_schema_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """When is_mock_mode is True, no GLM call happens — mock narratives are returned."""
    monkeypatch.setattr(futureclaw_narrative.ai_config, "is_mock_mode", True, raising=True)

    profile = _make_profile()
    raw = simulate_life_events(
        monthly_income_myr=profile.projected_income_monthly_myr,
        coverage_limit_myr=profile.coverage_limit_myr,
    )

    pairs = asyncio.run(futureclaw_narrative.generate_life_event_narratives(profile, raw))

    assert len(pairs) == 4
    for narrative_en, narrative_bm in pairs:
        # Schema limit is 500 chars on narrative_en / narrative_bm.
        assert 1 <= len(narrative_en) <= 500
        assert 1 <= len(narrative_bm) <= 500
        # Mock narratives reference the MYR figure — sanity check the interpolation.
        assert "RM" in narrative_en
        assert "RM" in narrative_bm


# ---------- _call_glm (streaming-path happy case) ----------


def test_call_glm_parses_streaming_json_into_narrative_batch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With GLM_API_KEY set, `_call_glm` POSTs via `post_glm_with_retry` and parses
    the concatenated stream content into a `_NarrativeBatch`. Stub the streaming
    helper so the test stays offline."""
    canned = json.dumps(
        {
            "scenarios": [
                {
                    "event": "cancer",
                    "narrative_en": "Cancer narrative in English (stub).",
                    "narrative_bm": "Naratif kanser dalam Bahasa Malaysia (stub).",
                },
                {
                    "event": "heart_attack",
                    "narrative_en": "Heart attack narrative (stub).",
                    "narrative_bm": "Naratif serangan jantung (stub).",
                },
                {
                    "event": "disability",
                    "narrative_en": "Disability narrative (stub).",
                    "narrative_bm": "Naratif hilang upaya (stub).",
                },
                {
                    "event": "death",
                    "narrative_en": "Death-of-primary-earner narrative (stub).",
                    "narrative_bm": "Naratif kematian pencari nafkah (stub).",
                },
            ]
        }
    )

    async def fake_post(*, url: str, headers: dict, payload: dict) -> str:  # noqa: ARG001
        assert payload["response_format"] == {"type": "json_object"}
        assert payload["messages"][0]["role"] == "system"
        return canned

    monkeypatch.setattr(futureclaw_narrative, "post_glm_with_retry", fake_post)

    batch = asyncio.run(futureclaw_narrative._call_glm("ignored prompt"))

    assert len(batch.scenarios) == 4
    assert {s.event for s in batch.scenarios} == {"cancer", "heart_attack", "disability", "death"}
    for pair in batch.scenarios:
        assert pair.narrative_en
        assert pair.narrative_bm


def test_generate_life_event_narratives_falls_back_on_glm_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Transport-level failure from `post_glm_with_retry` must surface as mock
    narratives, not a 500. Guarantees the demo never breaks on Ilmu timeouts."""
    monkeypatch.setattr(futureclaw_narrative.ai_config, "is_mock_mode", False, raising=True)

    async def boom(*, url: str, headers: dict, payload: dict) -> str:  # noqa: ARG001
        raise RuntimeError("simulated Ilmu gateway drop")

    monkeypatch.setattr(futureclaw_narrative, "post_glm_with_retry", boom)

    profile = _make_profile()
    raw = simulate_life_events(
        monthly_income_myr=profile.projected_income_monthly_myr,
        coverage_limit_myr=profile.coverage_limit_myr,
    )

    pairs = asyncio.run(futureclaw_narrative.generate_life_event_narratives(profile, raw))

    assert len(pairs) == 4
    for narrative_en, narrative_bm in pairs:
        assert "[fallback]" in narrative_en
        assert "[fallback]" in narrative_bm
