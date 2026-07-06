# Tribunais — Matriz de Capacidades e Parametros

Esta reference cobre os **29 tribunais com scraper direto** (25 estaduais + 4 federais). Para Datajud, JusBR, ComunicaCNJ e PDPJ, veja `references/agregadores.md`.

## Matriz de capacidades

### Tribunais com scraper direto (29)

| Tribunal | cjsg | cjpg | cpopg | cposg | Plataforma | Tag |
|----------|:----:|:----:|:-----:|:-----:|------------|---|
| **TJSP** | sim | sim | sim | sim | eSAJ + API REST | |
| **TJES** | sim | sim | - | - | PJe/Solr API | |
| **TJTO** | sim | sim | - | - | Custom HTML | |
| **TJAC** | sim | - | - | - | eSAJ | |
| **TJAL** | sim | - | - | - | eSAJ | |
| **TJAM** | sim | - | - | - | eSAJ | |
| **TJAP** | sim | - | - | - | Tucujuris REST | |
| **TJBA** | sim | - | - | - | GraphQL | |
| **TJCE** | sim | - | - | - | eSAJ | |
| **TJDFT** | sim | - | - | - | REST API | |
| **TJGO** | sim | - | - | - | Projudi HTML | `[v0.3.0+]` |
| **TJMG** | sim | - | - | - | Custom HTML + captcha | `[v0.3.0+, requer extra tjmg]` |
| **TJMS** | sim | - | - | - | eSAJ | |
| **TJMT** | sim | - | - | - | REST API | |
| **TJPA** | sim | - | - | - | BFF REST API | |
| **TJPB** | sim | - | - | - | PJe/Elasticsearch | |
| **TJPE** | sim | - | - | - | HTML form | |
| **TJPI** | sim | - | - | - | HTML server-rendered | |
| **TJPR** | sim | - | - | - | HTML form + sessao | |
| **TJRJ** | sim | - | - | - | ASPX + JSON | `[v0.3.0+]` |
| **TJRN** | sim | - | - | - | PJe/Elasticsearch | |
| **TJRO** | sim | - | - | - | JURIS/Elasticsearch | |
| **TJRR** | sim | - | - | - | JSF/PrimeFaces | |
| **TJRS** | sim | - | - | - | Google Search (GSA) | |
| **TJSC** | sim | - | - | - | eproc HTML | |
| **TRF1** | - | - | sim | - | PJe ConsultaPublica | `[unreleased]` |
| **TRF3** | - | - | sim | - | PJe ConsultaPublica | `[unreleased]` |
| **TRF5** | - | - | sim | - | PJe ConsultaPublica | `[unreleased]` |
| **TRF6** | - | - | sim | - | eproc/SJMG + captcha textual | `[unreleased]` |

**Legenda:** `sim` = implementado | `-` = nao implementado

Para Datajud, JusBR, ComunicaCNJ e PDPJ, ver `references/agregadores.md`.

### Tribunais documentados como nao-suportados

- **TJSE**: backend exige validacao server-side do Cloudflare Turnstile.
- **TJMA**: backend exige validacao server-side do reCAPTCHA v2 invisible.

---

## Mudancas estruturais recentes (le antes dos snippets)

**Nomes canonicos singulares (`[v0.3.0]` para tamanho_pagina; `[unreleased]` para classe/assunto/vara):**

| Canonico | Substitui | Onde |
|---|---|---|
| `tamanho_pagina` | `items_per_page`, `quantidade_por_pagina`, `per_page`, `qtde_itens_pagina`, `linhas_por_pagina` | TJBA, TJDFT, TJMT, TJES, TJGO, TJMG |
| `classe` | `classes`, `classe_cnj`, `classe_judicial` | TJSP `cjpg`, TJBA, TJPE, TJES, TJRO |
| `assunto` | `assuntos`, `assunto_cnj` | TJSP `cjpg`, TJPE, TJES |
| `vara` | `varas` | TJSP `cjpg` |
| `numero_processo` | `nr_processo`, `numero_cnj` | TJPB, TJRN, TJRO, TJAP |
| `relator` | `magistrado` | TJES, TJRO |
| `id_classe` | `id_classe_judicial` | TJRN, TJPB |

Os antigos continuam funcionando com `DeprecationWarning` por pelo menos um minor release. Passar canonico + alias simultaneamente -> `ValueError`.

**Filtros de classe/assunto/orgao em eSAJ aceitam `int | str | list[int|str]` `[unreleased]`:** `tjsp.cjsg(classe=[417], assunto=[3607, 5885])` funciona. Antes so aceitava `str`. Para descobrir IDs reais, use `listar_classes`, `listar_assuntos`, `listar_orgaos` e, no TJSP `cjpg`, `listar_varas`; todos retornam `id`, `nome`, `id_pai`, `nivel`, `selecionavel`, `caminho`.

**BREAKING — colunas renomeadas em DataFrames `[v0.3.0]`:**

| Tribunal | Coluna nova | Coluna antiga |
|---|---|---|
| TJES, TJMT | `processo` | `nr_processo` / `numero_unico` |
| TJRS, TJRN, TJES, TJPE, TJRO | `classe` | `classe_cnj` / `classe_judicial` |
| TJRS, TJPE, TJES | `assunto` | `assunto_cnj` / `assunto_principal` |
| TJES | `relator` | `magistrado` |

Codigo que acessa colunas pelo nome antigo precisa ser atualizado. Em particular, ao usar `dataframeit` com DataFrames desses tribunais, conferir `text_column` apos coleta.

**Datas aceitam multiplos formatos `[v0.3.0]`:**

Em endpoints com schema pydantic wired (familia eSAJ, agregadores, maioria dos tribunais), datas aceitam:

- `'DD/MM/AAAA'`
- `'DD-MM-AAAA'`
- `'AAAA-MM-DD'`
- `'AAAA/MM/DD'`
- `datetime.date` / `datetime.datetime`

O helper `coerce_brazilian_date` coage para o `BACKEND_DATE_FORMAT` declarado no schema antes da validacao pydantic.

**Auto-completar datas parciais `[unreleased]`:** quando o usuario informa apenas `data_*_inicio`, `data_*_fim` vira a data atual. Quando informa apenas `data_*_fim`, `data_*_inicio` vira `01/01/1990`. Um `UserWarning` e emitido sugerindo passar a data explicitamente.

**Validacao `extra="forbid"` em todos os endpoints wired `[v0.3.0]`:** kwargs desconhecidos viram `TypeError` com mensagem amigavel e sugestao de typo via difflib (ex: `data_juglamento` -> "voce quis dizer 'data_julgamento'?"). Antes, kwargs nao reconhecidos eram silenciosamente ignorados.

**Tribunais que rejeitam filtros de data por design `[v0.3.0]`:**

- **TJGO**: rejeita `data_julgamento_*` — backend Projudi so expoe `data_publicacao_*`.
- **TJES** (`cjsg`/`cjpg`) e **TJMT** (`cjsg`): rejeitam `data_publicacao_*` — backends so expoem `data_julgamento_*`.
- **TJRJ**: rejeita ambos `data_julgamento_*` e `data_publicacao_*` — backend ASPX so expoe granularidade anual via `ano_inicio`/`ano_fim`.

---

## Parametros da cjsg por tribunal

Todos os tribunais aceitam `pesquisa` e `paginas`. Os filtros adicionais variam.

### Tribunais eSAJ (TJAC, TJAL, TJAM, TJCE, TJMS, TJSP)

Compartilham a mesma estrutura de parametros:

```python
scraper.cjsg(
    pesquisa='dano moral',            # str
    paginas=range(1, 4),              # 1-based
    ementa=None,                      # filtro por texto da ementa
    numero_recurso=None,
    classe=None,                      # int | str | list[int|str]
    assunto=None,                     # int | str | list[int|str]
    comarca=None,                     # int | str (TJSP apenas — exclusivo na familia eSAJ)
    orgao_julgador=None,              # int | str | list[int|str]
    data_julgamento_inicio=None,      # aceita DD/MM/AAAA, AAAA-MM-DD, etc.
    data_julgamento_fim=None,
    data_publicacao_inicio=None,      # nao no TJSP
    data_publicacao_fim=None,
    origem=None,                      # 'T' (2o grau) ou 'R' (turma recursal)
    tipo_decisao=None                 # 'acordao' ou 'monocratica'
)
```

**Construtor eSAJ:** `(verbose=0, download_path=None, sleep_time=1.0)`. TJSP usa `sleep_time=0.5`.

**Auto-chunk para janelas longas `[v0.3.0]`:** janelas `data_julgamento_*` que excedem 366 dias sao automaticamente divididas em chunks e concatenadas (com dedup) por `auto_chunk=True` (default). Falhas em janelas individuais viram `UserWarning` e o DataFrame retorna parcial. Para o comportamento antigo (`ValueError` em janelas longas), passar `auto_chunk=False`. Veja `references/tjsp.md` para detalhes.

**Notas TJSP:** extras em relacao aos demais eSAJ — `comarca`, `tipo_decisao`, `baixar_sg`; `cjsg` aceita `pesquisa=""` `[unreleased]` para buscar so por filtros; `cjsg` e `cjpg` aceitam `count_only=True` `[unreleased]` para estimar volume antes da coleta. Ver `references/tjsp.md`.

**Guard de tamanho de `pesquisa` em TJSP `[v0.3.0]`:** mais de 120 caracteres levanta `QueryTooLongError` (subclasse de `ValueError`) antes do HTTP. Veja `references/tjsp.md`.

### TJRS

```python
tjrs.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    classe=None, assunto=None, orgao_julgador=None,
    relator=None,
    data_julgamento_inicio=None, data_julgamento_fim=None,
    data_publicacao_inicio=None, data_publicacao_fim=None,
    tipo_processo=None,
    secao=None                          # 'civel', 'crime'
)
```

**Coluna renomeada `[v0.3.0]`:** `classe` (era `classe_cnj`), `assunto` (era `assunto_cnj`).

### TJPR

```python
tjpr.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    data_julgamento_inicio=None, data_julgamento_fim=None,
    data_publicacao_inicio=None, data_publicacao_fim=None
)
```

### TJDFT

```python
tjdft.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    sinonimos=True,
    espelho=True,
    inteiro_teor=False,
    tamanho_pagina=10,                  # canonico [v0.3.0] (substitui quantidade_por_pagina)
    data_julgamento_inicio=None,        # [v0.3.0] agora aceita; envia termosAcessorios="entre X e Y"
    data_julgamento_fim=None
)
```

`[v0.3.0]` Agora envia `termosAcessorios="entre YYYY-MM-DD e YYYY-MM-DD"` ao backend (antes emitia `UserWarning` e ignorava o filtro). Schema wired via `apply_input_pipeline_search`; kwargs desconhecidos viram `TypeError`.

### TJES

```python
tjes.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    core='pje2g',                       # 'pje2g', 'pje2g_mono', 'legado', 'turma_recursal_legado'
    busca_exata=None,
    relator=None,                       # singular canonico [v0.3.0] (era magistrado)
    orgao_julgador=None,
    classe=None,                        # singular canonico [v0.3.0] (era classe_judicial)
    jurisdicao=None, assunto=None,
    ordenacao=None,
    tamanho_pagina=20,                  # canonico [v0.3.0] (substitui per_page); default 20 no TJES
    data_julgamento_inicio=None, data_julgamento_fim=None,
)
# cjpg usa mesma estrutura mas com core='pje1g'
tjes.cjpg(pesquisa='...', paginas=range(1, 4))
```

**Gotcha `[v0.3.0]`:** rejeita `data_publicacao_*` com `TypeError` — backend so expoe `data_julgamento_*`.

**Colunas renomeadas `[v0.3.0]`:** `processo`, `classe`, `assunto`, `relator` (antes: `nr_processo`, `classe_cnj`, `assunto_cnj`, `magistrado`).

### TJTO

```python
tjto.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    tipo_documento='acordaos',          # 'acordaos', 'decisoes', 'sentencas'
    ordenacao='DESC',                   # 'DESC', 'ASC', 'RELEV'
    numero_processo=None,
    soementa=None,                      # buscar so na ementa
    data_julgamento_inicio=None, data_julgamento_fim=None
)
# cjpg tem mesmos parametros
# metodo extra: tjto.cjsg_ementa(uuid) para buscar ementa completa
```

### TJBA

```python
tjba.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    numero_recurso=None,
    orgaos=None,                        # list de orgaos
    relatores=None,                     # list de relatores
    classe=None,                        # singular canonico [unreleased] (era classes)
    data_julgamento_inicio=None,        # aceita BR e ISO [v0.3.0]
    data_julgamento_fim=None,
    segundo_grau=None,                  # bool
    turmas_recursais=None,              # bool
    tipo_acordaos=None, tipo_decisoes_monocraticas=None,
    ordenado_por=None,
    tamanho_pagina=10                   # canonico [v0.3.0] (substitui items_per_page)
)
```

`[v0.3.0]` Datas aceitam formato BR (`DD/MM/AAAA`) alem do ISO original.

### TJMT

```python
tjmt.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    tipo_consulta=None,                 # 'Acordao' ou 'DecisaoMonocratica'
    relator=None, orgao_julgador=None, classe=None,
    tipo_processo=None,                 # 'Civel' ou 'Criminal'
    thesaurus=None,
    tamanho_pagina=10,                  # canonico [v0.3.0] (substitui quantidade_por_pagina)
    data_julgamento_inicio=None,        # ISO 8601 [v0.3.0]
    data_julgamento_fim=None
)
```

**Gotcha `[v0.3.0]`:** rejeita `data_publicacao_*` com `TypeError`. Coluna renomeada: `processo` (era `nr_processo`/`numero_unico`).

### TJPA

```python
tjpa.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    relator=None, orgao_julgador_colegiado=None,
    classe=None, assunto=None,
    origem=None,                        # list
    tipo=None,                          # list
    data_julgamento_inicio=None,        # ISO 8601 [v0.3.0]
    data_julgamento_fim=None,
    sort_by='datajulgamento',
    sort_order='asc',
    query_type='free',                  # 'free' ou 'any'
    query_scope='ementa'                # 'ementa' ou 'inteiroteor'
)
```

### TJAP

```python
tjap.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    orgao=None,
    numero_processo=None,               # singular canonico [v0.3.0] (era numero_cnj)
    numero_acordao=None,
    numero_ano=None, palavras_exatas=None,
    relator=None, secretaria=None, classe=None,
    votacao=None, origem=None
)
```

**Gotchas:** backend Tucujuris **nao expoe filtro de data** — `test_release_date_filter.py` marca o TJAP como `xfail` estrito por limitacao server-side. `[unreleased]` O site pode responder com validacao server-side do Cloudflare Turnstile; nesse caso o scraper levanta `TJAPSecurityCheckError`. Trate como bloqueio ambiental/anti-bot, nao como erro de filtros do usuario.

### TJPB

```python
tjpb.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    numero_processo=None,               # singular canonico [v0.3.0] (era nr_processo)
    id_classe=None,                     # singular canonico [v0.3.0] (era id_classe_judicial)
    id_orgao_julgador=None,
    id_relator=None,
    id_origem=None,                     # default '8,2'
    decisoes=None                       # bool
)
```

`[v0.3.0]` Backend nao filtra por data de julgamento — o scraper pos-filtra o DataFrame retornado em `dt_ementa` (exposto como `data_julgamento`). Funciona mesmo com so uma das datas informada.

### TJPE

```python
tjpe.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    data_julgamento_inicio=None,
    data_julgamento_fim=None,
    relator=None,
    classe=None,                        # singular canonico [v0.3.0] (era classe_cnj)
    assunto=None,                       # singular canonico [v0.3.0] (era assunto_cnj)
    meio_tramitacao=None,
    tipo_decisao=None,                  # 'acordaos', 'monocraticas', 'todos'
    contratos=None                      # [unreleased] filtro novo (issue #197)
)
```

`[unreleased]` Suporte a filtro `contratos`.

### TJPI

```python
tjpi.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    tipo=None,                          # 'Acordao', 'Decisao Terminativa', 'Sumula'
    relator=None, classe=None, orgao=None,
    data_julgamento_inicio=None,        # [v0.3.0] envia data_min/data_max
    data_julgamento_fim=None
)
```

### TJRN

```python
tjrn.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    numero_processo=None,               # singular canonico [v0.3.0] (era nr_processo)
    id_classe=None,                     # singular canonico [v0.3.0] (era id_classe_judicial)
    id_orgao_julgador=None,
    id_relator=None, id_colegiado=None,
    sistema=None,                       # 'PJE', 'SAJ', ''
    decisoes=None,                      # 'Monocraticas', 'Colegiadas', 'Sentencas', ''
    jurisdicoes=None, grau=None,
    data_julgamento_inicio=None,        # envia dt_inicio/dt_fim em DD-MM-YYYY [v0.3.0]
    data_julgamento_fim=None
)
```

**Coluna `data_julgamento`** vem de `dt_assinatura_teor` (`dt_julgamento` nao existe no indice Elasticsearch do TJRN). Coluna renomeada: `classe` (era `classe_cnj`).

### TJRO

```python
tjro.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    tipo=None,                          # list, default ['EMENTA']
    numero_processo=None,               # singular canonico [v0.3.0] (era nr_processo)
    relator=None,                       # singular canonico [v0.3.0] (era magistrado)
    orgao_julgador=None, orgao_julgador_colegiado=None,
    classe=None,                        # singular canonico [v0.3.0] (era classe_judicial)
    instancia=None,                     # list
    termo_exato=None,                   # bool
    data_julgamento_inicio=None,        # ISO 8601 [v0.3.0]
    data_julgamento_fim=None
)
```

### TJRR

```python
tjrr.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    relator=None,
    orgao_julgador=None,                # list
    especie=None,                       # list
    data_julgamento_inicio=None,
    data_julgamento_fim=None
)
```

`[v0.3.0]` JSF auto-gerado: descoberta dinamica dos nomes de campos (que mudam quando o tribunal reordena componentes do form). Antes, o scraper retornava zero resultados silenciosamente apos renumeracao do tribunal.

`[unreleased]` `relator` aceita lista de nomes regimentais. A paginacao da tabela principal de acordaos foi corrigida, mas decisoes monocraticas ficam numa segunda tabela com paginador proprio e ainda retornam so a primeira pagina.

### TJSC

```python
tjsc.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    campo=None,                         # 'E' (ementa) ou 'I' (inteiro teor)
    processo=None,
    data_julgamento_inicio=None, data_julgamento_fim=None,
    data_publicacao_inicio=None, data_publicacao_fim=None
)
```

### TJGO `[v0.3.0+]`

Backend Projudi com Cloudflare Turnstile (mas sem validacao server-side — flow funciona com HTTP puro).

```python
tjgo.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    id_instancia=0,                     # 0 todas / 1 1o grau / 2 recursal / 3 tribunal
    id_area=0,                          # 0 todas / 1 civel / 2 criminal
    id_serventia_subtipo=0,             # int | str — ID do subtipo de serventia
    numero_processo=None,
    tamanho_pagina=10,                  # canonico [v0.3.0] (substitui qtde_itens_pagina)
    data_publicacao_inicio=None,        # DD/MM/AAAA ou AAAA-MM-DD
    data_publicacao_fim=None
)
```

**Construtor:** `(sleep_time=1.0)`.

**Gotcha BREAKING `[v0.3.0]`:** rejeita `data_julgamento_inicio`/`fim` com `TypeError`. O backend Projudi so expoe `data_publicacao_*`. Antes emitia `UserWarning` e seguia sem o filtro (resultado nao-filtrado silenciosamente).

### TJMG `[v0.3.0+, requer extra tjmg]`

Captcha numerico de 5 digitos resolvido automaticamente via `txtcaptcha`. Requer `pip install 'juscraper[tjmg]'`.

```python
tjmg.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    pesquisar_por='ementa',             # 'ementa' ou 'acordao' (inteiro teor)
    order_by=2,                         # 2 data julgamento / 1 data publicacao / 0 precisao
    tamanho_pagina=10,                  # Literal[10, 20, 50]; substitui linhas_por_pagina
    data_julgamento_inicio=None, data_julgamento_fim=None,
    data_publicacao_inicio=None, data_publicacao_fim=None
)
```

**Construtor:** `(sleep_time=1.0)`.

**Gotcha:** cap de **400 resultados** (limite do TJMG). `paginas=None` baixa ate esse cap.

### TJRJ `[v0.3.0+]`

Backend ASPX com reCAPTCHA renderizado, mas **nao validado server-side**.

```python
tjrj.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    ano_inicio=None,                    # str | int — granularidade anual
    ano_fim=None,                       # str | int
    competencia='1',                    # '1' civel (default) / '2' criminal / '3' ambos
    origem='1',                         # '1' 2o grau (default)
    tipo_acordao=True,                  # bool
    tipo_monocratica=True,              # bool
    magistrado_codigo=None,             # str — IDs separados por virgula
    orgao_codigo=None                   # str — IDs separados por virgula
)
```

**Construtor:** `(sleep_time=1.0)`.

**Gotcha BREAKING `[v0.3.0]`:** **rejeita `data_julgamento_*` e `data_publicacao_*` com `TypeError`** — o backend ASPX so expoe granularidade anual via `ano_inicio`/`ano_fim` (campos `cmbAnoInicio`/`cmbAnoFim` do form). Sem `ano_inicio`/`ano_fim`, o backend usa o ano corrente, nao "todos os anos". `test_release_date_filter.py` marca o TJRJ como `xfail` estrito por limitacao server-side.

### TRFs (TRF1, TRF3, TRF5) — `cpopg` via PJe `[unreleased]`

Acessam a `ConsultaPublica/listView.seam` em:

- TRF1: `https://pje1g-consultapublica.trf1.jus.br/consultapublica/`
- TRF3: `https://pje1g.trf3.jus.br/pje/`
- TRF5: `https://pje1g.trf5.jus.br/pjeconsulta/`

```python
trf1 = jus.scraper('trf1')   # ou 'trf3', 'trf5'
df = trf1.cpopg(
    id_cnj='1003063-27.2023.4.01.3304',  # str ou list[str]
    download_pecas=True,
    diretorio='dados/trf1_pecas'
)
```

**Construtor:** `(verbose=0, download_path=None, sleep_time=1.0)`.

**Retorna:** `pd.DataFrame` com uma linha por processo. Colunas: `id_cnj`, `processo`, `classe`, `assunto`, `data_distribuicao`, `orgao_julgador`, `jurisdicao`, `endereco_orgao`, `polo_ativo`, `polo_passivo`, `movimentacoes`, `documentos`. Processos nao encontrados no portal publico devolvem linha so com `id_cnj`. Com `download_pecas=True`, o scraper baixa cada peca para `<diretorio>/<cnj>/<id_processo_doc>.html` e adiciona a coluna `pecas` com a lista de caminhos por processo.

**Paginacao automatica de movimentacoes e documentos `[unreleased]`:** PJe pagina as tabelas com Richfaces inslider (15 linhas/pagina). O scraper detecta o slider e itera as paginas restantes via POST AJAX. Isso vale tanto para `movimentacoes` quanto para `documentos`, e garante que `download_pecas=True` nao baixe apenas as primeiras 15 pecas.

**Especializacoes por tribunal:**

- **TRF3** envia `classeJudicial`+`sgbClasseJudicial_selection` (autocomplete) e campos `dataAutuacaoDecoration`. Pode ser bloqueado por Akamai; nesse caso levanta `BotChallengeBlockedError`.
- **TRF5** envia `classeProcessualProcessoHidden` (popup picker), omite as datas, ignora reCAPTCHA renderizado (`if (false)` no `executarReCaptcha` — dead code). Tambem pode sofrer `BotChallengeBlockedError`.
- **TRF1** segue o mesmo padrao do TRF3 (autocomplete + `dataAutuacaoDecoration`); divergencia em `BASE_URL` apenas. Tambem pode sofrer `BotChallengeBlockedError`.

**Gotcha:** cada tribunal tem implementacao independente em `courts/{trf1,trf3,trf5}/`, mas compartilha a base `_trf` para o contrato atual de `cpopg`/download de pecas. Bloqueios Akamai sao ambientais/anti-bot; reduza ritmo, tente outro horario/IP, ou use Datajud quando bastarem metadados.

### TRF6 — `cpopg` via eproc/SJMG `[unreleased]`

O TRF6 acessa o eproc de 1º grau da Seção Judiciaria de Minas Gerais (`https://eproc1g.trf6.jus.br/eproc/`). O formulario exige captcha textual em imagem PNG embutida no HTML e validada server-side; o scraper resolve via `txtcaptcha` e refaz o GET do form a cada tentativa porque o captcha e vinculado ao cookie `PHPSESSID`.

```python
trf6 = jus.scraper('trf6', max_captcha_attempts=3)
df = trf6.cpopg(id_cnj='1000149-71.2024.4.06.3800')
```

**Construtor:** `(verbose=0, download_path=None, sleep_time=1.0, max_captcha_attempts=3)`.

**Retorna:** `pd.DataFrame` com uma linha por processo. Colunas: `id_cnj`, `processo`, `classe`, `data_autuacao`, `situacao`, `magistrado`, `orgao_julgador`, `assuntos`, `polo_ativo`, `polo_passivo`, `mpf`, `perito`, `movimentacoes`. Processos nao encontrados devolvem linha so com `id_cnj`. **Nao documentar `download_pecas` para TRF6** — esse parametro e dos TRFs PJe acima.

**Instalacao:** ainda nao disponivel em PyPI. Requer `pip install git+https://github.com/jtrecenti/juscraper.git`.

---

## TJSP — Detalhes extras

Unico tribunal com suporte completo (cpopg + cposg + cjsg + cjpg).

Detalhes de endpoints exclusivos (`cjpg`, parametro `method`), extras da `cjsg` (`comarca`, `tipo_decisao`, `baixar_sg`, `pesquisa=""`), cobertura temporal validada, `QueryTooLongError` e `auto_chunk` movidos para a reference dedicada **`references/tjsp.md`**.

Convencao da skill: cada tribunal pode ter sua propria reference a medida que especificidades sejam validadas (ex: `tjsp.md`, futuramente `tjrs.md`, `tjpr.md` etc.). Este arquivo (`tribunais.md`) mantem a matriz comparativa e os parametros da `cjsg` por familia de plataforma.

---

## Gotchas comuns

1. **`paginas=None` baixa TODAS as paginas** — para buscas amplas pode gerar milhares de requisicoes. Sempre prefira um range explicito.

2. **`sleep_time=0` causa bloqueio** — os tribunais detectam acesso agressivo.

3. **cpopg/cposg retornam dict, cjsg/cjpg retornam DataFrame** — nao trate todos igual. Excecao: `cpopg` dos TRFs retorna DataFrame (uma linha por processo), nao dict.

4. **Numero CNJ: separadores opcionais mas zeros a esquerda importam** — `1000149-71.2024.8.26.0346` e `10001497120248260346` sao aceitos.

5. **TJDFT `[v0.3.0]` agora aceita filtros de data** — o que mudou: antes ignorava `data_julgamento_*` com `UserWarning`; agora envia `termosAcessorios="entre X e Y"` ao backend.

6. **Formatos de data `[v0.3.0]`:** em endpoints com schema pydantic wired, aceita `DD/MM/AAAA`, `DD-MM-AAAA`, `AAAA-MM-DD`, `AAAA/MM/DD` e objetos `datetime.date`/`datetime.datetime`. Antes era estritamente o formato declarado pelo backend de cada tribunal.

7. **Filtros parciais auto-completam `[unreleased]`:** informar apenas `data_*_inicio` ou apenas `data_*_fim` faz o outro lado virar respectivamente "hoje" ou `01/01/1990`. Emite `UserWarning`.

8. **cposg do TJSP com `method='api'`** — o parse JSON nao esta implementado. Use `'html'`.

9. **JusBR e PDPJ exigem autenticacao antes de qualquer chamada.** Detalhes em `references/agregadores.md`.

10. **Datajud requer `tribunal` ou `numero_processo`** — `[v0.3.0]` BREAKING: sem nenhum dos dois, agora levanta `ValueError` em vez de retornar DataFrame vazio.

11. **Aliases depreciados emitem `DeprecationWarning`** — sempre use o nome canonico (`pesquisa`, `data_julgamento_inicio`, `tamanho_pagina`, `classe`, `assunto`, `vara`, `numero_processo`, `relator`, `id_classe`). Tabela completa em `references/api.md`.

12. **`RetryExhaustedError` em `HTTPScraper` `[unreleased]`:** familia eSAJ (TJAC/TJAL/TJAM/TJCE/TJMS/TJSP `cjsg`) e familia 1C-a (TJRN/TJRO/TJRR `cjsg`) — alem dos agregadores ComunicaCNJ, JusBR e Datajud — migraram para `HTTPScraper`. Quando esgota `max_retries` em 429/5xx persistente, a excecao propagada e `juscraper.core.exceptions.RetryExhaustedError` em vez de `requests.HTTPError`/`requests.RequestException`. Para codigo defensivo, capture ambas.

13. **`auto_chunk=True` substitui workaround manual de iteracao por ano `[v0.3.0]`:** na familia eSAJ (TJSP/TJAC/TJAL/TJAM/TJCE/TJMS `cjsg`, TJSP `cjpg`), janelas `data_julgamento_*` maiores que 366 dias agora sao automaticamente divididas em chunks e concatenadas com dedup. O `pd.concat([cjpg(...) for ano in range(...)])` antigo ja nao e necessario para esse caso. Para o comportamento antigo (`ValueError` em janelas longas), passar `auto_chunk=False`.

14. **Colunas BREAKING em TJES/TJMT/TJRS/TJRN/TJPE/TJRO `[v0.3.0]`:** alguns DataFrames trocaram nomes de coluna (`processo`, `classe`, `assunto`, `relator` substituem `nr_processo`/`numero_unico`, `classe_cnj`/`classe_judicial`, `assunto_cnj`/`assunto_principal`, `magistrado`). Codigo que acessa colunas pelo nome antigo precisa ser atualizado. Em particular, ao integrar com `dataframeit` (`text_column=...`), conferir o DataFrame retornado.

15. **`extra="forbid"` em todos os endpoints wired `[v0.3.0]`:** kwarg desconhecido vira `TypeError` com sugestao de typo. Antes, kwargs nao reconhecidos eram silenciosamente ignorados (bug silencioso de raspagem nao-filtrada).
