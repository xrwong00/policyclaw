"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import * as pdfjs from "pdfjs-dist";

import { ClawViewOverlay, type Language } from "./ClawViewOverlay";
import type { ClawViewAnnotation } from "@/lib/api";

// pdfjs-dist v3 ships worker at build/pdf.worker.min.js. Loaded lazily so the
// viewer stays browser-only.
const DEFAULT_WORKER_URL =
  "https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js";

const PAGE_SCALE = 1.5;

export type PdfViewerProps = {
  fileUrl: string;
  annotations: ClawViewAnnotation[];
  workerUrl?: string;
  scale?: number;
};

type RenderedPage = {
  pageIndex: number;
  width: number;
  height: number;
};

export function PdfViewer({
  fileUrl,
  annotations,
  workerUrl = DEFAULT_WORKER_URL,
  scale = PAGE_SCALE,
}: PdfViewerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [pages, setPages] = useState<RenderedPage[]>([]);
  const [language, setLanguage] = useState<Language>("en");
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const container = containerRef.current;
    if (!container) return;

    setPages([]);
    setLoadError(null);
    container.innerHTML = "";

    const render = async () => {
      try {
        pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;

        const task = pdfjs.getDocument({ url: fileUrl });
        const doc = await task.promise;
        if (cancelled) {
          doc.destroy();
          return;
        }

        const rendered: RenderedPage[] = [];
        for (let i = 1; i <= doc.numPages; i += 1) {
          if (cancelled) break;
          const page = await doc.getPage(i);
          const viewport = page.getViewport({ scale });

          const pageContainer = document.createElement("div");
          pageContainer.className = "cv-pdf-page";
          pageContainer.style.width = `${viewport.width}px`;
          pageContainer.style.height = `${viewport.height}px`;
          pageContainer.dataset.pageIndex = String(i - 1);

          const canvas = document.createElement("canvas");
          canvas.width = viewport.width;
          canvas.height = viewport.height;
          canvas.style.display = "block";
          const ctx = canvas.getContext("2d");
          if (!ctx) continue;

          pageContainer.appendChild(canvas);
          container.appendChild(pageContainer);

          await page.render({
            canvasContext: ctx,
            viewport,
          }).promise;

          rendered.push({
            pageIndex: i - 1,
            width: viewport.width,
            height: viewport.height,
          });
          if (!cancelled) setPages([...rendered]);
        }
      } catch (err) {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Failed to render PDF";
        setLoadError(message);
      }
    };

    render();

    return () => {
      cancelled = true;
      if (container) container.innerHTML = "";
    };
  }, [fileUrl, scale, workerUrl]);

  return (
    <div className="cv-pdf-viewer">
      <div className="cv-pdf-viewer__pages" ref={containerRef} />
      {pages.map((p) => (
        <PageOverlayMount
          key={p.pageIndex}
          page={p}
          annotations={annotations}
          scale={scale}
          language={language}
          onLanguageChange={setLanguage}
        />
      ))}
      {loadError && (
        <div role="alert" className="cv-pdf-viewer__error">
          {loadError}
        </div>
      )}

      <style jsx>{`
        .cv-pdf-viewer {
          position: relative;
          height: 80vh;
          min-height: 560px;
          overflow-y: auto;
          overflow-x: hidden;
          border: 1px solid var(--border, rgba(16, 36, 30, 0.14));
          border-radius: 12px;
          background: #f5f3ef;
          padding: 16px;
          display: flex;
          justify-content: center;
        }
        .cv-pdf-viewer__pages {
          display: flex;
          flex-direction: column;
          gap: 16px;
          align-items: center;
        }
        .cv-pdf-viewer__error {
          position: absolute;
          top: 12px;
          left: 12px;
          right: 12px;
          color: #9e3d27;
          background: rgba(200, 79, 51, 0.08);
          border: 1px solid rgba(200, 79, 51, 0.28);
          border-radius: 8px;
          padding: 10px 12px;
        }
      `}</style>
      <style jsx global>{`
        .cv-pdf-page {
          position: relative;
          box-shadow: 0 4px 12px rgba(16, 36, 30, 0.12);
          background: #ffffff;
        }
      `}</style>
    </div>
  );
}

export default PdfViewer;

type PageOverlayMountProps = {
  page: RenderedPage;
  annotations: ClawViewAnnotation[];
  scale: number;
  language: Language;
  onLanguageChange: (lang: Language) => void;
};

function PageOverlayMount({
  page,
  annotations,
  scale,
  language,
  onLanguageChange,
}: PageOverlayMountProps) {
  const [host, setHost] = useState<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = document.querySelector<HTMLDivElement>(
      `.cv-pdf-page[data-page-index="${page.pageIndex}"]`
    );
    setHost(el ?? null);
  }, [page.pageIndex, page.width, page.height]);

  if (!host) return null;

  // Portal the overlay into the per-page container so it inherits the page's
  // coordinate system (position: relative on .cv-pdf-page).
  return (
    <OverlayPortal host={host}>
      <ClawViewOverlay
        annotations={annotations}
        pageIndex={page.pageIndex}
        scale={scale}
        width={page.width}
        height={page.height}
        language={language}
        onLanguageChange={onLanguageChange}
      />
    </OverlayPortal>
  );
}

type OverlayPortalProps = {
  host: HTMLElement;
  children: ReactNode;
};

function OverlayPortal({ host, children }: OverlayPortalProps) {
  return createPortal(children, host);
}
