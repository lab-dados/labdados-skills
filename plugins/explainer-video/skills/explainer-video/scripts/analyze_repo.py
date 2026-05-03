#!/usr/bin/env python3
"""
Sumariza um repositório para alimentar a escrita do roteiro.

Output: JSON em stdout com:
{
  "name": "...",
  "description": "...",
  "live_url": "..." (se detectada),
  "stack": [...],
  "features": [...],          # heurística do README
  "readme_excerpt": "...",    # primeiros 4000 chars do README pra contexto adicional
  "entry_points": [...]       # arquivos que cheiram a "main page" (index.html, app.py, etc)
}

Uso: python analyze_repo.py <path-do-repo>

A análise é deliberadamente simples — heurística sobre arquivos óbvios.
O modelo (Claude) refina depois usando o readme_excerpt.
"""
import json
import os
import re
import sys
from pathlib import Path


README_NAMES = ["README.md", "README.rst", "README.txt", "README", "readme.md"]
ENTRY_HINTS = [
    "index.html", "app.py", "main.py", "server.py", "app.js", "main.js",
    "src/App.tsx", "src/App.jsx", "src/main.tsx", "pages/index.tsx",
    "streamlit_app.py",
]
LIVE_URL_PATTERNS = [
    r"https?://[\w\-.]+\.vercel\.app[\w\-/]*",
    r"https?://[\w\-.]+\.netlify\.app[\w\-/]*",
    r"https?://[\w\-.]+\.streamlit\.app[\w\-/]*",
    r"https?://[\w\-.]+\.github\.io[\w\-/]*",
    r"https?://[\w\-.]+\.herokuapp\.com[\w\-/]*",
    r"https?://[\w\-.]+\.fly\.dev[\w\-/]*",
    r"https?://[\w\-.]+\.railway\.app[\w\-/]*",
    r"https?://[\w\-.]+\.onrender\.com[\w\-/]*",
]


def find_readme(repo: Path) -> Path | None:
    for name in README_NAMES:
        p = repo / name
        if p.exists():
            return p
    return None


def detect_stack(repo: Path) -> list[str]:
    stack = []
    if (repo / "package.json").exists():
        try:
            pkg = json.loads((repo / "package.json").read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "next" in deps: stack.append("Next.js")
            if "react" in deps: stack.append("React")
            if "vue" in deps: stack.append("Vue")
            if "svelte" in deps: stack.append("Svelte")
            if not stack: stack.append("Node.js")
        except Exception:
            stack.append("Node.js")
    if (repo / "pyproject.toml").exists() or (repo / "requirements.txt").exists():
        deps_text = ""
        for f in ("requirements.txt", "pyproject.toml"):
            p = repo / f
            if p.exists():
                deps_text += p.read_text(errors="ignore").lower()
        if "streamlit" in deps_text: stack.append("Streamlit")
        if "django" in deps_text: stack.append("Django")
        if "fastapi" in deps_text: stack.append("FastAPI")
        if "flask" in deps_text: stack.append("Flask")
        if not any(s in stack for s in ["Streamlit", "Django", "FastAPI", "Flask"]):
            stack.append("Python")
    if (repo / "Cargo.toml").exists(): stack.append("Rust")
    if (repo / "go.mod").exists(): stack.append("Go")
    return stack


def detect_live_url(text: str) -> str | None:
    for pat in LIVE_URL_PATTERNS:
        m = re.search(pat, text)
        if m:
            return m.group(0)
    return None


def detect_features(readme_text: str) -> list[str]:
    """Heurística: pega bullets sob seções 'Features', 'What it does', etc."""
    features = []
    lines = readme_text.split("\n")
    in_feature_section = False
    for line in lines:
        lower = line.lower().strip()
        if re.match(r"^#+\s*(features|what\s+it\s+does|funcionalidades|recursos|capabilities)", lower):
            in_feature_section = True
            continue
        if in_feature_section and re.match(r"^#+\s", line):
            in_feature_section = False
            continue
        if in_feature_section and (line.startswith("- ") or line.startswith("* ")):
            feat = line[2:].strip()
            feat = re.sub(r"\*\*(.+?)\*\*", r"\1", feat)  # bold off
            if feat:
                features.append(feat)
    return features[:10]


def detect_entry_points(repo: Path) -> list[str]:
    found = []
    for hint in ENTRY_HINTS:
        if (repo / hint).exists():
            found.append(hint)
    return found


def main():
    if len(sys.argv) < 2:
        print("Usage: analyze_repo.py <repo-path>", file=sys.stderr)
        sys.exit(1)

    repo = Path(sys.argv[1]).resolve()
    if not repo.exists():
        print(f"Repo path does not exist: {repo}", file=sys.stderr)
        sys.exit(1)

    readme_path = find_readme(repo)
    readme_text = readme_path.read_text(errors="ignore") if readme_path else ""

    # Try to extract a name from package.json or first H1 of README
    name = repo.name
    if (repo / "package.json").exists():
        try:
            name = json.loads((repo / "package.json").read_text()).get("name", name)
        except Exception:
            pass
    elif readme_text:
        m = re.search(r"^#\s+(.+)$", readme_text, re.MULTILINE)
        if m:
            name = m.group(1).strip()

    # Description: first paragraph after H1
    description = ""
    if readme_text:
        m = re.search(r"^#\s+.+\n+(.+?)(?:\n\n|\n#)", readme_text, re.DOTALL | re.MULTILINE)
        if m:
            description = m.group(1).strip().replace("\n", " ")[:300]

    output = {
        "name": name,
        "description": description,
        "live_url": detect_live_url(readme_text),
        "stack": detect_stack(repo),
        "features": detect_features(readme_text),
        "entry_points": detect_entry_points(repo),
        "readme_excerpt": readme_text[:4000],
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
