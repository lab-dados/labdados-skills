---
name: raspe-builder
description: "Usar quando pedirem para adicionar fonte nova à biblioteca raspe ou fazer engenharia reversa de site governamental, de agência reguladora ou de imprensa para virar scraper do raspe. Não confundir com raspe (usar fontes existentes) nem com juscraper-builder (tribunais)."
---

# Raspe Builder

Skill para gerar scrapers que se encaixam na arquitetura da biblioteca
[`raspe`](https://github.com/bdcdo/raspe) — fachada única
`raspe.<fonte>().raspar(...)` retornando `pandas.DataFrame`. Cobre fontes
HTTP/HTML, HTTP/JSON e Playwright (com bypass de Cloudflare).

## Princípio fundamental

O **Playwright MCP é usado apenas como ferramenta de engenharia reversa** —
para navegar no site, capturar requisições HTTP e snapshots de HTML que
viram samples de teste. O **código final preferencialmente usa `requests`**
via `BaseScraper`. Recorra a `PlaywrightScraper` apenas quando o site
comprovadamente exigir browser (conteúdo 100% JavaScript sem endpoint
identificável, Cloudflare ativo bloqueando `requests`, ou autenticação por
fluxo interativo).

A escolha do caminho — HTTP/HTML, HTTP/JSON, ou Playwright — é uma decisão
da Etapa 1 (Reconhecimento), e determina o template de código da Etapa 4.

## Pré-requisitos

Antes de iniciar, verifique:

1. **Playwright MCP disponível**. Execute `/mcp` e confirme que `playwright`
   aparece na lista. Se não estiver:
   ```
   Preciso do Playwright MCP para navegar no site da fonte e capturar
   as requisições. Por favor rode no terminal:
   claude mcp add playwright -- npx @playwright/mcp@latest
   E reinicie o Claude Code.
   ```

2. **Repositório raspe clonado**. A skill se refere a esse caminho como
   `<RASPE_REPO>` ao longo do documento. Para detectar:
   - Procure no diretório atual e no clone irmão `../raspe`:
     ```bash
     for d in . ../raspe; do [ -d "$d/src/raspe" ] && [ -d "$d/tests" ] && (cd "$d" && pwd) && break; done
     ```
   - Confirme com o usuário o caminho impresso antes de usá-lo; se o
     comando não imprimir nada, pergunte o caminho.

   Sempre que aparecer `<RASPE_REPO>` nesta skill ou nos references,
   substitua pelo caminho confirmado com o usuário.

   O `<MARKETPLACE_ROOT>` (clone de `lab-dados/labdados-skills`, editado
   na Etapa 7) se acha do mesmo jeito, antes de qualquer `cd`:
   ```bash
   for d in . "<RASPE_REPO>/../labdados-skills"; do [ -d "$d/plugins/raspe/skills/raspe" ] && (cd "$d" && pwd) && break; done
   ```
   Confirme ou pergunte, como acima.

3. **Dependências do raspe**:
   ```bash
   cd <RASPE_REPO>
   uv pip install -e ".[dev,browser]"
   python -m playwright install chromium
   ```

4. **Ler primeiro**. Antes de gerar qualquer código, leia:
   - `CLAUDE.md` do raspe (convenções do projeto). Se esta skill e ele
     divergirem, vale o `CLAUDE.md`.
   - Pelo menos dois scrapers existentes do mesmo tipo que você vai criar:
     - Para HTTP/HTML: `src/raspe/scrapers/ipea.py` (modelo enxuto, 5 colunas) e `src/raspe/scrapers/capes.py` (modelo rico, 15 colunas, parsing condicional de campos por card).
     - Para HTTP/JSON: `src/raspe/scrapers/nyt.py`.
     - Para Playwright: `src/raspe/scrapers/anvisa.py` e `src/raspe/scrapers/saudelegis.py`.
   - `src/raspe/base_scraper.py` e `src/raspe/playwright_scraper.py` (a interface real, sempre).
   - `tests/ipea/test_raspar_contract.py` (padrão canônico de testes offline;
     para Playwright, `tests/saudelegis/test_raspar_contract.py`).
   - `references/raspe-architecture.md` desta skill para um resumo das classes-base.

## Workflow principal

### Etapa 1 — Reconhecimento do site

1. Use o Playwright MCP para navegar até a URL fornecida pelo usuário:
   ```
   browser_navigate → URL da página de busca da fonte
   ```

2. Tire um snapshot (`browser_snapshot`) para mapear formulário, campos,
   botões.

3. Identifique e documente:
   - **Natureza do dado**: legislação? jurisprudência? notícias? publicações?
     atos normativos? Se for jurisprudência ou processos judiciais, **pare**
     e redirecione para `juscraper-builder` — não é raspe.
   - **Tecnologia**: form HTML tradicional (server-rendered) / SPA com API
     JSON / página estática com JS no client / proteção anti-bot
     (Cloudflare, captcha, rate limit visível).
   - **Campos de busca**: texto livre, datas (formato aceito), dropdowns,
     filtros enum.
   - **Indicadores de problema**: captcha visível, "verifying you are
     human" (Cloudflare), bloqueio por IP em primeira tentativa.

4. **Decisão de caminho** (registre por escrito antes da Etapa 2):
   - **HTTP/HTML**: o site responde HTML server-rendered e o endpoint
     responde sem JavaScript. Caminho default; use sempre que possível.
   - **HTTP/JSON**: existe uma API que devolve JSON estruturado (XHR/fetch).
     Geralmente é o caminho mais limpo se você encontrar.
   - **Playwright**: nenhum dos dois funciona — JS-heavy SPA sem endpoint
     útil, Cloudflare ativo, autenticação interativa. Justifique por escrito
     antes de optar por este caminho.

5. **Se houver captcha** (não Cloudflare passivo): informe o usuário e
   encerre. raspe não cobre captcha hoje. Crie um documento curto
   `docs/captcha/<fonte>.md` no repo raspe com a observação e finalize.

6. Confirme com o usuário o caminho escolhido antes de prosseguir:
   ```
   Identifiquei o site da {FONTE} como {tipo}.
   Caminho escolhido: {HTTP/HTML | HTTP/JSON | Playwright}.
   Campos disponíveis: ...
   Vou prosseguir para captura de requisições.
   ```

### Etapa 2 — Captura de requisições

Veja `references/playwright-mcp-recon.md` para o protocolo detalhado.

1. Prepare a interceptação. Se `browser_network_requests` estiver
   disponível, use-a; senão use `browser_evaluate` com listeners
   `page.on('request')` / `page.on('response')`.

2. Preencha o formulário com termo de busca genérico (`"saúde"`,
   `"educação"`, `"economia"`) que produza resultados. Use datas amplas se
   houver campo de data.

3. Submeta o formulário (`browser_click` no botão de busca).

4. Capture as requisições. Identifique a **principal**:
   - URL com keywords: `search`, `pesquisa`, `consulta`, `busca`, `api`,
     `resultado`.
   - Método: GET ou POST.
   - `resourceType`: `fetch`, `xhr`, ou `document`.
   - Ignore CSS/JS/imagens.

5. **Análise de paginação**: clique para ir à página 2 e capture a nova
   requisição. Compare com a página 1 — identifique:
   - Nome do parâmetro de página: `page`, `pagina`, `offset`, `start`, `sr`, etc.
   - Tipo: número de página ou offset, e o valor do parâmetro na página 1
     (ex.: `pagina=1`, `page=0`, `sr=1`).
   - Localização: query string ou body.

   **Atenção — validar via `requests` antes de escrever o scraper.** A URL
   que o navegador exibe ao clicar em "página 2" não prova que o parâmetro
   seja respeitado pelo servidor. Alguns sites (Joomla, SPAs com paginação
   client-side) montam URLs com `?page=2` via JS, mas o backend ignora o
   parâmetro e devolve sempre a página 1 — a paginação real está num
   handler JS que faz scroll/AJAX. Confirme assim:
   ```python
   import requests
   url = "<endpoint capturado>"
   p1 = requests.get(url, params={...}).text
   p2 = requests.get(url, params={..., "<param_paginacao>": "2"}).text
   # Comparar o primeiro título/registro:
   import re
   def primeiro(html):
       m = re.search(r'<a[^>]*class="<sel-titulo>"[^>]*>\s*([^<]+)', html)
       return m.group(1).strip()[:60] if m else None
   assert primeiro(p1) != primeiro(p2), "Parâmetro não está paginando — o servidor ignora"
   ```
   Se os dois retornarem o mesmo primeiro registro, o parâmetro não é o
   correto. Teste alternativos (`page` vs `pag` vs `start` vs `offset`,
   às vezes com filtros default obrigatórios) e/ou retorne ao Playwright
   MCP para inspecionar a URL real depois do `click`.

6. **HTML de referência**. Salve o HTML completo das páginas 1 e 2 (e
   responses JSON, se for o caso) em `<PASTA_RECON>/page_01.html` (e
   `page_02.html`), onde `<PASTA_RECON>` é o caminho impresso por
   `mktemp -d "${TMPDIR:-/tmp}/raspe-recon-<fonte>.XXXXXX"` (para
   reachá-lo: `ls -d "${TMPDIR:-/tmp}"/raspe-recon-<fonte>.*`). Esses
   arquivos servem para escrever o parser (e, nos Playwright, viram
   samples na Etapa 6).
   - HTTP: copie `r.text` da resposta.
   - Playwright: use `browser_evaluate` com `document.documentElement.outerHTML`.

7. **Headers necessários**: registre quais headers a requisição original
   carrega (User-Agent, Accept-Language, cookies, CSRF token). Cookies de
   sessão que vêm do GET inicial precisam ser herdados — `BaseScraper` já
   resolve isso porque usa `requests.Session()`.

### Etapa 3 — Análise e mapeamento

Crie um documento interno (pode ser um comentário no arquivo final ou
nota temporária) com:

```
FONTE: {nome curto, ex: "tesouro"}
NOME DA CLASSE: Scraper{Fonte}  (ex: ScraperTesouro)
NOME DO BUSCADOR: "tesouro"  (passado em super().__init__(...))

ENDPOINT: {url completa}
MÉTODO: {GET | POST}
CONTENT-TYPE REQ: {application/x-www-form-urlencoded | application/json | ...}
FORMATO RESPOSTA: {HTML | JSON}
ENCODING: {utf-8 | latin-1 | ...}

PARÂMETROS DA QUERY:
  - {param}: {valor, descrição, obrigatório?}
  - ...

PARÂMETROS DO RASPAR() (viram o schema de entrada):
  - pesquisa: sempre este nome (mixin de pesquisa)
  - {paginas (só HTTP), data_inicio/data_fim, ano: se a fonte aceita}
  - {parâmetro próprio: tipo, default, valores aceitos}

PAGINAÇÃO:
  - query_page_name: {nome do param}
  - tipo: {numero_pagina | offset}
  - query_page_multiplier: {1 se for número de página direto;
                             N se for offset com step N (ex: 25 para Folha)}
  - query_page_increment: {valor do parâmetro na página 1 menos o
                           multiplier (tabela em raspe-architecture.md)}
  - valor do parâmetro na página 1 e na página 2: {…}
  - itens por página: N
  - como obter total: {regex em HTML | campo no JSON | header}

HEADERS NECESSÁRIOS:
  - User-Agent: {valor}
  - Accept-Language: {valor}
  - Outros: {se houver}

COOKIES/SESSÃO:
  - Precisa de GET prévio? {sim/não}
  - Tokens CSRF? {sim/não, como obter}

PARA PLAYWRIGHT (se aplicável):
  - url_base: {URL inicial}
  - selector do campo de busca: {CSS}
  - selector do botão de busca: {CSS}
  - pagination_strategy: {NUMBERED_LINKS | NEXT_BUTTON | LOAD_MORE | INFINITE_SCROLL | SELECT_DROPDOWN | NONE}
  - selector de paginação: {CSS}
  - tem Cloudflare? {sim/não}

COLUNAS EXTRAÍDAS DO PARSE (viram o schema de saída, nesta ordem):
  - {coluna1: descrição, exemplo tirado do site}
  - ...
```

### Etapa 4 — Geração de código

Antes de escrever, leia novamente os scrapers de referência (item 4 da
seção Pré-requisitos) — o código real é a verdade canônica.

Localização: `src/raspe/scrapers/<fonte>.py`, com os schemas em
`src/raspe/schemas/<fonte>.py`.

#### 4.0 — Schemas de entrada e saída

Toda fonte nova declara `schema_entrada` e `schema_saida` (regra do
`CLAUDE.md` do raspe). Modelo: `src/raspe/schemas/ipea.py`; detalhes em
`references/raspe-architecture.md` (seção "Schemas").

```python
"""Schemas de ``raspe.{fonte}().raspar()``: {descrição da fonte}."""

from pydantic import Field

from .base import OutputBase, PaginasMixin, PesquisaObrigatoriaMixin


class Input{Fonte}(PaginasMixin, PesquisaObrigatoriaMixin):
    """Parâmetros de ``Scraper{Fonte}.raspar()``."""


class Output{Fonte}(OutputBase):
    """{O que cada linha representa}."""

    titulo: str = Field(description="Título.", examples=["{valor real de um sample}"])
    link: str = Field(description="Endereço no portal.", examples=["{valor real de um sample}"])
    # ... uma coluna por campo, na ordem em que o _parse_page as monta
```

- Escolha os mixins de `schemas/base.py` pelos parâmetros da Etapa 3
  (lista na seção "Schemas" da reference). `PaginasMixin` só em fonte
  HTTP: quem lê `paginas` é o `BaseScraper`.
- Cada campo do `Input` tem de ser lido no código do raspador (ou da
  base) com o nome literal, `kwargs['x']` ou `kwargs.get('x')`, e nada
  além deles: `tests/schemas/test_signature_parity.py` confere as duas
  direções.
- Os `examples` do `Output` têm de aparecer nos samples da Etapa 6
  (`tests/schemas/test_output_parity.py` confere).
- Exportar os dois em `src/raspe/schemas/__init__.py` (import e `__all__`).

#### 4.A — Template HTTP/HTML

Modelo enxuto: `src/raspe/scrapers/ipea.py`.

```python
from typing import Any, Literal

import pandas as pd

from ..base_scraper import BaseScraper
from ..html_scraper import HTMLScraper
from ..schemas.{fonte} import Input{Fonte}, Output{Fonte}


class Scraper{Fonte}(BaseScraper, HTMLScraper):
    schema_entrada = Input{Fonte}
    schema_saida = Output{Fonte}

    def __init__(self):
        super().__init__("{nome_buscador}")

        self._api_base = "{URL_DO_ENDPOINT}"
        self._api_method: Literal['GET'] = 'GET'  # ou 'POST'
        self._type: Literal['HTML'] = 'HTML'
        self._query_page_name = '{nome_param_pagina}'

        # Se o site usa offset com step N (ex: Folha com sr=1,26,51):
        # self.query_page_multiplier = 25
        # self.query_page_increment = -24  # página 1 → sr=1

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (...)",
            "Accept-Language": "pt-BR,en-US;q=0.7,en;q=0.3",
            # ... os headers reais do site
        })

    @property
    def api_base(self) -> str:
        return self._api_base

    @property
    def type(self) -> Literal['HTML']:
        return self._type

    @property
    def query_page_name(self) -> str:
        return self._query_page_name

    @property
    def api_method(self) -> Literal['GET']:
        return self._api_method

    def _set_query_base(self, **kwargs) -> dict[str, Any]:
        pesquisa = kwargs['pesquisa']

        return {
            '{nome_param_busca_no_site}': pesquisa,
            # Com IntervaloDatasMixin, a data ausente chega como None (o schema
            # preenche os defaults): '{nome_param_data_inicio}': kwargs['data_inicio'] or '',
            # ... demais params do Input{Fonte}
        }

    def _find_n_pags(self, r0) -> int:
        r0.raise_for_status()
        soup = self.soup_it(r0.content)
        marcador = soup.select_one('{seletor da contagem total}')
        if not marcador:
            # Aviso de busca vazia → 0; manutenção ou anti-robô → ScraperError
            return self._confirmar_busca_vazia(soup)
        total = int(marcador.get_text(strip=True))  # ajustar a extração
        itens_por_pagina = 10
        # Teto de resultados da fonte: max_resultados= (ver _paginas_para na raspe-architecture.md)
        return self._paginas_para(total, itens_por_pagina)

    def _parse_page(self, path: str) -> pd.DataFrame:
        from bs4 import BeautifulSoup

        # Sem try na página inteira: o erro de leitura sobe (ver _parse_data)
        with open(path, 'r', encoding='utf-8') as f:
            html = f.read()

        soup = BeautifulSoup(html, 'html.parser')
        registros = []

        for item in soup.select('{seletor dos cards}'):
            try:
                titulo = item.select_one('{seletor titulo}').text.strip()
                link = item.select_one('a')['href']
                # ... demais campos
                registros.append([titulo, link, '...'])
            except Exception as e:
                self.logger.warning(f"Erro parseando item: {e}")
                continue

        return pd.DataFrame(registros, columns=self.colunas)
```

Regras obrigatórias HTTP/HTML:

- Nome da classe: `Scraper{Fonte}` em CamelCase (ex: `ScraperTesouro`,
  `ScraperCapes`). Padrão único — não invente variações como
  `{Nome}Scraper`.
- `nome_buscador` em minúsculas curtas (ex: `"ipea"`, `"folha"`, `"nyt"`).
- Headers `User-Agent` real (Firefox/Chrome) — sites brasileiros bloqueiam
  User-Agents genéricos.
- `_parse_page` usa `columns=self.colunas`, também na página sem itens.
  Não declare `colunas` na classe: com `schema_saida`, a base as tira do
  schema. Não capture o erro de leitura da página inteira para devolver
  DataFrame vazio: deixe-o subir (ver `_parse_data` na
  `raspe-architecture.md`). Só o item que falha é pulado, com aviso no log.
- Sem o marcador de contagem, `_find_n_pags` devolve
  `self._confirmar_busca_vazia(soup)`, nunca 0 (item 6 de "Estrutura de
  Scrapers" no `CLAUDE.md` do raspe).
- Nunca tocar em `sleep_time` para reduzir (o default 2s é conservador);
  aumente se o site exigir.
- `time.sleep`, retry para 429/5xx e progress bar via `tqdm` são feitos
  automaticamente pelo `BaseScraper` — não duplique.

#### 4.B — Template HTTP/JSON

Modelo: `src/raspe/scrapers/nyt.py`.

Diferenças em relação a 4.A:

- Não herde de `HTMLScraper`.
- `self._type: Literal['JSON'] = 'JSON'`.
- `_find_n_pags`: `r0.json()['response']['meta']['hits']` (ou caminho
  equivalente da API), passado a `self._paginas_para`.
- `_parse_page` lê JSON do disco (`json.load(open(path, encoding='utf-8'))`) e itera sobre a
  lista de resultados.
- Se houver API key: valide no `__init__` com `APIKeyError` (importar de
  `raspe.exceptions`) — replique o padrão do `ScraperNYT`.
- Se a API tiver rate limit hard (ex: 5 req/min), ajuste `self.sleep_time`
  no `__init__`.

#### 4.C — Template Playwright

Modelo: `src/raspe/scrapers/anvisa.py`. Use **apenas** se a Etapa 1
provou que HTTP não funciona.

```python
import asyncio
from typing import Any

import pandas as pd

from ..playwright_scraper import PaginationStrategy, PlaywrightScraper
from ..schemas.{fonte} import Input{Fonte}, Output{Fonte}


class Scraper{Fonte}(PlaywrightScraper):
    schema_entrada = Input{Fonte}  # com PesquisaNavegadorMixin
    schema_saida = Output{Fonte}

    def __init__(self, debug: bool = True, headless: bool = True):
        super().__init__("{nome_buscador}", debug=debug, headless=headless)
        self._url_base = "{URL_INICIAL}"
        self._pagination_strategy = PaginationStrategy.NUMBERED_LINKS
        # ou: NEXT_BUTTON | LOAD_MORE | INFINITE_SCROLL | SELECT_DROPDOWN | NONE

    @property
    def url_base(self) -> str:
        return self._url_base

    async def _executar_busca(self, **kwargs) -> None:
        termo = kwargs['pesquisa']
        await self._preencher_campo("{seletor do campo de busca}", termo)
        await self._clicar_elemento("{seletor do botão de busca}")
        # A base já espera page_load_wait depois deste método.

    async def _encontrar_total_paginas(self) -> int:
        # Lê do HTML carregado o total de páginas
        html = await self._obter_html()
        # Regex ou parsing
        return 1

    # Se pagination_strategy for NEXT_BUTTON ou LOAD_MORE, sobrescreva:
    async def _paginar_por_botao_proximo(self) -> bool:
        try:
            await self._clicar_elemento("{seletor do botão próximo}")
            await asyncio.sleep(self.between_pages_wait)
            return True
        except Exception:
            return False

    def _parse_page(self, path: str) -> pd.DataFrame:
        # Sync, lê arquivo HTML do disco, retorna DataFrame
        from bs4 import BeautifulSoup
        with open(path, 'r', encoding='utf-8') as f:
            html = f.read()
        soup = BeautifulSoup(html, 'html.parser')
        # ... extração, uma lista por item na ordem de Output{Fonte}
        return pd.DataFrame(registros, columns=self.colunas)
```

Regras obrigatórias Playwright:

- Cloudflare bypass já é automático (`_aguardar_cloudflare()` é chamado
  pelo `_baixar_async` da base).
- Estratégia de paginação tem que casar com o que o site oferece. Se for
  `NEXT_BUTTON` ou `LOAD_MORE`, **sobrescreva** o método correspondente
  (`_paginar_por_botao_proximo` / `_paginar_por_carregar_mais`) — a base
  levanta `NotImplementedError` no default.
- `_parse_page` é sync (não `async`); ele lê o arquivo HTML salvo em disco
  por `_salvar_html_pagina`.
- Usar `self._page` direto (atributo `Optional`, `None` até a
  inicialização) tende a quebrar o mypy do pre-commit; `saudelegis` e
  `datalegis` passam porque estão em `[[tool.mypy.overrides]]` no
  `pyproject.toml` do raspe, então inclua o módulo novo ali se for o caso.

### Etapa 5 — Registro no factory

Ver `references/factory-registration.md`. Em `src/raspe/__init__.py`:

1. Para HTTP: import no topo:
   ```python
   from .scrapers.{fonte} import Scraper{Fonte}
   ```

2. Para Playwright: import lazy dentro da factory (para não quebrar quando
   o extra `[browser]` não está instalado):
   ```python
   def {fonte}(**kwargs):
       """..."""
       from .scrapers.{fonte} import Scraper{Fonte}
       return Scraper{Fonte}(**kwargs)
   ```

3. Factory pública:
   ```python
   def {fonte}(**kwargs):
       """Cria um raspador para {descrição da fonte}.

       Args:
           pesquisa: Termo de busca.

       Returns:
           Scraper{Fonte}: Instância configurada do raspador.
       """
       return Scraper{Fonte}(**kwargs)
   ```

4. Adicionar `"{fonte}"` na lista `__all__`, na seção apropriada (HTTP ou
   Browser).

5. Registrar a classe, HTTP ou Playwright, no `_MAPPING` de `scraper()`
   em `src/raspe/scraper_manager.py` (`"{FONTE}": Scraper{Fonte}`) e
   reexportá-la em `src/raspe/scrapers/__init__.py` (import e `__all__`).
   `tests/test_scraper_manager.py` e `tests/test_scrapers_init.py`
   reprovam fonte que falte num dos dois.

6. Testar o registro: um caso em `tests/test_init.py` (classe
   `TestFactoriesHTTP` ou `TestFactoriesPlaywright`).

### Etapa 6 — Testes de contrato offline

Siga `references/test-patterns.md`: captura dos samples, template do
contrato, casos mínimos e regras do `CLAUDE.md` do raspe. Modelos:
`tests/ipea/test_raspar_contract.py` (HTTP) e
`tests/saudelegis/test_raspar_contract.py` (Playwright).

1. Criar `tests/{fonte}/__init__.py` (vazio).
2. Criar o script de captura `tests/fixtures/capture/{fonte}.py`,
   obrigatório pelo `CLAUDE.md` do raspe, e rodá-lo para gravar em
   `tests/{fonte}/samples/raspar/` os samples `page_01.html`,
   `page_02.html`, `single_page.html` e `no_results.html`.
3. Criar `tests/{fonte}/test_raspar_contract.py` com os casos typical
   (paginação), single_page e no_results. HTTP usa `responses`;
   Playwright usa a página falsa de `navegador_falso`, sem abrir o
   navegador.
4. (Playwright) Criar também `tests/{fonte}/test_config.py`, com
   construtor e `_parse_page` sobre `samples/parse/`.

Com os samples gravados, registre a fonte em `ESPERADOS` de
`tests/schemas/test_schema_coverage.py` (ver `references/test-patterns.md`,
seção "Registro do schema"). Sem isso, a suíte reprova. Ponha também a
classe em `RASPADORES` de `tests/test_parse_page_erros.py` (seção "Erro de
leitura da página").

### Etapa 7 — Validação e documentação

1. Rodar testes. O `addopts` do raspe liga `--cov=src/raspe` e
   `fail_under = 80` vale para a suíte inteira, então a fonte isolada
   reprova por cobertura mesmo com todos os testes verdes; rode-a com
   `--no-cov` e, antes do PR, a suíte completa para conferir o gate.
   `filterwarnings = ["error"]` está ativo: warning não capturado vira
   falha.
   Regere `docs/colunas.md` antes dos testes, e de novo a cada mudança
   no schema: `tests/schemas/test_documentacao.py` o confere e roda já
   na fonte isolada, que inclui `tests/schemas/`:
   ```bash
   cd <RASPE_REPO>
   python -m raspe.schemas.documentacao
   pytest tests/{fonte}/ tests/schemas/ tests/test_parse_page_erros.py -v --no-cov
   pytest
   ```

2. Teste de integração rápido (não-mockado), com permissão do usuário:
   ```bash
   python -c "import raspe; df = raspe.{fonte}().raspar(pesquisa='X', paginas=range(1, 2)); print(df.shape); print(df.head())"
   ```
   Em fonte Playwright, cujo schema recusa `paginas` com `ValidationError`,
   limite pelo teto interno (o `UserWarning` de teto atingido é esperado):
   ```bash
   python -c "import raspe; s = raspe.{fonte}(); s._max_pages = 1; df = s.raspar(pesquisa='X'); print(df.shape); print(df.head())"
   ```

3. Atualizar `CHANGELOG.md` do raspe: uma linha em `### Adicionado`,
   sob `## [Não lançado]`, em pt-BR e no particípio ("Adicionado scraper
   X").

4. **Sincronizar a skill `raspe` do marketplace** — ver
   `references/raspe-skill-sync.md`. Isso fecha o ciclo: a skill que
   ensina a usar a biblioteca passa a conhecer a nova fonte. A edição é
   feita no `<MARKETPLACE_ROOT>` confirmado nos Pré-requisitos (item 2).

5. (Opcional) Criar notebook em `notebooks/NN_{fonte}.ipynb` no padrão
   dos vizinhos, se a fonte for de interesse alto.

6. Conferir `references/checklist.md` antes de declarar a fonte pronta.

## Decisões de design

### Quando admitir Playwright no código final

Apenas se:

- O site é uma SPA sem nenhum endpoint XHR/fetch identificável.
- Cloudflare ativo bloqueia `requests` mesmo com User-Agent realista.
- Autenticação interativa exige cliques (raríssimo em fontes públicas).

Antes de optar, tente: User-Agent de navegador real, headers completos
copiados do DevTools, sessão com cookies herdados de GET inicial.
Se nada disso passar, então Playwright.

### Nome do parâmetro de busca

O parâmetro de busca do `raspar()` é sempre `pesquisa`, vindo de um mixin
de pesquisa do schema de entrada. Com ele, a base adiciona a coluna
`termo_busca`, que todo `Output` tem. O nome do parâmetro no site fica
só no `_set_query_base` (ex.: NYT recebe `pesquisa` e envia `q` à API).
Nome antigo de fonte já publicada vai em `aliases_deprecados`.

### Encoding

Muitos sites governamentais brasileiros respondem em latin-1 / iso-8859-1.
A base grava toda página em UTF-8, qualquer que seja o encoding do site,
então o `_parse_page` lê sempre com `encoding='utf-8'` (em `latin-1`, os
acentos quebram e o `tests/test_parse_page_erros.py` reprova). Se o
arquivo gravado já sai com acento quebrado (só HTTP), corrija o
`r.encoding` num `_set_r` sobrescrito (`references/raspe-architecture.md`,
`_set_r`).

## Ética e operação

- User-Agent identificável (Firefox/Chrome real, não "Python-requests").
- Não diminuir `sleep_time` abaixo de 2s.
- Comece testando com `paginas=range(1, 2)`; expanda só depois de
  confirmar com o usuário.
- Sites governamentais são infraestrutura pública — uma coleta agressiva
  derruba o serviço para outros pesquisadores. Rodar em horários
  off-peak quando possível.

## Arquivos de referência

| Arquivo | Quando ler |
|---|---|
| `references/raspe-architecture.md` | Sempre antes de gerar código. Cobre a API real de `BaseScraper`, `HTMLScraper`, `PlaywrightScraper`. |
| `references/playwright-mcp-recon.md` | Etapa 2 (captura de requisições) — protocolo objetivo de uso do Playwright MCP. |
| `references/test-patterns.md` | Etapa 6 — padrão `responses` (HTTP) ou `navegador_falso` (Playwright) + samples HTML. |
| `references/factory-registration.md` | Etapa 5 — como editar `src/raspe/__init__.py`. |
| `references/raspe-skill-sync.md` | Etapa 7 — como atualizar a skill `raspe` do marketplace. |
| `references/checklist.md` | Final, antes de declarar a fonte pronta. |
