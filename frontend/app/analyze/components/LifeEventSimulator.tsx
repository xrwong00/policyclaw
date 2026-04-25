"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { PolicyProfile } from "./FutureClawSimulator";
import { exportSvgAsPng } from "./chartExport";

type LifeEventId = "cancer" | "heart_attack" | "disability" | "death";
type Lang = "en" | "bm";

interface LifeEventScenario {
  event: LifeEventId;
  total_event_cost_myr: number;
  covered_myr: number;
  copay_myr: number;
  out_of_pocket_myr: number;
  months_income_at_risk: number;
  alternative_out_of_pocket_myr: number | null;
  narrative_en: string;
  narrative_bm: string;
}

interface LifeEventCitation {
  source: string;
  quote: string;
  locator: string;
}

interface LifeEventSimulationResponse {
  policy_id: string;
  scenarios: LifeEventScenario[];
  data_citations: LifeEventCitation[];
  confidence_score: number;
  confidence_band: "high" | "medium" | "low";
}

interface LifeEventSimulatorProps {
  policyId: string;
  profile: PolicyProfile;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
const EVENTS: LifeEventId[] = ["cancer", "heart_attack", "disability", "death"];
const EVENT_LABELS: Record<LifeEventId, string> = {
  cancer: "Cancer",
  heart_attack: "Heart Attack",
  disability: "Disability",
  death: "Death of Primary Earner",
};

function formatMyr(value: unknown): string {
  const num = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(num)) return "—";
  return `RM${num.toLocaleString("en", { maximumFractionDigits: 0 })}`;
}

interface ChartRow {
  label: string;
  covered: number;
  copay: number;
  out_of_pocket: number;
}

function buildChartRows(scenario: LifeEventScenario | null, alternativeOn: boolean): ChartRow[] {
  if (!scenario) return [];
  const rows: ChartRow[] = [
    {
      label: "Current policy",
      covered: scenario.covered_myr,
      copay: scenario.copay_myr,
      out_of_pocket: scenario.out_of_pocket_myr,
    },
  ];
  if (alternativeOn && scenario.alternative_out_of_pocket_myr !== null) {
    const altCovered = Math.max(
      scenario.total_event_cost_myr - scenario.alternative_out_of_pocket_myr - scenario.copay_myr,
      0,
    );
    rows.push({
      label: "Alternative policy",
      covered: altCovered,
      copay: scenario.copay_myr,
      out_of_pocket: scenario.alternative_out_of_pocket_myr,
    });
  }
  return rows;
}

export default function LifeEventSimulator({ policyId, profile }: LifeEventSimulatorProps) {
  const [selected, setSelected] = useState<LifeEventId>("cancer");
  const [lang, setLang] = useState<Lang>("en");
  const [alternativeOn, setAlternativeOn] = useState<boolean>(false);
  const [data, setData] = useState<LifeEventSimulationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    const body: Record<string, unknown> = { profile, policy_id: policyId };
    if (alternativeOn) {
      body.alternative_coverage_limit_myr = profile.coverage_limit_myr * 2;
    }

    fetch(`${API_BASE}/v1/simulate/life-event`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return (await res.json()) as LifeEventSimulationResponse;
      })
      .then((resp) => {
        if (!cancelled) setData(resp);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [profile, policyId, alternativeOn]);

  const selectedScenario = useMemo(
    () => data?.scenarios.find((s) => s.event === selected) ?? null,
    [data, selected],
  );

  const chartRows = useMemo(
    () => buildChartRows(selectedScenario, alternativeOn),
    [selectedScenario, alternativeOn],
  );

  const onExport = useCallback(() => {
    const svg = chartRef.current?.querySelector("svg");
    if (svg) exportSvgAsPng(svg as SVGElement, `policyclaw-lifeevent-${selected}.png`);
  }, [selected]);

  return (
    <div className="futureclaw-grid-lifeevent">
      <aside className="futureclaw-aside">
        <div>
          <p className="event-section-label">Pick an event</p>
          <div className="event-list">
            {EVENTS.map((ev) => {
              const active = selected === ev;
              return (
                <button
                  key={ev}
                  type="button"
                  onClick={() => setSelected(ev)}
                  className={`event-button${active ? " active" : ""}`}
                >
                  {EVENT_LABELS[ev]}
                </button>
              );
            })}
          </div>
        </div>

        <label className="alt-toggle">
          <input
            type="checkbox"
            checked={alternativeOn}
            onChange={(e) => setAlternativeOn(e.target.checked)}
          />
          <span className="alt-toggle-label">
            Compare alternative policy
            <span className="alt-toggle-sub">2× current coverage limit</span>
          </span>
        </label>

        <div className="lang-toggle">
          {(["en", "bm"] as const).map((code) => {
            const active = lang === code;
            return (
              <button
                key={code}
                type="button"
                onClick={() => setLang(code)}
                className={`lang-button${active ? " active" : ""}`}
              >
                {code.toUpperCase()}
              </button>
            );
          })}
        </div>
      </aside>

      <div>
        <div ref={chartRef} className="futureclaw-chart-wrap">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartRows} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid stroke="rgba(16, 36, 30, 0.1)" strokeDasharray="3 3" />
              <XAxis dataKey="label" stroke="#39574c" tickLine={false} />
              <YAxis
                stroke="#39574c"
                tickLine={false}
                tickFormatter={(v: number) => `RM${(v / 1000).toFixed(0)}k`}
              />
              <Tooltip
                contentStyle={{
                  background: "rgba(255, 255, 255, 0.96)",
                  border: "1px solid rgba(16, 36, 30, 0.14)",
                  borderRadius: 10,
                  color: "#10241e",
                }}
                formatter={(value) => formatMyr(value)}
              />
              <Legend />
              <Bar dataKey="covered" stackId="a" fill="#2f7a3d" name="Covered" />
              <Bar dataKey="copay" stackId="a" fill="#b87a22" name="Co-pay" />
              <Bar dataKey="out_of_pocket" stackId="a" fill="#c84f33" name="Out of pocket" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="futureclaw-status-row">
          <span className="futureclaw-status">
            {loading
              ? "Generating narrative via gpt-5-mini…"
              : data
                ? "Costs sourced from LIAM / PIAM / MTA"
                : "Awaiting simulation"}
          </span>
          {error && <span className="futureclaw-error">{error}</span>}
          <button type="button" onClick={onExport} className="futureclaw-export">
            Export PNG
          </button>
        </div>

        {selectedScenario && (
          <div className="futureclaw-result-grid">
            <div className="futureclaw-risk-card">
              <p className="futureclaw-risk-label">Months of income at risk</p>
              <p className="futureclaw-risk-value">{selectedScenario.months_income_at_risk.toFixed(1)}</p>
            </div>
            <AnimatePresence mode="wait">
              <motion.p
                key={`${selected}-${lang}-${alternativeOn}`}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.18 }}
                className="futureclaw-narrative"
              >
                {lang === "en" ? selectedScenario.narrative_en : selectedScenario.narrative_bm}
              </motion.p>
            </AnimatePresence>
          </div>
        )}

        {data && (
          <details className="futureclaw-citations">
            <summary>
              Citations ({data.data_citations.length}) · confidence {data.confidence_band} (
              {data.confidence_score.toFixed(0)}/100)
            </summary>
            <ul>
              {data.data_citations.map((c, i) => (
                <li key={`${c.source}-${i}`}>
                  <strong>{c.source}</strong> — {c.locator}
                  <span className="futureclaw-citations-quote">&ldquo;{c.quote}&rdquo;</span>
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </div>
  );
}
