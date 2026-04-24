"use client";

import { useLangStore } from "../lib/store";
import { t } from "../lib/i18n";
import type { Lang } from "../lib/types";

const OPTIONS: Array<{ value: Lang; label: string }> = [
  { value: "en", label: "EN" },
  { value: "bm", label: "BM" },
];

export default function LanguageToggle() {
  const lang = useLangStore((s) => s.lang);
  const setLang = useLangStore((s) => s.setLang);

  return (
    <div
      role="radiogroup"
      aria-label={t("lang_label", lang)}
      style={{
        display: "inline-flex",
        gap: 4,
        padding: 3,
        borderRadius: 999,
        border: "1px solid rgba(0,0,0,0.12)",
        background: "rgba(255,255,255,0.6)",
      }}
    >
      {OPTIONS.map((option) => {
        const active = option.value === lang;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => setLang(option.value)}
            style={{
              minWidth: 40,
              padding: "4px 10px",
              borderRadius: 999,
              border: "none",
              background: active ? "#111" : "transparent",
              color: active ? "#fff" : "#111",
              fontWeight: 600,
              cursor: "pointer",
              fontSize: 12,
            }}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
