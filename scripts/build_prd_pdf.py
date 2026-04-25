"""Generate docs/hackathon/PolicyClaw-PRD.pdf from inlined content.

One-off build script. Run from repo root:

    backend/.venv/Scripts/python scripts/build_prd_pdf.py

Renders an HTML/CSS document via PyMuPDF's fitz.Story API into an A4 PDF
that mirrors the structure of docs/hackathon/prd-sample.pdf.
"""
from __future__ import annotations

from pathlib import Path

import fitz

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "docs" / "hackathon" / "PolicyClaw-PRD.pdf"

CSS = """
* { font-family: sans-serif; }
body { font-size: 11pt; line-height: 1.45; color: #111; }

h1.cover-title {
  font-size: 26pt;
  font-weight: 700;
  text-align: center;
  margin-top: 220pt;
  letter-spacing: 1pt;
}
p.cover-sub {
  font-size: 14pt;
  text-align: center;
  margin-top: 8pt;
  color: #333;
}
p.cover-meta {
  font-size: 11pt;
  text-align: center;
  margin-top: 6pt;
  color: #555;
}
p.cover-email {
  font-size: 10pt;
  text-align: center;
  margin-top: 220pt;
  color: #666;
}

h1.toc-title { font-size: 18pt; font-weight: 700; margin-top: 0; margin-bottom: 14pt; }
table.toc { width: 100%; border-collapse: collapse; }
table.toc td { padding: 4pt 0; font-size: 11pt; }
table.toc td.num { width: 24pt; }
table.toc td.page { width: 30pt; text-align: right; color: #555; }

h1.section { font-size: 16pt; font-weight: 700; margin-top: 14pt; margin-bottom: 6pt; color: #0b1e3f; }
h2.subsection { font-size: 12.5pt; font-weight: 700; margin-top: 10pt; margin-bottom: 4pt; color: #0b1e3f; }
h3.subsubsection { font-size: 11pt; font-weight: 700; margin-top: 8pt; margin-bottom: 2pt; }

ul { margin-top: 4pt; margin-bottom: 8pt; padding-left: 18pt; }
li { margin-bottom: 4pt; }

p { margin: 4pt 0; }
.lead { font-weight: 700; }

.page-break { page-break-before: always; }

code { font-family: monospace; font-size: 10.5pt; background: #f1f1f1; padding: 0 2pt; }

table.kv { width: 100%; border-collapse: collapse; margin-top: 6pt; }
table.kv td { padding: 3pt 6pt; vertical-align: top; font-size: 10.5pt; border-bottom: 1px solid #eee; }
table.kv td.k { width: 130pt; font-weight: 700; }
"""

HTML = """
<!-- ============== COVER ============== -->
<h1 class="cover-title">PRODUCT REQUIREMENT DOCUMENT (PRD)</h1>
<p class="cover-sub">UMHackathon 2026</p>
<p class="cover-meta">Project: PolicyClaw &nbsp;&middot;&nbsp; Version 2.2 &nbsp;&middot;&nbsp; 2026-04-24</p>
<p class="cover-meta">Domain 2 &mdash; AI for Economic Empowerment &amp; Decision Intelligence</p>
<p class="cover-email">Email: umhackathon@um.edu.my</p>

<!-- ============== TOC ============== -->
<div class="page-break"></div>
<h1 class="toc-title">Table of Contents</h1>
<table class="toc">
  <tr><td class="num">1.</td><td>Project Overview</td><td class="page">3</td></tr>
  <tr><td class="num">2.</td><td>Background &amp; Business Objective</td><td class="page">3</td></tr>
  <tr><td class="num">3.</td><td>Product Purpose</td><td class="page">3</td></tr>
  <tr><td class="num">4.</td><td>System Functionalities</td><td class="page">4</td></tr>
  <tr><td class="num">5.</td><td>User Stories &amp; Use Cases</td><td class="page">6</td></tr>
  <tr><td class="num">6.</td><td>Features Included (Scope Definition)</td><td class="page">7</td></tr>
  <tr><td class="num">7.</td><td>Features Not Included (Scope Control)</td><td class="page">7</td></tr>
  <tr><td class="num">8.</td><td>Assumptions &amp; Constraints</td><td class="page">7</td></tr>
  <tr><td class="num">9.</td><td>Risks &amp; Questions Throughout Development</td><td class="page">8</td></tr>
</table>

<!-- ============== BODY ============== -->
<div class="page-break"></div>

<p><span class="lead">Project Name:</span> PolicyClaw &mdash; AI Insurance Decision Copilot for Malaysians<br/>
<span class="lead">Version:</span> 2.2 &nbsp;&middot;&nbsp; <span class="lead">Date:</span> 2026-04-24 &nbsp;&middot;&nbsp;
<span class="lead">Status:</span> Active &mdash; Hackathon MVP</p>

<h1 class="section">1. Project Overview</h1>
<ul>
  <li><span class="lead">Problem Statement:</span> Malaysia is in a medical-insurance repricing crisis. BNM's 2024 Annual Report shows 9% of MHIT policyholders received premium hikes &gt;40%, with cumulative claims inflation of 56% across 2021&ndash;2023. EY Malaysia (2024) estimates 30 million underinsured Malaysians, with decision paralysis &mdash; not affordability &mdash; as the dominant root cause. Policyholders facing 30-day repricing decision windows have no neutral, citation-backed tool to evaluate Hold / Switch / Downgrade / Add Rider.</li>
  <li><span class="lead">Target Domain:</span> UMHackathon 2026 Domain 2 &mdash; AI for Economic Empowerment &amp; Decision Intelligence. Vertical: Malaysian retail health and life insurance decision support (LIAM / PIAM / MTA / BNM data ecosystem).</li>
  <li><span class="lead">Proposed Solution Summary:</span> PolicyClaw is an AI insurance decision copilot. Users upload 1&ndash;3 policy PDFs; the system extracts structured fields, annotates hidden risks directly on the original PDF (ClawView), scores policy health on a 0&ndash;100 gauge with four sub-scores, simulates 10 years of premiums and life events via Monte Carlo (FutureClaw), and returns a Hold / Switch / Downgrade / Add Rider verdict with three reasons, confidence percentage, 10-year MYR impact, and citations &mdash; in Bahasa Malaysia or English.</li>
</ul>

<h1 class="section">2. Background &amp; Business Objective</h1>
<ul>
  <li><span class="lead">Background of the Problem:</span> Malaysian insurance policies are dense, multilingual, and full of asymmetric clauses (premium repricing triggers, pre-existing condition exclusions, waiting-period traps, co-payment requirements, sub-limit caps). Public BNM, LIAM, PIAM, and MTA data exists but is never synthesized at the consumer's point of decision. Agents have a commission incentive; comparison sites have a placement incentive. There is no user-aligned, explainable second opinion.</li>
  <li><span class="lead">Importance of Solving This Issue:</span> BNM's interim 10% annual cap on medical-insurance hikes expires <span class="lead">31 December 2026</span>. Most policyholders do not know they qualify, and the cap's removal will compress decision windows further. The 30-day repricing-notice window leaves no time for human advisory. Decision-paralysis has measurable consequences: 30M underinsured Malaysians (EY 2024) translate to household-level financial fragility on every cancer diagnosis, hospitalisation, or critical-illness event.</li>
  <li><span class="lead">Strategic Fit / Impact:</span> PolicyClaw aligns directly with Domain 2's mandate &mdash; AI for Economic Empowerment &amp; Decision Intelligence. The product is built on five non-negotiable principles: (P1) user-aligned (no insurer commissions), (P2) explain or don't say it (every AI claim cites a source clause and page), (P3) decision support, not advice (user decides; disclaimer on every recommendation screen), (P4) confidence calibrated (0&ndash;100% on every output; low confidence routes the user to a human advisor), and (P5) Malaysian-first (BM + EN only for MVP; real BNM / LIAM / PIAM / MTA data, not generic placeholders).</li>
</ul>

<h1 class="section">3. Product Purpose</h1>

<h2 class="subsection">3.1 Main Goal of the System</h2>
<p>To give Malaysians an explainable, citation-backed verdict on whether to <span class="lead">Hold</span>, <span class="lead">Switch</span>, <span class="lead">Downgrade</span>, or <span class="lead">Add Rider</span> on each insurance policy they own &mdash; with quantified 10-year forward-looking impact in Malaysian Ringgit, in their preferred language. PolicyClaw replaces opaque agent advice and unfocused comparison-site browsing with a transparent, source-cited, decision-grade analysis delivered in roughly 15 seconds.</p>

<h2 class="subsection">3.2 Intended Users (Target Audience)</h2>
<ul>
  <li><span class="lead">Aisyah &mdash; primary persona.</span> 38, M40 KL marketing manager, 2&ndash;4 policies, just received a repricing notice with 30 days to decide. Needs a fast, citation-backed verdict and 10-year MYR impact she can show her spouse.</li>
  <li><span class="lead">Uncle Lim &mdash; secondary persona.</span> 58, multilingual (BM + Hokkien + EN), reads policy fine print but mistrusts agents. Needs plain-language clause explanations in Bahasa Malaysia and a clear &quot;why this matters&quot; per highlighted risk.</li>
  <li><span class="lead">Siti &mdash; secondary persona.</span> 32, takaful and Shariah-conscious. Needs an affordability projection that flags the year her premium is forecast to exceed 10% of household income, plus a switching alternative for comparison.</li>
</ul>

<h1 class="section">4. System Functionalities</h1>

<h2 class="subsection">4.1 Description</h2>
<p>PolicyClaw operates as an eight-step end-to-end analysis pipeline driven by a four-call typed LLM chain wrapped around a deterministic Monte Carlo simulator. Steps: (1) Upload 1&ndash;3 PDFs &le;10MB &mdash; PyMuPDF extracts text plus per-clause bounding boxes; (2) single-screen profile intake (age, income bracket, dependents, primary concern, language); (3) Policy X-Ray extracts structured policy fields with source-page tags; (4) ClawView paints color-coded risk highlights on the original PDF; (5) Policy Health Score renders a 0&ndash;100 gauge with four sub-scores; (6) FutureClaw runs 10-year Monte Carlo across two toggleable modes; (7) Recommendation Engine produces a Hold / Switch / Downgrade / Add Rider verdict with three reasons, confidence, MYR impact, and citations; (8) Action Summary delivers a downloadable PDF card with verdict, top-three reasons, top-three concrete actions, and disclaimer.</p>

<h2 class="subsection">4.2 Key Functionalities</h2>
<ul>
  <li><span class="lead">PDF Upload &amp; Extraction (F1, P0).</span> Drag-and-drop 1&ndash;3 PDFs; PyMuPDF text + bounding-box extraction; preview via react-pdf-viewer; &le;3s for a 5-page PDF.</li>
  <li><span class="lead">Profile Intake (F2, P0).</span> Single-screen form storing user inputs in localStorage; completes in &le;30 seconds.</li>
  <li><span class="lead">Policy X-Ray &mdash; LLM Extract (F3, P0).</span> Insurer, plan, premium, coverage, riders, exclusions, waiting periods, co-pay; &ge;90% field accuracy on three demo policies.</li>
  <li><span class="lead">ClawView &mdash; LLM Annotate (F4, P0, Wow Factor 1).</span> Color-coded highlights overlaid on the original PDF (green standard / yellow worth knowing / red hidden risk); click to reveal plain-language explanation plus citation. Targets at minimum five risk types per policy: premium repricing clauses, pre-existing condition exclusions, waiting-period traps, co-payment requirements, sub-limit caps.</li>
  <li><span class="lead">Policy Health Score (F5, P0).</span> Single 0&ndash;100 gauge with four sub-scores 0&ndash;25 each: Coverage Adequacy, Affordability, Premium Stability, Clarity &amp; Trust. Sample policies are calibrated to score 30&ndash;85, never all 90+.</li>
  <li><span class="lead">FutureClaw (F6, P0, Wow Factor 2).</span> Interactive 10-year Monte Carlo (1000 runs via numpy / scipy.stats) with two toggleable modes: <em>Affordability</em> (premium trajectory vs income, sliders for medical inflation 3&ndash;20% and income growth 0&ndash;8%, danger-zone flag when premium &gt; 10% of income) and <em>Life Event</em> (Cancer / Heart Attack / Disability / Death &mdash; covered vs co-pay vs out-of-pocket, months of household income at risk, compare-alternative toggle).</li>
  <li><span class="lead">Recommendation Engine &mdash; LLM Recommend (F7, P0).</span> Per-policy verdict with three reasons (each with citation), confidence percentage, 10-year MYR impact, explicit trade-offs. Verdict consistent across three reruns of identical input.</li>
  <li><span class="lead">Action Summary &amp; PDF Download (F8, P0).</span> Downloadable card via jsPDF in &lt;2s with verdict, top-three reasons, top-three concrete actions, and disclaimer.</li>
  <li><span class="lead">Multilingual BM / EN (F9, P1).</span> All AI outputs work in both languages; UI strings via JSON dict (no i18next dependency for MVP).</li>
  <li><span class="lead">Polish &amp; Animations (F10, P0).</span> Framer Motion transitions on key screens; loading and error states.</li>
</ul>

<h2 class="subsection">4.3 AI Model &amp; Prompt Design</h2>

<h3 class="subsubsection">4.3.1 Model Selection</h3>
<p><span class="lead">Model:</span> OpenAI <code>gpt-5-mini</code> via <code>api.openai.com/v1</code>. Defaults are resolved by <code>backend/app/core/glm_client.py</code> (<code>OPENAI_API_BASE=https://api.openai.com/v1</code>, <code>OPENAI_MODEL=gpt-5-mini</code>) and override every older provider reference in supplementary documents &mdash; the code is ground truth. <span class="lead">Justification:</span> gpt-5-mini delivers strong structured-output reliability (Pydantic v2 schema validation across all four LLM calls), low-latency streaming SSE (essential for keeping reasoning-model responses healthy under a ~15s analysis budget), and bilingual quality sufficient for clause-level Bahasa Malaysia and English narrative interpretation. <span class="lead">Provider waiver:</span> the project initially targeted Z.AI GLM via Ilmu (<code>api.ilmu.ai</code> / <code>ilmu-glm-5.1</code>) under the hackathon's mandatory-Z.AI rule; the organizers waived the rule for this submission after the Ilmu gateway proved unstable in practice, so the reasoning provider was swapped to OpenAI.</p>

<h3 class="subsubsection">4.3.2 Prompting Strategy</h3>
<p><span class="lead">Strategy:</span> multi-step agentic chain &mdash; four sequential typed LLM calls per analysis, each writing to a Pydantic v2 model: (1) <span class="lead">Extract</span> raw PDF text into a structured <code>Policy</code>; (2) <span class="lead">Annotate</span> each clause with <code>{risk_level: green|yellow|red, plain_explanation, clause_id}</code> &mdash; this drives ClawView; (3) <span class="lead">Score</span> the policy plus user profile into four sub-scores &mdash; this drives the Health Score gauge; (4) <span class="lead">Recommend</span> consumes everything above plus simulation results and produces verdict + 3 reasons + confidence + MYR impact + citations. <span class="lead">Why agentic over zero-shot:</span> each call has a narrow, schema-validated job, which (a) keeps prompts short enough that gpt-5-mini consistently produces valid JSON, (b) lets each stage's output be cited downstream, satisfying Principle P2 (&quot;explain or don't say it&quot;), and (c) lets the system degrade gracefully if any single call fails. All four calls flow through <code>post_glm_with_retry</code>, which streams SSE chunks to keep long reasoning-model responses healthy.</p>

<h3 class="subsubsection">4.3.3 Context &amp; Input Handling</h3>
<p>Maximum input: <span class="lead">three PDFs per session, &le;10MB each</span>. PyMuPDF (fitz) extracts text together with per-clause bounding boxes; bounding boxes are required for ClawView's overlay alignment, so the parser is not interchangeable with text-only extractors. <span class="lead">Oversized input:</span> rejected at the upload boundary with a user-facing error before any LLM call is dispatched &mdash; cost protection plus a clear failure mode. <span class="lead">Scanned PDFs:</span> best-effort &mdash; text extraction degrades gracefully but ClawView highlight alignment is not guaranteed; the user sees a notice that highlights may be approximate. <span class="lead">Unstructured / off-format documents</span> (non-policy uploads): the Extract call's Pydantic validator rejects malformed structures and the UI surfaces &quot;this does not look like an insurance policy.&quot; No truncation or chunking is applied within MVP scope; if a single PDF's clause count exceeds the per-call window in future, chunked annotation by clause-page is the planned escalation path.</p>

<h3 class="subsubsection">4.3.4 Fallback &amp; Failure Behavior</h3>
<p>All LLM calls route through <code>post_glm_with_retry</code> with exponential backoff on transport errors. Per-call default budget: <span class="lead">3 attempts / 120s httpx read timeout</span>. ClawView's Annotate call tightens this to <span class="lead">2 attempts / 30s</span> so a slow upstream degrades to the heuristic mock within ~60s instead of hanging the frontend. If Annotate fails, ClawView shows <em>&quot;limited annotation available&quot;</em> &mdash; the rest of the flow continues uninterrupted (graceful degradation). For demo robustness, the backend caches successful runs to <code>backend/data/demo_cache/</code> as JSON; if wifi drops during judging, the app reads from cache and the demo still works. Per Principle P4, low-confidence outputs (&lt; calibrated threshold) recommend that the user consult a licensed human advisor rather than acting on the verdict. Every recommendation screen carries an explicit &quot;not financial advice&quot; disclaimer (Principle P3).</p>

<h1 class="section">5. User Stories &amp; Use Cases</h1>

<p><span class="lead">User Stories:</span></p>
<ul>
  <li><em>As Aisyah,</em> I want to upload my repricing-notice policy PDF and receive a Hold / Switch / Downgrade / Add Rider verdict with three cited reasons, so I can make a defensible decision within my 30-day window without booking an agent meeting.</li>
  <li><em>As Uncle Lim,</em> I want every clause-level risk explained in Bahasa Malaysia at the same fidelity as the English version, so I can read my policy's hidden risks in my preferred language without losing nuance.</li>
  <li><em>As Siti,</em> I want a 10-year affordability projection that flags the year my premium is forecast to exceed 10% of my household income, so I can plan a switch before I am forced into one.</li>
</ul>

<p><span class="lead">Use Cases (Main Interactions):</span></p>
<ul>
  <li><span class="lead">Upload-to-Verdict primary flow:</span> the user drags 1&ndash;3 PDFs, completes the profile intake, and receives extracted fields, ClawView overlay, Health Score, FutureClaw simulation, verdict, and downloadable Action Summary &mdash; in roughly 15 seconds.</li>
  <li><span class="lead">ClawView click-to-explain:</span> on any color-coded highlight, the user clicks a clause and is shown a plain-language explanation (&le;80 words), the cited source page, and a &quot;why this matters&quot; framing in their selected language.</li>
  <li><span class="lead">FutureClaw scenario exploration:</span> the user toggles between Affordability and Life Event modes, drags inflation and income-growth sliders (60 FPS, &lt;100ms slider-to-chart latency, no LLM in the slider loop), picks a life-event scenario (Cancer / Heart Attack / Disability / Death), and downloads any chart as PNG.</li>
</ul>

<h1 class="section">6. Features Included (Scope Definition)</h1>
<ul>
  <li>PDF upload with PyMuPDF text + bounding-box extraction (F1, P0).</li>
  <li>Single-screen profile intake stored in localStorage (F2, P0).</li>
  <li>Plain-language Policy X-Ray with side-by-side PDF page &harr; extracted fields (F3, P0).</li>
  <li>ClawView color-coded risk overlay on the original PDF, click-to-explain tooltips (F4, P0 &mdash; Wow Factor 1).</li>
  <li>Policy Health Score with four 0&ndash;25 sub-scores rendered as a 0&ndash;100 gauge (F5, P0).</li>
  <li>FutureClaw 10-year Monte Carlo with toggleable Affordability and Life Event modes (F6, P0 &mdash; Wow Factor 2).</li>
  <li>Recommendation Engine: verdict + 3 reasons + confidence + MYR impact + citations (F7, P0).</li>
  <li>Action Summary with jsPDF download in &lt;2s (F8, P0).</li>
  <li>Bahasa Malaysia / English bilingual output across all AI surfaces (F9, P1).</li>
  <li>Framer Motion polish and loading / error states (F10, P0).</li>
</ul>

<h1 class="section">7. Features Not Included (Scope Control)</h1>
<ul>
  <li>Real-time insurer API integration &mdash; no public APIs exist for Malaysian retail insurers in scope.</li>
  <li>Actual policy purchase or cancellation &mdash; regulatory boundary; the product is decision support, not transaction execution.</li>
  <li>Claims filing assistance.</li>
  <li>SME or business insurance &mdash; retail individual policies only.</li>
  <li>Native mobile applications &mdash; responsive web only.</li>
  <li>Voice interface &mdash; risk profile too high for a 24-hour build.</li>
  <li>Mandarin / Tamil / Hokkien language support &mdash; Bahasa Malaysia and English only for MVP.</li>
  <li>Deep takaful / Shariah-specific features &mdash; product remains generic across conventional and takaful policies.</li>
  <li>Production frontend deployment &mdash; localhost demo only; Supabase remains a ship target, not an MVP gate.</li>
</ul>

<h1 class="section">8. Assumptions &amp; Constraints</h1>
<ul>
  <li><span class="lead">LLM Cost Constraint.</span> Each full analysis fans out to four typed LLM calls (Extract, Annotate, Score, Recommend). gpt-5-mini was selected partly for cost. <em>Cost-control design decision:</em> the demo cache at <code>backend/data/demo_cache/</code> replays cached LLM responses on the demo path, so judging-day reruns of identical demo PDFs do not pay live tokens. Equally important, <span class="lead">no LLM call sits inside the FutureClaw slider loop</span> &mdash; sliders run pure numpy / scipy Monte Carlo, and the LLM is only invoked once per scenario change to regenerate the narrative interpretation. This keeps the most-interactive surface free of per-keystroke inference cost.</li>
  <li><span class="lead">Technical Constraints.</span> Text-native PDFs are first-class; scanned PDFs are best-effort and may degrade ClawView highlight alignment. PyMuPDF is required for bounding boxes (pypdf is insufficient). No database in MVP &mdash; in-memory backend state plus browser localStorage; Supabase (Postgres + pgvector + Auth + Storage + Realtime) is the ship target but explicitly not MVP-gating, so requirements that depend on it (Auth, RLS, PDPA deletion endpoint, Realtime streaming) are out of MVP scope.</li>
  <li><span class="lead">Performance Constraints.</span> PDF upload &rarr; preview rendered &le;2s; full analysis (4 LLM calls) &le;15s; FutureClaw slider update at 60 FPS / &lt;100ms; ClawView highlight render &le;500ms after analysis; Action Summary PDF generation &le;2s.</li>
  <li><span class="lead">User Input Assumptions.</span> The product is decision <em>support</em>, never licensed financial advice. A &quot;not financial advice&quot; disclaimer appears on every recommendation screen. The user always makes the final decision (Principle P3). When confidence is below threshold, the system explicitly recommends a licensed human advisor (Principle P4). No auto-purchase, no auto-cancel, no binding legal advice, no dark patterns (anti-principles).</li>
</ul>

<h1 class="section">9. Risks &amp; Questions Throughout Development</h1>
<ul>
  <li><span class="lead">LLM hallucination on extracted clauses.</span> A fabricated exclusion or sub-limit could mislead a user's verdict. <em>Mitigation:</em> Pydantic-typed outputs at every stage, mandatory citation for every claim (Principle P2), explicit confidence calibration, and a hard rule that low-confidence outputs route the user to a human advisor (Principle P4).</li>
  <li><span class="lead">ClawView highlight misalignment.</span> Bounding-box drift on certain PDFs (especially scans) could produce visually wrong overlays. <em>Mitigation:</em> Hour-18 critical cut point pre-defined &mdash; if highlights are not aligned by then, the build falls back to a side-pane risk list with page references; the wow factor degrades but the analysis still ships.</li>
  <li><span class="lead">Provider waiver risk.</span> The hackathon's original rubric required Z.AI GLM and would have disqualified other reasoning providers. The organizers waived this rule for PolicyClaw after the Ilmu gateway proved unstable. <em>Mitigation:</em> the waiver is documented in PRD &sect;1, CLAUDE.md, and the README so reviewers can pre-empt any rubric-based eligibility flag.</li>
  <li><span class="lead">Ilmu gateway instability.</span> The original provider's transport-layer instability under sustained streaming load was the root cause of the provider swap. <em>Mitigation:</em> already mitigated by the swap to OpenAI <code>gpt-5-mini</code>; <code>post_glm_with_retry</code> retains exponential-backoff resilience for any future provider change.</li>
  <li><span class="lead">24-hour scope risk.</span> A solo dev cannot recover from a 6-hour blocker discovered at Hour 20. <em>Mitigation:</em> two pre-defined critical cut points &mdash; at Hour 12, drop F9 (English-only), drop the Life Event mode, drop PDF download; at Hour 18, fall back to side-pane ClawView. Both keep the demo viable even if the wow factors are partially compromised.</li>
  <li><span class="lead">PDPA / privacy risk.</span> Insurance PDFs contain sensitive personal data. <em>Mitigation:</em> MVP keeps state session-only (in-memory backend + localStorage), with no persistent PII across sessions and no PII in logs (UUIDs only). The ship target adds Supabase Row Level Security and a single-endpoint PDPA deletion path; both are documented as ship-target, not MVP-gating.</li>
  <li><span class="lead">Demo wifi failure.</span> Hackathon venues drop wifi without warning. <em>Mitigation:</em> the local JSON demo cache replays the last good run end-to-end without network access, so the demo continues even on full connectivity loss.</li>
</ul>
"""


def build() -> Path:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    mediabox = fitz.paper_rect("a4")  # 595 x 842 pt
    margin_x = 50
    margin_top = 50
    margin_bottom = 60  # leave room for footer
    where = fitz.Rect(margin_x, margin_top, mediabox.width - margin_x, mediabox.height - margin_bottom)

    story = fitz.Story(html=HTML, user_css=CSS)
    writer = fitz.DocumentWriter(str(OUT_PATH))

    page_count = 0
    more = 1
    while more:
        device = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(device)
        writer.end_page()
        page_count += 1

    writer.close()

    # Pass 2: open the just-written PDF and stamp footers on every page.
    doc = fitz.open(str(OUT_PATH))
    footer_text = "© UMHackathon 2026   |   PolicyClaw PRD v2.2   |   Email: umhackathon@um.edu.my"
    for i, page in enumerate(doc, start=1):
        rect = fitz.Rect(margin_x, mediabox.height - 40, mediabox.width - margin_x, mediabox.height - 20)
        page.insert_textbox(
            rect,
            footer_text,
            fontsize=8,
            fontname="helv",
            color=(0.4, 0.4, 0.4),
            align=fitz.TEXT_ALIGN_CENTER,
        )
        # Skip page-number on cover page (page 1)
        if i > 1:
            num_rect = fitz.Rect(mediabox.width - margin_x - 40, mediabox.height - 30, mediabox.width - margin_x, mediabox.height - 18)
            page.insert_textbox(
                num_rect,
                f"Page {i} / {len(doc)}",
                fontsize=8,
                fontname="helv",
                color=(0.4, 0.4, 0.4),
                align=fitz.TEXT_ALIGN_RIGHT,
            )

    # Add an outline / TOC so judges can navigate. Resolve each section's
    # real page by string-matching against page text — keeps the outline
    # in sync if the body content shifts in future edits.
    # (probe-prefix, full-title-for-outline) — short prefixes match cleanly
    # even when long parenthetical titles wrap to a second line in the PDF.
    section_specs = [
        ("1. Project Overview", "1. Project Overview"),
        ("2. Background", "2. Background & Business Objective"),
        ("3. Product Purpose", "3. Product Purpose"),
        ("4. System Functionalities", "4. System Functionalities"),
        ("5. User Stories", "5. User Stories & Use Cases"),
        ("6. Features Included", "6. Features Included (Scope Definition)"),
        ("7. Features Not Included", "7. Features Not Included (Scope Control)"),
        ("8. Assumptions", "8. Assumptions & Constraints"),
        ("9. Risks", "9. Risks & Questions Throughout Development"),
    ]
    page_texts = [doc[i].get_text() for i in range(len(doc))]

    def find_first_page(probe: str) -> int:
        # Skip the TOC page (index 1) when locating the first body occurrence.
        for i, text in enumerate(page_texts):
            if i == 1:
                continue
            if probe in text:
                return i + 1
        return 3

    toc = [
        [1, "Cover", 1],
        [1, "Table of Contents", 2],
    ]
    for probe, title in section_specs:
        toc.append([1, title, find_first_page(probe)])
    doc.set_toc(toc)
    doc.saveIncr()
    doc.close()

    return OUT_PATH


if __name__ == "__main__":
    out = build()
    print(f"Wrote {out}")
