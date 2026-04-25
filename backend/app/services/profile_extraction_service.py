from __future__ import annotations

import json

from app.core.glm_client import (
    config as _config,
    extract_json_from_content as _extract_json_object,
    post_glm_with_retry as _post_with_retry,
)
from app.schemas import ExtractPolicyProfileResponse
from app.services.pdf_parser import parse_pdf_chunks
from app.services.rag import build_context, retrieve_relevant_chunks


def _normalize_response(parsed: dict) -> ExtractPolicyProfileResponse:
    data = {
        "profiles": parsed.get("profiles") or [],
        "detected_count": parsed.get("detected_count") or 0,
        "notes": parsed.get("notes") or [],
    }

    if not data["profiles"]:
        data["profiles"] = [
            {
                "option_id": "option-1",
                "display_label": "Document profile",
            }
        ]

    # Ensure stable ids and count
    for idx, profile in enumerate(data["profiles"], start=1):
        if not profile.get("option_id"):
            profile["option_id"] = f"option-{idx}"
        if not profile.get("display_label"):
            insurer = profile.get("insurer_name") or "Unknown insurer"
            plan = profile.get("plan_name") or "Unknown plan"
            profile["display_label"] = f"{insurer} - {plan}"

    data["detected_count"] = len(data["profiles"])
    return ExtractPolicyProfileResponse.model_validate(data)


async def extract_policy_profiles(files: list[tuple[str, bytes]]) -> ExtractPolicyProfileResponse:
    """Extract normalized policy profile candidates from uploaded PDF files."""
    api_key = _config.api_key
    api_base = _config.api_base
    model = _config.model

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    all_chunks = []
    for source_name, content in files:
        all_chunks.extend(parse_pdf_chunks(content, source_name))

    if not all_chunks:
        raise ValueError("No extractable text found in uploaded PDF")

    query = (
        "Extract insurer, policyholder, plan details, premium, currency, dates, "
        "coverage limit, riders and detect multiple plans/insured persons"
    )
    selected_chunks = retrieve_relevant_chunks(all_chunks, query=query, k=14)
    context = build_context(selected_chunks)

    schema_hint = {
        "profiles": [
            {
                "option_id": "string",
                "display_label": "string",
                "insurer_name": "string|null",
                "policyholder_name": "string|null",
                "plan_name": "string|null",
                "policy_type": "medical|life|critical_illness|takaful|other|null",
                "premium_amount": "number|null",
                "premium_frequency": "monthly|annual|null",
                "currency": "ISO 4217 string|null",
                "effective_date": "YYYY-MM-DD|null",
                "renewal_date": "YYYY-MM-DD|null",
                "coverage_limit": "number|null",
                "riders": ["string"],
                "source_pages": ["integer"],
                "confidence_score": "number 0-100|null",
            }
        ],
        "detected_count": "integer",
        "notes": ["string"],
    }

    payload = {
        "model": model,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are PolicyClaw's policy profile extraction engine. "
                    "Extract only evidence-backed fields from context. "
                    "If unclear, set null. Return JSON only."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Extract normalized policy profiles from context. "
                    "Support multiple insured persons/plans by returning multiple profile options. "
                    "Do not invent missing fields.\n\n"
                    f"Output schema: {json.dumps(schema_hint, ensure_ascii=True)}\n\n"
                    f"Context:\n{context}"
                ),
            },
        ],
    }

    url = f"{api_base.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    content = await _post_with_retry(url=url, headers=headers, payload=payload)
    parsed = _extract_json_object(content)
    return _normalize_response(parsed)
