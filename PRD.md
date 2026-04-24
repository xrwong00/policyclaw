# PolicyClaw — Product Requirements Document

> **Claw through complexity. Decide with confidence.**

| | |
|---|---|
| **Version** | 2.2 — 2026-04-24 (condensed for execution) |
| **Status** | Active — Hackathon MVP |
| **Event** | UMHackathon 2026 — Domain 2 (AI for Economic Empowerment & Decision Intelligence) |
| **Build window** | 24 hours, solo developer |

---

## 1. What It Is

PolicyClaw is an AI insurance decision copilot for Malaysians. Users upload policy PDFs; the system extracts structured fields, annotates hidden risks directly on the PDF, scores policy health, simulates 10 years of premiums and life events, and returns a **Hold / Switch / Downgrade / Add Rider** verdict with citations — in Bahasa Malaysia or English.

**GLM centrality (brief requirement).** Remove Ilmu GLM and the system produces zero meaningful insights: plain-language extraction, ClawView annotations, Health Score sub-scores, recommendations, and multilingual output all break. Only the Monte Carlo numbers survive — without narrative interpretation. Keep GLM in the reasoning path; do not substitute heuristics.

---

## 2. Problem (Compressed)

- **2024 repricing crisis** — 9% of Malaysian MHIT policyholders saw premium hikes >40% (BNM 2024 Annual Report). Cumulative claims inflation 56% over 2021–2023.
- **BNM 10% cap window** — interim measures cap annual hikes at 10% through **31 December 2026**. Most policyholders don't know they qualify.
- **30 million underinsured Malaysians** (EY Malaysia 2024). Root cause is decision paralysis, not affordability.

**Primary user:** Aisyah, 38, M40 KL marketing manager, 2–4 policies, just received a repricing notice with 30 days to decide. Secondary: Uncle Lim (58, multi-language), Siti (32, takaful/Shariah-conscious).

---

## 3. Principles

- **P1. User-aligned** — no commission from insurers.
- **P2. Explain or don't say it** — every AI claim cites a source clause + page.
- **P3. Decision support, not advice** — user decides; disclaimer on every recommendation screen.
- **P4. Confidence calibrated** — 0–100% on every output; low confidence → suggest human advisor.
- **P5. Malaysian-first** — BM + EN only for MVP; real BNM / LIAM / PIAM / MTA data.
- **Anti-principles** — no selling user data, no auto-purchase/cancel, no binding legal advice, no dark patterns.

---

## 4. Core E2E Flow

**Step 1 — Upload.** Drag-and-drop 1–3 PDFs (≤10 MB each). PyMuPDF extracts text + bounding boxes. Preview rendered via react-pdf-viewer.

**Step 2 — Profile intake.** Single-screen form: age, income bracket, dependents, primary concern, language. Stored in `localStorage`.

**Step 3 — Policy X-Ray (GLM Extract).** Insurer, plan, premium, coverage, riders, exclusions, waiting periods, co-pay. Side-by-side: PDF page ↔ extracted fields with source-page tags.

**Step 4 — ClawView (GLM Annotate).** Color-coded highlights overlaid on the original PDF — 🟢 standard / 🟡 worth knowing / 🔴 hidden risk. Click → plain-language explanation + citation. **Wow Factor 1.**

**Step 5 — Policy Health Score.** Single 0–100 gauge with 4 sub-scores (0–25 each): Coverage Adequacy, Affordability, Premium Stability, Clarity & Trust.

**Step 6 — FutureClaw.** Interactive 10-year Monte Carlo with two toggleable modes. **Wow Factor 2.**
- **Affordability** — premium trajectory vs income under inflation sliders; flags year premium > 10% of income.
- **Life Event** — Cancer / Heart Attack / Disability / Death: covered vs out-of-pocket vs family impact.

**Step 7 — Recommendation (GLM Recommend).** Per-policy verdict: 🟢 HOLD / 🟡 DOWNGRADE / 🔴 SWITCH / ⚫ ADD RIDER. Includes 3 reasons (with citations), confidence %, 10-year MYR impact, and explicit trade-offs.

**Step 8 — Action Summary.** Downloadable card: verdict, top 3 reasons, top 3 concrete actions, disclaimer. PDF export via jsPDF.

---

## 5. Feature Spec

| ID | Feature | Priority | Hours | Acceptance |
|---|---|---|---|---|
| F1 | PDF Upload + Extraction | P0 | 2 | Extraction ≤3s for 5-page PDF |
| F2 | Profile Intake | P0 | 1 | Form completes in ≤30s |
| F3 | Policy X-Ray (plain language) | P0 | 2 | ≥90% field accuracy on 3 demo policies |
| F4 | ClawView (Wow 1) | P0 | 6 | See §6 |
| F5 | Policy Health Score | P0 | 1.5 | Sample policies score 30–85 (calibrated, not all 90+) |
| F6 | FutureClaw (Wow 2) | P0 | 4 | See §7 |
| F7 | Recommendation Engine | P0 | 2 | Verdict consistent across 3 reruns of identical input |
| F8 | Action Summary + PDF download | P0 | 1.5 | PDF generates <2s, professional layout |
| F9 | Multilingual (BM/EN) | P1 | 1 | All AI outputs work in both languages; JSON dict for UI strings (no i18next) |
| F10 | Polish + animations | P0 | 3 | Framer Motion transitions on key screens |

Priority: P0 = ship-or-die, P1 = ship-if-time. Total ~24h.

---

## 6. Wow Factor 1 — ClawView (Hidden Risk X-Ray)

**What.** Color-coded risk highlights overlaid *on the actual uploaded PDF* — not a side summary.

**How (technical).**
1. PyMuPDF extracts text **with bounding-box coordinates** per clause.
2. GLM returns `{ risk_level: green|yellow|red, plain_explanation, clause_id }` per clause.
3. Frontend: react-pdf-viewer + custom SVG highlight layer positioned from bounding boxes.
4. Click handler → tooltip with plain-language explanation + "why this matters."

**Functional requirements.** Highlight at minimum 5 risk types per policy: premium repricing clauses, pre-existing condition exclusions, waiting-period traps, co-payment requirements, sub-limit caps. Works on text-native PDFs; best-effort on scanned.

**Acceptance criteria.**
- [ ] ≥8 highlights generated per demo policy
- [ ] Color coding accurate (red ≠ random)
- [ ] Highlights align with PDF text (no offset bugs)
- [ ] Tooltip explanations ≤80 words each
- [ ] BM and EN both work

---

## 7. Wow Factor 2 — FutureClaw (10-Year Decision Simulator)

**What.** Two interactive Monte Carlo modes across 10 years.

- **Affordability** — sliders for medical inflation (3–20%) and income growth (0–8%). Output: 10-year line chart with 3 scenario bands, cumulative MYR, "danger zone" flag when premium > 10% of income.
- **Life Event** — pick Cancer / Heart Attack / Disability / Death. Output: covered / co-pay / out-of-pocket bars, months of household income at risk, "compare alternative" toggle against a switched policy.

**How (technical).** 1000 Monte Carlo runs via numpy/scipy — pure Python, **no GLM in the slider loop** (instant updates). GLM only generates the narrative interpretation. BNM medical inflation data (2014–2024) baked in as historical anchor.

**Acceptance criteria.**
- [ ] Slider drag updates chart smoothly (60 FPS, <100ms)
- [ ] All scenarios use cited Malaysian cost data
- [ ] Narrative regenerates on scenario change
- [ ] Both modes accessible via toggle (not separate pages)
- [ ] Charts downloadable as PNG

---

## 8. Technical Architecture

### 8.1 Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui |
| Backend | Python 3.12 + FastAPI + Pydantic v2 + SQLModel |
| AI | Ilmu GLM (`ilmu-glm-5.1` on `api.ilmu.ai/v1`) + `instructor` for typed outputs |
| PDF | PyMuPDF (fitz) parsing, react-pdf-viewer display |
| Charts | Recharts |
| Simulation | numpy + scipy.stats |
| Database (ship target) | Supabase (Postgres + pgvector + Auth + Storage + Realtime) |
| State (frontend) | Zustand + TanStack Query |
| Animation | Framer Motion |

> Env defaults in code (`backend/app/services/{ai_service,analyze_service,profile_extraction_service}.py`): `GLM_API_BASE=https://api.ilmu.ai/v1`, `GLM_MODEL=ilmu-glm-5.1`. These override any older "Z.AI GLM-4.6" references in earlier docs.

### 8.2 Supabase: Ship Target vs MVP Fallback

**Ship target** — Supabase unlocks managed Postgres + pgvector (RAG over BNM corpus), magic-link Auth, private bucket for PDFs (signed URLs), Realtime (agents stream results live during demo), and Row Level Security for PDPA. Setup ~15–20 min.

**Current implementation state (April 2026).** The repo has no database wired up. For the 24-hour build, the acceptable MVP fallback is **ephemeral in-memory backend state + browser `localStorage`**. Supabase is the ship target if time permits. Requirements that depend on Supabase (Auth, RLS, PDPA deletion endpoint, Realtime streaming) are **not MVP-gating** (see §9.3).

**Demo safety.** Cache demo runs to a local JSON file. If wifi drops, the app reads from cache and the demo still works.

### 8.3 Architecture Diagram

```
┌──────────────────────────────────────────────────────┐
│  Browser (localhost:3000)                            │
│  Next.js 15 + shadcn/ui + react-pdf + Recharts       │
└──────────────────────┬───────────────────────────────┘
                       │ HTTPS / JSON
                       ▼
┌──────────────────────────────────────────────────────┐
│  FastAPI (localhost:8000)                            │
│  Routes: /api/extract-policy-profile /api/analyze    │
└──────┬───────────────┬────────────────┬──────────────┘
       │               │                │
       ▼               ▼                ▼
┌────────────┐ ┌──────────────┐ ┌───────────────────┐
│ Ingestion  │ │ GLM Pipeline │ │ Simulation Engine │
│ PyMuPDF    │ │ Ilmu GLM-5.1 │ │ numpy + scipy     │
│ + Extract  │ │ + instructor │ │ Monte Carlo       │
└──────┬─────┘ └───────┬──────┘ └─────────┬─────────┘
       │               │                  │
       ▼               ▼                  ▼
┌──────────────────────────────────────────────────────┐
│  Supabase (ship target; in-memory for MVP)           │
│  Postgres + pgvector + Auth + Storage + Realtime     │
└──────────────────────────────────────────────────────┘
```

### 8.4 GLM Pipeline — 4 Sequential Calls per Analysis

1. **Extract** — raw PDF text → structured `Policy` Pydantic model.
2. **Annotate** — each clause → `{risk_level, plain_explanation, clause_id}` (drives ClawView).
3. **Score** — policy + user profile → 4 sub-scores (drives Health Score gauge).
4. **Recommend** — all above + simulation results → verdict + 3 reasons + confidence + MYR impact + citations.

Each call uses `instructor` for typed output. Total latency target: **~15s**.

### 8.5 Current Endpoint Surface

Production flow (keep working): `POST /api/extract-policy-profile`, `POST /api/analyze`. Legacy `/v1/ai/*` endpoints return mock data — check `backend/app/main.py` before assuming any `/v1/*` endpoint is live.

### 8.6 Repository Structure

```
policyclaw/
├── README.md
├── PRD.md                   # This document
├── backend/
│   ├── requirements.txt
│   ├── .env.example         # GLM_API_KEY, GLM_API_BASE, GLM_MODEL
│   ├── app/
│   │   ├── main.py          # FastAPI entry + CORS
│   │   ├── schemas.py       # Pydantic API schemas
│   │   └── services/
│   │       ├── analyze_service.py            # Orchestrates full analysis
│   │       ├── profile_extraction_service.py # Auto-fills PolicyProfile
│   │       ├── ai_service.py                 # GLM wrapper + mock fallback
│   │       ├── pdf_parser.py
│   │       ├── rag.py
│   │       ├── simulation.py
│   │       └── verdict.py
│   ├── tests/               # pytest: extraction, simulation, recommendation
│   └── data/
│       ├── bnm_corpus/      # Static BNM data
│       └── demo_cache/      # Cached GLM responses (offline demo fallback)
└── frontend/
    ├── package.json
    └── app/
        ├── layout.tsx
        ├── page.tsx
        └── analyze/              # Main user flow
            ├── components/
            │   ├── PolicyUploader.tsx
            │   ├── PdfViewer.tsx
            │   ├── ClawViewOverlay.tsx       # Wow 1
            │   ├── HealthScoreGauge.tsx
            │   ├── AffordabilitySimulator.tsx # Wow 2a
            │   ├── LifeEventSimulator.tsx     # Wow 2b
            │   ├── VerdictCard.tsx
            │   ├── ActionSummary.tsx
            │   └── LanguageToggle.tsx
            └── lib/
                ├── api.ts
                ├── store.ts     # Zustand
                └── i18n.ts      # JSON dict
```

---

## 9. Non-Functional Requirements

### 9.1 Performance Targets

| Metric | Target |
|---|---|
| PDF upload → preview rendered | ≤2s |
| Full analysis (4 GLM calls) | ≤15s |
| Simulation slider update | 60 FPS |
| ClawView highlight render | ≤500ms after analysis |
| Action Plan PDF generation | ≤2s |

### 9.2 Reliability

- All GLM calls wrapped in `tenacity` retry: **3 attempts, exponential backoff, 30s per-call timeout.**
- Graceful degradation: if **Annotate** fails, ClawView shows "limited annotation available" — rest of flow continues.
- Persist AI outputs to Supabase before UI consumes (enables Realtime replay). MVP: in-memory cache.

### 9.3 Data & Privacy

- **MVP fallback:** session-only state via backend in-memory store + browser `localStorage`. No persistent PII across sessions. Demo flow works without Supabase.
- **Ship target:** Supabase Auth (magic-link), private bucket with signed URLs (1h expiry), RLS enforcing `auth.uid() = user_id`, single-endpoint PDPA deletion.
- No PII in logs (UUIDs only).
- "Not financial advice" disclaimer on every recommendation screen.

### 9.4 Accessibility & Browser Support

- WCAG 2.1 AA target; color-blind-safe risk palette; keyboard navigation; ARIA labels.
- Chrome 120+, Safari 17+, Firefox 121+, Edge 120+. Responsive (tested on iPhone 14 viewport).

---

## 10. 24-Hour Build Plan

### Hour 0–2 — Foundations
- Next.js + FastAPI scaffolds running.
- Supabase setup is **ship target only** — if it takes >30 min, defer and proceed with in-memory fallback.
- GLM client tested with hello-world.
- 3 sample PDFs prepared (anonymized).

### Hour 2–6 — Backend Core
- `/upload` + PyMuPDF text extraction with bounding boxes.
- **GLM Call 1 (Extract)** working via `instructor` + Pydantic.
- Schemas defined. BNM corpus seeded (pgvector if Supabase on, else in-memory).

### Hour 6–10 — ClawView (Wow 1)
- **GLM Call 2 (Annotate)** returns per-clause risk levels.
- react-pdf-viewer + SVG bounding-box overlay.
- Tooltip with plain-language explanation.
- **Checkpoint: ClawView visibly working on 1 policy.**

### Hour 10–14 — Health Score + Recommendation
- **GLM Call 3 (Score)** → 4 sub-scores.
- Circular gauge (Recharts or custom SVG).
- **GLM Call 4 (Recommend)** → verdict + reasons + confidence.
- Verdict card UI.

### Hour 14–18 — FutureClaw (Wow 2)
- Monte Carlo via numpy.
- Affordability chart + sliders.
- Life Event mode, 4 scenarios (cut from 6).
- GLM narrative interpretation.
- **Checkpoint: both wow factors demonstrable.**

### Hour 18–21 — Polish
- Action Summary + PDF download.
- BM/EN toggle.
- Framer Motion transitions, loading states, error handling.

### Hour 21–23 — Testing & Docs
- 3–4 pytest units (extraction, simulation, recommendation).
- README screenshots; ARCHITECTURE.md (1 page).

### Hour 23–24 — Demo Prep
- Run demo flow 3× for muscle memory.
- Record 4-min screen capture as backup.

### Critical Cut Points

- **If at Hour 12 core flow isn't end-to-end working:** cut F9 (EN only), cut Life Event mode (Affordability only), cut PDF download (screen-only summary).
- **If at Hour 18 ClawView isn't aligned:** fall back to side-pane risk list with page references (loses the "wow" but ships).

---

## 11. Out of Scope

- Real-time insurer API integration (none exist publicly)
- Actual policy purchase/cancellation (regulatory)
- Claims filing assistance
- SME / business insurance
- Mobile native apps (responsive web only)
- Voice interface (too risky in 24h)
- Mandarin / Tamil / Hokkien (BM + EN only)
- Takaful Shariah deep features (stays generic)
- Production frontend deployment (localhost for demo; Supabase is hosted)

---

**End of PRD.** Decision-support software, not licensed financial advice.
