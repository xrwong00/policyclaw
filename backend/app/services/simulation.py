from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.schemas import ConfidenceBand, LifeEvent, ScenarioProjection


# ===== Legacy deterministic projection (used by /v1/simulate/premium) =====


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
        yearly: list[float] = []
        income_annual = monthly_income_myr * 12.0
        breakpoint_year: int | None = None

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


# ===== FutureClaw Monte Carlo (used by /v1/simulate/affordability + /v1/simulate/life-event) =====


_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "bnm_corpus"
_MEDICAL_INFLATION_PATH = _DATA_DIR / "medical_inflation.json"
_LIFE_EVENT_COSTS_PATH = _DATA_DIR / "life_event_costs.json"

# (label, percentile across 1000 runs): lower percentile = cheaper premiums = optimistic.
_SCENARIO_PERCENTILES: tuple[tuple[str, float], ...] = (
    ("optimistic", 10.0),
    ("realistic", 50.0),
    ("pessimistic", 90.0),
)

# Income-growth volatility proxy — Malaysian wage-growth dispersion is narrower than medical inflation.
_SIGMA_INCOME_PCT = 1.0


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _effective_annual_rate(yearly: np.ndarray, base: float, years: int) -> float:
    final = float(yearly[-1])
    if base <= 0 or final <= 0:
        return 0.0
    return (pow(final / base, 1.0 / years) - 1.0) * 100.0


def monte_carlo_affordability(
    annual_premium_myr: float,
    monthly_income_myr: float,
    medical_inflation_pct: float,
    income_growth_pct: float,
    runs: int = 1000,
    years: int = 10,
) -> list[ScenarioProjection]:
    """Vectorized 1000-run Monte Carlo for the Affordability mode.

    Returns exactly 3 ScenarioProjection entries (optimistic/realistic/pessimistic)
    derived from the 10th/50th/90th percentile of yearly premiums across runs.
    """
    corpus = _load_json(_MEDICAL_INFLATION_PATH)
    sigma_inflation_pct = float(corpus.get("stdev_pct", 1.25))

    rng = np.random.default_rng()
    inflation = rng.normal(
        loc=medical_inflation_pct / 100.0,
        scale=sigma_inflation_pct / 100.0,
        size=(runs, years),
    )
    income_growth = rng.normal(
        loc=income_growth_pct / 100.0,
        scale=_SIGMA_INCOME_PCT / 100.0,
        size=(runs, years),
    )
    inflation = np.clip(inflation, -0.02, 0.40)
    income_growth = np.clip(income_growth, -0.05, 0.20)

    premium_factors = np.cumprod(1.0 + inflation, axis=1)
    income_factors = np.cumprod(1.0 + income_growth, axis=1)

    premiums = annual_premium_myr * premium_factors  # shape (runs, years)
    incomes = monthly_income_myr * 12.0 * income_factors
    median_income_path = np.median(incomes, axis=0)

    scenarios: list[ScenarioProjection] = []
    for label, pct in _SCENARIO_PERCENTILES:
        yearly = np.percentile(premiums, pct, axis=0)
        ratio = yearly / np.where(median_income_path > 0, median_income_path, 1.0)
        over = np.where(ratio > 0.10)[0]
        breakpoint_year = int(over[0]) + 1 if over.size > 0 else None
        effective_pct = _effective_annual_rate(yearly, annual_premium_myr, years)

        scenarios.append(
            ScenarioProjection(
                scenario=label,  # type: ignore[arg-type]
                annual_inflation_pct=round(effective_pct, 2),
                yearly_premium_myr=[round(float(v), 2) for v in yearly],
                cumulative_10y_myr=round(float(np.sum(yearly)), 2),
                breakpoint_year=breakpoint_year,
            )
        )
    return scenarios


@dataclass
class LifeEventRaw:
    event: LifeEvent
    total_event_cost_myr: float
    covered_myr: float
    copay_myr: float
    out_of_pocket_myr: float
    months_income_at_risk: float
    alternative_out_of_pocket_myr: float | None
    citation_source: str
    citation_quote: str
    citation_locator: str
    citation_url: str | None


def _sample_event_cost(rng: np.random.Generator, median: float, stdev: float, runs: int) -> float:
    """Sample total cost under a clipped normal and return the median of the sample."""
    samples = rng.normal(loc=median, scale=stdev, size=runs)
    samples = np.clip(samples, 0.3 * median, 3.0 * median)
    return float(np.median(samples))


def simulate_life_events(
    monthly_income_myr: float,
    coverage_limit_myr: float,
    alternative_coverage_limit_myr: float | None = None,
    runs: int = 1000,
) -> list[LifeEventRaw]:
    """Compute the 4 LifeEvent scenarios (covered/copay/out-of-pocket) using the LIAM/PIAM/MTA corpus."""
    corpus = _load_json(_LIFE_EVENT_COSTS_PATH)
    events_cfg = corpus["events"]
    rng = np.random.default_rng()

    results: list[LifeEventRaw] = []
    for event in LifeEvent:
        cfg = events_cfg[event.value]
        median = float(cfg["median_cost_myr"])
        stdev = float(cfg["stdev_cost_myr"])
        copay_rate = float(cfg["copay_rate"])

        total_cost = _sample_event_cost(rng, median, stdev, runs)
        covered = min(total_cost, coverage_limit_myr)
        copay = covered * copay_rate
        out_of_pocket = max(total_cost - covered + copay, 0.0)
        months_at_risk = out_of_pocket / monthly_income_myr if monthly_income_myr > 0 else 0.0

        alt_oop: float | None = None
        if alternative_coverage_limit_myr is not None:
            alt_covered = min(total_cost, alternative_coverage_limit_myr)
            alt_copay = alt_covered * copay_rate
            alt_oop = max(total_cost - alt_covered + alt_copay, 0.0)

        citation = cfg["citation"]
        results.append(
            LifeEventRaw(
                event=event,
                total_event_cost_myr=round(total_cost, 2),
                covered_myr=round(covered, 2),
                copay_myr=round(copay, 2),
                out_of_pocket_myr=round(out_of_pocket, 2),
                months_income_at_risk=round(months_at_risk, 2),
                alternative_out_of_pocket_myr=round(alt_oop, 2) if alt_oop is not None else None,
                citation_source=citation["source"],
                citation_quote=citation["quote"],
                citation_locator=citation["locator"],
                citation_url=cfg.get("citation_url"),
            )
        )
    return results


def compute_life_event_confidence(results: list[LifeEventRaw]) -> tuple[float, ConfidenceBand]:
    """Derive overall confidence from aggregate coverage ratio across the 4 events."""
    total = sum(r.total_event_cost_myr for r in results)
    covered = sum(r.covered_myr for r in results)
    if total <= 0:
        return 60.0, ConfidenceBand.MEDIUM
    ratio = covered / total
    if ratio >= 0.80:
        return 88.0, ConfidenceBand.HIGH
    if ratio >= 0.50:
        return 72.0, ConfidenceBand.MEDIUM
    return 58.0, ConfidenceBand.LOW
