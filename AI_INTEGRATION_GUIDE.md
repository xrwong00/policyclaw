# PolicyClaw AI Features — Integration Guide

This document describes how to use and configure the AI-powered features in PolicyClaw. The F1/F2/F7/F9/F11 entries below are the original scaffolded endpoints that still return mock data unless `GLM_API_KEY` is set; the Wow-Factor entries are the two fully-shipped demos.

> **Live feature status is tracked in `CLAUDE.md`.** This guide focuses on how to wire the `/v1/ai/*` scaffolds and demo flows.

## Features Overview

| Feature | ID | Status | Endpoint |
|---------|----|---------|---------:|
| **ClawView** (Wow Factor 1) | F4 | **Shipped** | `POST /v1/clawview` |
| **FutureClaw — Affordability** (Wow Factor 2) | F6 | **Shipped** | `POST /v1/simulate/affordability` |
| **FutureClaw — Life Event** (Wow Factor 2) | F6 | **Shipped** | `POST /v1/simulate/life-event` |
| Policy X-Ray | F1 | Scaffolded | `POST /v1/ai/policy-xray` |
| Overlap Map | F2 | Scaffolded | `POST /v1/ai/overlap-map` |
| BNM Rights Scanner | F4* | Scaffolded | `POST /v1/ai/bnm-rights-scanner` |
| Voice Policy Interrogation | F7 | Scaffolded | `POST /v1/ai/voice-interrogation` |
| Multi-lingual Explainer | F9 | Scaffolded | `GET /v1/ai/multilingual-explainer/{subject}` |
| Citation Vault + Confidence | F11 | Scaffolded | `GET /v1/ai/citations/{analysis_id}` |

*F4 is used in two places in the PRD — ClawView (the Wow Factor 1 clause-risk overlay) and the BNM Rights Scanner scaffold. They live behind different endpoints.

## Current State

All features are **production-ready scaffolds** with:

- ✅ TypeScript/Pydantic schemas for API contracts
- ✅ Backend routes with proper error handling
- ✅ Frontend React components with loading states
- ✅ Mock data that mimics real responses
- ✅ Environment-based configuration
- ✅ CSS styling and responsive design

**Currently, all features return mock data.** This is intentional — the system runs without an API key, uses realistic fallback responses, and is ready to be "turned on" when you have your Z.AI GLM API key.

## Running the System Now

### Backend (Mock Mode)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/docs` to see all available endpoints.

Check AI status: `GET http://127.0.0.1:8000/v1/ai/status` — should show `"mode": "Mock Data"`.

### Frontend

```bash
cd frontend
pnpm install
pnpm dev --port 3001
```

Visit `http://localhost:3001` to see the landing page with all components.

## Adding Your AI API Key

When you receive your **Z.AI GLM-4.6 API key**, follow these steps:

### 1. Create Backend `.env` File

In `backend/` directory, create a `.env` file (or copy from `.env.example`):

```bash
# backend/.env
GLM_API_KEY=your-z-ai-glm-api-key-here
GLM_API_BASE=https://open.bigmodel.cn/api/paas/v4
GLM_MODEL=glm-4-flash
DEBUG=false
```

**⚠️ Important:** Never commit `.env` to Git. It's already in `.gitignore`.

### 2. Restart Backend

```bash
# Backend will now load GLM_API_KEY from .env
uvicorn app.main:app --reload
```

Check AI status: `GET http://127.0.0.1:8000/v1/ai/status` — should now show `"mode": "GLM API"`.

### 3. Implement GLM Integration

The backend is ready for GLM integration. The template functions are in:

```
backend/app/services/ai_service.py
```

Each feature has a TODO marker where you'll add GLM calls:

```python
async def analyze_policy_xray(policy_input, policy_id):
    if config.is_mock_mode:
        return _mock_policy_xray(...)  # Current behavior

    # TODO: Call GLM API when key is available
    # return await _call_glm_policy_xray(...)
    raise NotImplementedError()
```

Replace the `TODO` sections with actual GLM calls. Example structure:

```python
async def _call_glm_policy_xray(policy_input, policy_id):
    """Call GLM to analyze a policy document."""
    from openai import AsyncOpenAI  # Use OpenAI SDK for Z.AI (compatible)
    
    client = AsyncOpenAI(
        api_key=config.api_key,
        base_url=config.api_base,
    )
    
    response = await client.chat.completions.create(
        model=config.model,
        messages=[
            {
                "role": "user",
                "content": f"Extract policy clauses for: {policy_input.plan_name}...",
            }
        ],
        temperature=0.7,
        response_format={"type": "json_object"},  # Use instructor for structured outputs
    )
    
    # Parse response and return PolicyXRayResponse
    ...
```

## API Endpoints Reference

### F1 — Policy X-Ray
```
POST /v1/ai/policy-xray
Content-Type: application/json

{
  "insurer": "AIA",
  "plan_name": "MyShield Pro",
  "policy_type": "medical",
  "annual_premium_myr": 1800,
  "coverage_limit_myr": 100000,
  "effective_date": "2023-01-15",
  "age_now": 38,
  "projected_income_monthly_myr": 8500,
  "expected_income_growth_pct": 3.0
}
```

**Response:** `PolicyXRayResponse` with extracted fields, key clauses, and confidence score.

### F2 — Overlap Map
```
POST /v1/ai/overlap-map
Content-Type: application/json

[
  { "insurer": "AIA", "plan_name": "MyShield Pro", ... },
  { "insurer": "Zurich", "plan_name": "Assure Health Plus", ... }
]
```

**Response:** `OverlapMapResponse` with detected overlap zones and savings estimate.

### F4 — BNM Rights Scanner
```
POST /v1/ai/bnm-rights-scanner
Content-Type: application/json

{
  "insurer": "AIA",
  "plan_name": "MyShield Pro",
  ...
}
```

**Response:** `BNMRightsScannerResponse` with applicable BNM rights and demand letters.

### F7 — Voice Policy Interrogation
```
POST /v1/ai/voice-interrogation
Content-Type: application/json

{
  "transcript": "What does my policy cover?",
  "language": "en",
  "policy_ids": []
}
```

**Response:** `VoiceInterrogationResponse` with answer and citations.

### F9 — Multi-lingual Explainer
```
GET /v1/ai/multilingual-explainer/takaful?target_language=bm
```

**Response:** `MultilingualExplanation` with native-quality text in 4 languages.

### F11 — Citation Vault
```
GET /v1/ai/citations/{analysis_id}?policy_count=2
```

**Response:** `CitationVaultResponse` with all citations and confidence metrics.

### AI Status
```
GET /v1/ai/status
```

**Response:**
```json
{
  "ai_enabled": false,  // or true if GLM_API_KEY is set
  "mode": "Mock Data",  // or "GLM API"
  "model": "N/A",       // or "glm-4-flash"
  "features": [...]
}
```

## Frontend Components

The original `frontend/app/components/AIFeatures.tsx` scaffolded-feature card deck has been removed; rebuild per-feature components as the scaffolded endpoints are lifted out of mock mode.

Live Wow-Factor components ship under `frontend/app/analyze/components/`:

- `ClawViewOverlay.tsx` + `PdfViewer.tsx` — F4 / Wow Factor 1 risk overlay on the policy PDF.
- `FutureClawSimulator.tsx` (parent toggle) + `AffordabilitySimulator.tsx` + `LifeEventSimulator.tsx` — F6 / Wow Factor 2 10-year Monte Carlo simulator.

These are self-contained client components using Recharts + Framer Motion; they fetch from the live backend routes listed in the Features Overview table.

## Mock Data Behavior

Currently, calling any endpoint returns realistic mock data that matches the full schema. Examples:

**Policy X-Ray mock:**
- 3 key clauses (including 2 "gotcha" clauses)
- 78.5% confidence score (MEDIUM band)
- Plain-language translations to BM and EN
- Page numbers for each clause

**Overlap Map mock:**
- 2 coverage zones (high + medium severity)
- Specific rupiah amounts for duplicate premiums
- 65% confidence score
- Consolidation recommendation text

**BNM Rights Scanner mock:**
- 2 applicable rights (one applied, one unapplied)
- Demand letter templates in EN and BM
- Specific BNM circular references
- 82% confidence score (HIGH band)

These mocks are intentional and production-ready. When you add the API key, replace the `_mock_*` functions with real GLM calls.

## Testing

### Test Policy X-Ray
```bash
curl -X POST http://127.0.0.1:8000/v1/ai/policy-xray \
  -H "Content-Type: application/json" \
  -d '{
    "insurer": "AIA",
    "plan_name": "MyShield Pro",
    "policy_type": "medical",
    "annual_premium_myr": 1800,
    "coverage_limit_myr": 100000,
    "effective_date": "2023-01-15",
    "age_now": 38,
    "projected_income_monthly_myr": 8500,
    "expected_income_growth_pct": 3.0
  }'
```

### Test AI Status
```bash
curl http://127.0.0.1:8000/v1/ai/status
```

## Troubleshooting

**Q: AI status shows "Mock Data" even after adding GLM_API_KEY**
- A: Make sure you restarted the backend after creating `.env`. The key is loaded at startup.

**Q: Getting 500 error from an AI endpoint**
- A: Check backend logs. Mock mode should never error. If you're in GLM mode, verify API key and endpoint are correct.

**Q: Frontend components don't load**
- A: Check browser console for network errors. Verify `NEXT_PUBLIC_API_BASE_URL` env var points to correct backend (default: `http://127.0.0.1:8000`).

**Q: How do I test GLM integration without the real key?**
- A: The current mocks are perfect for this. Build your frontend flows against mocks, then swap the backend to call GLM when the key arrives.

## Next Steps

1. **Today**: Run the system with mock data (no API key needed)
2. **When you get the Z.AI key**: Add it to `.env` in the backend
3. **Week 2**: Implement GLM calls by replacing `TODO` markers in `ai_service.py`
4. **Week 3**: Test each feature end-to-end with real GLM
5. **Week 4**: Polish and optimization

## File Structure

```
policyclaw/
├── backend/
│   ├── app/
│   │   ├── main.py                         # FastAPI app: CORS + include_router only
│   │   ├── api/                            # Route handlers split by concern
│   │   │   ├── health.py                   # /health
│   │   │   ├── analyze.py                  # /api/analyze + /api/extract-policy-profile
│   │   │   ├── clawview.py                 # /v1/clawview (F4 / Wow 1)
│   │   │   ├── futureclaw.py               # /v1/simulate/* (F6 / Wow 2)
│   │   │   └── legacy.py                   # /v1/ai/*, /v1/policies/upload, /v1/verdict
│   │   ├── core/
│   │   │   └── glm_client.py               # Single GLM entry point (env, config, retry)
│   │   ├── schemas/                        # Pydantic contracts split by domain
│   │   │   ├── common.py                   # Citation, ConfidenceBand, PolicyType, ...
│   │   │   ├── policy.py                   # PolicyInput, PolicyClause, ...
│   │   │   ├── analyze.py                  # AnalyzeResponse, HealthScore, Verdict, ...
│   │   │   ├── clawview.py                 # ClawView annotation shapes
│   │   │   ├── futureclaw.py               # FutureClaw sim shapes
│   │   │   └── legacy_ai.py                # /v1/ai/* F1/F2/F4/F7/F9/F11 shapes
│   │   └── services/
│   │       ├── ai_service.py               # GLM prompts + mock fallback for /v1/ai/*
│   │       ├── analyze_service.py          # /api/analyze orchestration
│   │       ├── profile_extraction_service.py
│   │       ├── clawview_service.py         # F4 / Wow 1
│   │       ├── futureclaw_narrative.py     # F6 / Wow 2 GLM narrative
│   │       ├── simulation.py               # F6 Monte Carlo + legacy premium projection
│   │       ├── pdf_parser.py               # PyMuPDF extraction
│   │       └── rag.py, verdict.py
│   ├── data/bnm_corpus/                    # BNM inflation + LIAM/PIAM/MTA cost citations
│   ├── tests/                              # pytest suite (run: pytest backend/tests/ -q)
│   └── .env.example                        # Template for .env (GLM_API_KEY lives here)
├── evals/                                  # JSON-driven GLM pipeline eval harness
└── frontend/
    └── app/
        ├── analyze/
        │   ├── AnalyzeWorkflow.tsx         # Main analyze page
        │   └── components/                 # ClawView + FutureClaw components
        ├── clawview-demo/page.tsx          # Standalone ClawView demo route
        └── globals.css
```

## Questions?

Refer to the PRD.md for detailed feature specifications and user stories for each AI feature.
