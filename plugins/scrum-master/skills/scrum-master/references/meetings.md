# Reuniões gravadas e transcrições

Hoje **não há** reuniões registradas — o projeto ainda está montando esse fluxo. Mas a skill deve detectar automaticamente quando aparecerem, para não exigir reconfiguração no futuro.

## Onde procurar

Nesta ordem de prioridade:

1. **Pasta local `meetings/`** dentro do repositório. Se existir, liste todos os arquivos cujo mtime caia na janela de 7 dias.
2. **Pasta `Reuniões/` ou `Meetings/` no Google Drive** (dentro da folder ID principal).
3. **Pasta `.transcripts/`** ou padrão similar local.

Se nenhum desses existir, registre no relatório "Nenhuma reunião gravada nesta semana" e siga.

## Formatos esperados

- **Vídeos:** `.mp4`, `.mov`, `.webm`, `.mkv`. Não consiga transcrever você mesmo — procure transcrição correspondente.
- **Áudios:** `.m4a`, `.mp3`, `.wav`. Mesma lógica do vídeo.
- **Transcrições:** `.txt`, `.md`, `.vtt`, `.srt`, `.docx`. **Priorize essas** — são o conteúdo diretamente utilizável.

Se existir vídeo mas não transcrição, registre no relatório "Reunião gravada em YYYY-MM-DD sem transcrição — considere usar ferramenta de transcrição (ex.: Whisper) para próximas execuções."

## Como resumir uma transcrição

Para cada reunião encontrada:

1. Identifique participantes (quem falou) — útil para inferência de time.
2. Extraia 3 a 6 decisões/encaminhamentos concretos. Decisão = algo que vira ação ou mudança de rumo, não opinião solta.
3. Extraia dúvidas levantadas que ficaram em aberto.
4. Resuma em 2-3 bullets para a seção "O que foi feito" do relatório, com tag `[R]` e data.

Exemplo de bullet no relatório:
```
- [R] Reunião 16/04 (Julio, Maria, Pedro): decidido adiar raspagem do STF para M5; Pedro fica responsável pelo schema dos dados de jurimetria (cf. ata).
```

## Cuidados

- Reuniões podem ter conteúdo sensível (fofoca, discussão interna). Resuma em tom neutro; não reproduza literal.
- Se a transcrição for longa (>5000 palavras), leia em chunks e vá consolidando — não tente engolir de uma vez.
- Associe cada decisão a potenciais cards do Kanban, se fizer sentido. Decisões sem card podem virar sugestão na seção "Cards propostos".
