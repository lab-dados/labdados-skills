---
name: juscraper-builder
description: >
  Gera scrapers Python (baseados em requests) para tribunais brasileiros
  seguindo a arquitetura do pacote juscraper. Use sempre que o usuário
  pedir para criar um scraper para um novo tribunal, implementar
  cjsg/cjpg/cpopg/cposg, ou fazer engenharia reversa de uma página de
  consulta de jurisprudência ou processos judiciais. Também use quando o
  usuário mencionar juscraper, raspagem de tribunal, scraping judicial,
  web scraping de sistemas judiciais brasileiros, ou pedir para adicionar
  um novo tribunal ao juscraper. Requer o Playwright MCP para navegação
  e captura de requisições de rede. Mesmo que o usuário não mencione
  "skill" ou "builder", use esta skill se a tarefa envolve criar ou
  modificar scrapers para tribunais.
---

# Juscraper Builder

Skill para gerar automaticamente scrapers de tribunais brasileiros,
produzindo código Python baseado em `requests` que segue a arquitetura
do pacote juscraper.

## Princípio fundamental

O **Playwright MCP é usado apenas como ferramenta de engenharia
reversa** — para navegar no site, capturar requisições HTTP, e entender
a API por baixo. O **código final gerado usa apenas `requests`** (ou
`httpx` se necessário). Nunca gere código final que dependa de
Selenium, Playwright, ou qualquer automatizador de navegador, a menos
que o usuário explicitamente autorize após ser informado de que não
há alternativa. O precedente no juscraper é o STF: o Playwright entra
como extra opcional (`juscraper[stf]`), com import lazy, só para obter
o cookie do desafio JavaScript do AWS WAF; a busca continua em
`requests`.

## Pré-requisitos

Antes de iniciar, verifique:

1. **Playwright MCP disponível**: Execute `/mcp` e confirme que
   `playwright` aparece na lista de ferramentas. Se não estiver:
   ```
   Preciso do Playwright MCP para navegar no site do tribunal e
   capturar as requisições. Por favor, rode no terminal:
   claude mcp add playwright -- npx @playwright/mcp@latest
   E reinicie o Claude Code.
   ```

2. **Repositório juscraper**: Confirme que estamos dentro do
   repositório juscraper. Se não, pergunte o caminho. Leia o
   `CLAUDE.md` do projeto para relembrar as convenções.

3. **Dependências de dev**: Confirme que `uv pip install -e ".[dev]"`
   foi executado. Leia também o `CONTRIBUTING.md` (seções "Adding a
   new tribunal" e "Schemas pydantic"): é lá que está a lista de itens
   que o PR precisa ter.

4. **Aprender com os existentes**: Antes de gerar qualquer código
   novo, **sempre** leia pelo menos dois scrapers existentes para
   entender os padrões atuais:
   ```bash
   # Listar tribunais existentes
   ls src/juscraper/courts/
   # Ler um scraper de referência completo (cjsg sobre HTTPScraper)
   cat src/juscraper/courts/tjro/{client,download,parse,schemas}.py
   # Captcha de imagem sobre HTTPScraper, com request_fn: tjmg
   cat src/juscraper/courts/tjmg/{client,download,schemas}.py
   # cpopg (consulta por CNJ): base da família PJe
   cat src/juscraper/courts/_trf/base.py
   ```
   O TRF6 também tem `cpopg` com captcha, mas é anterior à migração
   para `HTTPScraper` (herda `BaseScraper`, cria a própria `Session`
   com `BROWSER_HEADERS` e não usa `_request_with_retry`): não copie
   essa estrutura.
   Também leia `src/juscraper/utils/params.py` (em especial
   `apply_input_pipeline_search`) e `src/juscraper/core/http.py`
   (`HTTPScraper`) para entender a normalização de parâmetros e a
   camada HTTP.

   Consulte `references/juscraper-conventions.md` nesta skill para
   um resumo das convenções. Mas o código real é sempre a referência
   mais atualizada.

## Workflow Principal

### Etapa 1 — Reconhecimento do Site

1. Use o Playwright MCP para navegar até a URL fornecida pelo usuário:
   ```
   browser_navigate → URL do tribunal
   ```

2. Tire um snapshot da página (`browser_snapshot`) para mapear a
   estrutura e os campos de formulário.

3. Identifique e documente:
   - **Tipo de consulta**: jurisprudência (cjsg), processos 1º grau
     (cpopg/cjpg), processos 2º grau (cposg)
   - **Campos do formulário**: texto livre, datas, dropdowns com
     valores, checkboxes, radio buttons
   - **Captcha**: reCAPTCHA, hCaptcha, imagem, Cloudflare Turnstile
   - **Tecnologia**: formulário HTML tradicional, SPA (React/Angular/
     Vue), eSAJ, ou outro sistema

4. **Se houver captcha**: não encerre. Interrompa este fluxo e siga
   a skill `juscraper-builder-captcha`, que cobre esse caso. Ela testa
   primeiro se o backend valida o captcha. No juscraper, o TJRJ exibe
   reCAPTCHA que o backend não valida e o TJGO aceita os campos de
   reCAPTCHA/Turnstile vazios; TJMG e TRF6 validam captcha de imagem
   e o resolvem com `txtcaptcha`. Captcha interativo validado no
   backend não tem solução: TJAP e TJSE (Cloudflare Turnstile) e TJMA
   (reCAPTCHA v2 invisível) estão bloqueados, os dois últimos
   registrados em `docs/captcha/tjse_captcha.md` e
   `docs/captcha/tjma_captcha.md`.

5. Informe o usuário sobre os campos encontrados e peça confirmação
   antes de prosseguir:
   ```
   Encontrei os seguintes campos de busca no site do {TRIBUNAL}:
   - Pesquisa livre (texto)
   - Data de julgamento (início/fim)
   - Órgão julgador (dropdown com N opções)
   - Relator (texto)
   - ...

   Vou prosseguir com a captura de requisições. Confirma?
   ```

### Etapa 2 — Captura de Requisições

1. Prepare a interceptação. Se o Playwright MCP tiver a tool
   `browser_network_requests`, use-a diretamente. Caso contrário,
   use `browser_run_code` para captura programática:

   ```javascript
   async (page) => {
     const requests = [];
     page.on('request', req => {
       const rt = req.resourceType();
       if (['fetch', 'xhr', 'document'].includes(rt)) {
         requests.push({
           url: req.url(),
           method: req.method(),
           resourceType: rt,
           headers: req.headers(),
           postData: req.postData()
         });
       }
     });
     page.on('response', res => {
       const matchReq = requests.find(r => r.url === res.url());
       if (matchReq) {
         matchReq.status = res.status();
         matchReq.responseHeaders = res.headers();
       }
     });
     // Sinalizar que está pronto para captura
     return 'Interceptação configurada. Submeta o formulário agora.';
   }
   ```

2. Preencha o formulário com dados de teste genéricos:
   - Termo de busca: `"direito"` ou `"dano moral"` (termos com
     muitos resultados)
   - Datas: último mês ou semestre recente
   - Outros campos: valores padrão / mais abrangentes possível

3. Submeta o formulário via Playwright (`browser_click` no botão de
   busca).

4. Aguarde o carregamento e capture as requisições com
   `browser_network_requests`.

5. Identifique a **requisição principal** — aquela que busca os dados:
   - Geralmente é POST ou GET para endpoint contendo "pesquisa",
     "consulta", "search", "jurisprudencia", "resultado", "busca"
   - Pode retornar HTML (server-rendered) ou JSON (API REST)
   - Ignore requisições de assets (CSS, JS, imagens, fonts)

6. **Analise a paginação**: Navegue para a página 2 e capture a nova
   requisição. Compare com a requisição da página 1 para entender o
   mecanismo:
   - Offset numérico (`offset=10`, `offset=20`)
   - Número de página (`page=2`, `pagina=2`)
   - Cursor/token
   - Parâmetro no body vs. na URL

7. **Verifique necessidade de sessão**: Algumas APIs requerem:
   - Cookie de sessão (JSESSIONID, ASP.NET_SessionId, etc.)
   - Token CSRF
   - Cookie de consentimento
   Se necessário, documente quais cookies/headers precisam ser
   obtidos em uma requisição prévia (GET na página do formulário).

### Etapa 3 — Análise e Mapeamento

Crie um mapeamento interno (pode ser um comentário no código ou
documentação temporária) com:

```
TRIBUNAL: {nome}
ENDPOINT: {url_completa}
MÉTODO: {GET|POST}
CONTENT_TYPE: {application/x-www-form-urlencoded|application/json|...}
FORMATO_RESPOSTA: {html|json|xml}

PARÂMETROS OBRIGATÓRIOS:
  - {nome_param}: {descrição} (tipo: {str|int|date})

PARÂMETROS OPCIONAIS (campos do formulário):
  - {nome_param}: {descrição} (tipo, valores possíveis se dropdown)

HEADERS NECESSÁRIOS:
  - {header}: {valor ou como obter}

COOKIES NECESSÁRIOS:
  - {cookie}: {como obter (GET prévio? Login?)}

PAGINAÇÃO:
  - Tipo: {offset|page|cursor}
  - Parâmetro: {nome}
  - Itens por página: {N}
  - Como obter total: {campo no response, header, parsing HTML}

OBSERVAÇÕES:
  - {qualquer peculiaridade do site}
```

### Etapa 4 — Geração de Código

**Antes de escrever código, leia os scrapers existentes** (item 4
dos Pré-requisitos) para alinhar com os padrões atuais. Sempre use
o código real como referência, não apenas as convenções documentadas.

Antes de criar um scraper do zero, veja se o site pertence a uma
família já implementada: eSAJ vira subclasse de `EsajSearchScraper`
(`courts/_esaj/`), PJe consulta pública vira subclasse de
`TRFConsultaScraper` (`courts/_trf/`). Só generalize algo para uma
família nova com 2+ ocorrências concretas.

Gere os seguintes arquivos. O template em `assets/template_tribunal/`
tem os cinco módulos prontos para adaptar (placeholders `TJXX`/`tjxx`):

#### 4.1 Client: `src/juscraper/courts/{tribunal}/client.py`

API pública. Herda de `juscraper.core.http.HTTPScraper`, valida a
entrada e delega para `download.py` e `parse.py`. Estrutura obrigatória:

```python
"""Scraper para o {Nome Completo do Tribunal} ({SIGLA})."""
from typing import Any

import pandas as pd

from juscraper.core.http import HTTPScraper
from juscraper.utils.params import apply_input_pipeline_search

from .download import cjsg_download_manager
from .parse import cjsg_parse_manager
from .schemas import InputCJSG{SIGLA}


class {SIGLA}Scraper(HTTPScraper):
    """Scraper para o {Nome Completo do Tribunal}."""

    BASE_URL = "{url_base_do_tribunal}"

    def __init__(self, verbose: int = 0, download_path: str | None = None,
                 sleep_time: float = 1.0, **kwargs: Any):
        super().__init__("{SIGLA}", verbose=verbose, download_path=download_path,
                         sleep_time=sleep_time, **kwargs)

    # --- cjsg (jurisprudência) ---

    def cjsg(self, pesquisa: str | None = None,
             paginas: int | list | range | None = None, **kwargs) -> pd.DataFrame:
        """Busca jurisprudência no {SIGLA}.

        Args:
            pesquisa (str): Termo de busca livre.
            paginas (int | list | range | None): Páginas 1-based; ``None``
                baixa todas. Default ``None``.
            **kwargs: Filtros aceitos pelo schema :class:`InputCJSG{SIGLA}`.
                Listados abaixo (todos opcionais; ``None`` = sem filtro):

                * ``{filtro}`` ({tipo}): {descrição}.

        Aliases deprecados (popados com ``DeprecationWarning`` antes do pydantic):
            * ``query`` / ``termo`` -> ``pesquisa``
            * ``data_inicio`` / ``data_fim`` -> ``data_julgamento_inicio`` / ``_fim``

        Raises:
            TypeError: Quando um kwarg desconhecido é passado.
            ValidationError: Quando um filtro tem formato inválido.

        Returns:
            pd.DataFrame: Uma linha por decisão, com as colunas canônicas.

        See also:
            :class:`InputCJSG{SIGLA}`: schema pydantic, fonte da verdade
            dos filtros aceitos.
        """
        return self.cjsg_parse(self.cjsg_download(pesquisa, paginas, **kwargs))

    def cjsg_download(self, pesquisa: str | None = None,
                      paginas: int | list | range | None = None, **kwargs) -> list:
        """Baixa as respostas brutas da busca de jurisprudência do {SIGLA}.

        Aceita os mesmos filtros de :meth:`cjsg`; veja lá a lista completa.

        Returns:
            list: Uma resposta bruta por página baixada.
        """
        inp = apply_input_pipeline_search(
            InputCJSG{SIGLA}, "{SIGLA}Scraper.cjsg_download()",
            pesquisa=pesquisa, paginas=paginas, kwargs=kwargs,
            consume_pesquisa_aliases=True,
        )
        return cjsg_download_manager(
            inp.pesquisa, inp.paginas,
            request_fn=self._request_with_retry, sleep_time=self.sleep_time,
            # filtros validados: inp.data_julgamento_inicio, ...
        )

    def cjsg_parse(self, resultados_brutos: list) -> pd.DataFrame:
        """Processa as respostas brutas de :meth:`cjsg_download`.

        Args:
            resultados_brutos (list): Saída de :meth:`cjsg_download`.

        Returns:
            pd.DataFrame: Mesmo formato de :meth:`cjsg`.
        """
        return cjsg_parse_manager(resultados_brutos)
```

`download.py` concentra o HTTP: constantes (`BASE_URL`,
`RESULTS_PER_PAGE`), o payload builder **público**
`build_cjsg_payload(...)` (sem underscore, porque o script de captura
e os contratos o importam) e o `cjsg_download_manager`, que recebe o
`request_fn` e o `sleep_time` do client. `parse.py` converte as
respostas brutas em DataFrame e renomeia as chaves do backend para os
nomes canônicos.

**Regras de geração obrigatórias**:

- Herdar de `HTTPScraper`: ele cria a `requests.Session()`, monta o
  User-Agent `juscraper/<versão>` e guarda `sleep_time`. Não fixar
  User-Agent; se o site exigir UA de navegador, cookies iniciais ou
  adapter TLS, sobrescrever `_configure_session(session)`
- Mapear TODOS os campos do formulário como filtros do schema
- Nomes de parâmetros em português, seguindo convenções do CLAUDE.md:
  - `pesquisa` (nunca `query` ou `termo`)
  - `data_julgamento_inicio`, `data_julgamento_fim`
  - `data_publicacao_inicio`, `data_publicacao_fim`
  - `data_inicio`/`data_fim` como alias de `data_julgamento_*`
  - `tamanho_pagina` para itens por página
  - nomes canônicos `numero_processo` (Input), `relator`, `classe`,
    `assunto`
- Validar a entrada com `apply_input_pipeline_search` de
  `juscraper.utils.params` (aliases de busca e data, `paginas`,
  conversão de datas, pydantic e `TypeError` para kwarg desconhecido).
  Alias específico do tribunal sai antes, com
  `resolve_deprecated_alias`/`pop_deprecated_alias`
- Paginação **1-based** conforme convenção do juscraper
- `tqdm` para barra de progresso no download
- `time.sleep(sleep_time)` entre páginas (default `1.0`, pode ser mais
  se o site exigir)
- Requisições via `self._request_with_retry`, repassado ao download
  como `request_fn` (backoff exponencial para 403/429/5xx, máx 3
  tentativas por padrão)
- Retornar `pd.DataFrame` nas funções de consulta
- `logging` ao invés de `print`
- Tratar `paginas` como `int | list | range | None`
- Se `paginas` é `None`, buscar total e baixar tudo
- Linhas de no máximo 120 caracteres
- Type hints nos parâmetros principais
- Docstrings em português, estilo Google (`Args:`/`Returns:`/`Raises:`),
  com `See also:` apontando o schema; `*_download` referencia o método
  top-level com `:meth:` em vez de repetir os filtros

#### 4.2 Init: `src/juscraper/courts/{tribunal}/__init__.py`

```python
"""Scraper para o {SIGLA}."""

from juscraper.courts.{tribunal}.client import {SIGLA}Scraper

__all__ = ["{SIGLA}Scraper"]
```

#### 4.3 Registrar na factory

Acrescentar a entrada no dict `_SCRAPERS` de `src/juscraper/__init__.py`,
no formato `"módulo:Classe"` (a factory importa o módulo só quando a
sigla é pedida):

```python
"{tribunal}": "juscraper.courts.{tribunal}.client:{SIGLA}Scraper",
```

Não editar `src/juscraper/tribunal_manager.py`: é código morto, sem
nenhum import no pacote.

#### 4.4 Schemas: `src/juscraper/courts/{tribunal}/schemas.py`

Um par `Input<Endpoint><SIGLA>`/`Output<Endpoint><SIGLA>` por método
implementado (ver `references/juscraper-conventions.md`, seção
"Schemas pydantic"):

- Input herda de `SearchBase` (traz `pesquisa`, `paginas` e
  `extra="forbid"`) e dos mixins de data que o backend aceita; consulta
  por CNJ herda de `CnjInputBase` (`id_cnj: str | list[str]`). Declarar
  `BACKEND_DATE_FORMAT` quando o backend não usa `DD/MM/AAAA`. Não
  redeclarar `paginas`.
- Campos do Input iguais, byte a byte, aos parâmetros explícitos do
  método público (`tests/schemas/test_signature_parity.py`).
- Output herda de `OutputCJSGBase` (+ `OutputRelatoriaMixin`,
  `OutputDataPublicacaoMixin`) ou de `OutputCnjConsultaBase`, com os
  nomes canônicos de coluna (`processo`, `classe`, `assunto`,
  `relator`).
- Registrar o Input em
  `tests/schemas/test_schema_coverage.py::EXPECTED_COURT_SCHEMAS` e o
  Output em `tests/schemas/test_output_parity.py::EXPECTED_COURT_OUTPUT_SCHEMAS`.

#### 4.5 Testes: `tests/{tribunal}/`

O `CONTRIBUTING.md` do juscraper bloqueia o PR sem **contrato offline
por método público**. Seguir `references/test-patterns.md`, que traz a
lista completa e os templates:

- `tests/fixtures/capture/{tribunal}.py`: script que roda contra o
  site real, importando `build_cjsg_payload` e `BASE_URL`, e grava os
  samples em `tests/{tribunal}/samples/cjsg/` (typical com duas
  páginas, página única, sem resultados). Nunca sintetizar sample à mão.
- `tests/{tribunal}/test_cjsg_contract.py`: `@responses.activate`,
  `mocker.patch("time.sleep")`, samples via `load_sample`, matcher de
  payload montado com `build_cjsg_payload` e colunas conferidas por
  subset.
- `tests/{tribunal}/test_cjsg_filters_contract.py`: todos os filtros
  de uma vez chegando ao body e um teste por alias deprecado, com
  `pytest.warns(DeprecationWarning)`.
- Teste de schema (params aceitos, kwarg desconhecido, defaults), no
  diretório do tribunal ou em `tests/schemas/test_cjsg_schemas.py`.
- Opcional: `tests/{tribunal}/test_cjsg_integration.py` com
  `@pytest.mark.integration`, que o `pytest` padrão não roda.

**Importante**: Criar `tests/{tribunal}/__init__.py` (arquivo vazio)
para que o pytest descubra os testes.

### Etapa 5 — Validação

1. Rodar os testes offline:
   ```bash
   pytest tests/{tribunal}/ tests/schemas/ -v --tb=short
   ```
   E, se houver integração, contra o site real:
   ```bash
   pytest tests/{tribunal}/ -m integration -v --tb=short
   ```

2. Checklist de validação:
   - [ ] Contratos e `tests/schemas/` passam
   - [ ] DataFrame tem colunas coerentes com o site e nomes canônicos
   - [ ] Paginação funciona (página 2 ≠ página 1)
   - [ ] Filtros chegam ao body/params (teste de filtros)
   - [ ] `cjsg_download` devolve as respostas brutas e `cjsg_parse` as processa
   - [ ] Samples vieram do script de captura
   - [ ] Sem warnings de deprecação do próprio código

3. Se testes falharem, diagnosticar:
   - **Status 403/429**: Adicionar mais delay, verificar se o site
     exige User-Agent de navegador (via `_configure_session`) ou
     cookie de sessão
   - **HTML de erro no response**: Verificar se headers ou cookies
     estão corretos
   - **Dados vazios**: Verificar parsing (HTML vs JSON), seletores
     CSS, XPath, ou chaves JSON
   - **Timeout**: Aumentar timeout nas requisições, verificar se o
     site está fora do ar
   - **`ConnectionError` do `responses` no contrato**: o payload
     enviado não bateu com o matcher; comparar com `build_cjsg_payload`

4. Rodar os hooks do pre-commit (ruff, isort, pylint, flake8, mypy
   e bandit, conforme `.pre-commit-config.yaml`) nos arquivos novos:
   ```bash
   pre-commit run --files src/juscraper/courts/{tribunal}/*.py tests/{tribunal}/*.py \
       tests/fixtures/capture/{tribunal}.py
   ```

5. Se tudo passar, prosseguir para a Etapa 6 (Documentação).

### Etapa 6 — Documentação

Após todos os testes passarem, gerar a documentação completa.
**IMPORTANTE**: toda documentação em `docs/` deve ser escrita em
inglês (ver CLAUDE.md — português causa problemas de encoding no
build Quarto + GitHub Actions).

#### 6.1 Notebook de exemplo: `docs/notebooks/{tribunal}.ipynb`

Criar um Jupyter notebook com as seguintes seções:

1. **Header (markdown)**: título com nome do tribunal, breve
   descrição do scraper e tabela com funcionalidades/cores
   disponíveis (se aplicável).
2. **Basic search**: criar scraper, fazer busca simples com
   `cjsg()`, mostrar `shape` e `head(3)`.
3. **Available columns**: listar `df.columns.tolist()`.
4. **Preview ementa**: imprimir os primeiros 300 caracteres da
   ementa do primeiro resultado.
5. **Using filters**: demonstrar uso de filtros disponíveis
   (datas, magistrado, órgão julgador, etc.).
6. **Querying different cores/tabs** (se aplicável): mostrar como
   mudar o core/base de consulta.
7. **Download and parse separately**: demonstrar `cjsg_download()`
   + `cjsg_parse()` separados, inspecionando a resposta bruta.

Usar os notebooks existentes como referência de estilo (ex:
`docs/notebooks/tjdft.ipynb`, `docs/notebooks/tjrs.ipynb`).

#### 6.2 Atualizar `docs/_quarto.yml`

- Adicionar o notebook na seção `sidebar > Exemplos > Tribunais`
  (em ordem alfabética).
- Adicionar a classe do scraper na seção `quartodoc > sections >
  Scrapers de Tribunais > contents`.

#### 6.3 Atualizar `docs/index.qmd`

- Adicionar o tribunal na tabela "Tribunais Disponíveis" com as
  funcionalidades implementadas.
- Adicionar link para o notebook na lista "Notebooks de Exemplo".

#### 6.4 Atualizar `CHANGELOG.md`

- Adicionar entrada sob `[Unreleased]` → `Added` descrevendo o
  novo tribunal e suas funcionalidades.

## Decisões de Design

### Quando usar httpx ao invés de requests

Use `httpx` apenas se:
- O site requer HTTP/2 (raro em tribunais)
- O response é muito grande e precisa de streaming assíncrono
Na dúvida, use `requests` — é o padrão do projeto.

### Quando admitir que precisa de Playwright no código final

Em último caso, se o site:
- Renderiza conteúdo 100% via JavaScript sem nenhum endpoint de API
  identificável
- Usa WebSockets exclusivamente para dados
- Tem proteção anti-bot que bloqueia requests normais

Se o bloqueio for só um desafio JavaScript que emite um cookie
reutilizável (caso do AWS WAF no STF), a saída já adotada no
juscraper é obter o cookie com Playwright num extra opcional, com
import lazy, e seguir a raspagem em `requests`. Fora disso, informe o
usuário:
```
⚠️ O site do {TRIBUNAL} não expõe uma API acessível via requests.
Todo o conteúdo é renderizado via JavaScript no navegador.

Opções:
1. Usar Playwright/Selenium no código final (menos estável)
2. Verificar se existe API alternativa (DataJud, etc.)
3. Marcar como "não suportado" e tentar novamente no futuro

O que prefere?
```

### Tratamento de encoding

Tribunais brasileiros frequentemente usam:
- `latin-1` / `iso-8859-1` ao invés de `utf-8`
- Acentos mal codificados em responses

Sempre verificar o encoding do response e adicionar tratamento se
necessário:
```python
response.encoding = response.apparent_encoding
```

### Parsing de HTML

Preferir `BeautifulSoup` com `lxml` como parser. Se o HTML for
muito irregular, usar `lxml.html` diretamente. Para tabelas simples,
`pd.read_html()` pode ser suficiente.

## Notas de Segurança e Ética

- Manter o User-Agent identificável que o `HTTPScraper` monta
  (`juscraper/<versão>` com link do projeto); trocar por UA de
  navegador só quando o site exigir
- Respeitar `robots.txt` quando presente
- Manter delay mínimo de 1 segundo entre requisições
- Não fazer mais requisições do que o necessário para o teste
- Rodar testes de integração fora do horário comercial quando possível
- Não armazenar credenciais ou dados sensíveis no código
