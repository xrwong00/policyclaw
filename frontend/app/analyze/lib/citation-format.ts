const SOURCE_LABELS: Record<string, string> = {
  policy_xray: "Policy X-Ray",
  health_score: "Health Score",
  key_clauses: "Key Clauses",
  narrative_en: "Narrative",
  narrative_bm: "Narrative (BM)",
  recommendation: "Recommendation",
  simulation: "Simulation",
  affordability: "Affordability",
  premium_stability: "Premium Stability",
  coverage_adequacy: "Coverage Adequacy",
  clarity_trust: "Clarity & Trust",
  overall: "Overall Score",
  reasons: "Reasons",
  verdict: "Verdict",
  gotcha_count: "Gotcha Count",
  confidence_score: "Confidence",
  source_page: "Page",
  plain_language_en: "Explanation",
};

const SCHEMA_TOKEN = /^[a-z][a-z0-9_]*$/;

function titleCase(token: string): string {
  return token
    .split("_")
    .map((p) => (p ? p[0].toUpperCase() + p.slice(1) : ""))
    .join(" ");
}

function labelFor(token: string): string {
  if (SOURCE_LABELS[token]) return SOURCE_LABELS[token];
  return titleCase(token);
}

export function formatCitationSource(raw: string): string {
  const trimmed = (raw ?? "").trim();
  if (!trimmed) return "Source";

  const tokens = trimmed.split(/\s+/);
  const allSchema = tokens.every((t) => SCHEMA_TOKEN.test(t));
  if (!allSchema) return trimmed;

  return tokens.map(labelFor).join(" — ");
}

export function formatCitationLocator(raw: string): string | null {
  const trimmed = (raw ?? "").trim();
  if (!trimmed) return null;

  const indexMatch = trimmed.match(/^([a-z][a-z0-9_]*)\[(\d+)\]$/);
  if (indexMatch) {
    const [, key, idx] = indexMatch;
    return `${labelFor(key)} #${Number(idx) + 1}`;
  }

  if (/^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$/.test(trimmed)) {
    return null;
  }

  if (SCHEMA_TOKEN.test(trimmed)) {
    return labelFor(trimmed);
  }

  return trimmed;
}
