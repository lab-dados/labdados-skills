# Agregadores — Datajud, JusBR, ComunicaCNJ, PDPJ

Quatro fontes nacionais que cobrem multiplos tribunais a partir de um unico endpoint. Cada uma resolve um problema diferente — escolha pela tabela abaixo.

## Quando usar cada agregador

| Agregador | Quando usar | Autenticacao | Status |
|---|---|---|---|
| **Datajud** | Listar/contar processos em qualquer tribunal (estaduais, federais, superiores, trabalho, eleitoral) por sigla ou por numero CNJ. Metadados sem texto. | Nenhuma (API key publica embutida) | Estavel desde v0.1.x |
| **JusBR** | Consultar processo por CNJ em **qualquer tribunal** e **baixar texto das pecas** (`download_documents`). Para texto integral em processos da Justica Estadual ou Federal. | Obrigatoria (JWT do gov.br) | Estavel desde v0.1.x |
| **ComunicaCNJ** | Coletar **comunicacoes processuais** publicadas pelos tribunais no PJe (DJe digital, intimacoes publicas). Util para acompanhar publicacoes em determinado tema sem percorrer Diarios Oficiais. | Nenhuma | `[v0.3.0+]` |
| **PDPJ** | Consulta unificada via API DATALAKE do PDPJ (mesmo SSO do PJe). Substitui parcialmente JusBR e oferece endpoints granulares: existe, cpopg, documentos, movimentos, partes, pesquisa, contar, download_documents. | Obrigatoria (JWT do PDPJ via SSO PJe) | `[unreleased]` — instalar via `pip install git+https://github.com/jtrecenti/juscraper.git` |

Comparativo de capacidade:

| Capacidade | Datajud | JusBR | ComunicaCNJ | PDPJ |
|---|:---:|:---:|:---:|:---:|
| Metadados de processo (cpopg) | parcial (sem texto) | sim | nao | sim |
| Texto integral de pecas | nao | sim | nao | sim |
| Consultar por nome de parte / OAB | nao | nao | nao | sim (`pesquisa`) |
| Comunicacoes/intimacoes publicas | nao | nao | sim | nao |
| Filtro por tipo de movimentacao | sim (`tipos_movimentacao`) | nao | nao | nao |
| Consultar varios tribunais numa chamada | sim (multi-alias) | um por vez | sim | um por vez |
| Auth | nenhuma | JWT gov.br | nenhuma | JWT PDPJ |

## Datajud — API publica do CNJ

API centralizada baseada em Elasticsearch. Cobre 40+ tribunais.

**Tribunais mapeados:**
- **Estaduais:** TJAC, TJAL, TJAM, TJAP, TJBA, TJCE, TJDFT, TJES, TJGO, TJMA, TJMG, TJMS, TJMT, TJPA, TJPB, TJPE, TJPI, TJPR, TJRJ, TJRN, TJRO, TJRR, TJRS, TJSC, TJSE, TJSP, TJTO
- **Federais:** TRF1, TRF2, TRF3, TRF4, TRF5, TRF6
- **Superiores:** STF, STJ, TST, TSE
- **Trabalho:** TRT1 a TRT24 — `[v0.3.0]` completou todos os 24 mappings
- **Eleitoral:** TRE-AC a TRE-TO (27 tribunais) — `[v0.3.0]` completou todos os mappings
- **Militar:** STM, TJMMG, TJMRS, TJMSP

**Deteccao automatica de tribunal**: quando `numero_processo` e fornecido sem `tribunal`, o Datajud extrai o tribunal dos digitos `J.TT` do proprio CNJ.

### Construtor

```python
datajud = jus.scraper('datajud',
    api_key=None,        # None = usa chave publica embutida
    verbose=1,           # 0 = silencioso
    download_path=None,  # diretorio temporario
    sleep_time=0.5
)
```

### `listar_processos`

```python
df = datajud.listar_processos(
    # Identificacao
    numero_processo=None,         # str ou list[str] — CNJ(s)
    tribunal=None,                # sigla (ex: 'TJSP', 'TRF1', 'STJ')

    # Filtros temporais (mutuamente exclusivos entre si)
    ano_ajuizamento=None,         # int (ex: 2023)
    data_ajuizamento_inicio=None, # 'YYYY-MM-DD'   [v0.3.0+]
    data_ajuizamento_fim=None,    # 'YYYY-MM-DD'   [v0.3.0+]

    # Filtros de conteudo
    classe=None,                  # codigo CNJ da classe
    assunto=None,                 # list[int|str] — codigos TPU (singular canonico; `assuntos` aceito como alias deprecado)
    tipos_movimentacao=None,      # list[str] — nomes amigaveis [v0.3.0+]:
                                  #   'decisao', 'sentenca', 'julgamento', 'tutela', 'transito_julgado'
    movimentos_codigo=None,       # list[int|str] — codigos TPU diretos [v0.3.0+]
    orgao_julgador=None,          # match em orgaoJulgador.nome [v0.3.0+]

    # Escape-hatch (mutuamente exclusivo com filtros amigaveis acima)
    query=None,                   # dict — query Elasticsearch literal [v0.3.0+]
                                  # exige tribunal explicito

    # Resposta
    mostrar_movs=False,           # incluir movimentos no _source
    paginas=None,                 # 1-based, range/list/int/None
    tamanho_pagina=5000           # default subiu para 5000 em [v0.3.0]
)
```

**Requer:** `tribunal` OU `numero_processo` (pelo menos um). `[v0.3.0]` **BREAKING**: faltar os dois agora levanta `ValueError` em vez de devolver DataFrame vazio. Sigla nao mapeada tambem vira `ValueError`.

**Filtros expandidos `[v0.3.0]`:**

```python
# Range de data ajuizamento + categoria de movimentacao
df = datajud.listar_processos(
    tribunal='TRF1',
    data_ajuizamento_inicio='2024-01-01',
    data_ajuizamento_fim='2024-03-31',
    tipos_movimentacao=['decisao', 'sentenca'],
    paginas=range(1, 3)
)

# Escape-hatch: query Elasticsearch arbitraria
df = datajud.listar_processos(
    tribunal='TRF1',
    query={
        'bool': {
            'must_not': [{'exists': {'field': 'orgaoJulgador.nome'}}],
            'should': [{'match': {'classe.nome': 'tutela'}}],
            'minimum_should_match': 1
        }
    },
    paginas=1
)
```

**Retorna:** `pd.DataFrame` com uma linha por processo. Colunas tipicas (camelCase do CNJ): `classe`, `numeroProcesso`, `sistema`, `formato`, `tribunal`, `dataHoraUltimaAtualizacao`, `grau`, `dataAjuizamento`, `movimentos` (se `mostrar_movs=True`), `id`, `nivelSigilo`, `orgaoJulgador`, `assuntos`.

### `contar_processos` `[v0.3.0]`

Conta processos sem baixar nenhum documento (mais leve que `listar_processos`). Aceita o mesmo conjunto de filtros (exceto `paginas`/`tamanho_pagina`/`mostrar_movs`).

```python
df_count = datajud.contar_processos(tribunal='TJSP', ano_ajuizamento=2023, classe='436')
#   tribunal             alias  count relation error
# 0     TJSP  api_publica_tjsp  12345       eq   None
```

Retorna uma linha por tribunal: `tribunal`, `alias` (indice ES), `count`, `relation` (`"eq"` exato ou `"gte"` truncado), `error`. Util para checagem de viabilidade antes de uma raspagem grande.

### Gotchas

- **Tamanho de pagina:** default de `5000` (subiu em v0.3.0). Em caso de `HTTP 504`/`Timeout`, o client refaz com `size // 4` automaticamente (1 retry com `UserWarning`); valores proximos de 10000 sao instaveis. Por isso `paginas=None` num tribunal grande pode demorar.
- **Alias plural `assuntos`** (e `classes` em TJBA) e aceito com `DeprecationWarning` (`[v0.3.0]`); nome canonico singular e `assunto` (e `classe`). Passar plural + singular juntos -> `ValueError` (`[unreleased]`). `assunto` aceita `int | str | list[int|str]`; `movimentos_codigo` aceita `int | str | list[int|str]`.
- **CNJ com whitespace ou separadores** (vindos de CSV/Excel) sao limpos automaticamente antes do envio. `[v0.3.0]`
- **Problemas de runtime** (CNJ invalido, tribunal nao mapeado, falha de API, JSON corrompido) emitem `warnings.warn(UserWarning)` alem do log — em Jupyter sem handler de logging, fica visivel. `[v0.3.0]`
- **`RetryExhaustedError`**: `[unreleased]` o `DatajudScraper` agora herda de `HTTPScraper`; a forma de transporte central nao muda (504/timeout continua usando o retry especializado da `call_datajud_api`), mas algumas falhas podem propagar `juscraper.core.exceptions.RetryExhaustedError` em vez de `requests.HTTPError`. Para codigo defensivo, capturar ambas.
- **`data_inicio`/`data_fim` NAO sao aceitos** no Datajud — esses aliases mapeiam para `data_julgamento_*` em scrapers de jurisprudencia, e o Datajud filtra por **ajuizamento**, nao julgamento. Use `data_ajuizamento_inicio`/`_fim`. `extra="forbid"` faz quem usar o nome generico receber `TypeError` direto.

---

## JusBR — Plataforma Digital do Poder Judiciario (PDPJ Legacy)

Portal unificado mantido pelo CNJ. Consulta processos de **qualquer tribunal** e permite **baixar o texto dos documentos/pecas**.

### Construtor

```python
jusbr = jus.scraper('jusbr',
    verbose=0,
    download_path=None,
    sleep_time=0.5,
    token=None           # JWT — pode passar aqui ou via .auth() depois
)
```

### Autenticacao (obrigatoria)

```python
jusbr = jus.scraper('jusbr')

# Opcao 1: token manual
jusbr.auth(token='eyJhbGciOiJSUzI1NiIs...')

# Opcao 2: via cookies do Firefox (requer sessao ativa no jus.br)
jusbr.auth_firefox()
```

Onde obter o token: acessar https://www.jus.br, fazer login via gov.br, abrir DevTools > Network, capturar a requisicao para a API e copiar o campo `access_token` do header `Authorization: Bearer <token>`.

Tokens JWT expiram. `[unreleased]` `auth(token)` valida explicitamente o claim `exp`: token expirado levanta `ValueError("Token JWT expirado.")`; token sem `exp` continua aceito. Se der erro de autenticacao, peca ao usuario um novo token.

### `cpopg`

```python
df = jusbr.cpopg(id_cnj='3005317-12.2025.8.06.0000')   # str ou list[str]
```

**Retorna:** `pd.DataFrame` com coluna canonica `processo`, alem de `numeroProcesso`, `idCodexTribunal`, `detalhes` (dict com metadados completos), `status_consulta`. Em linhas de fallback, `processo_pesquisado` pode aparecer como sinonimo historico, mas codigo novo deve usar `processo`.

### `download_documents`

```python
df_docs = jusbr.download_documents(
    base_df=resultado_cpopg,     # DataFrame retornado por cpopg()
    max_docs_per_process=None    # int ou None (todos)
)
```

**Retorna:** `pd.DataFrame` onde cada linha e um documento, com colunas `numero_processo`, `idDocumento`, `descricao`, `nome`, `tipo`, `dataHoraJuntada`, `nivelSigilo`, `hrefTexto`, `hrefBinario`, `texto` (conteudo extraido), `_raw_text_api`, `_raw_binary_api`. `[unreleased]` O downloader e tolerante a disponibilidade parcial: baixa o que existir quando ha so texto ou so binario; quando ambos os links faltam, pula o documento.

### Workflow completo

```python
jusbr = jus.scraper('jusbr')
jusbr.auth(token='...')

# 1. Buscar metadados do processo
resultado = jusbr.cpopg('3005317-12.2025.8.06.0000')

# 2. Baixar documentos desse processo
docs = jusbr.download_documents(resultado)
print(docs[['numero_processo', 'descricao', 'texto']].head())
```

### Gotchas

- **`RetryExhaustedError`**: `[unreleased]` o `JusbrScraper` agora herda de `HTTPScraper`. O contrato publico nao muda (os `fetch_*` internos capturam `RetryExhaustedError` e devolvem `None`, mantendo "erro -> None"). Mas se voce instrumentar codigo de baixo nivel para capturar excecoes do `download.py`, deve capturar `RetryExhaustedError` em vez de `requests.HTTPError` direto.
- **Token expirado** `[unreleased]` vira `ValueError("Token JWT expirado.")` ja em `auth(token)` quando o claim `exp` existe; peca novo token ao usuario.
- **Listar por nome de parte / OAB:** nao e suportado pelo JusBR. Para isso, use o **PDPJ** abaixo.

---

## ComunicaCNJ — Comunicacoes processuais publicas `[v0.3.0+]`

API publica do CNJ para acessar **comunicacoes processuais** publicadas via PJe (intimacoes, DJe digital). Util para acompanhar publicacoes em um tema sem percorrer Diarios Oficiais.

**Endpoint:** `https://comunicaapi.pje.jus.br/api/v1/comunicacao`

### Construtor

```python
cnj = jus.scraper('comunica_cnj',   # nota: underline, nao hifen
    verbose=1,                       # 0 = silencioso
    sleep_time=0.5
)
```

Construtor **nao aceita** `download_path` (a API e leve, sem arquivos intermediarios).

### `listar_comunicacoes`

```python
df = cnj.listar_comunicacoes(
    pesquisa='resolucao',                          # obrigatorio
    paginas=range(1, 4),                           # 1-based; None = todas
    data_disponibilizacao_inicio='2024-01-01',     # 'YYYY-MM-DD' ou 'DD/MM/YYYY'
    data_disponibilizacao_fim='2024-01-31',
    itens_por_pagina=100                           # 1-100 (default 100, max 100)
)
```

**Por que os nomes sao `data_disponibilizacao_*` e nao `data_inicio/fim`:** o ComunicaCNJ filtra por **data de disponibilizacao** no Diario Eletronico, nao por data de julgamento. O alias generico `data_inicio`/`data_fim` no projeto mapeia para `data_julgamento_*` em scrapers de jurisprudencia — usar o nome canonico explicito evita ambiguidade.

**Retorna:** `pd.DataFrame` com uma linha por comunicacao. Colunas refletem o JSON `items` da API (`numero_processo`, `siglaTribunal`, `texto`, `link`, etc.).

### Gotchas

- **Datas em dois formatos** (ISO e BR) sao aceitas e convertidas para ISO antes do schema. Intervalo invalido (fim antes de inicio) levanta `ValueError`.
- **`pesquisa` e obrigatorio.** Faltar gera `ValidationError`.
- **`RetryExhaustedError`** ao esgotar `max_retries` em 429/5xx persistente — `ComunicaCNJ` migrou para `HTTPScraper` em `[unreleased]`. Antes, 429/5xx propagava `requests.HTTPError`; agora propaga `juscraper.core.exceptions.RetryExhaustedError`. Codigo defensivo: capturar ambas. Este retry cobre 429/5xx; `pesquisa` ausente ou intervalo invalido continuam erros de input.

---

## PDPJ — DATALAKE Processos `[unreleased]`

Agregador novo `[unreleased]` para a API DATALAKE - Processos do PDPJ (`https://api-processo-integracao.data-lake.pdpj.jus.br/processo-api/api/v1`). Sucessor parcial do JusBR. **Usa o JWT do SSO do PJe — nao e o mesmo token do JusBR**, que consome o JWT do SSO do gov.br. Sao tokens distintos, embora o fluxo de captura via DevTools seja analogo. Oferece endpoints granulares e suporte a busca por nome de parte / OAB.

**Instalacao obrigatoria via dev:** `pip install git+https://github.com/jtrecenti/juscraper.git`

### Construtor

```python
pdpj = jus.scraper('pdpj',
    verbose=0,
    download_path=None,
    sleep_time=0.5,
    token=None           # JWT — pode passar aqui ou via .auth() depois
)
```

### Autenticacao

```python
pdpj = jus.scraper('pdpj')
pdpj.auth(token='eyJhbGciOiJSUzI1NiIs...')
```

O token e um JWT emitido pelo SSO do PJe (diferente do JWT do gov.br que o JusBR usa — ver nota acima). Obter pelo portal PDPJ logado (DevTools > Network > capturar header `Authorization: Bearer <token>`).

A autenticacao valida o formato e detecta tokens expirados antes de tentar usar:
- Token malformado -> `ValueError("Token JWT invalido: ...")`.
- Token expirado -> `ValueError("Token JWT expirado.")`.

### Endpoints

| Metodo | Para que serve | Retorno |
|---|---|---|
| `existe(id_cnj)` | Checa se o processo existe no Data Lake (rapido) | `bool` para `str`; `DataFrame[processo, existe]` para `list[str]` |
| `cpopg(id_cnj)` | Detalhes do processo (uma linha por tramitacao) | `DataFrame[processo, numero_processo, id, sigla_tribunal, segmento_justica, nivel_sigilo, data_atualizacao, detalhes, status_consulta]` |
| `documentos(id_cnj)` | Lista documentos do processo (sem texto) | `DataFrame` (uma linha por documento) |
| `movimentos(id_cnj)` | Lista movimentos do processo | `DataFrame` |
| `partes(id_cnj)` | Lista partes do processo | `DataFrame` |
| `pesquisa(paginas=None, **filtros)` | Busca profunda em `/processos` (filtros por parte, OAB, classe, assunto, orgao, etc.) | `DataFrame` |
| `contar(**filtros)` | Conta processos para os mesmos filtros de `pesquisa` | `int` |
| `download_documents(base_df, ...)` | Baixa textos e/ou binarios dos documentos | `DataFrame` |

### `pesquisa` — filtros principais

```python
df = pdpj.pesquisa(
    paginas=range(1, 4),
    numero_processo=None,
    numero_processo_sintetico=None,
    cpf_cnpj_parte=None,             # com formatacao
    nome_parte=None,
    polo_parte=None,                 # 'ATIVO' ou 'PASSIVO'
    situacao_parte=None,
    nome_representante=None,
    oab_representante=None,
    id_classe=None,                  # codigos separados por virgula
    id_assunto_judicial=None,        # ids separados por virgula
    id_orgao_julgador=None,          # str ou list[str]
    instancia=None,                  # 'PRIMEIRO_GRAU' | 'SEGUNDO_GRAU' | ...
    segmento_justica=None,           # 'JUSTICA_FEDERAL' | 'JUSTICA_ESTADUAL' | ...
    tribunal=None,                   # siglas separadas por virgula (max 5)
    data_atualizacao_inicio=None,    # ISO datetime
    data_atualizacao_fim=None,
    data_primeiro_ajuizamento_inicio=None,
    data_primeiro_ajuizamento_fim=None,
    campo_ordenacao=None,            # campo de ordenacao decrescente
    itens_por_pagina=100             # max 100
)
```

A paginacao usa cursor `searchAfter` (forwards-only) — o client itera ate exaurir ou atingir o limite solicitado em `paginas`.

### `download_documents`

```python
df_docs = pdpj.download_documents(
    base_df=resultado_documentos_ou_cpopg,
    max_docs_per_process=None,
    with_text=True,                  # baixa texto via /documentos/{id}/texto
    with_binary=False                # baixa binario via /documentos/{id}/binario
)
```

`base_df` pode vir tanto de `pdpj.documentos(...)` (uma linha por documento, ja com `id_documento`) quanto de `pdpj.cpopg(...)` (uma linha por processo — o client extrai documentos de `detalhes['documentos']` ou `detalhes['tramitacoes'][*]['documentos']`).

Pelo menos um de `with_text` ou `with_binary` deve ser `True` (senao `ValueError`).

### Workflow tipico

```python
pdpj = jus.scraper('pdpj')
pdpj.auth(token='...')

# Caminho A: ja tenho lista de CNJs
docs = pdpj.documentos(['1000149-71.2024.8.26.0346', '...'])
texts = pdpj.download_documents(docs, max_docs_per_process=20)

# Caminho B: busca por parte/OAB e depois baixa pecas
processos = pdpj.pesquisa(
    nome_parte='Joao da Silva',
    tribunal='TJSP',
    instancia='PRIMEIRO_GRAU',
    paginas=range(1, 3)
)
docs = pdpj.documentos(processos['processo'].tolist())
texts = pdpj.download_documents(docs)
```

### PDPJ vs JusBR — qual usar?

| Criterio | JusBR | PDPJ |
|---|---|---|
| Status | Estavel | `[unreleased]` |
| Auth | JWT gov.br | JWT PDPJ (mesmo SSO PJe) |
| cpopg por CNJ | sim | sim |
| Download de pecas | sim (texto) | sim (texto e/ou binario, granular) |
| Busca por nome de parte/OAB | nao | sim (`pesquisa`) |
| Contagem rapida | nao | sim (`contar`) |
| Endpoints granulares (`existe`/`movimentos`/`partes`) | nao | sim |

Se ja esta implementado com JusBR, nao ha necessidade de migrar. Para casos novos com requisitos de busca por parte/OAB ou contagem pre-coleta, PDPJ e a opcao mais rica — assumindo que o usuario aceita instalar pela `main`.

### Gotchas

- **Token expirado:** detectado na hora do `auth()` (vira `ValueError("Token JWT expirado.")`) e nao apenas na primeira chamada.
- **`existe` retorna tipos diferentes** conforme o input: `bool` quando recebe `str`, `DataFrame` quando recebe `list[str]`. Pense duas vezes antes de usar em codigo generico.
- **Cursor `searchAfter` em `pesquisa`** e forwards-only — `paginas=[3, 5]` baixa as paginas 3, 4 e 5 contiguamente (nao pula a 4).
- **Validacao `extra="forbid"`** em todos os endpoints: kwarg desconhecido vira `TypeError` com sugestao de typo via difflib (ex: `data_juglamento` -> "voce quis dizer 'data_julgamento'?").
