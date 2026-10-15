# /// script
# requires-python = ">=3.9"
# dependencies = ["requests"]
# ///
"""Reconhecimento de um site antes de escrever o raspador (skill raspador-builder).

Uso:
    python3 reconhecer_site.py "<endereço da página de busca>" [--max-testes 5]
(no Windows, `python` no lugar de `python3`; com uv, `uv run reconhecer_site.py ...`)

Faz poucos pedidos, com um segundo entre eles, e imprime cinco seções:
  1. robots.txt: o arquivo, o código de resposta e se o caminho da página é permitido;
  2. termos de uso: links da página inicial e da página pedida que parecem termos ou política;
  3. bloqueios: sinais de login, captcha e desafio anti-robô;
  4. página: código, tipo de conteúdo, tamanho, se o HTML parece vazio (montado por script);
  5. API candidatos: endereços do mesmo site, achados no HTML e nos scripts, que devolvem JSON.

O script sinaliza; quem decide é quem lê. Nenhum pedido depois do robots.txt (página pedida,
página inicial, scripts, API candidatos) vai a endereço que o robots.txt proíba para este robô,
e nenhum vai a outro domínio, nem seguindo redirecionamento: cada salto passa pela mesma
conferência, e o que não passa não é pedido. O robots.txt é lido como manda a RFC 9309, pelo código deste
arquivo e não pelo `urllib.robotparser`, para que a resposta não dependa da versão do Python.
"""

import argparse
import html
import re
import string
import sys
import time
from urllib.parse import quote, urljoin, urlsplit

import requests

USER_AGENT = "raspador-de-pesquisa/1.0 (reconhecimento; coleta academica)"
ESPERA = 1.0
# Redirecionamentos seguidos em sequência; a RFC 9309 (2.3.1.2) pede ao menos cinco para o robots.txt.
MAX_SALTOS = 5

SINAIS_CAPTCHA = ["g-recaptcha", "recaptcha/api.js", "hcaptcha", "cf-turnstile", "captcha"]
SINAIS_DESAFIO = ["challenge-platform", "just a moment", "checking your browser", "cf-chl", "attention required"]
SINAIS_LOGIN = ['type="password"', "type='password'", "faça login", "faça seu login", "entrar com", "acesso restrito"]
PALAVRAS_TERMOS = re.compile(
    r"termos?|condi[cç][oõ]es de uso|pol[ií]tica|aviso legal|privacidade|uso dos dados|licen[cç]a", re.IGNORECASE
)
# Endereços com cara de API: primeiro todo endereço (absoluto ou começando em /) que aparece no texto,
# depois só os que têm /api/, .json, graphql, /rest/, /vN/ ou format=json.
PADRAO_ENDERECO = re.compile(r"""https?://[^\s"'<>`]+|(?<![\w/<])/[\w\-.~%]+(?:/[^\s"'<>`)]*)?""")
PARECE_API = re.compile(r"/api/|\.json\b|graphql|/rest/|/v\d+/|format=json", re.IGNORECASE)
PADRAO_CHAMADA = re.compile(r"fetch\(|axios\.|\$\.ajax|\$\.getJSON|XMLHttpRequest", re.IGNORECASE)


# --- robots.txt (RFC 9309) -----------------------------------------------------------------------
#
# Até o Python 3.14, o `urllib.robotparser` aplica a primeira regra que casa, na ordem do arquivo,
# e lê `*` e `$` como letras. Com "Allow: /" antes de "Disallow: /busca" ele libera /busca, e com
# "Disallow: /*?q=" não proíbe nada; a partir do 3.15 ele segue a RFC. O mesmo site daria respostas
# diferentes conforme a versão de quem roda o script, então a leitura fica aqui.

# RFC 3986: caracteres "não reservados" e "reservados".
NAO_RESERVADOS = frozenset(string.ascii_letters + string.digits + "-._~")
RESERVADOS = frozenset(":/?#[]@!$&'()*+,;=")


def normalizar_caminho(caminho, regra=False):
    """Põe o caminho da regra e o do endereço na mesma grafia antes de comparar (RFC 9309, 2.2.2).

    A RFC manda decodificar o %XX de caractere não reservado e codificar o caractere reservado,
    nos dois lados: "/%7Euser" e "/~user" viram "/~user"; "/licitação" vira "/licita%C3%A7%C3%A3o",
    igual ao que o navegador manda; ":" e "%3a" viram "%3A". Assim a regra
    "/foo/bar?baz=https://foo.bar" casa com o endereço "/foo/bar?baz=https%3A%2F%2Ffoo.bar", como
    na tabela de exemplos da seção.

    Ficam por extenso os reservados que dão a estrutura do endereço, porque codificados eles mudam
    de sentido e não podem casar com a forma por extenso: o "?" que abre a consulta; "/" na parte
    do caminho, que separa segmentos ("/a%2Fb" é um segmento só); "&" e "=" na consulta, que
    separam os parâmetros ("a=1%26b" é um parâmetro só). A tabela da RFC os mantém assim.

    Com `regra=True`, `*` e o `$` final continuam sendo curinga e âncora, e não letras.
    """
    ancora = "$" if regra and caminho.endswith("$") else ""
    caminho = caminho[: len(caminho) - len(ancora)]
    parte_caminho, interrogacao, consulta = caminho.partition("?")
    saida = _normalizar_trecho(parte_caminho, "/", regra)
    if interrogacao:
        saida += "?" + _normalizar_trecho(consulta, "&=", regra)
    return saida + ancora


def _normalizar_trecho(trecho, estruturais, regra):
    saida = []
    posicao = 0
    while posicao < len(trecho):
        letra = trecho[posicao]
        codigo = trecho[posicao + 1 : posicao + 3]
        if letra == "%" and len(codigo) == 2 and all(c in string.hexdigits for c in codigo):
            decodificada = chr(int(codigo, 16))
            saida.append(decodificada if decodificada in NAO_RESERVADOS else "%" + codigo.upper())
            posicao += 3
            continue
        if regra and letra == "*":
            saida.append(letra)
        elif (letra in RESERVADOS and letra not in estruturais) or ord(letra) > 126 or ord(letra) <= 32:
            saida.append(quote(letra, safe=""))
        else:
            saida.append(letra)
        posicao += 1
    return "".join(saida)


def casa(regra, alvo):
    """A regra casa com o início do alvo; `*` vale qualquer sequência e `$` no fim exige o fim."""
    ancorada = regra.endswith("$")
    corpo = re.sub(r"\*+", "*", regra[:-1] if ancorada else regra)  # "**" vale o mesmo que "*", e é mais lento
    padrao = ".*".join(re.escape(parte) for parte in corpo.split("*"))
    return re.match(padrao + (r"\Z" if ancorada else ""), alvo, re.DOTALL) is not None


def produto(agente):
    """O nome do robô sem versão nem comentário: "raspador-de-pesquisa/1.0 (...)" vira "raspador-de-pesquisa"."""
    achado = re.match(r"\*|[a-z_-]+", agente.strip().lower())
    return achado.group(0) if achado else ""


class RegrasRobots:
    """Um robots.txt lido como manda a RFC 9309.

    Grupo: uma ou mais linhas User-agent seguidas das regras (Allow, Disallow, Crawl-delay). Vale o
    grupo cujo nome é o do robô; se não houver, o de `*`; grupos com o mesmo nome se somam. Entre
    as regras do grupo que casam com o caminho, vence a de caminho mais longo, e no empate o Allow.
    Sem regra que case, o caminho é permitido. Crawl-delay não está na RFC, mas muitos sites o usam.
    """

    def __init__(self, texto):
        self.grupos = []
        self.linhas_reconhecidas = 0
        lendo_agentes = False
        for linha in texto.lstrip("\ufeff").splitlines():
            linha = linha.split("#", 1)[0].strip()
            if ":" not in linha:
                continue
            chave, valor = (parte.strip() for parte in linha.split(":", 1))
            chave = chave.lower()
            if chave == "user-agent":
                if not lendo_agentes:  # User-agent depois de regra abre grupo novo
                    self.grupos.append({"agentes": set(), "regras": [], "atrasos": []})
                    lendo_agentes = True
                self.grupos[-1]["agentes"].add(produto(valor))
                self.linhas_reconhecidas += 1
            elif chave in ("allow", "disallow", "crawl-delay"):
                lendo_agentes = False
                self.linhas_reconhecidas += 1
                if not self.grupos:  # regra antes de qualquer User-agent não pertence a grupo
                    continue
                grupo = self.grupos[-1]
                if chave == "crawl-delay":
                    try:
                        grupo["atrasos"].append(float(valor))
                    except ValueError:
                        pass
                elif valor:  # "Disallow:" vazio não proíbe nada
                    grupo["regras"].append((normalizar_caminho(valor, regra=True), chave == "allow"))

    def nome_do_grupo(self, agente):
        """O nome do grupo que vale para `agente` ("*" se só o geral), ou None se nenhum vale."""
        nome = produto(agente)
        if any(nome in grupo["agentes"] for grupo in self.grupos):
            return nome
        if any("*" in grupo["agentes"] for grupo in self.grupos):
            return "*"
        return None

    def _grupos_para(self, agente):
        nome = self.nome_do_grupo(agente)
        return [grupo for grupo in self.grupos if nome in grupo["agentes"]]

    def permite(self, agente, endereco):
        partes = urlsplit(endereco)
        alvo = normalizar_caminho((partes.path or "/") + ("?" + partes.query if partes.query else ""))
        vencedora = None  # (comprimento da regra, é Allow)
        for grupo in self._grupos_para(agente):
            for regra, permitida in grupo["regras"]:
                candidata = (len(regra), permitida)
                # A tupla maior vence: a regra mais longa e, no empate, o Allow (True > False).
                if casa(regra, alvo) and (vencedora is None or candidata > vencedora):
                    vencedora = candidata
        return True if vencedora is None else vencedora[1]

    def atraso(self, agente):
        atrasos = [valor for grupo in self._grupos_para(agente) for valor in grupo["atrasos"]]
        return max(atrasos) if atrasos else None


class Visitante:
    """Uma sessão com espera antes de cada pedido e contagem dos pedidos feitos."""

    def __init__(self):
        self.sessao = requests.Session()
        self.sessao.headers["User-Agent"] = USER_AGENT
        self.pedidos = 0

    def get(self, endereco, conferir=None):
        """Pede `endereco` e segue até MAX_SALTOS redirecionamentos, um pedido de cada vez.

        O requests seguiria o redirecionamento sozinho, sem perguntar ao robots.txt: uma página
        permitida que redireciona para caminho proibido, ou para outro site, seria pedida. Aqui
        cada destino passa antes por `conferir` (quando dado); se não passar, nada é pedido e a
        função devolve None. Devolve None também em erro de rede e depois de saltos demais.
        """
        saltos = []
        for _ in range(MAX_SALTOS + 1):
            time.sleep(ESPERA)
            self.pedidos += 1
            try:
                resposta = self.sessao.get(endereco, timeout=30, allow_redirects=False)
            except requests.RequestException as erro:
                print(f"  erro ao pedir {endereco}: {erro}")
                return None
            if not resposta.is_redirect:
                resposta.history = saltos  # `sinais` usa o histórico para achar redirecionamento a login
                return resposta
            saltos.append(resposta)
            endereco = urljoin(resposta.url, resposta.headers["Location"])
            if conferir is not None and not conferir(endereco):
                return None
        print(f"  {saltos[0].url}: mais de {MAX_SALTOS} redirecionamentos seguidos, desisti")
        return None


def titulo(texto):
    print(f"\n== {texto} ==")


def conferir_robots(visitante, endereco):
    partes = urlsplit(endereco)
    endereco_robots = f"{partes.scheme}://{partes.netloc}/robots.txt"
    resposta = visitante.get(endereco_robots)
    titulo("1. robots.txt")
    print(f"Endereço: {endereco_robots}")
    proibe_tudo = RegrasRobots("User-agent: *\nDisallow: /")
    if resposta is None:
        print("Sem resposta: trate como proibição enquanto durar (RFC 9309). Não colete agora.")
        return proibe_tudo, False
    print(f"Código: {resposta.status_code}")
    if resposta.status_code >= 500:
        print("Erro do servidor: trate como proibição enquanto durar (RFC 9309). Não colete agora.")
        return proibe_tudo, False
    if resposta.status_code >= 400:
        print("Não existe robots.txt. O site não declarou regra para robôs.")
        if resposta.status_code in (401, 403):
            print("ATENÇÃO: 401/403 no robots.txt. Confira se a página também recusa o requests (bloqueio).")
        return RegrasRobots(""), True
    # Decide pelo conteúdo, não pelo Content-Type: há servidor que entrega o robots.txt como
    # text/html, e há site que responde com uma página HTML qualquer onde não há robots.txt.
    # O arquivo é UTF-8 (RFC 9309, 2.3). `resposta.text` não serve: com `text/plain` sem charset,
    # o requests decodifica como ISO-8859-1, o BOM vira "ï»¿" e "/licitação" vira outra palavra.
    texto = resposta.content.decode("utf-8", errors="replace")
    regras = RegrasRobots(texto)
    tipo = resposta.headers.get("Content-Type", "")
    if "html" in tipo.lower():
        print(f"O servidor entregou o arquivo como {tipo!r}; o que vale é o conteúdo.")
    if not regras.linhas_reconhecidas:
        print("O arquivo não traz nenhuma regra para robôs (User-agent, Allow, Disallow): o site não declarou regra.")
    else:
        linhas = texto.splitlines()
        print("Conteúdo:")
        for linha in linhas[:60]:
            print(f"  | {linha}")
        if len(linhas) > 60:
            print(f"  | ... ({len(linhas) - 60} linhas a mais)")
    caminho = partes.path or "/"
    if partes.query:
        caminho += "?" + partes.query
    grupo = regras.nome_do_grupo(USER_AGENT)
    if grupo is not None:
        print(f"Grupo que vale para este robô: User-agent: {grupo}")
    permitido = regras.permite(USER_AGENT, endereco)
    print(f"Caminho {caminho!r} permitido para este robô: {'sim' if permitido else 'NÃO'}")
    atraso = regras.atraso(USER_AGENT)
    if atraso:
        print(f"Crawl-delay: {atraso:g} s (o raspador deve esperar max(1, {atraso:g}) s entre pedidos)")
    return regras, permitido


def links_de_termos(pagina_html, base):
    achados = []
    for href, texto in re.findall(r"<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", pagina_html, re.IGNORECASE | re.DOTALL):
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
    if resposta.history and re.search(r"login|entrar|signin|auth", resposta.url, re.IGNORECASE):
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

    def pode_pedir(alvo):
        """Todo pedido depois do robots.txt passa por aqui: a página inicial, os scripts, a API e
        cada destino de redirecionamento."""
        if not mesmo_site(alvo, raiz):
            print(f"  {alvo}: outro site, não pedido")
            return False
        if robots.permite(USER_AGENT, alvo):
            return True
        print(f"  {alvo}: proibido pelo robots.txt, não pedido")
        return False

    paginas = {}
    for alvo in dict.fromkeys([endereco, raiz]):
        if not pode_pedir(alvo):
            continue
        resposta = visitante.get(alvo, conferir=pode_pedir)
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
        if re.search(r"<meta[^>]+name=[\"']robots[\"'][^>]*noindex", principal.text, re.IGNORECASE):
            print("  meta robots noindex: pede que buscadores não indexem; não proíbe acesso.")
        texto_visivel = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", principal.text, flags=re.DOTALL)
        palavras = len(texto_visivel.split())
        print(f"  Texto visível: cerca de {palavras} palavras.")
        if re.search(r"carregando|loading", texto_visivel, re.IGNORECASE) or palavras < 40:
            print("  A página parece ser preenchida por script: procure a API (seção 5 e scripts).")
        for pagina in paginas.values():
            for src in re.findall(r"<script[^>]+src=[\"']([^\"']+)[\"']", pagina.text, re.IGNORECASE):
                completo = urljoin(pagina.url, html.unescape(src))
                if mesmo_site(completo, raiz) and completo not in scripts_externos:
                    scripts_externos.append(completo)
        chamadas = sum(len(PADRAO_CHAMADA.findall(p.text)) for p in paginas.values())
        print(f"  Scripts do mesmo site: {len(scripts_externos)}; chamadas fetch/axios/ajax no HTML: {chamadas}")

    titulo("5. API candidatos")
    textos = [p.text for p in paginas.values()]
    for src in scripts_externos[:10]:
        if not pode_pedir(src):
            continue
        resposta = visitante.get(src, conferir=pode_pedir)
        if resposta is not None and resposta.ok:
            textos.append(resposta.text)
    candidatos = candidatos_de_api(textos, raiz)
    if not candidatos:
        print("Nenhum endereço com cara de API no HTML nem nos scripts do mesmo site.")
        print("Se a página mostra os resultados no HTML, raspe o HTML; se não, leia os scripts à mão.")
    for candidato in candidatos[: argumentos.max_testes]:
        if not pode_pedir(candidato):
            continue
        resposta = visitante.get(candidato, conferir=pode_pedir)
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
