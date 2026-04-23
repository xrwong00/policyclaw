"use client";

import { DragEvent, FormEvent, useMemo, useState } from "react";

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
  projected_income_monthly_myr: string;
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

type AnalysisCitation = {
  source: string;
  page: number;
  excerpt: string;
};

type AnalyzeResponse = {
  verdict: "keep" | "downgrade" | "switch" | "dump";
  projected_savings: number;
  overlap_detected: boolean;
  bnm_rights_detected: boolean;
  confidence_score: number;
  summary_reasons: string[];
  citations: AnalysisCitation[];
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
  projected_income_monthly_myr: "",
};

function verdictClass(value: string): string {
  if (value === "keep") return "pill keep";
  if (value === "downgrade") return "pill downgrade";
  if (value === "switch") return "pill switch";
  return "pill dump";
}

function formatAmount(value: number, currency: string): string {
  const amount = new Intl.NumberFormat("en", {
    maximumFractionDigits: 2,
  }).format(value);
  return currency ? `${currency} ${amount}` : amount;
}

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

export default function AnalyzeWorkflow() {
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

  const fileNames = useMemo(
    () => selectedFiles.map((file) => file.name).join(", "),
    [selectedFiles]
  );

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
      }

      setStatus(
        payload.profiles.length > 1
          ? `Detected ${payload.profiles.length} policy options. Review and choose one.`
          : "Policy fields detected. Review and confirm before analysis."
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown extraction error";
      setError(message);
      setDetectedProfiles([]);
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
      setStatus("Extraction failed");
    } finally {
      setExtracting(false);
    }
  };

  const onFileChosen = (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) {
      return;
    }

    const incoming = Array.from(fileList);
    const valid = incoming.filter((file) => file.type === "application/pdf");

    if (valid.length !== incoming.length) {
      setError("Only PDF files are accepted.");
      return;
    }

    setSelectedFiles(valid);
    setResult(null);
    void populateFromUpload(valid);
  };

  const onProfileChange = (nextId: string) => {
    setSelectedProfileId(nextId);
    const chosen = detectedProfiles.find((item) => item.option_id === nextId);
    if (!chosen) {
      return;
    }
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

    setLoading(true);
    setError(null);
    setStatus("Running AI analysis...");

    try {
      const formData = new FormData();
      for (const file of selectedFiles) {
        formData.append("files", file);
      }

      if (form.insurer_name) formData.append("insurer", form.insurer_name);
      if (form.policyholder_name) {
        formData.append("policyholder_name", form.policyholder_name);
      }
      if (form.plan_name) formData.append("plan_name", form.plan_name);
      if (form.policy_type) formData.append("policy_type", form.policy_type);
      if (form.premium_amount) formData.append("annual_premium_myr", form.premium_amount);
      if (form.premium_frequency) {
        formData.append("premium_frequency", form.premium_frequency);
      }
      if (form.currency) formData.append("currency", form.currency);
      if (form.coverage_limit) formData.append("coverage_limit_myr", form.coverage_limit);
      if (form.effective_date) formData.append("effective_date", form.effective_date);
      if (form.renewal_date) formData.append("renewal_date", form.renewal_date);
      if (form.riders) formData.append("riders", form.riders);
      if (form.projected_income_monthly_myr) {
        formData.append("projected_income_monthly_myr", form.projected_income_monthly_myr);
      }

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
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown analysis error";
      setError(message);
      setResult(null);
      setStatus("Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const notDetected = (value: string) => (value ? value : "Not detected");

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">PolicyClaw</p>
        <p className="subtitle">
          AI-powered insurance decision intelligence for policyholders.
        </p>
      </section>

      <section className="flow-grid">
        <article className="panel step-card">
          <div className="step-head">
            <span className="step-index">Step 1</span>
            <h2>Upload Policy Documents</h2>
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
        </article>

        <article className="panel step-card">
          <div className="step-head">
            <span className="step-index">Step 2</span>
            <h2>Review and Analyze</h2>
          </div>
          <p className="step-note">Confirm detected fields. Not detected values remain editable.</p>

          {detectedProfiles.length > 1 && (
            <label>
              Detected Policy Options
              <select
                value={selectedProfileId}
                onChange={(e) => onProfileChange(e.target.value)}
              >
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
              <small>{notDetected(form.insurer_name)}</small>
            </label>
            <label>
              Policyholder Name
              <input
                value={form.policyholder_name}
                onChange={(e) => setForm({ ...form, policyholder_name: e.target.value })}
                placeholder="Not detected"
              />
              <small>{notDetected(form.policyholder_name)}</small>
            </label>
            <label>
              Plan Name
              <input
                value={form.plan_name}
                onChange={(e) => setForm({ ...form, plan_name: e.target.value })}
                placeholder="Not detected"
              />
              <small>{notDetected(form.plan_name)}</small>
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
          </form>
          <div style={{ display: "flex", justifyContent: "center", marginTop: "1.5rem" }}>
            <button
              type="button"
              onClick={(e) => {
                // Find the form element and trigger submit
                const formEl = e.currentTarget.closest(".step-card")?.querySelector("form");
                if (formEl) {
                  formEl.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
                }
              }}
              disabled={loading || extracting}
              style={{ minWidth: 220 }}
            >
              {loading ? "Analyzing..." : "Analyze Policy"}
            </button>
          </div>
        </article>
      </section>

      <p className="status">Status: {status}</p>
      {error && <p className="status">Error: {error}</p>}

      {result && (
        <section className="results">
          <article className="panel">
            <h2>Decision Snapshot</h2>
            <span className={verdictClass(result.verdict)}>{result.verdict.toUpperCase()}</span>
            <div className="metrics">
              <div>
                <small>Projected Savings</small>
                <strong>{formatAmount(result.projected_savings, form.currency)}</strong>
              </div>
              <div>
                <small>Overlap Detected</small>
                <strong>{result.overlap_detected ? "Yes" : "No"}</strong>
              </div>
              <div>
                <small>BNM Rights Detected</small>
                <strong>{result.bnm_rights_detected ? "Yes" : "No"}</strong>
              </div>
              <div>
                <small>Confidence</small>
                <strong>{result.confidence_score.toFixed(1)}%</strong>
              </div>
            </div>
            <h3>Summary Reasons</h3>
            <ul>
              {result.summary_reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </article>

          <article className="panel">
            <h2>Citations</h2>
            <ul>
              {result.citations.map((item, idx) => (
                <li key={`${item.source}-${item.page}-${idx}`}>
                  <strong>{item.source}</strong> | Page {item.page}
                  <p>{item.excerpt}</p>
                </li>
              ))}
            </ul>
          </article>
        </section>
      )}
    </main>
  );
}
