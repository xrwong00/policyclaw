"use client";

import { DragEvent, FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import dynamic from "next/dynamic";

import ActionSummary from "./components/ActionSummary";
import ErrorBoundary from "./components/ErrorBoundary";
import FutureClawSimulator, {
  type PolicyProfile as FutureClawProfile,
} from "./components/FutureClawSimulator";
import HealthScoreGauge from "./components/HealthScoreGauge";
import LanguageToggle from "./components/LanguageToggle";
import VerdictCard from "./components/VerdictCard";
import { t } from "./lib/i18n";
import { useLangStore } from "./lib/store";
import type { AnalyzeResponse } from "./lib/types";
import { postClawView, type ClawViewResponse } from "@/lib/api";

const PdfViewer = dynamic(
  () => import("./components/PdfViewer").then((m) => m.PdfViewer),
  {
    ssr: false,
    loading: () => (
      <p style={{ margin: 0, opacity: 0.7 }}>Loading PDF viewer…</p>
    ),
  },
);

type FormState = {
  insurer_name: string;
  policyholder_name: string;
  plan_name: string;
  policy_type: string;
  premium_amount: string;
  premium_frequency: string;
  currency: string;
  effective_date: string;
  renewal_date: string;
  coverage_limit: string;
  riders: string;
  age_now: string;
  projected_income_monthly_myr: string;
  expected_income_growth_pct: string;
};

type ExtractedPolicyProfile = {
  option_id: string;
  display_label: string;
  insurer_name?: string | null;
  policyholder_name?: string | null;
  plan_name?: string | null;
  policy_type?: "medical" | "life" | "critical_illness" | "takaful" | "other" | null;
  premium_amount?: number | null;
  premium_frequency?: "monthly" | "annual" | null;
  currency?: string | null;
  effective_date?: string | null;
  renewal_date?: string | null;
  coverage_limit?: number | null;
  riders?: string[];
  source_pages?: number[];
  confidence_score?: number | null;
};

type ExtractPolicyProfileResponse = {
  profiles: ExtractedPolicyProfile[];
  detected_count: number;
  notes: string[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

const emptyForm: FormState = {
  insurer_name: "",
  policyholder_name: "",
  plan_name: "",
  policy_type: "",
  premium_amount: "",
  premium_frequency: "",
  currency: "",
  effective_date: "",
  renewal_date: "",
  coverage_limit: "",
  riders: "",
  age_now: "",
  projected_income_monthly_myr: "",
  expected_income_growth_pct: "3",
};

function applyProfileToForm(current: FormState, profile: ExtractedPolicyProfile): FormState {
  return {
    ...current,
    insurer_name: profile.insurer_name ?? "",
    policyholder_name: profile.policyholder_name ?? "",
    plan_name: profile.plan_name ?? "",
    policy_type: profile.policy_type ?? "",
    premium_amount:
      typeof profile.premium_amount === "number" ? String(profile.premium_amount) : "",
    premium_frequency: profile.premium_frequency ?? "",
    currency: profile.currency ?? "",
    effective_date: profile.effective_date ?? "",
    renewal_date: profile.renewal_date ?? "",
    coverage_limit:
      typeof profile.coverage_limit === "number" ? String(profile.coverage_limit) : "",
    riders: profile.riders?.join(", ") ?? "",
  };
}

function profileFromForm(form: FormState): FutureClawProfile {
  const parseFloatOr = (raw: string, fallback: number): number => {
    const n = Number.parseFloat(raw);
    return Number.isFinite(n) && n > 0 ? n : fallback;
  };
  const parseIntOr = (raw: string, fallback: number): number => {
    const n = Number.parseInt(raw, 10);
    return Number.isFinite(n) ? n : fallback;
  };

  const rawType = (form.policy_type || "medical").toLowerCase();
  const policyType: FutureClawProfile["policy_type"] =
    rawType === "medical" ||
    rawType === "life" ||
    rawType === "critical_illness" ||
    rawType === "takaful" ||
    rawType === "other"
      ? rawType
      : "medical";

  return {
    insurer: form.insurer_name || "Unknown Insurer",
    plan_name: form.plan_name || "Unknown Plan",
    policy_type: policyType,
    annual_premium_myr: parseFloatOr(form.premium_amount, 3600),
    coverage_limit_myr: parseFloatOr(form.coverage_limit, 500000),
    effective_date: form.effective_date || new Date().toISOString().slice(0, 10),
    age_now: parseIntOr(form.age_now, 38),
    projected_income_monthly_myr: parseFloatOr(form.projected_income_monthly_myr, 6000),
    expected_income_growth_pct: parseFloatOr(form.expected_income_growth_pct, 3),
  };
}

export default function AnalyzeWorkflow() {
  const lang = useLangStore((s) => s.lang);

  const [form, setForm] = useState<FormState>(emptyForm);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [detectedProfiles, setDetectedProfiles] = useState<ExtractedPolicyProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState("");
  const [status, setStatus] = useState("Ready");
  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [isDragActive, setIsDragActive] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [clawView, setClawView] = useState<ClawViewResponse | null>(null);
  const [clawViewLoading, setClawViewLoading] = useState(false);
  const [clawViewError, setClawViewError] = useState<string | null>(null);
  // Monotonic request token — any in-flight ClawView request whose token
  // no longer matches is discarded, so a slow response for an older upload
  // cannot clobber the annotations of the current one.
  const clawViewRequestIdRef = useRef(0);

  const fileNames = useMemo(
    () => selectedFiles.map((file) => file.name).join(", "),
    [selectedFiles]
  );

  const pdfObjectUrl = useMemo(() => {
    const first = selectedFiles[0];
    if (!first) return null;
    return URL.createObjectURL(first);
  }, [selectedFiles]);

  useEffect(() => {
    return () => {
      if (pdfObjectUrl) {
        URL.revokeObjectURL(pdfObjectUrl);
      }
    };
  }, [pdfObjectUrl]);

  const populateFromUpload = async (files: File[]) => {
    setExtracting(true);
    setStatus("Extracting policy fields from PDF...");
    setError(null);

    try {
      const formData = new FormData();
      for (const file of files) {
        formData.append("files", file);
      }

      const response = await fetch(`${API_BASE}/api/extract-policy-profile`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const details = await response.text();
        throw new Error(`Extraction failed (${response.status}): ${details}`);
      }

      const payload = (await response.json()) as ExtractPolicyProfileResponse;
      setDetectedProfiles(payload.profiles);

      const first = payload.profiles[0];
      if (first) {
        setSelectedProfileId(first.option_id);
        setForm((current) => applyProfileToForm(current, first));
      } else {
        // Extractor produced no candidates — clear any stale fields from a
        // previous upload so the next /api/analyze isn't seeded by the old
        // policy's metadata.
        setSelectedProfileId("");
        setForm((current) => ({
          ...current,
          insurer_name: "",
          policyholder_name: "",
          plan_name: "",
          policy_type: "",
          premium_amount: "",
          premium_frequency: "",
          currency: "",
          effective_date: "",
          renewal_date: "",
          coverage_limit: "",
          riders: "",
        }));
      }

      setStatus(
        payload.profiles.length > 1
          ? `Detected ${payload.profiles.length} policy options. Review and choose one.`
          : payload.profiles.length === 1
            ? "Policy fields detected. Review and confirm before analysis."
            : "No policy fields detected. Fill in Step 2 manually."
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown extraction error";
      setError(message);
      setDetectedProfiles([]);
      setSelectedProfileId("");
      setStatus("Extraction failed");
    } finally {
      setExtracting(false);
    }
  };

  const onFileChosen = (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;
    const incoming = Array.from(fileList);
    const valid = incoming.filter((file) => file.type === "application/pdf");
    if (valid.length !== incoming.length) {
      setError("Only PDF files are accepted.");
      return;
    }
    setSelectedFiles(valid);
    setResult(null);
    setClawView(null);
    setClawViewError(null);
    // Invalidate any in-flight ClawView request from a previous file.
    clawViewRequestIdRef.current += 1;
    void populateFromUpload(valid);
  };

  const onProfileChange = (nextId: string) => {
    setSelectedProfileId(nextId);
    const chosen = detectedProfiles.find((item) => item.option_id === nextId);
    if (!chosen) return;
    setForm((current) => applyProfileToForm(current, chosen));
  };

  const onDragOver = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setIsDragActive(true);
  };

  const onDragLeave = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setIsDragActive(false);
  };

  const onDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setIsDragActive(false);
    onFileChosen(event.dataTransfer.files);
  };

  const fetchClawView = async (file: File) => {
    const requestId = ++clawViewRequestIdRef.current;
    setClawViewLoading(true);
    setClawViewError(null);
    try {
      const data = await postClawView(file);
      // Discard response if another request has since superseded this one
      // (e.g. user uploaded a different PDF and re-ran Analyze mid-flight).
      if (requestId !== clawViewRequestIdRef.current) return;
      setClawView(data);
    } catch (err) {
      if (requestId !== clawViewRequestIdRef.current) return;
      setClawView(null);
      setClawViewError(err instanceof Error ? err.message : "ClawView failed");
    } finally {
      if (requestId === clawViewRequestIdRef.current) {
        setClawViewLoading(false);
      }
    }
  };

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (selectedFiles.length === 0) {
      setError("Please upload at least one policy PDF first.");
      return;
    }
    if (!form.projected_income_monthly_myr) {
      setError("Please fill monthly income before analysis.");
      return;
    }
    if (!form.age_now) {
      setError("Please fill your age before analysis.");
      return;
    }

    setLoading(true);
    setError(null);
    setStatus("Running AI analysis...");

    try {
      const formData = new FormData();
      for (const file of selectedFiles) {
        formData.append("files", file);
      }

      if (form.insurer_name) formData.append("insurer", form.insurer_name);
      if (form.policyholder_name) formData.append("policyholder_name", form.policyholder_name);
      if (form.plan_name) formData.append("plan_name", form.plan_name);
      if (form.policy_type) formData.append("policy_type", form.policy_type);
      if (form.premium_amount) formData.append("annual_premium_myr", form.premium_amount);
      if (form.premium_frequency) formData.append("premium_frequency", form.premium_frequency);
      if (form.currency) formData.append("currency", form.currency);
      if (form.coverage_limit) formData.append("coverage_limit_myr", form.coverage_limit);
      if (form.effective_date) formData.append("effective_date", form.effective_date);
      if (form.renewal_date) formData.append("renewal_date", form.renewal_date);
      if (form.riders) formData.append("riders", form.riders);
      if (form.age_now) formData.append("age_now", form.age_now);
      if (form.projected_income_monthly_myr)
        formData.append("projected_income_monthly_myr", form.projected_income_monthly_myr);
      if (form.expected_income_growth_pct)
        formData.append("expected_income_growth_pct", form.expected_income_growth_pct);

      const response = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        const details = await response.text();
        throw new Error(`Analysis failed (${response.status}): ${details}`);
      }

      const payload = (await response.json()) as AnalyzeResponse;
      setResult(payload);
      setStatus("Analysis complete");

      // Fire the 4th LLM call (ClawView Annotate) — runs in parallel with user review.
      const firstFile = selectedFiles[0];
      if (firstFile) {
        void fetchClawView(firstFile);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown analysis error";
      setError(message);
      setResult(null);
      setStatus("Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page">
      <section
        className="hero"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 16,
          flexWrap: "wrap",
        }}
      >
        <div>
          <p className="eyebrow">{t("app_title", lang)}</p>
          <p className="subtitle">{t("app_subtitle", lang)}</p>
        </div>
        <LanguageToggle />
      </section>

      <section className="flow-grid">
        <motion.article
          className="panel step-card"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
        >
          <div className="step-head">
            <span className="step-index">Step 1</span>
            <h2>{t("step1_title", lang)}</h2>
          </div>
          <p className="step-note">Upload PDF(s). Fields are auto-detected and loaded into Step 2.</p>
          <label
            htmlFor="policy-upload"
            className={`dropzone ${isDragActive ? "drag-active" : ""}`}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
          >
            <input
              id="policy-upload"
              type="file"
              accept="application/pdf"
              multiple
              onChange={(e) => onFileChosen(e.target.files)}
            />
            <span className="dropzone-title">Drop PDF(s) here or click to browse</span>
            <span className="dropzone-sub">Max 10MB per file, up to 5 policies.</span>
            {selectedFiles.length > 0 && (
              <span className="dropzone-file">Selected: {fileNames}</span>
            )}
          </label>
          {extracting && <p className="status">Extracting fields...</p>}
        </motion.article>

        <motion.article
          className="panel step-card"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: 0.08 }}
        >
          <div className="step-head">
            <span className="step-index">Step 2</span>
            <h2>{t("step2_title", lang)}</h2>
          </div>
          <p className="step-note">Confirm detected fields. Not detected values remain editable.</p>

          {detectedProfiles.length > 1 && (
            <label>
              Detected Policy Options
              <select value={selectedProfileId} onChange={(e) => onProfileChange(e.target.value)}>
                {detectedProfiles.map((profile) => (
                  <option key={profile.option_id} value={profile.option_id}>
                    {profile.display_label}
                  </option>
                ))}
              </select>
            </label>
          )}

          <form className="grid" onSubmit={onSubmit}>
            <label>
              Insurer Name
              <input
                value={form.insurer_name}
                onChange={(e) => setForm({ ...form, insurer_name: e.target.value })}
                placeholder="Not detected"
              />
            </label>
            <label>
              Policyholder Name
              <input
                value={form.policyholder_name}
                onChange={(e) => setForm({ ...form, policyholder_name: e.target.value })}
                placeholder="Not detected"
              />
            </label>
            <label>
              Plan Name
              <input
                value={form.plan_name}
                onChange={(e) => setForm({ ...form, plan_name: e.target.value })}
                placeholder="Not detected"
              />
            </label>
            <label>
              Policy Type
              <select
                value={form.policy_type}
                onChange={(e) => setForm({ ...form, policy_type: e.target.value })}
              >
                <option value="">Not detected</option>
                <option value="medical">Medical</option>
                <option value="life">Life</option>
                <option value="critical_illness">Critical Illness</option>
                <option value="takaful">Takaful</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label>
              Premium Amount
              <input
                type="number"
                min={0}
                value={form.premium_amount}
                onChange={(e) => setForm({ ...form, premium_amount: e.target.value })}
                placeholder="Not detected"
              />
            </label>
            <label>
              Premium Frequency
              <select
                value={form.premium_frequency}
                onChange={(e) => setForm({ ...form, premium_frequency: e.target.value })}
              >
                <option value="">Not detected</option>
                <option value="monthly">Monthly</option>
                <option value="annual">Annual</option>
              </select>
            </label>
            <label>
              Currency
              <input
                value={form.currency}
                onChange={(e) => setForm({ ...form, currency: e.target.value.toUpperCase() })}
                placeholder="Not detected"
              />
            </label>
            <label>
              Effective Date / Start Date
              <input
                type="date"
                value={form.effective_date}
                onChange={(e) => setForm({ ...form, effective_date: e.target.value })}
              />
            </label>
            <label>
              Renewal Date
              <input
                type="date"
                value={form.renewal_date}
                onChange={(e) => setForm({ ...form, renewal_date: e.target.value })}
              />
            </label>
            <label>
              Coverage Limit
              <input
                type="number"
                min={0}
                value={form.coverage_limit}
                onChange={(e) => setForm({ ...form, coverage_limit: e.target.value })}
                placeholder="Not detected"
              />
            </label>
            <label>
              Riders / Add-ons
              <input
                value={form.riders}
                onChange={(e) => setForm({ ...form, riders: e.target.value })}
                placeholder="Not detected"
              />
            </label>
            <label>
              Age Now
              <input
                type="number"
                min={18}
                max={100}
                value={form.age_now}
                onChange={(e) => setForm({ ...form, age_now: e.target.value })}
                required
              />
            </label>
            <label>
              Monthly Income
              <input
                type="number"
                min={0}
                value={form.projected_income_monthly_myr}
                onChange={(e) =>
                  setForm({ ...form, projected_income_monthly_myr: e.target.value })
                }
                required
              />
            </label>
            <label>
              Expected Income Growth %
              <input
                type="number"
                min={0}
                max={20}
                step="0.1"
                value={form.expected_income_growth_pct}
                onChange={(e) =>
                  setForm({ ...form, expected_income_growth_pct: e.target.value })
                }
              />
            </label>
          </form>
          <div style={{ display: "flex", justifyContent: "center", marginTop: "1.5rem" }}>
            <button
              type="button"
              onClick={(e) => {
                const formEl = e.currentTarget.closest(".step-card")?.querySelector("form");
                if (formEl) {
                  formEl.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
                }
              }}
              disabled={loading || extracting}
              style={{ minWidth: 220 }}
            >
              {loading ? t("analyzing", lang) : t("analyze_button", lang)}
            </button>
          </div>
        </motion.article>
      </section>

      <p className="status">Status: {status}</p>
      {error && (
        <p className="status" role="alert">
          Error: {error}
        </p>
      )}

      {loading && (
        <section className="results" aria-busy="true">
          <article className="panel">
            <div
              style={{
                height: 180,
                background:
                  "linear-gradient(90deg, rgba(0,0,0,0.05), rgba(0,0,0,0.1), rgba(0,0,0,0.05))",
                backgroundSize: "200% 100%",
                animation: "shimmer 1.4s infinite",
                borderRadius: 12,
              }}
            />
          </article>
        </section>
      )}

      <AnimatePresence>
        {result && !loading && (
          <motion.section
            className="results"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3 }}
            style={{ display: "flex", flexDirection: "column", gap: 20 }}
          >
            {result.cached && (
              <p
                role="status"
                style={{
                  alignSelf: "flex-start",
                  padding: "4px 10px",
                  background: "#fef9c3",
                  color: "#854d0e",
                  borderRadius: 999,
                  fontSize: 12,
                  fontWeight: 600,
                }}
              >
                {t("cached_badge", lang)}
              </p>
            )}

            <ErrorBoundary
              fallback={<article className="panel">ClawView could not render.</article>}
              resetKey={result.analysis_id}
            >
              {pdfObjectUrl && clawView ? (
                <article className="panel" style={{ padding: 0, overflow: "hidden" }}>
                  <PdfViewer fileUrl={pdfObjectUrl} annotations={clawView.annotations} />
                </article>
              ) : (
                <article className="panel">
                  <h3 style={{ marginTop: 0 }}>ClawView</h3>
                  {clawViewLoading && (
                    <p style={{ margin: 0, opacity: 0.7 }}>Loading PDF annotations…</p>
                  )}
                  {clawViewError && (
                    <div role="alert">
                      <p style={{ margin: 0, color: "#b91c1c" }}>
                        ClawView error: {clawViewError}
                      </p>
                      {selectedFiles[0] && (
                        <button
                          type="button"
                          style={{ marginTop: 12 }}
                          onClick={() => void fetchClawView(selectedFiles[0])}
                          disabled={clawViewLoading}
                        >
                          {clawViewLoading ? "Retrying…" : "Retry ClawView"}
                        </button>
                      )}
                    </div>
                  )}
                  {!clawViewLoading && !clawViewError && !clawView && (
                    <p style={{ margin: 0, opacity: 0.7 }}>
                      ClawView annotations are loading separately.
                    </p>
                  )}
                </article>
              )}
            </ErrorBoundary>

            {result.health_score && (
              <ErrorBoundary
                fallback={<article className="panel">Health score unavailable.</article>}
                resetKey={result.analysis_id}
              >
                <HealthScoreGauge score={result.health_score} lang={lang} />
              </ErrorBoundary>
            )}

            <ErrorBoundary
              fallback={<article className="panel">Future simulator unavailable.</article>}
              resetKey={result.analysis_id}
            >
              <FutureClawSimulator
                policyId={`${form.insurer_name}-${form.plan_name}`.toLowerCase().replace(/\s+/g, "-") || "current"}
                profile={profileFromForm(form)}
              />
            </ErrorBoundary>

            <VerdictCard result={result} lang={lang} />

            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <ActionSummary result={result} lang={lang} />
            </div>
          </motion.section>
        )}
      </AnimatePresence>
    </main>
  );
}
