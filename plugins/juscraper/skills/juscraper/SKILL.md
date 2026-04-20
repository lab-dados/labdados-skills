---
name: juscraper
description: Raspar dados judiciais brasileiros com a biblioteca juscraper. Use para consultar processos por numero CNJ (cpopg/cposg), buscar jurisprudencia (cjsg/cjpg), ou consultas cross-tribunal via Datajud e JusBR. Cobre 22 tribunais estaduais (TJSP, TJRS, TJPR, TJDFT, TJBA, TJCE, TJES, TJMT, TJPA, TJPB, TJPE, TJPI, TJRN, TJRO, TJRR, TJSC, TJTO, TJAC, TJAL, TJAM, TJAP, TJMS) e 2 agregadores nacionais (Datajud, JusBR). Use esta skill sempre que o usuario mencionar tribunal brasileiro, numero CNJ, acordao, jurisprudencia, pesquisa empirica em direito, dados judiciais, consulta processual, decisoes judiciais, processos judiciais, eSAJ, poder judiciario, ou qualquer tarefa envolvendo coleta de dados de tribunais brasileiros — mesmo que nao mencione explicitamente "juscraper".
---

# JusScraper Skill

juscraper e uma biblioteca Python para raspagem de dados do poder judiciario brasileiro.
Cobre **22 tribunais estaduais** e **2 agregadores nacionais** (Datajud e JusBR),
permitindo buscar jurisprudencia, consultar processos e baixar documentos.

- Repositorio: https://github.com/jtrecenti/juscraper
- Documentacao: https://jtrecenti.github.io/juscraper/

## Antes de comecar

Complete este checklist antes de qualquer chamada.

### 1. Instalacao

Verifique se `juscraper` esta instalado:
1. `pip show juscraper` ou `python -c "import juscraper; print(juscraper.__version__)"`
2. Se nao instalado: `pip install juscraper` ou `uv add juscraper`
3. Python >= 3.11 obrigatorio.
4. Para a versao mais recente (com todos os tribunais):
   `pip install git+https://github.com/jtrecenti/juscraper.git`

### 2. Autenticacao (condicional)

- **Todos os 22 tribunais diretos:** Nenhuma autenticacao necessaria.
- **Datajud:** Tem API key publica embutida. Funciona sem configuracao.
- **JusBR:** Autenticacao obrigatoria (sem token, qualquer chamada falha com RuntimeError).
  Pergunte ao usuario:
  > Para usar o JusBR, voce precisa de um token JWT do gov.br.
  > Acesse https://www.jus.br, faca login via gov.br, e extraia o token
  > da aba Network do navegador (campo `access_token`).
  > Alternativamente, use `.auth_firefox()` se tiver sessao ativa no Firefox.

## Roteamento de decisao — o que usar?

### Passo 1: O que voce precisa?

| Preciso de... | Metodo | Scrapers disponiveis |
|---|---|---|
| Buscar jurisprudencia por palavra-chave (2o grau) | `cjsg(pesquisa)` | Todos os 22 tribunais |
| Buscar jurisprudencia (1o grau) | `cjpg(pesquisa)` | TJSP, TJES, TJTO |
| Dados de processo por numero CNJ (1o grau) | `cpopg(id_cnj)` | TJSP (direto) ou JusBR (qualquer tribunal) |
| Dados de processo por numero CNJ (2o grau) | `cposg(id_cnj)` | TJSP |
| Listar processos de qualquer tribunal | `listar_processos()` | Datajud |
| Baixar documentos/pecas de um processo | `download_documents()` | JusBR |

### Passo 2: Qual tribunal?

- Se o usuario especificou um tribunal e ele esta entre os 22 → use o scraper direto.
- Se o tribunal nao tem scraper direto (ex: TJRJ, TJMG, TJGO) → use **Datajud**
  para listar processos ou **JusBR** para consultar por CNJ e baixar documentos.
- Para jurisprudencia sem tribunal especificado → TJSP e o maior e mais completo.
- Para jurisprudencia de 1o grau → apenas TJSP, TJES ou TJTO suportam cjpg.
- Consulte `references/tribunais.md` para a matriz completa de capacidades e parametros.

## Vocabulario academico → endpoint juscraper

Artigos de pesquisa empirica em direito usam termos proprios dos tribunais
que nem sempre sao obvios ao implementar a coleta. Mapeamento:

| Termo no artigo | Endpoint juscraper | Observacao |
|---|---|---|
| "banco de sentencas" / "decisoes de 1o grau" | `cjpg` | Consulta de Julgados de Primeiro Grau — **publico**, nao precisa login institucional. Disponivel apenas em TJSP, TJES, TJTO |
| "jurisprudencia" / "acordaos" | `cjsg` | Consulta de Jurisprudencia (2a instancia). Disponivel em todos os 22 tribunais com scraper direto |
| "portal eletronico do tribunal" | `cjpg` ou `cjsg` (contexto) | Verifique a serie temporal e instancia descrita |
| "classificacao tematica do tribunal" / "assunto" | filtro de **assunto** (codigo DPJ/CNJ) | Preferir a busca textual para termos genericos — ver proxima secao |
| "autos completos" / "inteiro teor" | `cpopg`/`cposg` por CNJ | Requer lista previa de numeros de processos |
| "banco de dados do CNJ" / "DataJud" | `listar_processos` via Datajud | Metadados cross-tribunal |

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

**Onde encontrar codigos de assunto**: TJSP tem lista extraida da
pagina de busca avancada em `references/assuntos-tjsp.md` (json:
`assuntos-tjsp.json`). Para outros tribunais, a **Tabela Processual
Unificada do CNJ** (Resolucao 46/2007) define os codigos nacionais
de assunto que a maioria dos tribunais adota. Conforme references
especificas de outros tribunais forem validadas, mais arquivos
`assuntos-<tribunal>.md` poderao aparecer aqui.

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

## Quando usar scrapers diretos vs Datajud vs JusBR

| Criterio | Scraper direto (22 tribunais) | Datajud | JusBR |
|---|---|---|---|
| Jurisprudencia (cjsg) | Sim — principal uso | Nao | Nao |
| Consulta por CNJ | Apenas TJSP (cpopg/cposg) | Sim (listar_processos) | Sim (cpopg) |
| Cross-tribunal | 1 tribunal por vez | Sim (detecta tribunal pelo CNJ) | Sim |
| Documentos/pecas | Nao | Nao | Sim |
| Autenticacao | Nenhuma | Nenhuma (key publica) | Obrigatoria (JWT) |

Priorize sempre os scrapers diretos quando o tribunal estiver disponivel — eles fornecem
dados mais ricos (ementas completas, filtros especificos) do que os agregadores.

## Tratamento de erros

Se o scraper falhar (timeout, bloqueio, erro HTTP):
- Aumente `sleep_time` e tente novamente com menos paginas.
- Tribunais ficam mais lentos em horario comercial — sugira tentar em outro horario.
- Se persistir, o Datajud e uma alternativa mais estavel para metadados de processos.

## O que fazer com os dados

Pesquisa empirica em direito tipicamente envolve coleta → armazenamento → analise.
Apos a coleta:

- **Para explorar no chat:** `df.head()`, `df.describe()`, `df['coluna'].value_counts()`
- **Para salvar:** `df.to_csv('resultados.csv', index=False)` ou
  `df.to_parquet('resultados.parquet')` (parquet e melhor para DataFrames grandes)
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
  assinaturas dos metodos principais com parametros, tipos de retorno e exemplos de codigo.
  Leia antes de qualquer tarefa.

- **`references/tribunais.md`** — Matriz de capacidades (22 tribunais), parametros especificos
  de cada tribunal (cada um tem filtros proprios na cjsg), plataformas, e gotchas comuns.
  Leia quando precisar escolher entre tribunais ou entender seus parametros especificos.

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
| Codificacao via LLM (campos estruturados) | **dataframeit-skill** | DataFrame com colunas extraidas + `_total_tokens` |
| Revisao de literatura | **openalex-skill** | Lista de artigos relevantes |

Se o usuario vai codificar o que foi coletado via LLM, lembre-o da
**dataframeit-skill** e, se ele tem plano Claude Code, do modo
`provider='claude_code'` (consome tokens do plano, nao API).

### Gotcha: nome da coluna de texto ao chamar dataframeit

O DataFrame do `cjpg`/`cjsg` tem a coluna com o texto da decisao chamada
**`decisao`**, e ela NAO e a primeira coluna do DataFrame (a primeira e
tipicamente `cd_processo` ou `id_processo`). O `dataframeit` por default
usa a **primeira coluna** como texto — entao sem `text_column="decisao"`
ele tenta enviar o numero do processo ao LLM e o resultado vira lixo.

Sempre passe explicitamente:

```python
resultado = dataframeit(
    df_cjpg, ModeloPydantic, "Analise: {texto}",
    text_column="decisao",   # obrigatorio para dataframes do juscraper
)
```

O mesmo vale para `cpopg`/`cposg`, que retornam um dict de DataFrames —
extraia o DataFrame relevante (ex: `dados["movimentacoes"]`) e confirme
qual coluna contem o texto antes de passar.
