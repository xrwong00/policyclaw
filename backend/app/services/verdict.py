from __future__ import annotations

from app.schemas import ConfidenceBand, PolicyInput, VerdictLabel


def _band(score: float) -> ConfidenceBand:
    if score > 80:
        return ConfidenceBand.HIGH
    if score >= 60:
        return ConfidenceBand.MEDIUM
    return ConfidenceBand.LOW


def generate_verdict(policy: PolicyInput, realistic_10y_cost_myr: float) -> tuple[VerdictLabel, float, float, ConfidenceBand]:
    annual_income = policy.projected_income_monthly_myr * 12.0
    burden = policy.annual_premium_myr / annual_income

    if burden < 0.05 and policy.coverage_limit_myr >= 1000000:
        verdict = VerdictLabel.KEEP
        confidence = 84.0
        savings = realistic_10y_cost_myr * 0.05
    elif burden < 0.10:
        verdict = VerdictLabel.DOWNGRADE
        confidence = 76.0
        savings = realistic_10y_cost_myr * 0.12
    elif burden < 0.15:
        verdict = VerdictLabel.SWITCH
        confidence = 72.0
        savings = realistic_10y_cost_myr * 0.18
    else:
        verdict = VerdictLabel.DUMP
        confidence = 58.0
        savings = realistic_10y_cost_myr * 0.22

    return verdict, confidence, round(float(savings), 2), _band(confidence)
