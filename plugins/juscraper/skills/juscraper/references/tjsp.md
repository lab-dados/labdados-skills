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

Construtor com `sleep_time=0.5` como default.

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
    classes=None,        # list[str]
    assuntos=None,       # list[str]
    varas=None,          # list[str]
    id_processo=None,
    data_julgamento_inicio=None, data_julgamento_fim=None
)
```

### `cjsg` — extras em relacao ao eSAJ padrao

Alem dos parametros eSAJ documentados em `tribunais.md`, o TJSP aceita:
- `comarca=None` — filtro por comarca (exclusivo TJSP na familia eSAJ)
- `tipo_decisao='acordao'|'monocratica'`
- `baixar_sg=True`

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

- **Janela temporal ≤ 1 ano por chamada.** Ranges maiores batem em um
  teto interno do eSAJ e o `cjpg_n_pags` falha com "Nao foi possivel
  encontrar o seletor de numero de paginas" (juscraper issue #91).
  Para cobrir varios anos, itere por ano e concatene com dedup pela
  combinacao `(id_processo, data_disponibilizacao)` — **nao** apenas
  por `id_processo`, porque um mesmo processo pode ter mais de uma
  sentenca publicada em datas distintas:
  ```python
  import pandas as pd
  partes = [tjsp.cjpg(pesquisa=q, assuntos=c,
                      data_julgamento_inicio=f"01/01/{ano}",
                      data_julgamento_fim=f"31/12/{ano}")
            for ano in range(2015, 2023)]
  df = (pd.concat(partes, ignore_index=True)
          .drop_duplicates(["id_processo", "data_disponibilizacao"]))
  ```
- **Campo `pesquisa` ≤ 120 caracteres** (issue #35). Priorize os
  termos mais discriminativos. Use `OR`/aspas/parenteses:
  `'criança OR adolescente OR "menor de idade"'`.
- **Filtro de `assuntos` NAO e hierarquico** — aceita apenas codigos
  `selectable=True` da arvore do eSAJ. Agrupadores (ex: 6683) retornam
  zero. Ver `assuntos-tjsp.md`.
- **Regex pos-coleta e redundante quando os termos cabem em
  `pesquisa=`**: passar ja ao endpoint corta volume baixado em 10-100×.
