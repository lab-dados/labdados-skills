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
no repositório raspe. Se a fonte tem três cenários (paginação típica,
página única, zero resultados), capture três samples — você pode
acionar cada um com termos diferentes durante a engenharia reversa.

Para regerar samples a partir do site ao vivo no futuro, crie
opcionalmente `tests/fixtures/capture/<fonte>.py` no padrão dos
existentes (`tests/fixtures/capture/ipea.py`).

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

        # Request inicial (para _find_n_pags)
        responses.add(
            responses.GET, API_URL,
            body=load_sample_bytes("{fonte}", "raspar/page_01.html"),
            status=200, content_type="text/html; charset=utf-8",
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
| (Opcional) Validação de query params | usar `matchers.query_param_matcher({...})` | Garante que o scraper envia os params esperados pela API |

Para POST, usar `matchers.urlencoded_params_matcher` ou
`matchers.json_params_matcher` conforme o `Content-Type`.

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
não usa o stack `requests`. Em vez disso:

1. Capture HTMLs reais durante a engenharia reversa.
2. Teste apenas o `_parse_page(path)`, que é sync:

```python
import pytest
from raspe.scrapers.{fonte} import Scraper{Fonte}

class TestParsePage:
    def test_extrai_dados_pagina_padrao(self):
        scraper = Scraper{Fonte}()
        df = scraper._parse_page("tests/{fonte}/samples/raspar/page_01.html")
        assert not df.empty
        assert COLUNAS_OBRIGATORIAS <= set(df.columns)
```

Veja `tests/saudelegis/` para o padrão Playwright.

## Não testar

- Retry / backoff de 429/5xx — já coberto em
  `tests/test_base_scraper.py`.
- Validação de datas — já coberto em `tests/test_abstract_scraper.py`.
- BeautifulSoup `soup_it` — coberto em `tests/test_html_scraper.py`.

Testes do scraper devem cobrir só o que é específico dele:
`_set_query_base`, `_find_n_pags`, `_parse_page`.

## Rodar

```bash
cd <RASPE_REPO>
pytest tests/{fonte}/ -v
```

Se passa, vá para a Etapa 7 (validação e sync de skill).
