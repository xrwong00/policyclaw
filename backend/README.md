# PolicyClaw Backend (MVP Slice 1)

Initial FastAPI implementation for core MVP flow:

- Health check
- Policy upload metadata intake (storage/extraction integration pending)
- 10-year premium simulation (optimistic/realistic/pessimistic)
- Keep/Switch/Downgrade/Dump heuristic verdict with citations and confidence

## Run

1. Install dependencies:

   ```powershell
   c:/Users/USER/Documents/policyclaw/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
   ```

2. Start API server:

   ```powershell
   c:/Users/USER/Documents/policyclaw/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --reload
   ```

3. API docs:

   - http://127.0.0.1:8000/docs

4. Backend base URL:

   - http://127.0.0.1:8000

## Implemented Endpoints

Core flow:
- `POST /api/extract-policy-profile` — extract `PolicyProfile` candidates from uploaded PDFs
- `POST /api/analyze` — full analysis → verdict + reasons + confidence + citations

ClawView (Wow Factor 1):
- `POST /v1/clawview` — clause-level risk highlights with PDF bounding boxes

FutureClaw simulator (Wow Factor 2):
- `POST /v1/simulate/affordability` — 1000-run Monte Carlo premium projection (3 scenario bands × 10 years)
- `POST /v1/simulate/life-event` — 4 life-event scenarios with GLM-generated EN + BM narratives

Legacy / scaffolded:
- `GET /health`
- `POST /v1/policies/upload`
- `POST /v1/simulate/premium`
- `POST /v1/verdict`
- `POST /v1/ai/*` — F1/F2/F4/F7/F9/F11 scaffolds (return mock data unless `GLM_API_KEY` is set)

Tests:

```powershell
pytest backend/tests/ -q
```

## Example Payload (`POST /v1/verdict`)

```json
{
  "insurer": "AIA",
  "plan_name": "A-Life Med 250",
  "policy_type": "medical",
  "annual_premium_myr": 2242,
  "coverage_limit_myr": 1200000,
  "effective_date": "2023-01-01",
  "age_now": 38,
  "projected_income_monthly_myr": 8500,
  "expected_income_growth_pct": 3
}
```
