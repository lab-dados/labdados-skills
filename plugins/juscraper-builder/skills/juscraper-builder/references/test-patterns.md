# Padrões de Testes

Referência para os testes que acompanham um scraper novo no juscraper.
A fonte da verdade é o `CONTRIBUTING.md` do juscraper, seção "Adding a
new tribunal": o PR fica bloqueado sem **pelo menos um teste de
contrato offline por método público**. Integração contra o site real é
opcional e fica fora do `pytest` padrão.

## Princípios

1. **Contrato offline primeiro**: a API pública é exercitada com
   `responses` servindo samples reais; nada toca a rede, o relógio ou
   TLS real
2. **Samples capturados, nunca sintetizados**: o script de captura
   roda o scraper contra o backend real e grava as respostas cruas
3. **Payload conferido**: matchers do `responses` afirmam o que foi
   enviado ao backend, a partir do `build_<endpoint>_payload` público
4. **Schema por subset**: `{"col_a", "col_b"} <= set(df.columns)`,
   nunca igualdade
5. **Integração marcada e opcional**: `@pytest.mark.integration`,
   excluída por default

## Pirâmide

| Camada | Arquivo | Marker |
|---|---|---|
| Contrato (API pública via `responses` + samples) | `test_<endpoint>_contract.py` | nenhum |
| Granular (função pura) | `test_<endpoint>_granular.py` | nenhum |
| Cassete (`pytest-recording`, caso a caso) | `test_<endpoint>_cassette.py` | `vcr` |
| Integração (tribunal real) | `test_<endpoint>_integration.py` | `integration` |

## Estrutura de arquivo

```
tests/{tribunal}/
├── __init__.py                          # OBRIGATÓRIO (vazio)
├── samples/cjsg/
│   ├── results_normal_page_01.json      # typical, página 1
│   ├── results_normal_page_02.json      # typical, página 2
│   ├── single_page.json                 # página única
│   └── no_results.json                  # sem resultados
├── test_cjsg_contract.py                # cenários typical/single/empty
├── test_cjsg_filters_contract.py        # todos os filtros + aliases deprecados
└── test_cjsg_integration.py             # opcional, @pytest.mark.integration

tests/fixtures/capture/{tribunal}.py     # script de captura dos samples
tests/schemas/test_schema_coverage.py    # registrar Input em EXPECTED_COURT_SCHEMAS
tests/schemas/test_output_parity.py      # registrar Output em EXPECTED_COURT_OUTPUT_SCHEMAS
```

Extensão do sample segue a resposta (`.html` ou `.json`). O teste de
schema do `CONTRIBUTING.md` (`test_<endpoint>_schema_contract.py`) pode
ficar no diretório do tribunal ou consolidado em
`tests/schemas/test_cjsg_schemas.py`.

## Checklist do `CONTRIBUTING.md` (Adding a new tribunal)

1. Script de captura em `tests/fixtures/capture/<xx>.py`, que roda o
   scraper contra o backend real e salva em
   `tests/<xx>/samples/<endpoint>/<cenario>.<ext>`. Mínimo de 3
   cenários por endpoint (typical, sem resultados, página única).
   Saneamento (truncar campos grandes) fica dentro do script.
2. Samples commitados com a convenção `results_normal.<ext>`,
   `single_page.<ext>`, `no_results.<ext>`,
   `results_normal_page_NN.<ext>`.
3. `test_<endpoint>_contract.py`: `@responses.activate`,
   `mocker.patch("time.sleep")`, `responses.add(...)` com o sample,
   matcher de payload (`urlencoded_params_matcher(..., allow_blank=True)`
   para POST form, `json_params_matcher` para JSON,
   `query_param_matcher` para GET), schema por subset, 3 cenários.
4. Schema pydantic em `src/juscraper/courts/<xx>/schemas.py`.
5. Teste de schema: parâmetros documentados aceitos, kwarg
   desconhecido rejeitado, defaults, validators e `Literal`.
6. `test_<endpoint>_filters_contract.py`: chama o método com **todos**
   os filtros de uma vez e o matcher confirma que cada um chegou ao
   body/params.
7. No mesmo arquivo, um teste por alias deprecado aceito, afirmando o
   `DeprecationWarning` e que o valor chega ao backend como o canônico.
8. Contrato sem `@pytest.mark.integration`.
9. Sem rede, relógio ou TLS real; adapter TLS testado só por montagem.
10. Fluxo multi-step com ordem obrigatória usa
    `responses.registries.OrderedRegistry`.
11. Captcha, token dinâmico e libs externas (`txtcaptcha`,
    `browser_cookie3`) são mockados, nunca invocados; import lazy
    ausente se injeta com `mocker.patch.dict(sys.modules, ...)`.
12. Entrada no CHANGELOG em `[Unreleased]/Added`.
13. Payload builder público `build_<endpoint>_payload` (sem underscore)
    e constantes de URL em `courts/<xx>/download.py`, importados pelo
    script de captura e pelos contratos.
14. Base `juscraper.core.http.HTTPScraper` para scraper novo.

## Template: script de captura

```python
"""Captura samples de cjsg do {SIGLA}.

Rodar da raiz do repositório::

    python -m tests.fixtures.capture.{tribunal}
"""
import requests

from juscraper.courts.{tribunal}.download import BASE_URL, build_cjsg_payload

from ._util import dump, samples_dir_for


def _capturar(session, destino, pesquisa, pagina, arquivo):
    payload = build_cjsg_payload(pesquisa, pagina)
    resp = session.post(BASE_URL, json=payload, timeout=30)
    resp.raise_for_status()
    dump(destino / arquivo, resp.content)
    print("wrote", arquivo)


def main() -> None:
    destino = samples_dir_for("{tribunal}", "cjsg")
    session = requests.Session()
    _capturar(session, destino, "dano moral", 1, "results_normal_page_01.json")
    _capturar(session, destino, "dano moral", 2, "results_normal_page_02.json")
    _capturar(session, destino, "mandado de seguranca", 1, "single_page.json")
    _capturar(session, destino, "juscraper_probe_zero_hits_xyzqwe", 1, "no_results.json")


if __name__ == "__main__":
    main()
```

## Template: contrato de cjsg

```python
"""Contratos offline de cjsg do {SIGLA}."""
import pandas as pd
import responses
from responses.matchers import json_params_matcher

import juscraper as jus
from juscraper.courts.{tribunal}.download import BASE_URL, build_cjsg_payload
from tests._helpers import load_sample

CJSG_MIN_COLUMNS = {"processo", "classe", "relator", "data_julgamento", "ementa"}


def _add_page(pesquisa: str, pagina: int, sample: str) -> None:
    responses.add(
        responses.POST,
        BASE_URL,
        body=load_sample("{tribunal}", sample),
        status=200,
        content_type="application/json",
        match=[json_params_matcher(build_cjsg_payload(pesquisa, pagina))],
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

## Template: filtros e aliases deprecados

```python
"""Propagação de filtros e aliases deprecados de cjsg do {SIGLA}."""
import pytest
import responses
from responses.matchers import json_params_matcher

import juscraper as jus
from juscraper.courts.{tribunal}.download import BASE_URL, build_cjsg_payload
from tests._helpers import assert_unknown_kwarg_raises, load_sample


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
    _add(build_cjsg_payload(
        "dano moral", 1,
        relator="FULANO DE TAL",
        classe="Apelacao",
        data_julgamento_inicio="01/01/2024",
        data_julgamento_fim="31/03/2024",
    ))
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
    _add(build_cjsg_payload("dano moral", 1))
    with pytest.warns(DeprecationWarning, match="query.*deprecado"):
        jus.scraper("{tribunal}").cjsg(pesquisa=None, query="dano moral", paginas=1)


# Repetir para ``termo``, ``data_inicio``/``data_fim``, ``*_de``/``*_ate``
# e cada alias específico do tribunal (ex.: ``magistrado`` -> ``relator``).


def test_cjsg_kwarg_desconhecido():
    assert_unknown_kwarg_raises(
        jus.scraper("{tribunal}").cjsg, "kwarg_inventado", "dano moral", paginas=1,
    )
```

## Template: integração (opcional)

```python
"""Integração de cjsg do {SIGLA} contra o site real."""
import pandas as pd
import pytest

import juscraper as jus


@pytest.mark.integration
class TestCJSG{SIGLA}:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.scraper = jus.scraper("{tribunal}")

    def test_busca_simples(self):
        df = self.scraper.cjsg("direito", paginas=1)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_paginacao(self):
        df1 = self.scraper.cjsg("dano moral", paginas=1)
        df2 = self.scraper.cjsg("dano moral", paginas=range(1, 3))
        assert len(df2) > len(df1)
```

Portal sujeito a bloqueio anti-bot condicional ao IP: acrescentar
`pytestmark = pytest.mark.anti_bot` no topo do arquivo de integração.

## Template: contrato de cpopg

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
    assert {"id_cnj", "processo", "classe"} <= set(df.columns)
```

## Rodar

- `pytest tests/{tribunal}/`: contratos (offline, padrão)
- `pytest tests/schemas/`: cobertura, paridade de assinatura e de Output
- `pytest -m integration tests/{tribunal}/`: só integração
- `pytest -m ""`: tudo

## Dicas

- Use termos de busca genéricos que garantidamente retornam
  resultados: "direito", "dano moral", "contrato"
- Para cpopg, use números de processos públicos e conhecidos
- Não teste contagens exatas — sites mudam seus dados
- Não confie que a ordem dos resultados será estável
- `filterwarnings = ["error"]` no pyproject: todo warning esperado
  precisa de `pytest.warns`
- Em teste de filtro de data, passe `*_inicio` e `*_fim` juntos: com
  só uma ponta, `fill_open_ended_dates` completa a outra e emite
  `UserWarning`, que o `filterwarnings = ["error"]` transforma em falha
- Helpers em `tests/_helpers.py`: `load_sample`, `load_sample_bytes`
  (quando o parser trata o encoding, ex.: latin-1),
  `assert_unknown_kwarg_raises`
