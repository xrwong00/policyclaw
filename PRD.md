# PolicyClaw — Product Requirements Document

> **Claw through complexity. Decide with confidence.**
>
> An AI-powered insurance decision copilot for Malaysians — built for UMHackathon 2026, Domain 2.

| | |
|---|---|
| **Version** | 2.1 (Merged — Untitled + PRD v1 reconciliation) |
| **Status** | Active — Hackathon MVP |
| **Event** | UMHackathon 2026 — AI for Economic Empowerment & Decision Intelligence |
| **Build window** | 24 hours, solo developer + 1 teammate (pitch/slides) |
| **Last updated** | 2026-04-24 |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Definition](#2-problem-definition)
3. [Target Users & Personas](#3-target-users--personas)
4. [Product Vision & Principles](#4-product-vision--principles)
5. [Core E2E Flow](#5-core-e2e-flow)
6. [Feature Specification](#6-feature-specification)
7. [Wow Factor 1 — ClawView](#7-wow-factor-1--clawview)
8. [Wow Factor 2 — FutureClaw](#8-wow-factor-2--futureclaw)
9. [Technical Architecture](#9-technical-architecture)
10. [Non-Functional Requirements](#10-non-functional-requirements)
11. [Success Metrics & Quantifiable Impact](#11-success-metrics--quantifiable-impact)
12. [Risks & Mitigations](#12-risks--mitigations)
13. [24-Hour Build Plan](#13-24-hour-build-plan)
14. [Out of Scope](#14-out-of-scope)
15. [Why This Wins](#15-why-this-wins)
16. [Appendix](#16-appendix)

---

## 1. Executive Summary

### 1.1 The One-Liner

PolicyClaw is an AI-powered insurance decision copilot that reads your policy PDFs, visually highlights hidden risks directly on the document, simulates 10 years of premium and life-event scenarios, and recommends whether to **hold, switch, downgrade, or add a rider** — all in plain Bahasa Malaysia or English.

### 1.2 The 30-Second Pitch

> *"In 2024, 9% of Malaysians saw their medical insurance premiums spike over 40% in one year. Many cancelled their coverage — including a cancer patient. The reason? Insurance is the most important financial decision Malaysians make, but they make it with the least information. PolicyClaw is a GLM-powered decision intelligence system that reads your actual policy, claws out the hidden risks, simulates your next 10 years, and tells you exactly what to do — with citations, in your language. It turns 30 million underinsured Malaysians into informed decision-makers."*

### 1.3 Why This Matters Now

Three converging Malaysian realities make 2026 the perfect window:

1. **The Repricing Crisis** — 2024 medical premiums jumped 40-70% for millions; cumulative 56% claims inflation 2021-2023.
2. **The BNM Intervention** — premium hikes capped at 10% annually through end-2026, but most policyholders don't know they qualify.
3. **The Information Asymmetry** — 30 million Malaysians underinsured. The root cause isn't affordability; it's decision paralysis.

### 1.4 The GLM-Powered Solution

PolicyClaw deploys Z.AI's GLM-4.6 to:

- **Interpret** structured policy data and unstructured legal prose
- **Reason** across multiple policies, user profile, and regulatory context
- **Recommend** specific actions with projected ringgit impact
- **Explain** every decision with traceable citations

**Without GLM, the system produces zero insights.** The LLM is not a chat layer — it is the reasoning brain.

### 1.5 Hackathon Brief Alignment

| Brief Requirement | PolicyClaw Delivery |
|---|---|
| Interpretation of structured + unstructured data | PDF policies (unstructured) + BNM regulations (structured) + user profile |
| Context-aware reasoning | Multi-step GLM pipeline consuming shared context |
| Actionable recommendations | Hold / Switch / Downgrade / Add Rider verdict per policy |
| Explainable decisions | Every claim cites source clause + page number |
| Decision-making, not automation | System informs; user decides |
| Quantifiable impact | Projected MYR savings + protection gap |
| Clear target users | Malaysian M40 policyholders, age 28-55 |
| Basic validation | 3 sample policies + 3 persona scenarios |

---

## 2. Problem Definition

### 2.1 The Macro Problem

Malaysia has one of the most information-asymmetric insurance markets in ASEAN. Policies are sold verbally, written in legalese, priced opaquely, and managed via paper notices. When prices shift — as they did dramatically in 2024 — consumers have no tools to evaluate options in the compressed 30-day window insurers provide.

### 2.2 Evidence Base

| Finding | Source | Why It Matters |
|---|---|---|
| 30 million Malaysians are underinsured | EY Malaysia (2024) | Total addressable problem |
| 85% of SMEs have inadequate coverage | EY Malaysia (2024) | B2B expansion |
| Medical claims inflation: 56% cumulative 2021-2023 | LIAM/PIAM/MTA joint statement (Nov 2024) | Driver of premium hikes |
| 9% of policyholders saw >40% premium hikes in 2024 | Bank Negara Malaysia 2024 Annual Report | Acute pain point |
| 60% of middle-income Malaysians view insurance as "wasteful if unused" | Institute for Health Systems Research (2025) | Decision paralysis evidence |
| BNM interim measures end 31 December 2026 | BNM Press Release (Dec 2024) | Urgency window |

### 2.3 The "Aisyah Moment" — Specific User Pain

Aisyah, 38, marketing manager in KL, opens a letter from her insurer:

> *"Dear Policyholder, your medical insurance premium will increase from RM1,679 to RM2,242 (34% increase) effective next month..."*

She has three policies across two insurers, accumulated over 8 years of agent relationships. The letter is 6 pages of legalese. She has 30 days to decide. Three questions she can't answer:

1. **Should I switch, downgrade, or pay?** — No tool exists.
2. **Am I getting what I pay for?** — Her policies overlap, but she doesn't know by how much.
3. **What are my BNM rights?** — Buried in news articles she never read.

Her current options: call an agent (biased), call a friend (uninformed), or ignore (most common). PolicyClaw is the fourth option.

### 2.4 Why Existing Solutions Fail

| Solution | Why It Fails |
|---|---|
| Price comparison sites (PolicyStreet, RinggitPlus) | Only help at purchase time; useless post-purchase |
| Insurance agents | Commission-motivated; can't advise against own products |
| Insurer apps (MyZurich, AIA+) | Loyal to insurer; won't suggest switching |
| Financial advisors | Inaccessible to B40/M40; priced for high-net-worth |
| ChatGPT / generic LLMs | No policy context, no BNM knowledge, no simulation |
| Status quo (ignore it) | Results in 30M underinsured Malaysians |

PolicyClaw occupies a genuinely empty quadrant: **policyholder-aligned, technically competent, always available, and Malaysian-native.**

---

## 3. Target Users & Personas

### 3.1 Primary Persona — "Aisyah the Reluctant Optimizer"

| Attribute | Value |
|---|---|
| Age | 38 |
| Income | RM 8,500/month (M40) |
| Location | Klang Valley |
| Family | Married, 2 children |
| Policies owned | 2-4 (medical + life + critical illness) |
| Tech comfort | High (Grab, Shopee, DuitNow daily) |
| Languages | BM (primary), English |
| Trigger event | Received premium repricing notice |
| Goal | Right decision within 30-day window |
| Fear | Losing coverage just before a health crisis |

### 3.2 Secondary Persona — "Uncle Lim the Skeptic"

| Attribute | Value |
|---|---|
| Age | 58 |
| Income | RM 5,200/month (semi-retired) |
| Family | Empty-nester |
| Policies | 3-5 (accumulated over 30 years) |
| Languages | Mandarin, Bahasa, English |
| Trigger | Adult child asks "Pa, what happens if you get sick?" |
| Fear | Too old to switch, stuck in expensive plans |

### 3.3 Tertiary Persona — "Siti the Shariah-Conscious Planner"

| Attribute | Value |
|---|---|
| Age | 32 |
| Income | RM 6,000/month |
| Family | Newlywed, expecting first child |
| Policies | 1 takaful family plan |
| Trigger | Pregnancy — planning family protection |
| Fear | Sold a plan that doesn't truly meet Shariah principles |

### 3.4 Epic User Stories

- **E1.** As Aisyah, I want to upload my insurance policies and get a clear verdict in under 60 seconds, so I can decide before my deadline.
- **E2.** As Aisyah, I want to see hidden risk clauses highlighted on my actual policy PDF, so I can trust what the AI is telling me.
- **E3.** As Aisyah, I want to see what my premiums will cost when I'm 48, 58, and 68, so I can plan whether to switch now.
- **E4.** As Aisyah, I want to simulate "what if I get cancer?" so I can feel whether my coverage is enough — not just read about it.
- **E5.** As Aisyah, I want a clear next-best-action with confidence and reasons, so I'm not left interpreting raw data.
- **E6.** As Uncle Lim, I want explanations in BM/Mandarin, so I don't depend on my daughter to translate.

---

## 4. Product Vision & Principles

### 4.1 Vision

To become the trusted decision copilot for every insurance policyholder in Malaysia — starting with the 30 million who are currently underinsured and overwhelmed.

### 4.2 Core Principles

- **P1. User-Aligned, Always.** PolicyClaw earns no commission from insurers.
- **P2. Explain or Don't Say It.** No opaque outputs. If GLM can't cite, the claim doesn't appear.
- **P3. Decision Support, Not Advice.** We present options with projected impact. The user decides. We are not a licensed financial advisor.
- **P4. Malaysian-First.** Built from the ground up for Malaysian regulations, languages, culture, and insurance products.
- **P5. Respect the Gravity.** Insurance decisions affect families for decades. No dark patterns.
- **P6. Confidence Calibrated.** Every output has a confidence score. Low confidence triggers human-advisor referral.

### 4.3 Anti-Principles

- ❌ Will not sell user data to insurers
- ❌ Will not auto-purchase or auto-cancel policies
- ❌ Will not give binding legal/financial advice
- ❌ Will not replicate aggressive insurance agent sales patterns

---

## 5. Core E2E Flow

The complete user journey from upload to decision. **This is what gets demoed live.**

### Step 1 — Upload Policy

User drops one or more policy PDFs (up to 3 for the demo).

- Drag-and-drop zone with progress indicator
- PDF preview appears immediately on the right pane
- Backend extracts text via PyMuPDF in real-time

**Output:** Policy preview rendered, extraction job queued.

### Step 2 — Quick Profile Intake

A single screen with 5 fields (no multi-step form):

- Age
- Monthly income (range slider: <3k / 3-5k / 5-8k / 8-12k / 12k+)
- Number of dependents
- Primary concern (affordability / coverage / family protection)
- Preferred language (BM / EN)

**Output:** User context saved to session.

### Step 3 — Policy X-Ray (GLM Extraction)

GLM extracts structured fields and translates legalese into plain language.

- Insurer name, plan name, annual premium, coverage limit
- Riders, exclusions, waiting periods, co-payment terms
- Side-by-side view: original PDF page (left) vs extracted plain-language fields (right)
- Each field has a "source page" tag

**Output:** Structured policy profile + plain-language summary.

### Step 4 — ClawView Hidden Risk Scan ⚡ Wow Factor 1

System overlays color-coded highlights directly on the original policy PDF:

- 🟢 **Green** — Standard, expected clause
- 🟡 **Yellow** — Worth knowing (waiting periods, mild restrictions)
- 🔴 **Red** — Hidden risk (repricing triggers, broad exclusions, co-pay traps)

User taps any highlight → plain-language explanation pops up with citation.

**Output:** Annotated PDF with risk overlays.

### Step 5 — Policy Health Score

A single 0-100 score with sub-dimension breakdown:

- **Coverage Adequacy** (0-25)
- **Affordability** (0-25)
- **Premium Stability** (0-25)
- **Clarity & Trust** (0-25)

Visualized as a circular gauge with sub-scores.

**Output:** One number Aisyah can show her husband.

### Step 6 — FutureClaw Scenario Simulator ⚡ Wow Factor 2

Interactive Monte Carlo simulation across 10 years.

**Two simulation modes (toggleable):**

- **Affordability Mode:** Premium trajectory under inflation (5% / 10% / 15% slider). Shows the year your premium exceeds 10% of projected income.
- **Life Event Mode:** Pick a scenario — Stage-2 Cancer / Heart Attack / Permanent Disability / Death of Primary Earner. See covered amount, out-of-pocket gap, and family impact.

**Output:** Interactive chart + narrative interpretation generated by GLM.

### Step 7 — Recommendation Engine

GLM synthesizes all prior steps into a verdict per policy:

- 🟢 **HOLD** — Keep this policy as-is
- 🟡 **DOWNGRADE** — Reduce coverage to lower premium burden
- 🔴 **SWITCH** — Move to a better-fit alternative
- ⚫ **ADD RIDER** — Current policy is solid but missing critical coverage

Each verdict includes:

- 3 strongest reasons (with citations)
- Confidence score (0-100%)
- Projected MYR impact over 10 years
- Trade-offs explicitly stated

### Step 8 — Action Summary

Final card the user can screenshot or download:

- **Verdict** — One-line bold conclusion
- **Top 3 reasons** — With clickable citations
- **Top 3 actions** — Concrete next steps (e.g., "Email AIA requesting BNM 10% cap")
- **Disclaimer** — "Decision support, not regulated financial advice"
- **Download as PDF** button

---

## 6. Feature Specification

### 6.1 Feature Prioritization (24-Hour Reality Check)

| ID | Feature | Priority | Build Hours | Risk |
|---|---|---|---|---|
| F1 | PDF Upload + Extraction | P0 | 2 | Low |
| F2 | Profile Intake | P0 | 1 | Low |
| F3 | Policy X-Ray (Plain Language) | P0 | 2 | Low |
| F4 | ClawView (Wow Factor 1) | P0 | 6 | Medium |
| F5 | Policy Health Score | P0 | 1.5 | Low |
| F6 | FutureClaw Simulator (Wow Factor 2) | P0 | 4 | Low |
| F7 | Recommendation Engine | P0 | 2 | Low |
| F8 | Action Summary + Download | P0 | 1.5 | Low |
| F9 | Multilingual (BM/EN) | P1 | 1 | Low |
| F10 | Polish + animations | P0 | 3 | Low |

**Total: ~24 hours.** Tight but doable. Notice we cut Voice (too risky), Takaful Showdown (too niche for demo), and Regret Simulator (folded into Recommendation reasoning).

Priority legend: P0 = ship-or-die, P1 = ship-if-time.

---

### 6.2 F1 — PDF Upload + Extraction

- Accept PDF up to 10 MB, up to 3 policies
- PyMuPDF extracts raw text + page coordinates
- Preview rendered via react-pdf in side pane
- **Acceptance:** Extraction completes in ≤3s for 5-page PDF

### 6.3 F2 — Profile Intake

- Single-screen form, 5 fields, no multi-step
- Stored in localStorage (no auth needed for demo)
- **Acceptance:** Form completes in ≤30 seconds

### 6.4 F3 — Policy X-Ray (Plain Language)

- GLM extracts structured fields via `instructor` library
- Each field shows source page number
- Side-by-side view: original PDF / extracted fields
- **Acceptance:** ≥90% extraction accuracy on 3 demo policies

### 6.5 F5 — Policy Health Score

- 4 sub-scores computed by deterministic rules + GLM judgments
- Single 0-100 number visualized as gauge
- Click each sub-dimension to see how it was calculated
- **Acceptance:** Score calibrated — sample policies score 30-85, not all 90+

### 6.6 F7 — Recommendation Engine

- GLM Strategist agent consumes all prior outputs
- Returns verdict + 3 reasons + confidence + MYR impact
- **Acceptance:** Verdict consistent across 3 reruns of identical input

### 6.7 F8 — Action Summary + Download

- Final card with verdict, reasons, actions, disclaimer
- "Download Action Plan PDF" button (uses jsPDF)
- **Acceptance:** PDF generates in <2 seconds, looks professional

### 6.8 F9 — Multilingual (BM/EN)

- Toggle in header
- GLM regenerates outputs in selected language
- UI strings via simple JSON dictionary (no i18next library — too heavy for 24h)
- **Acceptance:** All AI outputs work in both languages

---

## 7. Wow Factor 1 — ClawView (Hidden Risk X-Ray)

### 7.1 What It Does

Visual AI layer that overlays color-coded risk highlights **directly on the user's uploaded policy PDF**. This is not a side summary — it's annotation on the actual document.

### 7.2 Why It Wins

- **Tangible trust** — User sees AI working *on their document*, not generating tangentially
- **Demo gold** — Judges see policy → highlights → tap → explanation flow
- **Visceral** — Red highlights on legalese feel revelatory
- **Defensible** — Each highlight has a source citation (anti-hallucination by design)

### 7.3 How It Works (Technical)

1. PyMuPDF extracts text **with bounding box coordinates** for every clause
2. GLM analyzes each clause and returns: `risk_level: green|yellow|red`, `plain_explanation: str`, `clause_id: str`
3. Frontend renders PDF via react-pdf-viewer with custom highlight layer
4. SVG overlay positions highlights using bounding boxes from step 1
5. Click handler shows tooltip with plain-language explanation

### 7.4 Functional Requirements

- Highlight at minimum 5 risk types per policy:
  - Premium repricing clauses
  - Pre-existing condition exclusions
  - Waiting period traps
  - Co-payment requirements
  - Sub-limit caps
- Each highlight is tappable
- Tooltip shows: risk level, plain explanation, "why this matters" context
- Works on both text-native and (best-effort) scanned PDFs

### 7.5 Acceptance Criteria

- [ ] At least 8 highlights generated per demo policy
- [ ] Color coding accurate (red highlights truly are high-risk, not random)
- [ ] Highlights align with PDF text (no offset bugs)
- [ ] Tooltip explanations under 80 words each
- [ ] BM and EN versions both work

### 7.6 Demo Script

> *"This is Aisyah's actual AIA policy. Watch what happens when PolicyClaw scans it..."*
>
> **[Click ClawView]** — Page lights up with green/yellow/red highlights.
>
> *"The red one here? That's a clause allowing AIA to reprice annually based on 'medical claims experience' — which is exactly why her premium just jumped 34%. She had no idea this clause existed until now."*
>
> **[Tap red highlight]** — Plain-language explanation appears.

This is the visual moment that wins the room.

---

## 8. Wow Factor 2 — FutureClaw (10-Year Decision Simulator)

### 8.1 What It Does

Interactive Monte Carlo simulation of the user's insurance future across 10 years. Two modes:

**Mode A — Affordability Simulator**
- Slider: medical inflation (3-20%)
- Slider: income growth (0-8%)
- Output: premium trajectory chart, year of "danger zone" breach (premium > 10% of income)

**Mode B — Life Event Simulator**
- Pick scenario: Cancer / Heart Attack / Disability / Death
- Output: covered amount, out-of-pocket, months of household income at risk
- Compare against "what if you switched to Plan B" alternative

### 8.2 Why It Wins

- **Time-machine effect** — Most apps show now. PolicyClaw shows 2036.
- **Emotional resonance** — "If you get cancer at 45, your family covers 4 months of income."
- **Interactive** — Sliders demand audience attention during demo
- **Quantifiable impact** — Hard MYR numbers for the pitch

### 8.3 How It Works (Technical)

- Monte Carlo runs 1000 simulations using numpy/scipy
- Pure Python, no GLM in the loop — instant updates as sliders move
- BNM medical inflation data (2014-2024) baked in as historical anchor
- GLM only generates the **narrative interpretation** ("Your premium will hit RM4,800 by 2030")

### 8.4 Functional Requirements

**Affordability Mode:**
- 10-year line chart with 3 scenario bands (optimistic/realistic/pessimistic)
- Sliders update chart in <100ms (60 FPS)
- "Danger zone" highlighted in red when premium exceeds 10% of income
- Cumulative cost displayed in MYR

**Life Event Mode:**
- 6 pre-baked scenarios with realistic Malaysian medical cost data
- Visual bar: green (covered) / amber (co-pay) / red (out-of-pocket)
- "Compare alternative" toggle shows side-by-side with a switched policy
- Family impact narrative generated by GLM

### 8.5 Acceptance Criteria

- [ ] Slider drag updates chart smoothly (no lag)
- [ ] All scenarios use cited Malaysian cost data
- [ ] Narrative regenerates when scenarios change
- [ ] Both modes accessible via toggle, not separate pages
- [ ] Charts downloadable as PNG

### 8.6 Demo Script

> **[Switch to FutureClaw — Affordability Mode]**
>
> *"This is Aisyah's premium projection for the next 10 years. By 2030, she's paying RM4,800 — 8% of her income. By 2034, it's 14%. That's the danger zone."*
>
> **[Drag inflation slider from 10% to 15%]**
>
> *"If medical inflation stays at 15% — which it did in 2024 — she's paying RM7,200 by 2030. Her policy becomes unaffordable by year 6."*
>
> **[Switch to Life Event Mode → Pick "Stage-2 Cancer"]**
>
> *"And if she gets diagnosed with cancer at 45? Her current policy covers RM180,000. Treatment costs RM250,000. Her family is RM70,000 short — eight months of household income. PolicyClaw says: switch to Plan B, which would cover RM280,000 fully."*

---

## 9. Technical Architecture

### 9.1 Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui |
| Backend | Python 3.12 + FastAPI + Pydantic + SQLModel |
| AI | Z.AI GLM-4.6 API + `instructor` (typed outputs) |
| PDF | PyMuPDF (fitz) for parsing, react-pdf-viewer for display |
| Charts | Recharts |
| Simulation | numpy + scipy.stats |
| Database | **Supabase** (Postgres + Auth + Storage + Realtime) |
| File storage | **Supabase Storage** (private bucket with signed URLs) |
| State (frontend) | Zustand + TanStack Query |
| Animation | Framer Motion |

### 9.2 Why Supabase

For PolicyClaw, Supabase is strategically superior to a local DB because it unlocks features the rubric rewards:

| Capability | What It Gives PolicyClaw |
|---|---|
| **Postgres + pgvector** | Production-grade DB + RAG over BNM corpus in one place |
| **Supabase Auth** | Magic-link login out of the box — saves a full day of building auth |
| **Supabase Storage** | Private bucket for policy PDFs with signed-URL access |
| **Supabase Realtime** | Frontend subscribes to DB changes — agents stream results live during demo (massive wow moment) |
| **Row Level Security** | PDPA compliance enforced at the DB layer — every policy tied to its owner |

**Setup cost:** 15-20 minutes (project creation + 1 SQL migration + env vars). Worth it for the rubric points and demo polish.

**Demo safety:** Cache demo runs to a local JSON file as a fallback. If conference wifi drops mid-pitch, the app reads from cache and the demo still works.

**Architecture statement (for pitch deck):**
> *"PolicyClaw uses Supabase for managed Postgres, Auth, Storage, and Realtime — letting us focus 24 hours on AI logic instead of plumbing."*

**Current implementation state (April 2026).** The repo currently has no database wired up. For the 24-hour build, the acceptable MVP fallback is ephemeral in-memory state (backend) + `localStorage` (frontend), with Supabase as the ship target if time permits. PRD requirements that depend on Supabase (Auth, RLS, PDPA deletion endpoint, Realtime streaming) are explicitly marked as "ship target, not MVP-gating" in §10.3.

### 9.3 Architecture Diagram

```
┌──────────────────────────────────────────────────────┐
│  Browser (localhost:3000)                            │
│  Next.js 15 + shadcn/ui + react-pdf + Recharts       │
└──────────────────────┬───────────────────────────────┘
                       │ HTTPS / JSON
                       ▼
┌──────────────────────────────────────────────────────┐
│  FastAPI (localhost:8000)                            │
│  Routes: /upload /analyze /simulate /recommend       │
└──────┬───────────────┬────────────────┬──────────────┘
       │               │                │
       ▼               ▼                ▼
┌────────────┐ ┌──────────────┐ ┌───────────────────┐
│ Ingestion  │ │ GLM Pipeline │ │ Simulation Engine │
│ PyMuPDF    │ │ Z.AI GLM-4.6 │ │ numpy + scipy     │
│ + Extract  │ │ + instructor │ │ Monte Carlo       │
└──────┬─────┘ └───────┬──────┘ └─────────┬─────────┘
       │               │                  │
       ▼               ▼                  ▼
┌──────────────────────────────────────────────────────┐
│  Supabase (cloud)                                    │
│  Postgres + pgvector + Auth + Storage + Realtime     │
└──────────────────────────────────────────────────────┘
```

### 9.4 GLM Pipeline (4 Sequential Calls per Analysis)

To stay simple for solo build, **collapse 6 agents into 4 GLM calls**:

1. **Extract** — Raw PDF text → structured `Policy` Pydantic model
2. **Annotate** — Each clause → `risk_level + explanation` (drives ClawView)
3. **Score** — Policy + user profile → 4 sub-scores (drives Health Score)
4. **Recommend** — All above + simulation results → `Verdict + Reasons + Citations`

Each call uses `instructor` for guaranteed typed output. Total latency target: ~12 seconds.

### 9.5 GLM Centrality Test (Brief Requirement)

The brief mandates: *"If GLM is removed, the system should not generate meaningful insights."*

Remove GLM, what survives?

- ❌ Plain-language extraction → broken
- ❌ ClawView risk annotations → broken
- ❌ Policy Health Score → broken (sub-scores need GLM judgment)
- ❌ Recommendations → broken
- ❌ Multilingual outputs → broken
- ✅ Monte Carlo numbers → survive (but no narrative interpretation)

**Conclusion:** Without GLM, PolicyClaw is a chart with no insight. ✅ Brief requirement satisfied.

### 9.6 Repository Structure

```
policyclaw/
├── README.md                # Hero image, 2-command setup, demo GIF
├── PRD.md                   # This document
├── ARCHITECTURE.md          # Detailed tech doc
├── RISKS.md                 # Risk register
├── .gitignore
│
├── backend/
│   ├── pyproject.toml
│   ├── .env.example         # ZAI_API_KEY=...
│   ├── app/
│   │   ├── main.py          # FastAPI entry
│   │   ├── core/
│   │   │   ├── config.py    # Pydantic Settings
│   │   │   ├── database.py  # Supabase client + SQLModel
│   │   │   └── glm_client.py  # Z.AI wrapper + retry
│   │   ├── models/          # SQLModel schemas
│   │   ├── schemas/         # Pydantic API schemas
│   │   ├── services/
│   │   │   ├── extraction.py   # GLM call 1
│   │   │   ├── annotation.py   # GLM call 2 (ClawView)
│   │   │   ├── scoring.py      # GLM call 3
│   │   │   ├── recommendation.py  # GLM call 4
│   │   │   └── simulation.py   # numpy/scipy
│   │   └── api/
│   │       ├── upload.py
│   │       ├── analyze.py
│   │       ├── simulate.py
│   │       └── recommend.py
│   ├── tests/
│   │   ├── test_extraction.py
│   │   ├── test_simulation.py
│   │   └── fixtures/        # 3 sample policies
│   └── data/
│       ├── bnm_corpus/      # Static BNM data (JSON, seeded into Supabase pgvector)
│       └── demo_cache/      # Cached GLM responses for offline demo fallback
│
└── frontend/
    ├── package.json
    ├── src/
    │   ├── app/
    │   │   ├── layout.tsx
    │   │   ├── page.tsx           # Landing
    │   │   ├── upload/page.tsx
    │   │   └── dashboard/page.tsx # Main analysis view
    │   ├── components/
    │   │   ├── ui/                # shadcn primitives
    │   │   ├── policy/
    │   │   │   ├── PolicyUploader.tsx
    │   │   │   ├── PdfViewer.tsx           # react-pdf-viewer wrapper
    │   │   │   └── ClawViewOverlay.tsx     # Wow Factor 1
    │   │   ├── health/
    │   │   │   └── HealthScoreGauge.tsx
    │   │   ├── future/
    │   │   │   ├── AffordabilitySimulator.tsx  # Wow Factor 2a
    │   │   │   └── LifeEventSimulator.tsx      # Wow Factor 2b
    │   │   ├── recommendation/
    │   │   │   ├── VerdictCard.tsx
    │   │   │   └── ActionSummary.tsx
    │   │   └── common/
    │   │       └── LanguageToggle.tsx
    │   └── lib/
    │       ├── api.ts
    │       ├── store.ts             # Zustand
    │       └── i18n.ts              # Simple JSON dict
    └── public/
        └── demo/                # Sample policy PDFs
```

---

## 10. Non-Functional Requirements

### 10.1 Performance Targets

| Metric | Target |
|---|---|
| PDF upload → preview rendered | ≤2s |
| Full analysis pipeline (4 GLM calls) | ≤15s |
| Simulation slider update | 60 FPS |
| ClawView highlight render | ≤500ms after analysis |
| Action Plan PDF generation | ≤2s |

### 10.2 Reliability

- All GLM calls wrapped in `tenacity` retry (3 attempts, exponential backoff)
- Per-call timeout: 30 seconds
- Graceful degradation: if Annotate call fails, ClawView shows "limited annotation available" but rest of flow continues
- All AI outputs persisted to Supabase before UI consumes (replayability via Realtime subscriptions)

### 10.3 Data & Privacy

- *Ship target (not MVP-gating for 24h build):* Supabase Auth + private bucket + RLS. Supabase Auth provides magic-link login; uploaded PDFs stored in private bucket with signed URLs (1-hour expiry)
- Row Level Security enforces `auth.uid() = user_id` on every table — users can only see their own policies
- No PII in logs (only user UUIDs)
- Disclaimer: "Not financial advice" on every recommendation screen
- User can delete all their data via a single endpoint (PDPA compliance)
- *MVP fallback:* session-only state via backend in-memory store + browser `localStorage`; no persistent PII across sessions. Demo flow works without Supabase.

### 10.4 Accessibility

- WCAG 2.1 AA targeted (color-blind safe palette for risk highlights)
- Full keyboard navigation
- Screen reader friendly (semantic HTML, ARIA labels)

### 10.5 Browser Support

Chrome 120+, Safari 17+, Firefox 121+, Edge 120+. Mobile responsive (tested on iPhone 14 viewport).

---

## 11. Success Metrics & Quantifiable Impact

### 11.1 Demo Success Metrics

| Metric | Target |
|---|---|
| Full analysis pipeline latency | <15 seconds |
| Field extraction accuracy | ≥90% on 3 demo policies |
| Risk highlights per policy | ≥8 |
| Languages supported | 2 (BM, EN) at full quality |
| GLM calls per analysis | 4 |
| Per-user projected savings shown | RM 4,200 - RM 18,400 |

### 11.2 Macro Impact (Pitch Slide)

**Per Aisyah (demo persona):** RM 18,400 projected savings over 10 years from switching policies + applying BNM rights + removing overlap.

**If 10% of Malaysia's 12 million MHIT policyholders use PolicyClaw once per year:**

- 1.2 million analyses/year
- **RM 2.4 billion in projected household savings** (conservative RM 2,000/user)
- **90,000+ policy lapses prevented** through better-informed decisions
- Thousands of BNM rights unlocked

### 11.3 Per-Analysis Tracking

Every analysis logs:

- Time saved (vs ~6 hours manual research)
- MYR savings projected over 10 years
- Risk clauses surfaced (count)
- Decision distribution (Hold/Switch/Downgrade/Add Rider)

These feed the "Impact Counter" on the landing page (powerful for pitch).

---

## 12. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| GLM hallucinates policy fields | High | High | `instructor` validation; side-by-side PDF for user verification; confidence scores |
| ClawView highlights misalign with PDF | Medium | High | Use PyMuPDF bounding boxes (not text-search); test with 3 policies before demo |
| Misclassified as financial advice | Medium | High | "Decision support, not advice" disclaimer on every screen; consult-advisor CTA on low-confidence |
| 24h scope creep | High | High | P0/P1 strictly enforced; if behind by Hour 12, cut F9 (multilingual EN-only) |
| Demo wifi failure (breaks Supabase calls) | Low | High | Pre-recorded backup video + screenshots in slide deck; cached demo responses replayable from local JSON |
| GLM API cost spike during demo | Low | Medium | Cache demo runs; budget USD 10 for hackathon |
| PDF parsing fails on sample | Low | High | Pre-test all 3 demo policies during Day 1; have backups |
| Supabase free tier limits hit | Low | Low | Free tier covers 500MB DB + 1GB storage — far beyond demo needs |
| Solo dev burnout | High | High | 6 hours sleep mandatory; pair-debug with teammate via screen share |

---

## 13. 24-Hour Build Plan

**Critical insight:** With 24 hours, polish > features. Cut anything that doesn't work by Hour 18.

### Hour 0-2 — Foundations
- Repo init, Next.js + FastAPI scaffolds running
- **Supabase project created, migrations run, Auth + Storage + pgvector enabled**
- **Supabase setup is ship-target only.** If it takes >30 minutes, defer to post-MVP; proceed with in-memory fallback and revisit in Hour 21-23 if time allows.
- GLM client tested with hello-world prompt
- 3 sample PDFs prepared (anonymized real policies)
- README skeleton

### Hour 2-6 — Backend Core
- `/upload` endpoint + PyMuPDF text extraction with bounding boxes
- GLM Call 1 (Extract) → working with instructor + Pydantic
- Supabase schema + SQLModel/Pydantic models
- BNM corpus seeded into Supabase pgvector

### Hour 6-10 — ClawView (Wow Factor 1)
- GLM Call 2 (Annotate) → returns risk levels per clause
- react-pdf-viewer integrated
- SVG overlay with bounding box positioning
- Tooltip on click → plain language explanation
- **Checkpoint: ClawView visibly working on 1 policy**

### Hour 10-14 — Health Score + Recommendation
- GLM Call 3 (Score) → 4 sub-scores
- Circular gauge component (Recharts or custom SVG)
- GLM Call 4 (Recommend) → verdict + reasons + confidence
- Verdict card UI

### Hour 14-18 — FutureClaw (Wow Factor 2)
- Monte Carlo simulation (numpy)
- Affordability mode chart with sliders
- Life Event mode with 4 scenarios (cut from 6)
- GLM narrative interpretation
- **Checkpoint: Both wow factors demonstrable**

### Hour 18-21 — Polish
- Action Summary with PDF download
- Multilingual toggle (BM + EN)
- Animations via Framer Motion
- Dashboard layout polish
- Loading states & error handling

### Hour 21-23 — Testing & Docs
- 3-4 pytest unit tests (extraction, simulation, recommendation)
- README with setup, screenshots
- ARCHITECTURE.md (1-page, link to architecture diagram)
- RISKS.md (10-line table)

### Hour 23-24 — Demo Recording
- Run demo flow 3 times to lock muscle memory
- Record 4-min screen capture as backup
- Hand off to teammate for slide finalization

### Critical Cut Points

If at **Hour 12** the core flow isn't working end-to-end:
- ❌ Cut Multilingual (English only)
- ❌ Cut Life Event mode (Affordability mode only for FutureClaw)
- ❌ Cut Action Plan PDF (just show on screen)

If at **Hour 18** ClawView isn't aligned properly:
- 🩹 Fall back to side-pane risk list with page references (not on-PDF overlay)
- This still scores high but loses the "wow"

---

## 14. Out of Scope (Explicitly)

- ❌ Real-time integration with insurer APIs (none exist publicly)
- ❌ Actual policy purchase or cancellation (regulatory)
- ❌ Claims filing assistance
- ❌ SME / business insurance
- ❌ Mobile native apps (responsive web only)
- ❌ Voice interface (too risky in 24h)
- ❌ Hokkien / Mandarin / Tamil language support (BM + EN only)
- ❌ Takaful-specific deep features (Shariah analysis stays generic)
- ❌ Production cloud deployment of the frontend (Supabase backend is hosted; frontend runs on localhost for demo)

These get listed in Future Roadmap on the pitch deck — shows we know what V2 looks like.

---

## 15. Why This Wins

### 15.1 Rubric Coverage Map

| Aspect | Weight | How PolicyClaw Wins |
|---|---|---|
| **Originality, Innovation** | 10% | ClawView (PDF risk overlay) is genuinely novel; FutureClaw simulator is differentiated |
| **Implementation Quality** | 12% | Clean Next.js + FastAPI structure; typed outputs via `instructor`; tests included |
| **Code Modularity** | 8% | Service layer separates extraction / annotation / scoring / recommendation |
| **System Architecture** | 7% | 4-step GLM pipeline + Monte Carlo engine + clean separation of concerns |
| **Target Users** | 8% | 3 detailed personas; "Aisyah moment" narrative grounds entire product |
| **Feature Prioritization** | 7% | P0/P1 matrix; explicit cut points at Hour 12 and 18 |
| **Problem Definition** | 5% | 6 cited statistics; 30M underinsured; BNM 2026 deadline |
| **Schema Design** | 6% | SQLModel + Pydantic; clean policy/analysis/decision separation |
| **Technical Feasibility** | 7% | Managed Supabase backend; ~5 min setup with provided SQL migration; cached demo fallback |
| **Risk Anticipation** | 5% | 8 risks + mitigations; explicit fallback plans |
| **Testing Strategy** | 5% | 3-4 pytest unit tests; sample-policy fixtures; acceptance criteria per feature |
| **Technical Walkthrough** | 6% | GLM centrality test; clear architecture diagram |
| **UI/UX** | 5% | shadcn/ui + Framer Motion; ClawView is the killer UX moment |
| **Pitch Deck Quality** | 4% | Aisyah story + RM 2.4B macro impact slide |
| **Version Control** | 5% | Meaningful commits; PR-based workflow; .github/workflows/ci.yml |

**Projected: 85+/100 if executed cleanly.**

### 15.2 The Differentiators Other Teams Won't Have

1. **PDF risk overlay** — Most teams will build chatbots or summary cards. Visible AI on the document is rare.
2. **Real Malaysian data** — Most teams will use generic insurance data. PolicyClaw cites BNM, LIAM, EY by name.
3. **Decision verdicts, not Q&A** — Most teams will say "ask AI questions." PolicyClaw says "do this specific thing."
4. **Quantified impact** — Most teams will say "saves money." PolicyClaw says "RM 2.4 billion across 1.2M users."
5. **Citation vault** — Most teams' AI outputs will have no traceability. Every PolicyClaw claim links to source.
6. **Multilingual UX** — Most teams will be English-only. PolicyClaw nails BM.
7. **Confidence transparency** — Most teams will show outputs as 100% certain. PolicyClaw shows uncertainty.

### 15.3 The Pitch Hook (Memorize This)

> *"30 million Malaysians are underinsured. Not because they can't afford insurance — because they can't decide. PolicyClaw is the first AI that doesn't just summarize policies — it claws through them. Watch."*
>
> **[Demo: Upload → ClawView → FutureClaw → Verdict]**
>
> *"That's a 4-minute decision that used to take 4 weeks of agent meetings. PolicyClaw saves Malaysians RM 2.4 billion a year — and prevents 90,000 cancer patients from losing coverage."*

---

## 16. Appendix

### 16.1 Glossary

| Term | Definition |
|---|---|
| MHIT | Medical and Health Insurance/Takaful |
| ITO | Insurance and Takaful Operator |
| LIAM | Life Insurance Association of Malaysia |
| PIAM | Persatuan Insurans Am Malaysia |
| MTA | Malaysian Takaful Association |
| BNM | Bank Negara Malaysia |
| Repricing | Industry term for raising premiums on existing policies |
| B40/M40/T20 | Bottom/Middle/Top 40%/40%/20% income classifications |
| Tabarru' | Donation concept in takaful |

### 16.2 Source References

- Bank Negara Malaysia. *Interim Measures for MHIT Policyholders.* December 2024.
- LIAM, PIAM, MTA. *Joint Statement on Medical Insurance Repricing.* November 2024.
- CodeBlue. *The Crisis Of Rising Medical Insurance Premiums.* November 2024.
- EY Malaysia. *Will Digital Insurance and Takaful Operators Close Malaysia's Protection Gap?* 2024.
- Malaysian Re. *Malaysian Insurance Highlights 2024.*
- The Edge Malaysia. *Special Report: Medical and Health Insurance.* April 2025.
- Institute for Health Systems Research. *Health Insurance Among Middle-Income Malaysians.* 2025.
- Swiss Re. *Sigma 3/2024 Report.*

### 16.3 Team & Roles

| Role | Owner | Responsibilities |
|---|---|---|
| Solo Dev | (You) | Full-stack build, all 24 hours |
| Pitch Lead | (Teammate) | Slides, demo script, presentation, Q&A prep |

### 16.4 Demo Day Checklist

- [ ] Laptop fully charged + charger
- [ ] Backup laptop or phone hotspot
- [ ] Pre-recorded demo video (in case live fails)
- [ ] 3 sample policies pre-loaded in app
- [ ] GLM API key working + budget verified
- [ ] Pitch deck on Google Drive + USB
- [ ] Practiced 4-min pitch with teammate (3+ times)
- [ ] Q&A defenses prepped (see Anti-Principles section)
- [ ] Disclaimer slide ready ("decision support, not advice")
- [ ] Closing CTA: "PolicyClaw — try it after the hackathon at policyclaw.my"

### 16.5 Revision History

| Version | Date | Changes |
|---|---|---|
| 1.0 | April 2026 | Initial PRD for UMHackathon 2026 submission (7-day build, 6-agent architecture, 11 features) |
| 2.0 | April 2026 | Polished 24-hour edition ("Untitled"); introduced ClawView + FutureClaw wow factors; cut Voice/Takaful/Regret |
| 2.1 | 2026-04-24 | Merged v1 + v2 into single PRD.md; documented Supabase ship-target vs in-memory MVP fallback; reconciled with codebase state |

---

**End of PRD.**

*PolicyClaw is a hackathon prototype built for UMHackathon 2026. It is decision-support software, not a licensed financial advisor. All recommendations are for informational purposes only.*

🦅 **Claw through complexity. Decide with confidence.**
