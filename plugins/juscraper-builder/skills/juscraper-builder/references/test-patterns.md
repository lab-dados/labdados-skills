# Testes do raspador novo

A política de testes do juscraper é a do `CONTRIBUTING.md` dele: seção "Tests" (pirâmide, estrutura de samples, ferramentas, marker `anti_bot`) e seção "Adding a new tribunal" (a lista do que o PR precisa ter, que bloqueia o merge). Leia as duas antes de escrever o primeiro teste; este arquivo só ordena o trabalho e traz esqueletos de código para adaptar.

## Ordem de trabalho

1. **Payload builder antes do teste.** `build_<endpoint>_payload` e as constantes de URL ficam públicos em `download.py` (ou `<endpoint>_download.py`), porque o script de captura e os contratos os importam. No template, o builder recebe o `Input*` validado; os testes montam o modelo direto para obter o corpo esperado.
2. **Captura.** Escreva `tests/fixtures/capture/<xx>.py` e rode contra o backend real (`uv run python -m tests.fixtures.capture.<xx>`). Ele grava os cenários que o `CONTRIBUTING.md` exige em `tests/<xx>/samples/<endpoint>/`. Se o raspador configura cabeçalhos de navegador ou cookie de WAF, capture com a sessão do próprio raspador, senão o sample vem de uma resposta que a produção nunca recebe. Saneamento (truncar campos grandes, redigir dados pessoais) fica dentro do script.
3. **Contrato** (`test_<endpoint>_contract.py`): API pública com `responses`, sample servido, matcher de payload, colunas por subset.
4. **Filtros e aliases** (`test_<endpoint>_filters_contract.py`): todos os filtros mapeados na Etapa 1 da skill numa só chamada, conferidos contra um corpo literal com os nomes de campo do backend, e um teste por alias deprecado aceito, este sim comparado ao corpo que o builder monta para o nome canônico.
5. **Schema**: teste do `Input*` e registro nos arquivos de `tests/schemas/` listados no `CONTRIBUTING.md`.
6. **Integração**, opcional: `test_<endpoint>_integration.py` com marker `integration`.
7. Rode `uv run pytest tests/<xx> tests/schemas`.

Conjunto de referência para copiar a forma: `tests/tjro/` (contrato, filtros, aliases específicos do tribunal) e `tests/fixtures/capture/tjrs.py` (captura com saneamento, citada pelo `CONTRIBUTING.md`). Para portal com sessão própria e bot manager, os testes do `cjsg` do TRF3 (ver `juscraper-conventions.md`).

## Armadilhas que a suíte pega

- `filterwarnings = ["error"]` no `pyproject.toml`: warning não esperado quebra o teste. Alias deprecado se testa com `pytest.warns(DeprecationWarning)`, e o `match=` precisa casar com todos os avisos do bloco: o pytest reemite os que não casam, e o `error` os transforma em falha (caso de `data_inicio` e `data_fim` na mesma chamada).
- Em teste de filtro de data, passe `*_inicio` e `*_fim` juntos: com uma ponta só, `fill_open_ended_dates` completa a outra e emite `UserWarning`.
- `query_param_matcher` em GET: filtre os `None` antes, porque o `requests` os tira da URL.
- `responses` levanta `ConnectionError` quando o corpo enviado não bate com o matcher. Compare com o payload builder, não afrouxe o matcher.
- Não teste contagem exata nem ordem de resultados contra o site real.

## Esqueleto: script de captura

```python
"""Captura samples de cjsg do {SIGLA}.

Rodar da raiz do repositório::

    python -m tests.fixtures.capture.{tribunal}
"""
import logging

import juscraper as jus
from juscraper.courts.{tribunal}.download import BASE_URL, build_cjsg_payload
from juscraper.courts.{tribunal}.schemas import InputCJSG{SIGLA}

from ._util import dump, samples_dir_for

logger = logging.getLogger(__name__)


def _capturar(session, destino, pesquisa, pagina, arquivo):
    payload = build_cjsg_payload(InputCJSG{SIGLA}(pesquisa=pesquisa), pagina)
    resp = session.post(BASE_URL, json=payload, timeout=30)  # ADAPTAR: método e corpo reais
    resp.raise_for_status()
    dump(destino / arquivo, resp.content)  # sanear aqui, se preciso
    logger.info("gravado %s", arquivo)


def main() -> None:
    # Script novo não ganha dispensa de T201 no ruff.toml: logging, não print.
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    destino = samples_dir_for("{tribunal}", "cjsg")
    # Sessão do raspador: leva os cabeçalhos que o _configure_session aplica.
    session = jus.scraper("{tribunal}").session
    _capturar(session, destino, "dano moral", 1, "results_normal_page_01.json")
    _capturar(session, destino, "dano moral", 2, "results_normal_page_02.json")
    _capturar(session, destino, "mandado de seguranca", 1, "single_page.json")
    _capturar(session, destino, "juscraper_probe_zero_hits_xyzqwe", 1, "no_results.json")


if __name__ == "__main__":
    main()
```

## Esqueleto: contrato de cjsg

```python
"""Contratos offline de cjsg do {SIGLA}."""
import pandas as pd
import responses
from responses.matchers import json_params_matcher

import juscraper as jus
from juscraper.courts.{tribunal}.download import BASE_URL, build_cjsg_payload
from juscraper.courts.{tribunal}.schemas import InputCJSG{SIGLA}
from tests._helpers import load_sample

# Colunas do OutputCJSG{SIGLA}; conferidas por subset, nunca por igualdade.
CJSG_MIN_COLUMNS = {"processo", "classe", "relator", "data_julgamento", "ementa"}


def _add_page(pesquisa: str, pagina: int, sample: str) -> None:
    responses.add(
        responses.POST,
        BASE_URL,
        body=load_sample("{tribunal}", sample),
        status=200,
        content_type="application/json",
        match=[json_params_matcher(build_cjsg_payload(InputCJSG{SIGLA}(pesquisa=pesquisa), pagina))],
    )


@responses.activate
def test_cjsg_typical_com_paginacao(mocker):
    mocker.patch("time.sleep")
    _add_page("dano moral", 1, "cjsg/results_normal_page_01.json")
    _add_page("dano moral", 2, "cjsg/results_normal_page_02.json")

    df = jus.scraper("{tribunal}").cjsg("dano moral", paginas=range(1, 3))

    assert isinstance(df, pd.DataFrame)
    assert set(df.columns) >= CJSG_MIN_COLUMNS
    assert len(df) > 0


@responses.activate
def test_cjsg_single_page(mocker):
    mocker.patch("time.sleep")
    _add_page("mandado de seguranca", 1, "cjsg/single_page.json")

    df = jus.scraper("{tribunal}").cjsg("mandado de seguranca", paginas=1)

    assert set(df.columns) >= CJSG_MIN_COLUMNS


@responses.activate
def test_cjsg_no_results(mocker):
    mocker.patch("time.sleep")
    _add_page("juscraper_probe_zero_hits_xyzqwe", 1, "cjsg/no_results.json")

    df = jus.scraper("{tribunal}").cjsg("juscraper_probe_zero_hits_xyzqwe", paginas=1)

    assert df.empty
```

## Esqueleto: filtros e aliases deprecados

```python
"""Propagação de filtros e aliases deprecados de cjsg do {SIGLA}."""
import pytest
import responses
from responses.matchers import json_params_matcher

import juscraper as jus
from juscraper.courts.{tribunal}.download import BASE_URL, build_cjsg_payload
from juscraper.courts.{tribunal}.schemas import InputCJSG{SIGLA}
from tests._helpers import assert_unknown_kwarg_raises, load_sample


def _esperado(pesquisa: str, pagina: int = 1, **filtros) -> dict:
    """Corpo que o backend deve receber; datas já no BACKEND_DATE_FORMAT."""
    return build_cjsg_payload(InputCJSG{SIGLA}(pesquisa=pesquisa, **filtros), pagina)


def _add(payload: dict) -> None:
    responses.add(
        responses.POST,
        BASE_URL,
        body=load_sample("{tribunal}", "cjsg/no_results.json"),
        status=200,
        content_type="application/json",
        match=[json_params_matcher(payload)],
    )


@responses.activate
def test_cjsg_todos_os_filtros_chegam_ao_body(mocker):
    mocker.patch("time.sleep")
    # Corpo literal, com os nomes de campo do backend vistos na captura. Montar
    # este esperado com build_cjsg_payload esconderia um filtro que o builder
    # deixa de mapear: ele sumiria do esperado e do enviado ao mesmo tempo.
    # Um par chave/valor por filtro confirmado com o usuário na Etapa 1.
    _add({
        "texto": "dano moral",
        "pagina": 1,
        "tamanho": 10,
        "relator": "FULANO DE TAL",
        "classe": "Apelacao",
        "dataJulgamentoInicio": "01/01/2024",
        "dataJulgamentoFim": "31/03/2024",
    })
    jus.scraper("{tribunal}").cjsg(
        "dano moral", paginas=1,
        relator="FULANO DE TAL",
        classe="Apelacao",
        data_julgamento_inicio="2024-01-01",
        data_julgamento_fim="2024-03-31",
    )


@responses.activate
def test_cjsg_alias_query(mocker):
    mocker.patch("time.sleep")
    _add(_esperado("dano moral"))
    with pytest.warns(DeprecationWarning, match="query"):
        jus.scraper("{tribunal}").cjsg(pesquisa=None, query="dano moral", paginas=1)


@responses.activate
def test_cjsg_alias_data_inicio_fim(mocker):
    mocker.patch("time.sleep")
    _add(_esperado(
        "dano moral",
        data_julgamento_inicio="01/01/2024",
        data_julgamento_fim="31/03/2024",
    ))
    # Os dois aliases emitem um aviso cada; o padrão precisa casar com ambos.
    with pytest.warns(DeprecationWarning, match=r"'data_(inicio|fim)'"):
        jus.scraper("{tribunal}").cjsg(
            "dano moral", paginas=1, data_inicio="01/01/2024", data_fim="31/03/2024",
        )


# Repetir para ``termo``, ``*_de``/``*_ate`` e cada alias específico do
# tribunal (ex.: ``magistrado`` -> ``relator``). O caso de alias que vira noop
# com ``warn_unsupported`` está descrito no CONTRIBUTING.md.


def test_cjsg_kwarg_desconhecido():
    assert_unknown_kwarg_raises(
        jus.scraper("{tribunal}").cjsg, "kwarg_inventado", "dano moral", paginas=1,
    )
```

## Esqueleto: integração (opcional)

```python
"""Integração de cjsg do {SIGLA} contra o site real."""
import pandas as pd
import pytest

import juscraper as jus

# Portal com bloqueio anti-bot condicional ao IP acrescenta o marker anti_bot
# a esta lista (ver CONTRIBUTING.md > Tests).
pytestmark = [pytest.mark.integration]


def test_busca_simples():
    df = jus.scraper("{tribunal}").cjsg("direito", paginas=1)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0


def test_paginacao():
    scraper = jus.scraper("{tribunal}")
    df1 = scraper.cjsg("dano moral", paginas=1)
    df2 = scraper.cjsg("dano moral", paginas=range(1, 3))
    assert len(df2) > len(df1)
```

## Esqueleto: contrato de cpopg

```python
"""Contratos offline de cpopg do {SIGLA}."""
import pandas as pd
import responses

import juscraper as jus
from tests._helpers import load_sample_bytes


@responses.activate
def test_cpopg_retorna_dataframe(mocker):
    mocker.patch("time.sleep")
    responses.add(
        responses.GET,
        "https://{url_do_detalhe}",  # ADAPTAR
        body=load_sample_bytes("{tribunal}", "cpopg/detail_normal.html"),
    )
    df = jus.scraper("{tribunal}").cpopg("NNNNNNN-DD.AAAA.J.TT.OOOO")
    assert isinstance(df, pd.DataFrame)
    # id_cnj vem de OutputCnjConsultaBase; acrescentar as colunas do Output concreto.
    assert {"id_cnj"} <= set(df.columns)
```
