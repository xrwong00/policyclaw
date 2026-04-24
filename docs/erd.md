# PolicyClaw — Data Model (ERD)

Entity-relationship view of the Pydantic v2 schemas that flow between the
frontend, FastAPI backend, and the Ilmu GLM calls. These are the contracts
validated at every API boundary.

Source files: [`backend/app/schemas/`](../backend/app/schemas/).

---

## 1. Core contracts — `/api/analyze` pipeline

```mermaid
classDiagram
    class PolicyInput {
      +str insurer
      +str plan_name
      +PolicyType policy_type
      +float annual_premium_myr
      +float coverage_limit_myr
      +date effective_date
      +int age_now
      +float projected_income_monthly_myr
      +float expected_income_growth_pct
    }

    class PolicyXRayResponse {
      +str policy_id
      +str insurer
      +str plan_name
      +PolicyType policy_type
      +dict extracted_fields
      +List~PolicyClause~ key_clauses
      +int gotcha_count
      +float confidence_score
      +ConfidenceBand confidence_band
    }

    class PolicyClause {
      +str title
      +str original_text
      +str plain_language_en
      +str plain_language_bm
      +bool gotcha_flag
      +int source_page
    }

    class HealthScore {
      +int overall
      +int coverage_adequacy
      +int affordability
      +int premium_stability
      +int clarity_trust
      +str narrative_en
      +str narrative_bm
      +float confidence_score
      +ConfidenceBand confidence_band
    }

    class PolicyVerdict {
      +str policy_id
      +VerdictLabel verdict
      +float confidence_score
      +ConfidenceBand confidence_band
      +float projected_10y_premium_myr
      +float projected_10y_savings_myr
      +List~Reason~ reasons
      +str disclaimer
    }

    class Reason {
      +str title
      +str detail
    }

    class Citation {
      +str source
      +str quote
      +str locator
    }

    class AnalyzeResponse {
      +VerdictLabel verdict
      +float projected_savings
      +bool overlap_detected
      +bool bnm_rights_detected
      +float confidence_score
      +List~str~ summary_reasons
      +List~AnalysisCitation~ citations
      +List~Reason~ reasons
      +float projected_10y_premium_myr
      +float projected_10y_savings_myr
      +HealthScore health_score
      +str analysis_id
      +bool cached
      +bool needs_rider
    }

    class AnalysisCitation {
      +str source
      +int page
      +str excerpt
    }

    PolicyInput --> PolicyXRayResponse : Extract (GLM 1)
    PolicyXRayResponse --> HealthScore : Score (GLM 3)
    PolicyXRayResponse --> PolicyVerdict : Recommend (GLM 4)
    HealthScore --> PolicyVerdict : Recommend (GLM 4)
    PolicyXRayResponse "1" *-- "1..20" PolicyClause
    PolicyVerdict "1" *-- "2..5" Reason
    Reason "1" *-- "1" Citation
    AnalyzeResponse "1" *-- "0..1" HealthScore
    AnalyzeResponse "1" *-- "0..5" Reason
    AnalyzeResponse "1" *-- "1..12" AnalysisCitation
```

**Flow.** A user-supplied `PolicyInput` becomes a `PolicyXRayResponse`
(Extract), which feeds `HealthScore` (Score). Both flow into `PolicyVerdict`
(Recommend). The outer envelope delivered to the frontend is `AnalyzeResponse`.

---

## 2. ClawView (F4) — PDF risk overlay

```mermaid
classDiagram
    class BoundingBox {
      +int page
      +float x0
      +float y0
      +float x1
      +float y1
    }

    class ClawViewAnnotation {
      +str clause_id
      +BoundingBox bbox
      +RiskLevel risk_level
      +str plain_explanation_en
      +str plain_explanation_bm
      +str why_this_matters
      +int source_page
    }

    class ClawViewResponse {
      +str policy_id
      +List~ClawViewAnnotation~ annotations
      +int red_count
      +int yellow_count
      +int green_count
      +float confidence_score
      +ConfidenceBand confidence_band
    }

    ClawViewResponse "1" *-- "1..*" ClawViewAnnotation
    ClawViewAnnotation "1" *-- "1" BoundingBox
```

`RiskLevel` is `GREEN | YELLOW | RED`. `red_count + yellow_count + green_count`
must equal `len(annotations)` — invariant enforced by Pydantic validators in
`clawview_service.py`.

---

## 3. FutureClaw (F6) — simulation outputs

```mermaid
classDiagram
    class ScenarioProjection {
      +Literal scenario
      +float annual_inflation_pct
      +List~float~ yearly_premium_myr
      +float cumulative_10y_myr
      +int breakpoint_year
    }

    class PremiumSimulationResponse {
      +str policy_id
      +List~ScenarioProjection~ scenarios
    }

    class LifeEventScenario {
      +LifeEvent event
      +float total_event_cost_myr
      +float covered_myr
      +float copay_myr
      +float out_of_pocket_myr
      +float months_income_at_risk
      +float alternative_out_of_pocket_myr
      +str narrative_en
      +str narrative_bm
    }

    class LifeEventSimulationResponse {
      +str policy_id
      +List~LifeEventScenario~ scenarios
      +List~Citation~ data_citations
      +float confidence_score
      +ConfidenceBand confidence_band
    }

    PremiumSimulationResponse "1" *-- "3" ScenarioProjection
    LifeEventSimulationResponse "1" *-- "4" LifeEventScenario
    LifeEventSimulationResponse "1" *-- "1..*" Citation
```

Affordability emits exactly 3 scenarios (optimistic / realistic / pessimistic),
life-event exactly 4 (Cancer / Heart Attack / Disability / Death).

---

## 4. Shared enums

| Enum            | Values                                                        |
|-----------------|---------------------------------------------------------------|
| `PolicyType`    | `medical`, `life`, `critical_illness`, `takaful`, `other`     |
| `CoverageCategory` | `hospitalization`, `critical_illness`, `death_benefit`, `disability`, `outpatient`, `dental`, `maternity` |
| `ConfidenceBand` | `high` (≥80), `medium` (≥60), `low` (<60)                    |
| `VerdictLabel`  | `keep`, `downgrade`, `switch`, `dump`                         |
| `RiskLevel`     | `green`, `yellow`, `red`                                      |
| `LifeEvent`     | `cancer`, `heart_attack`, `disability`, `death`               |

---

## 5. Persistence note

MVP holds no durable state: extracted profiles live in browser `localStorage`
and demo-cache lookups are file-based (`backend/data/demo_cache/`). Supabase
(Postgres + Storage + pgvector) is the post-MVP ship target and is explicitly
non-MVP-gating per PRD §9.2. The schemas above are designed to map cleanly to
relational rows when that time comes.
