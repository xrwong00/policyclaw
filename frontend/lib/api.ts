const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type BoundingBox = {
  page: number;
  x0: number;
  y0: number;
  x1: number;
  y1: number;
};

export type RiskLevel = "green" | "yellow" | "red";

export type ConfidenceBand = "high" | "medium" | "low";

export type ClawViewAnnotation = {
  clause_id: string;
  bbox: BoundingBox;
  risk_level: RiskLevel;
  plain_explanation_en: string;
  plain_explanation_bm: string;
  why_this_matters: string;
  source_page: number;
};

export type ClawViewResponse = {
  policy_id: string;
  annotations: ClawViewAnnotation[];
  red_count: number;
  yellow_count: number;
  green_count: number;
  confidence_score: number;
  confidence_band: ConfidenceBand;
};

export async function postClawView(file: File): Promise<ClawViewResponse> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/v1/clawview`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(
      `ClawView request failed: ${res.status} ${res.statusText}${
        detail ? ` — ${detail}` : ""
      }`
    );
  }

  return (await res.json()) as ClawViewResponse;
}
