# Scrapers com Playwright — ANS, ANVISA, SaudeLegis

Três fontes da biblioteca usam navegador real (Chromium via Playwright) em vez de `requests`: sites dinâmicos com muito JavaScript (SaudeLegis) ou proteção Cloudflare (ANS, ANVISA). Este arquivo cobre setup e troubleshooting.

## Instalação

```bash
pip install "raspe[browser] @ git+https://github.com/bdcdo/raspe.git"
python -m playwright install chromium
```

A primeira linha instala as dependências Python (`playwright>=1.40.0`, `playwright-stealth>=1.0.6`). A segunda baixa o binário do Chromium (~300 MB) — roda uma única vez por máquina.

**Sintoma de instalação faltando**: ao chamar `raspe.ans()` (ou `anvisa`/`saudelegis`), sai `DriverNotInstalledError` com a mensagem exata de instalação. Não tente contornar — rode os dois comandos acima.

## Parâmetros do construtor

Todos os 3 scrapers aceitam os mesmos kwargs no construtor:

| Parâmetro | Tipo | Default | Uso |
|---|---|---|---|
| `headless` | `bool` | `True` | Se `False`, janela do Chromium aparece durante a coleta. Útil para debug. |
| `debug` | `bool` | `True` | Se `True`, mantém arquivos intermediários (HTML bruto de cada página) no disco após a coleta. Útil para inspeção e parse manual. |

```python
# Execução normal (headless, rápida)
df = raspe.ans().raspar(termo="doença rara")

# Modo visual para debug — você vê o navegador
df = raspe.ans(headless=False).raspar(termo="doença rara")

# Mantém HTMLs baixados para inspeção
df = raspe.anvisa(debug=True).raspar(termo="medicamento órfão")
```

## Cloudflare e `playwright-stealth`

**ANS e ANVISA** são hospedados em `datalegis.net` atrás de Cloudflare. Sem stealth, o navegador é bloqueado em segundos. A biblioteca aplica `playwright-stealth` automaticamente — você não configura nada.

Quando o bypass falha, o sintoma típico é:

- `BrowserError: Timeout ao aguardar elemento` em volta do seletor de busca.
- Página inicial fica travada em "Checking your browser...".

Passos se isso acontecer:

1. Rode com `headless=False` e observe. Se estiver preso em challenge do Cloudflare, a instância atual de Chromium foi identificada — geralmente resolve esperar alguns minutos e tentar de novo com uma nova sessão.
2. Se persistir, o usuário pode estar rodando de um IP bloqueado (VPNs e datacenters são comumente bloqueados). Sugira executar localmente sem VPN.
3. Em último caso, rode `debug=True, headless=False` para ver o HTML exato e considere abrir issue no repo com o comportamento observado.

**SaudeLegis não tem Cloudflare**, só JavaScript para renderizar resultados. Menos frágil que ANS/ANVISA.

## Estratégias de paginação

A biblioteca usa enum `PaginationStrategy`:

- `NUMBERED_LINKS` — clica em links numéricos (usado por SaudeLegis).
- `SELECT_DROPDOWN` — seleciona página num `<select>` com `onchange` (usado por ANS e ANVISA via Datalegis).
- Outros (`NEXT_BUTTON`, `URL_PARAMS`) existem mas não são usados por nenhum scraper atual.

Você não interage com essas strategies diretamente — elas aparecem em logs de debug se algo der errado. Se você ver "Combobox de paginação não encontrado", o layout do site mudou e a paginação quebrou — reporte como issue, já que a lógica assume o HTML atual do Datalegis/SaudeLegis.

## Limites práticos

| Scraper | `_max_pages` | Observação |
|---|---|---|
| `saudelegis` | 50 | Mais que suficiente para a maioria das buscas temáticas. |
| `ans` | 100 | Teto imposto pela lógica de paginação do Datalegis. |
| `anvisa` | 100 | Idem. |

Se uma busca tiver mais páginas que o limite, a coleta para no limite e emite warning. Para contornar, refine o `termo` (p. ex. adicione ano: `termo="dispositivo médico 2024"`).

## Tempo de execução e custo

Playwright é **ordens de magnitude mais lento** que `requests`. Ordem de grandeza:

- HTTP (Folha/Presidência): 2-5s por página.
- Playwright (ANS/ANVISA): 15-30s por página (Cloudflare + render + SELECT + wait).

Para `ans`/`anvisa` com 100 páginas: planeje ~30-60 minutos de coleta. Avise o usuário. Para iterações de desenvolvimento, **sempre comece com `paginas=range(1, 3)`**.

## Debugging

Quando uma coleta Playwright falha:

1. **Rode com `headless=False`**: abra o navegador visualmente.
2. **`debug=True`** (default): deixa os HTMLs em `/tmp/ans_*.html` (ou equivalente) após a coleta. Abra no navegador local para ver o que foi capturado.
3. **Logs**: a biblioteca usa `logging` padrão. Ative com:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```
4. **Minimal repro**: tente com `termo="teste"` e `paginas=range(1, 2)`. Se falhar na página 1, o problema é o acesso/busca, não paginação.

## Quando Playwright não é a resposta certa

Se o usuário pede "quero coletar da Presidência", não force Playwright — a Presidência usa `requests` (fonte HTTP) e funciona em 1/10 do tempo. O mapa correto de fonte ↔ tecnologia está em `references/fontes.md`. Playwright só aparece quando a fonte **exige** JavaScript ou tem Cloudflare.
