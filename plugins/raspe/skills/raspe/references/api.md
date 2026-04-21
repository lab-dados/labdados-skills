# Referencia de API — raspe

Assinaturas publicas exportadas em `raspe/__init__.py`. Todas as factories retornam instancias prontas; todas as instancias expoem `.raspar(**kwargs) -> pandas.DataFrame`.

## Factories

### Fontes HTTP (nao precisam de `[browser]`)

| Factory | Construtor | Parametros de `.raspar()` |
|---|---|---|
| `raspe.presidencia()` | sem args | `pesquisa: str \| list[str]`, `paginas: range = None` |
| `raspe.camara()` | sem args | `pesquisa: str \| list[str]`, `ano: int = None`, `tipo_materia: str = None`, `paginas: range = None` |
| `raspe.senado()` | sem args | `pesquisa: str \| list[str]`, `ano: int = None`, `tipo_materia: str = None`, `paginas: range = None` |
| `raspe.cnj()` | sem args | `pesquisa: str \| list[str]`, `data_inicio: str = None`, `data_fim: str = None`, `paginas: range = None` |
| `raspe.ipea()` | sem args | `pesquisa: str \| list[str]`, `paginas: range = None` |
| `raspe.cfm()` | sem args | `texto: str \| list[str]`, `uf: str = ''`, `revogada: str = ''`, `numero: str = ''`, `ano: str = ''`, `paginas: range = None` |
| `raspe.folha()` | sem args | `pesquisa: str \| list[str]`, `site: Literal['todos','online','jornal'] = 'todos'`, `data_inicio: str = None`, `data_fim: str = None`, `paginas: range = None` |
| `raspe.nyt(api_key=...)` | `api_key: str \| None = None` (fallback: env `NYT_API_KEY`) | `texto: str \| list[str]`, `ano: int = None`, `data_inicio: str = None`, `data_fim: str = None`, `sort: Literal['best','newest','oldest','relevance'] = 'newest'`, `filtro: str = ''`, `paginas: range = None` |

### Fontes Playwright (requerem `raspe[browser]`)

| Factory | Construtor | Parametros de `.raspar()` |
|---|---|---|
| `raspe.saudelegis()` | `debug: bool = True`, `headless: bool = True` | `assunto: str \| list[str]`, `paginas: range = None` |
| `raspe.ans()` | `debug: bool = True`, `headless: bool = True` | `termo: str \| list[str]`, `paginas: range = None` |
| `raspe.anvisa()` | `debug: bool = True`, `headless: bool = True` | `termo: str \| list[str]`, `paginas: range = None` |

## Parametros comuns

### `paginas: range | None`

Controla quantas paginas baixar. `range(1, 4)` baixa paginas 1, 2, 3 (1-based). Default `None` = todas as paginas disponiveis ate o limite da fonte.

**Sempre passe um range pequeno em buscas novas** para checar o volume antes de expandir.

### Listas em parametros de busca

Qualquer parametro "termo-de-busca" (`pesquisa`, `texto`, `termo`, `assunto`) aceita `str` ou `list[str]`. Com lista, o scraper roda a raspagem em sequencia para cada valor e concatena, adicionando uma coluna `termo_busca` para rastreabilidade.

```python
df = raspe.senado().raspar(pesquisa=["educacao", "saude"])
# df['termo_busca'].unique() -> ['educacao', 'saude']
```

Nao passe mais de **um** parametro como lista na mesma chamada — isso levanta `ValueError`.

### Datas

`data_inicio` e `data_fim` aceitam tres formatos, normalizados internamente para `YYYY-MM-DD`:

- `"2024-03-15"` (ISO)
- `"15/03/2024"` (brasileiro)
- `"20240315"` (sem separadores)

## Retorno de `.raspar()`

Sempre `pandas.DataFrame`. As colunas variam por fonte — veja `references/fontes.md` para a matriz completa. A biblioteca sempre adiciona a coluna `termo_busca` quando o parametro de busca foi usado.

## Utilitarios exportados

Em `raspe.*`:

| Funcao | Uso |
|---|---|
| `expand(df, col)` | Expande uma coluna com expressoes logicas em multiplas linhas. |
| `remove_duplicates(df)` | Remove duplicatas considerando colunas-chave padrao. |
| `extract(df, ...)` | Extrai padroes de texto. |
| `check(...)` | Valida estrutura de dados. |
| `validar_data(data_str)` | Normaliza string de data para `YYYY-MM-DD`. |
| `validar_intervalo_datas(inicio, fim)` | Valida e normaliza intervalo. |

## Excecoes

Em `raspe.exceptions` (todas tambem disponiveis em `raspe.*`):

| Classe | Significado | Atributos |
|---|---|---|
| `ScraperError` | Base de todas as excecoes da biblioteca | — |
| `APIKeyError` | API key faltando/invalida (so NYT hoje) | — |
| `RateLimitError` | 429 persistente apos `max_retries` | `retry_after: int \| None` |
| `APIError` | Erro HTTP generico (4xx/5xx nao tratado) | `status_code: int`, `response_text: str` (truncado em 500 chars) |
| `ValidationError` | Parametro invalido (data mal formatada, valor fora de enum) | — |
| `BrowserError` | Falha em Playwright (elemento/timeout/Cloudflare) | — |
| `DriverNotInstalledError` | Playwright nao instalado; subclasse de `BrowserError` | — |

`SeleniumError` existe como alias de `BrowserError` para retrocompatibilidade com codigo antigo. Nao use em codigo novo.

## Retry automatico

`BaseScraper` implementa retry com exponential backoff para:

- **429 (rate limit)**: respeita header `Retry-After` se presente, senao `2^tentativa` segundos. Padrao `max_retries=3`. Apos esgotar, levanta `RateLimitError`.
- **5xx (erro de servidor)**: mesmo esquema. Apos esgotar, levanta `APIError`.

Erros 4xx (exceto 429) nao sao retried — sao devolvidos imediatamente para as subclasses decidirem.

## Configuracoes sensiveis

Em instancias de `BaseScraper`, os seguintes atributos controlam comportamento:

- `sleep_time: int = 2` (NYT: 12, por causa do rate limit). Aumentar e seguro; reduzir causa bloqueio.
- `timeout: tuple[int, int] = (10, 30)` — `(connect, read)` em segundos.
- `max_retries: int = 3`.

Nao modifique esses atributos sem motivo claro (ex.: rede muito lenta justifica `timeout=(30, 120)`).

## Exemplo mininal

```python
import raspe

# Busca simples
df = raspe.presidencia().raspar(pesquisa="meio ambiente", paginas=range(1, 3))
print(df.shape, df.columns.tolist())

# Multiplos termos
df = raspe.senado().raspar(pesquisa=["educacao", "saude"], ano=2024)

# Com datas
df = raspe.folha().raspar(
    pesquisa="reforma tributaria",
    site="online",
    data_inicio="2024-01-01",
    data_fim="2024-06-30",
    paginas=range(1, 5),
)
```
