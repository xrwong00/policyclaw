"""Render a markdown deliverable (PRD/SAD/QATD) to PDF via headless Chrome.

Usage: python scripts/render-deliverable-pdf.py <input.md> <output.pdf>
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

CSS = """
@page { size: A4; margin: 18mm 16mm; }

* { box-sizing: border-box; }

body {
    font-family: "Segoe UI", -apple-system, "Inter", system-ui, Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.5;
    color: #1a1a1a;
    margin: 0;
    padding: 0;
}

h1, h2, h3, h4 { page-break-after: avoid; }

h1 {
    font-size: 22pt;
    margin: 0 0 14pt 0;
    padding-bottom: 8pt;
    border-bottom: 2px solid #2a2a2a;
    line-height: 1.25;
}

h2 {
    font-size: 15pt;
    margin: 22pt 0 8pt 0;
    color: #1a1a2e;
    line-height: 1.3;
}

h3 {
    font-size: 12pt;
    margin: 16pt 0 6pt 0;
    color: #232336;
}

h4 { font-size: 11pt; margin: 12pt 0 4pt 0; }

p { margin: 6pt 0; }

ul, ol { margin: 6pt 0; padding-left: 22pt; }
li { margin: 2pt 0; }

a { color: #1f4fa3; text-decoration: none; }

hr {
    border: none;
    border-top: 1px solid #cfcfd6;
    margin: 18pt 0;
}

table {
    border-collapse: collapse;
    width: 100%;
    font-size: 9.5pt;
    margin: 8pt 0 14pt 0;
    page-break-inside: auto;
}

th, td {
    border: 1px solid #d0d0d6;
    padding: 6px 8px;
    vertical-align: top;
    text-align: left;
}

th {
    background: #ececf0;
    font-weight: 600;
}

tr:nth-child(even) td { background: #f7f7f9; }

tr { page-break-inside: avoid; }

code {
    background: #f1f1f4;
    padding: 1px 5px;
    border-radius: 3px;
    font-family: "Consolas", "SF Mono", "Courier New", monospace;
    font-size: 9.5pt;
    color: #232336;
}

pre {
    background: #f4f4f7;
    border: 1px solid #e2e2e8;
    border-radius: 4px;
    padding: 8pt 10pt;
    font-family: "Consolas", "SF Mono", "Courier New", monospace;
    font-size: 9pt;
    line-height: 1.4;
    overflow-x: auto;
    page-break-inside: avoid;
    margin: 8pt 0;
}

pre code {
    background: transparent;
    padding: 0;
    border-radius: 0;
}

strong { color: #111; }

blockquote {
    border-left: 3px solid #c4c4cc;
    margin: 8pt 0;
    padding: 2pt 12pt;
    color: #444;
}
"""

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_chrome() -> str:
    override = os.environ.get("CHROME_PATH")
    if override and Path(override).exists():
        return override
    for path in CHROME_CANDIDATES:
        if Path(path).exists():
            return path
    raise RuntimeError(
        "Chrome / Edge not found. Set CHROME_PATH or install Chrome at a standard path."
    )


def extract_title(md_text: str) -> str:
    for line in md_text.splitlines():
        m = re.match(r"^#\s+(.+)$", line.strip())
        if m:
            return m.group(1).strip()
    return "Document"


def render_html(md_text: str, title: str) -> str:
    body_html = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists", "toc"],
        output_format="html5",
    )
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
{body_html}
</body>
</html>
"""


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python scripts/render-deliverable-pdf.py <input.md> <output.pdf>")
        return 2

    src = Path(sys.argv[1]).resolve()
    dst = Path(sys.argv[2]).resolve()

    if not src.exists():
        print(f"Input not found: {src}")
        return 1

    md_text = src.read_text(encoding="utf-8")
    title = extract_title(md_text)
    html = render_html(md_text, title)

    chrome = find_chrome()
    tmp = Path(tempfile.mkdtemp(prefix="deliverable-pdf-"))
    try:
        html_path = tmp / "doc.html"
        html_path.write_text(html, encoding="utf-8")
        file_url = "file:///" + str(html_path).replace("\\", "/")

        cmd = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-extensions",
            f"--print-to-pdf={dst}",
            "--no-pdf-header-footer",
            "--virtual-time-budget=10000",
            file_url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if result.returncode != 0:
            print("Chrome failed:", result.stderr or result.stdout)
            return 1

        if not dst.exists() or dst.stat().st_size < 100:
            print(f"PDF was not produced or is empty: {dst}")
            return 1

        magic = dst.read_bytes()[:5]
        if not magic.startswith(b"%PDF-"):
            print(f"Output is not a valid PDF (magic={magic!r})")
            return 1

        size_kb = dst.stat().st_size / 1024
        print(f"OK: wrote {dst} ({size_kb:.1f} KB)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
