"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

import AffordabilitySimulator from "./AffordabilitySimulator";
import LifeEventSimulator from "./LifeEventSimulator";

export interface PolicyProfile {
  insurer: string;
  plan_name: string;
  policy_type: "medical" | "life" | "critical_illness" | "takaful" | "other";
  annual_premium_myr: number;
  coverage_limit_myr: number;
  effective_date: string;
  age_now: number;
  projected_income_monthly_myr: number;
  expected_income_growth_pct: number;
}

export interface FutureClawSimulatorProps {
  policyId: string;
  profile: PolicyProfile;
}

type SimMode = "affordability" | "life_event";

const TOGGLE_OPTIONS: { id: SimMode; label: string }[] = [
  { id: "affordability", label: "Affordability" },
  { id: "life_event", label: "Life Event" },
];

export default function FutureClawSimulator({ policyId, profile }: FutureClawSimulatorProps) {
  const [mode, setMode] = useState<SimMode>("affordability");

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-950/60 p-6 text-slate-100">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-widest text-emerald-400">FutureClaw</p>
          <h2 className="text-xl font-semibold">10-year simulator</h2>
          <p className="mt-1 text-sm text-slate-400">
            See how your premium scales with inflation, and how your policy holds up in a life-changing event.
          </p>
        </div>
        <ModeToggle mode={mode} onChange={setMode} />
      </header>

      <div className="mt-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={mode}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.18 }}
          >
            {mode === "affordability" ? (
              <AffordabilitySimulator policyId={policyId} profile={profile} />
            ) : (
              <LifeEventSimulator policyId={policyId} profile={profile} />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
}

interface ModeToggleProps {
  mode: SimMode;
  onChange: (next: SimMode) => void;
}

function ModeToggle({ mode, onChange }: ModeToggleProps) {
  return (
    <div className="relative flex items-center gap-1 rounded-full border border-slate-700 bg-slate-900 p-1">
      {TOGGLE_OPTIONS.map((opt) => {
        const active = mode === opt.id;
        return (
          <button
            key={opt.id}
            type="button"
            onClick={() => onChange(opt.id)}
            className="relative z-10 rounded-full px-4 py-1.5 text-sm font-medium transition-colors"
            style={{ color: active ? "#020617" : "#cbd5e1" }}
          >
            {active && (
              <motion.span
                layoutId="futureclaw-toggle-pill"
                className="absolute inset-0 -z-10 rounded-full bg-emerald-400"
                transition={{ type: "spring", stiffness: 400, damping: 32 }}
              />
            )}
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
