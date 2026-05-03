# TTS — escolhas, troubleshooting

## Provedores na ordem de preferência

| Provedor | Custo | Qualidade PT-BR | Latência | Quando usar |
|----------|-------|-----------------|----------|-------------|
| ElevenLabs | $5+/mês plano básico | Excelente, voz muito natural | ~3s/200 chars | Vídeo final pra cliente/produção |
| OpenAI TTS | $0.015/1k chars | Boa, voz decente | ~2s/200 chars | Compromisso custo/qualidade |
| edge-tts | Grátis | Razoável (voz neural Microsoft) | ~1s/200 chars | Iterações, drafts, sem chave de API |

A skill tenta os três em ordem (ElevenLabs → OpenAI → edge-tts) automaticamente, parando no primeiro que tem chave configurada.

## Vozes recomendadas (PT-BR)

### edge-tts
- `pt-BR-FranciscaNeural` — feminina, neutra (default)
- `pt-BR-AntonioNeural` — masculina, mais formal
- `pt-BR-ThalitaNeural` — feminina, mais jovem/casual

Liste todas as vozes:
```bash
edge-tts --list-voices | grep pt-BR
```

### OpenAI
- Vozes: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`, `ash`, `ballad`, `coral`, `sage`, `verse`
- **Modelo padrão da skill é `gpt-4o-mini-tts`** (qualidade superior ao `tts-1-hd` legado). Para usar outro modelo, set `OPENAI_TTS_MODEL` no env.
- Para PT-BR, `nova` e `onyx` foram as que soaram mais naturais em produção. `nova` (feminina, neutra) é segura. `onyx` (masculina grave) tem mais autoridade pra material institucional.
- **CRÍTICO para PT-BR**: use `OPENAI_TTS_INSTRUCTIONS` para forçar sotaque brasileiro. Sem isso, mesmo com texto em PT, o modelo às vezes lê com sotaque de Portugal ou mistura inglês. Exemplo:
  ```
  OPENAI_TTS_INSTRUCTIONS="Fale com sotaque brasileiro nativo (português do Brasil, não de Portugal). Tom natural, calmo, didático. Pronuncie todas as palavras em português, mesmo termos como 'data', 'workshop' ou nomes técnicos."
  ```
  As `instructions` só funcionam com modelos `gpt-4o*-tts`, não com `tts-1`/`tts-1-hd`.

### ElevenLabs
- Vozes multilingual da própria plataforma. Use o ID dela.
- Para PT-BR, vozes multilingual v2 funcionam bem.

## Override de voz

```bash
python generate_tts.py script.json out_dir/ --provider edge --voice pt-BR-AntonioNeural
```

## Problemas comuns

### "edge-tts não está instalado"
```bash
pip install --break-system-packages edge-tts
```

### Áudio sai mudo/cortado no início
Bug conhecido do edge-tts em algumas versões: adicione um espaço no começo do `narration` ("  Texto..."). Ou prefira OpenAI/ElevenLabs.

### Áudio com pronúncia estranha de números/siglas
TTS lê "API" como "ah-pi-eye". Para forçar pronúncia em PT-BR, escreva por extenso: "A-P-I" ou "ei-pi-ai" (fonético).

### Velocidade da fala
- **edge-tts**: passe `rate` na narration via SSML (avançado, geralmente desnecessário).
- **OpenAI**: tem param `speed` (0.25 a 4.0).
- **ElevenLabs**: ajuste `stability` e `similarity_boost`.

Para a primeira versão, **NÃO** mexa nisso. Voz padrão é boa o suficiente.

## Idiomas além de PT-BR

```bash
python generate_tts.py script.json out_dir/ --lang en
```

Suporta `pt-BR` (default) e `en`. Para outros, force a voz manualmente:
```bash
python generate_tts.py script.json out_dir/ --provider edge --voice es-ES-ElviraNeural
```

## Validar áudio antes do merge

```bash
ls -la out_dir/scene_*.mp3
ffprobe -v error -show_entries format=duration out_dir/scene_000.mp3
```

Se algum arquivo está com 0 bytes ou duração 0, refaça aquele cena (provavelmente o provider falhou silenciosamente).

## Custos esperados (ElevenLabs / OpenAI)

Vídeo de 90s ≈ 230 palavras ≈ 1400 caracteres:
- ElevenLabs: ~$0.04
- OpenAI: ~$0.02

Roda quantas vezes quiser na iteração; o custo é desprezível.
