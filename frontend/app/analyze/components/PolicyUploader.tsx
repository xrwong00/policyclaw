"use client";

import { useCallback, useRef, useState, type DragEvent, type ChangeEvent } from "react";

export type PolicyUploaderProps = {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
  maxFiles?: number;
  maxBytesPerFile?: number;
};

const DEFAULT_MAX_FILES = 3;
const DEFAULT_MAX_BYTES = 10 * 1024 * 1024;

export function PolicyUploader({
  onFilesSelected,
  disabled,
  maxFiles = DEFAULT_MAX_FILES,
  maxBytesPerFile = DEFAULT_MAX_BYTES,
}: PolicyUploaderProps) {
  const [dragActive, setDragActive] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validate = useCallback(
    (files: File[]): { ok: File[]; error: string | null } => {
      if (files.length === 0) {
        return { ok: [], error: "No files selected." };
      }
      if (files.length > maxFiles) {
        return { ok: [], error: `Up to ${maxFiles} PDFs at a time.` };
      }
      for (const file of files) {
        if (!file.name.toLowerCase().endsWith(".pdf")) {
          return { ok: [], error: `"${file.name}" is not a PDF.` };
        }
        if (file.size > maxBytesPerFile) {
          const mb = (maxBytesPerFile / (1024 * 1024)).toFixed(0);
          return { ok: [], error: `"${file.name}" exceeds ${mb} MB.` };
        }
      }
      return { ok: files, error: null };
    },
    [maxFiles, maxBytesPerFile]
  );

  const handleFiles = useCallback(
    (fileList: FileList | null) => {
      if (!fileList) return;
      const result = validate(Array.from(fileList));
      if (result.error) {
        setLocalError(result.error);
        return;
      }
      setLocalError(null);
      onFilesSelected(result.ok);
    },
    [onFilesSelected, validate]
  );

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragActive(false);
    if (disabled) return;
    handleFiles(event.dataTransfer.files);
  };

  const onChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFiles(event.target.files);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div
      className={`cv-uploader ${dragActive ? "cv-uploader--active" : ""} ${
        disabled ? "cv-uploader--disabled" : ""
      }`}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={onDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if ((e.key === "Enter" || e.key === " ") && !disabled) {
          e.preventDefault();
          inputRef.current?.click();
        }
      }}
      aria-label="Upload policy PDF"
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        multiple={maxFiles > 1}
        onChange={onChange}
        style={{ display: "none" }}
        disabled={disabled}
      />
      <div className="cv-uploader__title">Drop a policy PDF here</div>
      <div className="cv-uploader__hint">
        or click to browse — up to {maxFiles} file{maxFiles > 1 ? "s" : ""},{" "}
        {(maxBytesPerFile / (1024 * 1024)).toFixed(0)} MB each
      </div>
      {localError && <div className="cv-uploader__error">{localError}</div>}

      <style jsx>{`
        .cv-uploader {
          border: 2px dashed var(--border, rgba(16, 36, 30, 0.24));
          background: var(--panel, rgba(255, 255, 255, 0.82));
          border-radius: 12px;
          padding: 40px 24px;
          text-align: center;
          cursor: pointer;
          transition: border-color 120ms ease, background 120ms ease;
          color: var(--ink, #10241e);
          outline-offset: 3px;
        }
        .cv-uploader:focus-visible {
          outline: 2px solid var(--accent, #c84f33);
        }
        .cv-uploader--active {
          border-color: var(--accent, #c84f33);
          background: rgba(200, 79, 51, 0.06);
        }
        .cv-uploader--disabled {
          opacity: 0.55;
          cursor: not-allowed;
        }
        .cv-uploader__title {
          font-size: 1.05rem;
          font-weight: 600;
        }
        .cv-uploader__hint {
          margin-top: 6px;
          color: var(--muted, #39574c);
          font-size: 0.9rem;
        }
        .cv-uploader__error {
          margin-top: 10px;
          color: #9e3d27;
          font-size: 0.9rem;
        }
      `}</style>
    </div>
  );
}
