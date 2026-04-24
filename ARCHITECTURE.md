# Architecture

PolicyClaw is a two-tier app: Next.js 15 frontend talking to a FastAPI backend
that orchestrates **four GLM calls** against an authorized Z.AI endpoint
(`api.ilmu.ai/v1`, model `ilmu-glm-5.1`). This document is the 3-minute read
for engineers and judges. For product scope see [`PRD.md`](PRD.md); for
deeper system context see [`SAD.md`](SAD.md); for QA strategy see
[`QATD.md`](QATD.md).

---

## 1. System diagram

```mermaid
flowchart LR
    U["User<br/>(Malaysian policyholder)"]
    subgraph FE["Next.js 15 (frontend/)"]
        Upload["/analyze upload wizard/"]
        Viewer["ClawView<br/>(PDF + risk overlay)"]
        Future["FutureClaw<br/>(Monte Carlo UI)"]
    end
    subgraph BE["FastAPI (backend/)"]
        API["api/ routers"]
        SVC["services/<br/>(analyze · clawview · futureclaw · ...)"]
        CORE["core/glm_client.py<br/>(single GLM seam)"]
        SCHEMA["schemas/<br/>(Pydantic v2 contracts)"]
    end
    ILMU[("Ilmu GLM<br/>ilmu-glm-5.1")]
    BNM[("backend/data/<br/>bnm_corpus")]

    U --> Upload
    Upload -->|multipart PDF| API
    API --> SVC
    SVC -->|"Extract · Annotate ·<br/>Score · Recommend"| CORE
    CORE -->|streamed JSON| ILMU
    SVC --> BNM
    API -->|AnalyzeResponse| Viewer
    API -->|ClawViewResponse| Viewer
    API -->|LifeEvent / Affordability| Future
    SCHEMA -.validates.- API
    SCHEMA -.validates.- SVC
```

Key property: **every GLM request in the system passes through
`backend/app/core/glm_client.py`.** Swapping providers or adjusting retry
behavior is a one-file change.

---

## 2. The four-call GLM pipeline

`/api/analyze` runs the first three calls sequentially. The fourth
(`Annotate` for ClawView) is served by `/v1/clawview` and fired by the
frontend in parallel with user review of the verdict, so the perceived
end-to-end latency target of **≤15s** is achievable.

| Stage        | Call         | Endpoint               | Temp | Output                                          | Fallback                         |
|--------------|--------------|------------------------|------|-------------------------------------------------|----------------------------------|
| 1. Extract   | `analyze_policy_xray`    | `/api/analyze` (internal) | 0.2  | `PolicyXRayResponse` — typed clauses, gotchas   | `_mock_policy_xray` (deterministic) |
| 2. Annotate  | `annotate_policy`        | `/v1/clawview`            | 0.2  | `ClawViewResponse` — per-clause risk + bboxes   | heuristic keyword match          |
| 3. Score     | `analyze_health_score`   | `/api/analyze` (internal) | 0.2  | `HealthScore` — 4 sub-scores, EN+BM narrative   | `_heuristic_health_score`        |
| 4. Recommend | `analyze_policy_verdict` | `/api/analyze` (internal) | 0.1  | `PolicyVerdict` — Keep/Switch/Dump + reasons    | `_heuristic_policy_verdict`      |

Each call is wrapped in a streamed POST with 3-attempt exponential-backoff
retry (see `core.glm_client.post_glm_with_retry`) and a per-call
`demo_cache` read-through so identical inputs yield identical outputs
(F7 verdict-consistency requirement).

### Sequence view

```mermaid
sequenceDiagram
    actor U as User
    participant FE as Next.js
    participant BE as FastAPI
    participant GLM as Ilmu GLM
    participant C as demo_cache

    U->>FE: Upload PDF + profile
    FE->>BE: POST /api/extract-policy-profile
    BE-->>FE: detected candidates

    U->>FE: Click Analyze
    FE->>BE: POST /api/analyze

    BE->>C: extract_key?
    alt cache miss
        BE->>GLM: Extract (~4s)
        BE->>C: put
    end
    BE->>C: score_key?
    alt cache miss
        BE->>GLM: Score (~3s)
        BE->>C: put
    end
    BE->>C: recommend_key?
    alt cache miss
        BE->>GLM: Recommend (~4s, T=0.1)
        BE->>C: put
    end
    BE-->>FE: AnalyzeResponse

    par ClawView fires in parallel
        FE->>BE: POST /v1/clawview
        BE->>GLM: Annotate (~4s)
        BE-->>FE: ClawViewResponse
    and user reads
        U->>FE: verdict + health + simulators
    end
```

---

## 3. LLM as a service layer

The core design rule: **feature code never talks to the GLM HTTP endpoint
directly.** It calls a thin module in `app.core.glm_client`:

```text
backend/app/core/glm_client.py
├── load_local_env()              # loads backend/.env idempotently
├── AIServiceConfig               # resolves GLM_API_KEY / GLM_API_BASE / GLM_MODEL
├── config: AIServiceConfig       # process-wide singleton
├── confidence_band_from_score()  # shared scorer → HIGH / MEDIUM / LOW
├── extract_json_from_content()   # tolerates ```json fences
├── post_glm_with_retry()         # streamed POST w/ 3-attempt backoff
└── GLMClient                     # optional object handle (chat_url, headers, complete_json)
```

Why this matters:

1. **Single point of change** — if Ilmu moves endpoints, rotates auth, or the
   hackathon organizers approve a new Z.AI model, one file updates.
2. **Testable seam** — tests swap `ai_service.config = AIServiceConfig()`
   after setting env vars (see `tests/test_orchestrator.py`), and every
   feature path respects the change.
3. **Mock mode is free** — when `GLM_API_KEY` is absent, `config.is_mock_mode`
   is true and every service falls back to its deterministic mock. The demo
   flow runs end-to-end without a live key.
4. **Feature prompts stay with the feature** — ClawView's prompt lives in
   `services/clawview_service.py`, the verdict prompt in
   `services/ai_service.py`. The client doesn't grow a god-method.

---

## 4. Dependency map

```mermaid
flowchart TD
    FE["frontend/<br/>Next.js 15 · React 19 · Tailwind<br/>react-pdf-viewer · Recharts"]
    API["backend/app/api/<br/>analyze · clawview · futureclaw · legacy · health"]
    SVC["backend/app/services/<br/>analyze · profile_extraction ·<br/>clawview · futureclaw_narrative ·<br/>simulation · rag · verdict · pdf_parser"]
    CORE["backend/app/core/<br/>glm_client.py"]
    SCHEMA["backend/app/schemas/<br/>common · policy · analyze ·<br/>clawview · futureclaw · legacy_ai"]
    EXT["External: pypdf · PyMuPDF · numpy ·<br/>httpx · tenacity · instructor"]
    ILMU[("Ilmu GLM")]
    BNM[("backend/data/bnm_corpus/")]

    FE -->|HTTP| API
    API --> SVC
    API --> SCHEMA
    SVC --> CORE
    SVC --> SCHEMA
    SVC --> EXT
    SVC --> BNM
    CORE --> EXT
    CORE --> ILMU
```

The arrow direction is strict: `api → services → core`. `schemas` is
imported by all three but imports nothing from them, so it stays acyclic.

---

## 5. What lives where (quick tour)

| Path                                   | Responsibility                                          |
|----------------------------------------|---------------------------------------------------------|
| `backend/app/main.py`                  | FastAPI app instance + CORS + `include_router` calls   |
| `backend/app/api/`                     | HTTP surface; one module per feature concern           |
| `backend/app/services/`                | Business logic; owns GLM prompts and fallbacks         |
| `backend/app/core/glm_client.py`       | The only place that opens an `httpx.AsyncClient` to Ilmu |
| `backend/app/schemas/`                 | Pydantic v2 request/response contracts                  |
| `backend/data/bnm_corpus/`             | Static BNM / LIAM / PIAM / MTA cost + rights corpus    |
| `backend/tests/`                       | 33 pytest tests (unit + orchestrator + verdict consistency) |
| `evals/`                               | JSON-driven pass/fail harness for the 4 GLM stages     |
| `frontend/app/analyze/`                | Upload wizard + results UI                              |
| `docs/erd.md`                          | Mermaid ERD of the Pydantic data model                  |

---

## 6. Further reading

- [`PRD.md`](PRD.md) — product requirements, scope, NFRs (authoritative spec)
- [`SAD.md`](SAD.md) — system architecture document (deeper than this file)
- [`QATD.md`](QATD.md) — quality assurance & test design
- [`AI_INTEGRATION_GUIDE.md`](AI_INTEGRATION_GUIDE.md) — how to wire real GLM
  responses into the scaffolded `/v1/ai/*` family
- [`docs/erd.md`](docs/erd.md) — entity-relationship diagram of the data model
- [`evals/README.md`](evals/README.md) — how to run the GLM eval harness
