# JusScraper — Referencia da API

## Instalacao

```bash
pip install juscraper        # PyPI (recomendado)
uv add juscraper             # com uv
pip install git+https://github.com/jtrecenti/juscraper.git  # versao dev
```

Python >= 3.11 obrigatorio.

## Factory function

```python
import juscraper as jus

scraper = jus.scraper(sigla, **kwargs)
```

**Siglas validas (22 tribunais + 2 agregadores):**
`tjac`, `tjal`, `tjam`, `tjap`, `tjba`, `tjce`, `tjdft`, `tjes`, `tjms`, `tjmt`,
`tjpa`, `tjpb`, `tjpe`, `tjpi`, `tjpr`, `tjrn`, `tjro`, `tjrr`, `tjrs`, `tjsc`,
`tjsp`, `tjto`, `datajud`, `jusbr`

A factory retorna a instancia do scraper correspondente. Qualquer `**kwargs`
e passado ao construtor do scraper.

## Construtores

### TJSP

```python
tjsp = jus.scraper('tjsp',
    verbose=0,           # 0=silencioso, 1=progresso
    download_path=None,  # None=diretorio temporario (apagado apos parse)
    sleep_time=0.5       # segundos entre requisicoes
)
```

### Tribunais eSAJ (TJAC, TJAL, TJAM, TJCE, TJMS)

```python
scraper = jus.scraper('tjac',   # ou tjal, tjam, tjce, tjms
    verbose=0,
    download_path=None,
    sleep_time=1.0               # default 1.0 (mais conservador que TJSP)
)
```

### Demais tribunais (TJRS, TJPR, TJDFT, TJES, TJTO, TJBA, TJMT, TJPA, TJAP, TJPB, TJPE, TJPI, TJRN, TJRO, TJRR, TJSC)

```python
scraper = jus.scraper('tjrs')   # sem parametros extras no construtor
```

### Datajud

```python
datajud = jus.scraper('datajud',
    api_key=None,        # None=usa chave publica padrao
    verbose=1,           # 0=silencioso, 1=progresso
    download_path=None,  # diretorio temporario
    sleep_time=0.5       # segundos entre requisicoes
)
```

### JusBR

```python
jusbr = jus.scraper('jusbr',
    verbose=0,
    download_path=None,
    sleep_time=0.5,
    token=None           # JWT token — pode passar aqui ou via .auth()
)
```

---

## Metodos — Tribunais

### cpopg — Consulta de processo (1o grau)

**Disponivel em:** TJSP

```python
result = tjsp.cpopg(
    id_cnj,                    # str ou list[str] — numero(s) CNJ
    method='html'              # 'html' ou 'api'
)
```

**Retorna:** `dict` com DataFrames. Chaves tipicas: `basicos`, `partes`, `movimentacoes`,
`peticoes_diversas` (variam conforme o processo).

**Exemplo:**
```python
tjsp = jus.scraper('tjsp')
result = tjsp.cpopg('1000149-71.2024.8.26.0346')
print(result.keys())          # dict_keys(['basicos', 'partes', 'movimentacoes', ...])
result['partes'].head()       # DataFrame com as partes do processo
```

**Variantes granulares:**
```python
tjsp.cpopg_download(id_cnj, method='html')  # baixa arquivos brutos
result = tjsp.cpopg_parse(path)              # parse dos arquivos
```

### cposg — Consulta de processo (2o grau)

**Disponivel em:** TJSP

```python
result = tjsp.cposg(
    id_cnj,                    # str ou list — numero(s) CNJ
    method='html'              # 'html' ou 'api'
)
```

**Retorna:** `dict` com DataFrames (mesmo padrao do cpopg).

**Variantes granulares:**
```python
tjsp.cposg_download(id_cnj, method='html')
result = tjsp.cposg_parse(path)
```

**Nota:** O parse via `method='api'` (JSON) nao esta implementado; use `method='html'`.

### cjsg — Busca de jurisprudencia (2o grau)

**Disponivel em:** Todos os 22 tribunais (com parametros diferentes por tribunal).
Consulte `references/tribunais.md` para os parametros especificos de cada um.
Abaixo os exemplos dos principais:

#### TJSP

```python
df = tjsp.cjsg(
    pesquisa='dano moral',                  # termo de busca (obrigatorio)
    ementa=None,                            # filtro por texto da ementa
    classe=None,                            # classe processual
    assunto=None,                           # assunto
    comarca=None,                           # comarca
    orgao_julgador=None,                    # orgao julgador
    data_julgamento_inicio=None,            # 'DD/MM/AAAA'
    data_julgamento_fim=None,               # 'DD/MM/AAAA'
    baixar_sg=True,                         # incluir dados do 2o grau
    tipo_decisao='acordao',                 # 'acordao' ou 'monocratica'
    paginas=range(1, 4)                     # paginas 1-based
)
```

#### TJRS

```python
df = tjrs.cjsg(
    pesquisa='dano moral',
    paginas=range(1, 4),
    classe=None,
    assunto=None,
    orgao_julgador=None,
    relator=None,                           # nome do relator
    data_julgamento_inicio=None,
    data_julgamento_fim=None,
    data_publicacao_inicio=None,            # filtro extra (nao disponivel no TJSP)
    data_publicacao_fim=None,
    tipo_processo=None,                     # tipo do processo
    secao=None                              # 'civel', 'crime', etc.
)
```

#### TJPR

```python
df = tjpr.cjsg(
    pesquisa='dano moral',
    paginas=range(1, 4),
    data_julgamento_inicio=None,
    data_julgamento_fim=None,
    data_publicacao_inicio=None,
    data_publicacao_fim=None
)
```

#### TJDFT

```python
df = tjdft.cjsg(
    pesquisa='dano moral',
    paginas=range(1, 4),
    sinonimos=True,                         # incluir sinonimos na busca
    espelho=True,                           # buscar no espelho
    inteiro_teor=False,                     # buscar no inteiro teor
    quantidade_por_pagina=10                # resultados por pagina
)
```

**IMPORTANTE:** TJDFT **nao** suporta filtros de data. Se passados, serao ignorados com aviso.

**Retorna:** `pandas.DataFrame` com colunas que variam por tribunal (processo, relator,
orgao_julgador, data_julgamento, ementa, etc.).

**Variantes granulares (todos os tribunais):**
```python
raw = scraper.cjsg_download(pesquisa='...', paginas=range(1, 4))
df = scraper.cjsg_parse(raw)
```

### cjpg — Busca de jurisprudencia (1o grau)

**Disponivel em:** TJSP, TJES, TJTO

```python
df = tjsp.cjpg(
    pesquisa='golpe do pix',               # termo de busca
    classes=None,                           # list[str] — classes processuais
    assuntos=None,                          # list[str] — assuntos
    varas=None,                             # list[str] — varas
    id_processo=None,                       # str — ID do processo
    data_julgamento_inicio=None,            # 'DD/MM/AAAA'
    data_julgamento_fim=None,               # 'DD/MM/AAAA'
    paginas=range(1, 4)                     # paginas 1-based
)
```

**Retorna:** `pandas.DataFrame` com colunas: `cd_processo`, `id_processo`, `classe`,
`assunto`, `magistrado`, `comarca`, `foro`, `vara`, `data_disponibilizacao`, `decisao`.

**TJES e TJTO tambem suportam cjpg:**
```python
tjes = jus.scraper('tjes')
df = tjes.cjpg(pesquisa='...', paginas=range(1, 4))  # usa core='pje1g'

tjto = jus.scraper('tjto')
df = tjto.cjpg(pesquisa='...', paginas=range(1, 4))  # mesmos params da cjsg
```

**Variantes granulares:**
```python
path = tjsp.cjpg_download(pesquisa='...', paginas=range(1, 4))
df = tjsp.cjpg_parse(path)
```

**Gotchas praticos do cjpg do TJSP** (janela temporal ≤ 1 ano,
tamanho de `pesquisa`, hierarquia de assuntos, dedup por
`(id_processo, data_disponibilizacao)`): ver `references/tjsp.md`
§"Gotchas praticos do cjpg".

---

## Metodos — Agregadores

### Datajud: listar_processos

```python
datajud = jus.scraper('datajud')

df = datajud.listar_processos(
    numero_processo=None,      # str ou list[str] — numero(s) CNJ
    tribunal=None,             # sigla (ex: 'TJSP', 'TRF1', 'STJ')
    ano_ajuizamento=None,      # int (ex: 2023)
    classe=None,               # str — codigo da classe
    assuntos=None,             # list[str] — codigos de assuntos
    mostrar_movs=False,        # True para incluir movimentacoes
    paginas=None,              # range (1-based) ou None (todas)
    tamanho_pagina=1000        # max 10000
)
```

**Requer:** `tribunal` OU `numero_processo` (pelo menos um).

**Retorna:** `pandas.DataFrame` com colunas: `classe`, `numeroProcesso`, `sistema`,
`formato`, `tribunal`, `dataHoraUltimaAtualizacao`, `grau`, `dataAjuizamento`,
`movimentos` (se `mostrar_movs=True`), `id`, `nivelSigilo`, `orgaoJulgador`, `assuntos`.

**Exemplo:**
```python
datajud = jus.scraper('datajud')
df = datajud.listar_processos(
    tribunal='TJSP',
    ano_ajuizamento=2023,
    paginas=range(1, 3)
)
print(f"Encontrados {len(df)} processos")
```

### JusBR: cpopg + download_documents

**Autenticacao obrigatoria antes de qualquer chamada:**

```python
jusbr = jus.scraper('jusbr')

# Opcao 1: token manual
jusbr.auth(token='seu_jwt_token_aqui')

# Opcao 2: via cookies do Firefox (requer sessao ativa no jus.br)
jusbr.auth_firefox()
```

#### cpopg (JusBR)

```python
df = jusbr.cpopg(
    id_cnj='3005317-12.2025.8.06.0000'   # str ou list[str]
)
```

**Retorna:** `pandas.DataFrame` com colunas: `processo_pesquisado`, `numeroProcesso`,
`idCodexTribunal`, `detalhes` (dict com metadados completos), `status_consulta`.

#### download_documents

```python
df_docs = jusbr.download_documents(
    base_df=resultado_cpopg,     # DataFrame retornado por cpopg()
    max_docs_per_process=None    # int ou None (todos)
)
```

**Retorna:** `pandas.DataFrame` onde cada linha e um documento, com colunas:
`numero_processo`, `idDocumento`, `descricao`, `nome`, `tipo`, `dataHoraJuntada`,
`nivelSigilo`, `hrefTexto`, `hrefBinario`, `texto` (conteudo extraido),
`_raw_text_api`, `_raw_binary_api`.

**Workflow completo JusBR:**
```python
jusbr = jus.scraper('jusbr')
jusbr.auth(token='...')

# 1. Buscar metadados do processo
resultado = jusbr.cpopg('3005317-12.2025.8.06.0000')

# 2. Baixar documentos desse processo
docs = jusbr.download_documents(resultado)
print(docs[['numero_processo', 'descricao', 'texto']].head())
```

---

## Padrao download/parse

Todos os metodos de coleta seguem o padrao:

```python
# Combinado (padrao — baixa + processa + apaga temporarios)
df = scraper.cjsg(pesquisa='teste', paginas=range(1, 4))

# Granular (controle sobre arquivos brutos)
raw = scraper.cjsg_download(pesquisa='teste', paginas=range(1, 4))
df = scraper.cjsg_parse(raw)
```

Use o modo granular quando:
- Quiser preservar os arquivos HTML/JSON brutos
- Precisar reprocessar dados sem baixar novamente
- Quiser inspecionar a resposta bruta do tribunal

Para preservar arquivos brutos, defina `download_path` no construtor:
```python
tjsp = jus.scraper('tjsp', download_path='./dados_brutos')
```

---

## Parametro paginas — detalhes

| Valor | Comportamento |
|-------|---------------|
| `range(1, 4)` | Baixa paginas 1, 2, 3 |
| `3` | Equivale a `range(1, 4)` |
| `[1, 3, 5]` | Baixa paginas 1, 3 e 5 |
| `None` | Baixa TODAS as paginas (usar com cautela) |

A paginacao e **1-based** em todos os scrapers. `range(0, 3)` NÃO e valido.

---

## Utilitarios CNJ

Funcoes auxiliares para manipulacao de numeros de processo no padrao CNJ.
Importacao: `from juscraper.utils.cnj import clean_cnj, split_cnj, format_cnj`

### clean_cnj

```python
clean_cnj('1000149-71.2024.8.26.0346')
# → '10001497120248260346'
```

Remove pontos e tracos, retornando apenas os 20 digitos.

### split_cnj

```python
split_cnj('10001497120248260346')
# → {'num': '1000149', 'dv': '71', 'ano': '2024', 'justica': '8', 'tribunal': '26', 'orgao': '0346'}
```

Divide os 20 digitos nas partes do padrao CNJ. Lanca `ValueError` se nao tiver 20 digitos.

### format_cnj

```python
format_cnj('10001497120248260346')
# → '1000149-71.2024.8.26.0346'
```

Formata os digitos no padrao visual NNNNNNN-DD.AAAA.J.TT.OOOO.

---

## Aliases de parametros depreciados

O juscraper aceita nomes antigos de parametros com `DeprecationWarning`.
Prefira sempre os nomes canonicos:

| Canonico | Aliases depreciados |
|----------|-------------------|
| `pesquisa` | `query`, `termo` |
| `data_julgamento_inicio` | `data_julgamento_de`, `data_inicio` |
| `data_julgamento_fim` | `data_julgamento_ate`, `data_fim` |
| `data_publicacao_inicio` | `data_publicacao_de` |
| `data_publicacao_fim` | `data_publicacao_ate` |

Os aliases `data_inicio`/`data_fim` sao mapeados para `data_julgamento_inicio`/`data_julgamento_fim`
(nao para publicacao). Ao gerar codigo, use sempre os nomes canonicos.
