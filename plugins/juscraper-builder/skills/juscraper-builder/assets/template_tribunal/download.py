"""Camada HTTP da busca de jurisprudência do TJXX.

Template da skill juscraper-builder. ``build_cjsg_payload`` e as constantes
de URL são públicos porque o script de captura
(``tests/fixtures/capture/tjxx.py``) e os testes de contrato os importam:
mudar o payload aqui quebra a captura e o contrato juntos, em vez de deixar
os samples divergirem em silêncio.

O builder e o manager recebem o modelo já validado pelo client. Assim o
schema continua sendo a única lista de filtros: nenhum dos dois repete os
parâmetros em assinatura própria.
"""
from __future__ import annotations

import math
import time

from tqdm import tqdm

from juscraper.core.http import RequestFn
from juscraper.utils.params import normalize_paginas

from .schemas import InputCJSGTJXX

BASE_URL = "https://www.tjxx.jus.br/api/jurisprudencia/pesquisa"  # TODO: endpoint real
RESULTS_PER_PAGE = 10  # TODO: itens por página que o backend devolve

#: Nome canônico do filtro no juscraper -> nome do campo no corpo do backend.
#: TODO: trocar pelos nomes capturados na engenharia reversa.
CAMPOS_BACKEND: dict[str, str] = {
    "relator": "relator",
    "classe": "classe",
    "data_julgamento_inicio": "dataJulgamentoInicio",
    "data_julgamento_fim": "dataJulgamentoFim",
    "data_publicacao_inicio": "dataPublicacaoInicio",
    "data_publicacao_fim": "dataPublicacaoFim",
}


def build_cjsg_payload(inp: InputCJSGTJXX, pagina: int = 1) -> dict:
    """Monta o corpo da requisição de busca de uma página.

    Args:
        inp (InputCJSGTJXX): Entrada validada; as datas já estão no
            ``BACKEND_DATE_FORMAT`` do schema.
        pagina (int): Página 1-based. Default ``1``.

    Returns:
        dict: Corpo pronto para ``json=`` ou ``data=``. Filtro vazio fica fora.
    """
    payload: dict = {"texto": inp.pesquisa, "pagina": pagina, "tamanho": RESULTS_PER_PAGE}
    for campo, chave in CAMPOS_BACKEND.items():
        valor = getattr(inp, campo)
        # ``is not None``, e não verdade: filtro com valor 0 ou False é filtro.
        if valor is not None:
            payload[chave] = valor
    return payload


def _total_resultados(resposta: dict) -> int:
    """Lê o total de resultados da primeira página. TODO: ajustar à resposta real."""
    return int(resposta.get("total", 0))


def cjsg_download_manager(
    inp: InputCJSGTJXX,
    *,
    request_fn: RequestFn,
    sleep_time: float = 1.0,
) -> list:
    """Baixa as páginas brutas da busca de jurisprudência.

    Args:
        inp (InputCJSGTJXX): Entrada validada; ``inp.paginas`` é 1-based e
            ``None`` baixa todas.
        request_fn (RequestFn): ``TJXXScraper._request_with_retry``, que
            aplica retry com backoff e ``raise_for_status``.
        sleep_time (float): Pausa em segundos entre páginas. Default ``1.0``.

    Returns:
        list: Uma resposta JSON por página baixada.
    """
    def _baixar(pagina: int) -> dict:
        # TODO: GET com ``params=`` ou POST com ``data=`` conforme o site. Sem
        # ``timeout=`` literal: ele venceria o perfil e o ``politica=`` do usuário.
        resp = request_fn("POST", BASE_URL, json=build_cjsg_payload(inp, pagina), perfil="cjsg")
        dados: dict = resp.json()
        return dados

    # O schema aceita ``int`` (``paginas=3`` é ``range(1, 4)``); normalize_paginas
    # devolve sempre ``list``, ``range`` ou ``None``.
    paginas = normalize_paginas(inp.paginas)
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
