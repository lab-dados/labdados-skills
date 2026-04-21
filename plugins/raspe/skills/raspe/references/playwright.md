# Scrapers com Playwright — ANS, ANVISA, SaudeLegis

Tres fontes da biblioteca usam navegador real (Chromium via Playwright) em vez de `requests`: sites dinamicos com muito JavaScript (SaudeLegis) ou protecao Cloudflare (ANS, ANVISA). Este arquivo cobre setup e troubleshooting.

## Instalacao

```bash
pip install "raspe[browser] @ git+https://github.com/bdcdo/raspe.git"
python -m playwright install chromium
```

A primeira linha instala as dependencias Python (`playwright>=1.40.0`, `playwright-stealth>=1.0.6`). A segunda baixa o binario do Chromium (~300 MB) — roda uma unica vez por maquina.

**Sintoma de instalacao faltando**: ao chamar `raspe.ans()` (ou `anvisa`/`saudelegis`), sai `DriverNotInstalledError` com a mensagem exata de instalacao. Nao tente contornar — rode os dois comandos acima.

## Parametros do construtor

Todos os 3 scrapers aceitam os mesmos kwargs no construtor:

| Parametro | Tipo | Default | Uso |
|---|---|---|---|
| `headless` | `bool` | `True` | Se `False`, janela do Chromium aparece durante a coleta. Util para debug. |
| `debug` | `bool` | `True` | Se `True`, mantem arquivos intermediarios (HTML bruto de cada pagina) no disco apos a coleta. Util para inspecao e parse manual. |

```python
# Execucao normal (headless, rapida)
df = raspe.ans().raspar(termo="doenca rara")

# Modo visual para debug — voce ve o navegador
df = raspe.ans(headless=False).raspar(termo="doenca rara")

# Mantem HTMLs baixados para inspecao
df = raspe.anvisa(debug=True).raspar(termo="medicamento orfao")
```

## Cloudflare e `playwright-stealth`

**ANS e ANVISA** sao hospedados em `datalegis.net` atras de Cloudflare. Sem stealth, o navegador e bloqueado em segundos. A biblioteca aplica `playwright-stealth` automaticamente — voce nao configura nada.

Quando o bypass falha, o sintoma tipico e:

- `BrowserError: Timeout ao aguardar elemento` em volta do seletor de busca.
- Pagina inicial fica travada em "Checking your browser...".

Passos se isso acontecer:

1. Rode com `headless=False` e observe. Se estiver preso em challenge do Cloudflare, a instancia atual de Chromium foi identificada — geralmente resolve esperar alguns minutos e tentar de novo com uma nova sessao.
2. Se persistir, o usuario pode estar rodando de um IP bloqueado (VPNs e datacenters sao comumente bloqueados). Sugira executar localmente sem VPN.
3. Em ultimo caso, rode `debug=True, headless=False` para ver o HTML exato e considere abrir issue no repo com o comportamento observado.

**SaudeLegis nao tem Cloudflare**, so JavaScript para renderizar resultados. Menos fragil que ANS/ANVISA.

## Estrategias de paginacao

A biblioteca usa enum `PaginationStrategy`:

- `NUMBERED_LINKS` — clica em links numericos (usado por SaudeLegis).
- `SELECT_DROPDOWN` — seleciona pagina num `<select>` com `onchange` (usado por ANS e ANVISA via Datalegis).
- Outros (`NEXT_BUTTON`, `URL_PARAMS`) existem mas nao sao usados por nenhum scraper atual.

Voce nao interage com essas strategies diretamente — elas aparecem em logs de debug se algo der errado. Se voce ver "Combobox de paginacao nao encontrado", o layout do site mudou e a paginacao quebrou — reporte como issue, ja que a logica assume o HTML atual do Datalegis/SaudeLegis.

## Limites praticos

| Scraper | `_max_pages` | Observacao |
|---|---|---|
| `saudelegis` | 50 | Mais que suficiente para a maioria das buscas tematicas. |
| `ans` | 100 | Teto imposto pela logica de paginacao do Datalegis. |
| `anvisa` | 100 | Idem. |

Se uma busca tiver mais paginas que o limite, a coleta para no limite e emite warning. Para contornar, refine o `termo` (p. ex. adicione ano: `termo="dispositivo medico 2024"`).

## Tempo de execucao e custo

Playwright e **ordens de magnitude mais lento** que `requests`. Ordem de grandeza:

- HTTP (Folha/Presidencia): 2-5s por pagina.
- Playwright (ANS/ANVISA): 15-30s por pagina (Cloudflare + render + SELECT + wait).

Para `ans`/`anvisa` com 100 paginas: planeje ~30-60 minutos de coleta. Avise o usuario. Para iteracoes de desenvolvimento, **sempre comece com `paginas=range(1, 3)`**.

## Debugging

Quando uma coleta Playwright falha:

1. **Rode com `headless=False`**: abra o navegador visualmente.
2. **`debug=True`** (default): deixa os HTMLs em `/tmp/ans_*.html` (ou equivalente) apos a coleta. Abra no navegador local para ver o que foi capturado.
3. **Logs**: a biblioteca usa `logging` padrao. Ative com:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```
4. **Minimal repro**: tente com `termo="teste"` e `paginas=range(1, 2)`. Se falhar na pagina 1, o problema e o acesso/busca, nao paginacao.

## Quando Playwright nao e a resposta certa

Se o usuario pede "quero coletar da Presidencia", nao force Playwright — a Presidencia usa `requests` (fonte HTTP) e funciona em 1/10 do tempo. O mapa correto de fonte ↔ tecnologia esta em `references/fontes.md`. Playwright so aparece quando a fonte **exige** JavaScript ou tem Cloudflare.
