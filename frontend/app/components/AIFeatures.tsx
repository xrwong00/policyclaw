"use client";

import { useEffect, useState } from "react";

interface AIStatus {
  ai_enabled: boolean;
  mode: "GLM API" | "Mock Data";
  model: string;
  features: string[];
}

/**
 * AIStatusBanner — Shows whether AI features are active (GLM) or in mock/development mode
 */
export function AIStatusBanner() {
  const [status, setStatus] = useState<AIStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"}/v1/ai/status`
        );
        if (res.ok) {
          const data = await res.json();
          setStatus(data);
        }
      } catch (e) {
        console.warn("Could not fetch AI status:", e);
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
  }, []);

  if (loading || !status) return null;

  if (status.ai_enabled) {
    return (
      <div className="ai-status-banner ai-enabled">
        <span>✓ AI features active (GLM-powered)</span>
      </div>
    );
  }

  return (
    <div className="ai-status-banner ai-mock">
      <span>ℹ Mock data mode (API key not configured)</span>
    </div>
  );
}

/**
 * PolicyXRayCard — Displays extracted policy information and plain-language clauses
 */
export function PolicyXRayCard({ policyId }: { policyId: string }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"}/v1/ai/policy-xray`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            insurer: "AIA",
            plan_name: "MyShield Pro",
            policy_type: "medical",
            annual_premium_myr: 1800,
            coverage_limit_myr: 100000,
            effective_date: "2023-01-15",
            age_now: 38,
            projected_income_monthly_myr: 8500,
            expected_income_growth_pct: 3.0,
          }),
        }
      );

      if (res.ok) {
        const result = await res.json();
        setData(result);
      } else {
        setError("Failed to analyze policy");
      }
    } catch (e) {
      setError("Error connecting to AI service");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-feature-card policy-xray">
      <h3>🔍 Policy X-Ray</h3>
      <p className="feature-description">
        Extract and translate policy clauses into plain language
      </p>

      <button onClick={handleAnalyze} disabled={loading} className="cta-button cta-secondary">
        {loading ? "Analyzing..." : "Analyze Policy"}
      </button>

      {error && <div className="error-message">{error}</div>}

      {data && (
        <div className="xray-results">
          <div className="result-section">
            <h4>Key Clauses ({data.key_clauses.length})</h4>
            {data.key_clauses.map((clause: any, idx: number) => (
              <div key={idx} className={`clause ${clause.gotcha_flag ? "gotcha" : ""}`}>
                <div className="clause-header">
                  {clause.gotcha_flag && <span className="gotcha-badge">⚠️</span>}
                  <strong>{clause.title}</strong>
                </div>
                <p className="plain-language">{clause.plain_language_en}</p>
                <small className="source-page">Page {clause.source_page}</small>
              </div>
            ))}
            <div className="confidence-badge">
              Confidence: {data.confidence_score.toFixed(1)}% ({data.confidence_band})
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * OverlapMapCard — Visualizes coverage overlap across policies
 */
export function OverlapMapCard({ policyCount }: { policyCount: number }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"}/v1/ai/overlap-map`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify([
            {
              insurer: "AIA",
              plan_name: "MyShield Pro",
              policy_type: "medical",
              annual_premium_myr: 1800,
              coverage_limit_myr: 100000,
              effective_date: "2023-01-15",
              age_now: 38,
              projected_income_monthly_myr: 8500,
              expected_income_growth_pct: 3.0,
            },
            {
              insurer: "Zurich",
              plan_name: "Assure Health Plus",
              policy_type: "medical",
              annual_premium_myr: 2100,
              coverage_limit_myr: 150000,
              effective_date: "2022-06-01",
              age_now: 38,
              projected_income_monthly_myr: 8500,
              expected_income_growth_pct: 3.0,
            },
          ]),
        }
      );

      if (res.ok) {
        const result = await res.json();
        setData(result);
      } else {
        setError("Failed to analyze overlap");
      }
    } catch (e) {
      setError("Error connecting to AI service");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-feature-card overlap-map">
      <h3>🔗 Overlap Map</h3>
      <p className="feature-description">
        Identify overlapping coverage across your policies
      </p>

      <button onClick={handleAnalyze} disabled={loading} className="cta-button cta-secondary">
        {loading ? "Analyzing..." : "Detect Overlaps"}
      </button>

      {error && <div className="error-message">{error}</div>}

      {data && (
        <div className="overlap-results">
          {data.overlap_zones.length > 0 ? (
            <>
              <div className="result-section">
                <h4>Coverage Overlaps</h4>
                {data.overlap_zones.map((zone: any, idx: number) => (
                  <div key={idx} className={`overlap-zone severity-${zone.severity}`}>
                    <div className="zone-header">
                      <strong>{zone.coverage_type}</strong>
                      <span className="severity-badge">{zone.severity}</span>
                    </div>
                    <p>Duplicate premium: RM {zone.duplicate_premium_yearly_myr.toFixed(2)}/year</p>
                  </div>
                ))}
              </div>

              <div className="savings-highlight">
                <strong>Potential Annual Savings: RM {data.total_potential_savings_yearly_myr.toFixed(2)}</strong>
                <p className="recommendation">{data.consolidation_recommendation}</p>
              </div>
            </>
          ) : (
            <p className="no-overlap">No overlapping coverage detected.</p>
          )}

          <div className="confidence-badge">
            Confidence: {data.confidence_score.toFixed(1)}% ({data.confidence_band})
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * BNMRightsScannerCard — Checks BNM protections and generates demand letters
 */
export function BNMRightsScannerCard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleScan = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"}/v1/ai/bnm-rights-scanner`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            insurer: "AIA",
            plan_name: "MyShield Pro",
            policy_type: "medical",
            annual_premium_myr: 1800,
            coverage_limit_myr: 100000,
            effective_date: "2023-01-15",
            age_now: 38,
            projected_income_monthly_myr: 8500,
            expected_income_growth_pct: 3.0,
          }),
        }
      );

      if (res.ok) {
        const result = await res.json();
        setData(result);
      } else {
        setError("Failed to scan BNM rights");
      }
    } catch (e) {
      setError("Error connecting to AI service");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-feature-card bnm-scanner">
      <h3>⚖️ BNM Rights Scanner</h3>
      <p className="feature-description">
        Check your eligibility for Bank Negara Malaysia protections
      </p>

      <button onClick={handleScan} disabled={loading} className="cta-button cta-secondary">
        {loading ? "Scanning..." : "Check BNM Rights"}
      </button>

      {error && <div className="error-message">{error}</div>}

      {data && (
        <div className="bnm-results">
          <div className="result-section">
            <h4>Applicable BNM Rights</h4>
            {data.applicable_rights.map((right: any, idx: number) => (
              <div key={idx} className={`bnm-right ${right.currently_applied ? "applied" : "unapplied"}`}>
                <div className="right-header">
                  <strong>{right.title}</strong>
                  <span className="status-badge">
                    {right.currently_applied ? "✓ Applied" : "⚠️ Unapplied"}
                  </span>
                </div>
                <p>{right.description}</p>
                {right.potential_savings_myr > 0 && (
                  <p className="savings">
                    Potential savings: RM {right.potential_savings_myr.toFixed(2)}
                  </p>
                )}
                <small>{right.bnm_circular_reference}</small>
              </div>
            ))}
          </div>

          {data.total_unapplied_savings_myr > 0 && (
            <div className="recommended-actions">
              <h4>Recommended Actions</h4>
              <ul>
                {data.recommended_actions.map((action: string, idx: number) => (
                  <li key={idx}>{action}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="confidence-badge">
            Confidence: {data.confidence_score.toFixed(1)}% ({data.confidence_band})
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * VoiceInterrogationCard — Ask questions about policies in multiple languages
 */
export function VoiceInterrogationCard() {
  const [transcript, setTranscript] = useState("");
  const [language, setLanguage] = useState("en");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAsk = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"}/v1/ai/voice-interrogation`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            transcript,
            language,
            policy_ids: [],
          }),
        }
      );

      if (res.ok) {
        const data = await res.json();
        setResult(data);
      } else {
        setError("Failed to process question");
      }
    } catch (e) {
      setError("Error connecting to AI service");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-feature-card voice-card">
      <h3>🎤 Ask About Your Policies</h3>
      <p className="feature-description">Ask questions in Bahasa, English, 中文, or Hokkien</p>

      <div className="voice-input-group">
        <textarea
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          placeholder="E.g., 'What does my policy cover?' or 'Polisi saya cover apa?'"
          disabled={loading}
          rows={3}
        />
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          disabled={loading}
        >
          <option value="en">English</option>
          <option value="bm">Bahasa Malaysia</option>
          <option value="zh">中文 (Mandarin)</option>
          <option value="hokkien">Hokkien</option>
        </select>
        <button
          onClick={handleAsk}
          disabled={loading || !transcript.trim()}
          className="cta-button cta-secondary"
        >
          {loading ? "Processing..." : "Get Answer"}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {result && (
        <div className="voice-result">
          <div className="result-answer">
            <h4>Answer</h4>
            <p>{result.answer_text}</p>
          </div>

          {result.citations && result.citations.length > 0 && (
            <div className="result-citations">
              <h4>Sources</h4>
              {result.citations.map((cite: any, idx: number) => (
                <div key={idx} className="citation">
                  <small>
                    <strong>{cite.source}</strong>: "{cite.quote}" ({cite.locator})
                  </small>
                </div>
              ))}
            </div>
          )}

          <div className="confidence-badge">
            Confidence: {result.confidence_score.toFixed(1)}%
          </div>
        </div>
      )}
    </div>
  );
}
