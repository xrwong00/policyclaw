"use client";

import type { HealthScore, Lang } from "../lib/types";
import { t } from "../lib/i18n";

interface HealthScoreGaugeProps {
  score: HealthScore;
  lang: Lang;
}

const GAUGE_SIZE = 180;
const STROKE_WIDTH = 16;
const RADIUS = (GAUGE_SIZE - STROKE_WIDTH) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

function gaugeColor(overall: number): string {
  if (overall >= 70) return "#22c55e";
  if (overall >= 50) return "#eab308";
  return "#ef4444";
}

function SubScoreBar({
  label,
  value,
  max,
}: {
  label: string;
  value: number;
  max: number;
}) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div style={{ marginBottom: 12 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 13,
          marginBottom: 4,
        }}
      >
        <span>{label}</span>
        <span style={{ fontVariantNumeric: "tabular-nums" }}>
          {value} / {max}
        </span>
      </div>
      <div
        style={{
          height: 8,
          width: "100%",
          borderRadius: 4,
          background: "rgba(0,0,0,0.08)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${pct}%`,
            background:
              pct >= 70
                ? "#22c55e"
                : pct >= 50
                  ? "#eab308"
                  : "#ef4444",
            transition: "width 300ms ease-out",
          }}
        />
      </div>
    </div>
  );
}

export default function HealthScoreGauge({ score, lang }: HealthScoreGaugeProps) {
  const overall = Math.max(0, Math.min(100, score.overall));
  const strokeDashoffset = CIRCUMFERENCE * (1 - overall / 100);
  const color = gaugeColor(overall);
  const narrative = lang === "bm" ? score.narrative_bm : score.narrative_en;

  return (
    <article
      className="panel"
      aria-label={t("health_title", lang)}
      style={{ display: "flex", gap: 32, alignItems: "center", flexWrap: "wrap" }}
    >
      <div style={{ position: "relative", width: GAUGE_SIZE, height: GAUGE_SIZE }}>
        <svg width={GAUGE_SIZE} height={GAUGE_SIZE} aria-hidden="true">
          <circle
            cx={GAUGE_SIZE / 2}
            cy={GAUGE_SIZE / 2}
            r={RADIUS}
            fill="none"
            stroke="rgba(0,0,0,0.08)"
            strokeWidth={STROKE_WIDTH}
          />
          <circle
            cx={GAUGE_SIZE / 2}
            cy={GAUGE_SIZE / 2}
            r={RADIUS}
            fill="none"
            stroke={color}
            strokeWidth={STROKE_WIDTH}
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            transform={`rotate(-90 ${GAUGE_SIZE / 2} ${GAUGE_SIZE / 2})`}
            style={{ transition: "stroke-dashoffset 600ms ease-out" }}
          />
        </svg>
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
          }}
          aria-live="polite"
        >
          <span
            style={{ fontSize: 42, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}
          >
            {overall}
          </span>
          <span style={{ fontSize: 12, opacity: 0.7 }}>/ 100</span>
        </div>
      </div>
      <div style={{ flex: "1 1 260px", minWidth: 240 }}>
        <h2 style={{ margin: 0, marginBottom: 12 }}>{t("health_title", lang)}</h2>
        <SubScoreBar label={t("health_coverage", lang)} value={score.coverage_adequacy} max={25} />
        <SubScoreBar label={t("health_affordability", lang)} value={score.affordability} max={25} />
        <SubScoreBar label={t("health_stability", lang)} value={score.premium_stability} max={25} />
        <SubScoreBar label={t("health_clarity", lang)} value={score.clarity_trust} max={25} />
        <p style={{ marginTop: 12, fontSize: 13, lineHeight: 1.5, opacity: 0.85 }}>
          {narrative}
        </p>
      </div>
    </article>
  );
}
