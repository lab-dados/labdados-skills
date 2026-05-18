# Engenharia reversa com Playwright MCP

Protocolo objetivo de uso das ferramentas Playwright MCP disponíveis no
Claude Code para reconhecer um site e capturar requisições. Aplicar na
**Etapa 2** do workflow do `raspe-builder`.

## Tools disponíveis (prefixo `mcp__plugin_playwright_playwright__`)

| Tool | Uso na engenharia reversa |
|---|---|
| `browser_navigate(url)` | Abrir a página inicial da fonte |
| `browser_snapshot()` | Mapear formulário, campos, botões (árvore de acessibilidade) |
| `browser_take_screenshot()` | Documentação visual e diagnóstico |
| `browser_type(target, text)` | Preencher campo individual |
| `browser_fill_form(fields)` | Preencher formulário inteiro |
| `browser_click(target)` | Submeter busca / paginar |
| `browser_network_requests()` | Listar todas as requisições da sessão |
| `browser_evaluate(code)` | Injetar JS — `document.documentElement.outerHTML`, listeners customizados |
| `browser_console_messages()` | Ler erros do console (debug de SPAs) |
| `browser_select_option(target, value)` | Mudar dropdown |
| `browser_wait_for(condition)` | Aguardar elemento aparecer |

## Sequência canônica

```
1. browser_navigate(URL_da_busca)
2. browser_snapshot()                     # mapear campos
3. browser_fill_form([{name, value}, ...])  # ou browser_type para 1 campo
4. browser_click(botão de busca)
5. browser_wait_for(resultado visível)
6. browser_network_requests()             # captura página 1
7. browser_evaluate("document.documentElement.outerHTML")  # salvar sample
8. browser_click(link/botão da página 2)
9. browser_wait_for(novo resultado)
10. browser_network_requests()            # captura página 2
11. browser_evaluate("document.documentElement.outerHTML")  # sample p.2
```

## Identificação do endpoint principal

Filtre as requisições retornadas por `browser_network_requests` aplicando
em ordem:

1. **Descartar assets**: ignore URLs que terminem em `.css`, `.js`, `.png`,
   `.jpg`, `.svg`, `.woff`, `.ico`, `.gif`, `.webp`, `.mp4`. Também
   descartar domínios de analytics/CDN (google-analytics, googletagmanager,
   doubleclick, cdn.jsdelivr, hotjar, etc.).

2. **Priorizar por `resourceType`**:
   - `xhr` ou `fetch`: forte sinal de API JSON.
   - `document`: form server-rendered (HTML completo de volta).
   - `stylesheet`/`image`/`font`: ignorar.

3. **Priorizar por keywords no path**: `search`, `pesquisa`, `consulta`,
   `busca`, `resultado`, `api`, `query`, `find`.

4. **Verificar payload**: a requisição principal deve refletir os campos
   que você preencheu — termo de busca, datas, filtros. Se um POST tem
   `q=meio+ambiente` ou `pesquisa=meio+ambiente` no body, é candidato
   forte.

5. **Verificar a resposta** (via `headers.content-type`):
   - `application/json` → caminho HTTP/JSON.
   - `text/html` → caminho HTTP/HTML.
   - Outros → investigar manualmente.

## Como capturar o HTML completo (sample para teste)

Use `browser_evaluate` com:

```javascript
() => document.documentElement.outerHTML
```

Salve o retorno em
`/tmp/raspe-recon/<fonte>/page_01.html` para virar
`tests/<fonte>/samples/raspar/page_01.html` na Etapa 6.

Para a página 2, repita após paginar. Mesmo arquivo, sufixo
`page_02.html`.

## Análise de paginação

Compare a requisição da página 1 com a da página 2 e identifique o que
muda:

| Padrão observado | Configuração no scraper |
|---|---|
| `?page=1` → `?page=2` | `query_page_name='page'`, multiplier=1, increment=0 |
| `?pagina=1` → `?pagina=2` | `query_page_name='pagina'`, multiplier=1, increment=0 |
| `?page=0` → `?page=1` (0-based) | multiplier=1, increment=-1 |
| `?offset=0` → `?offset=10` | `query_page_name='offset'`, multiplier=10, increment=-10 |
| `?rg=0` → `?rg=25` | `query_page_name='rg'`, multiplier=25, increment=-25 (estilo Folha) |
| Token / cursor (`?cursor=abc123`) | Paginação não-numérica — não suportada pelo `BaseScraper` padrão. Considere implementar como single-page e iterar manualmente, ou consultar mantenedores |

## Quando admitir que o caminho HTTP não funciona

Sintomas que justificam migrar para Playwright no código final:

1. **Sem requisição XHR/fetch identificável após `browser_click`**.
   Tudo que aparece em `browser_network_requests` são assets — o conteúdo
   foi renderizado por JS no client a partir de dados embutidos. Caminho:
   Playwright + parse do HTML pós-render.

2. **Cloudflare ativo**. Faça uma requisição teste com `requests` e um
   User-Agent realista — se voltar a página "Just a moment..." ou status
   403 com challenge HTML, Playwright + stealth é necessário.

3. **API exige cookies dinâmicos**. Alguns sites exigem tokens
   criptografados gerados no client (`__cf_bm`, `XSRF-TOKEN` dinâmico)
   que não conseguem ser reproduzidos via `requests`.

4. **Site é uma SPA pura**. URL não muda ao buscar, todo conteúdo vem de
   um único bundle JS. Mesmo se houver API XHR, ela pode exigir headers
   complicados (Authorization Bearer JWT renovável). Avalie custo.

Antes de optar por Playwright, sempre tente primeiro:
- User-Agent de Firefox/Chrome recente.
- Headers completos copiados do DevTools (Accept, Accept-Language,
  Accept-Encoding, Sec-Fetch-*, Referer).
- Sessão `requests.Session()` herdando cookies de um GET inicial à página
  do formulário.

## Headers a copiar para o `_set_query_base`

Do DevTools / `browser_network_requests`, copie os headers da requisição
principal e replique no `__init__` da subclasse:

```python
self.session.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,en-US;q=0.7,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    # ... headers específicos do site
})
```

Headers `Cookie`, `Authorization`, `X-CSRF-Token` ou similares precisam de
tratamento dinâmico — não cole valores brutos.

## Diagnóstico rápido

Se a requisição falha quando rodada via `requests` mas funciona no browser:

1. Compare User-Agent. Sites brasileiros gov frequentemente bloqueiam UA
   `python-requests`.
2. Verifique se faltam cookies. Use `browser_evaluate("document.cookie")`
   e compare com `self.session.cookies`.
3. Veja se há header `Origin` ou `Referer` obrigatório.
4. Se POST: o `Content-Type` está correto? form-encoded vs JSON é um
   erro comum.
5. Olhe o status code real. 403 + página de challenge → Cloudflare.
   429 → rate limit (esperar). 200 + HTML diferente → talvez precise de
   cookie de sessão.
