# Convenções do juscraper

Referência rápida das convenções do projeto. **Sempre leia o código
real dos scrapers existentes antes de gerar código novo** — este
arquivo é um resumo, não substitui a leitura do código-fonte, do
`CLAUDE.md` e do `CONTRIBUTING.md` (seções "Adding a new tribunal" e
"Schemas pydantic").

## Arquitetura

```
src/juscraper/
├── __init__.py              # _SCRAPERS + scraper() factory
├── core/
│   ├── base.py              # BaseScraper
│   ├── http.py              # HTTPScraper (session, User-Agent, retry)
│   └── parse_utils.py       # clean_html, coerce_date_columns, ...
├── schemas/                 # SearchBase, mixins, CnjInputBase, Output*Base
├── courts/
│   ├── _esaj/               # família eSAJ: EsajSearchScraper
│   ├── _trf/                # família PJe TRF1/3/5: TRFConsultaScraper
│   ├── tjro/                # exemplo de tribunal sem família
│   │   ├── __init__.py
│   │   ├── client.py        # TJROScraper: API pública
│   │   ├── download.py      # HTTP, paginação, build_cjsg_payload
│   │   ├── parse.py         # respostas brutas -> DataFrame
│   │   └── schemas.py       # InputCJSGTJRO / OutputCJSGTJRO
│   └── ...
├── aggregators/             # datajud, jusbr, pdpj, comunica_cnj
└── utils/
    ├── params.py             # pipeline de normalização de parâmetros
    └── cnj.py                # clean_cnj, format_cnj
```

Tribunal novo ganha os quatro módulos `client.py`, `download.py`,
`parse.py` e `schemas.py`, mais o `__init__.py`. O template em
`assets/template_tribunal/` segue essa divisão.

`src/juscraper/tribunal_manager.py` é código morto (importa módulos
que não existem mais e ninguém o importa). Não edite; o registro vai
em `_SCRAPERS`.

## Famílias e generalização

- **eSAJ** (TJAC, TJAL, TJAM, TJCE, TJMS, TJSP): infra em
  `courts/_esaj/`. Tribunal eSAJ típico é uma subclasse de
  `EsajSearchScraper` com `BASE_URL` e `TRIBUNAL_NAME`; particularidades
  entram pelos hooks (`_configure_session`, `INPUT_CJSG`,
  `CJSG_CHROME_UA`, `CJSG_EXTRACT_CONVERSATION_ID`, `_build_cjsg_body`).
  Nunca `if tribunal == "X"` no código compartilhado.
- **PJe consulta pública** (TRF1, TRF3, TRF5): infra em `courts/_trf/`,
  subclasse de `TRFConsultaScraper`.
- **Regra de generalização**: só mover algo para `_<familia>/` ou criar
  mixin/base com **2+ ocorrências concretas**. Com um caso só, duplicar
  é mais barato que abstrair errado. Vale para schemas também.

## Classe base

Scraper novo herda de `juscraper.core.http.HTTPScraper`, que:

- cria `self.session = requests.Session()` com o User-Agent
  `juscraper/<__version__> (https://github.com/jtrecenti/juscraper)`
  (não fixar User-Agent próprio);
- expõe o hook `_configure_session(session)` para adapter TLS, cookies
  ou User-Agent de navegador quando o site exigir;
- guarda `self.sleep_time` (default `1.0`) para a pausa entre páginas;
- oferece `self._request_with_retry(method, url, ...)` com backoff
  exponencial para 403/429/5xx e respeito a `Retry-After` numérico.
  O client repassa esse método como `request_fn` para o `download.py`.

## Nomes de classes

PEP 8 CamelCase: `{SIGLA}Scraper` com a sigla em maiúsculas
(`TJROScraper`, `TRF6Scraper`, `STFScraper`). Schemas:
`Input<Endpoint><SIGLA>` e `Output<Endpoint><SIGLA>` (`InputCJSGTJRO`).

## Factory function

`juscraper.scraper("tjro")` resolve a sigla em minúsculas no dict
`_SCRAPERS` de `src/juscraper/__init__.py`, no formato
`"módulo:Classe"`, com import lazy:

```python
"tjro":  "juscraper.courts.tjro.client:TJROScraper",
```

## Parâmetros padronizados

| Parâmetro                  | Tipo                        | Descrição                         |
|----------------------------|-----------------------------|-----------------------------------|
| `pesquisa`                 | str                         | Termo de busca                    |
| `paginas`                  | int \| list \| range \| None | Páginas a baixar (1-based)        |
| `data_julgamento_inicio`   | str ou date                 | Data de julgamento início         |
| `data_julgamento_fim`      | str ou date                 | Data de julgamento fim            |
| `data_publicacao_inicio`   | str ou date                 | Data de publicação início         |
| `data_publicacao_fim`      | str ou date                 | Data de publicação fim            |
| `tamanho_pagina`           | int                         | Itens por página (default 10)     |
| `numero_processo`          | str                         | Filtro por número (Input)         |
| `relator`                  | str                         | Filtro por relator                |
| `classe` / `assunto`       | str                         | Filtros por classe e assunto      |
| `id_cnj`                   | str \| list[str]            | Entrada de `cpopg`/`cposg`        |

Datas de entrada aceitam `DD/MM/AAAA`, `DD-MM-AAAA`, `AAAA-MM-DD`,
`AAAA/MM/DD` e `datetime.date`; o pipeline converte para o
`BACKEND_DATE_FORMAT` declarado no schema.

Aliases deprecados, aceitos com `DeprecationWarning`: `query`/`termo`
-> `pesquisa`; `data_inicio`/`data_fim` -> `data_julgamento_*`;
`*_de`/`*_ate` -> `*_inicio`/`*_fim`. Nome antigo específico do
tribunal (`nr_processo`, `magistrado`, `classe_judicial`) vira alias
com `resolve_deprecated_alias`/`pop_deprecated_alias`, sem remover o
campo canônico.

## Normalização (`src/juscraper/utils/params.py`)

O caminho padrão de `cjsg`/`cjpg` é `apply_input_pipeline_search`,
chamado no método público depois de popar os aliases específicos do
tribunal:

```python
relator = resolve_deprecated_alias(kwargs, "magistrado", "relator", relator)
inp = apply_input_pipeline_search(
    InputCJSGTJXX,
    "TJXXScraper.cjsg_download()",
    pesquisa=pesquisa,
    paginas=paginas,
    kwargs=kwargs,
    consume_pesquisa_aliases=True,
    relator=relator,
)
```

Ele roda, em ordem: `normalize_pesquisa` (aliases de busca),
`normalize_paginas` (int vira `range(1, n+1)`), `normalize_datas`
(aliases de data), conversão das datas, `validate_intervalo_datas`,
o schema pydantic e `raise_on_extra_kwargs` (kwarg desconhecido vira
`TypeError` com sugestão de nome parecido). Validador próprio do
tribunal (ex.: limite de tamanho da pesquisa) roda antes do pipeline.
Backend com limite documentado de janela passa `max_dias` e
`origem_mensagem`.

## Paginação

- Sempre **1-based**: `range(1, 4)` baixa páginas 1, 2 e 3
- `paginas=3` é equivalente a `range(1, 4)`
- `paginas=None` baixa todas as páginas
- `paginas` vem de `SearchBase`; não redeclarar no schema concreto

## Schemas pydantic

- `courts/<xx>/schemas.py` com `Input<Endpoint><SIGLA>` e
  `Output<Endpoint><SIGLA>` para cada endpoint implementado.
- Input herda de `SearchBase` (`pesquisa`, `paginas`,
  `extra="forbid"`) e dos mixins aplicáveis (`DataJulgamentoMixin`,
  `DataPublicacaoMixin`); consulta por CNJ herda de `CnjInputBase`.
  Declara `BACKEND_DATE_FORMAT: ClassVar[str]` quando o backend não
  usa `DD/MM/AAAA`.
- Output herda de `OutputCJSGBase` (+ `OutputRelatoriaMixin`,
  `OutputDataPublicacaoMixin`) ou de `OutputCnjConsultaBase`, com
  `extra="allow"`.
- Campos do Input batem byte a byte com os parâmetros explícitos do
  método público.
- Nomes canônicos de coluna: `processo` (não `nr_processo`/
  `numero_cnj`), `classe` (não `classe_cnj`), `assunto` (não
  `assunto_principal`), `relator` (não `magistrado`); no Input o filtro
  por número é `numero_processo`. O parser renomeia as chaves do
  backend antes de montar o DataFrame.
- Registrar em `tests/schemas/test_schema_coverage.py::EXPECTED_COURT_SCHEMAS`
  e `tests/schemas/test_output_parity.py::EXPECTED_COURT_OUTPUT_SCHEMAS`,
  e rodar `pytest tests/schemas/`.

## Métodos por tribunal

Cada tribunal pode implementar:

| Método              | Input                     | Output                        | Descrição                          |
|---------------------|---------------------------|-------------------------------|------------------------------------|
| `.cjsg()`           | params de busca           | pd.DataFrame                  | Consulta jurisprudência            |
| `.cjsg_download()`  | params de busca           | respostas brutas              | Baixa as páginas (lista de JSON/HTML; na família eSAJ, caminho da pasta) |
| `.cjsg_parse()`     | saída do download         | pd.DataFrame                  | Processa as respostas brutas       |
| `.cjpg()`           | params de busca           | pd.DataFrame                  | Consulta julgados 1º grau          |
| `.cpopg()`          | `id_cnj: str \| list[str]` | pd.DataFrame                  | Consulta processos 1º grau         |
| `.cpopg_download()` | `id_cnj`                  | respostas brutas              | Baixa o detalhe de cada processo   |
| `.cpopg_parse()`    | saída do download         | pd.DataFrame                  | Processa o detalhe                 |
| `.cposg()`          | `id_cnj`                  | pd.DataFrame                  | Consulta processos 2º grau         |

`cpopg` novo devolve um DataFrame: em TRF1/3/5 e TRF6, uma linha por
processo com a coluna `id_cnj` (herdada de `OutputCnjConsultaBase`);
JusBR e PDPJ também devolvem DataFrame. O `cpopg`/`cposg` do
TJSP é legado: devolve um dict de DataFrames (`basicos`, `partes`,
`movimentacoes`, `peticoes_diversas`) e não serve de modelo.

Nem todos os métodos são obrigatórios — implemente o que o site do
tribunal disponibiliza. Não crie schema para método que só levanta
`NotImplementedError`.

## Docstrings

Métodos públicos em português, estilo Google (`Args:`/`Returns:`/
`Raises:`). Métodos com filtros via `**kwargs` listam cada campo do
schema, têm seção "Aliases deprecados" e terminam com `See also:`
apontando o `Input*`. Os pares `*_download` referenciam o método
top-level com `:meth:` em vez de repetir a lista. `docs/*.qmd` e os
notebooks continuam em inglês.

## Testes

- Ficam em `tests/{tribunal}/` com `__init__.py`
- Contrato offline obrigatório por método público
  (`test_<endpoint>_contract.py`, com `responses` e samples); detalhes
  em `test-patterns.md`
- Integração é opcional (`test_<endpoint>_integration.py`,
  `@pytest.mark.integration`)
- `pytest`: roda só o offline (o `addopts` exclui `integration`)
- `pytest -m integration`: só integração; `pytest -m ""`: tudo
- Marker `anti_bot` para integração sujeita a bloqueio condicional ao
  IP (Akamai nos TRFs PJe): o conftest converte
  `BotChallengeBlockedError` em xfail
- `--strict-markers` ativo — markers registrados em `pyproject.toml`
- `filterwarnings = ["error"]`: warning não esperado quebra o teste;
  use `pytest.warns` ao testar alias deprecado

## Playwright no código final

Regra: o scraper usa `requests`. A exceção existente é o STF: o
portal fica atrás de um desafio JavaScript do AWS WAF, e o
Playwright entra como extra opcional (`juscraper[stf]`), com import
lazy, só para obter o cookie `aws-waf-token`; a busca segue em
`requests`. Repetir esse desenho exige autorização do usuário.

## Estilo de código

- Python >= 3.11
- Linha máxima: 120 caracteres
- Pre-commit hooks: trailing whitespace, isort, pylint, flake8, mypy
- Gerenciador de pacotes: `uv` (`uv pip install -e ".[dev]"`)
- Sem hacks de `sys.path` nos testes

## Workflow Git

- Worktree dedicada com branch de feature + PR (nunca push direto na main)
- CHANGELOG.md em formato Keep a Changelog, entrada em `[Unreleased]`
- Documentação em `docs/` em inglês (problemas de encoding com PT)
