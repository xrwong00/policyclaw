"""Unit test — F7 acceptance: verdict consistent across 3 reruns of identical input.

Exercises the heuristic fallback path (GLM_API_KEY unset) so the test runs offline
in CI. The fallback is pure math on `PolicyInput`, so identical inputs must produce
byte-identical `PolicyVerdict` fields.
"""

from __future__ import annotations

import asyncio
from datetime import date

import pytest

from app.schemas import Citation, PolicyInput, PolicyType, PolicyVerdict, Reason, VerdictLabel
from app.schemas import ConfidenceBand
from app.services.analyze_service import _needs_rider_flag, _summary_reasons
from app.services.verdict import generate_verdict


def _sample_policy() -> PolicyInput:
    return PolicyInput(
        insurer="TestInsurer",
        plan_name="TestPlan Gold",
        policy_type=PolicyType.MEDICAL,
        annual_premium_myr=3600.0,
        coverage_limit_myr=500_000.0,
        effective_date=date(2024, 1, 1),
        age_now=38,
        projected_income_monthly_myr=6000.0,
        expected_income_growth_pct=4.0,
    )


@pytest.mark.unit
def test_heuristic_verdict_is_deterministic() -> None:
    policy = _sample_policy()
    first = generate_verdict(policy, realistic_10y_cost_myr=72000.0)
    second = generate_verdict(policy, realistic_10y_cost_myr=72000.0)
    third = generate_verdict(policy, realistic_10y_cost_myr=72000.0)
    assert first == second == third


@pytest.mark.unit
def test_analyze_policy_verdict_consistent_across_three_runs_in_fallback_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With GLM_API_KEY unset, `analyze_policy_verdict` falls through to the
    heuristic. Three identical calls must produce byte-identical verdicts."""
    monkeypatch.setenv("GLM_API_KEY", "")
    import app.services.ai_service as ai_service_module

    ai_service_module.config = ai_service_module.AIServiceConfig()

    policy = _sample_policy()

    async def run_three() -> list[tuple[str, float]]:
        out: list[tuple[str, float]] = []
        for _ in range(3):
            verdict = await ai_service_module.analyze_policy_verdict(
                policy, realistic_10y_cost_myr=72000.0
            )
            out.append((verdict.verdict.value, verdict.confidence_score))
        return out

    results = asyncio.run(run_three())
    assert results[0] == results[1] == results[2]


def _make_verdict(first_title: str, verdict_label: VerdictLabel = VerdictLabel.KEEP) -> PolicyVerdict:
    return PolicyVerdict(
        policy_id="test",
        verdict=verdict_label,
        confidence_score=70.0,
        confidence_band=ConfidenceBand.MEDIUM,
        projected_10y_premium_myr=70000.0,
        projected_10y_savings_myr=3500.0,
        reasons=[
            Reason(
                title=first_title,
                detail="Supporting detail for the top reason.",
                citation=Citation(
                    source="TestInsurer — TestPlan Gold",
                    quote="Policy section cited.",
                    locator="page 4",
                ),
            ),
            Reason(
                title="Secondary reason",
                detail="Second reason detail.",
                citation=Citation(
                    source="BNM",
                    quote="BNM circular.",
                    locator="2024-12-31",
                ),
            ),
        ],
    )


@pytest.mark.unit
def test_needs_rider_flag_detects_add_rider_prefix_on_keep() -> None:
    assert _needs_rider_flag(_make_verdict("Add rider: Critical illness gap")) is True


@pytest.mark.unit
def test_needs_rider_flag_ignores_non_keep_verdicts() -> None:
    assert (
        _needs_rider_flag(_make_verdict("Add rider: Gap", verdict_label=VerdictLabel.SWITCH))
        is False
    )


@pytest.mark.unit
def test_needs_rider_flag_false_without_prefix() -> None:
    assert _needs_rider_flag(_make_verdict("Premium affordability signal")) is False


@pytest.mark.unit
def test_needs_rider_flag_requires_colon_not_bare_phrase() -> None:
    """Writer always emits 'Add rider: ...' with a colon. A bare 'Add rider'
    (no colon) is treated as a real reason title, not the ADD RIDER marker."""
    assert _needs_rider_flag(_make_verdict("Add rider opinion from advisor")) is False


@pytest.mark.unit
def test_summary_reasons_strips_add_rider_prefix() -> None:
    verdict = _make_verdict("Add rider: Critical illness gap")
    summaries = _summary_reasons(verdict)
    assert summaries[0].startswith("Critical illness gap")
    assert "Add rider" not in summaries[0].split(":", 1)[0]


@pytest.mark.unit
def test_summary_reasons_leaves_non_rider_titles_untouched() -> None:
    verdict = _make_verdict("Premium affordability signal")
    summaries = _summary_reasons(verdict)
    assert summaries[0].startswith("Premium affordability signal")
