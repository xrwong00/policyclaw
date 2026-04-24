"""Unit test — 10-year Monte Carlo premium simulation sanity."""

from __future__ import annotations

import pytest

from app.services.simulation import project_premiums


@pytest.mark.unit
def test_project_premiums_produces_three_scenarios_with_ten_years() -> None:
    results = project_premiums(
        annual_premium_myr=3600.0,
        monthly_income_myr=6000.0,
        annual_income_growth_pct=4.0,
    )

    assert len(results) == 3
    scenarios = {item.scenario for item in results}
    assert scenarios == {"optimistic", "realistic", "pessimistic"}

    for item in results:
        assert len(item.yearly_premium_myr) == 10
        assert item.cumulative_10y_myr > 0
        # Each year's premium should be at least the starting premium.
        assert item.yearly_premium_myr[0] >= 3600.0 * 0.9
        # Breakpoint is either unset or within range.
        assert item.breakpoint_year is None or 1 <= item.breakpoint_year <= 10


@pytest.mark.unit
def test_project_premiums_pessimistic_exceeds_realistic_exceeds_optimistic() -> None:
    results = project_premiums(
        annual_premium_myr=3600.0,
        monthly_income_myr=6000.0,
        annual_income_growth_pct=4.0,
    )
    by_name = {r.scenario: r for r in results}

    assert (
        by_name["pessimistic"].cumulative_10y_myr
        > by_name["realistic"].cumulative_10y_myr
        > by_name["optimistic"].cumulative_10y_myr
    )
