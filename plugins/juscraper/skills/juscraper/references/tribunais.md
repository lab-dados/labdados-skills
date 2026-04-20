# Tribunais — Matriz de Capacidades e Parametros

## Matriz de capacidades

### Tribunais com scraper direto (22)

| Tribunal | cjsg | cjpg | cpopg | cposg | Plataforma |
|----------|:----:|:----:|:-----:|:-----:|------------|
| **TJSP** | sim | sim | sim | sim | eSAJ + API REST |
| **TJES** | sim | sim | - | - | PJe/Solr API |
| **TJTO** | sim | sim | - | - | Custom HTML |
| **TJAC** | sim | - | - | - | eSAJ |
| **TJAL** | sim | - | - | - | eSAJ |
| **TJAM** | sim | - | - | - | eSAJ |
| **TJAP** | sim | - | - | - | Tucujuris REST |
| **TJBA** | sim | - | - | - | GraphQL |
| **TJCE** | sim | - | - | - | eSAJ |
| **TJDFT** | sim | - | - | - | REST API |
| **TJMS** | sim | - | - | - | eSAJ |
| **TJMT** | sim | - | - | - | REST API |
| **TJPA** | sim | - | - | - | BFF REST API |
| **TJPB** | sim | - | - | - | PJe/Elasticsearch |
| **TJPE** | sim | - | - | - | HTML form |
| **TJPI** | sim | - | - | - | HTML server-rendered |
| **TJPR** | sim | - | - | - | HTML form + sessao |
| **TJRN** | sim | - | - | - | PJe/Elasticsearch |
| **TJRO** | sim | - | - | - | JURIS/Elasticsearch |
| **TJRR** | sim | - | - | - | JSF/PrimeFaces |
| **TJRS** | sim | - | - | - | Google Search (GSA) |
| **TJSC** | sim | - | - | - | eproc HTML |

### Agregadores (2)

| Agregador | Metodos | Cobertura |
|-----------|---------|-----------|
| **Datajud** | `listar_processos` | 40+ tribunais (todos os segmentos) |
| **JusBR** | `cpopg`, `download_documents` | Qualquer tribunal (requer auth) |

**Legenda:** `sim` = implementado | `-` = nao implementado

---

## Parametros da cjsg por tribunal

Todos os tribunais aceitam `pesquisa` e `paginas`. Os filtros adicionais variam.

### Tribunais eSAJ (TJSP, TJAC, TJAL, TJAM, TJCE, TJMS)

Compartilham a mesma estrutura de parametros:

```python
scraper.cjsg(
    pesquisa='dano moral',
    paginas=range(1, 4),
    ementa=None,                    # filtro por texto da ementa
    numero_recurso=None,            # numero do recurso
    classe=None,                    # classe processual
    assunto=None,                   # assunto
    comarca=None,                   # comarca (TJSP apenas)
    orgao_julgador=None,            # orgao julgador
    data_julgamento_inicio=None,    # 'DD/MM/AAAA'
    data_julgamento_fim=None,
    data_publicacao_inicio=None,    # (nao TJSP)
    data_publicacao_fim=None,
    origem=None,                    # 'T' (2o grau) ou 'R' (turma recursal)
    tipo_decisao=None               # 'acordao' ou 'monocratica'
)
```

**Construtor eSAJ:** aceita `verbose`, `download_path`, `sleep_time` (default 1.0).

**Nota TJSP:** extras em relacao aos demais eSAJ (`comarca`,
`tipo_decisao`, `baixar_sg`, `sleep_time=0.5`). Ver `references/tjsp.md`.

### TJRS

```python
tjrs.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    classe=None, assunto=None, orgao_julgador=None,
    relator=None,                       # nome do relator
    data_julgamento_inicio=None, data_julgamento_fim=None,
    data_publicacao_inicio=None, data_publicacao_fim=None,
    tipo_processo=None,
    secao=None                          # 'civel', 'crime'
)
```

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
    sinonimos=True,                     # incluir sinonimos
    espelho=True,                       # buscar no espelho
    inteiro_teor=False,                 # buscar no inteiro teor
    quantidade_por_pagina=10
)
```

**Nao suporta filtros de data.** Se passados, serao ignorados com aviso.

### TJES

```python
tjes.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    core='pje2g',                       # 'pje2g', 'pje2g_mono', 'legado', 'turma_recursal_legado'
    busca_exata=None,                   # busca exata
    magistrado=None, orgao_julgador=None,
    classe_judicial=None, jurisdicao=None, assunto=None,
    ordenacao=None, per_page=None,
    data_julgamento_inicio=None, data_julgamento_fim=None
)
# cjpg usa mesma estrutura mas com core='pje1g'
tjes.cjpg(pesquisa='...', paginas=range(1, 4))
```

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
    classes=None,                       # list de classes
    data_julgamento_inicio=None,        # 'YYYY-MM-DD'
    data_julgamento_fim=None,
    segundo_grau=None,                  # bool
    turmas_recursais=None,              # bool
    tipo_acordaos=None, tipo_decisoes_monocraticas=None,
    ordenado_por=None, items_per_page=None
)
```

**Nota:** Datas no formato **YYYY-MM-DD** (diferente do DD/MM/AAAA dos eSAJ).

### TJMT

```python
tjmt.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    tipo_consulta=None,                 # 'Acordao' ou 'DecisaoMonocratica'
    relator=None, orgao_julgador=None, classe=None,
    tipo_processo=None,                 # 'Civel' ou 'Criminal'
    thesaurus=None,
    quantidade_por_pagina=None,
    data_julgamento_inicio=None,        # 'yyyy-mm-dd'
    data_julgamento_fim=None
)
```

### TJPA

```python
tjpa.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    relator=None, orgao_julgador_colegiado=None,
    classe=None, assunto=None,
    origem=None,                        # list
    tipo=None,                          # list
    data_julgamento_inicio=None,        # 'YYYY-MM-DD'
    data_julgamento_fim=None,
    sort_by='datajulgamento',           # campo de ordenacao
    sort_order='asc',                   # 'asc' ou 'desc'
    query_type='free',                  # 'free' ou 'any'
    query_scope='ementa'                # 'ementa' ou 'inteiroteor'
)
```

### TJAP

```python
tjap.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    orgao=None, numero_cnj=None, numero_acordao=None,
    numero_ano=None, palavras_exatas=None,
    relator=None, secretaria=None, classe=None,
    votacao=None, origem=None
)
```

### TJPB

```python
tjpb.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    nr_processo=None,
    id_classe_judicial=None, id_orgao_julgador=None,
    id_relator=None,
    id_origem=None,                     # default '8,2'
    decisoes=None                       # bool
)
```

### TJPE

```python
tjpe.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    data_julgamento_inicio=None,        # 'DD/MM/YYYY'
    data_julgamento_fim=None,
    relator=None, classe_cnj=None, assunto_cnj=None,
    meio_tramitacao=None,
    tipo_decisao=None                   # 'acordaos', 'monocraticas', 'todos'
)
```

### TJPI

```python
tjpi.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    tipo=None,                          # 'Acordao', 'Decisao Terminativa', 'Sumula'
    relator=None, classe=None, orgao=None
)
```

### TJRN

```python
tjrn.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    nr_processo=None,
    id_classe_judicial=None, id_orgao_julgador=None,
    id_relator=None, id_colegiado=None,
    sistema=None,                       # 'PJE', 'SAJ', ''
    decisoes=None,                      # 'Monocraticas', 'Colegiadas', 'Sentencas', ''
    jurisdicoes=None, grau=None
)
```

### TJRO

```python
tjro.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    tipo=None,                          # list, default ['EMENTA']
    nr_processo=None,
    magistrado=None, orgao_julgador=None, orgao_julgador_colegiado=None,
    classe_judicial=None,
    instancia=None,                     # list
    termo_exato=None,                   # bool
    data_julgamento_inicio=None, data_julgamento_fim=None
)
```

### TJRR

```python
tjrr.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    relator=None,
    orgao_julgador=None,               # list
    especie=None,                       # list
    data_julgamento_inicio=None, data_julgamento_fim=None
)
```

### TJSC

```python
tjsc.cjsg(
    pesquisa='...',
    paginas=range(1, 4),
    campo=None,                         # 'E' (ementa) ou 'I' (inteiro teor)
    processo=None,                      # numero do processo
    data_julgamento_inicio=None, data_julgamento_fim=None,
    data_publicacao_inicio=None, data_publicacao_fim=None
)
```

---

## TJSP — Detalhes extras

Unico tribunal com suporte completo (cpopg + cposg + cjsg + cjpg).

Detalhes de endpoints exclusivos (`cjpg`, parametro `method`), extras
da `cjsg` (`comarca`, `tipo_decisao`, `baixar_sg`) e **cobertura
temporal validada** movidos para a reference dedicada
**`references/tjsp.md`**.

Convencao da skill: cada tribunal pode ter sua propria reference a
medida que especificidades sejam validadas (ex: `tjsp.md`,
futuramente `tjrs.md`, `tjpr.md` etc.). Este arquivo (`tribunais.md`)
mantem a matriz comparativa e os parametros da `cjsg` por familia de
plataforma.

---

## Datajud — API Publica do CNJ

API centralizada baseada em Elasticsearch. Cobre 40+ tribunais de todos os segmentos.

**Tribunais mapeados:**
- **Estaduais:** TJAC, TJAL, TJAM, TJAP, TJBA, TJCE, TJDFT, TJES, TJGO, TJMA,
  TJMG, TJMS, TJMT, TJPA, TJPB, TJPE, TJPI, TJPR, TJRJ, TJRN, TJRO, TJRR,
  TJRS, TJSC, TJSE, TJSP, TJTO
- **Federais:** TRF1, TRF2, TRF3, TRF4, TRF5, TRF6
- **Superiores:** STF, STJ
- **Militar:** STM, TJMMG, TJMRS, TJMSP
- **Outros:** CNJ

**Deteccao automatica:** quando `numero_processo` e fornecido sem `tribunal`,
o Datajud extrai o tribunal do proprio numero CNJ (digitos J.TT).

---

## JusBR — Plataforma Digital do Poder Judiciario (PDPJ)

Portal unificado do CNJ. Consulta processos de **qualquer tribunal** e permite
**baixar o texto dos documentos/pecas**.

**Autenticacao obrigatoria:**
```python
jusbr = jus.scraper('jusbr')
jusbr.auth(token='eyJhbGciOiJSUzI1NiIs...')
# ou: jusbr.auth_firefox()
```

**Workflow em 2 etapas:**
1. `cpopg(id_cnj)` → DataFrame com metadados do processo
2. `download_documents(base_df)` → DataFrame com texto dos documentos

Tokens JWT expiram — se der erro de autenticacao, peca ao usuario novo token.

---

## Gotchas comuns

1. **`paginas=None` baixa TODAS as paginas** — para buscas amplas pode gerar milhares
   de requisicoes. Sempre prefira um range explicito.

2. **`sleep_time=0` causa bloqueio** — os tribunais detectam acesso agressivo.

3. **cpopg/cposg retornam dict, cjsg/cjpg retornam DataFrame** — nao trate todos igual.

4. **Numero CNJ: separadores opcionais mas zeros a esquerda importam** —
   `1000149-71.2024.8.26.0346` e `10001497120248260346` sao aceitos.

5. **TJDFT ignora filtros de data** — nao sao suportados pela API.

6. **Formatos de data variam por tribunal:**
   - eSAJ (TJSP, TJAC, TJAL, TJAM, TJCE, TJMS): `DD/MM/AAAA`
   - TJBA, TJMT, TJPA: `YYYY-MM-DD`
   - Outros: verificar parametros especificos acima.

7. **cposg do TJSP com method='api'** — o parse JSON nao esta implementado. Use `'html'`.

8. **JusBR exige autenticacao antes de qualquer chamada** — incluindo cpopg.

9. **Datajud requer `tribunal` ou `numero_processo`** — sem nenhum dos dois,
   retorna DataFrame vazio.

10. **Aliases depreciados** — `query` e `termo` funcionam como alias de `pesquisa` em
    alguns tribunais, mas prefira sempre `pesquisa` (nome canonico).
