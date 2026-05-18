---
name: raspe-builder
description: >
  Gera scrapers Python para a biblioteca raspe (https://github.com/bdcdo/raspe)
  via engenharia reversa com Playwright MCP. Use sempre que o usuário pedir
  para adicionar uma fonte nova ao raspe, criar um scraper que retorne
  pandas.DataFrame seguindo a arquitetura `raspe.<fonte>().raspar(...)`, ou
  fazer engenharia reversa de um site governamental brasileiro / imprensa /
  agência reguladora para coleta empírica. Também use quando o usuário
  mencionar "novo scraper para o raspe", "extender BaseScraper",
  "PlaywrightScraper", "novo módulo em src/raspe/scrapers", ou pedir para
  contribuir uma fonte ao repositório bdcdo/raspe. Cobre os três caminhos
  da arquitetura: HTTP/HTML (BaseScraper+HTMLScraper), HTTP/JSON
  (BaseScraper), e Playwright/stealth (PlaywrightScraper). Não confundir
  com a skill `raspe` (que ensina a usar fontes já existentes) nem com a
  skill `juscraper-builder` (que cria scrapers de tribunais para o pacote
  juscraper). Mesmo que o usuário não diga "raspe-builder", use esta skill
  se a tarefa é construir um novo scraper compatível com a arquitetura raspe.
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

2. **Repositório raspe clonado**. O destino esperado é
   `/home/brunodcdo/Desktop/dev/raspe`. Se outro caminho for usado,
   pergunte ao usuário. Confirme que `src/raspe/` e `tests/` existem.

3. **Dependências do raspe**:
   ```bash
   cd /home/brunodcdo/Desktop/dev/raspe
   uv pip install -e ".[dev,browser]"
   python -m playwright install chromium
   ```

4. **Ler primeiro**. Antes de gerar qualquer código, leia:
   - `CLAUDE.md` do raspe (convenções do projeto).
   - Pelo menos dois scrapers existentes do mesmo tipo que você vai criar:
     - Para HTTP/HTML: `src/raspe/scrapers/ipea.py` (modelo enxuto, 5 colunas) e `src/raspe/scrapers/capes.py` (modelo rico, 15 colunas, parsing condicional de campos por card).
     - Para HTTP/JSON: `src/raspe/scrapers/nyt.py`.
     - Para Playwright: `src/raspe/scrapers/anvisa.py` e `src/raspe/scrapers/saudelegis.py`.
   - `src/raspe/base_scraper.py` e `src/raspe/playwright_scraper.py` (a interface real, sempre).
   - `tests/ipea/test_raspar_contract.py` (padrão canônico de testes offline).
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
   - Nome do parâmetro de página: `page`, `pagina`, `offset`, `start`, `rg`, etc.
   - Tipo: número de página (1, 2, 3) ou offset (0, 10, 20).
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

6. **Captura de samples**. Salve o HTML completo das páginas 1 e 2 (e
   responses JSON, se for o caso) em
   `/tmp/raspe-recon/<fonte>/page_01.html` (e `page_02.html`). Esses
   arquivos vão virar samples de teste na Etapa 6.
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

NOME DO PARÂMETRO DE PESQUISA NO RASPAR(): {pesquisa | termo | texto | assunto}
  (escolha que case com sites análogos no raspe; default: "pesquisa")

PAGINAÇÃO:
  - query_page_name: {nome do param}
  - tipo: {numero_pagina | offset}
  - query_page_multiplier: {1 se for número de página direto;
                             N se for offset com step N (ex: 25 para Folha)}
  - query_page_increment: {0 se 1-based; -1 se 0-based; etc.}
  - 1-based ou 0-based no site?
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

COLUNAS EXTRAÍDAS DO PARSE:
  - {coluna1, coluna2, ...}
```

### Etapa 4 — Geração de código

Antes de escrever, leia novamente os scrapers de referência (Etapa 4 do
pré-requisito) — o código real é a verdade canônica.

Localização: `src/raspe/scrapers/<fonte>.py`.

#### 4.A — Template HTTP/HTML

Modelo enxuto: `src/raspe/scrapers/ipea.py`.

```python
from typing import Any, Literal

import pandas as pd

from ..base_scraper import BaseScraper
from ..html_scraper import HTMLScraper


class Scraper{Fonte}(BaseScraper, HTMLScraper):
    def __init__(self):
        super().__init__("{nome_buscador}")

        self._api_base = "{URL_DO_ENDPOINT}"
        self._api_method: Literal['GET'] = 'GET'  # ou 'POST'
        self._type: Literal['HTML'] = 'HTML'
        self._query_page_name = '{nome_param_pagina}'

        # Se o site usa offset com step N (ex: Folha com rg=0,25,50):
        # self.query_page_multiplier = 25
        # self.query_page_increment = -25  # para 1 → 0

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
        pesquisa = kwargs.get('pesquisa')
        data_inicio = kwargs.get('data_inicio', '')
        data_fim = kwargs.get('data_fim', '')

        return {
            '{nome_param_busca_no_site}': pesquisa,
            '{nome_param_data_inicio}': data_inicio,
            '{nome_param_data_fim}': data_fim,
            # ... demais params; coloque defaults vazios para campos não-obrigatórios
        }

    def _find_n_pags(self, r0) -> int:
        r0.raise_for_status()
        soup = self.soup_it(r0.content)
        # Localize o elemento com a contagem total
        # Calcule: pages = (total + itens_por_pagina - 1) // itens_por_pagina
        total = 0
        # ... extração via soup.find / select
        itens_por_pagina = 10
        return (total + itens_por_pagina - 1) // itens_por_pagina

    def _parse_page(self, path: str) -> pd.DataFrame:
        from bs4 import BeautifulSoup

        columns = ['titulo', 'link', 'data', '...']  # ajustar

        try:
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

            return pd.DataFrame(registros, columns=columns)

        except Exception as e:
            self.logger.error(f"Erro parseando {path}: {e}")
            return pd.DataFrame(columns=columns)
```

Regras obrigatórias HTTP/HTML:

- Nome da classe: `Scraper{Fonte}` em CamelCase (ex: `ScraperTesouro`,
  `ScraperCapes`). Padrão único — não invente variações como
  `{Nome}Scraper`.
- `nome_buscador` em minúsculas curtas (ex: `"ipea"`, `"folha"`, `"nyt"`).
- Headers `User-Agent` real (Firefox/Chrome) — sites brasileiros bloqueiam
  User-Agents genéricos.
- `_parse_page` tem que retornar `pd.DataFrame` com colunas consistentes
  mesmo no caminho de erro (`pd.DataFrame(columns=columns)`).
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
  equivalente da API).
- `_parse_page` lê JSON do disco (`json.load(open(path))`) e itera sobre a
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


class Scraper{Fonte}(PlaywrightScraper):
    def __init__(self, debug: bool = True, headless: bool = True):
        super().__init__("{nome_buscador}", debug=debug, headless=headless)
        self._url_base = "{URL_INICIAL}"
        self._pagination_strategy = PaginationStrategy.NUMBERED_LINKS
        # ou: NEXT_BUTTON | LOAD_MORE | INFINITE_SCROLL | SELECT_DROPDOWN | NONE

    @property
    def url_base(self) -> str:
        return self._url_base

    async def _executar_busca(self, **kwargs) -> None:
        termo = kwargs.get('termo') or kwargs.get('pesquisa', '')
        await self._preencher_campo("{seletor do campo de busca}", termo)
        await self._clicar_elemento("{seletor do botão de busca}")
        await asyncio.sleep(self.page_load_wait)

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
        # ... extração
        return pd.DataFrame(...)
```

Regras obrigatórias Playwright:

- Cloudflare bypass já é automático (`_aguardar_cloudflare()` é chamado
  pelo `_raspar_async` da base).
- Estratégia de paginação tem que casar com o que o site oferece. Se for
  `NEXT_BUTTON` ou `LOAD_MORE`, **sobrescreva** o método correspondente
  (`_paginar_por_botao_proximo` / `_paginar_por_carregar_mais`) — a base
  levanta `NotImplementedError` no default.
- `_parse_page` é sync (não `async`); ele lê o arquivo HTML salvo em disco
  por `_salvar_html_pagina`.
- O kwarg de busca tem que ser nomeado (`termo` / `pesquisa` / `assunto`)
  para que o `BaseScraper` adicione a coluna `termo_busca` no DataFrame
  final. Verifique a lista em `_raspar_async` do `PlaywrightScraper`:
  `['assunto', 'pesquisa', 'termo', 'q', 'query']`.

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
           pesquisa/termo/texto: Termo de busca.

       Returns:
           Scraper{Fonte}: Instância configurada do raspador.
       """
       return Scraper{Fonte}(**kwargs)
   ```

4. Adicionar `"{fonte}"` na lista `__all__`, na seção apropriada (HTTP ou
   Browser).

### Etapa 6 — Testes de contrato offline

Ver `references/test-patterns.md`. Padrão canônico:
`tests/ipea/test_raspar_contract.py`.

1. Criar `tests/{fonte}/__init__.py` (vazio).
2. Salvar samples HTML capturados na Etapa 2 em
   `tests/{fonte}/samples/raspar/page_01.html` e `page_02.html`.
3. Criar `tests/{fonte}/test_raspar_contract.py`:
   ```python
   import pytest
   import responses

   from raspe.scrapers.{fonte} import Scraper{Fonte}
   from tests._helpers import load_sample_bytes

   API_URL = "{endpoint do scraper}"
   COLUNAS_OBRIGATORIAS = {"titulo", "link", "..."}


   @pytest.fixture
   def scraper():
       return Scraper{Fonte}()


   class TestRasparContract:
       @responses.activate
       def test_typical_paginacao(self, scraper, mocker):
           mocker.patch("time.sleep")
           responses.add(responses.GET, API_URL,
               body=load_sample_bytes("{fonte}", "raspar/page_01.html"),
               status=200, content_type="text/html; charset=utf-8")
           # Adicionar responses extras para página 2 etc.

           df = scraper.raspar(pesquisa="economia")

           assert not df.empty
           assert COLUNAS_OBRIGATORIAS <= set(df.columns)
           assert "termo_busca" in df.columns
   ```

Casos mínimos: paginação típica, zero resultados, presença da coluna
`termo_busca`, conjunto mínimo de colunas. Não escreva testes de retry —
já estão cobertos em `tests/test_base_scraper.py`.

Para Playwright: capture HTMLs reais durante a engenharia reversa e teste
apenas `_parse_page(path)` diretamente. Mockar a navegação Playwright é
caro e instável.

### Etapa 7 — Validação e documentação

1. Rodar testes:
   ```bash
   cd /home/brunodcdo/Desktop/dev/raspe
   pytest tests/{fonte}/ -v
   ```

2. Teste de integração rápido (não-mockado), com permissão do usuário:
   ```bash
   python -c "import raspe; df = raspe.{fonte}().raspar(pesquisa='X', paginas=range(1, 2)); print(df.shape); print(df.head())"
   ```

3. Atualizar `CHANGELOG.md` do raspe (seção `[Unreleased] / Added`).

4. **Sincronizar a skill `raspe` do marketplace** — ver
   `references/raspe-skill-sync.md`. Isso fecha o ciclo: a skill que
   ensina a usar a biblioteca passa a conhecer a nova fonte.

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

A biblioteca adiciona a coluna `termo_busca` automaticamente apenas se
o kwarg de busca tiver um destes nomes:
- HTTP: `pesquisa`, `termo`, `q`, `query`.
- Playwright: `assunto`, `pesquisa`, `termo`, `q`, `query`.

Escolha o nome que case com a convenção do site (ex: NYT usa `texto` no
factory, mas mapeia para `q` na API interna). Quando em dúvida, prefira
`pesquisa`.

### Encoding

Muitos sites governamentais brasileiros respondem em latin-1 / iso-8859-1.
Se o `_parse_page` retornar acentos quebrados, force:
```python
r0.encoding = r0.apparent_encoding
```
no `_find_n_pags`, ou abra o arquivo de sample com `encoding='latin-1'`
no `_parse_page`.

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
| `references/test-patterns.md` | Etapa 6 — padrão `responses` + samples HTML. |
| `references/factory-registration.md` | Etapa 5 — como editar `src/raspe/__init__.py`. |
| `references/raspe-skill-sync.md` | Etapa 7 — como atualizar a skill `raspe` do marketplace. |
| `references/checklist.md` | Final, antes de declarar a fonte pronta. |
