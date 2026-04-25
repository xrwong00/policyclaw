"""Single LLM entry point — every chat-completions call flows through this module.

Default provider: OpenAI `gpt-5-mini` via `https://api.openai.com/v1`.
(Originally wired for Ilmu/Z.AI GLM; the file name is preserved for now.)

Responsibilities:
- Load `backend/.env` into `os.environ` on first import.
- Expose `AIServiceConfig` (api_key / api_base / model) and a singleton `config`.
- Provide the streaming-POST retry loop that gateway-tolerant callers depend on.
- Normalize JSON extraction from mixed-markdown model responses.

Feature-specific prompts, schemas, and mock paths live in `app.services.*`
(e.g. `ai_service.py`, `clawview_service.py`) — this file stays
provider-agnostic so swapping the LLM boundary is one file.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import httpx

from app.schemas import ConfidenceBand


def load_local_env() -> None:
    """Load `backend/.env` into `os.environ` if present.

    Values already set in the environment win — this only fills gaps. Safe to
    call multiple times (idempotent).
    """
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


load_local_env()


class AIServiceConfig:
    """Resolved LLM endpoint config (OpenAI-compatible chat completions).

    Construct a fresh instance after monkey-patching environment variables —
    tests do this via `ai_service.config = AIServiceConfig()`.
    """

    def __init__(self) -> None:
        self.api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
        self.api_base: str = os.getenv(
            "OPENAI_API_BASE", "https://api.openai.com/v1"
        ).strip()
        self.model: str = (
            os.getenv("OPENAI_MODEL", "gpt-5-mini").strip() or "gpt-5-mini"
        )
        self.is_mock_mode: bool = not self.api_key

    @property
    def enabled(self) -> bool:
        return not self.is_mock_mode


config = AIServiceConfig()


def confidence_band_from_score(score: float) -> ConfidenceBand:
    if score >= 80.0:
        return ConfidenceBand.HIGH
    if score >= 60.0:
        return ConfidenceBand.MEDIUM
    return ConfidenceBand.LOW


def extract_json_from_content(content: str) -> dict:
    """Extract a JSON object from a model response, tolerating ```json fences."""
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model response does not contain a JSON object")

    return json.loads(text[start : end + 1])


_REASONING_MODEL_PREFIXES = ("gpt-5", "o1", "o3")


def _adapt_payload_for_provider(payload: dict) -> dict:
    """OpenAI gpt-5 / o-series reasoning models reject custom temperature/top_p
    and accept reasoning_effort instead. Strip the former, default the latter.
    """
    model = str(payload.get("model", ""))
    if not model.startswith(_REASONING_MODEL_PREFIXES):
        return payload
    adapted = {k: v for k, v in payload.items() if k not in ("temperature", "top_p")}
    adapted.setdefault("reasoning_effort", "low")
    return adapted


async def post_glm_with_retry(
    url: str,
    headers: dict[str, str],
    payload: dict,
    *,
    attempts: int = 3,
    initial_backoff_s: float = 1.5,
    read_timeout_s: float = 120.0,
    connect_timeout_s: float = 20.0,
) -> str:
    """POST to the LLM with SSE streaming; concat `delta.content` chunks and return.

    Streaming is required for long reasoning calls; retries exponentially on
    transport-level errors.
    """
    streaming_payload = _adapt_payload_for_provider({**payload, "stream": True})
    backoff = initial_backoff_s
    last_exc: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            timeout = httpx.Timeout(read_timeout_s, connect=connect_timeout_s)
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST", url, headers=headers, json=streaming_payload
                ) as response:
                    if response.status_code >= 400:
                        body = await response.aread()
                        raise RuntimeError(
                            f"GLM API error {response.status_code}: "
                            f"{body[:400].decode(errors='replace')}"
                        )
                    parts: list[str] = []
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        chunk = line[6:].strip()
                        if chunk == "[DONE]":
                            break
                        try:
                            data = json.loads(chunk)
                            choices = data.get("choices")
                            if not choices:
                                continue
                            delta = choices[0]["delta"].get("content") or ""
                            parts.append(delta)
                        except (json.JSONDecodeError, KeyError):
                            pass
                    return "".join(parts)
        except (
            httpx.ReadTimeout,
            httpx.ConnectTimeout,
            httpx.RemoteProtocolError,
        ) as exc:
            last_exc = exc
            if attempt < attempts:
                await asyncio.sleep(backoff)
                backoff *= 2
                continue
            break

    if last_exc is not None:
        raise last_exc
    raise RuntimeError("GLM request failed without a captured exception")


class GLMClient:
    """Thin object wrapper for callers that prefer a handle over module funcs."""

    def __init__(self, cfg: AIServiceConfig | None = None) -> None:
        self._cfg = cfg or config

    @property
    def config(self) -> AIServiceConfig:
        return self._cfg

    @property
    def chat_url(self) -> str:
        return f"{self._cfg.api_base.rstrip('/')}/chat/completions"

    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._cfg.api_key}",
            "Content-Type": "application/json",
        }

    async def complete_json(self, payload: dict) -> dict:
        """POST a chat-completions payload and return the parsed JSON content."""
        if not self._cfg.api_key:
            raise RuntimeError("OPENAI_API_KEY is missing")
        content = await post_glm_with_retry(
            url=self.chat_url, headers=self.headers(), payload=payload
        )
        return extract_json_from_content(content)
