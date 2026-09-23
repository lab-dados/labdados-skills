# Checklist: Novo Tribunal no juscraper

Use esta checklist para garantir que nada foi esquecido ao adicionar
um novo tribunal. Marque cada item conforme for completando.

## Reconhecimento
- [ ] URL de consulta identificada e acessível
- [ ] Tipo de consulta mapeado (cjsg, cjpg, cpopg, cposg)
- [ ] Campos do formulário documentados
- [ ] Verificado se há captcha (tipo: ________________)
- [ ] Tecnologia do site identificada (eSAJ, custom, SPA, etc.)
- [ ] robots.txt verificado

## Engenharia reversa
- [ ] Requisições HTTP capturadas via Playwright MCP
- [ ] Endpoint principal identificado (URL: ________________)
- [ ] Método (GET/POST) e Content-Type documentados
- [ ] Parâmetros obrigatórios e opcionais mapeados
- [ ] Headers/cookies necessários identificados
- [ ] Mecanismo de paginação entendido (tipo: ________________)
- [ ] Formato de resposta identificado (HTML/JSON/XML)
- [ ] Total de resultados: como obter (campo/header/parsing)

## Código gerado
- [ ] `src/juscraper/courts/{tribunal}/__init__.py`
- [ ] `src/juscraper/courts/{tribunal}/client.py`
- [ ] `src/juscraper/courts/{tribunal}/download.py` com `build_<endpoint>_payload` público e constantes de URL
- [ ] `src/juscraper/courts/{tribunal}/parse.py`
- [ ] `src/juscraper/courts/{tribunal}/schemas.py` com `Input<Endpoint><SIGLA>` e `Output<Endpoint><SIGLA>`
- [ ] Classe `{SIGLA}Scraper` herdando de `HTTPScraper` (ou da família: `EsajSearchScraper`, `TRFConsultaScraper`)
- [ ] Registrado em `_SCRAPERS` de `src/juscraper/__init__.py`
- [ ] Parâmetros seguem convenções (pesquisa, data_*, paginas, nomes canônicos)
- [ ] Entrada validada por `apply_input_pipeline_search` (ou o equivalente da família)
- [ ] Paginação 1-based
- [ ] Sem User-Agent fixo (o `HTTPScraper` monta com a versão)
- [ ] Requisições via `self._request_with_retry` (retry com backoff)
- [ ] `time.sleep(self.sleep_time)` entre páginas
- [ ] `tqdm` para barra de progresso
- [ ] Retorna `pd.DataFrame` com colunas canônicas (`processo`, `classe`, `assunto`, `relator`)
- [ ] Docstrings Google em português, com `See also:` para o schema
- [ ] Logging ao invés de print

## Testes
- [ ] `tests/{tribunal}/__init__.py` existe
- [ ] `tests/fixtures/capture/{tribunal}.py` importa o payload builder e grava os samples
- [ ] Samples em `tests/{tribunal}/samples/<endpoint>/` (typical, página única, sem resultados)
- [ ] `test_<endpoint>_contract.py` com `responses`, matcher de payload e schema por subset
- [ ] `test_<endpoint>_filters_contract.py` com todos os filtros e um teste por alias deprecado
- [ ] Teste de schema (params aceitos, kwarg desconhecido, defaults)
- [ ] Contratos sem `@pytest.mark.integration` e sem rede
- [ ] Input e Output registrados em `tests/schemas/test_schema_coverage.py` e `test_output_parity.py`
- [ ] `pytest tests/{tribunal}/ tests/schemas/` passa
- [ ] (Opcional) `test_<endpoint>_integration.py` com `@pytest.mark.integration`

## Qualidade
- [ ] pylint sem erros críticos
- [ ] flake8 sem erros
- [ ] mypy sem erros
- [ ] Linhas <= 120 caracteres

## Documentação e release
- [ ] `docs/notebooks/{tribunal}.ipynb` criado com exemplo
- [ ] README.md atualizado (tabela de tribunais)
- [ ] `docs/_quarto.yml` e `docs/index.qmd` atualizados
- [ ] CHANGELOG.md atualizado ([Unreleased] → Added)
- [ ] Branch de feature criada
- [ ] PR aberto (nunca push direto na main)
