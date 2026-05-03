# Sincronização áudio/vídeo

## A lógica do merge_av.py

O `record_demo.py` produz:
- Um `gravacao.mp4` (vídeo único)
- Um `scene_timings` JSON com os tempos de início/fim de cada cena no vídeo

O `generate_tts.py` produz:
- Vários `scene_NNN.mp3`, um por cena
- Um `tts_manifest.json` com a duração real de cada áudio

O `merge_av.py` faz:

1. Para cada cena, corta o pedaço correspondente do vídeo (`-ss start -t duration`)
2. Compara `audio_duration` com `video_segment_duration`:
   - **audio > video**: estende o vídeo segurando o último frame (ffmpeg `tpad=stop_mode=clone`)
   - **audio ≤ video**: deixa como está, áudio termina antes do fim da cena (ok)
3. Faz mux: video_segment + audio_segment → segmento mp4 com áudio
4. Se a cena não tem narração: gera silêncio com `anullsrc`
5. Concatena todos os segmentos em um mp4 final

## Por que não acelerar o vídeo quando o áudio é mais curto?

Tentei. Fica esquisito. O olho percebe imediatamente que algo está acelerado, e isso parece amador. Melhor deixar respirar com silêncio breve.

## Por que não acelerar a narração quando o vídeo é mais curto?

Mesma razão. Narração acelerada parece TTS mal feito. Melhor estender o vídeo (freeze-frame).

## Speedup global no final (TTS lento)

O TTS da OpenAI (`gpt-4o-mini-tts`) tende a falar pausadamente. Se o usuário reclamar de "áudio lento" no produto final, **NÃO regere o áudio com `--speed`** (a voz fica artificial). Em vez disso, acelere o vídeo+áudio juntos com ffmpeg, preservando pitch:

```bash
ffmpeg -i final.mp4 \
  -filter_complex "[0:v]setpts=PTS/1.3[v];[0:a]atempo=1.3[a]" \
  -map "[v]" -map "[a]" \
  -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  final_speedup.mp4
```

`atempo=1.3` mantém o pitch (sem efeito chipmunk). Faixa segura: 1.1–1.5. Acima de 1.5 começa a soar acelerado.

## Sincronizar narração com transição visual (cena que clica)

Padrão ruim: a primeira ação da cena N é um `click` que muda a tela — a narração da cena N começa, mas o usuário já pulou pra outra tela. A narração descreve algo que ele não está mais vendo.

Padrão bom: dar um `wait` no início da cena ANTES do `click`, pra narração começar enquanto a tela anterior ainda está visível, e só depois fazer a transição. Ex.:

```json
{
  "narration": "Vamos olhar a seção de relatórios...",
  "actions": [
    {"type": "wait", "ms": 4000},
    {"type": "highlight", "selector": "...", "hold_ms": 1500},
    {"type": "click", "selector": "..."},
    {"type": "wait", "ms": 2000}
  ]
}
```

`4000ms` é geralmente suficiente — narração começa, anuncia o tópico, destaca o card, depois clica.

## Re-encode em cascata degrada qualidade

`merge_av.py` re-encoda 3 vezes (cut → extend → concat). Cada re-encode com CRF alto perde qualidade visivelmente. **Mantenha CRF 16 + preset slow** em todas as etapas intermediárias do merge — o vídeo final ainda fica com tamanho razoável (~5MB/100s @ 1080p) porque h264 comprime bem screencasts.

## Quando o resultado fica esquisito

### "O áudio termina muito antes do vídeo terminar"
Sua narração é curta demais para a cena. Adicione mais texto OU encurte os `wait` do vídeo.

### "O vídeo congela por muito tempo no fim de uma cena"
A narração é longa demais. Corte palavras OU divida em duas cenas.

### "As transições entre cenas estão abruptas"
Adicione `wait: 500` no fim das `actions` da cena. Isso dá um beat visual antes do corte.

### "O áudio dessincroniza progressivamente"
Bug. Os timings são absolutos por cena, então isso não deveria acontecer. Cheque se o `scene_timings.json` que você está passando bate com o vídeo (mesmo run).

## Adicionar música de fundo (opcional)

Se quiser música ambiente:

```bash
ffmpeg -i final.mp4 -i music.mp3 \
  -filter_complex "[1:a]volume=0.15[bg];[0:a][bg]amix=inputs=2:duration=first" \
  -c:v copy -c:a aac final_with_music.mp4
```

Volume 0.15 é bem baixo (15% do volume original) — isso é proposital para não competir com a narração.

Não inclua música por padrão. Pergunte ao usuário se ele quer.

## Custom thumbnails

Tirar um frame específico do vídeo como thumbnail:

```bash
ffmpeg -ss 8 -i final.mp4 -frames:v 1 -q:v 2 thumbnail.jpg
```

(Tira o frame aos 8 segundos.) Use `--thumbnail thumbnail.jpg` no upload do YouTube se quiser definir uma capa.
