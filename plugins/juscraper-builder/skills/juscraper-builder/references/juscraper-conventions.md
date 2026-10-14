# Mapa das convenções do juscraper

Este arquivo não repete as convenções do juscraper. Ele diz onde cada uma está escrita, quais raspadores ler como modelo e quais fatos só aparecem no código. A fonte da verdade é o repositório `jtrecenti/juscraper`; se algo aqui divergir dele, o repositório vence.

## Onde está cada regra

| Assunto | Fonte única no juscraper |
|---|---|
| Ambiente, comandos de teste, pre-commit | `CLAUDE.md` > "Desenvolvimento" e "Testes" |
| Quando criar família ou base compartilhada | `CLAUDE.md` > "Arquitetura" (regra de generalização) |
| Nomes canônicos, `paginas`, aliases, `TypeError` × `ValidationError` | `CLAUDE.md` > "API pública"; `docs/api-conventions.qmd` |
| Deprecação de parâmetro ou alias | `CLAUDE.md` > "Política de deprecação" |
| Lista do que o PR de tribunal novo precisa ter | `CONTRIBUTING.md` > "Adding a new tribunal" |
| Pirâmide de testes, samples, ferramentas, marker `anti_bot` | `CONTRIBUTING.md` > "Tests" |
| Bases e mixins de schema, registro, paridade, wiring, `BACKEND_DATE_FORMAT` | `CONTRIBUTING.md` > "Schemas pydantic" |
| Docstrings de método com `**kwargs` e dos pares `*_download` | `CONTRIBUTING.md` > "Docstrings de métodos públicos com kwargs" |
| Hooks da família eSAJ | `CONTRIBUTING.md` > "Adding an eSAJ tribunal"; `src/juscraper/courts/_esaj/base.py` |
| Retry, backoff, `Retry-After`, `sleep_time` | `docs/api-conventions.qmd` > "Rate limiting and retry behaviour"; `src/juscraper/core/http.py` |
| Funções de normalização | `docs/api-conventions.qmd` > "Normalization Utilities"; `src/juscraper/utils/params.py` |
| Nomes de campo substituídos | `tests/schemas/test_canonical_types.py::DEPRECATED_SYNONYMS` |
| Changelog | `CLAUDE.md` > "Changelog" |
| Idioma de docstring, commit e `docs/` | `CLAUDE.md` > "Idiomas" |
| Lint e dispensas | `CONTRIBUTING.md` > "Política de lint e adoção gradual"; `pyproject.toml`, `ruff.toml` |
| Configuração do pytest (markers, `filterwarnings`, `addopts`) | `pyproject.toml` > `[tool.pytest.ini_options]` |

## Código para ler como modelo

Leia pelo menos dois, cliente e testes, antes de escrever:

- `src/juscraper/courts/tjro/` e `tests/tjro/`: raspador sobre `HTTPScraper` com backend JSON, `build_cjsg_payload` público, contrato, contrato de filtros e aliases deprecados específicos do tribunal (`magistrado` -> `relator`). Os arquivos do TJRO têm dispensas em `ruff.toml` (anotações, número de argumentos); arquivo novo não tem, então copie a estrutura e não as assinaturas.
- O `cjsg` do TRF3 (`src/juscraper/courts/trf3/cjsg_download.py`, `cjsg_parse.py`, `cjsg_schemas.py`, `client.py` e `tests/trf3/`): portal atrás de bot manager com cabeçalhos medidos e documentados, sessão própria por busca, perfil `perfis_http["cjsg"]`, filtros que o JavaScript do formulário converte em texto, validação de combinações depois do pydantic, divisão de módulos por endpoint. Em 14/10/2026 ele estava no PR aberto [jtrecenti/juscraper#397](https://github.com/jtrecenti/juscraper/pull/397); se ainda não estiver em `main`, leia com `git show origin/feat/trf3-cjsg:<caminho>`.
- `src/juscraper/courts/stf/` e `src/juscraper/core/waf.py`: a exceção do navegador para obter o cookie do AWS WAF.
- `src/juscraper/courts/_trf/base.py`: `cpopg` da família PJe, com `_configure_session` aplicando `BROWSER_HEADERS`.
- `src/juscraper/courts/tjmg/`: captcha de imagem sobre `HTTPScraper` (ver a skill `juscraper-builder-captcha`).

Não use como modelo:

- `courts/trf6/`: herda `BaseScraper` direto e cria a própria `Session`, anterior ao `HTTPScraper`.
- `cpopg`/`cposg` do TJSP: devolvem dict de DataFrames, formato legado.
- `download.py` do TJMG e do TJBA: sem payload builder público, anteriores a essa convenção.
- `src/juscraper/tribunal_manager.py`: código morto, que importa módulos inexistentes e não é importado por ninguém. O registro vai em `_SCRAPERS` de `src/juscraper/__init__.py`.

## Fatos que estão no código e não na documentação

Conferidos em 14/10/2026 contra `origin/main` (82cbf15; até a67a855 só mudou o checkpoint do STF). Antes de confiar, rode de novo o comando indicado.

**Retorno de `cjsg_download`.** Todos os tribunais fora da família eSAJ devolvem `list` de respostas brutas, e `cjsg_parse` recebe essa lista; `EsajSearchScraper` e TJSP devolvem `str` com o caminho dos arquivos baixados.

```bash
uv run python -c 'import ast, pathlib as p; [print(f.parent.name, n.returns and ast.unparse(n.returns)) for f in sorted(p.Path("src/juscraper/courts").glob("*/*.py")) for n in ast.walk(ast.parse(f.read_text())) if isinstance(n, ast.FunctionDef) and n.name == "cjsg_download"]'
```

**User-Agent.** `HTTPScraper.__init__` monta `juscraper/<__version__> (https://github.com/jtrecenti/juscraper)` e chama `_configure_session`. Os portais com gating de UA ou bot manager trocam os cabeçalhos, com docstring ou comentário dizendo o que foi medido; o comando abaixo lista quem faz isso hoje. Dois casos ensinam: `_trf/download.py` (`BROWSER_HEADERS` com `Sec-Fetch-*`, por causa do Akamai) e `core/waf.py` (a sessão usa o UA do navegador que obteve o token, porque o AWS WAF amarra o cookie ao UA). Legado que não serve de modelo: a família eSAJ fixa `juscraper/0.1` por requisição em `_esaj/download.py`, e o TJSP troca o UA por requisição com `CJSG_CHROME_UA`, não em `_configure_session`.

```bash
grep -rn "User-Agent\|BROWSER_HEADERS\|CHROME_UA" src/juscraper --include=*.py
```

**Aliases de data.** `data_inicio`/`data_fim` estão em `DATE_ALIAS_TO_CANONICAL` (`src/juscraper/utils/params.py`) ao lado dos `*_de`/`*_ate`, e `normalize_datas` emite `DeprecationWarning` para todos. Na seção "Date Filters" de `docs/api-conventions.qmd` eles aparecem como "Generic aliases" sem o aviso; o "Migration Guide" do mesmo arquivo já o cita. Vale o código.

**Perfis HTTP.** `RequestPolicy` e `perfis_http` (em `core/http.py`) dão timeout, número de tentativas e retry em timeout ou erro de conexão por endpoint; o usuário ajusta com `politica=` no construtor. O `CONTRIBUTING.md` ainda não os descreve.

**Extra do navegador.** O Playwright entra pelo extra `juscraper[waf]`; `juscraper[stf]` continua como alias (`pyproject.toml`).

**Documentação do site.** As tabelas de tribunais de `README.md` e `docs/index.qmd` divergem entre si, e o STF não aparece em `docs/_quarto.yml`, `docs/index.qmd` nem `README.md`. Não há regra escrita sobre quais desses arquivos um tribunal novo atualiza; pergunte ao mantenedor.
