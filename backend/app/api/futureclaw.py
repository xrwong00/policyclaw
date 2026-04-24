"""FutureClaw (F6 / Wow 2) routes — Monte Carlo affordability + life-event sim.

Both endpoints share the pattern: small request body with the user profile +
toggle state, service-layer computes the numeric result, a single GLM call
(life-event only) fills narrative text.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.schemas import (
    Citation,
    LifeEventScenario,
    LifeEventSimulationResponse,
    PolicyInput,
    PremiumSimulationResponse,
)
from app.services.futureclaw_narrative import generate_life_event_narratives
from app.services.simulation import (
    compute_life_event_confidence,
    monte_carlo_affordability,
    simulate_life_events,
)

router = APIRouter(prefix="/v1/simulate", tags=["futureclaw"])


def _policy_id(policy: PolicyInput) -> str:
    return f"{policy.insurer}-{policy.plan_name}".lower().replace(" ", "-")


class AffordabilitySimRequest(BaseModel):
    profile: PolicyInput
    medical_inflation_pct: float = Field(ge=3.0, le=20.0)
    income_growth_pct: float = Field(ge=0.0, le=8.0)
    policy_id: str | None = None


class LifeEventSimRequest(BaseModel):
    profile: PolicyInput
    alternative_coverage_limit_myr: float | None = Field(default=None, gt=0)
    policy_id: str | None = None


@router.post("/affordability", response_model=PremiumSimulationResponse)
def simulate_affordability(
    request: AffordabilitySimRequest,
) -> PremiumSimulationResponse:
    """1000-run Monte Carlo premium projection.

    Returns 3 ScenarioProjection entries (optimistic / realistic / pessimistic)
    derived from the 10th / 50th / 90th percentile of yearly premiums across runs.
    No GLM — numpy-only so this is safe to call on every slider release.
    """
    projections = monte_carlo_affordability(
        annual_premium_myr=request.profile.annual_premium_myr,
        monthly_income_myr=request.profile.projected_income_monthly_myr,
        medical_inflation_pct=request.medical_inflation_pct,
        income_growth_pct=request.income_growth_pct,
    )
    return PremiumSimulationResponse(
        policy_id=request.policy_id or _policy_id(request.profile),
        scenarios=projections,
    )


@router.post("/life-event", response_model=LifeEventSimulationResponse)
async def simulate_life_event(
    request: LifeEventSimRequest,
) -> LifeEventSimulationResponse:
    """4 life-event scenarios with GLM-generated narratives.

    One GLM call per invocation fills narratives for all 4 scenarios.
    Alternative-policy toggle re-hits this endpoint with an elevated coverage limit.
    """
    raw = simulate_life_events(
        monthly_income_myr=request.profile.projected_income_monthly_myr,
        coverage_limit_myr=request.profile.coverage_limit_myr,
        alternative_coverage_limit_myr=request.alternative_coverage_limit_myr,
    )
    narratives = await generate_life_event_narratives(request.profile, raw)

    scenarios: list[LifeEventScenario] = []
    citations: list[Citation] = []
    seen_sources: set[str] = set()
    for raw_item, (narrative_en, narrative_bm) in zip(raw, narratives, strict=True):
        scenarios.append(
            LifeEventScenario(
                event=raw_item.event,
                total_event_cost_myr=raw_item.total_event_cost_myr,
                covered_myr=raw_item.covered_myr,
                copay_myr=raw_item.copay_myr,
                out_of_pocket_myr=raw_item.out_of_pocket_myr,
                months_income_at_risk=raw_item.months_income_at_risk,
                alternative_out_of_pocket_myr=raw_item.alternative_out_of_pocket_myr,
                narrative_en=narrative_en,
                narrative_bm=narrative_bm,
            )
        )
        if raw_item.citation_source not in seen_sources:
            citations.append(
                Citation(
                    source=raw_item.citation_source,
                    quote=raw_item.citation_quote,
                    locator=raw_item.citation_locator,
                )
            )
            seen_sources.add(raw_item.citation_source)

    score, band = compute_life_event_confidence(raw)
    return LifeEventSimulationResponse(
        policy_id=request.policy_id or _policy_id(request.profile),
        scenarios=scenarios,
        data_citations=citations,
        confidence_score=score,
        confidence_band=band,
    )
