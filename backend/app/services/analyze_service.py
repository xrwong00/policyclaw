from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import httpx

from app.schemas import AnalyzeResponse
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


def _normalize_analyze_payload(parsed: dict) -> dict:
    """Coerce model output into schema-safe bounds without inventing new facts."""
    normalized = dict(parsed)

    reasons = normalized.get("summary_reasons")
    if isinstance(reasons, list):
        cleaned_reasons = [str(item).strip() for item in reasons if str(item).strip()]
        normalized["summary_reasons"] = cleaned_reasons[:6]
    else:
        normalized["summary_reasons"] = []

    citations = normalized.get("citations")
    if isinstance(citations, list):
        normalized["citations"] = citations[:12]
    else:
        normalized["citations"] = []

    if not normalized["summary_reasons"]:
        normalized["summary_reasons"] = ["Insufficient extraction confidence for detailed reasons."]

    if not normalized["citations"]:
        normalized["citations"] = [
            {
                "source": "Uploaded policy document",
                "page": 1,
                "excerpt": "No citation excerpt was returned by the model.",
            }
        ]

    return normalized


async def _post_with_retry(url: str, headers: dict[str, str], payload: dict) -> httpx.Response:
    retries = 3
    delay = 1.5
    last_error: Exception | None = None

    for attempt in range(retries):
        try:
            timeout = httpx.Timeout(90.0, connect=20.0)
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


async def run_ai_analysis(
    files: list[tuple[str, bytes]],
    profile: dict[str, str | float | int],
) -> AnalyzeResponse:
    """Parse PDFs, retrieve relevant chunks, and produce structured AI analysis."""
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
        "Analyze insurance policy and return verdict, projected savings, overlap detection, "
        "BNM rights detection, confidence score, summary reasons, and citations"
    )
    if profile:
        profile_pairs = [f"{key}: {value}" for key, value in profile.items() if value not in (None, "")]
        if profile_pairs:
            query += "\nProfile: " + "; ".join(profile_pairs)

    selected_chunks = retrieve_relevant_chunks(all_chunks, query=query, k=10)
    context = build_context(selected_chunks)

    schema_hint = {
        "verdict": "keep|downgrade|switch|dump",
        "projected_savings": "number >= 0",
        "overlap_detected": "boolean",
        "bnm_rights_detected": "boolean",
        "confidence_score": "number 0-100",
        "summary_reasons": ["string"],
        "citations": [
            {
                "source": "string",
                "page": "integer >= 1",
                "excerpt": "string",
            }
        ],
    }

    prompt_payload = {
        "profile": profile,
        "document_count": len(files),
        "context_chunk_count": len(selected_chunks),
    }

    url = f"{api_base.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are PolicyClaw's insurance analysis engine for Malaysia. "
                    "Use only provided context. Return strict JSON only."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Produce an analysis result using this exact schema shape: "
                    f"{json.dumps(schema_hint, ensure_ascii=True)}\n\n"
                    f"Input metadata: {json.dumps(prompt_payload, ensure_ascii=True)}\n\n"
                    "Context chunks:\n"
                    f"{context}"
                ),
            },
        ],
    }

    response = await _post_with_retry(url=url, headers=headers, payload=payload)
    if response.status_code >= 400:
        raise RuntimeError(f"Ilmu API error {response.status_code}: {response.text[:300]}")

    response_json = response.json()
    content = response_json["choices"][0]["message"]["content"]
    parsed = _normalize_analyze_payload(_extract_json_object(content))

    return AnalyzeResponse.model_validate(parsed)
