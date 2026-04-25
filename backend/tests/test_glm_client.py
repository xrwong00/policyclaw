"""Unit tests for `app.core.glm_client._adapt_payload_for_provider`.

This helper sits on every production LLM call and silently transforms the
payload for OpenAI gpt-5 / o-series reasoning models (strip `temperature` /
`top_p`, default `reasoning_effort`). Catching a regression here is critical —
a bad transform means every analyze / clawview / futureclaw call breaks.
"""

from __future__ import annotations

import pytest

from app.core.glm_client import _adapt_payload_for_provider


@pytest.mark.unit
def test_passthrough_for_non_reasoning_model() -> None:
    payload = {"model": "gpt-4o-mini", "temperature": 0.2, "top_p": 0.9}
    assert _adapt_payload_for_provider(payload) is payload


@pytest.mark.unit
def test_strips_temperature_and_top_p_for_gpt5_family() -> None:
    payload = {"model": "gpt-5-mini", "temperature": 0.2, "top_p": 0.9, "messages": []}
    adapted = _adapt_payload_for_provider(payload)
    assert "temperature" not in adapted
    assert "top_p" not in adapted
    assert adapted["messages"] == []
    # Original payload must not be mutated.
    assert "temperature" in payload


@pytest.mark.unit
def test_injects_default_reasoning_effort_low() -> None:
    payload = {"model": "gpt-5-mini", "messages": []}
    adapted = _adapt_payload_for_provider(payload)
    assert adapted["reasoning_effort"] == "low"


@pytest.mark.unit
def test_preserves_caller_set_reasoning_effort() -> None:
    payload = {"model": "gpt-5", "reasoning_effort": "high", "messages": []}
    adapted = _adapt_payload_for_provider(payload)
    assert adapted["reasoning_effort"] == "high"


@pytest.mark.unit
@pytest.mark.parametrize("model", ["gpt-5", "gpt-5-mini", "gpt-5-nano", "o1-mini", "o3", "o3-mini"])
def test_reasoning_prefixes_all_trigger_adaptation(model: str) -> None:
    payload = {"model": model, "temperature": 0.5}
    adapted = _adapt_payload_for_provider(payload)
    assert "temperature" not in adapted
    assert adapted["reasoning_effort"] == "low"
