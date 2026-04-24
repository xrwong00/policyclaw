"""Core infrastructure — the single seam between PolicyClaw and the GLM provider.

Keep this package provider-agnostic: feature-specific prompts and schemas live
in `app.services.*`, not here. If we ever swap Ilmu for another Z.AI endpoint,
only `core.glm_client` changes.
"""

from app.core.glm_client import (
    AIServiceConfig,
    GLMClient,
    confidence_band_from_score,
    config,
    extract_json_from_content,
    load_local_env,
    post_glm_with_retry,
)

__all__ = [
    "AIServiceConfig",
    "GLMClient",
    "confidence_band_from_score",
    "config",
    "extract_json_from_content",
    "load_local_env",
    "post_glm_with_retry",
]
