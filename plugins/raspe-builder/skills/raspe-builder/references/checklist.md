# Checklist de aceitação — fonte pronta?

Antes de declarar uma fonte pronta para uso (e merge no repo `raspe`),
verifique cada item. Itens marcados com (*) são bloqueantes.

## 1. Reconhecimento e mapeamento

- [ ] (*) Tipo de site identificado: HTTP/HTML, HTTP/JSON ou Playwright
- [ ] (*) Documento de mapeamento da Etapa 3 produzido (endpoint, método,
  headers, paginação, parâmetros)
- [ ] Captcha verificado — se houver, fonte parada e documentada em
  `docs/captcha/<fonte>.md`

## 2. Scraper (`src/raspe/scrapers/<fonte>.py`)

- [ ] (*) Classe herda da base correta:
  `BaseScraper, HTMLScraper` (HTTP/HTML) | `BaseScraper` (HTTP/JSON) |
  `PlaywrightScraper` (browser)
- [ ] (*) Properties abstratas implementadas:
  - HTTP: `api_base`, `type`, `query_page_name`, `api_method`
  - Playwright: `url_base`
- [ ] (*) Métodos abstratos implementados:
  - HTTP: `_set_query_base`, `_find_n_pags`, `_parse_page`
  - Playwright: `_executar_busca` (async), `_encontrar_total_paginas`
    (async), `_parse_page` (sync)
- [ ] `__init__` chama `super().__init__("<nome_buscador_em_minusculas>")`
- [ ] Headers `User-Agent` realista (Firefox/Chrome) configurados via
  `self.session.headers.update({...})`
- [ ] Paginação configurada — `query_page_multiplier` e
  `query_page_increment` corretos para o tipo de paginação do site
- [ ] `_parse_page` retorna `pd.DataFrame` com colunas consistentes
  mesmo no caminho de erro (não levanta exceção, retorna DataFrame vazio
  com `columns=[...]`)
- [ ] Não duplica funcionalidades já fornecidas pela base: `tqdm`,
  `time.sleep`, retry para 429/5xx, criação de diretório temporário
- [ ] (Playwright) `_pagination_strategy` setado e, se for `NEXT_BUTTON`
  ou `LOAD_MORE`, o método respectivo sobrescrito
- [ ] (Playwright) Helpers da base usados quando aplicável
  (`_preencher_campo`, `_clicar_elemento`, `_aguardar_elemento`)

## 3. Factory (`src/raspe/__init__.py`)

- [ ] (*) Função factory `def <fonte>(**kwargs)` criada com docstring no
  padrão das vizinhas
- [ ] (*) `"<fonte>"` adicionado em `__all__` na seção correta (HTTP ou
  Browser)
- [ ] (HTTP) Import no topo do arquivo: `from .scrapers.<fonte> import Scraper<Fonte>`
- [ ] (Playwright) Import lazy dentro da factory (NÃO no topo do arquivo)
- [ ] `python -c "import raspe; print(raspe.<fonte>)"` funciona
- [ ] (Playwright) `import raspe` continua funcionando mesmo sem
  `[browser]` instalado
- [ ] (HTTP, convenção recente a partir da CAPES) Classe registrada no
  `mapping` de `scraper()` em `src/raspe/scraper_manager.py`
- [ ] Caso da factory em `tests/test_init.py` e, se registrada no
  `mapping`, em `tests/test_scraper_manager.py`

## 4. Testes (`tests/<fonte>/`)

- [ ] (*) `tests/<fonte>/__init__.py` vazio criado
- [ ] (*) (HTTP) Script de captura `tests/fixtures/capture/<fonte>.py` criado
- [ ] (*) (HTTP) Samples HTML salvos em `tests/<fonte>/samples/raspar/`:
  - `page_01.html` (paginação típica)
  - `page_02.html` (segunda página, se paginar)
  - `single_page.html` (cenário 1 página de resultados)
  - `no_results.html` (cenário zero resultados)
- [ ] (*) (HTTP) `tests/<fonte>/test_raspar_contract.py` criado seguindo o
  padrão `responses` (modelo: `tests/ipea/test_raspar_contract.py`)
- [ ] (*) (HTTP) Casos cobertos:
  - `test_typical_paginacao`
  - `test_single_page`
  - `test_no_results`
- [ ] (HTTP) Matcher de payload sempre que possível, sob
  `registries.OrderedRegistry` (`query_param_matcher` para GET,
  `urlencoded_params_matcher(..., strict_match=False)` para POST de
  formulário, que exige `responses>=0.26.1` no `pyproject.toml` do raspe,
  `json_params_matcher` para POST JSON)
- [ ] Colunas validadas por subconjunto (`<=`), nunca igualdade
- [ ] `mocker.patch("time.sleep")` em todos os testes
- [ ] (Se aplicável) Fluxo multi-etapa com
  `registries.OrderedRegistry`; captcha, token dinâmico ou import lazy
  mockados via `mocker.patch.dict(sys.modules, ...)`
- [ ] (*) (Playwright) Em vez de testar `raspar()` end-to-end,
  `tests/<fonte>/test_config.py` testa configuração (`url_base`,
  `pagination_strategy`, `_max_pages`) e `_parse_page` sobre
  `samples/parse/typical.html` e `no_results.html`
- [ ] (*) `pytest tests/<fonte>/ -v --no-cov` passa 100%, sem warning
  (`filterwarnings = ["error"]`)
- [ ] (*) `pytest` na suíte completa passa, incluindo o gate de
  cobertura (`fail_under = 80`)

## 5. Integração rápida (smoke test)

- [ ] (*) Com permissão do usuário, smoke test não-mockado:
  ```bash
  python -c "import raspe; df = raspe.<fonte>().raspar(pesquisa='X', paginas=range(1, 2)); print(df.shape); print(df.columns.tolist())"
  ```
  Retorna DataFrame não-vazio com colunas esperadas e coluna
  `termo_busca`.

## 6. Documentação no repo raspe

- [ ] `CHANGELOG.md` atualizado: linha em `### Adicionado`, sob
  `## [Não lançado]`
- [ ] (Opcional) Notebook `notebooks/NN_<fonte>.ipynb` criado
- [ ] (Se aplicável) Atualização no `README.md` do raspe listando a
  fonte nas tabelas

## 7. Sync com a skill `raspe` do marketplace

Conforme `references/raspe-skill-sync.md`:

- [ ] (*) Linha em `plugins/raspe/skills/raspe/SKILL.md` → tabela
  "Roteamento de decisão"
- [ ] Linha em `plugins/raspe/skills/raspe/SKILL.md` → tabela
  "Vocabulário do pesquisador"
- [ ] Linha em `plugins/raspe/skills/raspe/SKILL.md` → tabela "Arquivos
  de referência"
- [ ] `frontmatter > description` em `SKILL.md` menciona a nova fonte
- [ ] Linhas adicionadas em `plugins/raspe/skills/raspe/references/fontes.md`
  (matriz geral, colunas, limites, text_column)
- [ ] (*) Arquivo novo `plugins/raspe/skills/raspe/references/<fonte>.md`
  criado

## 8. Linting e estilo

- [ ] `pre-commit run --all-files` passa (isort, pylint, flake8, mypy,
  pyright; linha máxima de 120 caracteres). (Playwright) Se o mypy acusar
  o uso de `self._page`, incluir o módulo em `[[tool.mypy.overrides]]`
- [ ] Imports organizados (stdlib → third-party → relativo)
- [ ] Type hints nos métodos públicos e privados não-triviais
- [ ] Sem `print()` — usar `self.logger.{debug,info,warning,error}`

## 9. Ética / operação

- [ ] User-Agent identificável (não `python-requests/2.x`)
- [ ] `sleep_time` >= 2s
- [ ] Testes não fazem rede (todos via `responses` ou samples locais)
- [ ] Se a fonte tem limites documentados (rate limit, teto de
  resultados), aplicar como atributos do scraper (`sleep_time`,
  `_max_pages`) E documentar no reference da skill `raspe`

## 10. Commits

- [ ] Commit no repo `raspe`: `feat: adiciona scraper <fonte>` (ou
  estilo convencional do projeto — ver `git log --oneline` em
  `<RASPE_REPO>`)
- [ ] Commit no repo `labdados-skills`: `docs(raspe): adiciona
  referência da fonte <fonte>` para a sincronização da skill

## Quando todos os itens marcados com (*) estão concluídos

A fonte está pronta para uso local. Para upstream:
- Abrir PR no `bdcdo/raspe` com o scraper, factory, testes e CHANGELOG
- Abrir PR no `lab-dados/labdados-skills` com a sincronização da skill
  `raspe`

Os dois PRs podem ser independentes (a sincronização da skill funciona
mesmo antes do merge no upstream, desde que a versão local do raspe
tenha a fonte).
