---
name: relatorio-atividades
description: Gera relatórios de prestação de contas e atividades do LabDados para a diretoria e coordenações da FGV Direito SP. Produz os relatórios detalhados por frente (atividades e eventos do Luiz, SDK e ferramentas do Julio, juscraper e revisão de literatura do Bruno) e o resumo executivo macro que cobre toda a história do projeto, em PDF de alta diagramação e .docx editável a partir de uma fonte única Quarto (identidade FGV via template Typst + reference-doc) e com diagramas (frentes, mapa de entregas E1 a E9, linha do tempo). Consolida os repositórios da org lab-dados e os pessoais (juscraper, dataframeit, dataframeitgui, raspe), o GitHub Project, Google Drive e OneDrive, Slack, WhatsApp e as atas de reunião. Use sempre que pedirem "relatório de atividades", "prestação de contas", "relatório para a diretoria", "relatório para a coordenação", "relatório institucional do LabDados", "relatório macro/geral do LabDados", "relatório da issue #45", ou um panorama de tudo que o laboratório fez desde o início. Não confundir: scrum-master é o relatório semanal interno (últimos 7 dias, HTML/PDF para o líder); relatorio é genérico (uma análise vira docx); ata-reuniao é a ata de uma reunião específica.
---

# Relatório de atividades e prestação de contas (LabDados, diretoria)

Você gera os relatórios de prestação de contas do LabDados que atendem a issue
[lab-dados/adm#45](https://github.com/lab-dados/adm/issues/45). O público é a
**diretoria e as coordenações** da FGV Direito SP. O tom é macro e institucional:
mostra o progresso e a agenda do laboratório de forma ampla, cobrindo **toda a
história** do projeto, não a semana.

Esta skill combina duas coisas que já existem no marketplace: a coleta de várias
fontes (como a `scrum-master`) e o pipeline de docx com identidade FGV via Quarto
(como a `relatorio`). A diferença é a escala (história inteira), o público (diretoria),
o formato (Word com diagramas) e a estrutura (os blocos da issue #45).

## O que entregar

Você produz **um único relatório consolidado** que cobre toda a história do projeto e
atende a diretoria e as coordenações. É tudo num documento só (a antiga divisão em quatro
relatórios separados foi abandonada), em **dois formatos a partir de uma fonte única**:

**Fonte única no Quarto:** um **único `.qmd`** (`assets/relatorio_template.qmd`) gera os
dois formatos. **Nunca** mantenha um `.typ` de conteúdo escrito à mão em paralelo — isso já
saiu de sincronia e fez perder/parafrasear parágrafos (erro grave). Edite só o `.qmd`. Ver
`references/typst-e-figuras.md` para a arquitetura completa.

- **PDF de alta diagramação** (peça principal, "para o pessoal ver"), via `quarto render
  --to typst`, com os **template-partials** `assets/typst-template.typ` +
  `assets/typst-show.typ` (capa azul-marinho com faixa de losangos, títulos com régua lime,
  chips das frentes, agenda/skills em cartões, cabeçalho e rodapé). O PDF exige as fontes de
  marca: `TYPST_FONT_PATHS=<abs>/relatorios/fonts`. O `.typ` é gerado (`keep-typ`) e fica no
  `.gitignore`.
- **Word** (`.docx`) editável, via `quarto render --to docx` + `_reference-fgv.docx`. Menos
  sofisticado, serve para edição.

A arte de alta diagramação só-PDF (chips, agenda, skills, foto em 2 colunas, pull quotes,
molduras de print) sai do **mesmo** `.qmd` por conteúdo condicional: blocos
```` ```{=typst} ````, divs `.content-visible`/`.content-hidden when-format` e o filtro
`assets/labfoto.lua`. No Word esses trechos viram tabelas/imagens simples.

Os dois formatos usam **as mesmas figuras**, geradas por `scripts/build_figs.py` na pasta
`fig/` (3 diagramas: estrutura, linha do tempo vertical, mapa de entregas; 3 gráficos:
esforço por ferramenta, andamento do quadro, evolução do juscraper). Rode `build_figs.py`
antes de compilar. A paleta FGV/CEPI é azul-marinho com coral e verde-limão de apoio.
Sem fotos por enquanto (o laboratório ainda não tem banco de imagens).

**Estrutura: siga a proposta executiva** (`docs/proposta-executiva.docx`). Uma seção por
frente de atuação (mapeamento e captação de demandas, levantamento de literatura,
capacitação, escritório de apoio, projetos piloto, tecnologias e discussão metodológica)
e **uma subseção para cada projeto concreto** dentro da frente. Os projetos a cobrir, um
por subseção, incluem: diagnóstico institucional, dados abertos, scoping review de IA,
letramento em IA, curso de programação, oficina Atlas.ti, plataforma do escritório,
LabDados SDK, CCD Saúde, parceria InternetLab, juscraper, dataframeit, raspe, marketplace
de skills, app do CAJU, Revista Direito GV e eventos. Abra com resumo executivo, mapa das
frentes e linha do tempo; feche com mapa de entregas E1 a E9, indicadores e próximos
passos. Não force o encaixe: ajuste conforme o que as fontes mostrarem.

**Nome e título pelo conteúdo:** edite só `relatorios/AAAA-MM-relatorio-labdados.qmd`; ele
gera `.docx`, `.md`, `.typ` (gerado, gitignorado) e `.pdf`. Título "LabDados: Relatório de
Atividades e Prestação de Contas".

**Sem rótulos de fonte e sem números de issue no texto.** O relatório é institucional:
nada de tags como `[R]`, `[K]`, `[C]`, `[D]` nem de referências a issues (`#45`). Cite os
fatos de forma direta. Links para ferramentas, releases e documentos são bem-vindos;
números de issue não. Ver `references/estilo.md`.

A prestação de contas detalhada do CCD segue **à parte** (issue #43); aqui o CCD entra só
como uma subseção macro. Prestação de contas financeira e orçamento gerencial também
ficam de fora (viraram card próprio). Ver `references/issue-45.md`.

Salve tudo em `relatorios/` dentro do repo `lab-dados/adm`. Faça `git add` ao final,
mas **não commite** sozinho. Quem controla o histórico é o usuário.

## Leia primeiro

Antes de tudo, leia:

- `references/contexto-projetos.md` (**fatos de cada projeto, equipe, eventos, números**;
  é o que dá estofo ao texto e o que mais economiza tempo). Atualize-o a cada conversa.
- `references/typst-e-figuras.md` (pipeline do PDF em Typst, elementos visuais do template,
  tipos de figura e os **gotchas técnicos** já aprendidos).
- `references/melhores-praticas.md` (**como deixar o relatório bonito e institucional**:
  escrita, diagramação, uso de citações e recursos visuais; exemplos de referência).
- `references/estilo.md` (regras de escrita: linguagem simples, **sem travessões**).
- `references/projeto-labdados.md` (fases, entregas E1 a E9, frentes, papéis).
- `references/issue-45.md` (origem na issue #45; hoje é um relatório único).

## Passo a passo

### 1. Descoberta

- Localize o clone do repo `adm` (onde estão as atas em `reunioes/` e onde os
  relatórios vão para `relatorios/`). Se não achar, pergunte o caminho ao usuário.
- Garanta que a pasta `relatorios/` existe.
- Procure um zip do WhatsApp na pasta do projeto.
- Veja quais MCPs estão conectados (GitHub, Google Drive, Slack). Os que faltarem
  entram no modo degradado.

### 2. Coletar dados (toda a história, em paralelo)

Colete de cada fonte. Cada uma tem um reference com os comandos. Veja
`references/fontes-dados.md` para o índice. **Não há janela de 7 dias**, levante
totais, marcos e a evolução desde o início.

- **GitHub** (board, issues, repos da org e pessoais): `references/github.md`. Os
  repos pessoais são `jtrecenti/juscraper`, `bdcdo/dataframeit`, `bdcdo/dataframeitgui`,
  `bdcdo/raspe`.
- **Google Drive e OneDrive:** `references/google-drive.md`. Para o OneDrive, peça o
  link ou o acesso ao usuário se precisar.
- **Slack:** `references/slack.md`.
- **WhatsApp:** `references/whatsapp.md` (rode `parse_whatsapp.py` sem `--since-days`).
- **Reuniões e atas:** `references/reunioes.md` (leia `adm/reunioes/*.md`).

Se uma fonte estiver indisponível, **não pare**. Registre "fonte X indisponível nesta
execução" e siga. Parcial é melhor que nada.

### 3. Sintetizar

Organize o que coletou na estrutura da proposta executiva: uma seção por frente de
atuação e uma subseção por projeto concreto (ver `references/projeto-labdados.md` e a
lista de projetos no "O que entregar"). Para sua própria rastreabilidade, marque cada
item com a entrega E1 a E9 e a fonte; mas lembre que **essas marcas não vão para o texto
final** (sem tags, sem números de issue). Trate processo seletivo, remuneração e
avaliação de pessoas de forma neutra e agregada, nunca nominal.

### 4. Preparar a pasta de trabalho

Copie para `relatorios/` (ao lado do `.qmd`): `assets/relatorio_template.qmd`,
`assets/_reference-fgv.docx`, `assets/fgv_theme.py` e — para a fonte única com PDF de alta
diagramação — `assets/typst-template.typ`, `assets/typst-show.typ` e `assets/labfoto.lua`.
Garanta também as fontes de marca em `relatorios/fonts/` (Source Sans 3). Ver
`references/pipeline-docx.md` e `references/typst-e-figuras.md`.

### 5. Escrever o relatório

Escreva o relatório único a partir de `relatorio_template.qmd`. Siga `references/estilo.md`:
linguagem simples, natural, sem travessões, pouco jargão, todo número apontando para
tabela ou figura, e **sem tags de fonte nem números de issue no texto**. Uma seção por
frente, uma subseção por projeto.

### 6. Gerar os diagramas

Preencha os três diagramas com dados reais (ver `references/diagramas.md`): a estrutura de
frentes e projetos (grade de caixas em Graphviz), o mapa de entregas E1 a E9 (Graphviz) e
a linha do tempo vertical (plotnine). Se o Graphviz não estiver disponível, instale o
binário `dot` (em Windows dá para baixar uma versão portátil) ou use o fallback de tabelas
e registre isso no relatório.

### 7. Renderizar

Um render por formato, a partir do **mesmo** `.qmd`. O PDF exige as fontes de marca
(`TYPST_FONT_PATHS` apontando para `relatorios/fonts/`, senão cai na fonte padrão):

```bash
# PDF de alta diagramação (template-partials). Em PowerShell:
#   $env:TYPST_FONT_PATHS="<abs>\relatorios\fonts"; quarto render <nome>.qmd --to typst
TYPST_FONT_PATHS=<abs>/relatorios/fonts quarto render <nome>.qmd --to typst
quarto render <nome>.qmd --to docx
quarto render <nome>.qmd --to gfm
```

### 8. Pós-processar as tabelas (sempre)

Logo após cada render de docx:

```bash
python scripts/fix_docx_tables.py <nome>.docx
```

Refaça após cada novo render. Pular esse passo deixa as tabelas sem o fechamento da
última linha.

### 9. Git (sem commitar)

- `git add` dos `.qmd` e `.md` (e dos `.docx`, conforme a preferência do usuário).
- Garanta que `relatorios/.assets/`, ou as cópias de `_reference-fgv.docx` e
  `fgv_theme.py` ao lado dos `.qmd`, estejam no `.gitignore` se o usuário não quiser
  versioná-las.
- **Não commite.** Mostre o comando de commit sugerido.

### 10. Reportar ao usuário

Liste os caminhos de todos os relatórios gerados, um resumo de uma linha, o comando de
commit sugerido e quais fontes ficaram indisponíveis.

## Modo degradado

Se uma fonte falhar, siga com as outras e registre a ausência. Se **todas** falharem,
ainda assim gere o relatório, com uma seção "fontes indisponíveis" e a recomendação de
reconectar. Falhar em silêncio é pior que avisar.

## Arquivos de referência

- `references/estilo.md` — regras de escrita (sem travessões, linguagem simples).
- `references/projeto-labdados.md` — contexto do projeto (fases, E1 a E9, frentes).
- `references/issue-45.md` — estrutura dos blocos e divisão por frente.
- `references/fontes-dados.md` — índice das seis fontes e suas tags.
- `references/github.md` — board, issues e repositórios (história completa).
- `references/google-drive.md` — Google Drive e OneDrive.
- `references/slack.md` — canais e busca no Slack.
- `references/whatsapp.md` — export e parse do WhatsApp.
- `references/reunioes.md` — atas em `adm/reunioes/` e gravações.
- `references/diagramas.md` — diagramas estruturais (Graphviz + plotnine) e o fallback.
- `references/pipeline-docx.md` — render Quarto para docx e pós-processamento.
- `references/contexto-projetos.md` — **fatos de cada projeto, equipe, eventos, métricas**.
- `references/typst-e-figuras.md` — **PDF em Typst, elementos visuais e gotchas técnicos**.
- `references/melhores-praticas.md` — **boas práticas de relatório institucional**: escrita,
  diagramação, citações (sem pull quote pendurada) e recursos visuais; exemplos de referência.

## Aprendizados-chave desta família de relatórios

- **Fonte única no Quarto (regra dura):** um único `.qmd` gera Word **e** PDF. O PDF de alta
  diagramação sai por `--to typst` com os template-partials `typst-template.typ` +
  `typst-show.typ`, e a arte só-PDF por blocos ```` ```{=typst} ````, `.content-visible`/
  `.content-hidden when-format` e o filtro `labfoto.lua`. **Nunca** escreva um `.typ` de
  conteúdo à mão — ele sai de sincronia e leva a parafrasear/perder texto. Texto de Word
  revisado pelos autores: copiar **verbatim** (aceitando revisões: `w:ins` sim, `w:del` não,
  descer em `w:sdt`). Ver `typst-e-figuras.md`.
- **Paginação estável:** títulos com `sticky` (não órfãos); **não** usar pagebreak condicional
  por posição (`here().position().y` → "layout did not converge", instável); quebra manual só
  onde a página anterior já está cheia (senão vira vão morto). `.columns` do Quarto empilha no
  typst (não faz colunas) — para texto+foto lado a lado, usar `labfoto.lua`.
- **Dois formatos, um relatório só** (não vários — vários ficavam estranhos).
- **Sobre o laboratório, não sobre ferramentas.** Abrir com missão (do site oficial) e
  equipe; caixa de destaque "as ferramentas são meio". Não dar peso excessivo ao juscraper.
- **Cinco frentes** (estrutura do coordenador, jun/2026): **Institucional, Formação,
  Pesquisa, Escritório de apoio, Tecnologias/Comunicação**, cada uma com seus projetos. A
  Figura 1 (árvore de frentes→categorias→projetos) é o diagrama do coordenador; reproduza-o
  fiel (sem setas, conexões entrando pela esquerda). Não chamar os projetos de "piloto", e
  sim "projetos de pesquisa". As entregas E1–E9 só fazem sentido junto com o "mapa de
  entregas"; o coordenador removeu esse mapa, então **não** espalhe rótulos "EX" órfãos.
- **Citações:** ver `references/melhores-praticas.md`. **Não** feche seções com frase de
  efeito em caixa (fica cafona). Integre a frase forte à prosa; só destaque citação se for
  real (com fonte) ou trecho puxado do texto, bem posicionado.
- **Números no texto, não em página-placar.** O coordenador **vetou** a página/box "Em
  números". Distribua os indicadores na prosa, ligados ao significado.
- **Plataforma de serviços:** um tópico por serviço explicando como funciona (OCR,
  transcrição/diarização, estruturação com LLM, anonimização; + consultoria e chave de API).
  Estude o repo irmão `escritorio-servicos` (`backend/app/services_catalog.py`).
- **Visual:** prints da plataforma e do **juscraper-app** (`lab-dados.github.io/juscraper-app/`)
  via Playwright, gráficos do repo de pesquisa (CCD), fotos de eventos (do acervo do lab, não
  de terceiros), cartões de frentes/serviços/skills. Nunca o Kanban interno.
- **Equipe:** coordenador + membros em ordem alfabética + apoio, **sem papéis**.
- **Slack está ativo** (canais por frente, com mensagens de boas-vindas que descrevem cada
  uma): é fonte de primeira ordem. Ver `references/slack.md`.
