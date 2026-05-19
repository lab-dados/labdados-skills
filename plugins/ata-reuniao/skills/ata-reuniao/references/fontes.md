# Onde achar o conteúdo da reunião

Ordem de prioridade ao localizar o material de uma reunião.

## 1. Arquivo apontado pelo usuário

Se o usuário passou um caminho ou anexou um arquivo, **use-o**. Tipos:
- Áudio/vídeo: `.mp3`, `.m4a`, `.mp4`, `.mov`, `.wav`, `.webm`, `.mkv` → vai para transcrição (`references/transcricao.md`).
- Transcrição pronta: `.vtt`, `.srt`, `.txt`, `.md`, `.json` → pula a transcrição, vai direto para o resumo.

## 2. Google Drive — pasta de gravações

Pasta combinada pela equipe para áudios de reunião do Zoom (apontada pelo Julio no grupo):

`https://drive.google.com/drive/folders/1rNdsCAo8xYR2rHMH4k7h9CTD1b8etdGx`

Folder ID: `1rNdsCAo8xYR2rHMH4k7h9CTD1b8etdGx`

Use o MCP do Google Drive (prefixo `mcp__claude_ai_Google_Drive__` ou similar): liste arquivos por `modifiedTime`/nome, pegue a gravação cuja data bate com a reunião pedida. Se houver ambiguidade (vários áudios próximos), em modo interativo pergunte qual; em automático, pegue o mais recente compatível e registre a escolha no rodapé da ata.

A subpasta de gravações vive dentro da pasta-raiz do projeto LabDados no Drive (`1cGN2Mv2GLmmWEt-fFBrI5PKAhmgcgMWq`); se a folder ID acima não responder, procure por subpastas com nome "Reuniões"/"Gravações"/"Meetings" na raiz.

## 3. Transcrição já existente no Drive ou local

Antes de transcrever, verifique se já não existe transcrição para aquela reunião (mesma pasta do Drive, ou pasta local `reunioes/`/`.transcripts/`). Se existir, economize: use-a.

## 4. Histórico do WhatsApp (reconstrução, último recurso)

Sem gravação nem transcrição, dá para **reconstruir** uma ata a partir do que foi discutido/decidido no grupo de WhatsApp em torno da data da reunião. É menos confiável — marque a **Fonte** como "reconstruída do histórico do WhatsApp (sem gravação)" e seja conservador: registre só o que está evidenciado nas mensagens, não preencha lacunas com suposição.

Para extrair o WhatsApp, use o parser da skill `scrum-master`:
```bash
python <skills>/scrum-master/scripts/parse_whatsapp.py "<zip do WhatsApp>" --since-days N
```
(no Windows, defina `PYTHONUTF8=1` e redirecione para arquivo para evitar erro de encoding do console).

## Casar gravação ↔ reunião

A data no nome do arquivo (`reunioes/AAAA-MM-DD-ata.md`) é a data em que a **reunião aconteceu**. Ao pegar uma gravação, confirme pela data de modificação/criação e pelo conteúdo (primeiros minutos costumam ter "reunião de equipe", "entrevista", nomes). Não confie só no nome do arquivo do Zoom.
