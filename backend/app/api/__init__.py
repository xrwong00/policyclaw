"""FastAPI routers — one module per concern.

`main.py` composes these into the single `FastAPI` app. Splitting by concern
keeps route handlers near their request/response schemas and makes it obvious
which endpoints are production-critical (`analyze`, `clawview`, `futureclaw`)
vs. legacy/scaffolded (`legacy`).
"""

from app.api.analyze import router as analyze_router
from app.api.clawview import router as clawview_router
from app.api.futureclaw import router as futureclaw_router
from app.api.health import router as health_router
from app.api.legacy import router as legacy_router

__all__ = [
    "analyze_router",
    "clawview_router",
    "futureclaw_router",
    "health_router",
    "legacy_router",
]
