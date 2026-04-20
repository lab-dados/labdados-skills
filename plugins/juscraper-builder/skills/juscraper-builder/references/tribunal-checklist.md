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
- [ ] Classe `{SIGLA}Scraper` com métodos adequados
- [ ] Registrado na factory function `scraper()`
- [ ] Parâmetros seguem convenções (pesquisa, data_*, paginas)
- [ ] Paginação 1-based
- [ ] `requests.Session()` com User-Agent identificável
- [ ] `time.sleep()` entre requisições (mínimo 1s)
- [ ] `tqdm` para barra de progresso
- [ ] Retry com backoff (máx 3 tentativas)
- [ ] Retorna `pd.DataFrame`
- [ ] Logging ao invés de print

## Testes
- [ ] `tests/{tribunal}/__init__.py` existe
- [ ] `tests/{tribunal}/test_{tribunal}_cjsg.py` criado
- [ ] Testes marcados com `@pytest.mark.integration`
- [ ] test_busca_simples passa
- [ ] test_colunas_esperadas passa
- [ ] test_paginacao passa
- [ ] test_filtro_data passa
- [ ] test_download_e_parse passa
- [ ] test_paginas_int passa

## Qualidade
- [ ] pylint sem erros críticos
- [ ] flake8 sem erros
- [ ] mypy sem erros
- [ ] Linhas <= 120 caracteres

## Documentação e release
- [ ] `docs/notebooks/{tribunal}.ipynb` criado com exemplo
- [ ] README.md atualizado (tabela de tribunais)
- [ ] CHANGELOG.md atualizado ([Unreleased] → Added)
- [ ] Branch de feature criada
- [ ] PR aberto (nunca push direto na main)
