# Agregadores — Datajud, JusBR, ComunicaCNJ, PDPJ, Falcao

Cinco fontes nacionais que cobrem multiplos tribunais a partir de um unico endpoint. Cada uma resolve um problema diferente — escolha pela tabela abaixo.

## Quando usar cada agregador

| Agregador | Quando usar | Autenticacao | Status |
|---|---|---|---|
| **Datajud** | Listar/contar processos em qualquer tribunal (estaduais, federais, superiores, trabalho, eleitoral) por sigla ou por numero CNJ. Metadados sem texto. | Nenhuma (API key publica embutida) | Estavel desde v0.1.x |
| **JusBR** | Consultar processo por CNJ em **qualquer tribunal** e **baixar texto das pecas** (`download_documents`). Para texto integral em processos da Justica Estadual ou Federal. | Obrigatoria (JWT do SSO do PJe) | Estavel desde v0.1.x |
| **ComunicaCNJ** | Coletar **comunicacoes processuais** publicadas pelos tribunais no PJe (DJe digital, intimacoes publicas). Util para acompanhar publicacoes em determinado tema sem percorrer Diarios Oficiais. | Nenhuma | `[v0.3.0+]` |
| **PDPJ** | Consulta unificada via API DATALAKE do PDPJ (mesmo SSO do PJe). Substitui parcialmente JusBR e oferece endpoints granulares: existe, cpopg, documentos, movimentos, partes, pesquisa, contar, download_documents. | Obrigatoria (JWT do SSO do PJe) | `[v0.4.0+]` |
| **Falcao** | Jurisprudencia Nacional da Justica do Trabalho (CSJT): acordaos, sentencas, decisoes monocraticas, precedentes e recursos de revista do TST e dos 24 TRTs numa so busca (`listar_decisoes`). | Nenhuma | `[v0.5.0+]` |

Comparativo de capacidade:

| Capacidade | Datajud | JusBR | ComunicaCNJ | PDPJ |
|---|:---:|:---:|:---:|:---:|
| Metadados de processo (cpopg) | parcial (sem texto) | sim | nao | sim |
| Texto integral de pecas | nao | sim | nao | sim |
| Consultar por nome de parte / OAB | nao | nao | nao | sim (`pesquisa`) |
| Comunicacoes/intimacoes publicas | nao | nao | sim | nao |
| Filtro por tipo de movimentacao | sim (`tipos_movimentacao`) | nao | nao | nao |
| Consultar varios tribunais numa chamada | sim (multi-alias) | um por vez | sim | um por vez |
| Auth | nenhuma | JWT do SSO do PJe | nenhuma | JWT do SSO do PJe |

## Metodos por agregador

<!-- cobertura-juscraper:agregadores:inicio (gerado por scripts/cobertura_juscraper.py; nao editar a mao) -->

| Agregador | Metodos |
|---|---|
| **ComunicaCNJ** | `listar_comunicacoes` |
| **Datajud** | `contar_processos`, `listar_processos` |
| **Falcao** | `listar_decisoes` |
| **JusBR** | `cpopg`, `download_documents` |
| **PDPJ** | `cpopg`, `contar`, `documentos`, `download_documents`, `existe`, `movimentos`, `partes`, `pesquisa` |

<!-- cobertura-juscraper:agregadores:fim -->

Gerado do codigo da `main` do juscraper; a versao em que cada recurso entrou esta na coluna Status acima e nas secoes abaixo.

## Datajud — API publica do CNJ

API centralizada baseada em Elasticsearch. Cobre 40+ tribunais.

**Tribunais mapeados:**
- **Estaduais:** TJAC, TJAL, TJAM, TJAP, TJBA, TJCE, TJDFT, TJES, TJGO, TJMA, TJMG, TJMS, TJMT, TJPA, TJPB, TJPE, TJPI, TJPR, TJRJ, TJRN, TJRO, TJRR, TJRS, TJSC, TJSE, TJSP, TJTO
- **Federais:** TRF1, TRF2, TRF3, TRF4, TRF5, TRF6
- **Superiores:** STF, STJ, TST, TSE. Para jurisprudencia do STF (ementas, texto de decisoes, facetas), use o scraper proprio `jus.scraper('stf')` `[v0.4.0+]`, documentado em `references/tribunais.md` §STF; o alias do Datajud so traz metadados de processos.
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
    sleep_time=0.5,
    politica=None        # [v0.5.0+] so o timeout; ver Gotchas
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
    assunto=None,                 # list[int|str] — codigos TPU (singular canonico [v0.4.0+]; `assuntos` aceito como alias deprecado)
    tipos_movimentacao=None,      # list[str] — nomes amigaveis [v0.3.0+]:
                                  #   'decisao', 'sentenca', 'julgamento', 'tutela', 'transito_julgado'
    movimentos_codigo=None,       # list[int|str] — codigos TPU diretos [v0.3.0+]
    orgao_julgador=None,          # match em orgaoJulgador.nome [v0.3.0+]

    # Escape-hatch (mutuamente exclusivo com filtros amigaveis acima)
    query=None,                   # dict — query Elasticsearch literal [v0.3.0+]
                                  # exige tribunal explicito

    # Resposta
    mostrar_movs=False,           # incluir movimentos no _source
    paginas=None,                 # 1-based, range/list/int/None; lista esparsa vira intervalo contiguo
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
- **Alias plural `assuntos`** (e `classes` em TJBA) e aceito com `DeprecationWarning` `[v0.4.0+]`; nome canonico singular e `assunto` (e `classe`). Na 0.3.0, `assuntos` era o unico nome aceito no Datajud. Passar plural + singular juntos -> `ValueError`. `assunto` aceita `int | str | list[int|str]`; `movimentos_codigo` aceita `int | str | list[int|str]`.
- **CNJ com whitespace ou separadores** (vindos de CSV/Excel) sao limpos automaticamente antes do envio. `[v0.3.0]`
- **Problemas de runtime** (CNJ invalido, tribunal nao mapeado, falha de API, JSON corrompido) emitem `warnings.warn(UserWarning)` alem do log — em Jupyter sem handler de logging, fica visivel. `[v0.3.0]`
- **Paginacao por cursor** `[v0.4.0+]`: `paginas=range(3, 6)` devolve as paginas 3 a 5 (o scraper percorre o prefixo pelo cursor `search_after` e descarta o que nao foi pedido); antes da 0.4.0 devolvia na pratica as paginas 1 a 3. `paginas=[3, 5]` vira `range(3, 6)`. `paginas=[]`, `0`, negativos e `range` descendente levantam `ValueError` antes de qualquer requisicao.
- **Timeout** `[v0.5.0+]`: default em `jus.scraper('datajud').perfis_http['busca']` (60 s na 0.5.0), ajustavel com `politica={'busca': {'timeout': 180}}` (segundos ou o par `(conexao, leitura)`; `timeout=None` e os outros campos do perfil levantam `ValueError`). Consulta grande, como um ano inteiro de um assunto num TRF, pode passar de 60 s ja na pagina 1. O `UserWarning` de paginacao interrompida diz quantos registros vieram e quantos a consulta achou.
- **Sem `RetryExhaustedError`**: o `DatajudScraper` herda de `HTTPScraper` `[v0.4.0+]` so para sessao e headers. As requisicoes passam pela `call_datajud_api`, que tem retry proprio (504/timeout refaz uma vez com `size // 4`) e, quando a falha persiste, devolve `None` e emite `UserWarning` em vez de levantar excecao.
- **`data_inicio`/`data_fim` NAO sao aceitos** no Datajud — esses aliases mapeiam para `data_julgamento_*` em scrapers de jurisprudencia, e o Datajud filtra por **ajuizamento**, nao julgamento. Use `data_ajuizamento_inicio`/`_fim`. `extra="forbid"` faz quem usar o nome generico receber `TypeError` direto.

---

## JusBR — Plataforma Digital do Poder Judiciario (PDPJ Legacy)

Portal unificado mantido pelo CNJ. Consulta processos de **qualquer tribunal** e permite **baixar o texto dos documentos/pecas**. Autenticacao, falhas por linha e politica HTTP sao as mesmas do PDPJ: ver §"JusBR e PDPJ" abaixo.

### Construtor

```python
jusbr = jus.scraper('jusbr',
    verbose=0,
    download_path=None,
    sleep_time=0.5,
    token=None,          # JWT; ver §"JusBR e PDPJ"
    politica=None        # [v0.5.0+]; ver §"JusBR e PDPJ"
)
```

Alem de `auth(token)` e `auth_govbr()`, o JusBR tem `auth_firefox()`, que pega o token pela sessao do SSO aberta no Firefox.

### `cpopg`

```python
df = jusbr.cpopg(id_cnj='3005317-12.2025.8.06.0000')   # str ou list[str]
```

**Retorna:** `pd.DataFrame` com coluna canonica `processo` (tambem nas linhas de fallback `[v0.4.0+]`), alem de `numeroProcesso`, `idCodexTribunal`, `detalhes` (dict com metadados completos), `status_consulta` e `motivo_falha` `[v0.5.0+]`. Em linhas de fallback, `processo_pesquisado` pode aparecer como sinonimo historico, mas codigo novo deve usar `processo`. CNJ que a listagem nao acha sai com `status_consulta="Nao encontrado na lista inicial"` e `motivo_falha` `None`.

### `download_documents`

```python
df_docs = jusbr.download_documents(
    base_df=resultado_cpopg,     # DataFrame retornado por cpopg()
    max_docs_per_process=None    # int ou None (todos)
)
```

**Retorna:** `pd.DataFrame` onde cada linha e um documento, com colunas `numero_processo`, `idDocumento`, `descricao`, `nome`, `tipo`, `dataHoraJuntada`, `nivelSigilo`, `hrefTexto`, `hrefBinario`, `texto` (conteudo extraido), `_raw_text_api`, `_raw_binary_api` e `motivo_falha` `[v0.5.0+]`. O downloader e tolerante a disponibilidade parcial: baixa o que existir quando ha so texto ou so binario; quando ambos os links faltam, pula o documento. `[v0.5.0+]`: documento sem arquivo no metadado nao gera requisicao (conteudo `None`, `motivo_falha` `None`), e texto so com espacos sai `texto=None`.

Contrato `[v0.4.0+]`:

- `base_df` que nao seja `pd.DataFrame` e `max_docs_per_process` negativo levantam `ValidationError` (subclasse de `ValueError`) antes de qualquer chamada de rede; kwarg desconhecido vira `TypeError`. `max_docs_per_process=0` nao baixa nada.
- O limite vale para o processo inteiro (`numeroProcesso`), mesmo quando o processo aparece em mais de uma linha de `base_df`.
- Quando `dadosBasicos.documentos` ou `documentos` vem malformado, o downloader tenta a proxima fonte de metadados em vez de pular o processo. Metadados externos nao sobrescrevem `numero_processo`, `texto` nem as colunas brutas calculadas pelo scraper (jtrecenti/juscraper#312).

### Workflow completo

```python
jusbr = jus.scraper('jusbr')
jusbr.auth(token='...')        # se PDPJ_JWT ou o cache nao autenticaram

# 1. Buscar metadados do processo
resultado = jusbr.cpopg('3005317-12.2025.8.06.0000')

# 2. Baixar documentos desse processo
docs = jusbr.download_documents(resultado)
print(docs[['numero_processo', 'descricao', 'texto']].head())
```

### Gotchas

- **Falha de requisicao**: ver `motivo_falha` em §"JusBR e PDPJ". Na 0.4.0, virava "Nao encontrado na lista inicial" no `cpopg` e `texto=None` no `download_documents`, sem motivo.
- **Listar por nome de parte / OAB:** nao e suportado pelo JusBR. Para isso, use o **PDPJ** abaixo.

---

## JusBR e PDPJ — autenticacao, falhas por linha e politica HTTP

### Autenticacao (obrigatoria, o mesmo token nos dois)

JusBR e PDPJ usam o mesmo token: o JWT do SSO do PJe, obtido com login gov.br no portal de servicos do PDPJ. Sem token, a primeira consulta levanta `RuntimeError("Autenticacao necessaria...")`. Caminhos, do mais facil ao manual:

1. **Ja autenticado ao construir** `[v0.5.0+]`: sem `token=`, o construtor carrega a credencial da variavel `PDPJ_JWT` (o JusBR aceita tambem `JUSBR_JWT`) e depois do cache gravado por um `auth_govbr()` anterior (`$XDG_CONFIG_HOME/juscraper/pdpj_token.json`, default `~/.config/...`), ignorando com aviso a que estiver vencida. O cache vale para os dois scrapers.
2. **`auth_govbr()`** `[v0.5.0+]`, na maquina do usuario: abre o Chrome, Chromium ou Edge instalado para o login gov.br e captura o token, que grava no cache (`salvar=False` desliga) e renova sozinho quando ha refresh token. Exige `pip install 'juscraper[govbr]'` (sem ele, `ImportError`) e navegador com janela: nao roda no Colab nem em CI. `navegador=` aponta o executavel quando ele nao e achado; demais parametros em `help(jus.scraper('pdpj').auth_govbr)`.
3. **`auth(token)`** com um JWT copiado do portal logado (DevTools > Network > header `Authorization: Bearer <token>`), ou `token=` no construtor. Token malformado ou vencido levanta `ValueError` (`"Token JWT expirado."`), no JusBR desde a 0.4.0 e no PDPJ desde a 0.5.0; token sem `exp` continua aceito. Um `auth()` que falha mantem o token anterior.

Se a renovacao pelo SSO falhar, a requisicao levanta uma subclasse de `RuntimeError` e a coleta para: `RenovacaoPdpjError` (recusa: peca novo `auth_govbr()`) ou `SsoPdpjIndisponivelError` (a chamada seguinte tenta renovar de novo).

### Falhas por linha: `motivo_falha` `[v0.5.0+]`

Nos metodos com uma linha por item (JusBR: `cpopg` e `download_documents`; PDPJ: `cpopg`, `documentos`, `movimentos`, `partes`, `existe` com lista e `download_documents`), a requisicao que falha nao derruba a chamada: a linha sai com o conteudo `None` e a coluna `motivo_falha` diz por que, em vocabulario fechado:

| `motivo_falha` | Significado |
|---|---|
| `None` | Deu certo |
| `http_<status>` | Status HTTP de erro sem retry (ex.: `http_404`, `http_403`). No JusBR, o 403 na listagem aparece com processo ausente do data lake e tambem com acesso negado: para separar, cruze com o PDPJ, que marca o ausente com `nao_encontrado` |
| `retry_esgotado_<status>` | O servidor respondeu com status retentavel ate o fim das tentativas |
| `timeout` | Leitura lenta: o `timeout` do perfil pode estar curto (ver `politica=`) |
| `conexao` | Host inalcancavel (inclui timeout de conexao) |
| `json_invalido` | Resposta 200 com corpo que nao e o JSON esperado |
| `nao_encontrado` | So PDPJ: processo ausente do data lake (`status_consulta="Nao encontrado"` fica para a resposta 200 com lista vazia) |

- Um unico `UserWarning` ao fim da chamada conta as falhas e cita algumas. Para refazer so o que falhou: `df[df['motivo_falha'].notna()]`.
- O **401** (token ausente, vencido ou invalido) nao vira linha: propaga `requests.HTTPError` e interrompe o lote, com as falhas anteriores numa nota do erro (`__notes__`).
- Excecoes fora do vocabulario (ex.: `TooManyRedirects`) propagam.
- No `cpopg`, a linha de falha sai com `status_consulta="Falha na consulta"`.
- No `download_documents` com texto e binario, `motivo_falha` traz o motivo do texto quando o texto falhou, senao o do binario.

### Politica HTTP: `politica=` `[v0.5.0+]`

O construtor dos dois aceita `politica=`, que ajusta campo a campo os perfis `"listagem"` (lista de processos e detalhes) e `"documento"` (texto e binario). O que nao for passado fica com o default do scraper. Perfil ou campo desconhecido levanta `ValueError`.

```python
pdpj = jus.scraper('pdpj', politica={'documento': {'timeout': 120, 'max_retries': 3}})
```

Campos (os de `juscraper.core.http.RequestPolicy`): `timeout` (segundos ou `(conexao, leitura)`), `max_retries` (tentativas, inclusive a primeira), `base_backoff`, `retryable_statuses`, `retry_on_timeout`, `retry_on_connection_error`. Os defaults de cada perfil estao em `jus.scraper('pdpj').perfis_http` (ou `'jusbr'`). O 403 fica fora do retry de proposito: a API o usa para negar um documento isolado, como um sigiloso. Muitos `motivo_falha="timeout"` pedem um `timeout` maior no perfil correspondente.

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
    pesquisa='resolucao',                          # pesquisa, numero_processo ou os dois
    numero_processo=None,                          # CNJ, so os digitos vao a API [v0.5.0+]
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
- **`pesquisa` ou `numero_processo`.** O termo livre nao acha as comunicacoes de um processo pelo numero: use `numero_processo` `[v0.5.0+]`. Sem nenhum dos dois, `ValueError` antes da requisicao (ate a 0.4.0, `pesquisa` era obrigatorio e faltar gerava `ValidationError`).
- **`RetryExhaustedError`** `[v0.4.0+]` ao esgotar `max_retries` em 429/5xx persistente — `ComunicaCNJ` migrou para `HTTPScraper`. Antes, 429/5xx propagava `requests.HTTPError`; agora propaga `juscraper.core.exceptions.RetryExhaustedError`. Codigo defensivo: capturar ambas. Este retry cobre 429/5xx; `pesquisa` ausente ou intervalo invalido continuam erros de input.

---

## PDPJ — DATALAKE Processos `[v0.4.0+]`

Agregador para a API DATALAKE - Processos do PDPJ (`https://api-processo-integracao.data-lake.pdpj.jus.br/processo-api/api/v1`). Sucessor parcial do JusBR, com o mesmo token (JWT do SSO do PJe): autenticacao, `motivo_falha` e `politica=` em §"JusBR e PDPJ" acima. Oferece endpoints granulares e suporte a busca por nome de parte / OAB.

### Construtor

```python
pdpj = jus.scraper('pdpj',
    verbose=0,
    download_path=None,
    sleep_time=0.5,
    token=None,          # JWT; ver §"JusBR e PDPJ"
    politica=None        # [v0.5.0+]; ver §"JusBR e PDPJ"
)
```

### Endpoints

| Metodo | Para que serve | Retorno |
|---|---|---|
| `existe(id_cnj)` | Checa se o processo existe no Data Lake (rapido) | `bool` para `str`; `DataFrame[processo, existe, motivo_falha]` para `list[str]` |
| `cpopg(id_cnj)` | Detalhes do processo (uma linha por tramitacao) | `DataFrame[processo, numero_processo, id, sigla_tribunal, segmento_justica, nivel_sigilo, data_atualizacao, detalhes, status_consulta, motivo_falha]` |
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

`with_text` e `with_binary` sao keyword-only `[v0.5.0+]`: `download_documents(df, None, True, False)` levanta `TypeError`.

`base_df` pode vir tanto de `pdpj.documentos(...)` (uma linha por documento, ja com `id_documento`) quanto de `pdpj.cpopg(...)` (uma linha por processo — o client extrai documentos de `detalhes['documentos']` ou `detalhes['tramitacoes'][*]['documentos']`).

Pelo menos um de `with_text` ou `with_binary` deve ser `True` (senao `ValueError`).

### Workflow tipico

```python
pdpj = jus.scraper('pdpj')
pdpj.auth(token='...')       # se PDPJ_JWT ou o cache nao autenticaram

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
| Status | Estavel | `[v0.4.0+]` |
| cpopg por CNJ | sim | sim |
| Download de pecas | sim (texto) | sim (texto e/ou binario, granular) |
| Busca por nome de parte/OAB | nao | sim (`pesquisa`) |
| Contagem rapida | nao | sim (`contar`) |
| Endpoints granulares (`existe`/`movimentos`/`partes`) | nao | sim |

Se ja esta implementado com JusBR, nao ha necessidade de migrar. Para casos novos com requisitos de busca por parte/OAB ou contagem pre-coleta, PDPJ e a opcao mais rica — assumindo que o usuario tem o `juscraper` 0.4.0 ou posterior instalado.

### Gotchas

- **`existe` retorna tipos diferentes** conforme o input: `bool` quando recebe `str`, `DataFrame` quando recebe `list[str]`. Pense duas vezes antes de usar em codigo generico.
- **`existe` com `str`, `contar` e `pesquisa` levantam o erro da requisicao** `[v0.5.0+]`, em vez de devolver `False`, `0` ou o resultado truncado. Corpo fora do JSON esperado levanta `InvalidJSONResponseError`.
- **Cursor `searchAfter` em `pesquisa`** e forwards-only — `paginas=[3, 5]` baixa as paginas 3, 4 e 5 contiguamente (nao pula a 4).
- **Validacao `extra="forbid"`** em todos os endpoints: kwarg desconhecido vira `TypeError` com sugestao de typo via difflib (ex: `data_juglamento` -> "voce quis dizer 'data_julgamento'?").

## Falcao — Jurisprudencia Nacional da Justica do Trabalho `[v0.5.0+]`

Sistema do CSJT em `jurisprudencia.jt.jus.br` (endpoint publico `/no-auth/pesquisa`). Uma busca cobre o TST e os 24 TRTs. Sem autenticacao.

```python
falcao = jus.scraper('falcao')
df = falcao.listar_decisoes(
    pesquisa='horas extras',          # obrigatorio
    paginas=range(1, 4),              # 1-based; None = todas, ate o teto de 10000 resultados
    colecao='acordaos',               # acordaos | sentencas | decisoesmonocraticas | precedentes | recursorevista
    tribunais=['TST', 'TRT2'],        # str ou list[str]
    classe='ROT',                     # sigla, igual a coluna classe_sigla; o nome por extenso devolve zero sem erro
    data_juntada_inicio='01/01/2025', # cada limite pode ser usado sozinho
)
```

Outros filtros: `relator`, `orgao_julgador`, `fase_processual`, `prioridade`, `tem_ementa`, `somente_ementa`, `ordenacao` (`mais_relevante`, `mais_recente`, `menos_recente`), `tamanho_pagina` (so `5` ou `10`). Colunas canonicas: `processo`, `colecao`, `tribunal`, `relator`, `classe`, `classe_sigla`; `ementa`, `data_julgamento` e `data_juntada` aparecem quando a colecao os expoe. Para guardar as paginas cruas, `listar_decisoes_download` + `listar_decisoes_parse`.

**Gotchas:**

- A busca para em 10000 resultados; `paginas=None` emite `UserWarning` ao atingir o teto. Fatie por `data_juntada_*` ou por `tribunais`.
- Bloqueio do WAF levanta `BotChallengeBlockedError`; bloqueio de IP por excesso de requisicoes (dura horas) levanta `requests.HTTPError` sem retry.
- Na colecao `precedentes`, `processo` e uma chave como `TST-SUM-392`, nao um CNJ.
- Se a coleta falhar no meio, as paginas recebidas ficam num diretorio temporario citado na excecao; recupere com `listar_decisoes_parse`.
