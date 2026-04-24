"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { PolicyProfile } from "./FutureClawSimulator";
import { exportSvgAsPng } from "./chartExport";

interface ScenarioProjection {
  scenario: "optimistic" | "realistic" | "pessimistic";
  annual_inflation_pct: number;
  yearly_premium_myr: number[];
  cumulative_10y_myr: number;
  breakpoint_year: number | null;
}

interface PremiumSimulationResponse {
  policy_id: string;
  scenarios: ScenarioProjection[];
}

interface AffordabilitySimulatorProps {
  policyId: string;
  profile: PolicyProfile;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
const DEFAULT_INFLATION_PCT = 13.5;
const YEARS = 10;
const BACKEND_DEBOUNCE_MS = 160;

function formatMyr(value: unknown): string {
  const num = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(num)) return "—";
  return `RM${num.toLocaleString("en", { maximumFractionDigits: 0 })}`;
}

function buildScenario(
  label: ScenarioProjection["scenario"],
  premium: number,
  incomeAnnual: number,
  inflationPct: number,
  incomeGrowthPct: number,
): ScenarioProjection {
  const yearly: number[] = [];
  let current = premium;
  let breakpoint: number | null = null;
  let income = incomeAnnual;
  for (let y = 1; y <= YEARS; y++) {
    current = current * (1 + inflationPct / 100);
    yearly.push(Math.round(current * 100) / 100);
    if (breakpoint === null && current / income > 0.1) breakpoint = y;
    income = income * (1 + incomeGrowthPct / 100);
  }
  return {
    scenario: label,
    annual_inflation_pct: inflationPct,
    yearly_premium_myr: yearly,
    cumulative_10y_myr: Math.round(yearly.reduce((a, b) => a + b, 0) * 100) / 100,
    breakpoint_year: breakpoint,
  };
}

function localPreviewBands(
  premium: number,
  incomeAnnual: number,
  inflationPct: number,
  incomeGrowthPct: number,
): ScenarioProjection[] {
  return [
    buildScenario("optimistic", premium, incomeAnnual, Math.max(inflationPct - 2, 0), incomeGrowthPct),
    buildScenario("realistic", premium, incomeAnnual, inflationPct, incomeGrowthPct),
    buildScenario("pessimistic", premium, incomeAnnual, inflationPct + 2, incomeGrowthPct),
  ];
}

interface ChartRow {
  year: number;
  optimistic?: number;
  realistic?: number;
  pessimistic?: number;
}

function scenariosToChartRows(scenarios: ScenarioProjection[]): ChartRow[] {
  const by = new Map(scenarios.map((s) => [s.scenario, s]));
  const rows: ChartRow[] = [];
  for (let y = 0; y < YEARS; y++) {
    rows.push({
      year: y + 1,
      optimistic: by.get("optimistic")?.yearly_premium_myr[y],
      realistic: by.get("realistic")?.yearly_premium_myr[y],
      pessimistic: by.get("pessimistic")?.yearly_premium_myr[y],
    });
  }
  return rows;
}

export default function AffordabilitySimulator({ policyId, profile }: AffordabilitySimulatorProps) {
  const [inflationPct, setInflationPct] = useState<number>(DEFAULT_INFLATION_PCT);
  const [incomeGrowthPct, setIncomeGrowthPct] = useState<number>(profile.expected_income_growth_pct);
  const [mcScenarios, setMcScenarios] = useState<ScenarioProjection[] | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const chartRef = useRef<HTMLDivElement>(null);

  const incomeAnnual = profile.projected_income_monthly_myr * 12;
  const incomeThreshold = incomeAnnual * 0.1;

  useEffect(() => {
    let cancelled = false;
    const handle = setTimeout(() => {
      if (cancelled) return;
      setLoading(true);
      setError(null);
      fetch(`${API_BASE}/v1/simulate/affordability`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          profile,
          medical_inflation_pct: inflationPct,
          income_growth_pct: incomeGrowthPct,
          policy_id: policyId,
        }),
      })
        .then(async (res) => {
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          return (await res.json()) as PremiumSimulationResponse;
        })
        .then((resp) => {
          if (cancelled) return;
          setMcScenarios(resp.scenarios);
        })
        .catch((err: unknown) => {
          if (cancelled) return;
          setError(err instanceof Error ? err.message : "Simulation failed");
        })
        .finally(() => {
          if (cancelled) return;
          setLoading(false);
        });
    }, BACKEND_DEBOUNCE_MS);
    return () => {
      cancelled = true;
      clearTimeout(handle);
    };
  }, [profile, inflationPct, incomeGrowthPct, policyId]);

  const displayScenarios = useMemo<ScenarioProjection[]>(() => {
    if (mcScenarios) return mcScenarios;
    return localPreviewBands(profile.annual_premium_myr, incomeAnnual, inflationPct, incomeGrowthPct);
  }, [mcScenarios, profile.annual_premium_myr, incomeAnnual, inflationPct, incomeGrowthPct]);

  const previewScenarios = useMemo<ScenarioProjection[]>(
    () => localPreviewBands(profile.annual_premium_myr, incomeAnnual, inflationPct, incomeGrowthPct),
    [profile.annual_premium_myr, incomeAnnual, inflationPct, incomeGrowthPct],
  );

  const chartRows = scenariosToChartRows(loading ? previewScenarios : displayScenarios);
  const realistic = (loading ? previewScenarios : displayScenarios).find((s) => s.scenario === "realistic");
  const dangerYear = realistic?.breakpoint_year ?? null;
  const cumulative = realistic?.cumulative_10y_myr ?? 0;

  const onExport = useCallback(() => {
    const svg = chartRef.current?.querySelector("svg");
    if (svg) exportSvgAsPng(svg as SVGElement, `policyclaw-affordability-${policyId}.png`);
  }, [policyId]);

  return (
    <div className="grid gap-6 md:grid-cols-[minmax(0,1fr)_260px]">
      <div>
        {dangerYear !== null && (
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200"
          >
            Premium exceeds 10% of income by year <strong>{dangerYear}</strong> under the realistic scenario.
          </motion.div>
        )}
        <div ref={chartRef} className="h-80 w-full rounded-lg border border-slate-800 bg-slate-900/50 p-3">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartRows} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
              <XAxis dataKey="year" stroke="#94a3b8" tickLine={false} />
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
              <ReferenceLine
                y={incomeThreshold}
                stroke="#ef4444"
                strokeDasharray="5 3"
                label={{ value: "10% of income", fill: "#fca5a5", fontSize: 11, position: "insideTopRight" }}
              />
              <Line type="monotone" dataKey="optimistic" stroke="#34d399" strokeWidth={2} dot={false} name="Optimistic" />
              <Line type="monotone" dataKey="realistic" stroke="#f59e0b" strokeWidth={2.5} dot={false} name="Realistic" />
              <Line type="monotone" dataKey="pessimistic" stroke="#ef4444" strokeWidth={2} dot={false} name="Pessimistic" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
          <span>
            {loading
              ? "Re-running 1000-run Monte Carlo…"
              : mcScenarios
                ? "1000-run Monte Carlo — BNM 2014–2024 anchor"
                : "Live preview — Monte Carlo pending"}
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
      </div>

      <aside className="space-y-5">
        <SliderField
          label="Medical inflation"
          value={inflationPct}
          onChange={setInflationPct}
          min={3}
          max={20}
          step={0.5}
          unit="%"
        />
        <SliderField
          label="Income growth"
          value={incomeGrowthPct}
          onChange={setIncomeGrowthPct}
          min={0}
          max={8}
          step={0.25}
          unit="%"
        />
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 text-sm">
          <p className="text-xs uppercase tracking-widest text-slate-400">10-year cumulative (realistic)</p>
          <p className="mt-1 text-2xl font-semibold text-emerald-300">
            RM {cumulative.toLocaleString("en", { maximumFractionDigits: 0 })}
          </p>
          <p className="mt-2 text-xs text-slate-500">
            Source: BNM Financial Stability Review — medical inflation 2014–2024.
          </p>
        </div>
      </aside>
    </div>
  );
}

interface SliderFieldProps {
  label: string;
  value: number;
  onChange: (next: number) => void;
  min: number;
  max: number;
  step: number;
  unit: string;
}

function SliderField({ label, value, onChange, min, max, step, unit }: SliderFieldProps) {
  return (
    <label className="block">
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-300">{label}</span>
        <span className="font-mono text-emerald-300">
          {value.toFixed(2)}
          {unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="mt-2 w-full accent-emerald-400"
      />
      <div className="mt-1 flex justify-between text-xs text-slate-500">
        <span>
          {min}
          {unit}
        </span>
        <span>
          {max}
          {unit}
        </span>
      </div>
    </label>
  );
}
