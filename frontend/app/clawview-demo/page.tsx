"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";

import { PolicyUploader } from "@/app/analyze/components/PolicyUploader";
import { postClawView, type ClawViewResponse } from "@/lib/api";

const PdfViewer = dynamic(
  () => import("@/app/analyze/components/PdfViewer").then((m) => m.PdfViewer),
  { ssr: false, loading: () => <div style={{ padding: 24 }}>Loading viewer…</div> }
);

export default function ClawViewDemoPage() {
  const [file, setFile] = useState<File | null>(null);
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [response, setResponse] = useState<ClawViewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!file) {
      setFileUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setFileUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const onFilesSelected = async (files: File[]) => {
    const first = files[0];
    if (!first) return;
    setError(null);
    setResponse(null);
    setFile(first);
    setLoading(true);
    try {
      const result = await postClawView(first);
      setResponse(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const summary = useMemo(() => {
    if (!response) return null;
    return `${response.annotations.length} highlights · ${response.red_count} red · ${response.yellow_count} yellow · ${response.green_count} green · confidence ${response.confidence_score.toFixed(0)}% (${response.confidence_band})`;
  }, [response]);

  return (
    <main style={{ padding: "32px 24px", maxWidth: 1120, margin: "0 auto" }}>
      <header style={{ marginBottom: 24 }}>
        <p className="eyebrow" style={{ margin: 0 }}>ClawView</p>
        <h1
          className="hero-headline"
          style={{ fontSize: "clamp(1.8rem, 3vw, 2.6rem)", marginTop: 6 }}
        >
          See the risks hiding in your policy.
        </h1>
        <p style={{ margin: "10px 0 0", color: "var(--muted, #39574c)", maxWidth: "60ch" }}>
          Upload a policy PDF to get clause-level risk highlights overlaid on
          the page. Click any highlight for a plain-language explanation in EN
          or BM.
        </p>
      </header>

      {!file && (
        <PolicyUploader onFilesSelected={onFilesSelected} maxFiles={1} />
      )}

      {file && (
        <section style={{ marginTop: 16 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 12,
              gap: 12,
              flexWrap: "wrap",
            }}
          >
            <div>
              <strong>{file.name}</strong>
              {summary && (
                <span style={{ marginLeft: 10, color: "var(--muted, #39574c)" }}>
                  {summary}
                </span>
              )}
              {loading && (
                <span style={{ marginLeft: 10, color: "var(--muted, #39574c)" }}>
                  Analyzing…
                </span>
              )}
            </div>
            <button
              type="button"
              onClick={() => {
                setFile(null);
                setResponse(null);
                setError(null);
              }}
              style={{
                border: "1px solid rgba(16, 36, 30, 0.18)",
                background: "transparent",
                borderRadius: 8,
                padding: "6px 12px",
                cursor: "pointer",
              }}
            >
              Upload different PDF
            </button>
          </div>

          {error && (
            <div
              role="alert"
              style={{
                color: "#9e3d27",
                background: "rgba(200, 79, 51, 0.08)",
                border: "1px solid rgba(200, 79, 51, 0.28)",
                borderRadius: 8,
                padding: "10px 12px",
                marginBottom: 12,
              }}
            >
              {error}
            </div>
          )}

          {fileUrl && (
            <PdfViewer
              fileUrl={fileUrl}
              annotations={response?.annotations ?? []}
            />
          )}
        </section>
      )}
    </main>
  );
}
