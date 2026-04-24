// ClawView types live in `frontend/lib/api.ts` where `postClawView` is defined.
// Re-export so components can import everything from one place.
export type {
  BoundingBox,
  ClawViewAnnotation,
  ClawViewResponse,
  ConfidenceBand,
  RiskLevel,
} from "../../../lib/api";

export type Lang = "en" | "bm";

export type VerdictLabel = "keep" | "downgrade" | "switch" | "dump";

export interface AnalysisCitation {
  source: string;
  page: number;
  excerpt: string;
}

export interface ReasonCitation {
  source: string;
  quote: string;
  locator: string;
}

export interface Reason {
  title: string;
  detail: string;
  citation: ReasonCitation;
}

export interface HealthScore {
  overall: number;
  coverage_adequacy: number;
  affordability: number;
  premium_stability: number;
  clarity_trust: number;
  narrative_en: string;
  narrative_bm: string;
  confidence_score: number;
  confidence_band: "high" | "medium" | "low";
}

export interface AnalyzeResponse {
  verdict: VerdictLabel;
  projected_savings: number;
  overlap_detected: boolean;
  bnm_rights_detected: boolean;
  confidence_score: number;
  summary_reasons: string[];
  citations: AnalysisCitation[];

  reasons: Reason[];
  projected_10y_premium_myr: number;
  projected_10y_savings_myr: number;
  health_score: HealthScore | null;
  analysis_id: string;
  cached: boolean;
  needs_rider: boolean;
}
