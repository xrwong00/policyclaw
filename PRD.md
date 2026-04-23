# PolicyClaw — Product Requirements Document

> **Claw back what your insurer won't tell you.**
>
> AI-powered insurance decision intelligence for 30 million underinsured Malaysians.

| | |
|---|---|
| **Version** | 1.0 |
| **Status** | Active — Hackathon MVP |
| **Event** | UMHackathon 2026 — Domain 2: AI for Economic Empowerment & Decision Intelligence |
| **Last Updated** | April 2026 |
| **Timeline** | 7-day preliminary build |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Definition](#2-problem-definition)
3. [Target Users & User Stories](#3-target-users--user-stories)
4. [Product Vision & Principles](#4-product-vision--principles)
5. [Feature Specification](#5-feature-specification)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Success Metrics & Quantifiable Impact](#7-success-metrics--quantifiable-impact)
8. [Technical Architecture Summary](#8-technical-architecture-summary)
9. [Risks & Mitigations](#9-risks--mitigations)
10. [Build Plan & Milestones](#10-build-plan--milestones)
11. [Out of Scope](#11-out-of-scope)
12. [Appendix](#12-appendix)

---

## 1. Executive Summary

### 1.1 The One-Liner

PolicyClaw is an AI-powered decision co-pilot that reads your insurance policies, simulates your future premiums, identifies coverage gaps and overlaps, and tells you exactly whether to hold, switch, or downgrade — in plain Bahasa Malaysia, English, or Mandarin.

### 1.2 Why This Matters Now

Three converging Malaysian realities make 2026 the perfect window:

1. **The Repricing Crisis**: In 2024, medical insurance premiums jumped 40-70% for millions of Malaysians. Nine percent of policyholders saw increases above 40% in a single year. Many cancelled coverage — including a cancer patient covered in national news.
2. **The BNM Intervention**: Bank Negara Malaysia capped premium hikes at 10% annually through end-2026, but the cap is opt-in by complaint and most policyholders don't know they qualify.
3. **The Information Asymmetry**: 30 million Malaysians are underinsured. 85% of SMEs lack adequate coverage. The root cause isn't affordability — it's decision paralysis. People don't understand what they own, what they'll pay, or what they'd lose.

### 1.3 The GLM-Powered Solution

PolicyClaw deploys a multi-agent system built on Z.AI's GLM-4.6 to:

- **Interpret** structured policy data and unstructured legal prose
- **Reason** across multiple policies, user profile, and regulatory context
- **Recommend** specific actions with projected ringgit impact
- **Explain** every decision in citation-traceable plain language

Without the GLM, the system produces no insights. The LLM is not a chatbot layer — it is the reasoning brain of the architecture.

### 1.4 Hackathon Positioning

PolicyClaw directly addresses every requirement of UMHackathon 2026 Domain 2:

| Brief Requirement | PolicyClaw Delivery |
|---|---|
| Interpretation of structured + unstructured data | PDF policies (unstructured) + BNM regulations (structured) + user profile |
| Context-aware reasoning | 6 specialized GLM agents consuming shared context |
| Actionable recommendations | Hold/Switch/Downgrade verdict with specific policy targets |
| Explainable decisions | Citation vault linking every claim to source documents |
| Decision-making, not automation | System does not file claims or buy policies — it empowers the user |
| Quantifiable impact | Projected ringgit savings + protection gap in MYR |
| Clear target users | Malaysian M40 policyholders aged 28-55 |
| Basic validation | Scenario-tested with 3 persona profiles + 6 sample policies |

---

## 2. Problem Definition

### 2.1 The Macro Problem

Malaysia has one of the most information-asymmetric insurance markets in ASEAN. Policies are sold verbally by agents, written in dense legalese, priced opaquely, and managed via paper notices. When prices change — as they did dramatically in 2024 — consumers have no tools to evaluate their options in the compressed decision window insurers provide.

### 2.2 Evidence Base

| Finding | Source | Relevance |
|---|---|---|
| 30 million Malaysians are underinsured | EY Malaysia (2024) | Total addressable problem |
| 85% of SMEs have inadequate coverage | EY Malaysia (2024) | B2B expansion opportunity |
| Medical claims cost inflation: 56% cumulative 2021-2023 | LIAM/PIAM/MTA joint statement (Nov 2024) | Driver of premium hikes |
| 9% of policyholders saw >40% premium hikes in 2024 | Bank Negara Malaysia 2024 Annual Report | Acute pain point |
| 60% of middle-income Malaysians view insurance as "wasteful if unused" | Institute for Health Systems Research (2025) | Decision paralysis evidence |
| BNM interim measures end 31 December 2026 | BNM Press Release (Dec 2024) | Urgency window |

### 2.3 The Specific User Pain (The "Aisyah Moment")

Aisyah, 38, marketing manager in KL, opens a letter from her insurer:

> *"Dear Policyholder, your medical insurance premium will increase from RM1,679 to RM2,242 (34% increase) effective next month..."*

She has three policies across two insurers, accumulated over 8 years of agent relationships. The letter is six pages of legalese. She has three questions nobody can help her answer:

1. **Should I switch, downgrade, or pay?** — No tool exists to model this.
2. **Am I even getting what I pay for?** — Her policies overlap, but she doesn't know by how much.
3. **What are my rights under the new BNM rules?** — The rules were buried in news articles she never read.

Her choices today: call an agent (biased), call a friend (uninformed), or ignore the problem (most common). All three are suboptimal. PolicyClaw is the fourth option.

### 2.4 Why Existing Solutions Fail

| Existing Solution | Limitation |
|---|---|
| Price comparison sites (PolicyStreet, RinggitPlus) | Help at purchase time, useless post-purchase |
| Insurance agents | Commission-motivated; can't advise against their own products |
| Insurer apps (MyZurich, AIA+) | Loyal to insurer; won't suggest switching |
| Financial advisors | Inaccessible to B40/M40; priced for high-net-worth |
| ChatGPT / generic LLMs | No policy context, no BNM knowledge, no simulation |
| Status quo (ignore it) | Results in 30M underinsured Malaysians |

PolicyClaw occupies a genuinely empty quadrant: **policyholder-aligned, technically competent, and always available**.

---

## 3. Target Users & User Stories

### 3.1 Primary Persona — "Aisyah the Reluctant Optimizer"

| Attribute | Value |
|---|---|
| Age | 38 |
| Income | RM8,500/month (M40) |
| Location | Klang Valley |
| Family | Married, 2 children |
| Policies owned | 2-4 (mix of medical, life, CI, takaful) |
| Tech comfort | High (uses Grab, Shopee, DuitNow daily) |
| Languages | BM (primary), English, some Mandarin |
| Trigger event | Received premium repricing notice |
| Goal | Make the right decision within her 30-day window |
| Fear | Losing coverage just before a health crisis |

### 3.2 Secondary Persona — "Uncle Lim the Skeptic"

| Attribute | Value |
|---|---|
| Age | 58 |
| Income | RM5,200/month (retired/semi-retired) |
| Location | Penang |
| Family | Empty-nester, adult children |
| Policies owned | 3-5 (accumulated over 30 years, some lapsed) |
| Tech comfort | Moderate (uses WhatsApp, not much else) |
| Languages | Hokkien, Mandarin, Bahasa, English |
| Trigger event | Child asks "Pa, what happens if you get sick?" |
| Goal | Understand if 30 years of premium payments were worth it |
| Fear | Being too old to switch, stuck in expensive plans |

### 3.3 Tertiary Persona — "Siti the Shariah-Conscious Planner"

| Attribute | Value |
|---|---|
| Age | 32 |
| Income | RM6,000/month |
| Location | Shah Alam |
| Family | Newlywed, expecting first child |
| Policies owned | 1 (takaful family plan) |
| Tech comfort | High |
| Languages | Bahasa (primary), English |
| Trigger event | Pregnancy — planning family protection |
| Goal | Ensure Shariah-compliant coverage is adequate without overpaying |
| Fear | Being sold a plan that doesn't truly meet Shariah principles |

### 3.4 Epic User Stories

**Epic 1 — First-Time Analysis**

> As Aisyah, when I receive a repricing notice, I want to upload my insurance policies and get a clear verdict within 60 seconds, so I can make a confident decision before my deadline.

**Epic 2 — Coverage Confidence**

> As Aisyah, I want to know if my three policies have overlapping coverage, so I can stop paying twice for the same protection.

**Epic 3 — Future-Proofing**

> As Aisyah, I want to see what my premiums will cost when I'm 48, 58, and 68 years old, so I can plan whether to switch now.

**Epic 4 — Rights Advocacy**

> As Aisyah, I want to know if I qualify for BNM's premium cap protections, so I can demand them from my insurer.

**Epic 5 — Emotional Decision Support**

> As Aisyah, I want to simulate "what if I get cancer?" with my current policies, so I can feel the stakes viscerally, not abstractly.

**Epic 6 — Language Comfort**

> As Uncle Lim, I want the app to speak to me in Mandarin or Hokkien, so I can understand the recommendations without depending on my daughter to translate.

**Epic 7 — Shariah Alignment**

> As Siti, I want to compare takaful and conventional options with respect for the Shariah concepts that matter to me (tabarru', wakalah), so I can make a faith-aligned decision.

**Epic 8 — Cancellation Regret Prevention**

> As Aisyah, I want to see what I'd lose if I cancel my policy impulsively after a premium hike, so I don't make a decision I'll regret in 5 years.

**Epic 9 — Voice Access**

> As Uncle Lim, I want to ask questions about my policy using my voice in Hokkien, so I don't have to type on a small screen.

**Epic 10 — Trust Through Transparency**

> As Aisyah, I want to see exactly where PolicyClaw's recommendation came from — which clause, which regulation, which data point — so I know it's not making things up.

---

## 4. Product Vision & Principles

### 4.1 Vision

To become the trusted decision co-pilot for every insurance policyholder in Malaysia — starting with the 30 million who are currently underinsured and overwhelmed.

### 4.2 Core Principles

**P1. User-Aligned, Always.** PolicyClaw earns no commission from insurers. Every recommendation is solely for the user's benefit.

**P2. Explain or Don't Say It.** No opaque outputs. If GLM can't cite a source, the claim doesn't appear.

**P3. Decision Support, Not Advice.** We present options with projected impact. The user decides. We are not a licensed financial advisor.

**P4. Malaysian-First.** Not a global product with BM translated in. Built from the ground up for Malaysian regulations, languages, culture, and insurance products.

**P5. Respect the Gravity.** Insurance decisions affect families for decades. No tricks, no dark patterns, no premature celebratory confetti.

**P6. Confidence Calibrated.** Every AI output has a confidence score. Low confidence triggers human-advisor referral, not bluster.

### 4.3 Anti-Principles (Things We Will Not Do)

- Will not sell user data to insurers
- Will not auto-purchase or auto-cancel policies
- Will not give binding legal or financial advice
- Will not replicate an insurance agent's aggressive sales patterns
- Will not gamify decisions that deserve gravity

---

## 5. Feature Specification

### 5.1 Feature Prioritization Matrix

| ID | Feature | Priority | Effort | Impact | Day |
|---|---|---|---|---|---|
| F1 | Policy X-Ray | P0 | M | H | 2-3 |
| F2 | Overlap Map | P0 | M | H | 3 |
| F3 | 10-Year Premium Crystal Ball | P0 | M | H | 4 |
| F4 | BNM Rights Scanner | P0 | S | H | 4 |
| F5 | Keep-Switch-Dump Verdict | P0 | M | H | 4 |
| F6 | "If This Happens" Life Simulator | P1 | M | H | 5 |
| F7 | Voice Policy Interrogation | P1 | M | M | 5-6 |
| F8 | Takaful vs Conventional Showdown | P1 | S | M | 5 |
| F9 | Multi-lingual Explainer | P1 | S | H | 5 |
| F10 | Regret Simulator | P1 | S | M | 6 |
| F11 | Citation Vault + Confidence | P0 | S | H | Throughout |

Priority legend: P0 = must-ship, P1 = should-ship, P2 = nice-to-ship. Effort: S=small (≤1 day), M=medium (1-2 days), L=large (3+ days).

---

### 5.2 F1 — Policy X-Ray

**Description.** Upload one or more insurance policy PDFs. GLM parses the document, extracts every clause, translates legalese into plain language, and flags hidden exclusions.

**User Story.** *As Aisyah, when I upload my AIA medical policy, I want to see a plain-language breakdown of what it covers and excludes, so I understand what I actually own.*

**Functional Requirements.**

- Accept PDF uploads up to 10 MB each, up to 5 policies per session
- Support both text-native and scanned PDFs (OCR fallback via Tesseract)
- Extract structured fields: insurer, plan name, annual premium, coverage limit, effective date, policy type, riders, exclusions
- Translate each major clause into plain English and Bahasa Malaysia
- Display side-by-side view: original PDF page on left, extracted + translated fields on right
- Flag "gotcha clauses" with a visual indicator (e.g., 30-day waiting periods, pre-existing condition exclusions, age limits)

**Acceptance Criteria.**

- [ ] Upload completes in ≤3 seconds for a 5-page PDF
- [ ] Field extraction accuracy ≥90% on 6 sample policies (validated against ground truth)
- [ ] All extracted fields show source page number
- [ ] Plain-language summary under 150 words per clause
- [ ] UI displays side-by-side view responsively on desktop and tablet

**GLM Role.** Primary — entire extraction and translation relies on GLM's ability to read unstructured legal prose.

---

### 5.3 F2 — Overlap Map

**Description.** Interactive visualization showing coverage overlap across the user's uploaded policies. Identifies duplicate coverage and quantifies the ringgit cost of that duplication.

**User Story.** *As Aisyah, I want to see if my three policies are paying for the same cancer coverage, so I can stop wasting money on duplicates.*

**Functional Requirements.**

- Display an interactive Venn-style diagram of coverage across uploaded policies
- Categorize coverage by type: Hospitalization, Critical Illness, Death Benefit, Disability, Outpatient, Dental, Maternity
- For each overlap zone, compute: duplicate premium paid per year, coverage amount duplicated
- Show a "Potential Savings" ribbon quantifying what could be saved by consolidation
- Allow hover/click to see which policies contribute to each zone

**Acceptance Criteria.**

- [ ] Renders correctly for 2, 3, 4, and 5 uploaded policies
- [ ] Detects overlap on at least 7 coverage categories
- [ ] Duplicate premium calculation is within ±10% of a manually computed baseline
- [ ] Interactive elements respond in <100ms
- [ ] Fallback message if only one policy is uploaded

**GLM Role.** Heavy — semantic comparison of coverage clauses across policies (a simple string match would miss 80% of overlaps because insurers use different language for the same coverage).

---

### 5.4 F3 — 10-Year Premium Crystal Ball

**Description.** Monte Carlo simulation projecting the user's insurance premium trajectory over the next 10 years, under three economic scenarios.

**User Story.** *As Aisyah, I want to see what my premiums will look like when I'm 48, so I can decide if it's sustainable long-term.*

**Functional Requirements.**

- Pull historical medical inflation data from BNM (2014-2024)
- Project premiums under three scenarios: Optimistic (5% inflation), Realistic (10%), Pessimistic (15%)
- Factor in: age band jumps, BNM staggering cap (until end-2026), insurer repricing history
- Interactive slider allowing user to adjust inflation assumption from 3% to 20%
- Display a "breakpoint year" — the year premium exceeds 10% of user's projected income
- Show the cumulative 10-year premium cost in MYR

**Acceptance Criteria.**

- [ ] Simulation completes in ≤1 second (pure numpy, no GLM)
- [ ] Chart updates smoothly as slider is dragged (60 FPS target)
- [ ] Breakpoint year calculation accounts for assumed income growth (default 3% annually)
- [ ] All three scenarios rendered simultaneously as overlaid lines
- [ ] Results downloadable as PNG

**GLM Role.** Minimal — simulation is deterministic numpy; GLM only generates the narrative interpretation ("You're projected to spend RM52,000 on this policy by 2036").

---

### 5.5 F4 — BNM Rights Scanner

**Description.** Scans the user's policies against the current BNM regulatory corpus and identifies which consumer protections apply. Generates a written request letter to the insurer for any unapplied rights.

**User Story.** *As Aisyah, I want to know if I'm entitled to BNM's 10% premium cap, so I can demand it from AIA.*

**Functional Requirements.**

- Maintain a curated BNM knowledge base: Dec 2024 interim measures, July 2024 copayment rules, FAQ on repricing, relevant circulars
- For each uploaded policy, GLM evaluates eligibility against each BNM rule
- Display a checklist: ✅ Rights already applied / ⚠️ Rights you qualify for but aren't getting / ❌ Rights that don't apply
- For each unapplied right, generate a formal letter the user can email to their insurer
- Letter includes: policy reference, specific BNM circular, demand language, reply deadline

**Acceptance Criteria.**

- [ ] Knowledge base contains at least 5 BNM rulings from 2023-2025
- [ ] Each rule evaluation completes within 2 seconds
- [ ] Generated letter is in both English and Bahasa Malaysia
- [ ] Letter cites exact BNM circular number and section
- [ ] User can download letter as PDF or copy to clipboard

**GLM Role.** Heavy — requires reasoning about whether a specific user's policy falls under a specific regulation, including edge cases (policy age, plan type, policyholder age).

---

### 5.6 F5 — Keep-Switch-Dump Verdict

**Description.** The final decision output. A clear, traffic-light verdict for each policy: Keep (🟢), Downgrade (🟡), Switch (🔴), or Dump (⚫). Accompanied by the top 3 reasons and a confidence score.

**User Story.** *As Aisyah, after reviewing my policies, I want a clear recommendation for each one so I don't have to interpret raw data.*

**Functional Requirements.**

- For each uploaded policy, output: verdict (Keep / Downgrade / Switch / Dump), confidence score (0-100%), top 3 reasons with citations, projected ringgit impact
- Verdict synthesis consumes outputs from Coverage Gap Agent, Premium Forecaster, Duplicate Detector, and BNM Rights Scanner
- Display as a card per policy, with the overall verdict at the top of the dashboard
- Each reason expandable to show GLM's reasoning chain
- Low-confidence verdicts (<60%) display a "Consult a licensed advisor" banner

**Acceptance Criteria.**

- [ ] Every verdict has at least 2 and at most 5 reasons
- [ ] Every reason links to a specific source (policy clause, BNM regulation, simulation output)
- [ ] Confidence score is calibrated — low scores appear for ambiguous cases
- [ ] Verdict is consistent across reruns for identical input (deterministic)
- [ ] Cards visually distinct: color, icon, weight

**GLM Role.** Central — this is the agent that synthesizes everything. It is the Switch Strategist agent.

---

### 5.7 F6 — "If This Happens" Life Simulator

**Description.** Emotional decision support. User picks a life scenario (diagnosed with cancer, heart attack, pregnancy, death of primary earner); simulator shows financial outcome under current policies.

**User Story.** *As Aisyah, I want to simulate what happens if I'm diagnosed with stage-2 cancer tomorrow, so I can feel whether my coverage is enough.*

**Functional Requirements.**

- Offer 6 scenarios: Stage-2 Cancer, Heart Attack, Motor Accident (severe), Pregnancy + Complications, Primary Earner Death, Permanent Disability
- Each scenario has: estimated Malaysian medical/financial cost (based on public data), estimated duration, estimated out-of-pocket if uninsured
- With user's policies applied: compute covered amount, out-of-pocket amount, protection gap in MYR
- Visualize as a bar: Green (covered), Amber (co-payment), Red (out-of-pocket)
- Show the family impact: months of household income covered, recovery horizon

**Acceptance Criteria.**

- [ ] Each scenario uses realistic Malaysian cost data (cited in UI)
- [ ] Computation accounts for coverage limits, sub-limits, exclusions, waiting periods
- [ ] Protection gap calculated in MYR with context ("equivalent to 8 months of your income")
- [ ] Scenarios run in <500ms
- [ ] Emotionally thoughtful copy — no horror, no celebration, just clarity

**GLM Role.** Medium — for each scenario, GLM determines which policy clauses apply (e.g., "this cancer treatment falls under critical illness rider, not medical").

---

### 5.8 F7 — Voice Policy Interrogation

**Description.** User speaks into their device in BM, English, Mandarin, or Hokkien; GLM answers questions about their uploaded policies with spoken response.

**User Story.** *As Uncle Lim, I want to ask my policy questions in Hokkien and get spoken answers, so I don't need my daughter's help.*

**Functional Requirements.**

- Web Speech API for voice input (browser native, no extra infra)
- Support BM, English, Mandarin, and Hokkien (via GLM multilingual capability + Whisper fallback)
- Answer questions in the same language as the question
- Every voice response also displayed as text with citations
- Voice responses synthesized via browser's built-in speechSynthesis (falls back to ElevenLabs if budget allows)
- Example queries: "Boleh saya klaim jika kena diabetes?" / "我的保单什么时候过期?" / "Lim eh, zhe ge policy u pau kanser bo?"

**Acceptance Criteria.**

- [ ] Voice input works on Chrome and Safari (mobile + desktop)
- [ ] Speech recognition accuracy >85% on test queries in each language
- [ ] Response time ≤5 seconds from end of speech to start of answer
- [ ] Text transcription always visible alongside voice output
- [ ] Graceful fallback to text input if microphone denied

**GLM Role.** Heavy — understands multilingual queries, retrieves relevant policy context, generates contextual spoken response.

**Scope note.** Hokkien support is best-effort. Even showing it works on a few common phrases wins demo points; perfect Hokkien is out of scope for 7 days.

---

### 5.9 F8 — Takaful vs Conventional Showdown

**Description.** Side-by-side comparison of equivalent takaful and conventional policies, respecting the Shariah concepts that matter (tabarru', wakalah, mudharabah). Projects surplus-sharing outcomes over 10 years.

**User Story.** *As Siti, I want to compare my takaful plan with a conventional alternative while respecting my Shariah preferences, so I can make a faith-aligned financial decision.*

**Functional Requirements.**

- Side-by-side comparison of takaful vs equivalent conventional policy
- Explain takaful concepts in plain language: tabarru' (donation), wakalah (agency), mudharabah (profit-sharing), surplus sharing
- Project surplus distribution over 10 years for the takaful option
- Flag Shariah-specific features: absence of riba, gharar, maysir
- Allow user to toggle "Shariah Importance" from 0-10, which re-weights the recommendation

**Acceptance Criteria.**

- [ ] Comparison supports all 4 major Malaysian product categories (medical, life, family, investment-linked)
- [ ] Shariah concept explanations verified against MTA glossary
- [ ] Surplus projection uses realistic industry rates (public data)
- [ ] Toggle changes verdict in Keep-Switch-Dump when changed significantly
- [ ] Available in BM and English (Shariah terminology preserved)

**GLM Role.** Medium — understands Shariah concepts and their practical implications; generates culturally appropriate explanations.

---

### 5.10 F9 — Multi-lingual Explainer

**Description.** Every explanation, verdict, and AI output available in Bahasa Malaysia, English, Mandarin, and Hokkien romanization. Not translation — contextual regeneration.

**User Story.** *As Uncle Lim, I want the app to speak my language so I don't feel like an outsider in my own insurance decisions.*

**Functional Requirements.**

- Language toggle in UI header (persistent across session)
- Every AI-generated text regenerated in selected language (not translated — GLM generates native-quality text per language)
- Insurance terminology preserved correctly in each language
- UI chrome (buttons, headers) localized via next-intl
- Default language inferred from browser Accept-Language header

**Acceptance Criteria.**

- [ ] All 4 languages supported across all AI outputs
- [ ] Language switch takes ≤500ms
- [ ] No English leakage in BM/Mandarin modes
- [ ] Preferred language persisted in user profile
- [ ] Hokkien uses standard Pe̍h-ōe-jī romanization

**GLM Role.** Heavy — generates native-quality insurance language in 4 languages. This is why we use GLM over other LLMs — its Chinese and multilingual performance is differentiated.

---

### 5.11 F10 — Regret Simulator

**Description.** Before the user cancels a policy, the app simulates everything they'd lose: no-claim bonuses, accumulated waiting periods, loyalty benefits, future insurability risk due to age/health changes.

**User Story.** *As Aisyah, when I'm tempted to cancel my policy after a premium hike, I want to see what I'm giving up so I don't make a decision I'll regret.*

**Functional Requirements.**

- Triggered when user marks a policy for "Dump"
- Simulate: surrender value forfeited, no-claim bonus lost, waiting period reset consequences, increased premium if reinstated later (age-based calculation)
- Show probability of insurability refusal if user tries to buy similar coverage in 5 years, based on general population statistics
- Display a "Think Twice" screen with numerical and emotional framing
- Still allow the user to proceed — we inform, we don't paternalize

**Acceptance Criteria.**

- [ ] Trigger is automatic on "Dump" verdict
- [ ] Losses quantified in specific MYR amounts where possible
- [ ] Insurability refusal probability shown with disclaimer it's a general estimate
- [ ] Screen is skippable after 5 seconds if user is determined
- [ ] Logs an event for later "did they proceed?" analytics

**GLM Role.** Medium — interprets surrender clauses from the original policy, which vary wildly.

---

### 5.12 F11 — Citation Vault + Confidence Scores

**Description.** Every single claim PolicyClaw makes links to a specific source. Every AI output has a confidence score. Low-confidence outputs route to a human-advisor referral.

**User Story.** *As Aisyah, I want to see where every recommendation came from and how confident the AI is, so I can trust this over an insurance agent.*

**Functional Requirements.**

- Every fact in the UI has a citation marker (superscript number)
- Clicking a citation opens a side panel showing: source document, exact quote, page number, timestamp of retrieval
- Every AI output displays a confidence badge: High (>80%), Medium (60-80%), Low (<60%)
- Low-confidence outputs show a yellow banner: "This analysis has limited certainty. Consider consulting a licensed advisor."
- All citations logged in the database for audit

**Acceptance Criteria.**

- [ ] 100% of numerical claims have citations
- [ ] 100% of AI recommendations have confidence scores
- [ ] Citation panel loads in <200ms
- [ ] Confidence score is calibrated (not always >90%)
- [ ] Low-confidence banner doesn't appear spuriously

**GLM Role.** Structural — uses instructor library to force Pydantic schemas that include `citations: list[Citation]` and `confidence: float` as required fields.

---

## 6. Non-Functional Requirements

### 6.1 Performance

| Metric | Target |
|---|---|
| PDF upload → first extracted field | ≤3 seconds |
| Full 6-agent analysis cold run | ≤15 seconds |
| Full 6-agent analysis cached | ≤2 seconds |
| Frontend LCP | ≤1.5 seconds |
| Simulation chart update on slider | 60 FPS |
| Voice query → response start | ≤5 seconds |
| API p95 latency (non-GLM) | ≤200 ms |

### 6.2 Security & Privacy

- All user data stored in Supabase with Row Level Security enforced at the database level
- Policy PDFs stored in private Supabase Storage buckets with signed URLs (1-hour expiry)
- No PII logged beyond user ID
- Prompt injection defenses: uploaded content sanitized before GLM calls
- PDPA compliance: user can delete all their data via a single endpoint
- Rate limiting: 10 requests per minute per IP on sensitive endpoints

### 6.3 Reliability

- GLM calls wrapped in tenacity retry (exponential backoff, 3 attempts)
- Celery-free architecture uses asyncio.gather with per-agent timeouts
- Graceful degradation: if one agent fails, others continue and a partial result is shown
- All agent outputs persisted before UI consumes them (replayability)

### 6.4 Accessibility

- WCAG 2.1 AA compliance targeted
- Color-blind-safe palette for verdict traffic lights
- Voice input as alternative to typing (helps low-literacy users)
- All critical actions keyboard-navigable

### 6.5 Browser Support

Chrome 120+, Safari 17+, Firefox 121+, Edge 120+. Mobile Safari and Chrome on Android.

---

## 7. Success Metrics & Quantifiable Impact

### 7.1 Demo Success Metrics (What We Show Judges)

| Metric | Target | How Measured |
|---|---|---|
| Full analysis pipeline latency | <15 seconds | Timer in demo |
| Field extraction accuracy | ≥90% | Validated against 6 sample policies |
| Number of policies analyzable | Up to 5 in parallel | Demo uploads 3 |
| Languages supported | 4 (BM, EN, 中文, Hokkien) | Demo toggles all 4 |
| Distinct AI agents orchestrated | 6 | Shown in architecture |
| Projected per-user savings | RM 4,200 - RM 18,400 | Based on demo persona |

### 7.2 Macro Impact Projection (Pitch Slide)

Per Aisyah, the demo persona: **RM 18,400 projected savings over 10 years** from switching policies + applying BNM rights + removing overlap.

If 10% of Malaysia's 12 million MHIT policyholders use PolicyClaw once per year:

- **1.2 million analyses/year**
- **RM 2.4 billion in projected household savings** (at conservative RM 2,000 average per user)
- **90,000+ policy lapses prevented** (Regret Simulator intervention)
- **Thousands of BNM rights unlocked** (Rights Scanner)

These are the numbers for slide 7 of the pitch deck.

### 7.3 Per-User Impact Tracking

Every analysis logs:

- Time saved (vs estimated 6 hours of manual research)
- MYR savings projected over 10 years
- Rights unlocked (count)
- Overlap eliminated (MYR/year)
- Decisions made (Keep/Switch/Downgrade/Dump breakdown)

Aggregated into the "Impact Counter" shown on the landing page.

---

## 8. Technical Architecture Summary

Full architecture details are in `ARCHITECTURE.md`. This section is a PRD-level summary.

### 8.1 Stack

- **Frontend**: Next.js 15 (App Router) + TypeScript + Tailwind CSS + shadcn/ui + TanStack Query + Zustand + Recharts + Framer Motion
- **Backend**: Python 3.12 + FastAPI + Pydantic + SQLModel
- **AI Layer**: Z.AI GLM-4.6 API + LangGraph (orchestration) + instructor (structured outputs) + sentence-transformers (embeddings) + PyMuPDF (PDF parsing)
- **Data Plane**: Supabase (Postgres + pgvector + Auth + Storage + Realtime) — all managed
- **Dev Tooling**: uv (Python deps) + pnpm (Node deps) + ruff + mypy + pytest + pre-commit + GitHub Actions

### 8.2 Key Architectural Decisions

| Decision | Rationale |
|---|---|
| LangGraph over raw agent loops | Explainable state machine for financial decisions |
| instructor over raw JSON mode | Pydantic validation guarantees typed outputs |
| Supabase over self-hosted Postgres | Auth + Realtime + Storage + pgvector all unified |
| pgvector over ChromaDB | RAG + relational data in one database |
| Frontend talks to Supabase directly | Less backend code, leverages RLS for security |
| FastAPI reserved for AI operations | Python has the ML ecosystem; Supabase handles CRUD |
| Multilingual embeddings model | `paraphrase-multilingual-mpnet-base-v2` handles BM, EN, 中文, Tamil |

### 8.3 GLM Centrality (Brief Requirement)

The brief mandates: *"If the GLM component is removed, the system should no longer be able to generate meaningful insights."*

Test: remove GLM, what breaks?

- ✘ Policy X-Ray (can't parse legal prose into structured fields)
- ✘ Overlap Map (can't semantically compare clauses across policies)
- ✘ BNM Rights Scanner (can't reason about eligibility)
- ✘ Keep-Switch-Dump Verdict (can't synthesize agent outputs into a recommendation)
- ✘ Life Simulator (can't map scenarios to applicable clauses)
- ✘ Voice Interrogation (can't understand multilingual questions)
- ✘ Takaful Showdown (can't explain Shariah concepts in context)
- ✘ Multi-lingual Explainer (can't generate native-quality text in 4 languages)
- ✘ Regret Simulator (can't interpret surrender clauses)
- ✘ Citation Vault (can't generate citation-backed claims)

Only the Monte Carlo simulation (F3's numerics) survives without GLM — and it's just a chart without the narrative.

---

## 9. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| GLM hallucinates policy terms | High | High | instructor + Pydantic validation; all extracted fields shown side-by-side with source PDF for user confirmation |
| Misclassified as financial advice (BNM/SC regulatory issue) | Medium | High | Disclaimer layer on every recommendation; framed as "decision support" not "financial advice"; "consult a licensed advisor" CTA on low-confidence outputs |
| PDPA violation (sensitive policy data exposed) | Medium | High | Supabase RLS enforces auth.uid() on every row; no PII in logs; user-controlled data deletion endpoint |
| BNM rules change during hackathon | Low | Medium | Rules stored in versioned YAML, not hardcoded; easily updated |
| User uploads policy from non-supported insurer | Medium | Low | Graceful fallback: "Limited analysis available — key fields may be missing"; don't fail catastrophically |
| Voice recognition fails in noisy conditions | Medium | Low | Always show text input as alternative; Whisper fallback for accuracy |
| Demo crashes on live internet failure | Low | High | Pre-record fallback demo video; test wifi before pitch |
| Hokkien support is incomplete | High | Low | Set expectation as "best-effort"; show working BM/EN/Mandarin as strong evidence |
| 6-agent analysis exceeds 15s in demo | Medium | Medium | Aggressive caching; pre-warm demo policies; parallelize via asyncio.gather |
| Token costs spike during demos | Medium | Medium | Cache all demo runs; use shorter prompts; budget ~USD 20 for hackathon week |

See `RISKS.md` for the full risk register with mitigation owners and test procedures.

---

## 10. Build Plan & Milestones

### 10.1 Seven-Day Sprint

| Day | Focus | Key Deliverables | Done When |
|---|---|---|---|
| **1** | Foundations | Repo scaffolded, Supabase project live, migrations run, GLM hello-world, BNM data scraped | `pnpm dev` and `uvicorn` both run; GLM returns "hello"; SQL schema in Supabase |
| **2** | Ingestion + RAG | PDF parser working, structured extraction via instructor, pgvector seeded with BNM corpus | Upload PDF → see extracted fields in Supabase |
| **3** | Core Agents (Wave 1) | BaseAgent class, Coverage Gap Agent, Duplicate Detector Agent, Overlap Map UI | F1 + F2 demonstrable end-to-end |
| **4** | Core Agents (Wave 2) | Premium Forecaster, Switch Strategist, BNM Rights Scanner, Keep-Switch-Dump UI, Crystal Ball chart | F3 + F4 + F5 demonstrable; full primary flow works |
| **5** | Wow Features | Life Simulator, Multi-lingual Explainer, Takaful Comparator, Voice Interrogation | F6 + F8 + F9 shipped; F7 voice demo works in 2 languages |
| **6** | Polish & Trust | Regret Simulator, Citation Vault, Confidence Scores, Risk register, tests, docs | F10 + F11 done; coverage badge on README; ARCHITECTURE.md complete |
| **7** | Demo Production | Record demo, finalize pitch deck, dry runs, README polish | Final submission |

### 10.2 Checkpoint Gates

- **End of Day 2**: If ingestion pipeline is flaky, simplify F1 extraction and continue. Don't sink Day 3 debugging PDFs.
- **End of Day 4**: If core flow isn't end-to-end, defer F6 and F7 to "stretch" and focus on polish.
- **End of Day 5**: If voice is unreliable, show pre-recorded voice demo; don't ship broken live voice.
- **End of Day 6**: Freeze feature development. Day 7 is demo-only.

### 10.3 Team Assignments (Suggested)

Assuming a 3-4 person team:

- **AI/Backend Lead**: Days 1-2 ingestion + RAG. Days 3-4 agents. Day 5 voice.
- **Full-stack**: Days 1-2 repo + Supabase. Days 3-4 Overlap Map + Crystal Ball UI. Days 5-6 wow features UI.
- **Frontend/Design**: Day 1 design system. Days 2-4 component library. Days 5-6 polish, animation, accessibility.
- **PM/Demo**: Day 1 PRD. Day 2 BNM scraping. Day 5 demo script. Days 6-7 recording + deck.

---

## 11. Out of Scope

Explicitly excluded from the hackathon MVP:

- ❌ Real-time integration with insurer APIs (no Malaysian insurer exposes one publicly)
- ❌ Actual policy purchasing or cancellation (regulatory complexity, we inform only)
- ❌ Claims filing assistance (separate product area)
- ❌ SME/business insurance (consumer-focused for now)
- ❌ Mobile native apps (web-only for MVP; responsive web is sufficient)
- ❌ Licensed financial advisor network (future roadmap)
- ❌ Paid premium tiers (free MVP)
- ❌ Insurer partnerships (post-hackathon business development)
- ❌ Advanced fraud detection (separate problem domain)
- ❌ Historical policy backtesting beyond 10 years (data availability)

---

## 12. Appendix

### 12.1 Glossary

| Term | Definition |
|---|---|
| MHIT | Medical and Health Insurance/Takaful (BNM terminology) |
| ITO | Insurance and Takaful Operator |
| LIAM | Life Insurance Association of Malaysia |
| PIAM | Persatuan Insurans Am Malaysia (General Insurance Association) |
| MTA | Malaysian Takaful Association |
| BNM | Bank Negara Malaysia (central bank) |
| Tabarru' | Donation concept in takaful — participant contributes to a shared pool |
| Wakalah | Agency — takaful operator acts as agent managing the pool |
| Mudharabah | Profit-sharing investment structure |
| Repricing | Industry term for raising premiums on existing policies |
| DITO | Digital Insurance and Takaful Operator (new BNM license type) |
| B40/M40/T20 | Bottom/Middle/Top income classifications in Malaysia |
| DRG | Diagnosis-Related Group (proposed new hospital billing model) |

### 12.2 Source References

- Bank Negara Malaysia. *Interim Measures for MHIT Policyholders.* December 2024.
- LIAM, PIAM, MTA. *Joint Statement on Medical Insurance Repricing.* November 2024.
- CodeBlue. *The Crisis Of Rising Medical Insurance Premiums.* Dr Sean Thum. November 2024.
- EY Malaysia. *Will Digital Insurance and Takaful Operators Close Malaysia's Protection Gap?* 2024.
- Malaysian Re. *Malaysian Insurance Highlights 2024.*
- The Edge Malaysia. *Special Report: An urgent wake-up call to provide medical and health insurance for all.* April 2025.
- Institute for Health Systems Research. *Factors influencing health insurance purchase among middle-income Malaysians.* 2025.
- Swiss Re. *Sigma 3/2024 Report.*

### 12.3 Revision History

| Version | Date | Changes |
|---|---|---|
| 1.0 | April 2026 | Initial PRD for UMHackathon 2026 submission |

### 12.4 Team & Contacts

*To be filled by the PolicyClaw team.*

---

**End of PRD.**

*PolicyClaw is a hackathon prototype and not a licensed financial advisor. All recommendations are for decision-support purposes only.*
