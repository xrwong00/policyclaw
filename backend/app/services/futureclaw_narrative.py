"""FutureClaw narrative generation.

Single-GLM-call batch narrative generator for the Life Event simulator. Uses
`instructor` for typed Pydantic parsing and `tenacity` for retries. Falls back to
deterministic mock narratives when GLM_API_KEY is unset or after retries exhaust,
so the demo never 500s.
"""

from __future__ import annotations

import logging
from typing import Iterable

from pydantic import BaseModel, Field, ValidationError
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.schemas import PolicyInput
from app.services.ai_service import config as ai_config
from app.services.simulation import LifeEventRaw


logger = logging.getLogger(__name__)

_GLM_TIMEOUT_SECONDS = 30.0
_MAX_NARRATIVE_CHARS = 500  # matches LifeEventScenario.narrative_* schema limit


class _NarrativePair(BaseModel):
    event: str = Field(min_length=1)
    narrative_en: str = Field(min_length=1, max_length=_MAX_NARRATIVE_CHARS)
    narrative_bm: str = Field(min_length=1, max_length=_MAX_NARRATIVE_CHARS)


class _NarrativeBatch(BaseModel):
    scenarios: list[_NarrativePair] = Field(min_length=4, max_length=4)


def _build_prompt(profile: PolicyInput, scenarios: Iterable[LifeEventRaw]) -> str:
    lines = [
        "You are a Malaysian insurance decision copilot for PolicyClaw.",
        "Write an empathetic but direct one-paragraph narrative for each life event below.",
        f"Policyholder: age {profile.age_now}, monthly income RM{profile.projected_income_monthly_myr:,.0f},"
        f" policy '{profile.plan_name}' from {profile.insurer},"
        f" coverage limit RM{profile.coverage_limit_myr:,.0f}, annual premium RM{profile.annual_premium_myr:,.0f}.",
        "For each scenario output narrative_en (English) and narrative_bm (Bahasa Malaysia).",
        f"Each narrative MUST be under {_MAX_NARRATIVE_CHARS} characters, state the out-of-pocket impact in MYR,",
        "reference months of income at risk, and end with one concrete action the user can take.",
        "Do not invent numbers — only use the figures provided below.",
        "",
        "Scenarios:",
    ]
    for s in scenarios:
        lines.append(
            f"- event={s.event.value}"
            f" total_cost_myr={s.total_event_cost_myr:.0f}"
            f" covered_myr={s.covered_myr:.0f}"
            f" copay_myr={s.copay_myr:.0f}"
            f" out_of_pocket_myr={s.out_of_pocket_myr:.0f}"
            f" months_income_at_risk={s.months_income_at_risk:.1f}"
        )
    lines.append("")
    lines.append('Return strictly JSON matching {"scenarios":[{"event":..., "narrative_en":..., "narrative_bm":...}, ...]}')
    lines.append("Order the 4 scenarios in the SAME order as above.")
    return "\n".join(lines)


def _mock_batch(scenarios: list[LifeEventRaw], fallback_tag: str = "") -> list[tuple[str, str]]:
    tag = f"{fallback_tag} " if fallback_tag else ""
    output: list[tuple[str, str]] = []
    for s in scenarios:
        label = s.event.value.replace("_", " ").title()
        oop = s.out_of_pocket_myr
        months = s.months_income_at_risk
        en = (
            f"{tag}If {label} strikes, your policy covers RM{s.covered_myr:,.0f} of the RM{s.total_event_cost_myr:,.0f} bill,"
            f" leaving RM{oop:,.0f} out of pocket — about {months:.1f} months of household income."
            f" Talk to a licensed adviser about top-up riders before the next renewal."
        )
        bm = (
            f"{tag}Jika {label} berlaku, polisi anda menanggung RM{s.covered_myr:,.0f} daripada kos RM{s.total_event_cost_myr:,.0f},"
            f" meninggalkan RM{oop:,.0f} untuk anda tanggung sendiri — kira-kira {months:.1f} bulan pendapatan isi rumah."
            f" Bincang dengan ejen berlesen mengenai penambahan rider sebelum pembaharuan polisi."
        )
        # Clamp to schema limit defensively.
        output.append((en[:_MAX_NARRATIVE_CHARS], bm[:_MAX_NARRATIVE_CHARS]))
    return output


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=6),
    retry=retry_if_exception_type((ValidationError, ConnectionError, TimeoutError)),
    reraise=True,
)
async def _call_glm(prompt: str) -> _NarrativeBatch:
    import instructor
    from openai import AsyncOpenAI

    client = instructor.from_openai(
        AsyncOpenAI(
            api_key=ai_config.api_key,
            base_url=ai_config.api_base,
            timeout=_GLM_TIMEOUT_SECONDS,
        ),
        mode=instructor.Mode.JSON,
    )

    return await client.chat.completions.create(
        model=ai_config.model,
        response_model=_NarrativeBatch,
        messages=[
            {"role": "system", "content": "You write concise, cited insurance narratives in JSON."},
            {"role": "user", "content": prompt},
        ],
        max_retries=1,  # instructor-internal validation retry; outer tenacity handles network
    )


async def generate_life_event_narratives(
    profile: PolicyInput,
    scenarios: list[LifeEventRaw],
) -> list[tuple[str, str]]:
    """Return (narrative_en, narrative_bm) pairs aligned to the input scenarios order.

    Single GLM call per invocation. Falls back to mock narratives when mock mode is
    active or when the GLM call fails after retries.
    """
    if ai_config.is_mock_mode:
        return _mock_batch(scenarios)

    prompt = _build_prompt(profile, scenarios)
    try:
        batch = await _call_glm(prompt)
    except (RetryError, ValidationError, ConnectionError, TimeoutError, Exception) as exc:  # noqa: BLE001
        logger.warning("FutureClaw narrative GLM call failed, falling back to mock: %s", exc)
        return _mock_batch(scenarios, fallback_tag="[fallback]")

    by_event = {pair.event: pair for pair in batch.scenarios}
    output: list[tuple[str, str]] = []
    for s in scenarios:
        pair = by_event.get(s.event.value)
        if pair is None:
            # Model returned the right count but wrong labels — fill from mock for this event only.
            mock_en, mock_bm = _mock_batch([s], fallback_tag="[fallback]")[0]
            output.append((mock_en, mock_bm))
            continue
        output.append((pair.narrative_en[:_MAX_NARRATIVE_CHARS], pair.narrative_bm[:_MAX_NARRATIVE_CHARS]))
    return output
