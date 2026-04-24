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
  - `pdf_parser.py`, `rag.py`, `simulation.py`, `verdict.py`
  - Data contracts in `backend/app/schemas.py`.
- `frontend/` — Next.js 15 App Router (React 19, TypeScript). Main user flow in `frontend/app/analyze/`.
- `eval-harness/` — eval-driven-development scaffolding (see its `SKILL.md`).
- `scripts/` — setup helpers (`install-gstack.sh`).
- `.claude/rules/` — coding standards. Start with `common/development-workflow.md` and `common/agents.md`; language rules in `python/` and `typescript/`.

## Tech stack

- **Backend:** Python 3.10+ (PRD targets 3.12), FastAPI, Pydantic v2, httpx, numpy. Currently pypdf 5.4.0 in `requirements.txt`; **PRD target is PyMuPDF (fitz)** because ClawView needs per-clause bounding boxes. If you're touching the PDF pipeline for ClawView, migrate to PyMuPDF rather than extending pypdf.
- **Frontend:** Next.js 15.3, React 19, TypeScript 5.8, ESLint 9. PRD target adds Tailwind + shadcn/ui + react-pdf-viewer + Recharts + Framer Motion + Zustand + TanStack Query — check `frontend/package.json` for what's actually installed before assuming.
- **LLM:** **Ilmu GLM** — actual defaults in `backend/app/services/{ai_service,analyze_service,profile_extraction_service}.py` are `GLM_API_BASE=https://api.ilmu.ai/v1` and `GLM_MODEL=ilmu-glm-5.1`. Env vars live in `backend/.env` (see `.env.example`): `GLM_API_KEY`, `GLM_API_BASE`, `GLM_MODEL`. Note: `PRD.md` §1.4/§9.1 references "Z.AI GLM-4.6 via bigmodel.cn" and `README.md` lists `glm-5.1` — those are aspirational/outdated. **Treat the code defaults (`ilmu-glm-5.1` on `api.ilmu.ai`) as ground truth** until someone updates docs. The PRD specifies `instructor` for typed outputs — adopt it when wiring real GLM calls.
- **Database:** none in MVP. Supabase (Postgres + Auth + Storage + Realtime + pgvector) is the **ship target**, explicitly flagged in PRD §9.2 / §10.3 as *not MVP-gating*. MVP fallback is in-memory backend state + browser `localStorage`. Don't hard-require Supabase in any code path the demo depends on.

## Commands

Backend (from repo root):

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn app.main:app --app-dir backend --reload
# API: http://127.0.0.1:8000   Docs: http://127.0.0.1:8000/docs   Health: /health
```

Frontend:

```bash
cd frontend
npm install
npm run dev      # http://127.0.0.1:3000
npm run build
npm run lint
```

No automated test suite is wired up yet. Hour 21-23 of the PRD plan adds 3-4 pytest unit tests (extraction, simulation, recommendation). If you add tests, follow `.claude/rules/common/testing.md`.

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

Legacy / scaffolded under `/v1/...` — some `/v1/ai/*` endpoints return mock data. Check `backend/app/main.py` before assuming an endpoint is live. CORS is configured in `main.py` for the local frontend origin.

## Product principles to preserve

From PRD §4 — these shape judgment calls when specs are ambiguous:
- **Explain or don't say it** — every AI claim needs a citation. No opaque outputs.
- **Decision support, not advice** — present options + projected impact; user decides. Disclaimer on every recommendation screen.
- **Confidence calibrated** — every output carries a 0-100% confidence score. Low confidence → suggest human advisor, don't hide uncertainty.
- **Malaysian-first** — BM + EN only for MVP. Real BNM / LIAM / PIAM / MTA data, not generic placeholders.

## gstack

gstack is installed once per machine and provides the slash commands the user relies on (`/browse`, `/review`, `/ship`, `/investigate`, `/qa`, `/codex`, etc.). Use `/browse` — never `mcp__claude-in-chrome__*` — for web browsing.

Setup (once per machine):

```bash
bash scripts/install-gstack.sh
```

Full skill list: `/office-hours`, `/plan-ceo-review`, `/plan-eng-review`, `/plan-design-review`, `/design-consultation`, `/design-shotgun`, `/design-html`, `/review`, `/ship`, `/land-and-deploy`, `/canary`, `/benchmark`, `/browse`, `/connect-chrome`, `/qa`, `/qa-only`, `/design-review`, `/setup-browser-cookies`, `/setup-deploy`, `/retro`, `/investigate`, `/document-release`, `/codex`, `/cso`, `/autoplan`, `/plan-devex-review`, `/devex-review`, `/careful`, `/freeze`, `/guard`, `/unfreeze`, `/gstack-upgrade`, `/learn`.
