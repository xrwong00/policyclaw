from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import httpx

from app.schemas import ExtractPolicyProfileResponse
from app.services.pdf_parser import parse_pdf_chunks
from app.services.rag import build_context, retrieve_relevant_chunks


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_local_env()


def _extract_json_object(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("LLM response did not include a valid JSON object")
    return json.loads(text[start : end + 1])


async def _post_with_retry(url: str, headers: dict[str, str], payload: dict) -> httpx.Response:
    retries = 3
    delay = 1.5
    last_error: Exception | None = None

    for attempt in range(retries):
        try:
            timeout = httpx.Timeout(75.0, connect=15.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                return await client.post(url, headers=headers, json=payload)
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError) as exc:
            last_error = exc
            if attempt < retries - 1:
                await asyncio.sleep(delay)
                delay *= 2
                continue
            break

    if last_error:
        raise last_error
    raise RuntimeError("LLM request failed")


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
    api_key = os.getenv("GLM_API_KEY", "").strip()
    api_base = os.getenv("GLM_API_BASE", "https://api.ilmu.ai/v1").strip()
    model = os.getenv("GLM_MODEL", "ilmu-glm-5.1").strip() or "ilmu-glm-5.1"

    if not api_key:
        raise RuntimeError("GLM_API_KEY is not configured")

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

    response = await _post_with_retry(url=url, headers=headers, payload=payload)
    if response.status_code >= 400:
        raise RuntimeError(f"Ilmu API error {response.status_code}: upstream unavailable")

    content = response.json()["choices"][0]["message"]["content"]
    parsed = _extract_json_object(content)
    return _normalize_response(parsed)
