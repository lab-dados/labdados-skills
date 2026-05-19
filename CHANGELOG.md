# Changelog

Todas as mudanças notaveis deste marketplace serao documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/); versionamento
segue [Semantic Versioning](https://semver.org/).

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
