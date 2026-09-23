"""Camada HTTP da busca de jurisprudência do TJXX.

Template da skill juscraper-builder. ``build_cjsg_payload`` e as constantes
de URL são públicos porque o script de captura
(``tests/fixtures/capture/tjxx.py``) e os testes de contrato os importam:
mudar o payload aqui quebra a captura e o contrato juntos, em vez de deixar
os samples divergirem em silêncio.
"""
import math
import time

from tqdm import tqdm

from juscraper.core.http import RequestFn

BASE_URL = "https://www.tjxx.jus.br/api/jurisprudencia/pesquisa"  # TODO: endpoint real
RESULTS_PER_PAGE = 10  # TODO: itens por página que o backend devolve


def build_cjsg_payload(
    pesquisa: str,
    pagina: int = 1,
    *,
    relator: str = "",
    classe: str = "",
    data_julgamento_inicio: str = "",
    data_julgamento_fim: str = "",
    data_publicacao_inicio: str = "",
    data_publicacao_fim: str = "",
) -> dict:
    """Monta o corpo da requisição de busca de uma página.

    Os parâmetros usam os nomes canônicos do juscraper; os nomes de campo do
    backend ficam restritos a esta função.

    Args:
        pesquisa (str): Termo de busca já normalizado.
        pagina (int): Página 1-based. Default ``1``.
        relator (str): Nome do relator; ``""`` omite o filtro.
        classe (str): Classe processual; ``""`` omite o filtro.
        data_julgamento_inicio (str): Data já no ``BACKEND_DATE_FORMAT`` do schema.
        data_julgamento_fim (str): Idem.
        data_publicacao_inicio (str): Idem.
        data_publicacao_fim (str): Idem.

    Returns:
        dict: Corpo pronto para ``json=`` ou ``data=``.
    """
    # TODO: trocar pelos nomes de campo capturados na engenharia reversa.
    payload: dict = {"texto": pesquisa, "pagina": pagina, "tamanho": RESULTS_PER_PAGE}
    if relator:
        payload["relator"] = relator
    if classe:
        payload["classe"] = classe
    if data_julgamento_inicio:
        payload["dataJulgamentoInicio"] = data_julgamento_inicio
    if data_julgamento_fim:
        payload["dataJulgamentoFim"] = data_julgamento_fim
    if data_publicacao_inicio:
        payload["dataPublicacaoInicio"] = data_publicacao_inicio
    if data_publicacao_fim:
        payload["dataPublicacaoFim"] = data_publicacao_fim
    return payload


def _total_resultados(resposta: dict) -> int:
    """Lê o total de resultados da primeira página. TODO: ajustar à resposta real."""
    return int(resposta.get("total", 0))


def cjsg_download_manager(
    pesquisa: str,
    paginas=None,
    *,
    request_fn: RequestFn,
    sleep_time: float = 1.0,
    **filtros,
) -> list:
    """Baixa as páginas brutas da busca de jurisprudência.

    Args:
        pesquisa (str): Termo de busca já normalizado.
        paginas (list | range | None): Páginas 1-based; ``None`` baixa todas.
        request_fn (RequestFn): ``TJXXScraper._request_with_retry``, que
            aplica retry com backoff e ``raise_for_status``.
        sleep_time (float): Pausa em segundos entre páginas. Default ``1.0``.
        **filtros: Encaminhados a :func:`build_cjsg_payload`.

    Returns:
        list: Uma resposta JSON por página baixada.
    """
    def _baixar(pagina: int) -> dict:
        payload = build_cjsg_payload(pesquisa, pagina, **filtros)
        # TODO: GET com ``params=`` ou POST com ``data=`` conforme o site.
        resp = request_fn("POST", BASE_URL, json=payload, timeout=30)
        dados: dict = resp.json()
        return dados

    if paginas is None:
        primeira = _baixar(1)
        resultados = [primeira]
        total = _total_resultados(primeira)
        n_paginas = math.ceil(total / RESULTS_PER_PAGE) if total else 1
        for pagina in tqdm(range(2, n_paginas + 1), desc="Baixando CJSG TJXX"):
            time.sleep(sleep_time)
            resultados.append(_baixar(pagina))
        return resultados

    resultados = []
    for pagina in tqdm(list(paginas), desc="Baixando CJSG TJXX"):
        if resultados:
            time.sleep(sleep_time)
        resultados.append(_baixar(pagina))
    return resultados
