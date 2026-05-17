---
name: ata-reuniao
description: Gera a ata de uma reunião do LabDados a partir de uma gravação/áudio (Zoom, Google Drive) ou transcrição, e salva em reunioes/AAAA-MM-DD-ata.md no repo lab-dados/adm. Use sempre que o usuário pedir "ata da reunião", "ata", "registrar a reunião", "documentar a reunião", "resumo da reunião de hoje/ontem", "transcrever e resumir a reunião", "gerar ata", ou apontar uma gravação/áudio de reunião para virar documento. Também use quando o usuário disser que uma reunião aconteceu e quer registrá-la, mesmo sem dizer a palavra "ata". Não confundir com a skill scrum-master (relatório semanal): esta skill é por reunião específica.
---

# Ata de Reunião (LabDados)

Você transforma uma reunião do **LabDados** (FGV Direito SP) numa ata curta e acionável, em português, salva no repositório `lab-dados/adm`. O valor de uma ata está no acionável: quem ler tem que saber **o que foi decidido** e **quem ficou de fazer o quê**.

Esta skill roda em dois contextos:
- **Interativo**: o usuário pede a ata e/ou aponta a gravação. Pode tirar dúvidas rápidas (ex.: qual reunião, se há mais de uma candidata).
- **Scheduled/automático**: não faça perguntas — use defaults, registre incertezas numa seção "A confirmar" da própria ata.

## O que entregar

Um único arquivo: **`reunioes/AAAA-MM-DD-ata.md`** no repo `lab-dados/adm`, gerado a partir de `assets/ata_template.md`. Data = dia em que a reunião **aconteceu** (não o de hoje). Mais de uma reunião no mesmo dia → sufixo: `2026-05-19-ata-equipe.md`, `2026-05-19-ata-internetlab.md`.

Ao final: `git add` do arquivo, **sem commitar** (o Julio controla o histórico — mesmo princípio da skill `scrum-master`). Mostre o comando de commit sugerido.

## Passo a passo

### 1. Descobrir o repositório adm

A skill opera sobre o repo `lab-dados/adm` (clone local — tipicamente o diretório de trabalho atual). Confirme que `reunioes/` existe (crie se faltar). Se não estiver num clone do `adm`, avise o usuário e pergunte o caminho (interativo) ou registre o problema e siga gerando o arquivo localmente (automático).

### 2. Localizar o conteúdo da reunião

Leia `references/fontes.md`. Ordem de busca:

1. **Caminho/áudio passado pelo usuário** (arquivo local `.mp3/.m4a/.mp4/.wav` ou transcrição `.vtt/.txt/.md`). Tem prioridade.
2. **Pasta de gravações no Google Drive** (ver `references/fontes.md` para a folder ID) — pegue a gravação mais recente compatível com a data da reunião.
3. **Transcrição já existente** (Drive ou local) — se houver, pule a transcrição.

Se não achar nada, **não invente a ata**: registre "sem gravação/transcrição localizada" e peça ao usuário o arquivo (interativo) ou aborte com aviso (automático).

### 3. Transcrever (quando só há áudio/gravação)

Leia `references/transcricao.md`. Use o **`labdados-sdk`** (modo nuvem do escritório, WhisperX com diarização). Resumo do fluxo:

```python
import labdados
labdados.transcricao(
    arquivos="<audio_da_reuniao>",
    api_key="<sk_lab_...>",        # do portal do escritório; ver references/transcricao.md
    modelo="whisperx",
    diarizacao=True,
    saida="<pasta_saida>/",
)
```

A chamada faz upload, polling e baixa um `.zip` com a transcrição diarizada. Extraia e use o texto. Se o serviço estiver fora do ar ou faltar API key, **não trave**: registre na ata "transcrição automática indisponível — ata gerada a partir de anotações/áudio parcial" e peça insumo ao usuário.

Se já houver transcrição pronta (passo 2.3), pule este passo.

### 4. Escrever a ata

Use `assets/ata_template.md` como estrutura fixa. Preencha:

- **Cabeçalho** — data, horário, tipo (equipe / InternetLab / etc.), fonte (gravação Zoom, transcrição WhisperX, anotações).
- **Participantes** — quem falou (da diarização) + ausentes conhecidos. Mapeie falantes a nomes reais quando possível (use `weekly-plan/.team-inferred.json` do scrum-master como apoio, se acessível).
- **Pauta tratada** — tópicos efetivamente discutidos (não a pauta planejada se divergiu).
- **Decisões** — o que foi decidido, frase afirmativa, sem rodeio. Decisão = mudança de rumo ou ação aprovada, não opinião solta.
- **Encaminhamentos** — tabela: ação · responsável · prazo. Todo encaminhamento precisa de dono. Sem dono → registre "(responsável a definir)".
- **Pendências / a confirmar** — o que ficou em aberto, dúvidas não resolvidas.
- **Próxima reunião** — data/horário se mencionado.

Princípios (herdados da `scrum-master`):
- **Específico, não genérico.** "Decidido baixar via extrator da Helena (#35)" > "discutiu-se a estratégia de dados".
- **Pessoa por nome.** "Bruno fica de sondar a Maritaca" não "alguém vai verificar".
- **Não invente.** Sem evidência na transcrição/insumo, não afirme.
- **Neutralidade.** Conteúdo sensível (remuneração, avaliação de pessoas, processo seletivo) entra de forma factual e enxuta; não reproduza fofoca nem fala literal delicada. Em dúvida, resuma em terceira pessoa ou omita.
- **Linkar o referenciável.** Issues `#N` → `https://github.com/lab-dados/adm/issues/N`; PRs, docs do Drive, repos viram link markdown. Decisões que viram tarefa: aponte a issue do `adm` quando existir.

### 5. Salvar e tratar git

- Salve em `reunioes/AAAA-MM-DD-ata.md` (sufixo se houver mais de uma no dia). Em modo interativo, se o arquivo já existe, pergunte sobrescrever ou versionar `-v2`; em automático, sobrescreva.
- `git add reunioes/<arquivo>.md` — **não commite**.
- Mostre `git status reunioes/` e sugira:
  ```
  git commit -m "ata reuniao AAAA-MM-DD"
  git push
  ```

### 6. Relatar ao usuário

Mensagem curta: caminho do arquivo, 1 frase de resumo (ex.: "Ata da reunião de 19/05: 4 decisões, 7 encaminhamentos, 2 pendências"), e o comando de commit sugerido. Se algum encaminhamento claramente merece virar issue no `adm` e ainda não existe, **sugira** (não crie) — a criação de cards segue o fluxo do Julio (cf. skill `scrum-master`).

## Relação com a issue #16

Esta skill + a pasta `reunioes/` substituem a issue [#16](https://github.com/lab-dados/adm/issues/16) ("Atas de reuniões"), que era uma pendência permanente. Registrar reunião agora é processo: rodar `/ata-reuniao`. Não recrie a issue #16.

## Arquivos de referência

- `assets/ata_template.md` — estrutura fixa da ata. Não altere as seções; preencha.
- `references/transcricao.md` — uso do `labdados-sdk`, API key, fallback.
- `references/fontes.md` — onde achar gravações (Drive, Zoom, local) e como casar com a data.

## Modo degradado

Se não houver gravação, transcrição nem anotações, **não produza uma ata fictícia**. Gere um arquivo mínimo com cabeçalho, "conteúdo não disponível nesta execução" e um pedido de insumo. Falhar avisando é melhor que inventar decisões que não foram tomadas — uma ata errada é pior que ata nenhuma.
