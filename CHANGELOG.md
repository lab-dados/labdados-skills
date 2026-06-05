# Changelog

Todas as mudanças notaveis deste marketplace serao documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/); versionamento
segue [Semantic Versioning](https://semver.org/).

## [1.7.0] — 2026-06-05

Removido:

- As skills **institucionais** do LabDados foram separadas deste marketplace publico
  e migradas para o novo marketplace interno privado
  `lab-dados/labdados-skills-interno` (issue #18): `scrum-master`, `ata-reuniao`,
  `relatorio` e `relatorio-atividades-labdados`. Quem as instalava deve adicionar o
  marketplace interno (`/plugin marketplace add lab-dados/labdados-skills-interno`,
  acesso da org). O publico passa a conter so as skills de uso geral (juscraper,
  dataframeit, openalex, raspe, juscraper-builder, raspe-builder, explainer-video).
- `metadata.description` atualizada para refletir o escopo so-geral.

## [1.6.0] — 2026-05-30

Adicionado:

- `relatorio-atividades-labdados` — **skill INTERNA do LabDados** (assume as fontes,
  frentes e o pipeline FGV deste laboratorio; nao e replicavel direto em outros projetos,
  mas serve de guia). Gera os relatorios de prestacao de contas do LabDados que atendem a
  issue `lab-dados/adm#45`, voltados a diretoria e coordenacoes da FGV Direito SP. Produz
  os relatorios detalhados por frente (atividades/eventos; ferramentas/SDK; juscraper +
  revisao de literatura) e o resumo executivo macro que cobre toda a historia do projeto.
  A composicao da equipe muda com o tempo: quem esta em cada frente e dado de runtime, nao
  premissa fixa da skill. Consolida seis fontes (board
  e repos da org `lab-dados` + pessoais juscraper/dataframeit/dataframeitgui/raspe,
  Google Drive, OneDrive, Slack, WhatsApp e as atas em `adm/reunioes/`) sem janela de
  7 dias. **Fonte unica no Quarto:** um unico `.qmd` gera o PDF de alta diagramacao
  (peca principal, via `--to typst` com os template-partials `typst-template.typ` +
  `typst-show.typ` e as fontes de marca em `TYPST_FONT_PATHS`) e o `.docx` editavel
  (via `--to docx` + `_reference-fgv.docx`); a arte so-PDF (chips das frentes, agenda,
  skills, foto em 2 colunas, pull quotes) sai do mesmo arquivo por blocos `{=typst}`,
  divs `.content-visible`/`.content-hidden when-format` e o filtro `labfoto.lua`. Nunca
  manter um `.typ` de conteudo a mao em paralelo. Tres diagramas: estrutura por frentes
  e mapa de entregas E1-E9 (Graphviz pelo pacote python `graphviz`, sem browser) e linha
  do tempo (plotnine), com fallback de tabelas se o `dot` faltar. Estilo de escrita
  ajustado a pedido: linguagem simples e natural, sem travessoes, pouco jargao. Salva em
  `adm/relatorios/` e faz `git add` sem commitar. CCD (#43) e orcamento gerencial ficam
  fora do escopo.
- O plugin vendoriza copias de assets de outros plugins (isolamento de install):
  `_reference-fgv.docx`, `fgv_theme.py`, `fix_docx_tables.py` (de `relatorio`) e
  `parse_whatsapp.py` (de `scrum-master`), alem de references adaptadas de ambos. Cada
  copia leva um cabecalho `# copia de plugins/<x> — manter em sync`. Ao mudar o
  reference-doc da FGV ou o `fix_docx_tables.py`, propague manualmente aos tres plugins
  (`relatorio`, `scrum-master`, `relatorio-atividades-labdados`).

## [1.5.0] — 2026-05-29

Adicionado:

- `relatorio` — gera relatorios em `.docx` (e Markdown gfm) via Quarto com a
  identidade visual da FGV/LabDados. Inclui o template `relatorio_template.qmd`
  (header com `reference-doc`, formatos docx+gfm, exemplos de tabela e figura),
  o `_reference-fgv.docx` (tipografia Century Gothic, estilos de titulo,
  paragrafo e tabela), o `fgv_theme.py` (paleta FGV + tema plotnine sem titulo
  embutido) e o `fix_docx_tables.py`, que aplica o stroke da ultima linha das
  tabelas (o Pandoc deixa a ultima linha sem borda inferior) e zera o
  espacamento das celulas. Guia de escrita/formatacao em `references/estilo.md`.
  Pensado para substituir o fluxo de docx padrao por documentos consistentes.

## [1.4.0] — 2026-05-17

Adicionado:

- `ata-reuniao` — gera a ata de uma reuniao do LabDados a partir de gravacao/audio
  (Zoom, Google Drive) ou transcricao. Quando so ha audio, transcreve e diariza
  via `labdados-sdk` (WhisperX, modo nuvem do escritorio); resume num template
  markdown padrao (participantes, decisoes, encaminhamentos com responsavel/prazo,
  pendencias) e salva em `reunioes/AAAA-MM-DD-ata.md` no repo `lab-dados/adm`,
  deixando o `git add` feito sem commitar. Trata conteudo sensivel (processo
  seletivo, remuneracao) de forma neutra; modo degradado nao inventa atas.
## [1.4.0] — 2026-05-18

Adicionado:

- `raspe-builder` — gera scrapers Python para a biblioteca `raspe`
  (`bdcdo/raspe`) via engenharia reversa com Playwright MCP. Cobre os tres
  caminhos da arquitetura: HTTP/HTML (`BaseScraper` + `HTMLScraper`), HTTP/JSON
  (`BaseScraper`) e Playwright/stealth (`PlaywrightScraper`). Output completo:
  scraper em `src/raspe/scrapers/<fonte>.py`, registro de factory em
  `src/raspe/__init__.py`, testes de contrato offline em `tests/<fonte>/` com
  samples HTML versionados (padrao `responses` ja usado pelo repo), e sync
  automatico com a skill `raspe` deste marketplace (linha em tabelas + novo
  `references/<fonte>.md`). Workflow em 7 etapas: reconhecimento -> captura
  de requisicoes -> mapeamento -> geracao -> registro do factory ->
  testes offline -> validacao + documentacao. Inclui 6 references
  (arquitetura, protocolo Playwright MCP, padrao de testes, registro de
  factory, sync com a skill `raspe` e checklist final). Caminhos do repo
  raspe e do marketplace agora ficam como placeholders (`<RASPE_REPO>`,
  `<MARKETPLACE_ROOT>`) detectados em runtime, em vez de hardcoded.

Atualizado:

- `raspe` — adiciona referencia ao scraper `capes` (Portal de Periodicos
  da CAPES, ~29M itens via OpenAlex) com 15 colunas (incluindo Work ID
  do OpenAlex, DOI, acesso_aberto, producao_nacional, revisado_por_pares).
  Novo `references/capes.md` documenta sintaxe `all:contains(...)` e cross
  com `openalex-skill`. Matrizes em `references/fontes.md` atualizadas
  (12 fontes).
- `raspe` — converte SKILL.md e todos os 16 references para portugues
  com acentuacao plena (substitui `paginacao`/`publicacao`/`producao`
  pelas grafias corretas). Conteudo identico, apenas ortografia.

## [1.3.0] — 2026-05-03

Adicionado:

- `explainer-video` — gera videos explicativos curtos (30s–3min) de ferramentas
  web a partir de um repositorio ou URL ao vivo. Pipeline em 7 etapas: analise
  do repo, definicao de escopo, roteiro, gravacao via Playwright (CDP screencast
  H.264 ou `record_video_dir` legado), TTS (ElevenLabs/OpenAI/edge-tts com
  fallback), sincronizacao audio+video via ffmpeg e upload opcional no YouTube
  como nao-listado (OAuth Google Cloud).

## [1.2.0] — 2026-04-22

Adicionados dois novos plugins:

- `juscraper-builder` — gera scrapers Python para tribunais brasileiros
  seguindo a arquitetura do pacote juscraper. Inclui duas skills:
  `juscraper-builder` (paginas sem captcha) e `juscraper-builder-captcha`
  (paginas com captcha — text-based via `txtcaptcha`; desiste para
  reCAPTCHA/hCaptcha/Turnstile). Requer Playwright MCP.
- `scrum-master` — relatorio executivo semanal do LabDados, consolidando
  movimentacao do Kanban do GitHub, mensagens do WhatsApp, documentos do
  Google Drive e reunioes gravadas.

## [1.1.0] — 2026-04-20

### Adicionado

- `raspe` — raspagem de dados de fontes oficiais brasileiras (Presidencia,
  Camara, Senado, CNJ, IPEA, CFM, ANS, ANVISA, SaudeLegis) e imprensa (Folha
  de Sao Paulo, New York Times) via biblioteca raspe. Scrapers HTTP para 8
  fontes e Playwright (com stealth para Cloudflare) para ANS/ANVISA/SaudeLegis.
  References detalhados por fonte + guia de setup de navegador.

## [1.0.0] — 2026-04-20

Primeira publicacao do marketplace `labdados-skills` com tres plugins:

- `juscraper` — raspagem de dados judiciais brasileiros (22 tribunais estaduais
  + Datajud + JusBR) via biblioteca juscraper.
- `dataframeit` — enriquecimento de DataFrames com LLMs (extracao estruturada
  via Pydantic, classificacao, busca web, multi-provedor).
- `openalex` — busca e download de literatura academica via OpenAlex (460M+
  obras): API para descoberta + CLI para downloads em massa.
