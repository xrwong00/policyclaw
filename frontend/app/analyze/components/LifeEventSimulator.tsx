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
    <div className="grid gap-6 md:grid-cols-[260px_minmax(0,1fr)]">
      <aside className="space-y-5">
        <div>
          <p className="text-xs uppercase tracking-widest text-slate-400">Pick an event</p>
          <div className="mt-2 grid gap-2">
            {EVENTS.map((ev) => {
              const active = selected === ev;
              return (
                <button
                  key={ev}
                  type="button"
                  onClick={() => setSelected(ev)}
                  className={`rounded-lg border px-3 py-2 text-left text-sm transition-colors ${
                    active
                      ? "border-emerald-400 bg-emerald-400/10 text-emerald-200"
                      : "border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-500"
                  }`}
                >
                  {EVENT_LABELS[ev]}
                </button>
              );
            })}
          </div>
        </div>

        <label className="flex items-start gap-2 text-sm text-slate-300">
          <input
            type="checkbox"
            checked={alternativeOn}
            onChange={(e) => setAlternativeOn(e.target.checked)}
            className="mt-0.5 h-4 w-4 accent-emerald-400"
          />
          <span>
            Compare alternative policy
            <span className="block text-xs text-slate-500">2× current coverage limit</span>
          </span>
        </label>

        <div className="flex gap-2 text-xs">
          {(["en", "bm"] as const).map((code) => {
            const active = lang === code;
            return (
              <button
                key={code}
                type="button"
                onClick={() => setLang(code)}
                className={`rounded-full border px-3 py-1 transition-colors ${
                  active ? "border-emerald-400 text-emerald-200" : "border-slate-700 text-slate-400"
                }`}
              >
                {code.toUpperCase()}
              </button>
            );
          })}
        </div>
      </aside>

      <div>
        <div ref={chartRef} className="h-72 w-full rounded-lg border border-slate-800 bg-slate-900/50 p-3">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartRows} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
              <XAxis dataKey="label" stroke="#94a3b8" tickLine={false} />
              <YAxis
                stroke="#94a3b8"
                tickLine={false}
                tickFormatter={(v: number) => `RM${(v / 1000).toFixed(0)}k`}
              />
              <Tooltip
                contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }}
                formatter={(value) => formatMyr(value)}
              />
              <Legend />
              <Bar dataKey="covered" stackId="a" fill="#34d399" name="Covered" />
              <Bar dataKey="copay" stackId="a" fill="#f59e0b" name="Co-pay" />
              <Bar dataKey="out_of_pocket" stackId="a" fill="#ef4444" name="Out of pocket" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
          <span>
            {loading
              ? "Generating narrative via GLM…"
              : data
                ? "Costs sourced from LIAM / PIAM / MTA"
                : "Awaiting simulation"}
          </span>
          {error && <span className="text-red-300">{error}</span>}
          <button
            type="button"
            onClick={onExport}
            className="rounded border border-slate-700 px-3 py-1 text-slate-200 transition-colors hover:bg-slate-800"
          >
            Export PNG
          </button>
        </div>

        {selectedScenario && (
          <div className="mt-4 grid gap-4 md:grid-cols-[auto_1fr]">
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
              <p className="text-xs uppercase tracking-widest text-red-300">Months of income at risk</p>
              <p className="mt-1 text-2xl font-semibold">{selectedScenario.months_income_at_risk.toFixed(1)}</p>
            </div>
            <AnimatePresence mode="wait">
              <motion.p
                key={`${selected}-${lang}-${alternativeOn}`}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.18 }}
                className="rounded-lg border border-slate-800 bg-slate-950/60 px-4 py-3 text-sm leading-relaxed text-slate-200"
              >
                {lang === "en" ? selectedScenario.narrative_en : selectedScenario.narrative_bm}
              </motion.p>
            </AnimatePresence>
          </div>
        )}

        {data && (
          <details className="mt-4 rounded-lg border border-slate-800 bg-slate-900/40 px-4 py-3 text-xs text-slate-400">
            <summary className="cursor-pointer text-slate-300">
              Citations ({data.data_citations.length}) · confidence {data.confidence_band} (
              {data.confidence_score.toFixed(0)}/100)
            </summary>
            <ul className="mt-2 space-y-1.5">
              {data.data_citations.map((c, i) => (
                <li key={`${c.source}-${i}`}>
                  <strong className="text-slate-300">{c.source}</strong> — {c.locator}
                  <div className="text-slate-500">&ldquo;{c.quote}&rdquo;</div>
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </div>
  );
}
