# JusScraper — Referencia da API

## Instalacao

```bash
pip install juscraper                                              # PyPI (recomendado, v0.3.0)
pip install 'juscraper[tjmg]'                                      # para usar TJMG (captcha automatico)
uv add juscraper                                                   # com uv
pip install git+https://github.com/jtrecenti/juscraper.git         # versao dev (main HEAD)
```

Python >= 3.11 obrigatorio.

**Quando usar versao dev:** features marcadas `[unreleased]` (TRF1, TRF3, TRF5, PDPJ) existem apenas na `main` — exigem instalacao via `git+...`.

## Factory function

```python
import juscraper as jus

scraper = jus.scraper(sigla, **kwargs)
```

**Siglas validas (28 tribunais + 4 agregadores):**

| Categoria | Siglas |
|---|---|
| Estaduais (22 estaveis) | `tjac`, `tjal`, `tjam`, `tjap`, `tjba`, `tjce`, `tjdft`, `tjes`, `tjms`, `tjmt`, `tjpa`, `tjpb`, `tjpe`, `tjpi`, `tjpr`, `tjrn`, `tjro`, `tjrr`, `tjrs`, `tjsc`, `tjsp`, `tjto` |
| Estaduais (3 novos `[v0.3.0+]`) | `tjgo`, `tjmg` (requer `pip install 'juscraper[tjmg]'`), `tjrj` |
| Federais (`[unreleased]`) | `trf1`, `trf3`, `trf5` |
| Agregadores estaveis | `datajud`, `jusbr`, `comunica_cnj` (`[v0.3.0+]`) |
| Agregador `[unreleased]` | `pdpj` |

A factory retorna a instancia do scraper correspondente. Qualquer `**kwargs` e passado ao construtor.

**Sigla `comunica_cnj` usa underline, nao hifen.**

## Construtores

### TJSP

```python
tjsp = jus.scraper('tjsp',
    verbose=0,           # 0=silencioso, 1=progresso
    download_path=None,  # None=diretorio temporario
    sleep_time=0.5
)
```

### Tribunais eSAJ (TJAC, TJAL, TJAM, TJCE, TJMS)

```python
scraper = jus.scraper('tjac',   # ou tjal, tjam, tjce, tjms
    verbose=0,
    download_path=None,
    sleep_time=1.0               # mais conservador que TJSP
)
```

### TJGO, TJMG, TJRJ `[v0.3.0+]`

```python
tjgo = jus.scraper('tjgo')   # sleep_time=1.0 default
tjmg = jus.scraper('tjmg')   # requer extra [tjmg]; sleep_time=1.0
tjrj = jus.scraper('tjrj')   # sleep_time=1.0
```

### Demais tribunais (TJRS, TJPR, TJDFT, TJES, TJTO, TJBA, TJMT, TJPA, TJAP, TJPB, TJPE, TJPI, TJRN, TJRO, TJRR, TJSC)

```python
scraper = jus.scraper('tjrs')   # sem parametros extras no construtor
```

### TRFs (TRF1, TRF3, TRF5) `[unreleased]`

```python
trf1 = jus.scraper('trf1',
    verbose=0,
    download_path=None,
    sleep_time=1.0
)
# trf3 e trf5 com mesma assinatura
```

### Agregadores

Detalhes completos em `references/agregadores.md`. Sumario dos construtores:

```python
datajud = jus.scraper('datajud',
    api_key=None,        # None = usa chave publica embutida
    verbose=1,
    download_path=None,
    sleep_time=0.5
)

jusbr = jus.scraper('jusbr',
    verbose=0,
    download_path=None,
    sleep_time=0.5,
    token=None           # JWT — pode passar aqui ou via .auth()
)

cnj = jus.scraper('comunica_cnj',   # [v0.3.0+]
    verbose=1,
    sleep_time=0.5
)
# Nao aceita download_path.

pdpj = jus.scraper('pdpj',          # [unreleased]
    verbose=0,
    download_path=None,
    sleep_time=0.5,
    token=None
)
```

---

## Metodos — Tribunais

### cpopg — Consulta de processo (1o grau)

**Disponivel em:** TJSP (eSAJ); TRF1, TRF3, TRF5 `[unreleased]` (PJe ConsultaPublica); JusBR (qualquer tribunal); PDPJ `[unreleased]` (qualquer tribunal).

#### TJSP

```python
result = tjsp.cpopg(
    id_cnj,                    # str ou list[str] — numero(s) CNJ
    method='html'              # 'html' ou 'api'
)
```

**Retorna:** `dict` com DataFrames. Chaves tipicas: `basicos`, `partes`, `movimentacoes`, `peticoes_diversas`. Variantes granulares: `cpopg_download`, `cpopg_parse`.

#### TRF1, TRF3, TRF5 `[unreleased]`

```python
trf1 = jus.scraper('trf1')   # ou 'trf3', 'trf5'
df = trf1.cpopg(
    id_cnj='1003063-27.2023.4.01.3304'  # str ou list[str]
)
```

**Retorna:** `pd.DataFrame` com uma linha por processo. Colunas: `id_cnj`, `processo`, `classe`, `assunto`, `data_distribuicao`, `orgao_julgador`, `jurisdicao`, `polo_ativo`, `polo_passivo`, `movimentacoes`, `documentos`.

**Diferenca para o TJSP:** o TJSP devolve `dict` com varios DataFrames; os TRFs devolvem **um unico DataFrame** com uma linha por processo. Processos nao encontrados no portal publico devolvem linha so com `id_cnj`. Resiliencia por item: falha individual nao interrompe o batch.

Para JusBR e PDPJ, ver `references/agregadores.md`.

### cposg — Consulta de processo (2o grau)

**Disponivel em:** TJSP.

```python
result = tjsp.cposg(
    id_cnj,                    # str ou list — numero(s) CNJ
    method='html'              # 'html' ou 'api' (parse JSON nao implementado — use 'html')
)
```

Mesmo padrao de retorno e variantes do `cpopg` do TJSP.

### cjsg — Busca de jurisprudencia (2o grau)

**Disponivel em:** Todos os 25 tribunais estaduais (com parametros diferentes por tribunal). Consulte `references/tribunais.md` para os parametros especificos de cada um. Abaixo apenas os exemplos principais — TJSP, TJRS, TJPR, TJDFT.

#### TJSP

```python
df = tjsp.cjsg(
    pesquisa='dano moral',                  # str — aceita "" desde [unreleased]
    ementa=None,
    classe=None,                            # int | str | list[int|str] [unreleased]
    assunto=None,                           # int | str | list[int|str] [unreleased]
    comarca=None,                           # int | str (exclusivo TJSP na familia eSAJ)
    orgao_julgador=None,
    data_julgamento_inicio=None,            # multiplos formatos aceitos [v0.3.0]
    data_julgamento_fim=None,
    baixar_sg=True,
    tipo_decisao='acordao',                 # 'acordao' ou 'monocratica'
    paginas=range(1, 4),                    # 1-based
    auto_chunk=True                         # [v0.3.0] divide janela >366 dias
)
```

`[unreleased]` Aceita `pesquisa=""` para buscar so por filtros.

`[v0.3.0]` Guard `QueryTooLongError` para `pesquisa` >120 caracteres.

#### TJRS

```python
df = tjrs.cjsg(
    pesquisa='dano moral',
    paginas=range(1, 4),
    classe=None,                            # singular canonico [v0.3.0]
    assunto=None,                           # singular canonico [v0.3.0]
    orgao_julgador=None,
    relator=None,
    data_julgamento_inicio=None,
    data_julgamento_fim=None,
    data_publicacao_inicio=None,
    data_publicacao_fim=None,
    tipo_processo=None,
    secao=None                              # 'civel', 'crime'
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
    sinonimos=True,
    espelho=True,
    inteiro_teor=False,
    tamanho_pagina=10,                      # canonico [v0.3.0] (substitui quantidade_por_pagina)
    data_julgamento_inicio=None,            # [v0.3.0] agora aceito
    data_julgamento_fim=None
)
```

**Retorna:** `pandas.DataFrame` com colunas que variam por tribunal (`processo`, `relator`, `orgao_julgador`, `data_julgamento`, `ementa`, etc.).

**Variantes granulares (todos os tribunais):**

```python
raw = scraper.cjsg_download(pesquisa='...', paginas=range(1, 4))
df = scraper.cjsg_parse(raw)
```

### cjpg — Busca de jurisprudencia (1o grau)

**Disponivel em:** TJSP, TJES, TJTO.

```python
df = tjsp.cjpg(
    pesquisa='golpe do pix',
    classe=None,                            # singular canonico [unreleased] (era 'classes')
    assunto=None,                           # singular canonico [unreleased] (era 'assuntos')
    vara=None,                              # singular canonico [unreleased] (era 'varas')
    id_processo=None,
    data_julgamento_inicio=None,
    data_julgamento_fim=None,
    paginas=range(1, 4),
    auto_chunk=True                         # [v0.3.0] divide janela >366 dias
)
```

`[unreleased]` Plurais (`classes`/`assuntos`/`varas`) aceitos com `DeprecationWarning`. Plural + singular juntos -> `ValueError`. `[v0.3.0]` Guard `QueryTooLongError` para `pesquisa` >120 caracteres.

**Retorna:** `pandas.DataFrame` com colunas: `cd_processo`, `id_processo`, `classe`, `assunto`, `magistrado`, `comarca`, `foro`, `vara`, `data_disponibilizacao`, `decisao`.

**TJES e TJTO tambem suportam cjpg:**

```python
tjes = jus.scraper('tjes')
df = tjes.cjpg(pesquisa='...', paginas=range(1, 4))  # core='pje1g'

tjto = jus.scraper('tjto')
df = tjto.cjpg(pesquisa='...', paginas=range(1, 4))  # mesmos params da cjsg
```

`[v0.3.0]` TJES `cjpg` rejeita `data_publicacao_*` (so aceita `data_julgamento_*`).

**Variantes granulares:**

```python
path = tjsp.cjpg_download(pesquisa='...', paginas=range(1, 4))
df = tjsp.cjpg_parse(path)
```

**Gotchas praticos do cjpg do TJSP** (`auto_chunk` substitui workaround manual, `QueryTooLongError`, hierarquia de assuntos, dedup) — ver `references/tjsp.md` §"Gotchas praticos do cjpg".

---

## Metodos — Agregadores

Movidos para `references/agregadores.md`. Sumario dos endpoints publicos:

| Agregador | Metodos principais |
|---|---|
| **Datajud** | `listar_processos`, `contar_processos` (`[v0.3.0]`) |
| **JusBR** | `auth`, `auth_firefox`, `cpopg`, `download_documents` |
| **ComunicaCNJ** `[v0.3.0+]` | `listar_comunicacoes` |
| **PDPJ** `[unreleased]` | `auth`, `existe`, `cpopg`, `documentos`, `movimentos`, `partes`, `pesquisa`, `contar`, `download_documents` |

---

## Validacao de kwargs (`extra="forbid"`) `[v0.3.0]`

Todos os endpoints com schema pydantic wired (familia eSAJ, agregadores, maioria dos tribunais) validam kwargs com `extra="forbid"`. Kwarg desconhecido vira `TypeError` com mensagem amigavel:

```python
>>> tjsp.cjsg(pesquisa='teste', data_juglamento_inicio='2024-01-01')
TypeError: TJSPScraper.cjsg() got unexpected keyword argument(s):
  'data_juglamento_inicio' (você quis dizer 'data_julgamento_inicio'?)
```

A sugestao de typo usa `difflib.get_close_matches` contra os campos do schema. Diferente do comportamento antigo (kwargs nao reconhecidos silenciosamente ignorados, gerando raspagens nao-filtradas sem alarme), agora qualquer typo e capturado antes do request.

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

- Quiser preservar os arquivos HTML/JSON brutos.
- Precisar reprocessar dados sem baixar novamente.
- Quiser inspecionar a resposta bruta do tribunal.

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
| `[1, 3, 5]` | Baixa paginas 1, 3 e 5 (excecao PDPJ — o cursor `searchAfter` em `pesquisa` e forwards-only e forca o range contiguo `range(1, 6)`, ver agregadores.md) |
| `None` | Baixa TODAS as paginas (usar com cautela) |

A paginacao e **1-based** em todos os scrapers. `range(0, 3)` NAO e valido.

---

## Utilitarios CNJ

Funcoes auxiliares para manipulacao de numeros de processo no padrao CNJ. Importacao: `from juscraper.utils.cnj import clean_cnj, split_cnj, format_cnj`.

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

O juscraper aceita nomes antigos de parametros com `DeprecationWarning`. Prefira sempre os nomes canonicos:

| Canonico | Aliases depreciados | Origem |
|----------|---------------------|--------|
| `pesquisa` | `query`, `termo` | v0.1.6 |
| `data_julgamento_inicio` | `data_julgamento_de`, `data_inicio` | v0.1.6 |
| `data_julgamento_fim` | `data_julgamento_ate`, `data_fim` | v0.1.6 |
| `data_publicacao_inicio` | `data_publicacao_de` | v0.1.6 |
| `data_publicacao_fim` | `data_publicacao_ate` | v0.1.6 |
| `paginas` (1-based) | `paginas` (0-based) | v0.1.6 |
| `tamanho_pagina` | `items_per_page` (TJBA), `quantidade_por_pagina` (TJDFT/TJMT), `per_page` (TJES), `qtde_itens_pagina` (TJGO), `linhas_por_pagina` (TJMG) | `[v0.3.0]` |
| `classe` | `classes` (TJSP `cjpg`, TJBA), `classe_cnj` (TJPE), `classe_judicial` (TJES, TJRO) | `[v0.3.0]` / `[unreleased]` |
| `assunto` | `assuntos` (TJSP `cjpg`, Datajud), `assunto_cnj` (TJPE) | `[v0.3.0]` / `[unreleased]` |
| `vara` | `varas` (TJSP `cjpg`) | `[unreleased]` |
| `numero_processo` | `nr_processo` (TJPB, TJRN, TJRO), `numero_cnj` (TJAP) | `[v0.3.0]` |
| `relator` | `magistrado` (TJES, TJRO) | `[v0.3.0]` |
| `id_classe` | `id_classe_judicial` (TJRN, TJPB) | `[v0.3.0]` |

Os aliases `data_inicio`/`data_fim` sao mapeados para `data_julgamento_inicio`/`data_julgamento_fim` (nao para publicacao). Ao gerar codigo, use sempre os nomes canonicos.

**Casos especificos onde `data_inicio`/`data_fim` nao se aplica:**

- **Datajud:** rejeita o alias generico (filtra por **ajuizamento**, nao julgamento). Use `data_ajuizamento_inicio`/`data_ajuizamento_fim`. Ver `references/agregadores.md`.
- **ComunicaCNJ:** filtra por **disponibilizacao** no DJe. Use `data_disponibilizacao_inicio`/`data_disponibilizacao_fim`.
- **TJRJ:** rejeita ambos `data_julgamento_*` e `data_publicacao_*`. Use `ano_inicio`/`ano_fim` (granularidade anual).
- **TJGO:** rejeita `data_julgamento_*`. Use `data_publicacao_*`.
- **TJES, TJMT:** rejeitam `data_publicacao_*`. Use `data_julgamento_*`.
