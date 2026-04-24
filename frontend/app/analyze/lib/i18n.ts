import type { Lang } from "./types";

type Dict = Record<string, string>;
type I18nDict = Record<Lang, Dict>;

export const dict: I18nDict = {
  en: {
    app_title: "PolicyClaw",
    app_subtitle: "AI-powered insurance decision intelligence for policyholders.",
    step1_title: "Upload Policy Documents",
    step2_title: "Review and Analyze",
    analyze_button: "Analyze Policy",
    analyzing: "Analyzing...",
    health_title: "Policy Health Score",
    health_coverage: "Coverage Adequacy",
    health_affordability: "Affordability",
    health_stability: "Premium Stability",
    health_clarity: "Clarity & Trust",
    verdict_title: "Decision",
    verdict_hold: "HOLD",
    verdict_downgrade: "DOWNGRADE",
    verdict_switch: "SWITCH",
    verdict_dump: "DUMP",
    verdict_add_rider: "ADD RIDER",
    reasons_title: "Top Reasons",
    confidence_label: "Confidence",
    impact_title: "10-Year MYR Impact",
    impact_premium: "Projected premium",
    impact_savings: "Potential savings",
    disclaimer:
      "Decision support only. PolicyClaw is not a licensed financial advisor.",
    download_action: "Download Action Summary",
    download_preparing: "Preparing PDF...",
    lang_label: "Language",
    cite_page: "Page",
    cached_badge: "Served from demo cache",
    annotations_limited: "Limited annotation mode — ClawView degraded.",
  },
  bm: {
    app_title: "PolicyClaw",
    app_subtitle: "Kecerdasan keputusan insurans berkuasa AI untuk pemegang polisi.",
    step1_title: "Muat Naik Dokumen Polisi",
    step2_title: "Semak dan Analisis",
    analyze_button: "Analisis Polisi",
    analyzing: "Menganalisis...",
    health_title: "Skor Kesihatan Polisi",
    health_coverage: "Kecukupan Perlindungan",
    health_affordability: "Kemampuan",
    health_stability: "Kestabilan Premium",
    health_clarity: "Kejelasan & Kepercayaan",
    verdict_title: "Keputusan",
    verdict_hold: "KEKALKAN",
    verdict_downgrade: "TURUN TARAF",
    verdict_switch: "TUKAR",
    verdict_dump: "LUPUSKAN",
    verdict_add_rider: "TAMBAH RIDER",
    reasons_title: "Sebab Utama",
    confidence_label: "Keyakinan",
    impact_title: "Kesan MYR 10 Tahun",
    impact_premium: "Unjuran premium",
    impact_savings: "Potensi penjimatan",
    disclaimer:
      "Sokongan keputusan sahaja. PolicyClaw bukan penasihat kewangan berlesen.",
    download_action: "Muat Turun Ringkasan Tindakan",
    download_preparing: "Menyediakan PDF...",
    lang_label: "Bahasa",
    cite_page: "Halaman",
    cached_badge: "Dihidangkan dari cache demo",
    annotations_limited: "Mod anotasi terhad — ClawView terdegradasi.",
  },
};

export function t(key: string, lang: Lang): string {
  return dict[lang]?.[key] ?? dict.en[key] ?? key;
}
