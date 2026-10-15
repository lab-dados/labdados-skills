# /// script
# requires-python = ">=3.9"
# dependencies = ["requests", "pandas"]
# ///
"""Coleta <O QUE> de <NOME DO SITE> e salva em CSV.

Modelo da skill raspador-builder. Os trechos marcados com ADAPTAR mudam de site para site;
o resto (espera entre pedidos, tratamento de 404, 403 e 429, paginação, CSV) fica como está.

Fonte: <ENDEREÇO>, lida pela <API em JSON | página HTML>, conferida em <DATA>.
robots.txt: <O QUE DIZ, ou "não existe (404)">.

Como rodar:
    uv run raspador_<site>.py --pesquisa "<termo>"
ou, sem uv (no Windows, `python` no lugar de `python3`):
    python3 -m pip install requests pandas
    python3 raspador_<site>.py --pesquisa "<termo>"
"""

import argparse
import sys
import time
from datetime import timezone
from email.utils import parsedate_to_datetime

import pandas as pd
import requests

# ADAPTAR: o endereço que devolve os resultados (a API, ou a página de busca em HTML).
ENDERECO_BUSCA = "https://exemplo.gov.br/api/busca"
# ADAPTAR: quem roda o programa e para quê. O site sabe de onde vêm os pedidos e com quem falar.
USER_AGENT = "raspador-de-pesquisa/1.0 (coleta academica; contato: SEU-EMAIL)"
# Segundos de espera antes de cada pedido. Não diminuir; aumentar se o robots.txt pedir Crawl-delay.
ESPERA = 1.0
# Quantas vezes repetir um pedido que voltou 429 (pedidos demais) ou 5xx (erro do servidor).
TENTATIVAS = 4
# Maior espera, em segundos, que o programa aceita quando o site pede para esperar (Retry-After).
# Se o site pedir mais, a coleta para com o que já tem: melhor rodar de novo mais tarde do que
# deixar o programa parado por horas sem dizer nada.
TETO_ESPERA = 120


class AcessoNegado(Exception):
    """O site respondeu 401 ou 403: o dado pede login ou o site recusou o robô."""


class ColetaInterrompida(Exception):
    """A coleta parou no meio; `tabela` guarda o que veio até ali, para ser gravado mesmo assim."""

    def __init__(self, motivo, tabela):
        super().__init__(motivo)
        self.tabela = tabela


def segundos_para_esperar(resposta, padrao):
    """Lê o cabeçalho Retry-After, que vem em segundos ("2") ou como data; sem ele, usa `padrao`."""
    valor = resposta.headers.get("Retry-After")
    if not valor:
        return padrao
    if valor.strip().isdigit():
        return float(valor)
    try:
        data = parsedate_to_datetime(valor)
    except (TypeError, ValueError):
        return padrao
    if data.tzinfo is None:
        # Data de HTTP é sempre em GMT. Sem fuso (ou com "-0000"), o Python a devolve sem fuso, e
        # `timestamp()` a leria como hora local: no Brasil, três horas a mais de espera.
        # (`datetime.UTC`, que o ruff sugere, só existe a partir do Python 3.11.)
        data = data.replace(tzinfo=timezone.utc)  # noqa: UP017
    return max(0.0, data.timestamp() - time.time())


def pedir(sessao, endereco, parametros):
    """Faz um GET e devolve a resposta; devolve None se a página não existe (404).

    A espera vem antes de cada pedido, inclusive o primeiro: assim nunca saem dois pedidos com
    menos de ESPERA segundos entre eles, mesmo quando uma tentativa é repetida.
    """
    for tentativa in range(1, TENTATIVAS + 1):
        time.sleep(ESPERA)
        resposta = sessao.get(endereco, params=parametros, timeout=30)
        if resposta.status_code == 200:
            return resposta
        if resposta.status_code == 404:
            return None
        if resposta.status_code in (401, 403):
            # Não tentar de novo nem contornar: o site disse que este acesso não é permitido.
            raise AcessoNegado(f"{resposta.status_code} em {resposta.url}: {resposta.text[:200]}")
        if resposta.status_code == 429 or resposta.status_code >= 500:
            espera = segundos_para_esperar(resposta, padrao=ESPERA * 2**tentativa)
            if espera > TETO_ESPERA:
                raise RuntimeError(
                    f"{resposta.status_code} em {resposta.url}: o site pediu {espera:.0f} s de espera, mais que "
                    f"o teto de {TETO_ESPERA} s (TETO_ESPERA). Rode de novo mais tarde."
                )
            print(f"  {resposta.status_code}: esperando {espera:.0f} s (tentativa {tentativa})", file=sys.stderr)
            time.sleep(espera)
            continue
        resposta.raise_for_status()
    raise RuntimeError(f"{endereco} continuou respondendo {resposta.status_code} depois de {TENTATIVAS} tentativas")


# ADAPTAR: os nomes dos parâmetros que o site usa para a busca e para a página.
def parametros_da_pagina(pesquisa, pagina):
    return {"pesquisa": pesquisa, "pagina": pagina}


# ADAPTAR: onde o site informa o total de resultados (para saber quando parar e para conferir).
# Se o site não informa, devolva None.
def ler_total(dados):
    return dados["total"]


# ADAPTAR: uma linha por resultado, só com os campos pedidos, com nomes de coluna em português.
def ler_resultados(dados):
    return [{"data": item["data"], "titulo": item["titulo"]} for item in dados["resultados"]]


def coletar(pesquisa, max_paginas=None):
    """Coleta todos os resultados da busca `pesquisa`, página por página.

    Args:
        pesquisa: o termo de busca, como se digitaria no site.
        max_paginas: para depois desta página (útil para testar); None coleta todas.

    Returns:
        Um DataFrame com uma linha por resultado. O total que o site informou (ou None) fica em
        `tabela.attrs["total_informado"]`.

    Raises:
        ColetaInterrompida: algo deu errado no meio; o que já foi coletado está em `erro.tabela`.
    """
    sessao = requests.Session()  # guarda os cookies entre um pedido e outro, como um navegador
    sessao.headers["User-Agent"] = USER_AGENT
    linhas, total_informado = [], None
    # As linhas já coletadas, para reconhecer página que só repete o que já veio. Cada linha entra
    # como texto (repr), porque um valor pode ser lista ou dicionário, que não cabem num set.
    vistas = set()
    pagina = 1
    try:
        while True:
            resposta = pedir(sessao, ENDERECO_BUSCA, parametros_da_pagina(pesquisa, pagina))
            if resposta is None:  # 404: não há esta página
                break
            dados = resposta.json()
            novos = ler_resultados(dados)
            if pagina == 1:
                total_informado = ler_total(dados)
                if total_informado is None:
                    print(f"Para {pesquisa!r}, o site não informou o total de resultados.", file=sys.stderr)
                else:
                    print(f"O site informa {total_informado} resultados para {pesquisa!r}.", file=sys.stderr)
            if not novos:  # página vazia: acabou
                break
            chaves = [repr(sorted(linha.items())) for linha in novos]
            if all(chave in vistas for chave in chaves):
                # A página só trouxe linhas que já vieram (na mesma ordem ou não). Na página 2, o
                # site ignorou o número da página e devolveu a primeira: parar com erro, senão o
                # laço não termina e as linhas se repetem. Da 3 em diante, as anteriores já
                # mostraram que a paginação funciona: muitos sites devolvem a última página de
                # novo quando se pede uma além dela, e isso é o fim da coleta.
                if pagina == 2:
                    raise RuntimeError("a página 2 só trouxe linhas da página 1; confira o parâmetro de paginação")
                if total_informado is not None and len(linhas) < total_informado:
                    print(
                        f"  página {pagina} só trouxe linhas já coletadas: fim da coleta, com {len(linhas)} "
                        f"dos {total_informado} resultados informados.",
                        file=sys.stderr,
                    )
                break
            vistas.update(chaves)
            linhas.extend(novos)
            print(f"  página {pagina}: {len(novos)} resultados ({len(linhas)} até agora)", file=sys.stderr)
            if total_informado is not None and len(linhas) >= total_informado:
                break
            if max_paginas is not None and pagina >= max_paginas:
                break
            pagina += 1
    except Exception as erro:
        raise ColetaInterrompida(f"{type(erro).__name__}: {erro}", montar_tabela(linhas, total_informado)) from erro
    return montar_tabela(linhas, total_informado)


def montar_tabela(linhas, total_informado):
    tabela = pd.DataFrame(linhas)
    tabela.attrs["total_informado"] = total_informado
    return tabela


def main():
    leitor = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    leitor.add_argument("--pesquisa", required=True, help="termo de busca")
    leitor.add_argument("--saida", default="resultados.csv", help="arquivo CSV de saída")
    leitor.add_argument("--max-paginas", type=int, default=None, help="para depois de N páginas")
    argumentos = leitor.parse_args()

    try:
        tabela = coletar(argumentos.pesquisa, argumentos.max_paginas)
    except ColetaInterrompida as erro:
        # Grava o que veio antes do erro: uma coleta longa não se perde por causa da última página.
        erro.tabela.to_csv(argumentos.saida, index=False, encoding="utf-8-sig")
        print(f"Coleta interrompida: {erro}", file=sys.stderr)
        print(f"As {len(erro.tabela)} linhas coletadas até aí foram salvas em {argumentos.saida}.", file=sys.stderr)
        return 2
    # utf-8-sig: o Excel reconhece a codificação e mostra os acentos certos.
    tabela.to_csv(argumentos.saida, index=False, encoding="utf-8-sig")

    total = tabela.attrs["total_informado"]
    informado = "o site não informou o total" if total is None else f"o site informou {total}"
    print(f"{len(tabela)} linhas salvas em {argumentos.saida}; {informado}.")
    if argumentos.max_paginas is None and total is not None and len(tabela) != total:
        print("Atenção: o número de linhas não bate com o total do site.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
