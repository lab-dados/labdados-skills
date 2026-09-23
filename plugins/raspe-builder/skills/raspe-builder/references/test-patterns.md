# Padrão de testes do raspe

A biblioteca raspe usa **testes de contrato offline** com a lib
[`responses`](https://github.com/getsentry/responses) e samples HTML
salvos no disco. Não há integração real com o site nos testes — esse
desenho é deliberado:
- Os scrapers travam quando o site muda; os testes garantem que o parser
  + paginação não regridam.
- Os samples também servem como documentação do formato esperado.

A referência canônica é `tests/ipea/test_raspar_contract.py`.

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

Durante a Etapa 2 (engenharia reversa), use `browser_evaluate`:

```javascript
() => document.documentElement.outerHTML
```

Os samples capturados na Etapa 2 ficam temporariamente em
`/tmp/raspe-recon/<fonte>/page_NN.html`. Para usar como teste, **mova**
(ou copie) cada arquivo para `tests/<fonte>/samples/raspar/page_NN.html`
no repositório raspe. Capture os três cenários mínimos (paginação
típica, página única, zero resultados), acionando cada um com termos
diferentes durante a engenharia reversa.

O script `tests/fixtures/capture/<fonte>.py` é obrigatório pela
checklist do `CLAUDE.md` do raspe: ele exercita o scraper real e grava
as respostas cruas em `tests/<fonte>/samples/<endpoint>/`, e é o que
permite regerar os samples quando o site mudar. Siga o padrão dos
existentes (`tests/fixtures/capture/ipea.py`, que usa
`attach_capture_hook` de `_util.py`) e leia
`tests/fixtures/capture/README.md`.

## Template de test_raspar_contract.py

```python
"""Contrato offline para ``Scraper{Fonte}.raspar``.

Os samples em ``tests/{fonte}/samples/raspar/`` foram capturados de
respostas reais do site. Para regerar, ver
``tests/fixtures/capture/{fonte}.py``.
"""

import pytest
import responses
from responses import matchers

from raspe.scrapers.{fonte} import Scraper{Fonte}
from tests._helpers import load_sample_bytes

API_URL = "{endpoint exato do scraper}"
COLUNAS_OBRIGATORIAS = {"titulo", "link", "data"}  # ajustar


@pytest.fixture
def scraper():
    return Scraper{Fonte}()


class TestRasparContract:
    @responses.activate
    def test_typical_paginacao(self, scraper, mocker):
        """N resultados → M páginas: 1 request inicial + M requests de página."""
        mocker.patch("time.sleep")

        # Request inicial (para _find_n_pags), com matcher dos params
        responses.add(
            responses.GET, API_URL,
            body=load_sample_bytes("{fonte}", "raspar/page_01.html"),
            status=200, content_type="text/html; charset=utf-8",
            match=[matchers.query_param_matcher(
                {"{param_busca}": "economia"}, strict_match=False,
            )],
        )
        # Request da página 1 (mesmo conteúdo, segunda chamada)
        responses.add(
            responses.GET, API_URL,
            body=load_sample_bytes("{fonte}", "raspar/page_01.html"),
            status=200, content_type="text/html; charset=utf-8",
        )
        # Request da página 2
        responses.add(
            responses.GET, API_URL,
            body=load_sample_bytes("{fonte}", "raspar/page_02.html"),
            status=200, content_type="text/html; charset=utf-8",
        )

        df = scraper.raspar(pesquisa="economia")

        assert not df.empty
        assert COLUNAS_OBRIGATORIAS <= set(df.columns)
        assert "termo_busca" in df.columns
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
        responses.add(
            responses.GET, API_URL,
            body=load_sample_bytes("{fonte}", "raspar/single_page.html"),
            status=200, content_type="text/html; charset=utf-8",
        )

        df = scraper.raspar(pesquisa="pobreza")
        assert not df.empty
        assert COLUNAS_OBRIGATORIAS <= set(df.columns)

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
```

## Cenários mínimos

| Cenário | Sample | Por que testar |
|---|---|---|
| Paginação típica | `page_01.html` + `page_02.html` | Verifica `_set_query_base`, `_find_n_pags`, paginação automática, parsing |
| Página única | `single_page.html` | Caminho de saída quando só tem 1 página |
| Zero resultados | `no_results.html` | Caminho do `_find_n_pags = 0`; assertiva `df.empty` |

Os três cenários são o mínimo por método público exigido pelo
`CLAUDE.md` do raspe.

## Regras do `CLAUDE.md` do raspe para o contrato

- **Matcher de payload sempre que possível**, não como caso opcional:
  `matchers.query_param_matcher(...)` para GET,
  `matchers.urlencoded_params_matcher(..., strict_match=False)` para POST
  de formulário, `matchers.json_params_matcher(...)` para POST JSON.
- **Schema por subconjunto**: `COLUNAS_OBRIGATORIAS <= set(df.columns)`,
  nunca igualdade.
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

`BaseScraper.raspar` faz **2 requisições para a primeira página**:
- Uma para `_find_n_pags` (descobrir o total).
- Uma para `_download_data` (baixar a página 1 que será parseada).

Mais 1 requisição por página adicional. Adicione `responses.add` na
ordem das chamadas. Se o teste falhar com `ConnectionError` ou
`NoCallableResponses`, conte de novo quantos `add` você adicionou.

## Mockar time.sleep

Sempre passe `mocker.patch("time.sleep")` para o teste rodar em
milissegundos em vez de esperar 2s por página. O `mocker` vem de
`pytest-mock` que já está no `pyproject.toml` de dev.

## Testes para Playwright

Mockar a navegação Playwright via `responses` não funciona — Playwright
não usa o stack `requests`. O padrão do raspe (`tests/saudelegis/`,
`tests/datalegis/`) é um `test_config.py` que testa configuração e
parsing síncrono, sem abrir navegador:

```
tests/<fonte>/
├── __init__.py
├── samples/
│   └── parse/
│       ├── typical.html
│       └── no_results.html
└── test_config.py
```

```python
import pytest

from raspe.playwright_scraper import PaginationStrategy, PlaywrightScraper
from raspe.scrapers.{fonte} import Scraper{Fonte}
from tests._helpers import load_sample_bytes

COLUNAS_OBRIGATORIAS = {"titulo", "link", "data"}  # ajustar


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
        assert COLUNAS_OBRIGATORIAS <= set(df.columns)

    def test_no_results(self, scraper, tmp_path):
        sample = tmp_path / "page.html"
        sample.write_bytes(load_sample_bytes("{fonte}", "parse/no_results.html"))
        assert scraper._parse_page(str(sample)).empty
```

Os scrapers Playwright concretos ficam no denominador da cobertura; só
a base `playwright_scraper.py` é excluída (`[tool.coverage.run] omit`).
Por isso o `test_config.py` precisa exercitar o construtor e o
`_parse_page` da fonte nova.

## Não testar

- Retry / backoff de 429/5xx — já coberto em
  `tests/test_base_scraper.py`.
- Validação de datas — já coberto em `tests/test_abstract_scraper.py`.
- BeautifulSoup `soup_it` — coberto em `tests/test_html_scraper.py`.

Testes do scraper devem cobrir só o que é específico dele:
`_set_query_base`, `_find_n_pags`, `_parse_page`.

## Rodar

O `addopts` do `pyproject.toml` liga `--cov=src/raspe` e
`[tool.coverage.report] fail_under = 80`. Rodando só a pasta da fonte, a
cobertura medida é a do pacote inteiro, e o comando reprova pelo gate
mesmo com todos os testes verdes. Rode a fonte isolada com `--no-cov` e,
antes do PR, a suíte completa, que é onde o gate vale:

```bash
cd <RASPE_REPO>
pytest tests/{fonte}/ -v --no-cov
pytest
```

Se as duas passam, vá para a Etapa 7 (validação e sync de skill).
