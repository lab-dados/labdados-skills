---
name: juscraper-builder-captcha
description: >
  Gera scrapers Python (baseados em requests) para tribunais brasileiros
  cuja página de consulta apresenta captcha, seguindo a arquitetura do
  pacote juscraper. Use quando o usuário pedir para criar um scraper
  para um tribunal que usa captcha (imagem com texto, reCAPTCHA,
  hCaptcha, Cloudflare Turnstile, etc.) ou quando, durante a análise
  inicial, for detectado captcha na página de consulta. Sempre tenta
  primeiro construir o scraper SEM preencher o captcha — muitos
  tribunais exibem o widget mas não validam o token no backend. Se o
  captcha for realmente obrigatório e for text-based (imagem com
  texto), usa o pacote `txtcaptcha` (mesmo autor do juscraper) para
  resolvê-lo de forma unificada. Se for reCAPTCHA v2/v3, hCaptcha,
  Turnstile ou qualquer captcha interativo, desiste e avisa o usuário.
  Requer o Playwright MCP para engenharia reversa. Para tribunais sem
  nenhum captcha visível, prefira a skill `juscraper-builder`.
---

# Juscraper Builder (Captcha)

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
há alternativa.

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
   foi executado.

4. **Aprender com os existentes**: Antes de gerar qualquer código
   novo, **sempre** leia pelo menos dois scrapers existentes para
   entender os padrões atuais:
   ```bash
   # Listar tribunais existentes
   ls src/juscraper/courts/
   # Ler um scraper de referência (ex: TJRS por ser compacto)
   cat src/juscraper/courts/tjrs/client.py
   # Ler outro para comparar padrões
   cat src/juscraper/courts/tjdft/client.py
   ```
   Também leia `src/juscraper/utils/params.py` para entender a
   normalização de parâmetros.

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

4. **Se houver captcha**: esta skill existe justamente para esse
   caso. Siga o fluxo abaixo, em ordem, sem pular etapas.

   **4.a — Classifique o captcha**. Identifique com precisão o tipo
   antes de qualquer outra coisa:
   - **text-based**: `<img>` com uma palavra/letras distorcidas que o
     usuário precisa digitar em um `<input>`. Costuma vir de um
     endpoint tipo `captcha.png`, `gerarImagem`, `imagemCaptcha`,
     etc.
   - **interativo**: reCAPTCHA v2 ("I'm not a robot"), reCAPTCHA v3
     (invisível, baseado em score), hCaptcha, Cloudflare Turnstile,
     FriendlyCaptcha, Arkose/FunCaptcha. Detectáveis por scripts de
     `google.com/recaptcha`, `hcaptcha.com`, `challenges.cloudflare
     .com`, ou divs `.g-recaptcha` / `.h-captcha` / `.cf-turnstile`.

   **4.b — SEMPRE tente primeiro SEM resolver o captcha**. Muitos
   tribunais brasileiros exibem o widget mas não validam o token no
   backend, ou só validam em algumas rotas. Antes de invocar
   `txtcaptcha` ou desistir, faça o experimento:

   1. Abra DevTools / use `browser_network_requests` para capturar
      a requisição real de busca (ver Etapa 2).
   2. Reproduza a requisição com `curl` ou `requests` em um script
      de scratch, **omitindo** o parâmetro do captcha (ou enviando
      string vazia, ou um valor qualquer):
      ```python
      import requests
      r = requests.post(URL, data={..., "captcha": ""})
      print(r.status_code, len(r.text))
      ```
   3. Compare com uma resposta conhecida (feita via navegador com
      captcha preenchido). Se o conteúdo de resultados vier igual
      (ou se o status for 200 com a mesma estrutura), **o captcha
      é decorativo** — prossiga com a Etapa 2 normalmente, tratando
      o tribunal como se não tivesse captcha. Documente no código
      um comentário curto: `# captcha exibido mas não validado no
      backend`.

   **4.c — Se o captcha for validado E for text-based**: use o
   pacote [`txtcaptcha`](https://github.com/jtrecenti/txtcaptcha)
   (mesmo autor do juscraper). Ele oferece uma interface unificada
   para decodificar captchas de imagem de tribunais brasileiros.

   1. Garanta a instalação:
      ```bash
      uv pip install txtcaptcha
      ```
   2. No scraper, baixe a imagem do captcha dentro da mesma
      `requests.Session()` usada para a busca (o cookie de sessão
      precisa bater com o token do captcha), resolva com
      `txtcaptcha`, e envie o resultado na requisição de busca:
      ```python
      from txtcaptcha import solve

      img_bytes = self.session.get(CAPTCHA_URL).content
      texto = solve(img_bytes)  # interface unificada
      payload["captcha"] = texto
      resp = self.session.post(SEARCH_URL, data=payload)
      ```
   3. Trate falhas: se a resposta indicar "captcha inválido",
      baixe um novo captcha e tente de novo (máx 3 tentativas
      por página). Conte falhas em `logger.warning`.
   4. Os testes de integração devem cobrir que a resolução
      funciona de ponta a ponta — se `txtcaptcha` errar demais
      em um tribunal específico, reporte ao usuário antes de
      finalizar.

   **4.d — Se o captcha for interativo (reCAPTCHA v2/v3,
   hCaptcha, Turnstile, etc.)**: desista. Não tente usar serviços
   pagos (2captcha/anti-captcha), não tente automatizar cliques no
   widget, não tente extrair tokens via Playwright no código final.
   Informe o usuário e encerre:
   ```
   ⚠️ O site do {TRIBUNAL} usa {tipo detectado}, que é um captcha
   interativo. Esta skill (juscraper-builder-captcha) só consegue
   lidar com captchas de imagem baseados em texto (via `txtcaptcha`).

   Não é possível automatizar a raspagem deste tribunal por aqui.
   Registrando a informação para referência futura.

   Tipo de captcha: {tipo}
   URL: {url}
   Observações: {notas adicionais}
   ```
   Crie `docs/captcha/{tribunal}_captcha.md` com essas informações
   e encerre o trabalho. **Não gere scraper parcial.**

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

**Antes de escrever código, leia os scrapers existentes** (Etapa 0
dos pré-requisitos) para alinhar com os padrões atuais. Sempre use
o código real como referência, não apenas as convenções documentadas.

Gere os seguintes arquivos:

#### 4.1 Client: `src/juscraper/courts/{tribunal}/client.py`

Estrutura obrigatória:

```python
"""Scraper para o {Nome Completo do Tribunal} ({SIGLA})."""

import logging
import time
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

from juscraper.utils.params import normalize_params

logger = logging.getLogger(__name__)


class {SIGLA}Scraper:
    """Scraper para o {Nome Completo do Tribunal}."""

    BASE_URL = "{url_base_do_tribunal}"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "juscraper/0.1 "
                "(https://github.com/jtrecenti/juscraper)"
            ),
        })

    # --- cjsg (jurisprudência) ---

    def cjsg(self, pesquisa, paginas=None, **kwargs):
        """Consulta de jurisprudência do {SIGLA}.

        Parameters
        ----------
        pesquisa : str
            Termo de busca.
        paginas : int, list, range, or None
            Páginas a baixar (1-based). None = todas.
        {param} : {tipo}
            {descrição de cada parâmetro extra do formulário}

        Returns
        -------
        pd.DataFrame
            Tabela com os resultados da consulta.
        """
        # Implementação: download para temp + parse
        ...

    def cjsg_download(self, pesquisa, paginas=None,
                      diretorio=".", **kwargs):
        """Baixa arquivos brutos da jurisprudência do {SIGLA}.

        Cria uma pasta dentro de `diretorio` com os arquivos
        HTML/JSON brutos de cada página.

        Returns
        -------
        Path
            Caminho da pasta com os arquivos baixados.
        """
        ...

    def cjsg_parse(self, diretorio):
        """Lê e processa arquivos brutos baixados por cjsg_download.

        Parameters
        ----------
        diretorio : str or Path
            Pasta contendo os arquivos brutos.

        Returns
        -------
        pd.DataFrame
            Tabela com os resultados processados.
        """
        ...
```

**Regras de geração obrigatórias**:

- `requests.Session()` para manter cookies entre requisições
- Mapear TODOS os campos do formulário como kwargs opcionais
- Nomes de parâmetros em português, seguindo convenções do CLAUDE.md:
  - `pesquisa` (nunca `query` ou `termo`)
  - `data_julgamento_inicio`, `data_julgamento_fim`
  - `data_publicacao_inicio`, `data_publicacao_fim`
  - `data_inicio`/`data_fim` como alias de `data_julgamento_*`
- Usar `normalize_params()` de `juscraper.utils.params` quando
  aplicável
- Paginação **1-based** conforme convenção do juscraper
- `tqdm` para barra de progresso no download
- `time.sleep(1)` mínimo entre requisições (pode ser mais se o
  site exigir)
- Retry com backoff em caso de erro HTTP (máx 3 tentativas)
- Retornar `pd.DataFrame` nas funções de consulta
- `logging` ao invés de `print`
- Tratar `paginas` como `int | list | range | None`
- Se `paginas` é `None`, buscar total e baixar tudo (com aviso ao
  usuário sobre o volume)
- Linhas de no máximo 120 caracteres
- Type hints nos parâmetros principais

#### 4.2 Init: `src/juscraper/courts/{tribunal}/__init__.py`

```python
"""Scraper para o {SIGLA}."""

from juscraper.courts.{tribunal}.client import {SIGLA}Scraper

__all__ = ["{SIGLA}Scraper"]
```

#### 4.3 Registrar na factory

Atualizar `src/juscraper/__init__.py` (ou o arquivo onde está a
função `scraper()`) para incluir o novo tribunal no mapeamento.
Ler o arquivo antes de editar para não quebrar nada.

#### 4.4 Testes: `tests/{tribunal}/test_{tribunal}_cjsg.py`

Testes de integração **reais** (sem mock). Cada teste deve fazer
requisições reais ao site do tribunal:

```python
"""Testes de integração para o scraper do {SIGLA}."""

import pytest
import juscraper as jus


@pytest.mark.integration
class TestCJSG{SIGLA}:
    """Testes para cjsg do {SIGLA}."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.scraper = jus.scraper("{tribunal}")

    def test_busca_simples(self):
        """Busca simples retorna resultados."""
        df = self.scraper.cjsg("direito", paginas=1)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_colunas_esperadas(self):
        """Resultado contém colunas mínimas esperadas."""
        df = self.scraper.cjsg("direito", paginas=1)
        # Ajustar conforme colunas reais do tribunal
        colunas_minimas = {"ementa"}  # ou {"decisao", "relator"}
        assert colunas_minimas.issubset(set(df.columns))

    def test_paginacao(self):
        """Paginação traz resultados de múltiplas páginas."""
        df = self.scraper.cjsg("dano moral", paginas=range(1, 3))
        # Com 2 páginas, deve ter mais resultados que 1 página
        df_p1 = self.scraper.cjsg("dano moral", paginas=1)
        assert len(df) > len(df_p1)

    def test_filtro_data(self):
        """Filtro de data funciona."""
        df = self.scraper.cjsg(
            "direito",
            data_inicio="2024-01-01",
            data_fim="2024-06-30",
            paginas=1,
        )
        assert len(df) > 0

    def test_download_e_parse(self, tmp_path):
        """Download + parse produz mesmo resultado que cjsg."""
        pasta = self.scraper.cjsg_download(
            "direito", paginas=1, diretorio=str(tmp_path)
        )
        df = self.scraper.cjsg_parse(pasta)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_paginas_int(self):
        """paginas=2 equivale a range(1, 3)."""
        df_int = self.scraper.cjsg("direito", paginas=2)
        df_range = self.scraper.cjsg("direito", paginas=range(1, 3))
        assert len(df_int) == len(df_range)
```

**Importante**: Criar `tests/{tribunal}/__init__.py` (arquivo vazio)
para que o pytest descubra os testes.

### Etapa 5 — Validação

1. Rodar os testes:
   ```bash
   pytest tests/{tribunal}/ -v -m integration --tb=short
   ```

2. Checklist de validação:
   - [ ] Todos os testes passam
   - [ ] DataFrame tem colunas coerentes com o site
   - [ ] Paginação funciona (página 2 ≠ página 1)
   - [ ] Filtros de data afetam os resultados
   - [ ] Download cria arquivos no diretório correto
   - [ ] Parse lê os arquivos corretamente
   - [ ] Sem warnings de deprecação do próprio código

3. Se testes falharem, diagnosticar:
   - **Status 403/429**: Adicionar mais delay, revisar User-Agent,
     verificar se precisa cookie de sessão
   - **HTML de erro no response**: Verificar se headers ou cookies
     estão corretos
   - **Dados vazios**: Verificar parsing (HTML vs JSON), seletores
     CSS, XPath, ou chaves JSON
   - **Timeout**: Aumentar timeout na Session, verificar se o site
     está fora do ar

4. Rodar linting:
   ```bash
   pylint src/juscraper/courts/{tribunal}/ --max-line-length=120
   flake8 src/juscraper/courts/{tribunal}/ --max-line-length=120
   mypy src/juscraper/courts/{tribunal}/
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

Nesse caso, informe o usuário:
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

- Incluir User-Agent identificável com link do projeto
- Respeitar `robots.txt` quando presente
- Manter delay mínimo de 1 segundo entre requisições
- Não fazer mais requisições do que o necessário para o teste
- Rodar testes de integração fora do horário comercial quando possível
- Não armazenar credenciais ou dados sensíveis no código
