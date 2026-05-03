---
name: explainer-video
description: 'Cria vídeos explicativos curtos de plataformas web/ferramentas a partir de um repositório de código ou URL ao vivo. Use sempre que o usuário pedir "vídeo explicativo", "demo em vídeo", "screencast", "tutorial em vídeo", "vídeo de onboarding", "explainer video", "video walkthrough", "gravar uma demo", "fazer um vídeo da minha ferramenta", "mostrar como funciona em vídeo", ou quando mencionar gerar narração + gravação de tela de uma aplicação. Também use se o usuário descrever o objetivo (por exemplo "preciso mostrar essa feature pro time" ou "quero um vídeo curto pro README") mesmo sem dizer a palavra "vídeo". A skill analisa a documentação do repo, escreve roteiro narrado, grava o navegador via Playwright, gera áudio TTS sincronizado e oferece upload no YouTube como não-listado.'
---

# Explainer Video

Cria um vídeo explicativo curto (geralmente 30s–3min) de uma ferramenta web a partir de:
- Um **repositório de código** (caminho local ou URL git) cuja documentação descreve o que a ferramenta faz
- Uma **URL ao vivo** onde a ferramenta está deployada (preferencial), OU instruções de deploy local

O resultado é um arquivo `.mp4` com tela gravada + narração em PT-BR (ou outro idioma se pedido), pronto para upload no YouTube como vídeo não-listado.

## Princípio: reutilize, não reinvente

Esta skill é uma **orquestradora**. Toda a parte pesada é feita por bibliotecas estabelecidas:
- **Playwright** para gravar o navegador (suporte nativo a `record_video_dir`)
- **edge-tts / OpenAI TTS / ElevenLabs** para gerar áudio narrado
- **ffmpeg** para combinar áudio+vídeo e ajustar timing
- **google-api-python-client** para upload no YouTube

Você não precisa escrever lógica de vídeo do zero. Os scripts em `scripts/` são wrappers finos sobre essas ferramentas.

## Pipeline de 7 etapas

Siga as etapas em ordem. Cada etapa tem detalhes em `references/` — leia o arquivo correspondente quando entrar na etapa.

### Etapa 1: Entender a ferramenta

Identifique a fonte da informação:
- Se o usuário deu um caminho de repo local: leia `README.md`, `docs/`, `package.json`/`pyproject.toml`, e arquivos óbvios como `index.html` ou rotas principais
- Se deu uma URL git remota: clone para `/tmp/explainer-repo-<timestamp>` e analise lá
- Se deu só uma URL ao vivo sem repo: use `mcp__workspace__web_fetch` para extrair o conteúdo da página e qualquer link de docs

Use `scripts/analyze_repo.py <repo-path>` para gerar um sumário estruturado JSON com:
- Nome da ferramenta, propósito (1-2 frases)
- Lista de features principais detectadas
- Stack técnica
- URL ao vivo se mencionada

### Etapa 2: Determinar escopo

Pergunte ao usuário (ou deduza do prompt) **qual parte** explicar:
- Se ele NÃO especificou: explique a **ferramenta inteira** num overview de ~60-90 segundos
- Se especificou uma feature: foque nela com vídeo de ~30-60 segundos
- Se pediu vídeo longo: até 3 minutos

Não produza vídeos com mais de 3 minutos sem confirmação explícita — vídeos longos são chatos e geralmente sinal de que o roteiro está inflado.

### Etapa 3: Decidir como acessar a ferramenta

Ordem de preferência (do melhor pro pior):
1. **URL ao vivo** mencionada pelo usuário ou detectada no README — sempre prefira isto
2. **Deploy live conhecido** (Vercel/Netlify/etc) detectável via badges no README
3. **Deploy local**: só se não houver opção live. Use o comando do README (`npm run dev`, `streamlit run`, etc). Faça em background, espere a porta abrir, e use `http://localhost:<porta>`

Se for fazer deploy local, **avise o usuário antes** — pode demorar e exigir dependências.

### Etapa 4: Escrever o roteiro

Esta é a parte mais importante. Um roteiro ruim gera um vídeo ruim mesmo com gravação perfeita. Veja `references/script_writing.md` para o detalhamento.

Roteiro = arquivo JSON `script.json` com lista de "cenas". Cada cena:
```json
{
  "narration": "Texto curto que vai virar áudio (1-3 frases).",
  "actions": [
    {"type": "goto", "url": "https://app.com"},
    {"type": "click", "selector": "button#login"},
    {"type": "wait", "ms": 1500},
    {"type": "highlight", "selector": ".header"}
  ],
  "duration_hint_seconds": 8
}
```

Mostre o roteiro pro usuário em formato legível antes de gravar — ele provavelmente vai querer ajustar.

### Etapa 5: Gravar o vídeo

Há duas variantes do gravador. Escolha conforme a prioridade:

**`scripts/record_demo_screencast.py` (preferido — qualidade alta):** captura via CDP `Page.startScreencast` (frames JPEG q95 direto do Chromium) e encoda H.264 CRF 16. Bypassa o codec VP8 lossy. Use isto por padrão.

**`scripts/record_demo.py` (legado):** usa `record_video_dir` do Playwright (webm VP8), depois converte pra mp4. Mais rápido mas qualidade visual notavelmente inferior — texto/UI ficam borrados em 1080p. Só use se a cena tem MUITO movimento e o tamanho do arquivo importa mais que nitidez.

Os dois aceitam o mesmo `script.json` e produzem o mesmo formato de saída (mp4 + scene_timings JSON no stdout). Internamente:
- Lança Chromium com `viewport={width:1920, height:1080}` e `color_scheme` configurável (use `"dark"` pra gravar em dark mode automaticamente)
- Executa cada `action` da cena
- Salva o mp4 e imprime o JSON de timings pro merge_av usar

Veja `references/recording.md` para opções avançadas (cursor visível, slow-motion, dark mode, troubleshooting de qualidade).

### Etapa 6: Gerar áudio e sincronizar

Use `scripts/generate_tts.py <script.json> <output_dir>` para gerar um clipe de áudio por cena. Ele tenta na ordem: ElevenLabs → OpenAI → edge-tts (este último é gratuito e local, sempre disponível).

Depois `scripts/merge_av.py <video.mp4> <audio_dir> <script.json> <final.mp4>` para combinar. O merge:
- Mede a duração real de cada clipe de áudio
- Ajusta o timing do vídeo para encaixar (estende com freeze-frames se o áudio for mais longo, ou acelera levemente se o vídeo passou do tempo)
- Produz o mp4 final

Veja `references/audio.md` para troubleshooting de TTS e `references/sync.md` para a lógica de sincronização.

### Etapa 7: Salvar e oferecer upload

Sempre salve o `.mp4` final no diretório de outputs do usuário com nome descritivo (ex.: `myapp-demo-2026-05-03.mp4`).

Em seguida, **ofereça** upload no YouTube como não-listado. Não suba sem permissão explícita. Se o usuário aceitar:
- Use `scripts/upload_youtube.py --video <path> --title "..." --description "..." --privacy unlisted`
- Requer credenciais OAuth do YouTube Data API. Se não estiverem configuradas, explique como configurar (veja `references/youtube.md`) e ofereça salvar localmente para o usuário subir manualmente.

## Antes de começar: instalação de dependências

Sempre verifique e instale as dependências em uma única passada antes da Etapa 5:

```bash
pip install --break-system-packages playwright edge-tts google-api-python-client google-auth-oauthlib
python -m playwright install chromium
# ffmpeg geralmente já está instalado; se não: apt-get install -y ffmpeg
```

Faça isso em background enquanto escreve o roteiro (Etapa 4) para economizar tempo.

## Escolhas pequenas mas importantes

- **Resolução padrão**: 1920x1080. Não use 4K (arquivos enormes, demora pra subir).
- **Cursor**: o Playwright não mostra cursor por padrão. Para vídeos didáticos, injete um overlay CSS (ver `references/recording.md`).
- **Slow-motion**: use `slow_mo=300` (ms) no Playwright para que ações fiquem visíveis. Ações instantâneas confundem o espectador.
- **Idioma**: padrão PT-BR. Se o usuário pediu inglês ou se o repo claramente é internacional (README em inglês, sem texto em português), proponha inglês — mas pergunte antes de mudar.
- **Voice picking** (edge-tts): use `pt-BR-AntonioNeural` (masculino) ou `pt-BR-FranciscaNeural` (feminino). Padrão: Francisca.

## Erros comuns a evitar

- **Roteiro muito longo**: se você está escrevendo mais de ~150 palavras por minuto de vídeo, está enchendo linguiça. Corte.
- **Ações instantâneas demais**: sem `wait` ou `slow_mo`, o vídeo vira um borrão. Sempre dê 1-2s entre ações importantes.
- **Tentar "narrar" cada clique**: deixe o vídeo respirar. Algumas cenas podem ser puramente visuais com música ambiente (ou silêncio curto).
- **Subir no YouTube sem permissão**: NUNCA. Sempre confirme com o usuário antes do upload, mesmo sendo não-listado.
- **Esquecer de testar o roteiro antes**: antes de gravar o vídeo final, rode o Playwright em modo `headless=False` ou tire screenshots em pontos-chave para verificar que os seletores funcionam. Gravar 2 minutos para descobrir que um seletor estava errado é frustrante.

## Fluxo recomendado de comunicação com o usuário

1. Confirme: "Vou criar um vídeo explicativo de [ferramenta]. Vou explicar [escopo]. Tudo bem?"
2. Mostre o roteiro proposto antes de gravar
3. Avise quando começar a gravação ("Gravando agora, ~30s...")
4. Entregue o `.mp4` final e pergunte se quer subir no YouTube
5. Se subir: entregue o link não-listado

## Estrutura de arquivos da skill

```
explainer-video/
├── SKILL.md (este arquivo)
├── scripts/
│   ├── analyze_repo.py             # Sumariza repo → JSON
│   ├── record_demo.py              # Playwright record_video_dir → webm/mp4 (legado, lossy)
│   ├── record_demo_screencast.py   # Playwright CDP screencast → mp4 (preferido, alta qualidade)
│   ├── generate_tts.py             # TTS com fallback ElevenLabs/OpenAI/edge-tts
│   ├── merge_av.py                 # ffmpeg sync áudio+vídeo
│   └── upload_youtube.py           # YouTube Data API OAuth, unlisted
└── references/
    ├── script_writing.md     # Como escrever um bom roteiro
    ├── recording.md          # Opções avançadas do Playwright
    ├── audio.md              # Troubleshooting TTS, escolha de voz
    ├── sync.md               # Lógica de sincronização ffmpeg
    └── youtube.md            # Setup OAuth + upload
```
