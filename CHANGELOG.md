# Changelog

Todas as mudanças notaveis deste marketplace serao documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/); versionamento
segue [Semantic Versioning](https://semver.org/).

## [1.9.0] — 2026-09-23

Adicionado:

- `juscraper` 1.3.0: alinha a skill ao juscraper v0.4.0 (PyPI, 2026-09-15). Entram o scraper do STF (`listar_decisoes` e `contar_decisoes`, com o extra `stf` para o cookie do AWS WAF e o teto de 10.000 registros por busca), TRF6 (`cpopg` via eproc/txtcaptcha), `download_pecas` em TRF1/TRF3/TRF5, `count_only=True` em `cjsg`/`cjpg` quando suportado e os metodos eSAJ de descoberta de filtros (`listar_classes`, `listar_assuntos`, `listar_orgaos`, `listar_varas`).
- `juscraper`: tag `[unreleased]` para o que so existe na `main` do juscraper (snapshot `5ebde28`), com instalacao via `git+https://github.com/jtrecenti/juscraper.git`: checkpoint e retomada (`checkpoint_dir`, `resume=True`) e coleta integral do STF acima de 10.000 registros.

Alterado:

- `juscraper`: atualiza a matriz para 25 estaduais + 4 TRFs + STF e revisa Datajud, JusBR, ComunicaCNJ e PDPJ com os filtros, validacoes e retornos da v0.4.0. As mencoes a "release com `0bc0de5`" viram `[v0.4.0+]`, e recursos da v0.4.0 sem tag (TRFs, PDPJ, `count_only`, `listar_*`, escopo de `RetryExhaustedError`, `pesquisa=""` no TJSP, autopreenchimento de datas parciais) ganham a tag.
- `juscraper`: registra que TRF6 exige `txtcaptcha` fora das dependencias base e que `df.to_parquet` passa a exigir `pyarrow` instalado a parte.

Corrigido:

- `juscraper`: os nomes singulares `classe`/`assunto`/`vara` (TJSP `cjpg`), `classe` (TJBA) e `assunto` (Datajud) passam a constar como da v0.4.0, nao da v0.3.0; TJGO, TJMG e TJRJ passam a constar como da 0.2.1 (da 0.3.0 e so o extra `[tjmg]`); a linha 1.1.0 de `versao.md` separa o que veio da 0.3.0 do que veio da `main`, e a 1.2.0, nunca publicada, foi fundida na 1.3.0.
- `juscraper`: `RetryExhaustedError` deixa de ser prometido para Datajud e JusBR, que devolvem `None` internamente; o PDPJ nao detecta token expirado em `auth()`; o dedup do auto-chunk do `cjpg` do TJSP e so por `id_processo`; sai o filtro `contratos` do TJPE, que a biblioteca nao aceita.
- `juscraper`: a `description` da skill cabe no limite de 1024 caracteres da especificacao de Agent Skills.
- `juscraper`: documenta o contrato de `paginas` da v0.4.0 (selecao vazia, zero, negativo e `range` descendente levantam `ValueError`; no Datajud, `range(3, 6)` devolve as paginas 3 a 5) e a validacao de entrada do `download_documents` do JusBR.
- `juscraper`: remove a coluna `_total_tokens` e a regra da "primeira coluna" da integracao com o dataframeit, que nao valem desde o dataframeit 0.6.0.
- `juscraper`: esclarece que `tjsp.cjpg(id_processo=...)` recebe o numero CNJ do processo, com ou sem mascara, e cobre busca de jurisprudencia de 1o grau por CNJ alem da busca textual. Isso evita confundir `id_processo` com ID interno do eSAJ ou sugerir `cpopg` quando a tarefa pede jurisprudencia ou decisoes.

## [1.8.0] — 2026-09-23

Corrigido:

- `dataframeit` — coloca a descricao longa do frontmatter entre aspas para que o parser YAML do Claude Code preserve `name` e `description`; antes, o `:` na prosa invalidava todo o frontmatter e impedia a descoberta da skill.
- A validacao do CI agora executa `claude plugin validate` em cada plugin e bloqueia frontmatter que o runtime descartaria, em vez de verificar apenas a existencia de `SKILL.md`.
- `dataframeit` — alinha a skill ao dataframeit 0.6.0 (PyPI): extras reais de instalacao (nao existem `[cohere]` nem `[mistral]`; Mistral e Cohere seguem suportados via LangChain com `langchain-mistralai`/`langchain-cohere` instalados a parte; `[search]` e so Tavily; Claude Code via `[claude-code]`); provider `'mistralai'` em vez de `'mistral'`; remove a tabela de "modelo padrao por provedor", que nao existe no codigo (o unico default e `gemini-3-flash-preview`, e `model=` e obrigatorio ao trocar de provider, inclusive em `claude_code`).
- `dataframeit` — documenta que a biblioteca injeta `temperature=0` e que modelos sem `temperature` (Claude Sonnet 5, Opus 4.7+, GPT-6 com raciocinio, o1/o3, Gemini 3.5 Flash-Lite e 3.6+) precisam de `model_kwargs={'temperature': None}`.
- `dataframeit` — o total de tokens e `_input_tokens + _output_tokens`: `_reasoning_tokens` ja esta contido na saida, e a formula anterior contava o raciocinio duas vezes.
- `dataframeit` — campos condicionais (`depends_on`/`condition`) so sao avaliados com `use_search=True, search_per_field=True` e sem `search_groups`; o Exemplo 2 usava `search_groups` sem `search_per_field=True`, o que levanta `ValueError`. `checkpoint_path` aceita `.csv`, `.xlsx` e `.parquet`.
- `dataframeit` — tabela de modelos atualizada para setembro/2026 (Gemini 3.x, GPT-6, Claude 5, Mistral Small 4/Large 3, Cohere Command A, Groq GPT-OSS), com os aposentados listados e datas de desligamento.

Adicionado:

- `dataframeit` — coluna `_search_credits`, chave `prompt_replace` e, marcadas `[unreleased]`, as mudancas da main 0.7.x (`depends_on` derivado de `condition`; receitas de Vertex AI, Bedrock e Azure OpenAI hospedados no Brasil).

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
