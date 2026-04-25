"""
AI Service Layer for PolicyClaw.

This module orchestrates calls to an OpenAI-compatible chat-completions API.
When OPENAI_API_KEY is not set, all functions return carefully crafted mock
responses. When set, functions call the real API.

Environment variables:
  - OPENAI_API_KEY: Provider API key (leave empty for mock mode)
  - OPENAI_API_BASE: API endpoint (default: https://api.openai.com/v1)
  - OPENAI_MODEL: Model identifier (default: gpt-5-mini)
"""

from __future__ import annotations

import json
from datetime import datetime
from uuid import uuid4

from app.core.glm_client import (
    AIServiceConfig,
    config,
    confidence_band_from_score as _confidence_band_from_score,
    extract_json_from_content as _extract_json_from_content,
    post_glm_with_retry as _post_glm_with_retry,
)
from app.schemas import (
    BNMRight,
    BNMRightsScannerResponse,
    Citation,
    ConfidenceBand,
    HealthScore,
    MultilingualExplanation,
    OverlapMapResponse,
    PolicyClause,
    PolicyInput,
    PolicyVerdict,
    Reason,
    PolicyXRayResponse,
    VerdictLabel,
    VoiceInterrogationResponse,
    CoverageZone,
    CitationVaultResponse,
    CitationVaultEntry,
)
from app.services import demo_cache
from app.services.verdict import generate_verdict

# `AIServiceConfig` and `config` are re-exported above from `app.core.glm_client`
# so test code that does `ai_service.AIServiceConfig()` / reassigns
# `ai_service.config` keeps working without changes.


async def _call_glm_policy_xray(
    policy_input: PolicyInput,
    policy_id: str,
    context: str | None = None,
) -> PolicyXRayResponse:
    """Call GLM API for F1 Policy X-Ray and return schema-validated response.

    When `context` (retrieved PDF text chunks) is provided, the prompt instructs
    the model to paraphrase clauses drawn from the real document rather than
    inventing plausible-sounding Malaysian insurance clauses. This grounds the
    downstream `citations[]` array in the uploaded PDF — PRD P2 compliance.
    """
    if not config.api_key:
        raise RuntimeError("OPENAI_API_KEY is missing")

    url = f"{config.api_base.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    schema_hint = {
        "policy_id": "string",
        "insurer": "string",
        "plan_name": "string",
        "policy_type": "medical|life|critical_illness|takaful|other",
        "extracted_fields": {
            "annual_premium": "number",
            "coverage_limit": "number",
            "effective_date": "YYYY-MM-DD",
            "age_now": "number",
        },
        "key_clauses": [
            {
                "title": "string",
                "original_text": "string",
                "plain_language_en": "string",
                "plain_language_bm": "string",
                "gotcha_flag": "boolean",
                "source_page": "integer >=1",
            }
        ],
        "gotcha_count": "integer >=0",
        "confidence_score": "number 0-100",
        "confidence_band": "low|medium|high",
    }

    prompt = {
        "policy_id": policy_id,
        "insurer": policy_input.insurer,
        "plan_name": policy_input.plan_name,
        "policy_type": policy_input.policy_type.value,
        "annual_premium_myr": policy_input.annual_premium_myr,
        "coverage_limit_myr": policy_input.coverage_limit_myr,
        "effective_date": policy_input.effective_date.isoformat(),
        "age_now": policy_input.age_now,
        "projected_income_monthly_myr": policy_input.projected_income_monthly_myr,
        "expected_income_growth_pct": policy_input.expected_income_growth_pct,
    }

    if context:
        user_content = (
            "Extract a PolicyXRayResponse JSON for the policy BELOW. "
            "Every `key_clauses[]` entry MUST paraphrase text that appears in the "
            "Context section; do NOT invent clauses that are not present in the "
            "Context. `source_page` must be the actual PDF page number the clause "
            "is drawn from (see the `page=N` markers in each context block). "
            "`original_text` is a short verbatim quote from the Context. "
            "Output must follow this schema shape exactly: "
            f"{json.dumps(schema_hint, ensure_ascii=True)}\n"
            f"Input policy: {json.dumps(prompt, ensure_ascii=True)}\n\n"
            f"Context (uploaded PDF chunks):\n{context}"
        )
        system_content = (
            "You are PolicyClaw's Policy X-Ray analyst for Malaysia. "
            "Return strict JSON only, no markdown, no prose outside JSON. "
            "Ground every clause in the supplied Context. If the Context is thin, "
            "return fewer clauses rather than inventing ones. "
            "Keep clause explanations concise and factual."
        )
    else:
        user_content = (
            "Generate a PolicyXRayResponse JSON for this policy input. "
            "Use realistic clauses for Malaysian insurance contexts. "
            "Output must follow this schema shape exactly: "
            f"{json.dumps(schema_hint, ensure_ascii=True)}\n"
            f"Input policy: {json.dumps(prompt, ensure_ascii=True)}"
        )
        system_content = (
            "You are PolicyClaw's Policy X-Ray analyst for Malaysia. "
            "Return strict JSON only, no markdown, no prose outside JSON. "
            "Keep clause explanations concise and factual."
        )

    payload = {
        "model": config.model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ],
    }

    content = await _post_glm_with_retry(url=url, headers=headers, payload=payload)
    parsed = _extract_json_from_content(content)

    parsed["policy_id"] = policy_id
    parsed["insurer"] = policy_input.insurer
    parsed["plan_name"] = policy_input.plan_name
    parsed["policy_type"] = policy_input.policy_type.value

    extracted_fields = parsed.get("extracted_fields") or {}
    if not isinstance(extracted_fields, dict):
        extracted_fields = {}
    extracted_fields.setdefault("annual_premium", policy_input.annual_premium_myr)
    extracted_fields.setdefault("coverage_limit", policy_input.coverage_limit_myr)
    extracted_fields.setdefault("effective_date", policy_input.effective_date.isoformat())
    extracted_fields.setdefault("age_now", policy_input.age_now)
    parsed["extracted_fields"] = extracted_fields

    clauses = parsed.get("key_clauses")
    if not isinstance(clauses, list) or not clauses:
        raise RuntimeError("GLM response missing key_clauses")
    parsed["gotcha_count"] = sum(1 for clause in clauses if clause.get("gotcha_flag") is True)

    confidence_score = float(parsed.get("confidence_score", 70.0))
    confidence_score = max(0.0, min(100.0, confidence_score))
    parsed["confidence_score"] = confidence_score

    band_value = str(parsed.get("confidence_band", "")).lower()
    if band_value not in {"low", "medium", "high"}:
        parsed["confidence_band"] = _confidence_band_from_score(confidence_score).value

    return PolicyXRayResponse.model_validate(parsed)


async def _call_glm_policy_verdict(
    policy: PolicyInput,
    policy_id: str,
    realistic_10y_cost_myr: float,
    xray: PolicyXRayResponse | None = None,
    health: HealthScore | None = None,
) -> PolicyVerdict:
    """Call GLM API for F5 Keep-Switch-Dump verdict and return validated response.

    When `xray` and `health` are provided, their context is passed to the prompt so
    the recommendation is grounded in the earlier pipeline stages. Temperature 0.1
    gives deterministic output on identical inputs (F7 acceptance).
    """
    if not config.api_key:
        raise RuntimeError("OPENAI_API_KEY is missing")

    cache_key = demo_cache.make_key(
        "recommend",
        policy_id,
        policy.model_dump(mode="json"),
        round(realistic_10y_cost_myr, 2),
        xray.model_dump(mode="json") if xray else None,
        health.model_dump(mode="json") if health else None,
    )
    cached = demo_cache.get(cache_key)
    if cached is not None:
        try:
            return PolicyVerdict.model_validate(cached)
        except Exception:
            pass  # Fall through and re-call GLM if cache payload is stale.

    url = f"{config.api_base.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    schema_hint = {
        "verdict": "keep|downgrade|switch|dump",
        "confidence_score": "number 0-100",
        "needs_rider": "boolean (true only when verdict==keep AND a specific rider gap is identified)",
        "reasons": [
            {
                "title": "string (prefix with 'Add rider:' when the primary action is adding a rider)",
                "detail": "string",
                "citation": {
                    "source": "human-readable source name (e.g. 'Policy X-Ray', 'Health Score narrative') — NEVER raw schema paths like 'policy_xray key_clauses'",
                    "quote": "exact verbatim quote from the source",
                    "locator": "human-readable pointer (e.g. 'Key Clause 2', 'Section 3.2'); empty string if redundant — NEVER raw paths like 'key_clauses[1]' or 'health_score.narrative_en'",
                },
            }
        ],
    }

    prompt = {
        "policy_id": policy_id,
        "insurer": policy.insurer,
        "plan_name": policy.plan_name,
        "policy_type": policy.policy_type.value,
        "annual_premium_myr": policy.annual_premium_myr,
        "coverage_limit_myr": policy.coverage_limit_myr,
        "effective_date": policy.effective_date.isoformat(),
        "age_now": policy.age_now,
        "projected_income_monthly_myr": policy.projected_income_monthly_myr,
        "expected_income_growth_pct": policy.expected_income_growth_pct,
        "realistic_10y_cost_myr": realistic_10y_cost_myr,
    }

    if xray is not None:
        prompt["policy_xray"] = {
            "gotcha_count": xray.gotcha_count,
            "confidence_score": xray.confidence_score,
            "key_clauses": [
                {
                    "title": c.title,
                    "plain_language_en": c.plain_language_en,
                    "gotcha_flag": c.gotcha_flag,
                    "source_page": c.source_page,
                }
                for c in xray.key_clauses[:6]
            ],
        }
    if health is not None:
        prompt["health_score"] = {
            "overall": health.overall,
            "coverage_adequacy": health.coverage_adequacy,
            "affordability": health.affordability,
            "premium_stability": health.premium_stability,
            "clarity_trust": health.clarity_trust,
            "narrative_en": health.narrative_en,
        }

    payload = {
        "model": config.model,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are PolicyClaw's decision strategist for Malaysian insurance. "
                    "Return strict JSON only. Give pragmatic decision support, not legal advice. "
                    "Ground every reason in the supplied policy_xray key_clauses or health_score narrative. "
                    "Set needs_rider=true ONLY when verdict=keep AND a specific rider gap is identified."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Generate a Keep/Switch/Downgrade/Dump verdict for this policy input. "
                    "Output must match this schema shape exactly: "
                    f"{json.dumps(schema_hint, ensure_ascii=True)}\n"
                    f"Input: {json.dumps(prompt, ensure_ascii=True)}"
                ),
            },
        ],
    }

    content = await _post_glm_with_retry(url=url, headers=headers, payload=payload)
    parsed = _extract_json_from_content(content)

    verdict_value = str(parsed.get("verdict", "")).lower()
    if verdict_value not in {"keep", "downgrade", "switch", "dump"}:
        raise RuntimeError("GLM verdict output missing valid verdict label")

    confidence_score = float(parsed.get("confidence_score", 70.0))
    confidence_score = max(0.0, min(100.0, confidence_score))

    reasons_data = parsed.get("reasons")
    if not isinstance(reasons_data, list) or len(reasons_data) < 2:
        raise RuntimeError("GLM verdict output missing sufficient reasons")

    cleaned_reasons: list[Reason] = []
    for item in reasons_data[:5]:
        cleaned_reasons.append(Reason.model_validate(item))

    # Carry the needs_rider hint through the first reason's title since PolicyVerdict
    # schema is shared with other worktrees and we don't want to change its shape.
    # Detection uses the exact "add rider:" prefix (including colon) — matches the
    # format the writer below produces and what _needs_rider_flag looks for.
    # Strict boolean parsing — a JSON string like "false" is truthy in Python,
    # so coerce via known-good representations only.
    raw_needs_rider = parsed.get("needs_rider", False)
    if isinstance(raw_needs_rider, bool):
        needs_rider_raw = raw_needs_rider
    elif isinstance(raw_needs_rider, (int, float)):
        needs_rider_raw = bool(raw_needs_rider)
    elif isinstance(raw_needs_rider, str):
        needs_rider_raw = raw_needs_rider.strip().lower() in {"true", "1", "yes"}
    else:
        needs_rider_raw = False
    needs_rider = needs_rider_raw and verdict_value == "keep"
    if needs_rider and cleaned_reasons and not cleaned_reasons[0].title.lower().startswith("add rider:"):
        first = cleaned_reasons[0]
        cleaned_reasons[0] = Reason(
            title=f"Add rider: {first.title}",
            detail=first.detail,
            citation=first.citation,
        )

    projected_savings = 0.0
    if verdict_value == "keep":
        projected_savings = realistic_10y_cost_myr * 0.05
    elif verdict_value == "downgrade":
        projected_savings = realistic_10y_cost_myr * 0.12
    elif verdict_value == "switch":
        projected_savings = realistic_10y_cost_myr * 0.18
    elif verdict_value == "dump":
        projected_savings = realistic_10y_cost_myr * 0.22

    result = PolicyVerdict(
        policy_id=policy_id,
        verdict=VerdictLabel(verdict_value),
        confidence_score=confidence_score,
        confidence_band=_confidence_band_from_score(confidence_score),
        projected_10y_premium_myr=realistic_10y_cost_myr,
        projected_10y_savings_myr=round(float(projected_savings), 2),
        reasons=cleaned_reasons,
    )
    try:
        demo_cache.put(cache_key, result.model_dump(mode="json"))
    except Exception:
        pass  # Cache write is best effort; never discard a successful GLM result.
    return result


def _heuristic_policy_verdict(policy: PolicyInput, realistic_10y_cost_myr: float) -> PolicyVerdict:
    """Deterministic fallback for verdict generation when GLM is unavailable."""
    policy_id = f"{policy.insurer}-{policy.plan_name}".lower().replace(" ", "-")
    verdict, confidence, projected_savings, band = generate_verdict(
        policy=policy,
        realistic_10y_cost_myr=realistic_10y_cost_myr,
    )

    reasons = [
        Reason(
            title="Premium affordability signal",
            detail="Assessment compares annual premium against projected household income trajectory.",
            citation=Citation(
                source="PolicyClaw Simulation Engine",
                quote="Premium ratio against income used for initial recommendation thresholding.",
                locator="simulation.py:project_premiums",
            ),
        ),
        Reason(
            title="10-year cost projection",
            detail="Realistic inflation scenario quantifies long-term burden and potential optimization impact.",
            citation=Citation(
                source="PolicyClaw Simulation Engine",
                quote="Realistic scenario applies 10% inflation with age-band jumps.",
                locator="simulation.py:project_premiums",
            ),
        ),
    ]

    if verdict.value in {"switch", "dump"}:
        reasons.append(
            Reason(
                title="Switch/downgrade opportunity",
                detail="Estimated savings suggest this policy may be optimized or replaced.",
                citation=Citation(
                    source="PolicyClaw Heuristic Verdict",
                    quote="Policies with high premium burden are candidates for switch or downgrade.",
                    locator="verdict.py:generate_verdict",
                ),
            )
        )

    return PolicyVerdict(
        policy_id=policy_id,
        verdict=verdict,
        confidence_score=confidence,
        confidence_band=band,
        projected_10y_premium_myr=realistic_10y_cost_myr,
        projected_10y_savings_myr=projected_savings,
        reasons=reasons,
    )


# ===== MOCK DATA GENERATORS =====


def _mock_policy_xray(policy_input: PolicyInput, policy_id: str) -> PolicyXRayResponse:
    """Mock F1: Policy X-Ray response."""
    return PolicyXRayResponse(
        policy_id=policy_id,
        insurer=policy_input.insurer,
        plan_name=policy_input.plan_name,
        policy_type=policy_input.policy_type,
        extracted_fields={
            "annual_premium": policy_input.annual_premium_myr,
            "coverage_limit": policy_input.coverage_limit_myr,
            "effective_date": policy_input.effective_date.isoformat(),
            "age_now": policy_input.age_now,
        },
        key_clauses=[
            PolicyClause(
                title="Coverage Scope",
                original_text="All injuries and illnesses are covered, with exceptions listed in Schedule A.",
                plain_language_en="You are covered for most medical treatment, except for specific exclusions in the policy document (Schedule A).",
                plain_language_bm="Anda dilindungi untuk kebanyakan rawatan perubatan, kecuali pengecualian khusus yang tersenarai dalam Jadual A.",
                gotcha_flag=False,
                source_page=2,
            ),
            PolicyClause(
                title="30-Day Waiting Period",
                original_text="New claims within 30 days of policy inception are subject to a 30-day elimination period.",
                plain_language_en="If you need to make a claim within the first month, the waiting period applies.",
                plain_language_bm="Jika anda perlu membuat tuntutan dalam bulan pertama, tempoh menunggu berkuat kuasa.",
                gotcha_flag=True,
                source_page=3,
            ),
            PolicyClause(
                title="Pre-existing Condition Exclusion",
                original_text="Any condition diagnosed before policy inception is excluded for 12 months.",
                plain_language_en="If you had a health condition before buying this policy, it won't be covered for one year.",
                plain_language_bm="Jika anda mempunyai masalah kesihatan sebelum membeli polisi ini, ia tidak akan dilindungi selama satu tahun.",
                gotcha_flag=True,
                source_page=4,
            ),
        ],
        gotcha_count=2,
        confidence_score=78.5,
        confidence_band=ConfidenceBand.MEDIUM,
    )


def _mock_overlap_map(policy_inputs: list[PolicyInput], analysis_id: str) -> OverlapMapResponse:
    """Mock F2: Overlap Map response."""
    if len(policy_inputs) < 2:
        return OverlapMapResponse(
            analysis_id=analysis_id,
            total_policies=len(policy_inputs),
            overlap_zones=[],
            total_duplicate_premium_yearly_myr=0.0,
            total_potential_savings_yearly_myr=0.0,
            consolidation_recommendation="Only one policy provided. No overlap detected.",
            confidence_score=100.0,
            confidence_band=ConfidenceBand.HIGH,
        )

    # Mock: assume policies 0 and 1 have overlap
    overlap_zones = [
        CoverageZone(
            coverage_type="hospitalization",
            policies_involved=[policy_inputs[0].plan_name, policy_inputs[1].plan_name],
            duplicate_premium_yearly_myr=600.0,
            covered_amount_myr=100000.0,
            severity="high",
        ),
        CoverageZone(
            coverage_type="critical_illness",
            policies_involved=[policy_inputs[0].plan_name, policy_inputs[1].plan_name],
            duplicate_premium_yearly_myr=300.0,
            covered_amount_myr=50000.0,
            severity="medium",
        ),
    ]

    total_dup_premium = sum(z.duplicate_premium_yearly_myr for z in overlap_zones)
    return OverlapMapResponse(
        analysis_id=analysis_id,
        total_policies=len(policy_inputs),
        overlap_zones=overlap_zones,
        total_duplicate_premium_yearly_myr=total_dup_premium,
        total_potential_savings_yearly_myr=total_dup_premium * 0.9,  # Conservative 90% savings estimate
        consolidation_recommendation=f"You have identified overlapping coverage across {len(policy_inputs)} policies. Consider consolidating medical and critical illness coverage into a single plan to reduce duplicate premiums by approximately RM {total_dup_premium:.0f} per year.",
        confidence_score=65.0,
        confidence_band=ConfidenceBand.MEDIUM,
    )


def _mock_bnm_rights_scanner(policy_input: PolicyInput, policy_id: str) -> BNMRightsScannerResponse:
    """Mock F4: BNM Rights Scanner response."""
    applicable_rights = [
        BNMRight(
            rule_id="BNM_2024_REPRICING_10PCT",
            title="Annual Premium Cap (10%)",
            description="Bank Negara Malaysia caps annual premium increases at 10% for MHIT policies until 31 December 2026.",
            eligible=True,
            currently_applied=False,  # Mock: not applied
            potential_savings_myr=policy_input.annual_premium_myr * 0.08,  # Savings from not hiking above 10%
            demand_letter_text_en="Dear [Insurer Name], I am writing to request that you apply Bank Negara Malaysia's premium cap of 10% annual increase to my policy number [POLICY_ID], effective immediately, as mandated under BNM Press Release 31 December 2024.",
            demand_letter_text_bm="Dengan hormatnya, saya menulis untuk meminta agar anda memohonkan had premium 10% tahunan Bank Negara Malaysia kepada polisi saya nombor [POLICY_ID], berkuat kuasa serta-merta, seperti yang diwajibkan di bawah Siaran Akhbar BNM 31 Disember 2024.",
            bnm_circular_reference="BNM Press Release, 31 December 2024: Interim Measures for MHIT Policyholders",
        ),
        BNMRight(
            rule_id="BNM_2024_COPAYMENT_FLEXIBILITY",
            title="Copayment Flexibility",
            description="Insurers must offer at least one MHIT plan with copayment flexibility (e.g., RM100 or RM300 options).",
            eligible=True,
            currently_applied=True,
            potential_savings_myr=0.0,
            demand_letter_text_en="",
            demand_letter_text_bm="",
            bnm_circular_reference="BNM Circular 31 July 2024",
        ),
    ]

    total_unapplied = sum(r.potential_savings_myr for r in applicable_rights if not r.currently_applied)
    return BNMRightsScannerResponse(
        policy_id=policy_id,
        applicable_rights=applicable_rights,
        total_unapplied_savings_myr=total_unapplied,
        recommended_actions=[
            "Send the demand letter to your insurer requesting the 10% cap be applied.",
            "Follow up within 7 days if no acknowledgment received.",
            "File a complaint with BNM if the insurer refuses to apply the cap.",
        ],
        confidence_score=82.0,
        confidence_band=ConfidenceBand.HIGH,
    )


def _mock_voice_interrogation(
    question: str, language: str, policy_ids: list[str]
) -> VoiceInterrogationResponse:
    """Mock F7: Voice Policy Interrogation response."""
    # Simple mock answers based on question keywords
    if "cover" in question.lower() or "cakupan" in question.lower():
        answer_en = "Based on your uploaded policies, your main coverage includes hospitalization, critical illness, and disability benefits. You also have outpatient coverage up to RM500 per year."
        answer_bm = "Berdasarkan dasar anda yang dimuatnaik, cakupan utama anda termasuk manfaat rawatan di hospital, penyakit kritikal, dan hilang upaya. Anda juga mempunyai cakupan pesakit luar sehingga RM500 setahun."
    elif "premium" in question.lower() or "premium" in question.lower():
        answer_en = "Your total annual premium across all uploaded policies is approximately RM4,200. In 10 years, this could grow to RM52,000 under realistic economic scenarios."
        answer_bm = "Jumlah premium tahunan anda merentasi semua polisi yang dimuat naik adalah kira-kira RM4,200. Dalam 10 tahun, ini boleh berkembang kepada RM52,000 di bawah senario ekonomi yang realistik."
    else:
        answer_en = "I can help you understand your policies, compare coverage, check BNM rights, or simulate future scenarios. What would you like to know?"
        answer_bm = "Saya boleh membantu anda memahami polisi anda, membandingkan cakupan, memeriksa hak BNM, atau mensimulasikan senario masa depan. Apa yang ingin anda ketahui?"

    # Choose language
    if language == "bm":
        answer = answer_bm
    elif language == "zh":
        answer = answer_en  # Fallback to English for now
    elif language == "hokkien":
        answer = answer_en  # Fallback to English for now
    else:
        answer = answer_en

    return VoiceInterrogationResponse(
        question_transcript=question,
        answer_text=answer,
        answer_language=language,
        citations=[
            Citation(
                source="Policy Upload",
                quote="Your policies cover hospitalization, critical illness, and disability.",
                locator="Extracted from uploaded policy documents",
            )
        ],
        confidence_score=71.0,
        audio_url="",  # Future: TTS URL
    )


def _mock_multilingual_explanation(subject: str, target_language: str) -> MultilingualExplanation:
    """Mock F9: Multi-lingual Explainer response."""
    return MultilingualExplanation(
        subject=subject,
        explanation_en=f"This is an explanation of {subject} for Malaysian policyholders. It covers the key concepts and how they apply to your insurance decisions.",
        explanation_bm=f"Ini adalah penjelasan tentang {subject} untuk pemegang polisi Malaysia. Ia meliputi konsep utama dan cara ia berlaku kepada keputusan insurans anda.",
        explanation_zh=f"这是关于{subject}的解释，针对马来西亚保单持有人。它涵盖了关键概念及其如何应用于您的保险决策。",
        explanation_hokkien=f"Tsia tsiok tsi buan bue {subject} gia tshik bue, hun kuann Malaysia he khoo hhue jit gia.  [Best-effort Hokkien transliteration]",
        target_audience="policyholder",
    )


def _mock_citation_vault(analysis_id: str, policy_count: int) -> CitationVaultResponse:
    """Mock F11: Citation Vault response."""
    entries = [
        CitationVaultEntry(
            citation_id=f"cite_{i}",
            claim=f"Mock claim {i} from policy analysis",
            source_document=f"Policy Document {i % policy_count}",
            source_page=2 + (i % 5),
            quote=f"Mock quote from source document page {2 + (i % 5)}",
            timestamp_utc=datetime.utcnow().isoformat(),
            claim_type="extraction",
            confidence_score=75.0 + (i % 20),
        )
        for i in range(5)
    ]

    avg_confidence = sum(e.confidence_score for e in entries) / len(entries)
    return CitationVaultResponse(
        analysis_id=analysis_id,
        total_citations=len(entries),
        entries=entries,
        avg_confidence_score=avg_confidence,
        low_confidence_claims=[],
    )


# ===== PUBLIC API =====


async def analyze_policy_xray(
    policy_input: PolicyInput,
    policy_id: str,
    context: str | None = None,
    file_digest: str | None = None,
) -> PolicyXRayResponse:
    """
    F1: Policy X-Ray — Extract and translate policy clauses.

    Args:
        policy_input: Structured policy input
        policy_id: Unique policy identifier
        context: Optional concatenated PDF text chunks for GLM grounding
        file_digest: Optional SHA-256 over raw uploaded PDF bytes — included in
            the cache key so two different PDFs with identical profile fields
            don't share cached analysis output.

    Returns:
        PolicyXRayResponse with extracted fields and plain-language clauses
    """
    if config.is_mock_mode:
        return _mock_policy_xray(policy_input, policy_id)

    cache_key = demo_cache.make_key(
        "extract",
        policy_id,
        policy_input.model_dump(mode="json"),
        file_digest or "",
        bool(context),
    )
    cached = demo_cache.get(cache_key)
    if cached is not None:
        try:
            return PolicyXRayResponse.model_validate(cached)
        except Exception:
            pass  # Cached payload stale — re-call GLM.

    try:
        result = await _call_glm_policy_xray(policy_input, policy_id, context=context)
        # Cache write is best-effort — never let a disk-full or permission error
        # discard a successful GLM response.
        try:
            demo_cache.put(cache_key, result.model_dump(mode="json"))
        except Exception:
            pass
        return result
    except Exception:
        fallback = _mock_policy_xray(policy_input, policy_id)
        fallback.confidence_score = 45.0
        fallback.confidence_band = ConfidenceBand.LOW
        fallback.extracted_fields["llm_status"] = "fallback_mock_due_to_llm_error"
        return fallback


# ===== F5 HEALTH SCORE (GLM Call 3 — Score) =====

_HEALTH_SCORE_SCHEMA_HINT = {
    "coverage_adequacy": "integer 0-25",
    "affordability": "integer 0-25",
    "premium_stability": "integer 0-25",
    "clarity_trust": "integer 0-25",
    "narrative_en": "string 1-500 chars",
    "narrative_bm": "string 1-500 chars",
    "confidence_score": "number 0-100",
}


async def _call_glm_health_score(
    policy_input: PolicyInput, xray: PolicyXRayResponse
) -> HealthScore:
    """Call GLM API for F5 Health Score and return validated HealthScore."""
    if not config.api_key:
        raise RuntimeError("OPENAI_API_KEY is missing")

    url = f"{config.api_base.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    prompt = {
        "policy": policy_input.model_dump(mode="json"),
        "xray_summary": {
            "gotcha_count": xray.gotcha_count,
            "confidence_score": xray.confidence_score,
            "clauses": [
                {
                    "title": c.title,
                    "plain_language_en": c.plain_language_en,
                    "gotcha_flag": c.gotcha_flag,
                }
                for c in xray.key_clauses[:8]
            ],
        },
    }

    payload = {
        "model": config.model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are PolicyClaw's Health Score analyst. Return strict JSON only. "
                    "Produce four 0-25 sub-scores: coverage_adequacy, affordability, "
                    "premium_stability, clarity_trust. Calibrate strictly — the overall "
                    "(sum of sub-scores) must land between 30 and 85 for real Malaysian "
                    "policies. Do not output 95+ unless every single sub-score clearly "
                    "deserves a maximum. Provide narrative_en and narrative_bm under 500 chars each."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Schema: {json.dumps(_HEALTH_SCORE_SCHEMA_HINT, ensure_ascii=True)}\n\n"
                    f"Input: {json.dumps(prompt, ensure_ascii=True, default=str)}"
                ),
            },
        ],
    }

    content = await _post_glm_with_retry(url=url, headers=headers, payload=payload)
    parsed = _extract_json_from_content(content)

    def _clip(value, lo, hi):
        try:
            v = int(round(float(value)))
        except (TypeError, ValueError):
            v = lo
        return max(lo, min(hi, v))

    coverage = _clip(parsed.get("coverage_adequacy"), 0, 25)
    afford = _clip(parsed.get("affordability"), 0, 25)
    stability = _clip(parsed.get("premium_stability"), 0, 25)
    clarity = _clip(parsed.get("clarity_trust"), 0, 25)
    overall = coverage + afford + stability + clarity

    confidence = float(parsed.get("confidence_score", 70.0))
    confidence = max(0.0, min(100.0, confidence))

    return HealthScore(
        overall=overall,
        coverage_adequacy=coverage,
        affordability=afford,
        premium_stability=stability,
        clarity_trust=clarity,
        narrative_en=str(parsed.get("narrative_en") or "No narrative returned.")[:500],
        narrative_bm=str(parsed.get("narrative_bm") or "Tiada naratif dikembalikan.")[:500],
        confidence_score=confidence,
        confidence_band=_confidence_band_from_score(confidence),
    )


def _heuristic_health_score(
    policy_input: PolicyInput, xray: PolicyXRayResponse | None = None
) -> HealthScore:
    """Deterministic fallback targeting a 45-65 overall range so the demo never shows 95."""
    annual_income = policy_input.projected_income_monthly_myr * 12.0
    burden = policy_input.annual_premium_myr / max(annual_income, 1.0)
    coverage_ratio = policy_input.coverage_limit_myr / max(annual_income, 1.0)

    if burden < 0.04:
        affordability = 22
    elif burden < 0.07:
        affordability = 18
    elif burden < 0.10:
        affordability = 14
    elif burden < 0.15:
        affordability = 10
    else:
        affordability = 6

    if coverage_ratio >= 20:
        coverage_adequacy = 22
    elif coverage_ratio >= 10:
        coverage_adequacy = 17
    elif coverage_ratio >= 5:
        coverage_adequacy = 13
    else:
        coverage_adequacy = 8

    premium_stability = 14
    # Let clarity dip when the xray flagged many gotchas.
    gotchas = xray.gotcha_count if xray else 0
    clarity_trust = max(6, 18 - gotchas * 3)

    overall = affordability + coverage_adequacy + premium_stability + clarity_trust
    return HealthScore(
        overall=overall,
        coverage_adequacy=coverage_adequacy,
        affordability=affordability,
        premium_stability=premium_stability,
        clarity_trust=clarity_trust,
        narrative_en=(
            "Heuristic score: premium burden and coverage ratio drive the result. "
            "AI narrative unavailable; review with an advisor if the gauge is below 50."
        ),
        narrative_bm=(
            "Skor heuristik: bebanan premium dan nisbah perlindungan mendorong keputusan. "
            "Naratif AI tidak tersedia; rujuk penasihat jika tolok menunjukkan di bawah 50."
        ),
        confidence_score=55.0,
        confidence_band=ConfidenceBand.LOW,
    )


async def analyze_health_score(
    policy_input: PolicyInput, xray: PolicyXRayResponse
) -> HealthScore:
    """F5 Health Score synthesis with GLM primary path and heuristic fallback."""
    if config.is_mock_mode:
        return _heuristic_health_score(policy_input, xray)

    cache_key = demo_cache.make_key(
        "score",
        policy_input.model_dump(mode="json"),
        xray.model_dump(mode="json"),
    )
    cached = demo_cache.get(cache_key)
    if cached is not None:
        try:
            return HealthScore.model_validate(cached)
        except Exception:
            pass

    try:
        result = await _call_glm_health_score(policy_input, xray)
        try:
            demo_cache.put(cache_key, result.model_dump(mode="json"))
        except Exception:
            pass
        return result
    except Exception:
        fallback = _heuristic_health_score(policy_input, xray)
        # Nudge confidence even lower so the UI flags the fallback.
        fallback = HealthScore(
            overall=fallback.overall,
            coverage_adequacy=fallback.coverage_adequacy,
            affordability=fallback.affordability,
            premium_stability=fallback.premium_stability,
            clarity_trust=fallback.clarity_trust,
            narrative_en=fallback.narrative_en,
            narrative_bm=fallback.narrative_bm,
            confidence_score=45.0,
            confidence_band=ConfidenceBand.LOW,
        )
        return fallback


async def analyze_overlap_map(
    policy_inputs: list[PolicyInput], analysis_id: str
) -> OverlapMapResponse:
    """
    F2: Overlap Map — Detect coverage overlaps across policies.

    Args:
        policy_inputs: List of structured policy inputs
        analysis_id: Unique analysis identifier

    Returns:
        OverlapMapResponse with detected zones and savings estimate
    """
    if config.is_mock_mode:
        return _mock_overlap_map(policy_inputs, analysis_id)

    # TODO: Call GLM API when key is available
    # return await _call_glm_overlap_map(policy_inputs, analysis_id)
    raise NotImplementedError("GLM API integration pending")


async def analyze_policy_verdict(
    policy: PolicyInput,
    realistic_10y_cost_myr: float,
    xray: PolicyXRayResponse | None = None,
    health: HealthScore | None = None,
) -> PolicyVerdict:
    """F5 verdict synthesis with GLM primary path and deterministic fallback.

    Optional `xray` and `health` context are passed into the GLM prompt so the
    recommendation is grounded in the Extract and Score stage outputs.
    """
    if config.is_mock_mode:
        return _heuristic_policy_verdict(policy, realistic_10y_cost_myr)

    policy_id = f"{policy.insurer}-{policy.plan_name}".lower().replace(" ", "-")
    try:
        return await _call_glm_policy_verdict(
            policy, policy_id, realistic_10y_cost_myr, xray=xray, health=health
        )
    except Exception:
        fallback = _heuristic_policy_verdict(policy, realistic_10y_cost_myr)
        fallback.confidence_score = min(fallback.confidence_score, 55.0)
        fallback.confidence_band = ConfidenceBand.LOW
        fallback.reasons.append(
            Reason(
                title="LLM fallback activated",
                detail="LLM call failed or timed out, so deterministic fallback logic was used for reliability.",
                citation=Citation(
                    source="PolicyClaw Runtime",
                    quote="LLM provider request did not complete within configured limits.",
                    locator="ai_service.py:analyze_policy_verdict",
                ),
            )
        )
        return fallback


async def scan_bnm_rights(
    policy_input: PolicyInput, policy_id: str
) -> BNMRightsScannerResponse:
    """
    F4: BNM Rights Scanner — Check policy eligibility for BNM protections.

    Args:
        policy_input: Structured policy input
        policy_id: Unique policy identifier

    Returns:
        BNMRightsScannerResponse with applicable rights and demand letters
    """
    if config.is_mock_mode:
        return _mock_bnm_rights_scanner(policy_input, policy_id)

    # TODO: Call GLM API when key is available
    # return await _call_glm_bnm_rights(policy_input, policy_id)
    raise NotImplementedError("GLM API integration pending")


async def interrogate_policy_voice(
    question: str, language: str = "en", policy_ids: list[str] | None = None
) -> VoiceInterrogationResponse:
    """
    F7: Voice Policy Interrogation — Answer user questions about policies.

    Args:
        question: User's question transcript
        language: Language code (bm, en, zh, hokkien)
        policy_ids: Optional list of policy IDs to scope question

    Returns:
        VoiceInterrogationResponse with answer and citations
    """
    if config.is_mock_mode:
        return _mock_voice_interrogation(question, language, policy_ids or [])

    # TODO: Call GLM API when key is available
    # return await _call_glm_voice_interrogation(question, language, policy_ids)
    raise NotImplementedError("GLM API integration pending")


async def explain_multilingual(
    subject: str, target_language: str = "en"
) -> MultilingualExplanation:
    """
    F9: Multi-lingual Explainer — Generate explanations in multiple languages.

    Args:
        subject: Topic to explain
        target_language: Target language (bm, en, zh, hokkien)

    Returns:
        MultilingualExplanation with native-quality text in 4 languages
    """
    if config.is_mock_mode:
        return _mock_multilingual_explanation(subject, target_language)

    # TODO: Call GLM API when key is available
    # return await _call_glm_multilingual_explanation(subject, target_language)
    raise NotImplementedError("GLM API integration pending")


async def vault_citations(analysis_id: str, policy_count: int) -> CitationVaultResponse:
    """
    F11: Citation Vault — Retrieve all citations and confidence scores from an analysis.

    Args:
        analysis_id: Unique analysis identifier
        policy_count: Number of policies analyzed

    Returns:
        CitationVaultResponse with citation entries and confidence metrics
    """
    if config.is_mock_mode:
        return _mock_citation_vault(analysis_id, policy_count)

    # TODO: Call GLM API when key is available, retrieve from database
    # return await _get_citations_from_database(analysis_id)
    raise NotImplementedError("Citation vault database integration pending")
