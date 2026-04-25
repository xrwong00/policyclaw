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

const CLAWVIEW_CLIENT_TIMEOUT_MS = 150_000;

async function fetchClawViewOnce(file: File): Promise<Response> {
  const form = new FormData();
  form.append("file", file);

  return fetch(`${API_BASE}/v1/clawview`, {
    method: "POST",
    body: form,
    signal: AbortSignal.timeout(CLAWVIEW_CLIENT_TIMEOUT_MS),
  });
}

function isNetworkError(err: unknown): boolean {
  // Browser fetch throws TypeError for network-level failures ("Failed to fetch",
  // DNS errors, server closed connection). AbortSignal.timeout fires DOMException
  // with name "TimeoutError" — treat both as retryable network errors.
  if (err instanceof TypeError) return true;
  if (err instanceof DOMException && err.name === "TimeoutError") return true;
  return false;
}

export async function postClawView(file: File): Promise<ClawViewResponse> {
  let res: Response;
  try {
    res = await fetchClawViewOnce(file);
  } catch (err) {
    if (!isNetworkError(err)) throw err;
    await new Promise((resolve) => setTimeout(resolve, 500));
    try {
      res = await fetchClawViewOnce(file);
    } catch (retryErr) {
      if (!isNetworkError(retryErr)) throw retryErr;
      throw new Error(
        `ClawView request failed: network error — is the backend running at ${API_BASE}?`
      );
    }
  }

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
