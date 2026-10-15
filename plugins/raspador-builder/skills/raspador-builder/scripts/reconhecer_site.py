# /// script
# requires-python = ">=3.9"
# dependencies = ["requests"]
# ///
"""Reconhecimento de um site antes de escrever o raspador (skill raspador-builder).

Uso:
    python reconhecer_site.py "<endereço da página de busca>" [--max-testes 5]

Faz poucos pedidos, com um segundo entre eles, e imprime cinco seções:
  1. robots.txt: o arquivo, o código de resposta e se o caminho da página é permitido;
  2. termos de uso: links da página inicial e da página pedida que parecem termos ou política;
  3. bloqueios: sinais de login, captcha e desafio anti-robô;
  4. página: código, tipo de conteúdo, tamanho, se o HTML parece vazio (montado por script);
  5. API candidatos: endereços do mesmo site, achados no HTML e nos scripts, que devolvem JSON.

O script sinaliza; quem decide é quem lê. Ele não testa endereço que o robots.txt proíbe e não
segue endereço de outro domínio.
"""

import argparse
import html
import re
import sys
import time
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import requests

USER_AGENT = "raspador-de-pesquisa/1.0 (reconhecimento; coleta academica)"
ESPERA = 1.0

SINAIS_CAPTCHA = ["g-recaptcha", "recaptcha/api.js", "hcaptcha", "cf-turnstile", "captcha"]
SINAIS_DESAFIO = ["challenge-platform", "just a moment", "checking your browser", "cf-chl", "attention required"]
SINAIS_LOGIN = ['type="password"', "type='password'", "faça login", "faça seu login", "entrar com", "acesso restrito"]
PALAVRAS_TERMOS = re.compile(
    r"termos?|condi[cç][oõ]es de uso|pol[ií]tica|aviso legal|privacidade|uso dos dados|licen[cç]a", re.I
)
# Endereços com cara de API: primeiro todo endereço (absoluto ou começando em /) que aparece no texto,
# depois só os que têm /api/, .json, graphql, /rest/, /vN/ ou format=json.
PADRAO_ENDERECO = re.compile(r"""https?://[^\s"'<>`]+|(?<![\w/<])/[\w\-.~%]+(?:/[^\s"'<>`)]*)?""")
PARECE_API = re.compile(r"/api/|\.json\b|graphql|/rest/|/v\d+/|format=json", re.I)
PADRAO_CHAMADA = re.compile(r"fetch\(|axios\.|\$\.ajax|\$\.getJSON|XMLHttpRequest", re.I)


class Visitante:
    """Uma sessão com espera antes de cada pedido e contagem dos pedidos feitos."""

    def __init__(self):
        self.sessao = requests.Session()
        self.sessao.headers["User-Agent"] = USER_AGENT
        self.pedidos = 0

    def get(self, endereco):
        time.sleep(ESPERA)
        self.pedidos += 1
        try:
            return self.sessao.get(endereco, timeout=30, allow_redirects=True)
        except requests.RequestException as erro:
            print(f"  erro ao pedir {endereco}: {erro}")
            return None


def titulo(texto):
    print(f"\n== {texto} ==")


def conferir_robots(visitante, endereco):
    partes = urlsplit(endereco)
    endereco_robots = f"{partes.scheme}://{partes.netloc}/robots.txt"
    resposta = visitante.get(endereco_robots)
    leitor = RobotFileParser()
    titulo("1. robots.txt")
    print(f"Endereço: {endereco_robots}")
    if resposta is None:
        print("Sem resposta: trate como proibição enquanto durar (RFC 9309). Não colete agora.")
        return leitor, False
    print(f"Código: {resposta.status_code}")
    if resposta.status_code >= 500:
        print("Erro do servidor: trate como proibição enquanto durar (RFC 9309). Não colete agora.")
        return leitor, False
    if resposta.status_code >= 400 or "html" in resposta.headers.get("Content-Type", "").lower():
        print("Não existe robots.txt (ou devolveu outra coisa). O site não declarou regra para robôs.")
        if resposta.status_code in (401, 403):
            print("ATENÇÃO: 401/403 no robots.txt. Confira se a página também recusa o requests (bloqueio).")
        leitor.parse([])
        return leitor, True
    linhas = resposta.text.splitlines()
    print("Conteúdo:")
    for linha in linhas[:60]:
        print(f"  | {linha}")
    if len(linhas) > 60:
        print(f"  | ... ({len(linhas) - 60} linhas a mais)")
    leitor.parse(linhas)
    caminho = partes.path or "/"
    if partes.query:
        caminho += "?" + partes.query
    permitido = leitor.can_fetch(USER_AGENT, endereco) and leitor.can_fetch("*", endereco)
    print(f"Caminho {caminho!r} permitido para '*' e para este robô: {'sim' if permitido else 'NÃO'}")
    atraso = leitor.crawl_delay("*")
    if atraso:
        print(f"Crawl-delay: {atraso} s (o raspador deve esperar max(1, {atraso}) s entre pedidos)")
    return leitor, permitido


def links_de_termos(pagina_html, base):
    achados = []
    for href, texto in re.findall(r"<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", pagina_html, re.I | re.S):
        texto_limpo = re.sub(r"<[^>]+>", " ", texto).strip()
        if PALAVRAS_TERMOS.search(texto_limpo) or PALAVRAS_TERMOS.search(href):
            achados.append((texto_limpo[:60], urljoin(base, html.unescape(href))))
    return achados


def sinais(resposta):
    texto = resposta.text.lower()
    encontrados = []
    for nome, lista in (("captcha", SINAIS_CAPTCHA), ("desafio anti-robô", SINAIS_DESAFIO), ("login", SINAIS_LOGIN)):
        for marca in lista:
            if marca in texto:
                encontrados.append(f"{nome}: '{marca}' no HTML")
    if resposta.status_code in (401, 403, 503):
        encontrados.append(f"código {resposta.status_code}")
    if "cf-mitigated" in resposta.headers:
        encontrados.append("cabeçalho cf-mitigated (desafio do Cloudflare)")
    if resposta.history and re.search(r"login|entrar|signin|auth", resposta.url, re.I):
        encontrados.append(f"redirecionou para {resposta.url}")
    return encontrados


def mesmo_site(endereco, base):
    return urlsplit(endereco).netloc == urlsplit(base).netloc


def candidatos_de_api(textos, base):
    vistos = []
    for texto in textos:
        for achado in filter(PARECE_API.search, PADRAO_ENDERECO.findall(html.unescape(texto))):
            completo = urljoin(base, achado.rstrip(".,;"))
            if not mesmo_site(completo, base):
                continue
            # A página pode escrever o próprio endereço com outro esquema (https atrás de proxy);
            # o teste usa o esquema pelo qual o site respondeu.
            completo = urlsplit(completo)._replace(scheme=urlsplit(base).scheme).geturl()
            if completo not in vistos:
                vistos.append(completo)
    return vistos


def main():
    leitor_argumentos = argparse.ArgumentParser(description="Reconhecimento antes de raspar.")
    leitor_argumentos.add_argument("endereco", help="endereço da página de busca (com o termo, se der)")
    leitor_argumentos.add_argument("--max-testes", type=int, default=5, help="API candidatos a testar")
    argumentos = leitor_argumentos.parse_args()
    endereco = argumentos.endereco
    partes = urlsplit(endereco)
    raiz = f"{partes.scheme}://{partes.netloc}/"
    visitante = Visitante()

    robots, permitido = conferir_robots(visitante, endereco)
    if not permitido:
        print("\nPARE: o robots.txt não permite este caminho (ou o servidor não respondeu). Avise o usuário.")
        return 2

    paginas = {}
    for alvo in dict.fromkeys([endereco, raiz]):
        resposta = visitante.get(alvo)
        if resposta is not None:
            paginas[alvo] = resposta

    titulo("2. Termos de uso")
    termos = []
    for resposta in paginas.values():
        termos += [t for t in links_de_termos(resposta.text, resposta.url) if t not in termos]
    if termos:
        for texto, link in termos:
            print(f"  {texto!r}: {link}")
        print("Leia esses textos e procure o que dizem sobre robôs, raspagem e uso automatizado.")
    else:
        print("Nenhum link de termos de uso ou política encontrado na página pedida nem na inicial.")

    titulo("3. Login, captcha e bloqueio anti-robô")
    algum = False
    for alvo, resposta in paginas.items():
        for sinal in sinais(resposta):
            algum = True
            print(f"  {alvo}: {sinal}")
    print("  Confira cada sinal abrindo a página: a palavra pode estar num texto comum." if algum else "  Nenhum.")

    titulo("4. Página pedida")
    principal = paginas.get(endereco)
    scripts_externos = []
    if principal is not None:
        tipo = principal.headers.get("Content-Type", "")
        print(
            f"Código {principal.status_code}, tipo {tipo!r}, {len(principal.content)} bytes, final em {principal.url}"
        )
        for nome in ("X-Robots-Tag", "Retry-After", "Set-Cookie", "Server"):
            if nome in principal.headers:
                print(f"  {nome}: {principal.headers[nome][:120]}")
        if re.search(r"<meta[^>]+name=[\"']robots[\"'][^>]*noindex", principal.text, re.I):
            print("  meta robots noindex: pede que buscadores não indexem; não proíbe acesso.")
        texto_visivel = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", principal.text, flags=re.S)
        palavras = len(texto_visivel.split())
        print(f"  Texto visível: cerca de {palavras} palavras.")
        if re.search(r"carregando|loading", texto_visivel, re.I) or palavras < 40:
            print("  A página parece ser preenchida por script: procure a API (seção 5 e scripts).")
        for pagina in paginas.values():
            for src in re.findall(r"<script[^>]+src=[\"']([^\"']+)[\"']", pagina.text, re.I):
                completo = urljoin(pagina.url, html.unescape(src))
                if mesmo_site(completo, raiz) and completo not in scripts_externos:
                    scripts_externos.append(completo)
        chamadas = sum(len(PADRAO_CHAMADA.findall(p.text)) for p in paginas.values())
        print(f"  Scripts do mesmo site: {len(scripts_externos)}; chamadas fetch/axios/ajax no HTML: {chamadas}")

    titulo("5. API candidatos")
    textos = [p.text for p in paginas.values()]
    for src in scripts_externos[:10]:
        resposta = visitante.get(src)
        if resposta is not None and resposta.ok:
            textos.append(resposta.text)
    candidatos = candidatos_de_api(textos, raiz)
    if not candidatos:
        print("Nenhum endereço com cara de API no HTML nem nos scripts do mesmo site.")
        print("Se a página mostra os resultados no HTML, raspe o HTML; se não, leia os scripts à mão.")
    for candidato in candidatos[: argumentos.max_testes]:
        if not robots.can_fetch(USER_AGENT, candidato):
            print(f"  {candidato}: proibido pelo robots.txt, não testado")
            continue
        resposta = visitante.get(candidato)
        if resposta is None:
            continue
        tipo = resposta.headers.get("Content-Type", "")
        trecho = ""
        if "json" in tipo:
            try:
                dados = resposta.json()
                chaves = list(dados.keys())[:8] if isinstance(dados, dict) else f"lista de {len(dados)}"
                trecho = f" chaves: {chaves}"
            except ValueError:
                trecho = " (diz JSON mas não lê)"
        print(f"  {candidato}\n    -> {resposta.status_code} {tipo}{trecho}")
    if len(candidatos) > argumentos.max_testes:
        print(f"  ... e mais {len(candidatos) - argumentos.max_testes} não testados:")
        for candidato in candidatos[argumentos.max_testes :]:
            print(f"    {candidato}")

    print(f"\nPedidos feitos: {visitante.pedidos}, com {ESPERA:.0f} s de espera antes de cada um.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
