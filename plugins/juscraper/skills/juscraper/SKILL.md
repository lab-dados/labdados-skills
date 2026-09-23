---
name: juscraper
description: Raspar dados judiciais brasileiros com a biblioteca juscraper. Use para consultar processos por numero CNJ (cpopg/cposg), buscar jurisprudencia (cjsg/cjpg; STF via listar_decisoes), coletar comunicacoes/DJe digital ou consultas cross-tribunal via Datajud, JusBR, ComunicaCNJ e PDPJ. Cobre 25 tribunais estaduais (TJSP, TJRS, TJPR, TJDFT, TJBA, TJCE, TJES, TJMT, TJPA, TJPB, TJPE, TJPI, TJRN, TJRO, TJRR, TJSC, TJTO, TJAC, TJAL, TJAM, TJAP, TJMS, TJGO, TJMG, TJRJ), 4 tribunais regionais federais (TRF1, TRF3, TRF5, TRF6), o STF (Supremo Tribunal Federal, busca de jurisprudencia) e 4 agregadores nacionais (Datajud, JusBR, ComunicaCNJ, PDPJ). Use esta skill sempre que o usuario mencionar tribunal brasileiro, STF, numero CNJ, acordao, jurisprudencia, pesquisa empirica em direito, dados judiciais, consulta processual, decisoes judiciais, processos judiciais, eSAJ, PJe, poder judiciario, justica federal, comunicacoes processuais, DJe, intimacoes publicas, ou qualquer tarefa envolvendo coleta de dados de tribunais brasileiros — mesmo que nao mencione explicitamente "juscraper".
---

# JusScraper Skill

juscraper e uma biblioteca Python para raspagem de dados do poder judiciario brasileiro.
Cobre **25 tribunais estaduais**, **4 tribunais regionais federais** (TRF1, TRF3, TRF5, TRF6),
o **STF** (busca de jurisprudencia) e **4 agregadores nacionais** (Datajud, JusBR, ComunicaCNJ e PDPJ), permitindo buscar
jurisprudencia, consultar processos, baixar documentos e coletar comunicacoes do DJe.

> **Alinhada ao juscraper 0.4.0 (PyPI, 2026-09-15).** Recursos marcados `[v0.4.0+]` exigem
> `pip install -U 'juscraper>=0.4.0'`; `[v0.3.0+]` exigem `juscraper>=0.3.0`. Recursos marcados
> `[unreleased]` existem so na `main` do repositorio (snapshot `5ebde28`) e exigem
> `pip install "git+https://github.com/jtrecenti/juscraper.git"`. Ver `references/versao.md`
> para o changelog skill ↔ biblioteca.

- Repositorio: https://github.com/jtrecenti/juscraper
- Documentacao: https://jtrecenti.github.io/juscraper/

## Antes de comecar

Complete este checklist antes de qualquer chamada.

### 1. Instalacao

Verifique se `juscraper` esta instalado:
1. `pip show juscraper` ou `python -c "import juscraper; print(juscraper.__version__)"`
2. Python >= 3.11 obrigatorio.
3. Escolha o modo de instalacao conforme o que vai usar:

| Necessidade | Comando |
|---|---|
| Tudo que esta em PyPI, incluindo os recursos `[v0.4.0+]` (default, recomendado) | `pip install -U juscraper` ou `uv add juscraper` |
| TJMG e TRF6 (captcha automatico via `txtcaptcha`) | `pip install 'juscraper[tjmg]'` ou `pip install txtcaptcha` |
| STF `[v0.4.0+]` (cookie do AWS WAF via Playwright) | `pip install 'juscraper[stf]'` e depois `playwright install chromium` |
| Salvar em parquet (`df.to_parquet`) | `pip install pyarrow` (saiu das dependencias base na 0.4.0) |
| Recursos `[unreleased]` (so na `main`) | `pip install "git+https://github.com/jtrecenti/juscraper.git"` |

Para TRF6, o captcha textual exige `txtcaptcha`, que nao faz parte das dependencias base: sem ele, o `cpopg` do TRF6 levanta `ImportError`. O extra `tjmg` declara `txtcaptcha`, entao `pip install 'juscraper[tjmg]'` resolve os dois tribunais.

### 2. Autenticacao (condicional)

- **Todos os 25 tribunais estaduais e 4 TRFs federais:** Nenhuma autenticacao necessaria. TRF6 tem captcha textual validado server-side, mas o scraper resolve via `txtcaptcha` (instalar a parte, ver acima).
- **STF** `[v0.4.0+]`: sem login, mas o portal fica atras de um desafio JavaScript do AWS WAF. O scraper obtem o cookie `aws-waf-token` com Playwright na primeira busca (extra `stf` + `playwright install chromium`) ou usa um cookie ja obtido em `jus.scraper('stf', waf_token=...)`. Sem nenhum dos dois, a primeira busca levanta `ImportError`.
- **Datajud:** Tem API key publica embutida. Funciona sem configuracao.
- **ComunicaCNJ:** API publica, sem autenticacao.
- **JusBR:** Autenticacao obrigatoria (sem token, qualquer chamada falha com RuntimeError).
  Pergunte ao usuario:
  > Para usar o JusBR, voce precisa de um token JWT do gov.br.
  > Acesse https://www.jus.br, faca login via gov.br, e extraia o token
  > da aba Network do navegador (campo `access_token`).
  > Alternativamente, use `.auth_firefox()` se tiver sessao ativa no Firefox.
- **PDPJ:** Autenticacao obrigatoria via JWT do SSO do PJe.
  **Nao e o mesmo token do JusBR** (que usa o SSO do gov.br) — sao tokens
  distintos, embora o fluxo de captura via DevTools seja analogo. O token vem
  do portal PDPJ logado (DevTools > Network > header
  `Authorization: Bearer <token>`). Token invalido ou expirado vira
  `ValueError` ja em `pdpj.auth(token)`.

## Roteamento de decisao — o que usar?

### Passo 1: O que voce precisa?

| Preciso de... | Metodo | Scrapers disponiveis |
|---|---|---|
| Buscar jurisprudencia por palavra-chave (2o grau) | `cjsg(pesquisa)` | Todos os 25 tribunais estaduais |
| Buscar jurisprudencia (1o grau) por texto ou CNJ | `cjpg(pesquisa=...)` ou `cjpg(id_processo=cnj)` | TJSP, TJES, TJTO |
| Dados de processo por numero CNJ (1o grau, estadual) | `cpopg(id_cnj)` | TJSP (direto), JusBR (qualquer tribunal), PDPJ |
| Buscar jurisprudencia do STF (acordaos ou decisoes monocraticas) | `listar_decisoes(pesquisa)`; `contar_decisoes()` para total e facetas `[v0.4.0+]` | STF |
| Dados de processo por numero CNJ (1o grau, federal) | `cpopg(id_cnj)` `[v0.4.0+]` | TRF1, TRF3, TRF5, TRF6 |
| Dados de processo por numero CNJ (2o grau) | `cposg(id_cnj)` | TJSP |
| Listar/contar processos em qualquer tribunal | `listar_processos()` / `contar_processos()` `[v0.3.0]` | Datajud (40+ tribunais) |
| Baixar texto de documentos/pecas | `download_documents()`; `cpopg(download_pecas=True, diretorio=...)` `[v0.4.0+]` | JusBR; PDPJ `[v0.4.0+]`; TRF1/TRF3/TRF5 `[v0.4.0+]` |
| Coletar comunicacoes/intimacoes publicadas no DJe | `listar_comunicacoes()` | ComunicaCNJ `[v0.3.0+]` |
| Busca por nome de parte / OAB | `pesquisa()` | PDPJ `[v0.4.0+]` |

### Passo 2: Qual tribunal?

- Se o usuario especificou um **tribunal estadual** e ele esta entre os 25 (incluindo agora **TJGO**, **TJMG** e **TJRJ** `[v0.3.0+]`) → use o scraper direto.
- Se o usuario especificou um **tribunal federal** (TRF1, TRF3, TRF5 ou TRF6) `[v0.4.0+]` → use o scraper direto para `cpopg` ou o Datajud para metadados. Para baixar pecas junto com `cpopg`, isso existe em TRF1/TRF3/TRF5 (`download_pecas=True`, `diretorio=...`), nao em TRF6.
- Se o usuario pediu **jurisprudencia do STF** → use o scraper `stf` `[v0.4.0+]` (`listar_decisoes`/`contar_decisoes`). O Datajud tem o alias do STF, mas so devolve metadados de processos, sem ementa nem texto da decisao.
- Se o tribunal estadual nao tem scraper direto (TJMA, TJSE — captcha server-side) → use **Datajud** para metadados ou **JusBR**/**PDPJ** para consultar por CNJ e baixar documentos.
- Para jurisprudencia sem tribunal especificado → TJSP e o maior e mais completo.
- Para jurisprudencia de 1o grau → apenas TJSP, TJES ou TJTO suportam `cjpg`; no TJSP, `cjpg(id_processo=cnj)` busca pelo numero CNJ do processo, nao por ID interno do eSAJ.
- Para buscar por nome de parte ou numero OAB → use **PDPJ** `[v0.4.0+]` (`pdpj.pesquisa(nome_parte=..., oab_representante=...)`).
- Para acompanhar publicacoes no DJe sobre um tema → use **ComunicaCNJ** `[v0.3.0+]`.
- Consulte `references/tribunais.md` (tribunais) e `references/agregadores.md` (agregadores) para a matriz completa de capacidades e parametros.

## Vocabulario academico → endpoint juscraper

Artigos de pesquisa empirica em direito usam termos proprios dos tribunais
que nem sempre sao obvios ao implementar a coleta. Mapeamento:

| Termo no artigo | Endpoint juscraper | Observacao |
|---|---|---|
| "banco de sentencas" / "decisoes de 1o grau" | `cjpg` | Consulta de Julgados de Primeiro Grau — **publico**, nao precisa login institucional. Disponivel apenas em TJSP, TJES, TJTO |
| "jurisprudencia" / "acordaos" | `cjsg` | Consulta de Jurisprudencia (2a instancia). Disponivel em todos os 25 tribunais estaduais com scraper direto |
| "jurisprudencia do STF" / "acordaos do Supremo" / "decisoes monocraticas do STF" | `listar_decisoes` via STF `[v0.4.0+]` | `base='acordaos'` ou `base='decisoes'` (default) |
| "portal eletronico do tribunal" | `cjpg` ou `cjsg` (contexto) | Verifique a serie temporal e instancia descrita |
| "classificacao tematica do tribunal" / "assunto" | filtro de **assunto** (codigo DPJ/CNJ) | Preferir a busca textual para termos genericos — ver proxima secao |
| "autos completos" / "inteiro teor" | `cpopg`/`cposg` por CNJ | Requer lista previa de numeros de processos |
| "banco de dados do CNJ" / "DataJud" | `listar_processos` / `contar_processos` via Datajud | Metadados cross-tribunal |
| "comunicacoes processuais" / "DJe digital" / "intimacoes publicas" / "publicacoes do tribunal" | `listar_comunicacoes` via ComunicaCNJ `[v0.3.0+]` | Util para acompanhar publicacoes em um tema sem percorrer Diarios |
| "busca por advogado" / "OAB" / "nome de parte" | `pesquisa` via PDPJ | Substitui parcialmente buscas avancadas que JusBR nao oferece |

**Importante**: quando o artigo menciona "login institucional" ou "credenciais
do pesquisador", NAO assuma que os dados sao privados. Pesquisadores
acessam via login apenas por agilidade (paginacao rapida, menos CAPTCHA,
sessao persistente). Os **dados em si sao publicos** e replicaveis via
`cjpg`/`cjsg` — que e o que o juscraper usa.

## Recorte temporal — ate onde a base cobre

Bases de jurisprudencia tem datas de inicio de cobertura que variam
por tribunal, endpoint e periodo de digitalizacao. Antes de aceitar um
recorte temporal do usuario, **verifique se o tribunal cobre aquele
periodo**.

**Convencao das references**: cada tribunal pode ter uma reference
dedicada (`references/<tribunal>.md`) quando houver especificidades
validadas — cobertura temporal, parametros exclusivos, gotchas.
Consulte primeiro se existe reference para o tribunal do estudo.

**Tribunais ja documentados**:
- `references/tjsp.md` — cobertura temporal, endpoints exclusivos
  (`cjpg`), parametro `method` de `cpopg`/`cposg`, extras da `cjsg`.

**Tribunais ainda nao validados**: a maioria dos demais. Nao assuma
cobertura equivalente a TJSP — cada TJ tem calendario proprio de
migracao SAJ/eSAJ. Quando o usuario pedir recorte antigo em tribunal
sem reference especifica, **rode a primeira pagina do endpoint em
anos candidatos antes** de rodar a raspagem completa e registre o
que voce observou (se for util, proponha criar `references/<tribunal>.md`).

## Busca por assunto vs. busca textual — o default correto

Para temas genericos ("direito a saude", "responsabilidade civil",
"relacao de consumo", "dano moral"), **priorize busca por codigo de
assunto** sobre busca por palavra-chave textual. Justificativa:

1. **Precisao**: busca textual retorna decisoes que **mencionam** o termo,
   incluindo falsos positivos (cita em fundamentacao incidental, rejeita
   a tese, usa em obiter dictum, etc.). Busca por assunto retorna decisoes
   **classificadas** pelo proprio tribunal como tratando daquela materia
   — classificacao feita pelo magistrado/serventuario no momento da
   distribuicao do processo.
2. **Reprodutibilidade**: o mesmo codigo de assunto produz sempre os
   mesmos resultados. Termos textuais sao sensiveis a variacoes
   ortograficas, sinonimos e forma de redacao.
3. **Validade conceitual**: Ovadek et al. (2024) alertam que conceitos
   analiticos devem vir do pesquisador, nao do texto da decisao. Usar
   a classificacao oficial do tribunal como filtro primario aproxima o
   frame amostral do conceito de pesquisa — e um proxy mais robusto.

**Quando usar cada um**:

| Estrategia | Quando usar | Exemplo |
|---|---|---|
| Busca por assunto | Tema generico com codigo especifico disponivel | "direito a saude" → filtrar por codigo do assunto "Saude" (ex: 10070 no TJSP) |
| Busca textual | Conceito sem codigo de assunto; refinamento dentro de frame ja filtrado | termos tecnicos, nomes de leis, citacao de precedente |
| Combinacao (assunto + texto) | Recomendado — filtrar por assunto e refinar por texto | `assunto=<codigo> AND pesquisa="fornecimento medicamento"` |

**Onde encontrar codigos de assunto**: na familia eSAJ, prefira descobrir IDs pelo proprio scraper antes de adivinhar `[v0.4.0+]`: `listar_classes(grau="2")`, `listar_assuntos(grau="2")` e `listar_orgaos(grau="2")` listam filtros de `cjsg`; no TJSP, `listar_varas(grau="1")` lista varas de `cjpg`. Esses metodos retornam arvore com `id`, `nome`, `id_pai`, `nivel`, `selecionavel` e `caminho`. TJSP tambem tem lista extraida da pagina de busca avancada em `references/assuntos-tjsp.md` (json: `assuntos-tjsp.json`). Para outros tribunais, a **Tabela Processual Unificada do CNJ** (Resolucao 46/2007) define os codigos nacionais de assunto que a maioria dos tribunais adota. Conforme references especificas de outros tribunais forem validadas, mais arquivos `assuntos-<tribunal>.md` poderao aparecer aqui.

## LGPD e etica — coletar vs. publicar

Decisoes judiciais sao publicas no sentido da publicidade processual
(CF art. 5º LX; CPC art. 189), e coletar decisoes para fins de
pesquisa academica e permitido por LGPD art. 7º X. Mas **republicar o
texto integral** em dataset aberto e outra categoria — raramente
cumpre o principio da minimizacao (LGPD art. 6º III).

Regra operacional para pesquisa:

1. **Coletar e ok**: usar juscraper para baixar decisoes para analise
   local (codificacao, extracao de variaveis, avaliacao) esta coberto
   pela base legal academica.
2. **Nao republicar o texto integral por default**: o material
   publicavel de uma pesquisa deve conter apenas (a) numeros dos
   processos (identificadores unicos publicos — padrao CNJ Res. 65/2008),
   (b) campos codificados, (c) scripts, (d) artefatos de avaliacao. O
   texto bruto fica em parquet interno, nao distribuivel.
3. **Dados sensiveis exigem cuidado adicional**: Res. CNJ 331/2020;
   ECA art. 247 (criancas/adolescentes — dados sensiveis, removal
   total em trechos publicados); crimes contra dignidade sexual
   (vitimas anonimizadas); testemunhas nao identificadas.
4. **Publicacao de trechos e excecao justificada**: se o estudo exige
   citar trechos (ex: analise de retorica judicial), seguir um
   checklist de anonimizacao documentado no protocolo de pesquisa;
   nao liberar sem revisao manual.

Essas regras nao sao bloqueios — sao o default operacional. Pesquisa
cientifica em direito brasileiro segue essa logica: coleta ampla para
analise, publicacao minima para replicacao.

## Fundamentacao (ambito empirico)

As recomendacoes metodologicas desta skill — preferir busca por assunto
sobre textual, documentar string exata de busca, registrar data da
consulta, assumir vies de publicacao de bases publicas — seguem o
consenso da literatura de pesquisa empirica em direito:

- **Validade conceitual**: Ovadek et al. (2024). Conceitos analiticos
  vem do pesquisador, nao do texto — por isso filtrar por assunto
  aproxima o frame amostral do conceito.
- **Accountability e reprodutibilidade**: Verbruggen & Wijntjens
  (2025) audit. Coletas sem string exata + data + filtros nao sao
  replicaveis — 65% dos estudos holandeses omitiram a lista de casos.
- **Vies de publicacao**: Hall & Wright (2008, p. 103-104). Bases
  publicas contem fracao das decisoes proferidas; conclusoes se
  aplicam a decisoes **publicadas**, nao a todas as decisoes.

## Rate limiting

Os tribunais sao sites governamentais com infraestrutura limitada. Requisicoes
agressivas causam bloqueio de IP e prejudicam outros usuarios do sistema.
Por isso:

- Mantenha `sleep_time` >= 0.5 (o padrao). Se zero, o tribunal pode bloquear
  a sessao inteira e o usuario tera que esperar horas ou trocar de IP.
- `paginas=None` baixa todas as paginas — para buscas amplas como "dano moral"
  isso pode significar milhares de paginas. Sempre comece com um range pequeno
  (ex: `range(1, 4)`) e so amplie se o usuario pedir explicitamente.
- Antes de uma raspagem ampla em eSAJ/TJSP, use `count_only=True` `[v0.4.0+]` quando suportado (`cjsg` em TJAC/TJAL/TJAM/TJCE/TJMS/TJSP e `cjpg` em TJSP). Ele retorna um `int`, ignora `paginas` com warning e, com `auto_chunk=True`, soma resultados brutos por janela — pode divergir de `len(df)` por deduplicacao. No STF, o equivalente e `contar_decisoes()`.
- O juscraper avisa quando uma busca retorna muitos resultados. Mostre essa
  contagem ao usuario e peca confirmacao antes de prosseguir.

## Conceitos-chave

**Numero CNJ**: Formato NNNNNNN-DD.AAAA.J.TT.OOOO (ex: 1000149-71.2024.8.26.0346).
Aceito com ou sem separadores. Os digitos significam:
- NNNNNNN: numero sequencial
- DD: digito verificador
- AAAA: ano de ajuizamento
- J: segmento de justica (8 = Estadual)
- TT: tribunal (26 = SP, 21 = RS, 16 = PR, 07 = DFT)
- OOOO: origem/foro

Utilitarios para manipulacao: `from juscraper.utils.cnj import clean_cnj, split_cnj, format_cnj`
(detalhes em `references/api.md`).

**Paginacao 1-based**: `range(1, 4)` baixa paginas 1, 2, 3. `paginas=3` equivale a `range(1, 4)`.
`paginas=None` = todas (usar com cautela).

**Tipos de retorno**:
- `cpopg()`/`cposg()`: retorna `dict` com DataFrames (chaves: dados, partes, movimentacoes, etc.)
- `cjsg()`/`cjpg()`: retorna um unico `pandas.DataFrame`
- `listar_processos()`: retorna `pandas.DataFrame`
- `download_documents()`: retorna `pandas.DataFrame` com coluna `texto`

**Padrao download/parse**: todo metodo tem variantes `_download()` e `_parse()` para
controle granular sobre arquivos brutos. O metodo sem sufixo combina ambos.

## Quando usar scrapers diretos vs agregadores

| Criterio | Scrapers diretos (25 estaduais + 4 TRFs + STF) | Datajud | JusBR | ComunicaCNJ `[v0.3.0+]` | PDPJ |
|---|---|---|---|---|---|
| Jurisprudencia (`cjsg`) | Sim — principal uso; STF via `listar_decisoes` | Nao | Nao | Nao | Nao |
| Consulta por CNJ | TJSP (cpopg/cposg), TRF1/TRF3/TRF5/TRF6 (cpopg) | Sim (`listar_processos`) | Sim (`cpopg`) | Nao | Sim (`cpopg`) |
| Cross-tribunal | 1 tribunal por vez | Sim (detecta tribunal pelo CNJ) | Sim | Sim (filtro `siglaTribunal`) | Sim (filtro `tribunal`) |
| Documentos/pecas | TRF1/TRF3/TRF5 via `cpopg(download_pecas=True)` | Nao | Sim (texto) | Nao | Sim (texto e/ou binario) |
| Busca por nome de parte / OAB | Nao | Nao | Nao | Nao | Sim (`pesquisa`) |
| Comunicacoes / DJe | Nao | Nao | Nao | Sim (`listar_comunicacoes`) | Nao |
| Contagem rapida | eSAJ/TJSP (`count_only=True`) e STF (`contar_decisoes`) `[v0.4.0+]` | Sim (`contar_processos`) | Nao | Sim (campo `count`) | Sim (`contar`) |
| Autenticacao | Nenhuma (STF: cookie do WAF obtido via Playwright ou `waf_token`) | Nenhuma (key publica) | Obrigatoria (JWT gov.br) | Nenhuma | Obrigatoria (JWT PDPJ) |

Priorize sempre os scrapers diretos quando o tribunal estiver disponivel — eles fornecem
dados mais ricos (ementas completas, filtros especificos) do que os agregadores. Os
agregadores entram quando o tribunal nao tem scraper direto, ou quando o caso de uso e
especifico (busca por parte, comunicacoes, contagem pre-coleta).

Detalhes completos dos 4 agregadores em `references/agregadores.md`.

## Tratamento de erros

Se o scraper falhar (timeout, bloqueio, erro HTTP):

- Aumente `sleep_time` e tente novamente com menos paginas.
- Tribunais ficam mais lentos em horario comercial — sugira tentar em outro horario.
- Se persistir, o Datajud e uma alternativa mais estavel para metadados de processos.

**Excecoes a conhecer:**

- **`juscraper.core.exceptions.RetryExhaustedError`** `[v0.4.0+]`: levantada quando 403/429/5xx persistente esgota `max_retries`. Na 0.4.0 vale para o `cjsg` dos 25 tribunais estaduais (e o `cjpg` de TJES/TJTO), o `cpopg` de TRF1/TRF3/TRF5, o STF e os agregadores ComunicaCNJ, JusBR e Datajud, todos migrados para `HTTPScraper`. Substitui `requests.HTTPError` / `requests.RequestException` nesse cenario. Para codigo defensivo, capture ambas.
- **STF `ValueError`** `[v0.4.0+]`: pagina que comeca depois do registro 10.000 da busca falha antes de qualquer requisicao. Ver `references/tribunais.md` §STF.
- **`TypeError` por kwarg desconhecido** `[v0.3.0]`: todos os endpoints com schema pydantic wired (a maioria) rejeitam kwargs nao reconhecidos com mensagem amigavel e sugestao de typo via difflib (`(você quis dizer 'data_julgamento_inicio'?)`). Se aparecer, confira o nome canonico em `references/api.md` §"Aliases de parametros depreciados".
- **`juscraper.courts.tjsp.exceptions.QueryTooLongError`** `[v0.3.0]`: no TJSP `cjsg`/`cjpg`, `pesquisa` com mais de 120 caracteres levanta erro antes do HTTP (antes, o backend silenciosamente truncava). Priorize os termos mais discriminativos.
- **Datajud `ValueError`** `[v0.3.0]` **BREAKING**: chamar `listar_processos`/`contar_processos` sem `tribunal` nem `numero_processo`, ou com sigla nao mapeada, agora vira `ValueError` em vez de retornar DataFrame vazio.

## O que fazer com os dados

Pesquisa empirica em direito tipicamente envolve coleta → armazenamento → analise.
Apos a coleta:

- **Para explorar no chat:** `df.head()`, `df.describe()`, `df['coluna'].value_counts()`
- **Para salvar:** `df.to_csv('resultados.csv', index=False)` ou
  `df.to_parquet('resultados.parquet')` (parquet e melhor para DataFrames grandes). Desde a
  0.4.0 o juscraper nao instala `pyarrow`: rode `pip install pyarrow` antes do `to_parquet`.
- **Para combinar tribunais:** colete separadamente e concatene com `pd.concat([df1, df2])`
- **cpopg/cposg retornam dict:** itere com `for tabela, df in resultado.items():`

## Workflow tipico do agente

1. Leia este SKILL.md (feito).
2. Execute o checklist "Antes de comecar" (instalacao, autenticacao).
3. Identifique o que o usuario precisa (processo especifico vs busca de jurisprudencia).
4. Aplique o roteamento de decisao (qual scraper, qual metodo).
5. Leia `references/api.md` para assinaturas e parametros exatos.
6. Se incerto sobre qual tribunal usar ou seus parametros, leia `references/tribunais.md`.
7. Use paginacao explicita e respeite rate limiting.
8. Execute.

## Arquivos de referencia

Leia a referencia apropriada antes de gerar codigo:

- **`references/api.md`** — Referencia completa da API: factory function, construtores,
  assinaturas dos metodos principais com parametros, tipos de retorno, tabela de aliases
  depreciados, validacao `extra="forbid"`. Leia antes de qualquer tarefa.

- **`references/tribunais.md`** — Matriz de capacidades (25 estaduais + 4 TRFs + STF),
  parametros especificos de cada tribunal (cada um tem filtros proprios na cjsg),
  plataformas, e gotchas comuns. Leia quando precisar escolher entre tribunais ou entender
  seus parametros especificos. Inclui as secoes TJGO, TJMG, TJRJ, TRFs e STF.

- **`references/agregadores.md`** — Datajud, JusBR, ComunicaCNJ e PDPJ: construtores,
  metodos, autenticacao, gotchas. Leia quando o caso de uso for cross-tribunal,
  comunicacoes/DJe, contagem antes da coleta, ou download de pecas.

- **`references/tjsp.md`** — Especificidades do TJSP: endpoints exclusivos (`cjpg`),
  parametro `method` de `cpopg`/`cposg`, extras da `cjsg`, `pesquisa=""`,
  `QueryTooLongError`, `auto_chunk`, cobertura temporal validada.

- **`references/versao.md`** — Mapa skill ↔ versao do juscraper. Vocabulario das tags
  `[v0.3.0+]`, `[v0.3.0+, requer extra tjmg]`, `[v0.4.0+]` e `[unreleased]`, alem do procedimento
  para bumps futuros.

- **`references/assuntos-tjsp.md`** — Arvore oficial de assuntos (classificacao tematica)
  do TJSP, coletada diretamente do portal. Inclui metodologia de extracao, listagem completa
  de **DIREITO DA SAUDE** (util para replicacoes), ramos principais e instrucoes de uso em
  `cjpg`/`cjsg`. Leia **sempre que precisar filtrar por assunto/tema** em vez de por texto
  livre — especialmente em replicacao de pesquisa empirica.

- **`references/assuntos-tjsp.json`** — Dump JSON completo (~2.3 MB, 8886 nós) acompanhando
  o .md. Carregue programaticamente quando precisar buscar codigos de forma exploratoria.

## Integracao com outras skills

Esta skill entrega **dados brutos**. O fluxo tipico de pesquisa empirica
em direito combina:

| Etapa | Skill | Produto |
|---|---|---|
| Coleta de decisoes/processos | **juscraper-skill** (esta) | DataFrame/Parquet com texto de decisoes |
| Codificacao via LLM (campos estruturados) | **dataframeit-skill** | DataFrame com colunas extraidas + `_input_tokens`/`_output_tokens` |
| Revisao de literatura | **openalex-skill** | Lista de artigos relevantes |

Se o usuario vai codificar o que foi coletado via LLM, lembre-o da
**dataframeit-skill** e, se ele tem plano Claude Code, do modo
`provider='claude_code'` (consome tokens do plano, nao API).

### Gotcha: nome da coluna de texto ao chamar dataframeit

O `cjpg` do TJSP traz o texto da sentenca na coluna **`decisao`**; o `cjsg`
costuma trazer o texto em `ementa`, e o nome varia por tribunal. Com
`text_column=None` (default), o `dataframeit` procura, nesta ordem, `texto`,
`text`, `decisao`, `content` e `content_text`; se nenhuma existir e o
DataFrame tiver uma unica coluna, usa essa coluna; senao levanta `ValueError`.
Em DataFrames do juscraper, `decisao` e inferida quando existe, mas um
DataFrame so com `ementa` falha, e uma coluna `texto` teria precedencia.
Prefira passar a coluna explicitamente:

```python
resultado = dataframeit(
    df_cjsg, ModeloPydantic, "Analise: {texto}",
    text_column="ementa",   # ou "decisao" no cjpg; confira df.columns antes
)
```

O total de tokens por linha e `_input_tokens + _output_tokens`; a coluna
`_total_tokens` nao existe desde o dataframeit 0.6.0, e `_reasoning_tokens`
ja esta contido em `_output_tokens` (nao somar de novo).

O mesmo vale para `cpopg`/`cposg`, que retornam um dict de DataFrames —
extraia o DataFrame relevante (ex: `dados["movimentacoes"]`) e confirme
qual coluna contem o texto antes de passar.
