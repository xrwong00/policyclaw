"""PolicyClaw FastAPI entry point.

Route handlers live in `app.api.*` — this module only wires the app together:
  * create the `FastAPI` instance
  * install CORS for the local frontend origin
  * `include_router` each feature module

The concrete pipeline stages (Extract → Annotate → Score → Recommend) live in
`app.services.*` and all GLM plumbing flows through `app.core.glm_client`.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    analyze_router,
    clawview_router,
    futureclaw_router,
    health_router,
    legacy_router,
)

app = FastAPI(title="PolicyClaw Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:3001",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(analyze_router)
app.include_router(clawview_router)
app.include_router(futureclaw_router)
app.include_router(legacy_router)
