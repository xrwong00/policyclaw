"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ClawViewAnnotation, RiskLevel } from "@/lib/api";

export const RISK_PALETTE: Record<
  RiskLevel,
  { fill: string; stroke: string; glyph: string; label: string }
> = {
  red: { fill: "rgba(213, 94, 0, 0.30)", stroke: "#D55E00", glyph: "▲", label: "High risk" },
  yellow: { fill: "rgba(230, 159, 0, 0.30)", stroke: "#E69F00", glyph: "●", label: "Warning" },
  green: { fill: "rgba(0, 158, 115, 0.20)", stroke: "#009E73", glyph: "■", label: "Standard" },
};

export type Language = "en" | "bm";

export type ClawViewOverlayProps = {
  annotations: ClawViewAnnotation[];
  pageIndex: number; // 0-based (react-pdf-viewer)
  scale: number;
  width: number;
  height: number;
  language: Language;
  onLanguageChange?: (lang: Language) => void;
};

type SelectedState = {
  annotation: ClawViewAnnotation;
  xCss: number;
  yCss: number;
  widthCss: number;
  heightCss: number;
};

export function ClawViewOverlay({
  annotations,
  pageIndex,
  scale,
  width,
  height,
  language,
  onLanguageChange,
}: ClawViewOverlayProps) {
  const [selected, setSelected] = useState<SelectedState | null>(null);

  // 1-based page numbers from backend (PyMuPDF/PRD), 0-based from viewer.
  const pageAnnotations = useMemo(
    () => annotations.filter((a) => a.bbox.page === pageIndex + 1),
    [annotations, pageIndex]
  );

  const onKeyDismiss = useCallback((e: KeyboardEvent) => {
    if (e.key === "Escape") setSelected(null);
  }, []);

  useEffect(() => {
    window.addEventListener("keydown", onKeyDismiss);
    return () => window.removeEventListener("keydown", onKeyDismiss);
  }, [onKeyDismiss]);

  if (pageAnnotations.length === 0) return null;

  return (
    <div
      className="cv-overlay-root"
      style={{ width, height }}
      onClick={(e) => {
        // Background click dismisses tooltip
        if (e.target === e.currentTarget) setSelected(null);
      }}
    >
      <svg
        className="cv-overlay-svg"
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        aria-label={`${pageAnnotations.length} ClawView risk highlights on this page`}
      >
        {pageAnnotations.map((ann) => {
          const palette = RISK_PALETTE[ann.risk_level];
          const x = ann.bbox.x0 * scale;
          const y = ann.bbox.y0 * scale;
          const w = Math.max(4, (ann.bbox.x1 - ann.bbox.x0) * scale);
          const h = Math.max(4, (ann.bbox.y1 - ann.bbox.y0) * scale);

          return (
            <g
              key={ann.clause_id}
              role="button"
              tabIndex={0}
              aria-label={`${palette.label}: ${ann.plain_explanation_en.slice(0, 80)}`}
              onClick={(e) => {
                e.stopPropagation();
                setSelected({
                  annotation: ann,
                  xCss: x,
                  yCss: y,
                  widthCss: w,
                  heightCss: h,
                });
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  setSelected({
                    annotation: ann,
                    xCss: x,
                    yCss: y,
                    widthCss: w,
                    heightCss: h,
                  });
                }
              }}
              style={{ cursor: "pointer" }}
            >
              <rect
                x={x}
                y={y}
                width={w}
                height={h}
                fill={palette.fill}
                stroke={palette.stroke}
                strokeWidth={1.5}
                rx={3}
              />
              <text
                x={x + 4}
                y={y + 12}
                fill={palette.stroke}
                fontSize={11}
                fontWeight={700}
                style={{ userSelect: "none", pointerEvents: "none" }}
              >
                {palette.glyph}
              </text>
            </g>
          );
        })}
      </svg>

      {selected && (
        <Tooltip
          state={selected}
          language={language}
          onLanguageChange={onLanguageChange}
          onClose={() => setSelected(null)}
          pageWidth={width}
          pageHeight={height}
        />
      )}

      <style jsx>{`
        .cv-overlay-root {
          position: absolute;
          inset: 0;
          pointer-events: auto;
        }
        .cv-overlay-svg {
          position: absolute;
          inset: 0;
          overflow: visible;
        }
      `}</style>
    </div>
  );
}

type TooltipProps = {
  state: SelectedState;
  language: Language;
  onLanguageChange?: (lang: Language) => void;
  onClose: () => void;
  pageWidth: number;
  pageHeight: number;
};

function Tooltip({
  state,
  language,
  onLanguageChange,
  onClose,
  pageWidth,
  pageHeight,
}: TooltipProps) {
  const palette = RISK_PALETTE[state.annotation.risk_level];
  const explanation =
    language === "bm"
      ? state.annotation.plain_explanation_bm
      : state.annotation.plain_explanation_en;

  // Position below the rect by default; flip above if it would overflow.
  const preferredWidth = 340;
  const gap = 8;
  const left = Math.max(
    8,
    Math.min(state.xCss, pageWidth - preferredWidth - 8)
  );
  const top =
    state.yCss + state.heightCss + gap + 200 > pageHeight
      ? Math.max(8, state.yCss - 200 - gap)
      : state.yCss + state.heightCss + gap;

  return (
    <div
      role="dialog"
      aria-label="Risk explanation"
      className="cv-tooltip"
      style={{
        top,
        left,
        width: preferredWidth,
        borderColor: palette.stroke,
      }}
      onClick={(e) => e.stopPropagation()}
    >
      <div className="cv-tooltip__header">
        <span
          className="cv-tooltip__badge"
          style={{ background: palette.fill, color: palette.stroke }}
        >
          {palette.glyph} {palette.label}
        </span>
        <div className="cv-tooltip__lang">
          <button
            type="button"
            onClick={() => onLanguageChange?.("en")}
            aria-pressed={language === "en"}
            className={language === "en" ? "is-active" : ""}
          >
            EN
          </button>
          <button
            type="button"
            onClick={() => onLanguageChange?.("bm")}
            aria-pressed={language === "bm"}
            className={language === "bm" ? "is-active" : ""}
          >
            BM
          </button>
        </div>
        <button
          type="button"
          className="cv-tooltip__close"
          onClick={onClose}
          aria-label="Close explanation"
        >
          ×
        </button>
      </div>
      <p className="cv-tooltip__body">{explanation}</p>
      {state.annotation.why_this_matters && (
        <p className="cv-tooltip__why">
          <strong>Why this matters: </strong>
          {state.annotation.why_this_matters}
        </p>
      )}
      <p className="cv-tooltip__meta">
        Clause {state.annotation.clause_id} · page {state.annotation.source_page}
      </p>

      <style jsx>{`
        .cv-tooltip {
          position: absolute;
          background: #ffffff;
          border: 2px solid #10241e;
          border-radius: 10px;
          padding: 12px 14px 10px;
          box-shadow: 0 8px 24px rgba(16, 36, 30, 0.18);
          z-index: 20;
          color: #10241e;
          font-size: 0.88rem;
          line-height: 1.45;
        }
        .cv-tooltip__header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }
        .cv-tooltip__badge {
          font-size: 0.78rem;
          font-weight: 700;
          padding: 3px 8px;
          border-radius: 999px;
        }
        .cv-tooltip__lang {
          display: flex;
          gap: 4px;
          margin-left: auto;
        }
        .cv-tooltip__lang button {
          border: 1px solid rgba(16, 36, 30, 0.18);
          background: transparent;
          font-size: 0.72rem;
          padding: 3px 8px;
          border-radius: 999px;
          cursor: pointer;
          color: inherit;
        }
        .cv-tooltip__lang button.is-active {
          background: #10241e;
          color: #ffffff;
          border-color: #10241e;
        }
        .cv-tooltip__close {
          border: 0;
          background: transparent;
          font-size: 1.2rem;
          line-height: 1;
          padding: 2px 6px;
          cursor: pointer;
          color: inherit;
        }
        .cv-tooltip__body {
          margin: 0 0 6px 0;
        }
        .cv-tooltip__why {
          margin: 0 0 6px 0;
          color: #39574c;
          font-size: 0.82rem;
        }
        .cv-tooltip__meta {
          margin: 0;
          font-size: 0.72rem;
          color: #88968f;
        }
      `}</style>
    </div>
  );
}
