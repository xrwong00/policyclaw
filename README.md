# PolicyClaw

Claw back what your insurer will not tell you.

PolicyClaw is an AI-powered insurance decision intelligence app for Malaysian policyholders. It helps users understand policy documents, detect overlap, project premium impact, and make a Keep/Switch/Downgrade/Dump decision with citations and confidence.

This repository follows the product direction in [PRD.md](PRD.md).

## Why PolicyClaw

Malaysia policyholders face complex policy language, repricing pressure, and low visibility into rights and overlap. PolicyClaw is built as decision support, not automation:

- Interpret structured and unstructured insurance data
- Provide context-aware recommendations
- Explain outputs with citations and confidence
- Support multilingual user understanding

## Current Build Status

Implemented in this codebase:

- Core MVP flow
- Policy upload metadata intake
- Premium simulation and verdict engine
- AI feature scaffolding with mock and real-mode switching
- Frontend UI for upload, analysis, and AI feature cards

AI-heavy features are scaffolded and return realistic mock responses by default. When `GLM_API_KEY` is configured, the architecture is ready for real GLM integration points in the backend service layer.

## Repository Structure

- [PRD.md](PRD.md): Product requirements document
- [AI_INTEGRATION_GUIDE.md](AI_INTEGRATION_GUIDE.md): AI feature integration guide
- [AI_SCAFFOLDING_SUMMARY.md](AI_SCAFFOLDING_SUMMARY.md): Scaffolding summary
- [backend](backend): FastAPI backend
- [frontend](frontend): Next.js frontend


## User Workflow

1. **Upload Policy PDF(s):**
	- Drag and drop or select one or more insurance policy PDFs in Step 1.
	- PolicyClaw auto-extracts key fields (insurer, plan, coverage, etc.) using real AI (GLM-5.1) if configured, or mock extraction if not.
	- If multiple policies are detected, select the correct one from the dropdown.

2. **Review and Confirm Fields:**
	- Step 2 auto-populates detected fields (editable if not detected).
	- "Monthly Income" is required for analysis ("Income Growth" is no longer present).
	- Confirm or edit any field as needed.

3. **Analyze Policy:**
	- The "Analyze Policy" button is now centered below the Riders/Add-ons field for clarity.
	- Click to run real AI analysis (if GLM API is configured) or mock analysis (if not).
	- Results include a Keep/Switch/Downgrade/Dump verdict, projected savings, overlap/rights detection, summary reasons, and citations with page numbers.

## Quickstart (Windows PowerShell)

### 1. Install backend dependencies

```powershell
c:/Users/USER/Documents/policyclaw/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
```

### 2. Run backend

```powershell
c:/Users/USER/Documents/policyclaw/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --reload
```


Backend URLs:
- API base: http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs

### 3. Install frontend dependencies

```powershell
cd frontend
npm install
copy .env.local.example .env.local
```

### 4. Run frontend

```powershell
npm run dev
```

Open:

- http://127.0.0.1:3000

If port 3000 is occupied:

```powershell
npm run dev -- --port 3001
```

## Environment Configuration

Backend environment template is available at [backend/.env.example](backend/.env.example).

Key variables:

- `GLM_API_KEY=`
- `GLM_API_BASE=https://open.bigmodel.cn/api/paas/v4`
- `GLM_MODEL=glm-4-flash`
- `DEBUG=false`

When `GLM_API_KEY` is empty, the backend runs in mock mode for AI endpoints.


## API Endpoints

### Core endpoints
- `GET /health`
- `POST /v1/policies/upload` (legacy)
- `POST /v1/simulate/premium` (legacy)
- `POST /v1/verdict` (legacy)

### Real AI endpoints (current UI uses these)
- `POST /api/extract-policy-profile` — Extracts policy fields from uploaded PDF(s) using GLM-5.1 (or mock if not configured). Returns one or more detected policy profiles.
- `POST /api/analyze` — Runs full policy analysis on the selected/extracted profile and PDF(s). Returns verdict, savings, overlap, rights, summary reasons, and citations.

### AI endpoints (legacy/scaffolded)
- `POST /v1/ai/policy-xray`
- `POST /v1/ai/overlap-map`
- `POST /v1/ai/bnm-rights-scanner`
- `POST /v1/ai/voice-interrogation`
- `GET /v1/ai/multilingual-explainer/{subject}`
- `GET /v1/ai/citations/{analysis_id}`
- `GET /v1/ai/status`


## UI/UX Notes

- The "Analyze Policy" button is now centered below the Riders/Add-ons field in Step 2 for improved clarity and accessibility.
- The "Income Growth" field has been removed; only "Monthly Income" is required for analysis.
- All fields are auto-filled from PDF extraction when possible, but remain editable.

## Product Scope Alignment

This project is aligned to the PRD focus areas:

- F1 Policy X-Ray
- F2 Overlap Map
- F3 Premium Crystal Ball
- F4 BNM Rights Scanner
- F5 Keep-Switch-Dump Verdict
- F7 Voice Interrogation
- F9 Multi-lingual Explainer
- F11 Citation Vault and confidence

For detailed feature specs and acceptance criteria, see [PRD.md](PRD.md).

## Notes for Judges and Reviewers

- This is a hackathon prototype optimized for clarity and demonstrability
- AI outputs are schema-validated and confidence-scored
- Recommendations are decision support outputs, not licensed financial advice

## Disclaimer

PolicyClaw is a decision-support prototype and not a licensed financial advisor. Users remain responsible for final financial decisions.
