# Tribunais — Matriz de Capacidades e Parametros

Esta reference cobre os **30 tribunais com scraper direto** (25 estaduais + 4 TRFs + STF). Para Datajud, JusBR, ComunicaCNJ e PDPJ, veja `references/agregadores.md`.

## Matriz de capacidades

### Tribunais com scraper direto (30)

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
| **TJGO** | sim | - | - | - | Projudi HTML | |
| **TJMG** | sim | - | - | - | Custom HTML + captcha | `[v0.3.0+, requer extra tjmg]` |
| **TJMS** | sim | - | - | - | eSAJ | |
| **TJMT** | sim | - | - | - | REST API | |
| **TJPA** | sim | - | - | - | BFF REST API | |
| **TJPB** | sim | - | - | - | PJe/Elasticsearch | |
| **TJPE** | sim | - | - | - | HTML form | |
| **TJPI** | sim | - | - | - | HTML server-rendered | |
| **TJPR** | sim | - | - | - | HTML form + sessao | |
| **TJRJ** | sim | - | - | - | ASPX + JSON | |
| **TJRN** | sim | - | - | - | PJe/Elasticsearch | |
| **TJRO** | sim | - | - | - | JURIS/Elasticsearch | |
| **TJRR** | sim | - | - | - | JSF/PrimeFaces | |
| **TJRS** | sim | - | - | - | Google Search (GSA) | |
| **TJSC** | sim | - | - | - | eproc HTML | |
| **TRF1** | - | - | sim | - | PJe ConsultaPublica | `[v0.4.0+]` |
| **TRF3** | - | - | sim | - | PJe ConsultaPublica | `[v0.4.0+]` |
| **TRF5** | - | - | sim | - | PJe ConsultaPublica | `[v0.4.0+]` |
| **TRF6** | - | - | sim | - | eproc/SJMG + captcha textual | `[v0.4.0+]`, requer `txtcaptcha` |
| **STF** | `listar_decisoes` | - | - | - | API do portal + AWS WAF | `[v0.4.0+]`, requer extra `stf` ou `waf_token` |

**Legenda:** `sim` = implementado | `-` = nao implementado. O STF nao tem `cjsg`: a busca de jurisprudencia e `listar_decisoes`, e a contagem, `contar_decisoes`.

Para Datajud, JusBR, ComunicaCNJ e PDPJ, ver `references/agregadores.md`.

### Tribunais documentados como nao-suportados

- **TJSE**: backend exige validacao server-side do Cloudflare Turnstile.
- **TJMA**: backend exige validacao server-side do reCAPTCHA v2 invisible.

---

## Mudancas estruturais recentes (le antes dos snippets)

**Nomes canonicos singulares:**

| Canonico | Substitui | Onde |
|---|---|---|
| `tamanho_pagina` | `items_per_page`, `quantidade_por_pagina`, `per_page`, `qtde_itens_pagina`, `linhas_por_pagina` | TJBA, TJDFT, TJMT, TJES, TJGO, TJMG |
| `classe` | `classes`, `classe_cnj`, `classe_judicial` | TJSP `cjpg` e TJBA `[v0.4.0+]`; TJPE, TJES, TJRO `[v0.3.0]` |
| `assunto` | `assuntos`, `assunto_cnj` | TJSP `cjpg` e Datajud `[v0.4.0+]`; TJPE `[v0.3.0]` |
| `vara` | `varas` | TJSP `cjpg` `[v0.4.0+]` |
| `numero_processo` | `nr_processo`, `numero_cnj` | TJPB, TJRN, TJRO, TJAP |
| `relator` | `magistrado` | TJES, TJRO |
| `id_classe` | `id_classe_judicial` | TJRN, TJPB |

Os antigos continuam funcionando com `DeprecationWarning` por pelo menos um minor release. Passar canonico + alias simultaneamente -> `ValueError`.

**Filtros de classe/assunto/orgao em eSAJ aceitam `int | str | list[int|str]` `[v0.4.0+]`:** `tjsp.cjsg(classe=[417], assunto=[3607, 5885])` funciona. Antes so aceitava `str`. Para descobrir IDs reais `[v0.4.0+]`, use `listar_classes`, `listar_assuntos`, `listar_orgaos` e, no TJSP `cjpg`, `listar_varas`; todos retornam `id`, `nome`, `id_pai`, `nivel`, `selecionavel`, `caminho`.

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

**Auto-completar datas parciais `[v0.4.0+]`:** quando o usuario informa apenas `data_*_inicio`, `data_*_fim` vira a data atual. Quando informa apenas `data_*_fim`, `data_*_inicio` vira `01/01/1990`. Um `UserWarning` e emitido sugerindo passar a data explicitamente.

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
    numero_recurso=None,              # nao no TJSP
    classe=None,                      # int | str | list[int|str]
    assunto=None,                     # int | str | list[int|str]
    comarca=None,                     # int | str (ID interno da comarca, valor unico)
    orgao_julgador=None,              # int | str | list[int|str]
    data_julgamento_inicio=None,      # aceita DD/MM/AAAA, AAAA-MM-DD, etc.
    data_julgamento_fim=None,
    data_publicacao_inicio=None,      # nao no TJSP
    data_publicacao_fim=None,
    origem='T',                       # 'T' (2o grau) ou 'R' (turma recursal); nao no TJSP
    tipo_decisao='acordao'            # 'acordao' ou 'monocratica'
)
```

**Construtor eSAJ:** `(verbose=0, download_path=None, sleep_time=1.0)`. TJSP usa `sleep_time=0.5`.

**Auto-chunk para janelas longas `[v0.3.0]`:** janelas `data_julgamento_*` que excedem 366 dias sao automaticamente divididas em chunks e concatenadas (com dedup) por `auto_chunk=True` (default). Falhas em janelas individuais viram `UserWarning` e o DataFrame retorna parcial. Para o comportamento antigo (`ValueError` em janelas longas), passar `auto_chunk=False`. Veja `references/tjsp.md` para detalhes.

**Notas TJSP:** no lugar de `origem` o TJSP usa `baixar_sg`, e nao aceita `numero_recurso` nem `data_publicacao_*`; `comarca`, `tipo_decisao` e `count_only` valem para toda a familia eSAJ. `cjsg` aceita `pesquisa=""` para buscar so por filtros; `cjsg` e `cjpg` aceitam `count_only=True` para estimar volume antes da coleta. Ver `references/tjsp.md`.

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
    classe=None,                        # singular canonico (era classes)
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

**Gotchas:** backend Tucujuris **nao expoe filtro de data** — `test_release_date_filter.py` marca o TJAP como `xfail` estrito por limitacao server-side. O site pode responder com validacao server-side do Cloudflare Turnstile; nesse caso o scraper levanta `TJAPSecurityCheckError`. Trate como bloqueio ambiental/anti-bot, nao como erro de filtros do usuario.

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
    tipo_decisao='acordaos'             # 'acordaos', 'monocraticas', 'todos'
)
```

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

`relator` aceita lista de nomes regimentais `[v0.4.0+]`. A paginacao da tabela principal de acordaos foi corrigida na 0.4.0 (antes, a pagina 2 repetia a 1), mas decisoes monocraticas ficam numa segunda tabela com paginador proprio e ainda retornam so a primeira pagina.

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

### TJGO

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

### TJRJ

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

**Gotcha BREAKING `[v0.3.0]`:** **rejeita `data_julgamento_*` e `data_publicacao_*` com `TypeError`** — o backend ASPX so expoe granularidade anual via `ano_inicio`/`ano_fim` (campos `cmbAnoInicio`/`cmbAnoFim` do form). Sem `ano_inicio`/`ano_fim`, o scraper preenche os dois com o ano corrente `[v0.4.0+]`, entao o resultado cobre so o ano corrente, nao "todos os anos". Antes da 0.4.0, a chamada sem ano recebia HTTP 500 do backend e abortava com `RetryExhaustedError`. `test_release_date_filter.py` marca o TJRJ como `xfail` estrito por limitacao server-side.

### TRFs (TRF1, TRF3, TRF5) — `cpopg` via PJe `[v0.4.0+]`

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

**Paginacao automatica de movimentacoes e documentos:** PJe pagina as tabelas com Richfaces inslider (15 linhas/pagina). O scraper detecta o slider e itera as paginas restantes via POST AJAX. Isso vale tanto para `movimentacoes` quanto para `documentos`, e garante que `download_pecas=True` nao baixe apenas as primeiras 15 pecas.

**Especializacoes por tribunal:**

- **TRF3** envia `classeJudicial`+`sgbClasseJudicial_selection` (autocomplete) e campos `dataAutuacaoDecoration`. Pode ser bloqueado por Akamai; nesse caso levanta `BotChallengeBlockedError`.
- **TRF5** envia `classeProcessualProcessoHidden` (popup picker), omite as datas, ignora reCAPTCHA renderizado (`if (false)` no `executarReCaptcha` — dead code). Tambem pode sofrer `BotChallengeBlockedError`.
- **TRF1** segue o mesmo padrao do TRF3 (autocomplete + `dataAutuacaoDecoration`); divergencia em `BASE_URL` apenas. Tambem pode sofrer `BotChallengeBlockedError`.

**Gotcha:** cada tribunal tem implementacao independente em `courts/{trf1,trf3,trf5}/`, mas compartilha a base `_trf` para o contrato atual de `cpopg`/download de pecas. Bloqueios Akamai sao ambientais/anti-bot; reduza ritmo, tente outro horario/IP, ou use Datajud quando bastarem metadados.

### TRF6 — `cpopg` via eproc/SJMG `[v0.4.0+]`

O TRF6 acessa o eproc de 1º grau da Seção Judiciaria de Minas Gerais (`https://eproc1g.trf6.jus.br/eproc/`). O formulario exige captcha textual em imagem PNG embutida no HTML e validada server-side; o scraper resolve via `txtcaptcha` e refaz o GET do form a cada tentativa porque o captcha e vinculado ao cookie `PHPSESSID`.

```python
trf6 = jus.scraper('trf6', max_captcha_attempts=3)
df = trf6.cpopg(id_cnj='1000149-71.2024.4.06.3800')
```

**Construtor:** `(verbose=0, download_path=None, sleep_time=1.0, max_captcha_attempts=3)`.

**Retorna:** `pd.DataFrame` com uma linha por processo. Colunas: `id_cnj`, `processo`, `classe`, `data_autuacao`, `situacao`, `magistrado`, `orgao_julgador`, `assuntos`, `polo_ativo`, `polo_passivo`, `mpf`, `perito`, `movimentacoes`. Processos nao encontrados devolvem linha so com `id_cnj`. **Nao documentar `download_pecas` para TRF6** — esse parametro e dos TRFs PJe acima.

**Instalacao:** `[v0.4.0+]`. `txtcaptcha` nao faz parte das dependencias base: use `pip install -U 'juscraper[tjmg]'` (o extra declara `txtcaptcha`) ou `pip install txtcaptcha`. Sem ele, `cpopg` levanta `ImportError` pedindo o pacote.

### STF (busca de jurisprudencia) `[v0.4.0+]`

Raspa a busca de jurisprudencia do portal `jurisprudencia.stf.jus.br` (acordaos e decisoes monocraticas), com o mesmo corpo de requisicao que o site envia (jtrecenti/juscraper#345).

**Instalacao e cookie do WAF:** o portal fica atras de um desafio JavaScript do AWS WAF. O scraper obtem o cookie `aws-waf-token` com Playwright na primeira busca e o renova quando o WAF volta a desafiar; as buscas seguem em `requests`.

```bash
pip install -U 'juscraper[stf]'
playwright install chromium
```

Alternativa sem Playwright: passar um cookie ja obtido no navegador em `jus.scraper('stf', waf_token='...')`. Instanciar o scraper nao exige nenhum dos dois; sem ambos, a primeira chamada de `listar_decisoes`/`contar_decisoes` levanta `ImportError`.

```python
stf = jus.scraper('stf', waf_token=None, verbose=0, sleep_time=1.0)

df = stf.listar_decisoes(
    pesquisa='pejotização',           # None = tudo o que os filtros selecionam
    paginas=range(1, 3),              # 1-based; None = todas (ver teto abaixo)
    base='acordaos',                  # 'decisoes' (monocraticas, default) ou 'acordaos'
    classe='Rcl',                     # sigla da classe; str ou list[str]
    inteiro_teor=False,               # True pesquisa tambem no inteiro teor
    data_julgamento_inicio=None, data_julgamento_fim=None,
    data_publicacao_inicio=None,
    data_publicacao_fim='20/08/2023',
    tamanho_pagina=250                # 1 a 250; default 250
)

contagem = stf.contar_decisoes(pesquisa='pejotização', base='acordaos')
```

**`listar_decisoes` retorna** `pd.DataFrame` com uma linha por documento: `processo`, `classe`, `relator`, `data_julgamento`, `data_publicacao`, `ementa` (acordaos), `decisao_texto` (monocraticas), `inteiro_teor_url` e o restante do `_source` da API. No `dataframeit`, o texto das monocraticas esta em `decisao_texto`, que a inferencia de `text_column` nao encontra: passe `text_column=` explicito.

**`contar_decisoes` retorna** `pd.DataFrame` com colunas `faceta`, `valor` e `n`, sem baixar documentos. A primeira linha e `faceta='total'`; as demais sao facetas do portal (base, ministro, classe, UF de procedencia, orgao julgador e indicadores). Uma decisao pode ter mais de um ministro, entao a soma da faceta de ministro pode passar do total. Aceita os mesmos filtros de `listar_decisoes`, exceto `tamanho_pagina` (que vira `TypeError`).

**Sintaxe de `pesquisa`:** a do portal. `$` e curinga (`terceiriz$` vira `terceiriz*`); `e`, `ou` e `nao`/`não` como palavras soltas viram `AND`, `OR` e `NOT`; `AND`/`OR`/`NOT`, `?`, `~` e parenteses passam como sintaxe do Elasticsearch. Trechos entre aspas ficam intactos, sem funcao de operador.

**Teto de 10.000 registros na 0.4.0:** a API so entrega os 10.000 primeiros registros de uma busca, com no maximo 250 por pagina. Pagina que comeca depois do registro 10.000 levanta `ValueError` antes de qualquer requisicao. Com `paginas=None` e mais de 10.000 resultados, `listar_decisoes` emite `UserWarning` e devolve so os 10.000 primeiros; divida a busca por intervalo de datas para obter o resto. `tamanho_pagina` fora de 1-250 vira `ValidationError`. Rode `contar_decisoes` antes para saber se a busca passa do teto.

**Na `main`, ainda sem release `[unreleased]`** (jtrecenti/juscraper#347, #348, #349; instalar com `pip install "juscraper[stf] @ git+https://github.com/jtrecenti/juscraper.git"`):

- `paginas=None` deixa de truncar: divide buscas acima do teto em janelas de datas disjuntas (datas de publicacao quando ha filtro de publicacao; senao, de julgamento) e devolve todas as linhas ou levanta erro. Um unico dia acima do teto, residual sem data acima do teto, IDs faltando ou duplicados e contagens divergentes levantam `ValueError`. Paginas explicitas mantem os offsets e a ordem do portal e nao disparam a divisao.
- Coleta integral (`paginas=None`) ordena so por `id`, sem o score de relevancia, que varia entre replicas do indice e fazia a paginacao repetir ou pular documentos.
- Datas abertas deixam de receber limites artificiais (01/01/1990 ou hoje); na 0.4.0, o STF ainda autopreenche datas parciais como os demais tribunais.
- `listar_decisoes` aceita `checkpoint_dir=` (diretorio de paginas e manifesto) e `resume=True` para retomar coleta interrompida. Sem `checkpoint_dir`, nada e gravado. Diretorio ocupado so aceita retomada compativel (mesma pesquisa, filtros, paginas, `tamanho_pagina` e ordenacao); checkpoint incompativel ou corrompido levanta `ValueError`, e checkpoints gravados com a ordenacao anterior sao recusados. A trava de concorrencia usa `fcntl`, entao o checkpoint exige sistema POSIX (nao roda no Windows); use diretorio local, nao montagem de rede, cuja semantica de trava e de durabilidade difere. `contar_decisoes` nao aceita `checkpoint_dir` nem `resume`.
- Resposta parcial da API (timeout da busca ou shards falhos) levanta `RuntimeError` em vez de devolver resultado incompleto.
- O filtro `classe` passa a valer tambem nas facetas de base e de indicadores de `contar_decisoes` (a faceta de classe continua ignorando o proprio filtro, como no portal).
- A obtencao e a renovacao do cookie funcionam com loop asyncio ativo, inclusive em notebooks Jupyter.

**Gotchas:**

- Se o WAF desafiar de novo logo apos a renovacao do cookie, o scraper levanta `RuntimeError`; espere alguns minutos antes de tentar outra vez.
- `classe` recebe a **sigla** da classe processual (`'Rcl'`, `'ADI'`), nao codigo numerico da TPU.
- Para metadados processuais do STF (sem texto), o Datajud continua servindo; para ementas e decisoes, use este scraper.

---

## TJSP — Detalhes extras

Unico tribunal com suporte completo (cpopg + cposg + cjsg + cjpg).

Detalhes de endpoints exclusivos (`cjpg`, parametro `method`), diferencas da `cjsg` (`baixar_sg`, `pesquisa=""`), cobertura temporal validada, `QueryTooLongError` e `auto_chunk` movidos para a reference dedicada **`references/tjsp.md`**.

Convencao da skill: cada tribunal pode ter sua propria reference a medida que especificidades sejam validadas (ex: `tjsp.md`, futuramente `tjrs.md`, `tjpr.md` etc.). Este arquivo (`tribunais.md`) mantem a matriz comparativa e os parametros da `cjsg` por familia de plataforma.

---

## Gotchas comuns

1. **`paginas=None` baixa TODAS as paginas** — para buscas amplas pode gerar milhares de requisicoes. Sempre prefira um range explicito.

2. **`sleep_time=0` causa bloqueio** — os tribunais detectam acesso agressivo.

3. **cpopg/cposg retornam dict, cjsg/cjpg retornam DataFrame** — nao trate todos igual. Excecao: `cpopg` dos TRFs retorna DataFrame (uma linha por processo), nao dict.

4. **Numero CNJ: separadores opcionais mas zeros a esquerda importam** — `1000149-71.2024.8.26.0346` e `10001497120248260346` sao aceitos.

5. **TJDFT `[v0.3.0]` agora aceita filtros de data** — o que mudou: antes ignorava `data_julgamento_*` com `UserWarning`; agora envia `termosAcessorios="entre X e Y"` ao backend.

6. **Formatos de data `[v0.3.0]`:** em endpoints com schema pydantic wired, aceita `DD/MM/AAAA`, `DD-MM-AAAA`, `AAAA-MM-DD`, `AAAA/MM/DD` e objetos `datetime.date`/`datetime.datetime`. Antes era estritamente o formato declarado pelo backend de cada tribunal.

7. **Filtros parciais auto-completam `[v0.4.0+]`:** informar apenas `data_*_inicio` ou apenas `data_*_fim` faz o outro lado virar respectivamente "hoje" ou `01/01/1990`. Emite `UserWarning`.

8. **cposg do TJSP com `method='api'`** — o parse JSON nao esta implementado. Use `'html'`.

9. **JusBR e PDPJ exigem autenticacao antes de qualquer chamada.** Detalhes em `references/agregadores.md`.

10. **Datajud requer `tribunal` ou `numero_processo`** — `[v0.3.0]` BREAKING: sem nenhum dos dois, agora levanta `ValueError` em vez de retornar DataFrame vazio.

11. **Aliases depreciados emitem `DeprecationWarning`** — sempre use o nome canonico (`pesquisa`, `data_julgamento_inicio`, `tamanho_pagina`, `classe`, `assunto`, `vara`, `numero_processo`, `relator`, `id_classe`). Tabela completa em `references/api.md`.

12. **`RetryExhaustedError` em `HTTPScraper` `[v0.4.0+]`:** na 0.4.0, o `cjsg` dos 25 tribunais estaduais (familia eSAJ e todos os demais), o `cjpg` de TJES/TJTO, o `cpopg` de TRF1/TRF3/TRF5, o STF e o agregador ComunicaCNJ migraram para `HTTPScraper` e propagam a excecao. Datajud e JusBR herdam `HTTPScraper`, mas nao a propagam: o Datajud usa o retry proprio da `call_datajud_api` e devolve `None` com `UserWarning` quando falha; o JusBR captura a excecao nos `fetch_*` internos e devolve `None`. TRF6 e PDPJ ficaram fora. Quando esgota `max_retries` em 403/429/5xx persistente, a excecao propagada e `juscraper.core.exceptions.RetryExhaustedError` em vez de `requests.HTTPError`/`requests.RequestException`. Para codigo defensivo, capture ambas.

13. **`auto_chunk=True` substitui workaround manual de iteracao por ano `[v0.3.0]`:** na familia eSAJ (TJSP/TJAC/TJAL/TJAM/TJCE/TJMS `cjsg`, TJSP `cjpg`), janelas `data_julgamento_*` maiores que 366 dias agora sao automaticamente divididas em chunks e concatenadas com dedup. O `pd.concat([cjpg(...) for ano in range(...)])` antigo ja nao e necessario para esse caso. Para o comportamento antigo (`ValueError` em janelas longas), passar `auto_chunk=False`.

14. **Colunas BREAKING em TJES/TJMT/TJRS/TJRN/TJPE/TJRO `[v0.3.0]`:** alguns DataFrames trocaram nomes de coluna (`processo`, `classe`, `assunto`, `relator` substituem `nr_processo`/`numero_unico`, `classe_cnj`/`classe_judicial`, `assunto_cnj`/`assunto_principal`, `magistrado`). Codigo que acessa colunas pelo nome antigo precisa ser atualizado. Em particular, ao integrar com `dataframeit` (`text_column=...`), conferir o DataFrame retornado.

15. **`extra="forbid"` em todos os endpoints wired `[v0.3.0]`:** kwarg desconhecido vira `TypeError` com sugestao de typo. Antes, kwargs nao reconhecidos eram silenciosamente ignorados (bug silencioso de raspagem nao-filtrada).
