# PolicyClaw — QA & Test Document (QATD)

| | |
|---|---|
| **Version** | 1.0 — 2026-04-24 |
| **Status** | Active — Hackathon MVP |
| **Event** | UMHackathon 2026 — Domain 2 |
| **Paired spec** | `PRD.md` v2.2, `SAD.md` v1.0 |

Judged against ~10% of the rubric directly (Risk Anticipation 5% + Testing Strategy 5%) and influences another ~10% via Technical Feasibility (7%).

---

## 1. Quality Goals & Metrics

Derived from PRD §9.1:

| Metric | Target | Verification |
|---|---|---|
| PDF upload → preview rendered | ≤2 s | Manual browser stopwatch |
| `/api/analyze` full response | ≤15 s | Network tab + `cached` badge on reruns |
| Monte Carlo simulator slider | 60 FPS, <100 ms update | Chrome DevTools Performance panel |
| ClawView highlight render | ≤500 ms after `/v1/clawview` resolves | Network tab + visual check |
| Action Plan PDF generation | <2 s from button click | Manual stopwatch |
| Verdict consistency across 3 identical reruns | Byte-identical verdict + confidence_score | `test_verdict_consistency.py` (F7) |
| Health Score calibration | Overall in 30-85 band on real policies | Manual check on 3 sample PDFs (F5) |

---

## 2. Risk Matrix

Likelihood × Impact, scale 1 (low) – 5 (critical). Score = L × I.

| ID | Risk | L | I | Score | Mitigation | Owner |
|---|---|---|---|---|---|---|
| R1 | GLM API failure or rate-limit mid-demo | 3 | 5 | 15 | Streaming `post_glm_with_retry` with exponential-backoff retries (default 3 attempts / 120s read timeout; ClawView Annotate tightens to 2 attempts / 30s so it degrades within ~60s instead of hanging). Demo cache serves last successful payload. Recommend stage falls back to deterministic `generate_verdict`; Extract stage falls back to `_mock_policy_xray`; Score stage falls back to `_heuristic_health_score`; ClawView/FutureClaw fall back to heuristic/mock narratives. | shell |
| R2 | Wifi drops during the live demo | 2 | 5 | 10 | `backend/data/demo_cache/*.json` pre-warmed on 3 sample PDFs before the demo. Re-run serves cached payloads; UI shows "Served from demo cache" badge. | shell |
| R3 | ClawView bbox misalignment on scanned / rasterized PDFs | 4 | 3 | 12 | `/v1/clawview` catches exceptions and returns a handled error. UI renders an inline message instead of blanking. A side-pane risk list is the planned fallback if bbox alignment breaks on demo day. | clawview |
| R4 | Verdict inconsistency across reruns (F7 break) | 3 | 4 | 12 | Temperature 0.1 on Recommend. Demo cache makes repeated identical inputs fully deterministic. Covered by `backend/tests/test_verdict_consistency.py`. | shell |
| R5 | Simulator jitter on underpowered laptops | 2 | 3 | 6 | Monte Carlo is pure numpy, 1000 runs complete in <50 ms on modern laptops. GLM narrative regenerates only on toggle, not every tick. Chart export is off the render path. | futureclaw |
| R6 | Text-native PDF parse failure | 3 | 3 | 9 | `pdf_parser.parse_pdf_chunks` returns `[]` on non-PDF bytes; `clawview_service` handles empty-chunk case by surfacing a low-confidence mock response rather than 500. Covered by `test_extraction.py`. | clawview |
| R7 | Ilmu endpoint returns malformed JSON | 2 | 4 | 8 | `_extract_json_from_content` tolerates code-fenced responses. Schema validation raises on invalid shapes, which the `analyze_policy_*` wrappers catch and route into the heuristic fallback with a LOW confidence band so the UI can nudge the user toward a human advisor. | shell |
| R8 | `GLM_API_KEY` unset on judge's machine | 2 | 5 | 10 | Pipeline automatically enters mock / heuristic mode. All four stages produce valid outputs; confidence bands drop to LOW; reasons indicate the fallback. Demo still works end-to-end. | shell |
| R9 | Scanned-only PDFs (no OCR text layer) | 2 | 3 | 6 | PyMuPDF returns zero text; parsing yields empty chunks; Annotate falls back to a low-confidence "limited annotation" response. OCR is deferred post-hackathon. | clawview |
| R10 | AI hallucination passing as cited fact | 3 | 4 | 12 | Every `Reason` requires a `Citation` with source + quote + locator. Prompt explicitly forbids invented citations. Low confidence steers the UI to "consult a human advisor." Disclaimer on every recommendation screen. | shell |
| R11 | Secret leakage in commit | 1 | 5 | 5 | `.env` in `.gitignore`. `backend/.env.example` is the only tracked env file. GLM key is read via `os.getenv`, never logged. | shell |

---

## 3. Testing Strategy

### Pyramid

| Layer | Framework | Location | Current count | Scope |
|---|---|---|---|---|
| **Unit (backend)** | `pytest` | `backend/tests/` | **19 green** | FutureClaw Monte Carlo + narrative (13), extraction sanity (2), premium simulation sanity (2), verdict consistency / F7 (2). |
| **Integration (manual)** | `curl` + browser | — | — | End-to-end against a live local stack with 3 sample PDFs. |
| **End-to-end (manual)** | Browser | — | — | Full user journey: upload → intake → analyze → ClawView → FutureClaw → VerdictCard → PDF download → BM/EN toggle. |
| **Offline demo** | Demo cache pre-warmed | `backend/data/demo_cache/` | — | Pipeline works with wifi disabled. |

### New unit tests added by this worktree

| File | Tests | Purpose |
|---|---|---|
| `test_extraction.py` | 2 | `parse_pdf_chunks` handles valid PDFs; returns `[]` or raises on garbage bytes (never produces spurious chunks a GLM could over-interpret). |
| `test_simulation.py` | 2 | `project_premiums` produces 3 scenarios × 10-year arrays. Pessimistic cumulative > realistic > optimistic. Breakpoint year is `None` or 1..10. Names chosen to avoid collision with `test_futureclaw.py`'s coverage of `monte_carlo_affordability` and `simulate_life_events`. |
| `test_verdict_consistency.py` | 2 | F7 acceptance. Heuristic `generate_verdict` is byte-deterministic. `analyze_policy_verdict` (fallback mode) produces identical verdict + confidence across 3 reruns. |

### Running tests

```bash
pytest backend/tests/ -q    # from repo root — CI invocation
```

Expect 19 tests green.

### Manual QA checklist (pre-demo walk-through)

| Step | Pass criterion |
|---|---|
| Upload sample PDF 1 (medical) | Profile fields auto-populate in Step 2. |
| Click Analyze | `POST /api/analyze` returns in ≤ 15 s. VerdictCard + HealthScoreGauge render. |
| ClawView follow-up | `POST /v1/clawview` fires exactly once; PDF renders with bbox highlights. |
| Click a red highlight | Tooltip with plain-language explanation appears. |
| Toggle FutureClaw to Life Event | `POST /v1/simulate/life-event` fires once; 4 scenario bars render. |
| Drag Affordability slider | Chart updates at 60 FPS; `POST /v1/simulate/affordability` fires on release only. |
| Repeat Analyze with identical input | "Served from demo cache" badge; verdict + confidence identical. |
| Toggle BM ↔ EN | All AI strings re-render in target language. Static labels switch via `t()`. Disclaimer and pill labels both switch. |
| Download Action Summary | jsPDF file opens cleanly in <2 s; contains verdict + 3 reasons + 3 actions + disclaimer + analysis_id. |
| HealthScoreGauge calibration | Overall scores on 3 sample policies all in 30-85 range (PRD F5). |
| Disable wifi, re-run Analyze | Demo cache serves the response; UI shows cached badge; ClawView panel surfaces a handled error (not a blank page). |

---

## 4. Test Fixtures & Data

| Fixture | Location | Purpose |
|---|---|---|
| BNM medical inflation series | `backend/data/bnm_corpus/medical_inflation.json` | Historical anchor for FutureClaw Monte Carlo. |
| Life-event cost medians | `backend/data/bnm_corpus/life_event_costs.json` | Seeds life-event scenarios with cited Malaysian cost data. |
| Demo cache (gitignored in MVP; pre-warmed for demo) | `backend/data/demo_cache/*.json` | One file per (stage, canonical args) SHA-256. Protects demo against wifi drops and keeps verdicts deterministic. |
| Mock-mode guarantees | `ai_service._mock_*`, `_heuristic_*` | Every public `ai_service.analyze_*` path has a non-GLM fallback — the pipeline never returns 500 from a GLM problem. |

---

## 5. CI/CD Gates — live

`.github/workflows/ci.yml` is **live on main** and runs on every push and PR to `**` branches. Two parallel jobs:

### Backend job (`ubuntu-latest`, Python 3.12)

| Step | Behavior on failure |
|---|---|
| `pip install -r backend/requirements.txt` | Hard fail — must install. |
| `pip install ruff` | Hard fail — must install. |
| `python -c "import app.main"` (smoke import) | **Hard gate.** CI red on import error. |
| `ruff check backend/` | **Informational** (`continue-on-error: true`). |
| `pytest backend/tests/ -q` | **Hard gate when tests present** (guarded by `hashFiles('backend/tests/**/test_*.py') != ''`). |

### Frontend job (`ubuntu-latest`, Node 20)

| Step | Behavior on failure |
|---|---|
| `npm ci --prefix frontend` | Hard fail. |
| `npm run lint --prefix frontend` | **Informational** (`continue-on-error: true`). Present to surface debt without blocking shipping. |
| `npm run build --prefix frontend` | **Hard gate.** Next.js build must complete. |

**Rationale for the informational-lint choice.** During the 24-hour build, style debt cannot block critical path changes. Lint warnings are surfaced to developers but do not block merges; once the team has bandwidth, promote lint to a hard gate post-hackathon.

---

## 6. Manual Verification Checklist — one row per wow-factor demo moment

| Demo moment | Acceptance |
|---|---|
| ClawView overlay renders on the real PDF | ≥8 highlights per demo policy (F4 acceptance); color coding is meaningful (red is not random); highlights align with text. |
| Click a red ClawView highlight | Tooltip appears with plain-language explanation in current language; ≤80 words. |
| HealthScoreGauge overall score | In 30-85 band for real Malaysian policies (F5 acceptance — not all 90+). |
| FutureClaw Affordability chart | Updates at 60 FPS on slider drag; `POST /v1/simulate/affordability` fires on release only. |
| FutureClaw Life Event toggle | 4 scenarios (Cancer / Heart Attack / Disability / Death); `POST /v1/simulate/life-event` fires exactly once per event switch; narratives regenerate. |
| ClawView fetch after Analyze | `POST /v1/clawview` fires exactly once after `POST /api/analyze` completes. |
| BM/EN toggle | All AI strings re-render in target language (narrative_en ↔ narrative_bm, plain_explanation_en ↔ plain_explanation_bm); static UI strings switch via `t()`. |
| Action Summary PDF | jsPDF generates a one-pager in <2 s (F8 acceptance); opens cleanly in Preview/Acrobat. |
| VerdictCard ADD RIDER pill | Renders when `needs_rider === true && verdict === "keep"`; reason #1 surfaces the suggested rider. |

---

## 7. Known Limitations & Defer List

| Item | Reason | Reopen when |
|---|---|---|
| Supabase (Auth, RLS, pgvector RAG, Realtime) | PRD §8.2 + §9.3 flag as ship target, not MVP-gating. | Post-hackathon, any paid plan. |
| Zh + Hokkien UI | PRD P5 limits MVP to BM + EN. | Beyond Malaysian-first scope. |
| Voice interrogation (F7) | Scaffold endpoint stays in mock mode. | Post-hackathon product work. |
| OCR path for scanned PDFs | Tesseract integration deferred; current MVP covers text-native PDFs. | Post-hackathon if user research justifies. |
| Frontend unit / E2E suite (Vitest + Playwright) | 24-hour budget excludes setup. Manual QA + CI build gate carry the frontend. | Post-hackathon; CI already has a `frontend` job that can host the new steps. |
| `AIFeatures.tsx` style debt | Already deleted on main (commit `6cb1a3e`). Historical baggage resolved. | N/A. |

---

## 8. Submission Evidence

At submission time this document pairs with:

- `backend/tests/` — passing pytest suite (19 tests green).
- `backend/data/demo_cache/*.json` — pre-warmed cached runs for the 3 sample policies.
- `SAD.md` — architecture reference.
- `PRD.md` — product reference.
- A 4-minute demo video recorded on Hour 23 per PRD §10 schedule.
- `.github/workflows/ci.yml` CI run showing backend + frontend green.

**End of QATD.**
