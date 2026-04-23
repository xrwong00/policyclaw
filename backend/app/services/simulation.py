from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ScenarioResult:
    scenario: str
    annual_inflation_pct: float
    yearly_premium_myr: list[float]
    cumulative_10y_myr: float
    breakpoint_year: int | None


def _age_band_jump(year_index: int) -> float:
    # Simple proxy for premium jumps at future age bands.
    if year_index in (4, 8):
        return 1.08
    return 1.0


def project_premiums(
    annual_premium_myr: float,
    monthly_income_myr: float,
    annual_income_growth_pct: float,
    scenarios: tuple[tuple[str, float], ...] = (
        ("optimistic", 5.0),
        ("realistic", 10.0),
        ("pessimistic", 15.0),
    ),
    years: int = 10,
) -> list[ScenarioResult]:
    results: list[ScenarioResult] = []

    for scenario_name, inflation_pct in scenarios:
        yearly = []
        income_annual = monthly_income_myr * 12.0
        breakpoint_year = None

        current = annual_premium_myr
        for idx in range(1, years + 1):
            policy_cap = 1.10 if idx <= 2 else 1.0
            inflation_factor = 1.0 + (inflation_pct / 100.0)
            current = current * inflation_factor * _age_band_jump(idx)
            current = min(current, yearly[-1] * policy_cap) if yearly and idx <= 2 else current
            yearly.append(round(current, 2))

            premium_ratio = current / income_annual
            if breakpoint_year is None and premium_ratio >= 0.10:
                breakpoint_year = idx

            income_annual = income_annual * (1.0 + annual_income_growth_pct / 100.0)

        cumulative = float(np.round(np.sum(yearly), 2))
        results.append(
            ScenarioResult(
                scenario=scenario_name,
                annual_inflation_pct=inflation_pct,
                yearly_premium_myr=yearly,
                cumulative_10y_myr=cumulative,
                breakpoint_year=breakpoint_year,
            )
        )

    return results
