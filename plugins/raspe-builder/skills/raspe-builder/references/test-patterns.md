# Padrão de testes do raspe

A biblioteca raspe usa **testes de contrato offline** com a lib
[`responses`](https://github.com/getsentry/responses) e samples HTML
salvos no disco. Não há integração real com o site nos testes — esse
desenho é deliberado:
- Os scrapers travam quando o site muda; os testes garantem que o parser
  + paginação não regridam.
- Os samples também servem como documentação do formato esperado.

A referência canônica é `tests/ipea/test_raspar_contract.py`. Fonte
Playwright troca o `responses` por uma página falsa (seção "Testes para
Playwright").

## Estrutura de arquivos por fonte

```
tests/<fonte>/
├── __init__.py                       (vazio)
├── samples/
│   └── raspar/
│       ├── page_01.html              (sample da página 1)
│       ├── page_02.html              (sample da página 2, se paginar)
│       ├── single_page.html          (cenário poucos resultados)
│       └── no_results.html           (cenário sem resultados)
└── test_raspar_contract.py
```

`tests/_helpers.py` (já existe no repo) expõe:

```python
load_sample(scraper, "raspar/page_01.html", encoding="utf-8")  # str
load_sample_bytes(scraper, "raspar/page_01.html")              # bytes
```

Prefira `load_sample_bytes` em `responses.add(body=...)` para preservar
encoding (especialmente sites em latin-1).

## Captura dos samples

Os samples HTTP saem do script `tests/fixtures/capture/<fonte>.py`,
obrigatório pela checklist do `CLAUDE.md` do raspe, e não do
`browser_evaluate` da Etapa 2: o `outerHTML` é o DOM que o navegador
montou, não a resposta crua que o scraper recebe.

O script passa os cenários a `capturar_cenarios`, de
`tests/fixtures/capture/_util.py`, que faz cada requisição pelo próprio
scraper e grava a resposta crua. Copie `tests/fixtures/capture/presidencia.py`
(docstring, `CENARIOS`, `main()` com `pasta_saida`) e leia
`tests/fixtures/capture/README.md`. Rode da raiz do raspe, como módulo:

```bash
cd <RASPE_REPO>
SAIDA=$(mktemp -d "${TMPDIR:-/tmp}/captura-{fonte}.XXXXXX") && echo "captura em $SAIDA" &&
  uv run python -m tests.fixtures.capture.{fonte} --saida "$SAIDA"
```

Cada cenário imprime o `_find_n_pags` da resposta: `single_page` tem de
dar 1 e `no_results`, 0. Se não der, troque o termo. Quando der, rode
sem `--saida` para gravar em `tests/{fonte}/samples/raspar/`. Fonte de
API JSON grava `.json` (como o `nyt.py`).

Página acima dos 500 KB do hook `check-added-large-files`: passe
`enxugar=enxugar_html` (também de `_util.py`) a `capturar_cenarios`,
como o `camara.py`. Se o peso vier de outra parte da página, `enxugar`
aceita qualquer função `bytes -> bytes` (`ipea.py`, `capes.py`).

Fonte Playwright também tem script de captura: copie
`tests/fixtures/capture/saudelegis.py`, que passa cada cenário a
`capturar_paginas_lidas` (um arquivo por página lida). Ele abre o
Chromium: precisa do extra `browser` e de `playwright install chromium`.
Cada cenário declara o que a busca tem de dar: `"linhas"` (`page_01` e
`page_02`, `single_page`), `"vazia"` (`no_results`, zero linhas sem
erro) ou `"erro"` (`ScraperError`, como o acesso recusado do
`acesso_negado.html` no `datalegis.py`). Se a busca der outra coisa, ou
outro número de páginas que o de arquivos do cenário, a função levanta
`RuntimeError` antes de gravar. No cenário `"vazia"` ou `"erro"`, o
arquivo gravado é a página que a contagem leu: não há sample da
confirmação de busca vazia.

## Template de test_raspar_contract.py

```python
"""Contrato offline para ``Scraper{Fonte}.raspar``.

Os samples em ``tests/{fonte}/samples/raspar/`` foram capturados de
respostas reais do site. Para regerar, ver
``tests/fixtures/capture/{fonte}.py``.
"""

import pytest
import responses
from responses import matchers, registries

from raspe.schemas.{fonte} import Output{Fonte}
from raspe.scrapers.{fonte} import Scraper{Fonte}
from tests._helpers import load_sample_bytes

API_URL = "{endpoint exato do scraper}"
COLUNAS = Output{Fonte}.colunas()


@pytest.fixture
def scraper():
    return Scraper{Fonte}()


class TestRasparContract:
    # OrderedRegistry consome os `add` na ordem. Com o registry padrão, um
    # request com params errados cairia num `add` sem matcher e o matcher
    # não verificaria nada.
    @responses.activate(registry=registries.OrderedRegistry)
    def test_typical_paginacao(self, scraper, mocker):
        """N resultados → 2 páginas: 2 requests, a página 1 trazendo também a contagem."""
        mocker.patch("time.sleep")

        # Página 1 (dá a contagem e é gravada) e página 2, com matcher dos params.
        # Valores que _set_query_atual envia (tabela de paginação da raspe-architecture.md).
        for pagina, sample in [("1", "page_01.html"), ("2", "page_02.html")]:
            responses.add(
                responses.GET, API_URL,
                body=load_sample_bytes("{fonte}", f"raspar/{sample}"),
                status=200, content_type="text/html; charset=utf-8",
                match=[matchers.query_param_matcher(
                    {"{nome_param_busca_no_site}": "economia", "{nome_param_pagina}": pagina}, strict_match=False,
                )],
            )

        df = scraper.raspar(pesquisa="economia")

        assert not df.empty
        assert list(df.columns) == COLUNAS
        assert (df["termo_busca"] == "economia").all()
        # Soma do parse das duas páginas — ajustar ao conteúdo dos samples

    @responses.activate
    def test_single_page(self, scraper, mocker):
        """Cenário 1 página de resultados."""
        mocker.patch("time.sleep")
        responses.add(
            responses.GET, API_URL,
            body=load_sample_bytes("{fonte}", "raspar/single_page.html"),
            status=200, content_type="text/html; charset=utf-8",
        )

        df = scraper.raspar(pesquisa="pobreza")
        assert not df.empty
        assert list(df.columns) == COLUNAS

    @responses.activate
    def test_no_results(self, scraper, mocker):
        """Zero resultados → DataFrame vazio."""
        mocker.patch("time.sleep")
        responses.add(
            responses.GET, API_URL,
            body=load_sample_bytes("{fonte}", "raspar/no_results.html"),
            status=200, content_type="text/html; charset=utf-8",
        )

        df = scraper.raspar(pesquisa="termo_inexistente_xyzabc")
        assert df.empty
        assert list(df.columns) == COLUNAS
```

## Cenários mínimos

| Cenário | Sample | Por que testar |
|---|---|---|
| Paginação típica | `page_01.html` + `page_02.html` | Verifica `_set_query_base`, `_find_n_pags`, paginação automática, parsing |
| Página única | `single_page.html` | Caminho de saída quando só tem 1 página |
| Zero resultados | `no_results.html` | Caminho do `_find_n_pags = 0`; `df.empty` com as colunas do schema |

Os três cenários são o mínimo por método público exigido pelo
`CLAUDE.md` do raspe.

## Regras do `CLAUDE.md` do raspe para o contrato

- **Matcher de payload sempre que possível**, não como caso opcional:
  `matchers.query_param_matcher(...)` para GET,
  `matchers.urlencoded_params_matcher(..., strict_match=False)` para POST
  de formulário, `matchers.json_params_matcher(...)` para POST JSON.
  Matcher só verifica algo sob `OrderedRegistry` ou quando todo `add`
  daquela URL tem matcher; com o registry padrão, request errado cai no
  `add` seguinte.
- **`strict_match` em `urlencoded_params_matcher` exige
  `responses>=0.26.1`.** O piso do raspe é `responses>=0.25.0`, e em
  0.25.x ou 0.26.0 o kwarg levanta `TypeError`. Se usar esse matcher,
  suba o piso no `pyproject.toml` do raspe.
- **Colunas por igualdade**: `list(df.columns) == Output{Fonte}.colunas()`,
  também no no_results.
- **Sem `@pytest.mark.integration`** no contrato, e sem dependência de
  rede, relógio ou TLS real. Adapter custom (ex.: SSL desabilitado):
  testar só a configuração (`isinstance`).
- **Fluxo multi-etapa com ordem obrigatória** usa
  `@responses.activate(registry=registries.OrderedRegistry)`
  (`from responses import registries`). Há exemplos em
  `tests/test_base_scraper.py`.
- **Captcha, token dinâmico e import lazy** (ex.: `txtcaptcha`,
  `browser_cookie3`) são mockados com
  `mocker.patch.dict(sys.modules, {...})`, nunca invocados de verdade.
- **Warning vira falha**: o `pyproject.toml` tem
  `filterwarnings = ["error"]`, então qualquer warning não capturado
  reprova o teste.

## Quantos `responses.add` por teste

`BaseScraper` faz **1 requisição por página**, e a página 1 é sempre
pedida, para a contagem (ver `_download_data` na `raspe-architecture.md`),
mesmo com `paginas` sem ela; com 0 páginas, só ela. Adicione
`responses.add` na ordem das chamadas. Se o teste falhar com
`ConnectionError` ou `NoCallableResponses`, conte de novo quantos `add`
você adicionou.

## Mockar time.sleep

Nos testes HTTP, sempre passe `mocker.patch("time.sleep")` para o teste rodar em
milissegundos em vez de esperar 2s por página. O `mocker` vem de
`pytest-mock` que já está no `pyproject.toml` de dev. Nos de Playwright,
o `navegador_falso` já zera as esperas.

## Testes para Playwright

`responses` não intercepta o navegador, mas o contrato existe do mesmo
jeito: `navegador_falso(mocker, raspador)`, de `tests/_helpers.py` (ver
a docstring), troca o navegador por uma página falsa em
`raspador.pagina_falsa`, e nada abre o Chromium. Modelos:
`tests/saudelegis/test_raspar_contract.py` e
`tests/datalegis/test_raspar_contract.py`.

```
tests/<fonte>/
├── __init__.py
├── samples/
│   ├── raspar/                       (gravados pelo script de captura)
│   │   ├── page_01.html
│   │   ├── page_02.html
│   │   ├── single_page.html
│   │   └── no_results.html
│   └── parse/
│       ├── typical.html
│       └── no_results.html
├── test_raspar_contract.py
└── test_config.py
```

### Quantas leituras por teste

`pagina_falsa.content.side_effect` recebe os HTMLs na ordem em que o
raspador os lê: a primeira leitura é a da contagem de páginas
(`_encontrar_total_paginas`); depois, uma por página salva. Sem
resultados, a segunda leitura é a do aviso de busca vazia. Paginação
típica com 2 páginas = 3 HTMLs (`page_01`, `page_01`, `page_02`);
single_page e no_results = 2. A conta vale quando a contagem lê o HTML
por `_obter_html`, como no saudelegis e no datalegis; se a fonte lê o
HTML também na busca, ou conta sem ele, ajuste a lista.

### Template de test_raspar_contract.py (Playwright)

Copie `tests/saudelegis/test_raspar_contract.py` e troque os nomes. O
esqueleto:

```python
from raspe.schemas.{fonte} import Output{Fonte}
from raspe.scrapers.{fonte} import Scraper{Fonte}
from tests._helpers import load_sample, navegador_falso

COLUNAS = Output{Fonte}.colunas()


def _raspador(mocker, *nomes: str) -> Scraper{Fonte}:
    """Raspador cuja página falsa devolve os samples ``nomes``, um por leitura."""
    raspador = navegador_falso(mocker, Scraper{Fonte}(debug=False))
    raspador.pagina_falsa.content.side_effect = [load_sample("{fonte}", f"raspar/{n}") for n in nomes]
    return raspador


class TestRaspar:
    def test_typical_le_as_duas_paginas(self, mocker):
        raspador = _raspador(mocker, "page_01.html", "page_01.html", "page_02.html")
        df = raspador.raspar(pesquisa="economia")
        assert len(df) == {N}  # soma das duas páginas
        assert list(df.columns) == COLUNAS
        assert (df["termo_busca"] == "economia").all()
        cliques = [c.args[0] for c in raspador.pagina_falsa.click.await_args_list]
        assert cliques[-1] == "{seletor do link da página 2}"

    def test_no_results(self, mocker):
        df = _raspador(mocker, "no_results.html", "no_results.html").raspar(pesquisa="termo_inexistente_xyzabc")
        assert df.empty
        assert list(df.columns) == COLUNAS
```

`test_single_page` é igual ao no_results, com `single_page.html` e
`assert not df.empty`. O modelo do saudelegis ainda roda o typical com
o Playwright fora de `sys.modules` (o contrato não depende do extra
`browser`) e testa a página 2 que não carrega (`wait_for_selector`
levantando `PlaywrightTimeoutFalso`).

O template segue a paginação por link numerado (`NUMBERED_LINKS`, a do
saudelegis). Com `SELECT_DROPDOWN`, o contrato do datalegis confere o
`select_option` do combobox no lugar do clique. Para as outras
estratégias o raspe não tem modelo: leia o `_paginar_por_*` da base
antes de montar a página falsa.

Se a fonte usa `asyncio.sleep` próprio (fora de `page_load_wait` e
`between_pages_wait`), mocke-o no `_raspador`:
`mocker.patch("asyncio.sleep", mocker.AsyncMock())`, como no contrato
do datalegis.

### test_config.py

O raspe mantém também um `test_config.py` por fonte Playwright, com a
configuração e o `_parse_page` sobre `samples/parse/`, sem passar pelo
`raspar()`:

```python
import pytest

from raspe.playwright_scraper import PaginationStrategy, PlaywrightScraper
from raspe.schemas.{fonte} import Output{Fonte}
from raspe.scrapers.{fonte} import Scraper{Fonte}
from tests._helpers import load_sample_bytes

# _parse_page devolve as colunas da fonte; termo_busca entra depois, no _raspar.
COLUNAS_DA_FONTE = Output{Fonte}.colunas_da_fonte()


@pytest.fixture
def scraper():
    return Scraper{Fonte}()


class TestConstrutor:
    def test_url_base(self, scraper):
        assert "{dominio}" in scraper.url_base

    def test_pagination_strategy(self, scraper):
        assert scraper.pagination_strategy == PaginationStrategy.NUMBERED_LINKS

    def test_max_pages(self, scraper):
        assert scraper._max_pages == {N}

    def test_eh_playwright_scraper(self, scraper):
        assert isinstance(scraper, PlaywrightScraper)


class TestParsePage:
    def test_typical(self, scraper, tmp_path):
        sample = tmp_path / "page.html"
        sample.write_bytes(load_sample_bytes("{fonte}", "parse/typical.html"))
        df = scraper._parse_page(str(sample))
        assert not df.empty
        assert list(df.columns) == COLUNAS_DA_FONTE

    def test_no_results(self, scraper, tmp_path):
        sample = tmp_path / "page.html"
        sample.write_bytes(load_sample_bytes("{fonte}", "parse/no_results.html"))
        df = scraper._parse_page(str(sample))
        assert df.empty
        assert list(df.columns) == COLUNAS_DA_FONTE
```

Os scrapers Playwright concretos ficam no denominador da cobertura; só
a base `playwright_scraper.py` é excluída (`[tool.coverage.run] omit`).
O contrato e o `test_config.py` juntos exercitam a busca, a contagem, a
paginação e o `_parse_page` da fonte nova.

## Registro do schema (`tests/schemas/`)

`tests/schemas/` confere todo raspador com schema. Fonte nova entra em
`ESPERADOS` de `tests/schemas/test_schema_coverage.py`: copie a linha de
uma fonte análoga (`ScraperIpea` para HTTP, `ScraperNYT` para JSON,
`ScraperSaudeLegis` para Playwright), trocando os nomes, e importe as
três classes no topo do arquivo. As docstrings do arquivo explicam os
campos de `Registro`.

## Erros de leitura (`tests/test_parse_page_erros.py`)

Esse teste confere que o erro de leitura chega a quem chamou, em vez de
virar página vazia. Ele não se copia por fonte: a fonte nova entra nos
testes que já existem.

- **Página ilegível:** grava uma página que não é UTF-8 e confere que o
  erro do `_parse_page` chega ao `ScraperError` do `_parse_data`. Cobre
  sozinho todo raspador com fábrica pública (`RASPADORES` sai de
  `descobrir_raspadores` e `fabricas_por_raspador`), então basta a
  Etapa 5. Se o construtor exige argumento (como o `api_key` do NYT) ou
  faz requisição (como o da Câmara), ajuste o `_construir`.
- **Item ilegível:** fonte cujo `_parse_page` tem `except Exception` por
  item (template 4.A) entra em `ITENS`, com o import da classe no topo
  do arquivo, a pasta dos samples e a função que quebra os itens do
  `page_01.html`: `_quebrar_tag` (um
  método de `Tag` lido uma vez por item, como Câmara e IPEA) ou
  `_quebrar_metodo` (um método do raspador chamado por item, como CAPES e
  CFM). `test_todo_raspador_que_pula_item_esta_em_itens` reprova a fonte
  que pula itens e ficou fora, mas só a reconhece pelo texto
  `except Exception` no próprio `_parse_page`. Com ela em `ITENS`, a classe
  `TestErroDeItem` confere os dois casos: um item quebrado dá
  `UserWarning` e mantém os demais; todos quebrados dão `ScraperError`,
  com a causa encadeada.

O zero resultado legítimo fica no `test_no_results` do contrato:
DataFrame vazio, com as colunas do schema e sem erro.

## Não testar

- Retry / backoff de 429/5xx — já coberto em
  `tests/test_base_scraper.py`.
- Validação de datas — já coberto em `tests/test_abstract_scraper.py`.
- BeautifulSoup `soup_it` — coberto em `tests/test_html_scraper.py`.

Testes do scraper devem cobrir só o que é específico dele:
`_set_query_base`, `_find_n_pags`, `_parse_page` (Playwright:
`_executar_busca`, `_encontrar_total_paginas`, a paginação e
`_parse_page`).

## Rodar

Com os testes escritos, siga o passo 1 da Etapa 7 do `SKILL.md`.
