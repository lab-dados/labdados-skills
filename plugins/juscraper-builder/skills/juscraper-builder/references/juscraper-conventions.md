# Convenções do juscraper

Referência rápida das convenções do projeto. **Sempre leia o código
real dos scrapers existentes antes de gerar código novo** — este
arquivo é um resumo, não substitui a leitura do código-fonte.

## Arquitetura

```
src/juscraper/
├── __init__.py              # scraper() factory function
├── courts/
│   ├── tjsp/
│   │   ├── __init__.py
│   │   └── client.py        # TJSPScraper
│   ├── tjrs/
│   │   ├── __init__.py
│   │   └── client.py        # TJRSScraper
│   ├── tjpr/
│   │   ├── __init__.py
│   │   └── client.py        # TJPRScraper
│   └── tjdft/
│       ├── __init__.py
│       └── client.py        # TJDFTScraper
├── aggregators/
│   ├── datajud/
│   └── jusbr/
└── utils/
    └── params.py             # normalize_params()
```

## Nomes de classes

PEP 8 CamelCase: `TJDFTScraper`, `TJPRScraper`, `TJRSScraper`, `TJSPScraper`.

O nome da classe é sempre `{SIGLA}Scraper` onde SIGLA é em maiúsculas.

## Factory function

A função `juscraper.scraper("tjrs")` retorna uma instância do scraper.
O argumento é o nome do tribunal em minúsculas.

## Parâmetros padronizados

| Parâmetro                  | Tipo                        | Descrição                         |
|----------------------------|-----------------------------|-----------------------------------|
| `pesquisa`                 | str                         | Termo de busca (obrigatório)      |
| `paginas`                  | int \| list \| range \| None | Páginas a baixar (1-based)        |
| `data_julgamento_inicio`   | str (YYYY-MM-DD)            | Data de julgamento início         |
| `data_julgamento_fim`      | str (YYYY-MM-DD)            | Data de julgamento fim            |
| `data_publicacao_inicio`   | str (YYYY-MM-DD)            | Data de publicação início         |
| `data_publicacao_fim`      | str (YYYY-MM-DD)            | Data de publicação fim            |
| `data_inicio`              | str (alias)                 | Alias para data_julgamento_inicio |
| `data_fim`                 | str (alias)                 | Alias para data_julgamento_fim    |
| `diretorio`                | str ou Path                 | Pasta para download de arquivos   |

Nomes antigos (`query`, `termo`, `_de`/`_ate`) devem ser aceitos
com `DeprecationWarning`.

## Paginação

- Sempre **1-based**: `range(1, 4)` baixa páginas 1, 2 e 3
- `paginas=3` é equivalente a `range(1, 4)`
- `paginas=None` baixa todas as páginas (com aviso ao usuário)
- Normalização centralizada em `src/juscraper/utils/params.py`

## Métodos por tribunal

Cada tribunal pode implementar:

| Método              | Input               | Output             | Descrição                          |
|---------------------|---------------------|--------------------|------------------------------------|
| `.cjsg()`           | params de busca     | pd.DataFrame       | Consulta jurisprudência            |
| `.cjsg_download()`  | params + diretório  | Path               | Baixa arquivos brutos              |
| `.cjsg_parse()`     | diretório           | pd.DataFrame       | Lê arquivos brutos                 |
| `.cjpg()`           | params de busca     | pd.DataFrame       | Consulta julgados 1º grau          |
| `.cjpg_download()`  | params + diretório  | Path               | Baixa arquivos brutos 1º grau      |
| `.cjpg_parse()`     | diretório           | pd.DataFrame       | Lê arquivos brutos 1º grau         |
| `.cpopg()`          | nº processo         | dict de DataFrames | Consulta processos 1º grau         |
| `.cpopg_download()` | nº processo + dir   | Path               | Baixa HTMLs do processo             |
| `.cpopg_parse()`    | diretório           | dict de DataFrames | Lê HTMLs do processo                |
| `.cposg()`          | nº processo         | dict de DataFrames | Consulta processos 2º grau         |

Nem todos os métodos são obrigatórios — implemente o que o site do
tribunal disponibiliza.

## Testes

- Ficam em `tests/{tribunal}/` com `__init__.py`
- Testes que acessam servidores reais: `@pytest.mark.integration`
- Rodar rápidos: `pytest -m "not integration"`
- Rodar todos: `pytest`
- `--strict-markers` ativo — markers registrados em `pyproject.toml`

## Estilo de código

- Python >= 3.11
- Linha máxima: 120 caracteres
- Pre-commit hooks: trailing whitespace, isort, pylint, flake8, mypy
- Gerenciador de pacotes: `uv`
- Sem hacks de `sys.path` nos testes

## Workflow Git

- Feature branches + PR (nunca push direto na main)
- CHANGELOG.md em formato Keep a Changelog
- Documentação em `docs/` em inglês (problemas de encoding com PT)
