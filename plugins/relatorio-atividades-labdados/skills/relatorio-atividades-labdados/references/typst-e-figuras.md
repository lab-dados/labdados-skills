# Pipeline Typst, figuras e gotchas (alta diagramação)

## Fonte única no Quarto (arquitetura — leia primeiro)

O relatório é **fonte única**: um **único `.qmd`** gera os três formatos. **Nunca**
mantenha um `.typ` de conteúdo escrito à mão em paralelo (foi o que, no passado, saiu
de sincronia e fez perder/parafrasear parágrafos — erro grave, o usuário teve que revisar
tudo). Edite só o `.qmd`.

- **PDF (peça principal)** via `--to typst`, usando os **template-partials**
  `assets/typst-template.typ` + `assets/typst-show.typ`. É onde mora o acabamento FGV.
- **Word (editável)** via `--to docx` + `assets/_reference-fgv.docx`.
- **Markdown** via `--to gfm`.

O `.typ` que aparece em `relatorios/` é **gerado** (`keep-typ: true`) e está no
`.gitignore` — não versionar, não editar.

Frontmatter (ver `assets/relatorio_template.qmd`):

```yaml
toc-title: "Sumário"
filters: [labfoto.lua]
format:
  docx: { reference-doc: _reference-fgv.docx, toc: true, toc-depth: 3 }
  typst:
    template-partials: [typst-template.typ, typst-show.typ]
    toc: true
    toc-depth: 3
    keep-typ: true
  gfm: { toc: true }
```

### Os dois partials

- **`typst-template.typ`** define `#let article(...)` (a função do template) **e** todos
  os helpers de marca no escopo do arquivo: cores (navy/azul/coral/lime/cinza…),
  `losango-band`, `callout` (redefine o callout do Quarto → caixa de destaque com borda
  azul), `frente_chip`/`frentes_grid()`, `agenda(itens)`, `skill_card`/`skills_grid(cards,
  legenda)`. As show rules de heading, figura, tabela, quote, a capa navy e o cabeçalho/
  rodapé vivem dentro de `#let article`.
- **`typst-show.typ`** é o partial do pandoc-template: `#show: doc => article(title: [$title$],
  subtitle: [$subtitle$], toc: $toc$, toc_title: [$toc-title$], …, doc)`. É a cola entre o
  YAML do Quarto e a função `article`.

**Mapeamento de heading (importante):** o Quarto usa `shift-heading-level-by: -1`, então no
`.qmd` `##` vira **nível 1** no typst, `###` → 2, `####` → 3. As show rules são
`heading.where(level: 1/2/3)`.

## Como renderizar

```bash
# 1. dependências de figura (no .venv do projeto, via uv)
uv pip install pandas plotnine tabulate graphviz

# 2. gerar as figuras base (precisa do binário 'dot' no PATH)
python build_figs.py

# 3. um render por formato (o MESMO .qmd). O PDF EXIGE as fontes de marca:
TYPST_FONT_PATHS=<abs>/relatorios/fonts quarto render <nome>.qmd --to typst
quarto render <nome>.qmd --to docx
python scripts/fix_docx_tables.py <nome>.docx
quarto render <nome>.qmd --to gfm
```

Sem `TYPST_FONT_PATHS` apontando para `relatorios/fonts/`, o typst cai na fonte padrão
(perde a marca). Em PowerShell: `$env:TYPST_FONT_PATHS="<abs>\relatorios\fonts"; quarto render …`.

## Conteúdo condicional por formato (uma fonte, duas saídas)

O segredo de manter fonte única **com** alta diagramação é usar os recursos do Quarto para
emitir arte só no PDF sem duplicar o texto:

- **Bloco só-PDF:** raw ```` ```{=typst} ```` — passa typst cru direto (ignorado no docx/gfm).
  Usado para `#frentes_grid()`, `#agenda((...))`, `#skills_grid((...))`, `#pagebreak(weak: true)`.
- **`::: {.content-visible when-format="typst"}`** / **`when-format="docx"`** — mostra um bloco
  só num formato. Ex.: a imagem do prédio entra com `when-format="docx"` (no PDF ela vem pela
  arte de 2 colunas); pull quotes entram só no typst.
- **`::: {.content-hidden when-format="typst"}`** — esconde do PDF. Usado nas **tabelas**
  (agenda e skills): o Word/gfm recebem a tabela markdown; o PDF recebe a arte equivalente
  (`#agenda`/`#skills_grid`) num bloco `{=typst}` logo acima.
- **Filtro Lua `labfoto.lua`** para layouts que o markdown não expressa sem duplicar texto:
  - `.labfoto` (texto à esquerda + foto à direita, 2 colunas, legenda dentro da coluna da
    imagem) — só no typst; no docx devolve só os parágrafos.
  - `.parceiro` (rótulo "Em parceria com" + logo) vira `#block(sticky: true)` no typst, para o
    logo não ficar órfão no fim da página.

## Helpers de marca disponíveis (template-partial)

- `frentes_grid()` / `frente_chip(nome, cor, desc)` — **chips** das cinco frentes.
- `agenda(itens)` — **agenda visual**: cartão com selo de data + título + etiqueta de status
  (Realizado/Em curso/Previsto). Para eventos e cursos.
- `skills_grid(cards, legenda)` / `skill_card(nome, desc, cor)` — **caixinhas** de skills por
  categoria.
- `callout(...)` — redefine o `callout` do Quarto, então `::: {.callout-note appearance="simple"
  icon=false}` no `.qmd` vira a caixa de destaque azul **nos dois formatos**.
- `losango-band(...)` — faixa de losangos da capa. Pull quotes: escreva `> citação` dentro de
  `::: {.content-visible when-format="typst"}`; a show rule de `quote` faz a arte.

## Identidade visual (paleta e fontes)

- Paleta FGV/CEPI: navy `#13294b` (base/capa/bandas), azul `#1b3a6b`, azul claro `#4f7cc0`,
  **coral `#e0556a`**, **verde-limão `#a6ce39`**, cinzas. (Mais rico que só azul+amarelo.)
- Capa: fundo navy, logotipo textual "FGV DIREITO SP", **faixa de losangos**, título em
  caixa-alta, acento lime. Títulos com régua lime; cabeçalho/rodapé a partir da página 2.

### Tipografia da marca FGV

O manual da FGV usa **Frutiger** (primária, licenciada, raramente instalada) e **Arial**
(secundária).

- **PDF (Typst):** **Source Sans 3** (humanista livre, melhor aproximação do Frutiger),
  empacotada em `relatorios/fonts/` (Regular/SemiBold/Bold/Italic). No template,
  `font: ("Source Sans 3",)`, corpo **10,5pt**. Renderizar **sempre** com
  `TYPST_FONT_PATHS=relatorios/fonts`. Não usar Bahnschrift (condensada, fora da marca).
- **Word (docx):** `_reference-fgv.docx` ajustado para **Arial** (secundária oficial, presente
  em qualquer máquina), corpo 11pt.

## Paginação (estável — não repetir o que deu errado)

- **Use `sticky`, não pagebreak condicional.** As show rules de heading têm
  `block(..., sticky: true)`: o título "cola" no bloco seguinte e não fica órfão no rodapé.
  Estável.
- **NÃO** tente quebra de página condicional por posição:
  `context { if here().position().y > Xmm { pagebreak() } }` dispara o aviso **"layout did not
  converge within 5 attempts"** (instável, com hard e com weak pagebreak). Foi abandonado.
- **Quebras manuais (`#pagebreak(weak: true)`) só onde NÃO criam vão.** Quebra manual num
  ponto em que a página anterior não está cheia deixa um vão morto enorme no rodapé (o
  usuário reclama disso). Mantenha o mínimo: o Sumário em página própria e uma quebra antes de uma
  figura de tela cheia cuja página anterior já está preenchida (ex.: a de chips). Tirar as
  demais resolveu "páginas com muito espaço em branco".
- Encha páginas-âncora pela altura do conteúdo (ex.: altura do `frente_chip`), não por quebra.

## Figuras geradas por build_figs.py

1. **estrutura.png** — árvore de iniciativas (LabDados → frentes → projetos), Graphviz.
2. **timeline.png** — linha do tempo **vertical** (evita sobreposição de rótulos da horizontal).
3. **entregas.png** — mapa E1–E9 em caixas de fase.
4. **fluxo.png** — pipeline dos pacotes (fontes → coleta → estruturação com IA → entrega).

Outras figuras (não geradas pelo script):
- **Prints da plataforma / juscraper-app** (Playwright MCP: navigate + take_screenshot;
  recortar a barra de rolagem com PIL). No typst, a show rule `show image` põe moldura
  (stroke + clip) quando o caminho contém `servico-`/`juscraper-app`/`escritorio`.
- **Gráficos de pesquisa** do repo `lab-dados/ccd-saude-data` (baixar PNG via `gh api`).
- **Fotos de eventos** (acervo do lab), em `fig/`.

## Gotchas aprendidos (não repetir os erros)

- **`.columns`/`.column` do Quarto NÃO faz colunas lado a lado no typst** — ele **empilha**
  (testado e confirmado). Para texto+foto lado a lado, use o filtro `labfoto.lua`. Já
  `layout-ncol=2` (ex.: `::: {#fig-evento layout-ncol=2}`) **produz** uma grade typst — bom
  para duas fotos com uma legenda só.
- **`show image: it => …` usa `it.source`** (typst 0.14.2) para ler o caminho da imagem.
  Para foto cobrindo uma caixa: `box(clip: true, image(..., fit: "cover"))`.
- **`block(sticky: true)`** é a forma estável de manter um bloco com o próximo (títulos,
  logos de parceiro). `breakable: false` para caixas que não devem partir entre páginas.
- **Verbatim do Word revisado:** extraia o texto aceitando revisões — manter `w:ins`,
  descartar `w:del`/`w:delText`, e **descer recursivamente em `w:sdt`** (content controls;
  iterar só filhos diretos perde parágrafos aninhados). Não reescrever/parafrasear.
- **Windows / UTF-8:** rode `parse_whatsapp.py` com `PYTHONUTF8=1`.
- **python = .venv** do projeto (uv). Use `uv pip install`, não `pip`.
- **Graphviz `dot`** pode faltar. Em Windows, baixar a versão **portátil** e pôr o `bin` no
  PATH. `dot -V` escreve no stderr (não é erro). Rótulos HTML do Graphviz usam `<br/>`, não `\n`.
- **`height: 100%` em blocos Typst estica** o bloco até a altura da página — só usar de
  propósito (ex.: capa); em cartões deixar altura fixa em cm ou automática.
- **fix_docx_tables.py:** rode após **cada** render de docx (alinha a borda da última linha).
- **docx travado pelo Word:** se estiver aberto, o render dá "permission denied". Renderize
  para `*-novo.docx` (gitignorado) e avise para fechar o Word.
- **Travessões:** zero "—" no texto e nas legendas. Conferir com `grep -c "—"` no .qmd/.md.

## Logos de parceiros (fontes já testadas)

Logo real do parceiro na seção de cada projeto (mais institucional que arte de IA). No `.qmd`,
envolva em `::: {.parceiro}` (rótulo "Em parceria com" + imagem) — o `labfoto.lua` deixa o bloco
sticky no PDF.

- **InternetLab:** SVG inline no header de `internetlab.org.br` (Playwright `browser_evaluate`).
- **FAPESP (colorido):** `https://fapesp.br/assets/img/logo.png` (cuidado: `logo-simple2.png` é
  a versão **branca**, some no fundo branco).
- **Revista Direito GV:** `https://periodicos.fgv.br/public/journals/24/pageHeaderLogoImage_pt_BR.png`.
- **CEPI e CAJU:** URLs públicas não encontradas (404); pedir os arquivos ao usuário.

Fetch de sites que bloqueiam (403): `Invoke-WebRequest -UserAgent "<UA de navegador>"`.
