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
ou, sem uv:
    python -m pip install requests pandas
    python raspador_<site>.py --pesquisa "<termo>"
"""

import argparse
import sys
import time
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


class AcessoNegado(Exception):
    """O site respondeu 401 ou 403: o dado pede login ou o site recusou o robô."""


def segundos_para_esperar(resposta, padrao):
    """Lê o cabeçalho Retry-After, que vem em segundos ("2") ou como data; sem ele, usa `padrao`."""
    valor = resposta.headers.get("Retry-After")
    if not valor:
        return padrao
    if valor.strip().isdigit():
        return float(valor)
    try:
        return max(0.0, parsedate_to_datetime(valor).timestamp() - time.time())
    except (TypeError, ValueError):
        return padrao


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
            print(f"  {resposta.status_code}: esperando {espera:.0f} s (tentativa {tentativa})", file=sys.stderr)
            time.sleep(espera)
            continue
        resposta.raise_for_status()
    raise RuntimeError(f"{endereco} continuou respondendo {resposta.status_code} depois de {TENTATIVAS} tentativas")


# ADAPTAR: os nomes dos parâmetros que o site usa para a busca e para a página.
def parametros_da_pagina(pesquisa, pagina):
    return {"pesquisa": pesquisa, "pagina": pagina}


# ADAPTAR: onde o site informa o total de resultados (para saber quando parar e para conferir).
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
        Um DataFrame com uma linha por resultado. O total que o site informou fica em
        `tabela.attrs["total_informado"]`.
    """
    sessao = requests.Session()  # guarda os cookies entre um pedido e outro, como um navegador
    sessao.headers["User-Agent"] = USER_AGENT
    linhas, total_informado, anteriores = [], None, None
    pagina = 1
    while True:
        resposta = pedir(sessao, ENDERECO_BUSCA, parametros_da_pagina(pesquisa, pagina))
        if resposta is None:  # 404: não há esta página
            break
        dados = resposta.json()
        if total_informado is None:
            total_informado = ler_total(dados)
            print(f"O site informa {total_informado} resultados para {pesquisa!r}.", file=sys.stderr)
        novos = ler_resultados(dados)
        if not novos:  # página vazia: acabou
            break
        if novos == anteriores:  # o site ignorou o número da página e devolveu a mesma de novo
            raise RuntimeError(f"a página {pagina} repetiu a anterior; confira o parâmetro de paginação")
        linhas.extend(novos)
        print(f"  página {pagina}: {len(novos)} resultados ({len(linhas)} até agora)", file=sys.stderr)
        anteriores = novos
        if total_informado is not None and len(linhas) >= total_informado:
            break
        if max_paginas is not None and pagina >= max_paginas:
            break
        pagina += 1
    tabela = pd.DataFrame(linhas)
    tabela.attrs["total_informado"] = total_informado
    return tabela


def main():
    leitor = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    leitor.add_argument("--pesquisa", required=True, help="termo de busca")
    leitor.add_argument("--saida", default="resultados.csv", help="arquivo CSV de saída")
    leitor.add_argument("--max-paginas", type=int, default=None, help="para depois de N páginas")
    argumentos = leitor.parse_args()

    tabela = coletar(argumentos.pesquisa, argumentos.max_paginas)
    # utf-8-sig: o Excel reconhece a codificação e mostra os acentos certos.
    tabela.to_csv(argumentos.saida, index=False, encoding="utf-8-sig")

    total = tabela.attrs["total_informado"]
    print(f"{len(tabela)} linhas salvas em {argumentos.saida}; o site informou {total}.")
    if argumentos.max_paginas is None and total is not None and len(tabela) != total:
        print("Atenção: o número de linhas não bate com o total do site.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
