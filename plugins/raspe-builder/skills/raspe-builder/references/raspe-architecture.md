# Arquitetura do raspe — interface real das classes-base

Este documento resume a interface real das classes-base da biblioteca
`raspe` (em `<RASPE_REPO>/src/raspe/`). Sempre prefira ler o código
real, mas use este resumo para orientar a geração. O placeholder
`<RASPE_REPO>` é o caminho do clone local de `bdcdo/raspe` — definido
na Etapa de pré-requisitos do `SKILL.md`.

## Hierarquia

```
AbstractScraper (abstract_scraper.py)
├── BaseScraper (base_scraper.py)         ← HTTP via requests
│   └── + HTMLScraper (mixin)             ← Para parsing HTML com BeautifulSoup
│       (Folha, IPEA, Câmara, Senado, Presidência, CFM)
│   └── (sem mixin)                       ← Para HTTP/JSON puro (NYT)
└── PlaywrightScraper (playwright_scraper.py)
    └── ScraperDatalegis (datalegis.py)   ← Subclasse-base usada por ANS, ANVISA, SaudeLegis
```

## AbstractScraper

`<RASPE_REPO>/src/raspe/abstract_scraper.py`.

Construtor: `AbstractScraper(nome_buscador: str, debug: bool = True)`.

Atributos:
- `nome_buscador`: identificador da instância.
- `download_path`: diretório base dos downloads; por padrão, uma pasta do
  `tempfile.mkdtemp()`, criada na primeira busca.
- `debug`: se True, mantém arquivos baixados após `raspar()`.
- `exclude_cols_from_dedup`: list[str] — colunas a ignorar no
  `remove_duplicates`.
- `logger`: logging configurado.

Atributos de classe (declarados no corpo da classe, não no `__init__`):
- `schema_entrada` — schema pydantic dos parâmetros de `raspar()` (ver
  "Schemas" abaixo). Com ele, kwarg desconhecido levanta
  `ValidationError`, alias de `aliases_deprecados` emite
  `DeprecationWarning`, e o `_raspar()` recebe todos os campos, com os
  defaults preenchidos.
- `schema_saida` — schema pydantic das colunas do DataFrame, conferido no
  fim do `raspar()`.
- `colunas: list[str]` — colunas que o `_parse_page` devolve, sem
  `termo_busca`. Com `schema_saida`, **não declare**: o
  `__init_subclass__` preenche com `schema_saida.colunas_da_fonte()`. Use
  `self.colunas` no `_parse_page`, inclusive no DataFrame vazio do
  caminho de erro. Só fontes antigas sem schema (Câmara, Senado) declaram
  a lista à mão.

Properties abstratas:
- `type` → Literal['JSON', 'HTML'].

Métodos abstratos:
- `_parse_page(path: str) -> pd.DataFrame`.
- `_raspar(**kwargs) -> pd.DataFrame` — coleta com os kwargs já
  validados. `BaseScraper` e `PlaywrightScraper` já o implementam.

Métodos concretos:
- `raspar(**kwargs) -> pd.DataFrame` — caminho único de todos os
  raspadores: chama `_validar_parametros(**kwargs)`, depois
  `_raspar(**kwargs)`, e confere a saída com o `schema_saida` da classe
  (se houver) via `conferir_saida`: DataFrame sem linhas volta vazio com
  as colunas de `OutputXx.colunas()`; as mesmas colunas em outra ordem
  são reordenadas; colunas diferentes emitem `UserWarning` (que vira
  falha nos testes do raspe). Não sobrescreva `raspar()` na subclasse.
- `_validar_parametros(**kwargs)` — passa os kwargs pelo `schema_entrada`
  (se houver), depois auto-detecta pares de data
  (`data_inicio`/`data_fim`, `data_inicial`/`data_final`, `inicio`/`fim`,
  `begin_date`/`end_date`) e normaliza via
  `raspe.utils.validar_intervalo_datas`.
- `_create_download_dir()` — cria subdir temporário com timestamp.
- `_limpar_download(path)` — apaga a pasta de uma busca (e a raiz
  temporária, se ficou vazia). As bases chamam quando `debug=False`.
- `_parse_data(path)` — itera arquivos `*.{type}` em path e concatena
  DataFrames retornados por `_parse_page`. Sem arquivos, devolve
  `pd.DataFrame(columns=self.colunas)`.
- `scrape(**kwargs)` — alias retrocompatível de `raspar()`.

Subclasses podem sobrescrever `_validar_parametros`, mas devem chamar
`kwargs = super()._validar_parametros(**kwargs)` para manter validação de
datas e devolver o dict: é ele que o `raspar()` passa ao `_raspar()`.

## BaseScraper

`<RASPE_REPO>/src/raspe/base_scraper.py`.

Construtor: `BaseScraper(nome_buscador: str, debug: bool = True)`.

Atributos default configuráveis:
- `session: requests.Session` — já com headers default via
  `raspe.utils.start_session()`. Atualize via
  `self.session.headers.update({...})` no `__init__`.
- `sleep_time: int = 2` — segundos entre requisições. Aumente se o site
  exigir; nunca diminua.
- `query_page_multiplier: int = 1` — número de página enviado é
  `pag * multiplier + increment`.
- `query_page_increment: int = 0`.
- `timeout: tuple = (10, 30)` — connect/read.
- `old_page_name: str | None = None` — para sites que esperam ambos
  o nome da página atual e o da página anterior no body (Presidência
  envia `pagina` e `paginaAnterior` simultaneamente). Veja
  `ScraperPresidencia` como modelo.
- `max_retries: int = 3` — para 429 e 5xx.

Properties abstratas (precisam ser implementadas):
- `api_base: str` — URL do endpoint.
- `type: Literal['JSON', 'HTML']`.
- `query_page_name: str` — nome do parâmetro de paginação.
- `api_method: Literal['GET', 'POST']`.

Métodos abstratos:
- `_set_query_base(**kwargs) -> dict[str, Any]` — constrói o dict da
  requisição inicial (sem o param de paginação, que é adicionado pela
  base).
- `_find_n_pags(r0: requests.Response) -> int` — total de páginas.
- `_parse_page(path: str) -> pd.DataFrame` — herdado do AbstractScraper.

Funcionalidades já prontas (não duplique):
- `_raspar(**kwargs)` — coleta completa. Aceita kwargs como listas para
  iterar (ex: `pesquisa=["a", "b"]`) e adiciona coluna `termo_busca`
  automaticamente: no modo lista, com o item da lista, qualquer que seja
  o kwarg; na busca única, se algum kwarg for `pesquisa`/`termo`/`q`/`query`.
- `_download_data` — chama `_set_query_base`, `_get_n_pags`, itera páginas,
  salva arquivos.
- `_set_query_atual(query, pag)` — adiciona `query_page_name` ao dict
  como `pag * query_page_multiplier + query_page_increment`.
- `_set_r(query_atual)` — faz GET ou POST conforme `api_method`. POST
  envia como form-encoded (`data=query_atual`). Se a API exige
  `application/json`, sobrescreva `_set_r` na subclasse.
- `_request_with_retry` — retry exponencial para 429 (respeita
  `Retry-After`) e 5xx. Levanta `RateLimitError` ou `APIError`.
- Paginação 1-based padrão: `paginas=None` baixa todas;
  `paginas=range(1, 4)` baixa 1, 2, 3.

### Configurações comuns para paginação

| Site responde com... | `query_page_multiplier` | `query_page_increment` |
|---|---|---|
| Página numerada 1-based (`pagina=1, 2, 3`) | 1 | 0 |
| Página numerada 0-based (`page=0, 1, 2`) | 1 | -1 |
| Offset com step N (`rg=0, 25, 50`) | 25 | -25 |

A página inicial passada ao multiplicador é 1 (porque a base usa
`paginas=range(1, n_pags+1)`).

## Schemas

`<RASPE_REPO>/src/raspe/schemas/`: um módulo por fonte
(`schemas/<fonte>.py`), com dois schemas pydantic, exportados em
`schemas/__init__.py`. Modelos: `schemas/ipea.py` (HTTP) e
`schemas/saudelegis.py` (Playwright).

- `Input{Fonte}` — parâmetros de `raspar()`. Herda de `InputBase`
  (`extra="forbid"`) pelos mixins de `schemas/base.py`, que trazem os
  campos de nome canônico (tipos e descrições no próprio `base.py`):
  `PesquisaObrigatoriaMixin` ou `PesquisaOpcionalMixin` (HTTP),
  `PesquisaNavegadorMixin` (Playwright, sem lista), `PaginasMixin`,
  `IntervaloDatasMixin` e `AnoMixin`. Campos próprios da fonte entram
  como `Field(default=..., description=..., examples=[...])`. Nome
  antigo de parâmetro vai em
  `aliases_deprecados: ClassVar[dict[str, str]] = {"antigo": "pesquisa"}`.
- `Output{Fonte}` — uma linha do DataFrame. Herda de `OutputBase`, que já
  traz `termo_busca`. Cada coluna é um `Field(description=...,
  examples=[...])`, na ordem em que o `_parse_page` a monta.
  `Output{Fonte}.colunas()` é a ordem final do DataFrame;
  `colunas_da_fonte()` é a mesma lista sem `termo_busca`.

## HTMLScraper

`<RASPE_REPO>/src/raspe/html_scraper.py`. Mixin com:

- `soup_it(content)` — `BeautifulSoup(content, 'html.parser')`.
- `_confirmar_busca_vazia(soup)` — devolve 0 se a página traz o aviso de
  busca vazia e levanta `ScraperError` se não traz (manutenção,
  anti-robô). Use no lugar de `return 0` no `_find_n_pags` quando o
  marcador de contagem não aparece.

Use em conjunto com `BaseScraper` quando o tipo for HTML:
`class ScraperX(BaseScraper, HTMLScraper)`.

## PlaywrightScraper

`<RASPE_REPO>/src/raspe/playwright_scraper.py`.

Construtor:
`PlaywrightScraper(nome_buscador: str, debug: bool = True, headless: bool = True)`.

Já herda de `AbstractScraper, HTMLScraper`. `type` é sempre `'HTML'`.

Atributos:
- `wait_timeout: int = 15` — timeout default para elementos (em segundos).
- `cloudflare_timeout: int = 60` — timeout para bypass.
- `page_load_wait: float = 2.0` — espera após carregar página.
- `between_pages_wait: float = 3.0` — espera entre páginas.
- `_pagination_strategy: PaginationStrategy = PaginationStrategy.NONE`.
- `_max_pages: int = 100` — limite de segurança.
- `_headless: bool` — se False, abre janela de browser visível.

Property abstrata:
- `url_base: str` — URL inicial visitada antes da busca.

Métodos abstratos:
- `async _executar_busca(**kwargs) -> None` — preenche o formulário,
  clica em buscar, aguarda resultados.
- `async _encontrar_total_paginas() -> int`.
- `_parse_page(path: str) -> pd.DataFrame` — sync, lê arquivo HTML.

Estratégias de paginação (enum `PaginationStrategy` em
`playwright_scraper.py`):

| Valor | Quando usar | Método a sobrescrever |
|---|---|---|
| `NUMBERED_LINKS` | Site tem links numerados (1, 2, 3...) | `_paginar_por_numero(numero)` opcional — seletor default `a:text-is('{numero}')` |
| `NEXT_BUTTON` | Site tem botão "Próximo" / "Next" | **obrigatório** `_paginar_por_botao_proximo` (default levanta `NotImplementedError`) |
| `LOAD_MORE` | Botão "Carregar mais" | **obrigatório** `_paginar_por_carregar_mais` (default levanta `NotImplementedError`) |
| `INFINITE_SCROLL` | Scroll infinito | Default funcional, sobrescreva se precisar custom |
| `SELECT_DROPDOWN` | Dropdown com número de página | Usa `_paginar_por_numero` |
| `NONE` | Sem paginação | — |

Helpers disponíveis (já implementados):
- `_aguardar_elemento(selector, timeout=None, state='visible')`.
- `_clicar_elemento(selector, force=False)`.
- `_preencher_campo(selector, texto)`.
- `_obter_html()` — `await page.content()`.
- `_salvar_html_pagina(numero, download_dir)`.
- `_aguardar_cloudflare(selector_pagina_real=None)` — chamado
  automaticamente pelo `_baixar_async`. Detecta cookie `cf_clearance` ou
  ausência de markers de challenge.

Pipeline interno, com kwargs já validados pelo `raspar()` da
`AbstractScraper`. O `_raspar()` (sync) chama `_rodar_async`, que roda
`_baixar_async` com `asyncio.run` (ou num loop próprio em outra thread,
quando já há um loop ativo, como no Jupyter). O `_baixar_async`:
1. Cria download dir.
2. Abre browser com stealth.
3. `page.goto(url_base)`.
4. `_aguardar_cloudflare()`, depois espera `page_load_wait`.
5. `_executar_busca(**kwargs)`, depois espera `page_load_wait`.
6. `_encontrar_total_paginas()` — limita a `_max_pages`.
7. Com 0 páginas, chama `_confirmar_busca_vazia` no HTML atual
   (`ScraperError` se a página não traz o aviso de busca vazia) e segue
   sem salvar nada. Senão, salva a primeira página e itera até
   `total_paginas`, navegando via `_navegar_proxima_pagina(pagina - 1)`.

De volta ao `_raspar()`, fora do loop do asyncio:
8. `_parse_data(download_dir)` — chama seu `_parse_page` para cada HTML.
   Com 0 páginas, a pasta está vazia e sai `pd.DataFrame(columns=self.colunas)`.
9. Adiciona a coluna `termo_busca` com o valor de `pesquisa`.
10. Com `debug=False`, apaga a pasta de download (`_limpar_download`).

## Exceções (raspe.exceptions)

```
ScraperError
├── APIKeyError           # API key faltando/inválida
├── RateLimitError        # 429 persistente; atributo retry_after
├── APIError              # HTTP 4xx/5xx genérico; status_code, response_text
├── ValidationError       # parâmetro inválido (data, enum, etc.)
└── BrowserError          # falha em Playwright
    └── DriverNotInstalledError  # playwright não instalado
```

Levantar a exceção certa:
- API key obrigatória ausente no `__init__`: `APIKeyError`.
- Enum inválido (`site` fora de `{'todos','online','jornal'}` na Folha):
  `ValidationError` (de dentro de `_validar_parametros`).
- 401 da API: `APIKeyError` em `_find_n_pags`.

## Utilitários (raspe.utils)

- `start_session()` — `requests.Session` com headers default.
- `validar_data(s)` — aceita `YYYY-MM-DD`, `DD/MM/YYYY`, `YYYYMMDD`,
  retorna `YYYY-MM-DD`.
- `validar_intervalo_datas(inicio, fim, nome_inicio, nome_fim)` —
  normaliza par + valida ordem.
- `expand`, `extract`, `check`, `remove_duplicates` — utilitários de
  pós-processamento de DataFrame.
