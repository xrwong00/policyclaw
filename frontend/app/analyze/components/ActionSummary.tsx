"use client";

import { useState } from "react";

import type { AnalyzeResponse, Lang } from "../lib/types";
import { t } from "../lib/i18n";

interface ActionSummaryProps {
  result: AnalyzeResponse;
  lang: Lang;
}

function topActions(result: AnalyzeResponse, lang: Lang): string[] {
  const actions: string[] = [];
  const verdictText =
    result.verdict === "keep"
      ? result.needs_rider
        ? lang === "bm"
          ? "Tambah rider yang dicadangkan untuk menutup jurang perlindungan."
          : "Add the suggested rider to close the coverage gap."
        : lang === "bm"
          ? "Kekalkan polisi tetapi semak semula dalam 12 bulan."
          : "Hold the policy but review again within 12 months."
      : result.verdict === "downgrade"
        ? lang === "bm"
          ? "Hubungi penanggung insurans untuk pilihan premium yang lebih rendah."
          : "Contact the insurer for a lower-premium variant."
        : result.verdict === "switch"
          ? lang === "bm"
            ? "Bandingkan 3 polisi alternatif sebelum tempoh pembaharuan."
            : "Compare 3 alternative policies before your renewal date."
          : lang === "bm"
            ? "Hentikan polisi selepas mendapatkan perlindungan pengganti."
            : "Terminate the policy only after you have replacement coverage in place.";
  actions.push(verdictText);

  if (result.bnm_rights_detected) {
    actions.push(
      lang === "bm"
        ? "Mohon perlindungan had 10% BNM dengan surat tuntutan yang dihasilkan."
        : "Request BNM's 10% premium cap via the generated demand letter.",
    );
  }

  actions.push(
    lang === "bm"
      ? "Muat turun ringkasan ini dan kongsikan dengan penasihat yang dipercayai."
      : "Download this summary and share it with a trusted advisor before acting.",
  );

  return actions.slice(0, 3);
}

async function buildPdf(result: AnalyzeResponse, lang: Lang): Promise<Blob> {
  const { jsPDF } = await import("jspdf");
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const left = 48;
  let y = 56;

  doc.setFont("helvetica", "bold");
  doc.setFontSize(22);
  doc.text(t("app_title", lang), left, y);
  y += 26;

  doc.setFont("helvetica", "normal");
  doc.setFontSize(11);
  doc.text(t("app_subtitle", lang), left, y);
  y += 24;

  doc.setFont("helvetica", "bold");
  doc.setFontSize(14);
  doc.text(t("verdict_title", lang), left, y);
  y += 18;

  const verdictText =
    result.needs_rider && result.verdict === "keep"
      ? t("verdict_add_rider", lang)
      : result.verdict === "keep"
        ? t("verdict_hold", lang)
        : result.verdict === "downgrade"
          ? t("verdict_downgrade", lang)
          : result.verdict === "switch"
            ? t("verdict_switch", lang)
            : t("verdict_dump", lang);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(18);
  doc.text(verdictText, left, y);
  y += 24;

  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.text(
    `${t("confidence_label", lang)}: ${result.confidence_score.toFixed(0)}%`,
    left,
    y,
  );
  y += 14;
  doc.text(
    `${t("impact_savings", lang)}: MYR ${Math.round(result.projected_10y_savings_myr).toLocaleString()}`,
    left,
    y,
  );
  y += 14;
  doc.text(
    `${t("impact_premium", lang)}: MYR ${Math.round(result.projected_10y_premium_myr).toLocaleString()}`,
    left,
    y,
  );
  y += 20;

  // A4 page height is 842pt; reserve ~60pt for the fixed footer.
  const PAGE_BOTTOM = 780;
  const newPage = () => {
    doc.addPage();
    y = 56;
  };
  const ensureRoom = (lines: number) => {
    if (y + lines * 12 > PAGE_BOTTOM) newPage();
  };

  doc.setFont("helvetica", "bold");
  doc.setFontSize(12);
  doc.text(t("reasons_title", lang), left, y);
  y += 16;

  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  for (const reason of result.reasons.slice(0, 3)) {
    const line = `• ${reason.title}: ${reason.detail}`;
    const wrapped = doc.splitTextToSize(line, 500);
    ensureRoom(wrapped.length + 4);
    doc.text(wrapped, left, y);
    y += wrapped.length * 12 + 4;
    const cite = `   "${reason.citation.quote}" — ${reason.citation.source}`;
    const citeWrapped = doc.splitTextToSize(cite, 500);
    ensureRoom(citeWrapped.length + 1);
    doc.setFont("helvetica", "italic");
    doc.text(citeWrapped, left, y);
    doc.setFont("helvetica", "normal");
    y += citeWrapped.length * 12 + 8;
  }

  ensureRoom(3);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(12);
  doc.text(lang === "bm" ? "Tindakan Disyorkan" : "Recommended Actions", left, y);
  y += 16;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  for (const action of topActions(result, lang)) {
    const wrapped = doc.splitTextToSize(`• ${action}`, 500);
    ensureRoom(wrapped.length + 1);
    doc.text(wrapped, left, y);
    y += wrapped.length * 12 + 4;
  }

  // Footer on every page — disclaimer + analysis_id.
  const pageCount = doc.getNumberOfPages();
  doc.setFontSize(8);
  doc.setTextColor(100);
  for (let page = 1; page <= pageCount; page += 1) {
    doc.setPage(page);
    doc.text(t("disclaimer", lang), left, 800);
    doc.text(`Analysis ID: ${result.analysis_id}`, left, 814);
  }

  return doc.output("blob");
}

export default function ActionSummary({ result, lang }: ActionSummaryProps) {
  const [busy, setBusy] = useState(false);

  async function handleDownload() {
    setBusy(true);
    try {
      const blob = await buildPdf(result, lang);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `policyclaw-${result.analysis_id || "summary"}.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      // Delay revoke so browsers that resolve blob URLs asynchronously
      // (Firefox, some WebKit versions) still have a valid URL to fetch.
      setTimeout(() => URL.revokeObjectURL(url), 2000);
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      type="button"
      onClick={handleDownload}
      disabled={busy}
      style={{
        padding: "10px 18px",
        borderRadius: 8,
        border: "1px solid rgba(0,0,0,0.12)",
        background: busy ? "#e5e7eb" : "#111",
        color: busy ? "#374151" : "#fff",
        fontWeight: 600,
        cursor: busy ? "wait" : "pointer",
      }}
    >
      {busy ? t("download_preparing", lang) : t("download_action", lang)}
    </button>
  );
}
