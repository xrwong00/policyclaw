"""Canned `PolicyInput` fixtures for the eval harness.

Keep these representative of the three main Malaysian policy archetypes we
demo against (young saver medical, takaful family plan, mid-life critical
illness). The values below are synthetic — they don't reflect any real
insurer, policyholder, or BNM-registered product.
"""

from __future__ import annotations

from datetime import date

from app.schemas import PolicyInput, PolicyType

FIXTURES: dict[str, PolicyInput] = {
    "medical_young_saver": PolicyInput(
        insurer="DemoInsure Berhad",
        plan_name="HealthShield Plus",
        policy_type=PolicyType.MEDICAL,
        annual_premium_myr=2400.0,
        coverage_limit_myr=150000.0,
        effective_date=date(2024, 3, 1),
        age_now=28,
        projected_income_monthly_myr=6500.0,
        expected_income_growth_pct=4.0,
    ),
    "takaful_family": PolicyInput(
        insurer="ContohTakaful",
        plan_name="Keluarga Sejahtera",
        policy_type=PolicyType.TAKAFUL,
        annual_premium_myr=3600.0,
        coverage_limit_myr=300000.0,
        effective_date=date(2023, 7, 15),
        age_now=36,
        projected_income_monthly_myr=9000.0,
        expected_income_growth_pct=3.0,
    ),
    "critical_illness_midlife": PolicyInput(
        insurer="SampleCI Life",
        plan_name="LifeGuard CI",
        policy_type=PolicyType.CRITICAL_ILLNESS,
        annual_premium_myr=4800.0,
        coverage_limit_myr=500000.0,
        effective_date=date(2022, 11, 1),
        age_now=47,
        projected_income_monthly_myr=12500.0,
        expected_income_growth_pct=2.5,
    ),
}
