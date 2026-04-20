#!/usr/bin/env python3
"""Render an HTML file to PDF.

Strategy (first that works wins):
  1. Microsoft Edge headless (default on Windows 11)
  2. Google Chrome / Chromium headless
  3. `playwright` Python package
  4. `weasyprint` Python package

Usage:
    python render_pdf.py input.html [output.pdf]

Exits non-zero only if all strategies fail.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def _candidates_windows():
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    pfx86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local = os.environ.get("LOCALAPPDATA", "")
    return [
        rf"{pfx86}\Microsoft\Edge\Application\msedge.exe",
        rf"{pf}\Microsoft\Edge\Application\msedge.exe",
        rf"{pf}\Google\Chrome\Application\chrome.exe",
        rf"{pfx86}\Google\Chrome\Application\chrome.exe",
        rf"{local}\Google\Chrome\Application\chrome.exe",
    ]


def _candidates_macos():
    return [
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]


def _candidates_linux():
    return ["microsoft-edge", "google-chrome", "chromium", "chromium-browser"]


def find_browser():
    system = platform.system()
    if system == "Windows":
        direct = _candidates_windows()
    elif system == "Darwin":
        direct = _candidates_macos()
    else:
        direct = []

    for path in direct:
        if Path(path).exists():
            return path

    # PATH lookups
    names = ["msedge", "microsoft-edge", "google-chrome",
             "chrome", "chromium", "chromium-browser"]
    if system == "Linux":
        names = _candidates_linux() + names
    for n in names:
        found = shutil.which(n)
        if found:
            return found
    return None


def render_with_browser(html_path, pdf_path, browser):
    url = Path(html_path).resolve().as_uri()
    out = str(Path(pdf_path).resolve())
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        f"--print-to-pdf={out}",
        "--no-pdf-header-footer",
        url,
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, timeout=60)
    except subprocess.TimeoutExpired:
        return False, "browser timed out"
    ok = res.returncode == 0 and Path(pdf_path).exists()
    if not ok:
        stderr = res.stderr.decode("utf-8", errors="replace")[:500]
        return False, stderr or "unknown error"
    return True, None


def render_with_playwright(html_path, pdf_path):
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        return False, "playwright not installed"
    url = Path(html_path).resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.pdf(
            path=str(pdf_path),
            format="A4",
            margin={"top": "14mm", "bottom": "14mm", "left": "16mm", "right": "16mm"},
            print_background=True,
        )
        browser.close()
    return True, None


def render_with_weasyprint(html_path, pdf_path):
    try:
        from weasyprint import HTML  # type: ignore
    except Exception:
        return False, "weasyprint not installed"
    HTML(filename=str(html_path)).write_pdf(str(pdf_path))
    return True, None


def main():
    if len(sys.argv) < 2:
        print("usage: render_pdf.py <input.html> [output.pdf]", file=sys.stderr)
        return 2
    html = Path(sys.argv[1])
    if not html.exists():
        print(f"ERROR: {html} not found", file=sys.stderr)
        return 2
    pdf = Path(sys.argv[2]) if len(sys.argv) >= 3 else html.with_suffix(".pdf")

    attempts = []

    browser = find_browser()
    if browser:
        ok, err = render_with_browser(html, pdf, browser)
        attempts.append(("browser", Path(browser).name, ok, err))
        if ok:
            print(f"wrote {pdf} via {Path(browser).name}")
            return 0

    ok, err = render_with_playwright(html, pdf)
    attempts.append(("playwright", "chromium", ok, err))
    if ok:
        print(f"wrote {pdf} via playwright")
        return 0

    ok, err = render_with_weasyprint(html, pdf)
    attempts.append(("weasyprint", "-", ok, err))
    if ok:
        print(f"wrote {pdf} via weasyprint")
        return 0

    print("ERROR: could not render PDF. Attempts:", file=sys.stderr)
    for kind, name, ok, err in attempts:
        print(f"  - {kind} ({name}): {err}", file=sys.stderr)
    print("Install Edge/Chrome, or `pip install playwright` (+ browsers), or `pip install weasyprint`.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
