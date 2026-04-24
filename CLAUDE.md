# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**PolicyClaw** is an AI insurance decision copilot for Malaysians, built for **UMHackathon 2026 (Domain 2 — AI for Economic Empowerment & Decision Intelligence)**. It is a 24-hour solo-dev MVP. Users upload insurance policy PDFs; the system uses **Ilmu GLM (`ilmu-glm-5.1`)** to extract structured fields, annotate hidden risks directly on the PDF, score policy health, simulate 10 years of premiums and life events, and return a **Hold / Switch / Downgrade / Add Rider** verdict with citations.

The GLM centrality test matters: per the hackathon brief, if the LLM is removed the system must produce no meaningful insights. Keep Ilmu GLM in the reasoning path — don't replace GLM calls with pure heuristics.

See `README.md` for framing and **`PRD.md` (v2.1, 2026-04-24) for the authoritative spec**. Anytime scope, architecture, or feature priority is in question, the PRD is the source of truth.

## The two things being judged

1. **ClawView (Wow Factor 1)** — color-coded risk highlights (green/yellow/red) overlaid *on the actual policy PDF* using PyMuPDF bounding boxes + GLM annotation. Click a highlight → plain-language explanation + citation. This is the visual demo moment.
2. **FutureClaw (Wow Factor 2)** — interactive 10-year Monte Carlo simulator with two toggleable modes: **Affordability** (premium vs income trajectory) and **Life Event** (Cancer / Heart Attack / Disability / Death of primary earner). Math runs in numpy (no GLM in the slider loop); GLM only generates the narrative interpretation.

Don't erode either of these while refactoring — they're the differentiator.

## Repository layout

- `backend/` — FastAPI service. Entry: `backend/app/main.py`. Pipeline services in `backend/app/services/`:
  - `analyze_service.py` — orchestrates the full analysis flow
  - `profile_extraction_service.py` — auto-fills `PolicyProfile` fields from PDFs
  - `ai_service.py` — GLM API wrapper (falls back to mock responses when `GLM_API_KEY` is unset)
  - `clawview_service.py` — drives the ClawView (F4 / Wow 1) clause-risk overlay
  - `futureclaw_narrative.py` — single-GLM-call narrative batch for the FutureClaw (F6 / Wow 2) life-event simulator
  - `pdf_parser.py`, `rag.py`, `simulation.py`, `verdict.py`
  - Data contracts in `backend/app/schemas.py`. Cost/inflation corpus in `backend/data/bnm_corpus/`.
  - Unit tests in `backend/tests/` (run with `pytest backend/tests/ -q`).
- `frontend/` — Next.js 15 App Router (React 19, TypeScript). Main user flow in `frontend/app/analyze/`.
- `eval-harness/` — eval-driven-development scaffolding (see its `SKILL.md`).
- `scripts/` — setup helpers (`install-gstack.sh`).
- `.claude/rules/` — coding standards. Start with `common/development-workflow.md` and `common/agents.md`; language rules in `python/` and `typescript/`.
- Root-level docs: `README.md` (public framing), `PRD.md` (authoritative spec), `AI_INTEGRATION_GUIDE.md` (how to wire `/v1/ai/*` scaffolds + live Wow-Factor endpoints), `AI_SCAFFOLDING_SUMMARY.md` (historical record of the initial F1-F11 scaffolding).

## Tech stack

- **Backend:** Python 3.10+ (PRD targets 3.12), FastAPI, Pydantic v2, httpx, numpy. Currently pypdf 5.4.0 in `requirements.txt`; **PRD target is PyMuPDF (fitz)** because ClawView needs per-clause bounding boxes. If you're touching the PDF pipeline for ClawView, migrate to PyMuPDF rather than extending pypdf.
- **Frontend:** Next.js 15.3, React 19, TypeScript 5.8, ESLint 9. PRD target adds Tailwind + shadcn/ui + react-pdf-viewer + Recharts + Framer Motion + Zustand + TanStack Query — check `frontend/package.json` for what's actually installed before assuming.
- **LLM:** **Z.AI GLM via Ilmu** — actual defaults in `backend/app/services/{ai_service,analyze_service,profile_extraction_service}.py` are `GLM_API_BASE=https://api.ilmu.ai/v1` and `GLM_MODEL=ilmu-glm-5.1`. Env vars live in `backend/.env` (see `.env.example`): `GLM_API_KEY`, `GLM_API_BASE`, `GLM_MODEL`. `api.ilmu.ai` / `ilmu-glm-5.1` is an **authorized Z.AI endpoint** (confirmed with organizers), which satisfies the hackathon's mandatory-Z.AI rule — **do not migrate to `bigmodel.cn` or rename away from Ilmu.** `PRD.md` §1.4/§9.1 references to "Z.AI GLM-4.6 via bigmodel.cn" and `README.md` references to `glm-5.1` predate this confirmation; the code defaults are ground truth. The PRD specifies `instructor` for typed outputs — adopt it when wiring real GLM calls.
- **Database:** none in MVP. Supabase (Postgres + Auth + Storage + Realtime + pgvector) is the **ship target**, explicitly flagged in PRD §9.2 / §10.3 as *not MVP-gating*. MVP fallback is in-memory backend state + browser `localStorage`. Don't hard-require Supabase in any code path the demo depends on.

## Commands

Backend uses a venv at `backend/.venv/` — install and run from `backend/` with the venv activated:

```bash
cd backend
# First time only: python -m venv .venv
source .venv/Scripts/activate          # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload          # NOT `--app-dir backend` from inside backend/
# API: http://127.0.0.1:8000   Docs: http://127.0.0.1:8000/docs   Health: /health
```

Do **not** install requirements against the system Python — uvicorn imports from the venv's site-packages and will throw `ModuleNotFoundError` (e.g. `tenacity`) if deps go elsewhere. If running from the repo root instead, the equivalent is `backend/.venv/Scripts/python -m uvicorn app.main:app --app-dir backend --reload`.

Frontend:

```bash
cd frontend
npm install
npm run dev      # http://127.0.0.1:3000
npm run build
npm run lint
```

Pytest lives in `backend/tests/` and runs via `pytest backend/tests/ -q` (also enforced by CI). FutureClaw has 13 unit tests covering the Monte Carlo + life-event + confidence + narrative-mock paths. Extraction and recommendation tests are still the Hour 21-23 PRD target. If you add tests, follow `.claude/rules/common/testing.md`.

## Target architecture (per PRD §9.4) — 4 GLM calls per analysis

1. **Extract** — raw PDF text → structured `Policy` Pydantic model
2. **Annotate** — each clause → `{risk_level: green|yellow|red, explanation, clause_id}` (drives ClawView)
3. **Score** — policy + user profile → 4 sub-scores: Coverage Adequacy, Affordability, Premium Stability, Clarity & Trust (drives Health Score gauge)
4. **Recommend** — all above + simulation results → `Verdict + 3 Reasons + Confidence + MYR impact + Citations`

Total latency target: ~15s. Wrap each call in `tenacity` retry (3 attempts, exponential backoff, 30s per-call timeout). If the Annotate call fails, ClawView should degrade gracefully ("limited annotation available") without blocking the rest of the flow.

## Current endpoint surface

Production flow (keep these working):
- `POST /api/extract-policy-profile` — extract `PolicyProfile` candidates from uploaded PDFs
- `POST /api/analyze` — full analysis → verdict + reasons + confidence + citations
- `POST /v1/clawview` — ClawView (F4 / Wow 1) clause-level risk overlay
- `POST /v1/simulate/affordability` — FutureClaw (F6 / Wow 2) Monte Carlo premium projection
- `POST /v1/simulate/life-event` — FutureClaw life-event scenarios with GLM narratives

Legacy / scaffolded under `/v1/...` — `/v1/simulate/premium`, `/v1/verdict`, `/v1/policies/upload`, and the `/v1/ai/*` family (F1/F2/F4/F7/F9/F11) — some `/v1/ai/*` endpoints return mock data. Check `backend/app/main.py` before assuming an endpoint is live. CORS is configured in `main.py` for the local frontend origin.

## Product principles to preserve

From PRD §4 — these shape judgment calls when specs are ambiguous:
- **Explain or don't say it** — every AI claim needs a citation. No opaque outputs.
- **Decision support, not advice** — present options + projected impact; user decides. Disclaimer on every recommendation screen.
- **Confidence calibrated** — every output carries a 0-100% confidence score. Low confidence → suggest human advisor, don't hide uncertainty.
- **Malaysian-first** — BM + EN only for MVP. Real BNM / LIAM / PIAM / MTA data, not generic placeholders.

## Hackathon judging

Preliminary-round rubric from `docs/hackathon/judging-criteria.pdf`. Full reference PDFs (PRD/SAD/QATD templates + rubric) live in `docs/hackathon/`. Let these weights inform scope and polish decisions — not every trade-off is equal.

**Eligibility (hard rule):** Z.AI GLM is mandatory; any other reasoning model is disqualifying. `api.ilmu.ai` / `ilmu-glm-5.1` is an authorized Z.AI endpoint and satisfies this — see the LLM bullet under Tech stack.

**Scoring weights** (sorted by weight, total = 100%):

| Weight | Aspect | Category |
|---|---|---|
| 12% | Implementation Quality | Engineering Execution |
| 10% | Originality, Innovation & Value Realization | Product Vision |
| 8%  | Target Users & User Stories | Product Vision |
| 8%  | Code Modularity & Structure | Engineering Execution |
| 7%  | System Logic & Architecture | System Architecture |
| 7%  | Technical Feasibility & Workflow Integration | System Architecture |
| 7%  | Feature Prioritization & MVP Scope | Product Vision |
| 6%  | System Schema & Design | System Architecture |
| 6%  | Technical Walkthrough | Pitch & Prototype |
| 5%  | Problem Definition & Purpose | Product Vision |
| 5%  | Version Control & Repository Management | Engineering Execution |
| 5%  | Risk Anticipation & Mitigation | QA & Test Planning |
| 5%  | Testing Strategy, Coverage & Impact | QA & Test Planning |
| 5%  | UI/UX & Usability | Pitch & Prototype |
| 4%  | Presentation Delivery & Deck Quality | Pitch & Prototype |

**Deliverable docs (not yet drafted):** PRD, SAD, QATD — templates in `docs/hackathon/{prd,sad,qatd}-sample.pdf`. Together these directly drive ~16% of the score (System Schema 6% + Risk 5% + Testing 5%) and indirectly back another ~30% (architecture, feasibility, user stories are judged partly from the docs, not only from code). Don't skip them.

**Judgment rules derived from the weights:**

1. **Polish > breadth on the core flow.** Implementation Quality (12%) + Technical Walkthrough (6%) reward a solid ClawView + FutureClaw demo over a wider shaky one. When in doubt, cut scope, don't cut polish.
2. **Every new feature needs a user-story justification.** Target Users & User Stories (8%) is scored independently from "does it work." If a feature can't be mapped to a stated user story, it's probably scope creep.
3. **Write the deliverable docs, don't hope code speaks for itself.** ~16% is judged from SAD/QATD craft. Architecture diagrams, risk matrices, and CI/CD thresholds go in the docs — not the README.

## gstack

gstack is installed once per machine and provides the slash commands the user relies on (`/browse`, `/review`, `/ship`, `/investigate`, `/qa`, `/codex`, etc.). Use `/browse` — never `mcp__claude-in-chrome__*` — for web browsing.

Setup (once per machine):

```bash
bash scripts/install-gstack.sh
```

Full skill list: `/office-hours`, `/plan-ceo-review`, `/plan-eng-review`, `/plan-design-review`, `/design-consultation`, `/design-shotgun`, `/design-html`, `/review`, `/ship`, `/land-and-deploy`, `/canary`, `/benchmark`, `/browse`, `/connect-chrome`, `/qa`, `/qa-only`, `/design-review`, `/setup-browser-cookies`, `/setup-deploy`, `/retro`, `/investigate`, `/document-release`, `/codex`, `/cso`, `/autoplan`, `/plan-devex-review`, `/devex-review`, `/careful`, `/freeze`, `/guard`, `/unfreeze`, `/gstack-upgrade`, `/learn`.
