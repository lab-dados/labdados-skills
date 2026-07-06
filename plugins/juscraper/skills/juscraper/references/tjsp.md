# TJSP — Especificidades

Reference dedicada ao Tribunal de Justica do Estado de Sao Paulo. Leia
quando o estudo envolver TJSP ou quando o usuario pedir recorte
temporal, metodo de coleta ou endpoint especifico deste tribunal.

Para matriz comparativa cross-tribunal, parametros da `cjsg` e outros
scrapers, ver `tribunais.md`.

## Por que TJSP tem reference propria

Cada tribunal brasileiro tem peculiaridades de plataforma, janela de
cobertura temporal, parametros exclusivos e gotchas. Esta skill
convenciona que **cada tribunal pode ter sua propria reference**
(`references/tjsp.md`, `references/tjrs.md`, etc.) a medida que
especificidades sejam validadas. O TJSP e o primeiro porque e o unico
tribunal com suporte completo (cpopg + cposg + cjsg + cjpg) e o mais
usado em pesquisa empirica.

## Endpoints suportados

TJSP e o unico tribunal com os quatro endpoints do juscraper:

| Endpoint | Descricao | Construtor |
|---|---|---|
| `cjsg` | Consulta de Jurisprudencia (2º grau, acordaos e monocraticas) | `jus.scraper('tjsp').cjsg(...)` |
| `cjpg` | Consulta de Julgados de Primeiro Grau | `jus.scraper('tjsp').cjpg(...)` |
| `cpopg` | Consulta Processual Originaria de 1º grau | `jus.scraper('tjsp').cpopg(id_cnj, ...)` |
| `cposg` | Consulta Processual Originaria de 2º grau | `jus.scraper('tjsp').cposg(id_cnj, ...)` |

Construtor com `sleep_time=0.5` como default. `[unreleased]` Para descobrir IDs de filtros antes de consultar, use `listar_classes(grau="2")`, `listar_assuntos(grau="2")`, `listar_orgaos(grau="2")` e `listar_varas(grau="1")`; todos retornam arvore com `id`, `nome`, `id_pai`, `nivel`, `selecionavel`, `caminho`.

## Parametros exclusivos

### `method` em `cpopg`/`cposg`

```python
tjsp.cpopg(id_cnj, method='html')  # padrao: scraping HTML
tjsp.cpopg(id_cnj, method='api')   # via API REST do TJSP
```

O metodo `'html'` e mais estavel. O parse JSON do `cposg` **nao esta
implementado** — use `'html'`.

### `cjpg` (1º grau, exclusivo TJSP)

```python
tjsp.cjpg(
    pesquisa='...', paginas=range(1, 4),
    classe=None,         # int | str | list[int|str] — singular canonico [unreleased] (era `classes`)
    assunto=None,        # int | str | list[int|str] — singular canonico [unreleased] (era `assuntos`)
    vara=None,           # str | list[str] — singular canonico [unreleased] (era `varas`)
    id_processo=None,    # CNJ do processo, com ou sem mascara; normalizado via clean_cnj()
    data_julgamento_inicio=None, data_julgamento_fim=None,
    auto_chunk=True,     # [v0.3.0] divide janela >366 dias automaticamente
    count_only=False     # [unreleased] retorna int com total estimado
)
```

`[unreleased]` Plurais (`classes`/`assuntos`/`varas`) ainda aceitos com `DeprecationWarning`. Passar plural + singular juntos -> `ValueError`.

```python
df = tjsp.cjpg(id_processo='1011654-78.2024.8.26.0566', paginas=range(1, 2))
```

`id_processo` aqui significa numero CNJ do processo, nao ID interno do eSAJ. Para jurisprudencia ou decisoes de 1o grau de um processo especifico, use `cjpg(id_processo=cnj)`; para dados cadastrais e andamento processual, use `cpopg(id_cnj=cnj)`.

`[unreleased]` Para estimar volume antes de baixar sentencas, use `count_only=True`:

```python
n = tjsp.cjpg(pesquisa='fornecimento medicamento', assunto=10070, count_only=True)
```

Retorna `int`; `paginas` e ignorado com `UserWarning`. Com `auto_chunk=True`, janelas longas sao somadas sem dedup por `(id_processo, data_disponibilizacao)`, entao a contagem pode divergir de `len(tjsp.cjpg(...))`.

### `cjsg` — extras em relacao ao eSAJ padrao

Alem dos parametros eSAJ documentados em `tribunais.md`, o TJSP aceita:
- `comarca=None` — filtro por comarca (exclusivo TJSP na familia eSAJ)
- `tipo_decisao='acordao'|'monocratica'`
- `baixar_sg=True`
- **`pesquisa=""` aceito `[unreleased]`** — antes era obrigatorio; agora `tjsp.cjsg(classe='...', assunto='...')` sem termo textual funciona, igualando o comportamento de `cjpg`.
- **`count_only=True` aceito `[unreleased]`** — retorna `int` com o total estimado de resultados em vez de `DataFrame`. Mesmo contrato do `cjpg`: ignora `paginas` com warning e soma janelas longas sem dedup.

## Cobertura temporal

Validacao empirica (2026-04, `pesquisa='dano moral'`, primeira pagina
por ano):

| Endpoint | Inicio marginal | Inicio consistente |
|---|---|---|
| `cjpg` (1º grau) | **1994** (≤2 resultados/ano) | **1998** (1ª pag. saturada com 10) |
| `cjsg` (2º grau) | **1985** (registros historicos esparsos) | **1998** (1ª pag. saturada com 20) |
| `cpopg` / `cposg` | depende do processo | **verificar caso a caso** |

**O que isso significa:**
- Para recortes pre-1998 no `cjpg`/`cjsg`, ausencia de resultado e
  provavelmente ausencia de digitalizacao, nao ausencia do fenomeno.
  Documente a limitacao no protocolo.
- Em 1985-1993 o `cjpg` retorna "Nao foi encontrado nenhum resultado..."
  (tratado como erro de parse pela biblioteca).
- `cpopg`/`cposg` dependem de o processo especifico ter sido
  digitalizado, nao da data de referencia. Processos antigos
  fisicamente arquivados podem nao estar disponiveis mesmo com CNJ
  posterior.

**Se o usuario pedir recorte que comeca antes de 1998 no TJSP**:
alerte que ausencia de resultado provavelmente reflete ausencia de
digitalizacao. Considere comecar o recorte em 1998 ou depois para
evitar vies de cobertura, ou documente explicitamente a limitacao no
protocolo.

**Validacao propria**: testada apenas no TJSP. Cada TJ tem calendario
proprio de migracao SAJ/eSAJ — nao assumir cobertura equivalente em
outros tribunais sem testar.

## Gotchas praticos do cjpg

Tetos empiricos (validos em 2026-04) que afetam a implementacao de
raspagens do primeiro grau:

- **Janela temporal > 1 ano: `auto_chunk=True` (default) `[v0.3.0]`.**
  Antes, ranges maiores que 1 ano batiam num teto interno do eSAJ e o
  `cjpg_n_pags` falhava com "Nao foi possivel encontrar o seletor de
  numero de paginas" (issue #91). Agora a familia eSAJ (TJSP `cjpg`/`cjsg`,
  TJAC/TJAL/TJAM/TJCE/TJMS `cjsg`) divide automaticamente intervalos
  `data_julgamento_*` que excedem 366 dias, baixa cada chunk e
  concatena com dedup. Falhas em janelas individuais viram
  `UserWarning` e o DataFrame retorna parcial.

  ```python
  # [v0.3.0] funciona — divide internamente em chunks anuais e concatena
  df = tjsp.cjpg(
      pesquisa=q, assunto=c,
      data_julgamento_inicio='01/01/2015',
      data_julgamento_fim='31/12/2022',
  )
  ```

  Para o comportamento antigo (`ValueError` em janelas longas), passar
  `auto_chunk=False`. Workaround manual em `pd.concat([cjpg(...) for
  ano in range(...)])` continua funcionando — util para ter controle
  granular sobre dedup, retry por chunk, ou progress reporting.

  **Dedup interno usa `(id_processo, data_disponibilizacao)`** — nao
  apenas `id_processo`, porque um mesmo processo pode ter mais de uma
  sentenca publicada em datas distintas.

- **Campo `pesquisa` ≤ 120 caracteres — `QueryTooLongError` `[v0.3.0]`.**
  O backend do eSAJ trunca strings com mais de 120 chars silenciosamente.
  Agora `cjpg_download` e `cjsg_download` levantam
  `juscraper.courts.tjsp.exceptions.QueryTooLongError` (subclasse de
  `ValueError`) antes da requisicao. Priorize os termos mais
  discriminativos. Use `OR`/aspas/parenteses:
  `'criança OR adolescente OR "menor de idade"'`.

- **Filtro de `assunto` NAO e hierarquico** — aceita apenas codigos
  `selecionavel=True` da arvore do eSAJ. Agrupadores (ex: 6683) retornam
  zero. Use `tjsp.listar_assuntos(grau="1")`/`grau="2"` ou ver `assuntos-tjsp.md` antes de escolher o ID.

- **Regex pos-coleta e redundante quando os termos cabem em
  `pesquisa=`**: passar ja ao endpoint corta volume baixado em 10-100×.
