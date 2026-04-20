#!/usr/bin/env python3
"""Analisa requisições HTTP capturadas para identificar a API do tribunal.

Este script é usado pela skill juscraper-builder para processar
as requisições capturadas pelo Playwright MCP e identificar
automaticamente o endpoint principal, parâmetros, e mecanismo
de paginação.

Uso:
    python analyze_requests.py requests.json

O arquivo JSON deve conter uma lista de objetos com:
  - url: str
  - method: str
  - resourceType: str
  - headers: dict
  - postData: str (opcional)
  - status: int (opcional)
"""

import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse


# Extensões e padrões que indicam assets (ignorar)
ASSET_PATTERNS = {
    ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".woff", ".woff2", ".ttf", ".eot", ".ico", ".map",
}

ASSET_DOMAINS = {
    "fonts.googleapis.com", "cdn.jsdelivr.net", "cdnjs.cloudflare.com",
    "www.google-analytics.com", "www.googletagmanager.com",
    "connect.facebook.net", "platform.twitter.com",
}

# Palavras-chave que indicam endpoints de busca/consulta
SEARCH_KEYWORDS = {
    "pesquisa", "consulta", "search", "busca", "jurisprudencia",
    "resultado", "julgado", "acordao", "decisao", "sentenca",
    "processo", "query", "find", "list", "listar",
}


def is_asset(url: str) -> bool:
    """Verifica se a URL é de um asset estático."""
    parsed = urlparse(url)
    path = parsed.path.lower()
    if any(path.endswith(ext) for ext in ASSET_PATTERNS):
        return True
    if parsed.hostname in ASSET_DOMAINS:
        return True
    return False


def score_request(req: dict) -> int:
    """Pontua uma requisição pela probabilidade de ser o endpoint de busca."""
    score = 0
    url = req.get("url", "").lower()
    method = req.get("method", "").upper()
    resource_type = req.get("resourceType", "")

    # Ignorar assets
    if is_asset(url):
        return -100

    # Preferir XHR/fetch
    if resource_type in ("fetch", "xhr"):
        score += 30

    # Preferir POST (formulários de busca geralmente usam POST)
    if method == "POST":
        score += 20

    # Palavras-chave na URL
    for kw in SEARCH_KEYWORDS:
        if kw in url:
            score += 15

    # Penalizar URLs muito curtas (geralmente são páginas iniciais)
    parsed = urlparse(url)
    if len(parsed.path) < 5:
        score -= 10

    # Bônus se tem postData (indica submissão de formulário)
    if req.get("postData"):
        score += 10

    return score


def analyze_pagination(reqs_page1: list, reqs_page2: list) -> dict:
    """Compara requisições de página 1 e 2 para identificar paginação."""
    # Encontrar requisições que diferem entre as duas páginas
    urls_p1 = {r["url"] for r in reqs_page1 if not is_asset(r["url"])}
    urls_p2 = {r["url"] for r in reqs_page2 if not is_asset(r["url"])}

    # URLs que aparecem em ambas (com parâmetros diferentes)
    result = {
        "tipo": "desconhecido",
        "parametro": None,
        "detalhes": [],
    }

    for r2 in reqs_page2:
        if is_asset(r2["url"]):
            continue
        for r1 in reqs_page1:
            if is_asset(r1["url"]):
                continue
            p1 = urlparse(r1["url"])
            p2 = urlparse(r2["url"])
            if p1.path == p2.path and p1.query != p2.query:
                q1 = parse_qs(p1.query)
                q2 = parse_qs(p2.query)
                diffs = {
                    k: (q1.get(k), q2.get(k))
                    for k in set(q1) | set(q2)
                    if q1.get(k) != q2.get(k)
                }
                if diffs:
                    result["detalhes"].append({
                        "path": p1.path,
                        "diffs": diffs,
                    })

            # Comparar postData
            if (p1.path == p2.path
                    and r1.get("postData") and r2.get("postData")
                    and r1["postData"] != r2["postData"]):
                try:
                    pd1 = parse_qs(r1["postData"])
                    pd2 = parse_qs(r2["postData"])
                    diffs = {
                        k: (pd1.get(k), pd2.get(k))
                        for k in set(pd1) | set(pd2)
                        if pd1.get(k) != pd2.get(k)
                    }
                    if diffs:
                        result["detalhes"].append({
                            "path": p1.path,
                            "postData_diffs": diffs,
                        })
                except Exception:
                    pass

    return result


def main():
    if len(sys.argv) < 2:
        print("Uso: python analyze_requests.py <requests.json>")
        print("     python analyze_requests.py <page1.json> <page2.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        requests_data = json.load(f)

    # Filtrar e pontuar
    scored = []
    for req in requests_data:
        s = score_request(req)
        if s > -50:
            scored.append((s, req))

    scored.sort(key=lambda x: x[0], reverse=True)

    print("=" * 70)
    print("ANÁLISE DE REQUISIÇÕES CAPTURADAS")
    print("=" * 70)

    print(f"\nTotal de requisições: {len(requests_data)}")
    print(f"Após filtrar assets: {len(scored)}")

    print("\n--- Top 5 candidatos a endpoint principal ---\n")
    for i, (score, req) in enumerate(scored[:5]):
        print(f"#{i+1} (score: {score})")
        print(f"  URL: {req['url']}")
        print(f"  Método: {req.get('method', '?')}")
        print(f"  Tipo: {req.get('resourceType', '?')}")
        if req.get("postData"):
            pd_preview = req["postData"][:200]
            print(f"  POST data: {pd_preview}...")
        print()

    # Se dois arquivos foram fornecidos, analisar paginação
    if len(sys.argv) >= 3:
        with open(sys.argv[2]) as f:
            requests_page2 = json.load(f)

        pagination = analyze_pagination(requests_data, requests_page2)
        print("\n--- Análise de paginação ---\n")
        print(json.dumps(pagination, indent=2, ensure_ascii=False))

    # Salvar análise
    output = {
        "total_requests": len(requests_data),
        "filtered_requests": len(scored),
        "top_candidates": [
            {
                "score": s,
                "url": r["url"],
                "method": r.get("method"),
                "resource_type": r.get("resourceType"),
                "has_post_data": bool(r.get("postData")),
            }
            for s, r in scored[:5]
        ],
    }

    output_path = Path(sys.argv[1]).with_suffix(".analysis.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nAnálise salva em: {output_path}")


if __name__ == "__main__":
    main()
