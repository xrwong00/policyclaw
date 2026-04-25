"use client";

import type { AnalyzeResponse, Lang, Reason, VerdictLabel } from "../lib/types";
import { t } from "../lib/i18n";
import { formatCitationLocator, formatCitationSource } from "../lib/citation-format";

interface VerdictCardProps {
  result: AnalyzeResponse;
  lang: Lang;
}

interface PillStyle {
  dot: string;
  bg: string;
  fg: string;
}

function verdictStyle(verdict: VerdictLabel, needsRider: boolean): PillStyle {
  if (needsRider && verdict === "keep") {
    return { dot: "⚫", bg: "#1f2937", fg: "#f3f4f6" };
  }
  switch (verdict) {
    case "keep":
      return { dot: "🟢", bg: "#dcfce7", fg: "#166534" };
    case "downgrade":
      return { dot: "🟡", bg: "#fef9c3", fg: "#854d0e" };
    case "switch":
      return { dot: "🔴", bg: "#fee2e2", fg: "#991b1b" };
    case "dump":
      return { dot: "⛔", bg: "#fee2e2", fg: "#7f1d1d" };
  }
}

function verdictLabel(verdict: VerdictLabel, needsRider: boolean, lang: Lang): string {
  if (needsRider && verdict === "keep") return t("verdict_add_rider", lang);
  switch (verdict) {
    case "keep":
      return t("verdict_hold", lang);
    case "downgrade":
      return t("verdict_downgrade", lang);
    case "switch":
      return t("verdict_switch", lang);
    case "dump":
      return t("verdict_dump", lang);
  }
}

function formatMYR(value: number): string {
  return new Intl.NumberFormat("en-MY", {
    style: "currency",
    currency: "MYR",
    maximumFractionDigits: 0,
  }).format(value);
}

function ReasonRow({ reason }: { reason: Reason }) {
  const source = formatCitationSource(reason.citation.source);
  const locator = formatCitationLocator(reason.citation.locator);
  return (
    <li style={{ marginBottom: 14 }}>
      <strong style={{ display: "block", marginBottom: 4 }}>{reason.title}</strong>
      <span style={{ display: "block", fontSize: 14, lineHeight: 1.5 }}>
        {reason.detail}
      </span>
      <small style={{ display: "block", marginTop: 4, opacity: 0.7, fontSize: 12 }}>
        <em>&ldquo;{reason.citation.quote}&rdquo;</em> — {source}
        {locator ? ` (${locator})` : ""}
      </small>
    </li>
  );
}

export default function VerdictCard({ result, lang }: VerdictCardProps) {
  const style = verdictStyle(result.verdict, result.needs_rider);
  const label = verdictLabel(result.verdict, result.needs_rider, lang);
  const topReasons = result.reasons.slice(0, 3);

  return (
    <article className="panel" aria-label={t("verdict_title", lang)}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          justifyContent: "space-between",
          flexWrap: "wrap",
        }}
      >
        <h2 style={{ margin: 0 }}>{t("verdict_title", lang)}</h2>
        <span
          style={{
            padding: "6px 14px",
            borderRadius: 999,
            background: style.bg,
            color: style.fg,
            fontWeight: 700,
            fontSize: 14,
            letterSpacing: 0.5,
          }}
        >
          {style.dot} {label}
        </span>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 12,
          marginTop: 16,
        }}
      >
        <div>
          <small style={{ opacity: 0.7 }}>{t("confidence_label", lang)}</small>
          <strong style={{ display: "block", fontSize: 20 }}>
            {result.confidence_score.toFixed(0)}%
          </strong>
        </div>
        <div>
          <small style={{ opacity: 0.7 }}>{t("impact_savings", lang)}</small>
          <strong style={{ display: "block", fontSize: 20 }}>
            {formatMYR(result.projected_10y_savings_myr)}
          </strong>
        </div>
        <div style={{ gridColumn: "1 / -1" }}>
          <small style={{ opacity: 0.7 }}>{t("impact_premium", lang)}</small>
          <strong style={{ display: "block", fontSize: 16 }}>
            {formatMYR(result.projected_10y_premium_myr)}
          </strong>
        </div>
      </div>

      <h3 style={{ marginTop: 20, marginBottom: 8, fontSize: 15 }}>
        {t("reasons_title", lang)}
      </h3>
      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {topReasons.map((reason, index) => (
          <ReasonRow key={`${reason.title}-${index}`} reason={reason} />
        ))}
      </ul>

      <p
        role="note"
        style={{
          marginTop: 16,
          padding: "10px 12px",
          borderRadius: 8,
          background: "rgba(0,0,0,0.04)",
          fontSize: 12,
          lineHeight: 1.4,
          opacity: 0.8,
        }}
      >
        {t("disclaimer", lang)}
      </p>
    </article>
  );
}
