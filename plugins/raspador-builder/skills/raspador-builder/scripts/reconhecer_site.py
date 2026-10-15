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
import sys
import time
from urllib.parse import urljoin, urlsplit

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
# "Disallow: /*?q=" não proíbe nada. O do 3.15 segue a RFC nisso, mas divide a regra no "?" e
# codifica "=" e "&" do lado do caminho, e aí "Disallow: /*sort=" não proíbe "/busca?sort=1". O mesmo
# site daria respostas diferentes conforme a versão de quem roda o script, então a leitura fica aqui.


def _enviados_por_extenso():
    """Os octetos que o requests manda por extenso no caminho e na consulta; os outros vão como %XX.

    Sai do próprio requests, e não de uma lista escrita aqui, para acompanhar a versão instalada
    (na 2.34, por exemplo, ":" e "," vão por extenso e "|" vai como "%7C"). Os octetos ASCII vão
    num endereço só, cada um entre dois "z", que não é dígito hexadecimal nem forma segmento de
    ponto, uma vez no caminho e outra na consulta; um pedido preparado por octeto deixaria o
    script (e cada teste que o carrega) uma décima de segundo mais lento. Conta como por extenso o
    octeto que volta como ele mesmo, seguido do "z", nas duas partes; o que volta como "%" mais
    dois dígitos foi codificado, e o que não volta foi descartado. O "#" abriria o fragmento, que
    não é enviado, e fica fora; o "%" volta como "%25". Octeto acima de 127 é sempre codificado.
    """
    caracteres = [chr(valor) for valor in range(128) if chr(valor) != "#"]
    texto = "z" + "z".join(caracteres) + "z"
    partes = []
    for endereco in (f"http://x/{texto}", f"http://x/?{texto}"):
        try:
            enviado = requests.Request("GET", endereco).prepare().path_url
        except (requests.RequestException, ValueError):
            return frozenset()  # sem como saber: todo octeto conta 3, como o codificado
        posicao = enviado.index("z") + 1
        por_extenso = set()
        for caractere in caracteres:
            if enviado.startswith(caractere + "z", posicao):
                por_extenso.add(ord(caractere))
                posicao += 2
            elif enviado.startswith("%", posicao):
                posicao += 4
            else:  # descartado pelo requests: o que está aqui já é o "z" seguinte
                posicao += 1
        partes.append(por_extenso)
    return frozenset(partes[0] & partes[1])


ENVIADOS_POR_EXTENSO = _enviados_por_extenso()

# Os reservados que dão a estrutura do endereço em cada parte dele. Ali, por extenso e codificados
# têm sentidos diferentes: no caminho, "/" separa segmentos e "%2F" é letra de um segmento; o
# primeiro "?" abre a consulta e "%3F" é letra; na consulta, "&" e "=" separam os parâmetros e
# "%26" e "%3D" são parte do valor. Fora da sua parte, cada um deles vale o mesmo nas duas grafias.
ESTRUTURAIS = {"caminho": frozenset(b"/?"), "consulta": frozenset(b"&=")}
PODEM_SER_ESTRUTURAIS = ESTRUTURAIS["caminho"] | ESTRUTURAIS["consulta"]
# Um octeto estrutural do endereço vira um caractere da área de uso privado do Unicode, longe dos
# 256 valores de octeto, com uma faixa para a grafia por extenso e outra para a codificada.
POR_EXTENSO, CODIFICADO = 0xE000, 0xE100
# Uma sequência de %XX, ou uma sequência sem "%", ou um "%" solto.
PADRAO_OCTETOS = re.compile(r"((?:%[0-9A-Fa-f]{2})+)|([^%]+|%)")


def octetos(texto):
    """Os octetos do texto, cada um como (valor, veio codificado como %XX?).

    "%62" e "b" dão o mesmo valor; "ç" dá os dois octetos do UTF-8. Um "%" sem dois dígitos
    hexadecimais depois é o próprio "%", que o requests manda como "%25". Não decodifica duas
    vezes: "%2541" são os octetos "%", "4" e "1".
    """
    saida = []
    for codificados, por_extenso in PADRAO_OCTETOS.findall(texto):
        if codificados:
            saida += [(octeto, True) for octeto in bytes.fromhex(codificados.replace("%", ""))]
        else:
            saida += [(octeto, False) for octeto in por_extenso.encode("utf-8")]
    return saida


def caminho_enviado(endereco):
    """O caminho e a consulta exatamente como o requests os manda ao servidor.

    O requests (com o urllib3) codifica o que não pode ir por extenso ("|" vira "%7C", "ç" vira
    "%C3%A7", "%" solto vira "%25"), decodifica os não reservados ("%7E" vira "~"), resolve os
    segmentos "." e ".." (RFC 3986, 5.2.4, também em endereço absoluto) e tira o fragmento. A
    regra do robots.txt tem de ser conferida contra esse caminho, e não contra o que foi escrito.
    """
    try:
        return requests.Request("GET", endereco).prepare().path_url
    except (requests.RequestException, ValueError):  # endereço que o requests nem pediria
        partes = urlsplit(endereco)
        return (partes.path or "/") + ("?" + partes.query if partes.query else "")


def sem_segmentos_de_ponto(caminho):
    """O caminho com "." e ".." resolvidos (RFC 3986, 5.2.4); a consulta fica como está."""
    parte_caminho, interrogacao, consulta = caminho.partition("?")
    segmentos = parte_caminho.split("/")[1:]
    resolvidos = []
    for segmento in segmentos:
        if segmento == "..":
            if resolvidos:
                resolvidos.pop()
        elif segmento != ".":
            resolvidos.append(segmento)
    if segmentos and segmentos[-1] in (".", ".."):  # "/a/.." é "/", com a barra do fim
        resolvidos.append("")
    return "/" + "/".join(resolvidos) + interrogacao + consulta


def endereco_enviado(endereco):
    """O endereço inteiro como o requests o pede (ver `caminho_enviado`)."""
    try:
        return requests.Request("GET", endereco).prepare().url
    except (requests.RequestException, ValueError):
        return endereco


def codificar_alvo(caminho):
    """O caminho enviado (com a consulta) como texto em que cada octeto é um caractere.

    O octeto comum vira o caractere de mesmo valor, venha por extenso ou como %XX. O estrutural na
    sua parte do endereço (ver ESTRUTURAIS) vira um caractere de POR_EXTENSO ou de CODIFICADO,
    conforme a grafia. O primeiro "?" por extenso é o separador: estrutural do caminho, e a partir
    dele vale a lista da consulta. "*" e "$" do endereço são letras como as outras.
    """
    codigos = []
    estruturais = ESTRUTURAIS["caminho"]
    for valor, codificado in octetos(caminho):
        if valor in estruturais:
            codigos.append(chr((CODIFICADO if codificado else POR_EXTENSO) + valor))
        else:
            codigos.append(chr(valor))
        if valor == ord("?") and not codificado:
            estruturais = ESTRUTURAIS["consulta"]
    return "".join(codigos)


class Regra:
    """Um caminho de Allow ou Disallow, pronto para casar com o alvo de `codificar_alvo`.

    Critério de comparação. A regra casa com o caminho mais a consulta como uma cadeia só, sem ser
    dividida no "?": o curinga atravessa do caminho para a consulta, e "Disallow: /*sort=" proíbe
    "/busca?sort=1". Os dois lados são comparados octeto a octeto, depois de decodificar o %XX,
    como manda a RFC 9309 (2.2.2): "/%7Euser" e "/~user", ":" e "%3a", "|" e "%7C" são iguais.
    A exceção são os reservados estruturais (ver ESTRUTURAIS), que só casam com a mesma grafia na
    parte do endereço em que são estruturais. Como a regra não sabe em que parte do endereço cada
    letra dela vai cair, um octeto que pode ser estrutural vira uma classe de dois caracteres: o
    comum, para onde ele não é estrutural, e o da sua grafia, para onde é. Assim "/" da regra casa
    com "/" e "%2F" da consulta, mas só com "/" do caminho; "%2F" da regra casa com "%2F" do caminho
    e com "/" e "%2F" da consulta.

    `*` vale qualquer sequência e o `$` final exige o fim do alvo; "%2A" e "%24" são letras.

    Casamento sem retrocesso: cada trecho entre curingas tem tamanho fixo e é procurado uma vez, na
    primeira posição em que aparece depois do trecho anterior. Pegar a primeira ocorrência nunca
    impede um casamento que outra permitiria, porque deixa mais alvo livre para os trechos
    seguintes. Com `.*` no lugar dos curingas, o retrocesso cresceria como potência do tamanho do
    endereço (oito curingas contra 41 letras levavam segundos). O trecho sem octeto que possa ser
    estrutural é texto e se procura com `str.find`; o que tem vira expressão regular de classes,
    sem `*` nem `+`, que também não retrocede.
    """

    def __init__(self, texto, permitida=False):
        self.permitida = permitida
        self.ancorada = texto.endswith("$")
        trechos = [octetos(trecho) for trecho in (texto[:-1] if self.ancorada else texto).split("*")]
        self.trechos = [_trecho(trecho) for trecho in trechos]
        self.tamanhos = [len(trecho) for trecho in trechos]
        # Especificidade (RFC 9309, 2.2.2: vence a regra com mais octetos). Cada octeto conta pelo
        # tamanho com que o requests o manda ao servidor (ver ENVIADOS_POR_EXTENSO): 1 o que vai
        # por extenso, 3 o que vai como %XX. A grafia da regra não muda a conta, porque ":" e
        # "%3A" são o mesmo octeto e empatam; a exceção é o estrutural (ver ESTRUTURAIS), em que
        # "/" e "%2F" são octetos diferentes e vão ao servidor cada um na sua grafia.
        # Curinga e âncora contam 1.
        self.comprimento = len(trechos) - 1 + self.ancorada + sum(
            3 if (codificado and valor in PODEM_SER_ESTRUTURAIS) or valor not in ENVIADOS_POR_EXTENSO else 1
            for trecho in trechos
            for valor, codificado in trecho
        )

    def casa(self, alvo):
        primeiro, *meio = self.trechos
        if not _comeca_em(primeiro, alvo, 0):
            return False
        posicao = self.tamanhos[0]
        if not meio:  # regra sem curinga
            return not self.ancorada or posicao == len(alvo)
        *meio, ultimo = meio
        for trecho in meio:
            posicao = _fim_da_primeira(trecho, alvo, posicao)
            if posicao < 0:
                return False
        if self.ancorada:
            inicio = len(alvo) - self.tamanhos[-1]
            return inicio >= posicao and _comeca_em(ultimo, alvo, inicio)
        return _fim_da_primeira(ultimo, alvo, posicao) >= 0


def _trecho(octetos_do_trecho):
    """Texto, se nenhum octeto pode ser estrutural; senão, expressão regular em que o octeto que
    pode ser estrutural vira a classe dos dois caracteres com que casa (ver `Regra`)."""
    if not any(valor in PODEM_SER_ESTRUTURAIS for valor, _ in octetos_do_trecho):
        return "".join(chr(valor) for valor, _ in octetos_do_trecho)
    partes = []
    for valor, codificado in octetos_do_trecho:
        letra = re.escape(chr(valor))
        if valor in PODEM_SER_ESTRUTURAIS:
            letra = "[" + letra + re.escape(chr((CODIFICADO if codificado else POR_EXTENSO) + valor)) + "]"
        partes.append(letra)
    return re.compile("".join(partes))


def _comeca_em(trecho, alvo, posicao):
    if isinstance(trecho, str):
        return alvo.startswith(trecho, posicao)
    return trecho.match(alvo, posicao) is not None


def _fim_da_primeira(trecho, alvo, posicao):
    """Onde termina a primeira ocorrência do trecho em `alvo` a partir de `posicao`, ou -1."""
    if isinstance(trecho, str):
        inicio = alvo.find(trecho, posicao)
        return -1 if inicio < 0 else inicio + len(trecho)
    achado = trecho.search(alvo, posicao)
    return -1 if achado is None else achado.end()


def casa(regra, caminho):
    """A regra (texto de Allow ou Disallow) casa com o início do caminho enviado?"""
    return Regra(regra).casa(codificar_alvo(caminho))


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
                    grupo["regras"].append(Regra(valor, permitida=chave == "allow"))

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
        caminho = caminho_enviado(endereco)
        # O requests resolve "." e ".." antes de decodificar "%2E": "/a/%2E%2E/privado" vai ao
        # servidor como "/a/../privado", que ele costuma ler como "/privado". Sobrando segmento de
        # ponto, o caminho resolvido também tem de ser permitido.
        resolvido = sem_segmentos_de_ponto(caminho)
        return all(self._permite_caminho(agente, alvo) for alvo in dict.fromkeys([caminho, resolvido]))

    def _permite_caminho(self, agente, caminho):
        alvo = codificar_alvo(caminho)
        vencedora = None  # (comprimento da regra, é Allow)
        for grupo in self._grupos_para(agente):
            for regra in grupo["regras"]:
                candidata = (regra.comprimento, regra.permitida)
                # A tupla maior vence: a regra mais longa e, no empate, o Allow (True > False).
                if regra.casa(alvo) and (vencedora is None or candidata > vencedora):
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
        self.barrado = None  # o destino que `conferir` recusou no último `get`, se houve

    def get(self, endereco, conferir=None):
        """Pede `endereco` e segue até MAX_SALTOS redirecionamentos, um pedido de cada vez.

        O requests seguiria o redirecionamento sozinho, sem perguntar ao robots.txt: uma página
        permitida que redireciona para caminho proibido, ou para outro site, seria pedida. Aqui
        cada destino passa antes por `conferir` (quando dado); se não passar, nada é pedido, o
        destino fica em `self.barrado` e a função devolve None. Devolve None também em erro de
        rede, em redirecionamento sem destino e depois de saltos demais.
        """
        saltos = []
        self.barrado = None
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
            destino = resposta.headers["Location"].strip()
            if not destino:  # urljoin devolveria a própria página, e o laço a pediria seis vezes
                print(f"  {resposta.url}: redirecionamento sem destino (Location vazio), desisti")
                return None
            # O destino é conferido já como o requests vai pedi-lo: com os segmentos "." e ".."
            # resolvidos também no endereço absoluto ("http://site/publico/../privado/x" vai ao
            # servidor como "/privado/x"), que o urljoin deixa como veio.
            endereco = endereco_enviado(urljoin(resposta.url, destino))
            if conferir is not None and not conferir(endereco):
                self.barrado = endereco
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
    caminho = caminho_enviado(endereco)
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


PORTAS_PADRAO = {"http": 80, "https": 443}


def origem(endereco):
    """(esquema, host, porta) do endereço, na forma em que dois endereços do mesmo site coincidem.

    Esquema e host não distinguem maiúsculas (RFC 3986, 3.1 e 3.2.2): "http://LOCALHOST:8000" e
    "http://localhost:8000" são o mesmo site, e o requests manda o host em minúsculas. A porta
    padrão do esquema escrita por extenso ("http://site.gov.br:80") é a mesma que a ausente, e as
    duas viram None. Porta que não é número válido fica no host, para não coincidir com nenhum.
    """
    partes = urlsplit(endereco)
    esquema = partes.scheme.lower()
    try:
        porta = partes.port
    except ValueError:  # o requests nem pediria esse endereço
        return esquema, partes.netloc.lower(), None
    return esquema, partes.hostname or "", None if porta == PORTAS_PADRAO.get(esquema) else porta


def mesmo_site(endereco, base):
    """Mesmo esquema e mesmo host (com a porta). O robots.txt vale só para eles (RFC 9309, 2.3):
    o de http://site.gov.br não diz nada sobre https://site.gov.br."""
    return origem(endereco) == origem(base)


def mesmo_host(endereco, base):
    """Mesmo host e mesma porta, com qualquer esquema (ver `origem`)."""
    return origem(endereco)[1:] == origem(base)[1:]


def no_esquema_da_base(endereco, base):
    """O endereço do mesmo host que `base` (ver `mesmo_host`), com o esquema e o host da base; ou
    None, se for de outro host.

    A página pode escrever o próprio endereço com outro esquema (https atrás de proxy); o pedido
    usa o esquema pelo qual o site respondeu, que é o do robots.txt lido. O host vai na grafia da
    base: "https://site.gov.br:443" trocado só de esquema seria "http://site.gov.br:443".
    """
    if not mesmo_host(endereco, base):
        return None
    partes_base = urlsplit(base)
    return urlsplit(endereco)._replace(scheme=partes_base.scheme, netloc=partes_base.netloc).geturl()


def candidatos_de_api(textos, base):
    vistos = []
    for texto in textos:
        for achado in filter(PARECE_API.search, PADRAO_ENDERECO.findall(html.unescape(texto))):
            completo = no_esquema_da_base(urljoin(base, achado.rstrip(".,;")), base)
            if completo is not None and completo not in vistos:
                vistos.append(completo)
    return vistos


def main():
    leitor_argumentos = argparse.ArgumentParser(description="Reconhecimento antes de raspar.")
    leitor_argumentos.add_argument("endereco", help="endereço da página de busca (com o termo, se der)")
    leitor_argumentos.add_argument("--max-testes", type=int, default=5, help="API candidatos a testar")
    argumentos = leitor_argumentos.parse_args()
    endereco = argumentos.endereco
    partes = urlsplit(endereco)
    # Esquema e host em minúsculas, como o requests os manda: o destino de um redirecionamento vem
    # na grafia do requests e é comparado com esta raiz (ver `origem`). Usuário e senha ficam fora.
    raiz = f"{partes.scheme.lower()}://{partes.netloc.rpartition('@')[2].lower()}/"
    visitante = Visitante()

    robots, permitido = conferir_robots(visitante, endereco)
    if not permitido:
        print("\nPARE: o robots.txt não permite este caminho (ou o servidor não respondeu). Avise o usuário.")
        return 2

    def pode_pedir(alvo):
        """Todo pedido depois do robots.txt passa por aqui: a página inicial, os scripts, a API e
        cada destino de redirecionamento."""
        if not mesmo_site(alvo, raiz):
            if mesmo_host(alvo, raiz):
                print(
                    f"  {alvo}: troca de {partes.scheme} para {urlsplit(alvo).scheme}, não pedido. O robots.txt "
                    f"lido vale só para {raiz}; rode o script de novo com {alvo}"
                )
            else:
                print(f"  {alvo}: outro site, não pedido (para ler o robots.txt de lá, rode o script com ele)")
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
        elif alvo == endereco and visitante.barrado is not None and mesmo_site(visitante.barrado, raiz):
            # Barrado no mesmo site só pode ter sido pelo robots.txt: a página pedida leva a um
            # caminho proibido, e isso vale como pedir o caminho proibido. A conclusão sai ainda na
            # seção 1, antes de qualquer outra.
            print(f"A página pedida redireciona para {visitante.barrado}, que o robots.txt não permite a este robô.")
            print("\nPARE: o robots.txt não permite o destino da página pedida. Avise o usuário.")
            return 2

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
                # Mesmo tratamento do API candidato: o script "https://" do mesmo host numa página
                # http é pedido pelo http, e não some do relatório.
                completo = no_esquema_da_base(urljoin(pagina.url, html.unescape(src)), raiz)
                if completo is not None and completo not in scripts_externos:
                    scripts_externos.append(completo)
        chamadas = sum(len(PADRAO_CHAMADA.findall(p.text)) for p in paginas.values())
        print(f"  Scripts do mesmo site: {len(scripts_externos)}; chamadas fetch/axios/ajax no HTML: {chamadas}")
        for src in scripts_externos:
            print(f"    {src}")

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
