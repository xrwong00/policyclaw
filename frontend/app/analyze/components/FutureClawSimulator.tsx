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
    <section className="panel futureclaw">
      <header className="futureclaw-header">
        <div className="futureclaw-head-text">
          <p className="futureclaw-eyebrow">FutureClaw</p>
          <h2 className="futureclaw-title">10-year simulator</h2>
          <p className="futureclaw-sub">
            See how your premium scales with inflation, and how your policy holds up in a life-changing event.
          </p>
        </div>
        <ModeToggle mode={mode} onChange={setMode} />
      </header>

      <div>
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
    <div className="futureclaw-tabs" role="tablist" aria-label="Simulator mode">
      {TOGGLE_OPTIONS.map((opt) => {
        const active = mode === opt.id;
        return (
          <button
            key={opt.id}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(opt.id)}
            className={`futureclaw-tab${active ? " active" : ""}`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
