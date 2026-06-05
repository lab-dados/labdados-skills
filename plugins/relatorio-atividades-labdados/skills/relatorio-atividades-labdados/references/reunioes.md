# Reuniões: atas no repo adm e gravações

> Adaptado de `plugins/scrum-master/.../meetings.md`. A novidade é que o repositório
> `adm` já guarda atas estruturadas em `reunioes/`, então essa é a primeira fonte.

## Onde procurar, nesta ordem

1. **Atas no repo `adm`**, pasta `reunioes/`. A skill `ata-reuniao` salva atas em
   `reunioes/AAAA-MM-DD-ata.md`. Leia todas, são a fonte mais limpa e direta de
   decisões e encaminhamentos ao longo da história.
   ```bash
   ls <caminho-do-adm>/reunioes/*.md
   ```
2. **Pasta `Reuniões/` ou `Meetings/` no Google Drive** (gravações e transcrições).
3. **Pasta local `meetings/`** dentro de algum repositório, se existir.

Se não houver nenhuma ata nem gravação, registre "Nenhuma reunião encontrada nesta
execução" e siga.

## Formatos

- **Atas em markdown** (`reunioes/*.md`): conteúdo direto e estruturado
  (participantes, decisões, encaminhamentos). **Priorize.**
- **Transcrições** (`.txt`, `.md`, `.vtt`, `.srt`, `.docx`): conteúdo utilizável.
- **Vídeos e áudios** (`.mp4`, `.m4a`, etc.): não transcreva você mesmo, procure a
  ata ou transcrição correspondente. Se houver só a gravação, registre que existe
  reunião sem ata e siga.

## Como usar no relatório macro

As atas dão a linha do tempo das decisões do laboratório. Para cada ata:

1. Identifique a data e os participantes.
2. Extraia as decisões e os encaminhamentos que viraram fato (eventos, parcerias,
   contratações, mudanças de rumo dos pilotos, datas de curso).
3. Ligue cada decisão ao bloco da issue #45 e à entrega (E1 a E9) correspondente.

Use a tag `[R]` para reunião ou ata. Exemplo:
`[R] Reunião de 19/05/2026: definida a divisão dos relatórios por frente`.

## Cuidados

- Atas podem ter conteúdo sensível (processo seletivo, remuneração). Trate de forma
  neutra e agregada, não reproduza nominalmente.
- Atas longas: leia em blocos e consolide.
