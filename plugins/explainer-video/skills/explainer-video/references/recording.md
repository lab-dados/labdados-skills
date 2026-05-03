# Gravação com Playwright — opções avançadas

## Instalação (em background, antes da Etapa 5 do pipeline)

```bash
pip install --break-system-packages playwright
python -m playwright install chromium
```

## Configurações importantes do `script.json`

| Campo | Default | Quando mudar |
|-------|---------|--------------|
| `viewport` | `{width:1920, height:1080}` | Use `{width:1280, height:800}` para webapps mobile-first ou para arquivos menores. NUNCA use 4K. |
| `slow_mo_ms` | 300 | Diminua para 100 se as ações estão muito lentas. Aumente para 500 se ações estão rápidas demais. |
| `show_cursor` | true | Desligue só se a UI já tem destaque visual claro (botões grandes, hover states fortes). |
| `base_url` | "" | Setar se você está fazendo várias `goto` para a mesma origem. |

## Quando o seletor não funciona

Sintomas: timeout no `click`, `Element not found`, ou o vídeo grava mas o clique não acontece.

Estratégias (em ordem de preferência):

1. **Use seletor por texto visível** (mais robusto a refactor):
   ```json
   {"type": "click", "selector": "button:has-text('Login')"}
   ```

2. **Use `data-testid`** se o repo tiver:
   ```json
   {"type": "click", "selector": "[data-testid='login-btn']"}
   ```

3. **Aria/role**:
   ```json
   {"type": "click", "selector": "role=button[name='Login']"}
   ```

4. **CSS específico** (último recurso, frágil):
   ```json
   {"type": "click", "selector": ".header > nav > button.primary"}
   ```

## Antes de gravar: verificar seletores

Modifique o script.json temporariamente para só fazer goto + screenshot:

```json
{
  "scenes": [
    {"narration": "", "actions": [
      {"type": "goto", "url": "/"},
      {"type": "wait", "ms": 2000},
      {"type": "screenshot", "path": "/tmp/check-1.png"}
    ]}
  ]
}
```

Rode, abra o screenshot, confirme que a página carregou. Repita para cada estado importante.

## SPA routing / wait_for_load_state

Para SPAs (React/Vue/etc), `goto` com `wait_until="domcontentloaded"` retorna ANTES do JS terminar de hidratar. Se a página depende de fetch após carregar:

Adicione um `wait` explícito:
```json
{"type": "goto", "url": "/dashboard"},
{"type": "wait", "ms": 2500}
```

Ou aguarde um elemento aparecer (use `highlight` que só executa se o seletor existir):
```json
{"type": "wait", "ms": 1000},
{"type": "highlight", "selector": ".dashboard-loaded-marker"}
```

## Cursor visível

A skill já injeta um overlay CSS automaticamente (`show_cursor: true`). O cursor aparece como uma bolinha vermelha de 24px que segue o mouse. Se quiser desligar, set `show_cursor: false`.

## Vídeo final muito grande

Se o `.mp4` ficou >50MB para um vídeo de 1 minuto, provavelmente o `crf` (qualidade) está agressivo demais para upload. Em `record_demo.py` o crf default é 18 (qualidade alta). Você pode aumentar para 23-28 (mais leve, qualidade ainda razoável) editando a chamada do ffmpeg lá.

## Qualidade visual ruim no vídeo final

Se o usuário reclama de qualidade ("baixa resolução", "borrado", "sem nitidez") MESMO com viewport 1080p e CRF baixo, o gargalo é a captura. O `record_video_dir` do Playwright grava em **VP8 lossy** com bitrate fixo baixo, e isso não é configurável. Re-encode com CRF 16 não recupera qualidade que já foi perdida na fonte.

**Solução: use `record_demo_screencast.py`** em vez do `record_demo.py`. Ele captura via CDP `Page.startScreencast` (frames JPEG q95 direto do Chromium) e encoda H.264 a partir disso. Bitrate menor, qualidade visual MUITO melhor (texto/UI ficam nítidos).

### Pegadinhas do screencast e como evitar

- **Tela preta no início**: o screencast começa antes do primeiro `goto`, capturando a tela em branco do Chromium. Solução implementada: `goto about:blank` + warm-up de 300ms ANTES do `Page.startScreencast`, depois descarta os primeiros frames e reseta `t=0`.
- **Piscadas em transições**: chromium às vezes envia 2-3 frames quase simultâneos durante uma transição. Solução: deduplicar frames com gap < 30ms entre si.
- **Frames duplicados causam judder**: NÃO use `-vf fps=N` no ffmpeg (interpola de forma feia). Use `-vsync cfr -r N` que respeita as `duration` do concat demuxer.
- **Pouco movimento entre frames**: o screencast só envia frames quando há mudança visual significativa. Para um screencast de UI estática, isso significa ~3-10 fps efetivos. É OK — h264 lida bem com freezes longos.

## Bugs corrigidos no record_demo.py (lembrar de não regressar)

1. **`base_url` prependado em URLs absolutas**: `goto file:///...` virava `https://seu.app/file:///...`. O check é por `("http://", "https://", "file://", "data:", "about:")`.
2. **Scroll em `body`/`html` não scrollava a página**: `body.scrollBy()` não faz nada quando o scroll é da window. Solução: detectar se o elemento tem overflow real, senão usar `document.scrollingElement`.

## Dark mode automático

Para gravar o app no tema escuro sem clicar em nenhum toggle, set no script.json:

```json
{ "color_scheme": "dark" }
```

Isso passa `color_scheme="dark"` ao `browser.new_context(...)` do Playwright, que dispara `prefers-color-scheme: dark`. Apps que respeitam essa media query (a maioria das apps modernas — Tailwind `dark:`, MUI ThemeProvider, etc) entram em dark mode automaticamente sem stub de localStorage.

Se o app só lê o tema de localStorage, você precisará setar via `add_init_script` antes de qualquer goto.

## Local deploy: padrões

Se precisa subir um servidor local antes de gravar:

```bash
# Em background, com log redirecionado
nohup npm run dev > /tmp/dev-server.log 2>&1 &
SERVER_PID=$!

# Esperar a porta abrir (max 30s)
for i in {1..30}; do
  if curl -s http://localhost:3000 > /dev/null; then break; fi
  sleep 1
done

# ... rodar record_demo.py com base_url=http://localhost:3000 ...

# Depois matar
kill $SERVER_PID 2>/dev/null
```

Detecte a porta lendo `package.json` (`scripts.dev`), `Procfile`, ou perguntando ao usuário.

## Gravar páginas com auth/login

A skill NÃO faz login automático com credenciais reais (regra de segurança). Se a ferramenta exige login, o usuário deve criar uma conta de demo e prover as credenciais explicitamente, OU você grava só as partes públicas (landing, docs, signup flow).
