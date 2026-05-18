# Referência de API — raspe

Assinaturas públicas exportadas em `raspe/__init__.py`. Todas as factories retornam instâncias prontas; todas as instâncias expõem `.raspar(**kwargs) -> pandas.DataFrame`.

## Factories

### Fontes HTTP (não precisam de `[browser]`)

| Factory | Construtor | Parâmetros de `.raspar()` |
|---|---|---|
| `raspe.presidencia()` | sem args | `pesquisa: str \| list[str]`, `paginas: range = None` |
| `raspe.camara()` | sem args | `pesquisa: str \| list[str]`, `ano: int = None`, `tipo_materia: str = None`, `paginas: range = None` |
| `raspe.senado()` | sem args | `pesquisa: str \| list[str]`, `ano: int = None`, `tipo_materia: str = None`, `paginas: range = None` |
| `raspe.cnj()` | sem args | `pesquisa: str \| list[str]`, `data_inicio: str = None`, `data_fim: str = None`, `paginas: range = None` |
| `raspe.ipea()` | sem args | `pesquisa: str \| list[str]`, `paginas: range = None` |
| `raspe.capes()` | sem args | `pesquisa: str \| list[str]`, `paginas: range = None` |
| `raspe.cfm()` | sem args | `texto: str \| list[str]`, `uf: str = ''`, `revogada: str = ''`, `numero: str = ''`, `ano: str = ''`, `paginas: range = None` |
| `raspe.folha()` | sem args | `pesquisa: str \| list[str]`, `site: Literal['todos','online','jornal'] = 'todos'`, `data_inicio: str = None`, `data_fim: str = None`, `paginas: range = None` |
| `raspe.nyt(api_key=...)` | `api_key: str \| None = None` (fallback: env `NYT_API_KEY`) | `texto: str \| list[str]`, `ano: int = None`, `data_inicio: str = None`, `data_fim: str = None`, `sort: Literal['best','newest','oldest','relevance'] = 'newest'`, `filtro: str = ''`, `paginas: range = None` |

### Fontes Playwright (requerem `raspe[browser]`)

| Factory | Construtor | Parâmetros de `.raspar()` |
|---|---|---|
| `raspe.saudelegis()` | `debug: bool = True`, `headless: bool = True` | `assunto: str \| list[str]`, `paginas: range = None` |
| `raspe.ans()` | `debug: bool = True`, `headless: bool = True` | `termo: str \| list[str]`, `paginas: range = None` |
| `raspe.anvisa()` | `debug: bool = True`, `headless: bool = True` | `termo: str \| list[str]`, `paginas: range = None` |

## Parâmetros comuns

### `paginas: range | None`

Controla quantas páginas baixar. `range(1, 4)` baixa páginas 1, 2, 3 (1-based). Default `None` = todas as páginas disponíveis até o limite da fonte.

**Sempre passe um range pequeno em buscas novas** para checar o volume antes de expandir.

### Listas em parâmetros de busca

Qualquer parâmetro "termo-de-busca" (`pesquisa`, `texto`, `termo`, `assunto`) aceita `str` ou `list[str]`. Com lista, o scraper roda a raspagem em sequência para cada valor e concatena, adicionando uma coluna `termo_busca` para rastreabilidade.

```python
df = raspe.senado().raspar(pesquisa=["educação", "saúde"])
# df['termo_busca'].unique() -> ['educação', 'saúde']
```

Não passe mais de **um** parâmetro como lista na mesma chamada — isso levanta `ValueError`.

### Datas

`data_inicio` e `data_fim` aceitam três formatos, normalizados internamente para `YYYY-MM-DD`:

- `"2024-03-15"` (ISO)
- `"15/03/2024"` (brasileiro)
- `"20240315"` (sem separadores)

## Retorno de `.raspar()`

Sempre `pandas.DataFrame`. As colunas variam por fonte — veja `references/fontes.md` para a matriz completa. A biblioteca sempre adiciona a coluna `termo_busca` quando o parâmetro de busca foi usado.

## Utilitários exportados

Em `raspe.*`:

| Função | Uso |
|---|---|
| `expand(df, col)` | Expande uma coluna com expressões lógicas em múltiplas linhas. |
| `remove_duplicates(df)` | Remove duplicatas considerando colunas-chave padrão. |
| `extract(df, ...)` | Extrai padrões de texto. |
| `check(...)` | Valida estrutura de dados. |
| `validar_data(data_str)` | Normaliza string de data para `YYYY-MM-DD`. |
| `validar_intervalo_datas(inicio, fim)` | Valida e normaliza intervalo. |

## Exceções

Em `raspe.exceptions` (todas também disponíveis em `raspe.*`):

| Classe | Significado | Atributos |
|---|---|---|
| `ScraperError` | Base de todas as exceções da biblioteca | — |
| `APIKeyError` | API key faltando/inválida (só NYT hoje) | — |
| `RateLimitError` | 429 persistente após `max_retries` | `retry_after: int \| None` |
| `APIError` | Erro HTTP genérico (4xx/5xx não tratado) | `status_code: int`, `response_text: str` (truncado em 500 chars) |
| `ValidationError` | Parâmetro inválido (data mal formatada, valor fora de enum) | — |
| `BrowserError` | Falha em Playwright (elemento/timeout/Cloudflare) | — |
| `DriverNotInstalledError` | Playwright não instalado; subclasse de `BrowserError` | — |

`SeleniumError` existe como alias de `BrowserError` para retrocompatibilidade com código antigo. Não use em código novo.

## Retry automático

`BaseScraper` implementa retry com exponential backoff para:

- **429 (rate limit)**: respeita header `Retry-After` se presente, senão `2^tentativa` segundos. Padrão `max_retries=3`. Após esgotar, levanta `RateLimitError`.
- **5xx (erro de servidor)**: mesmo esquema. Após esgotar, levanta `APIError`.

Erros 4xx (exceto 429) não são retried — são devolvidos imediatamente para as subclasses decidirem.

## Configurações sensíveis

Em instâncias de `BaseScraper`, os seguintes atributos controlam comportamento:

- `sleep_time: int = 2` (NYT: 12, por causa do rate limit). Aumentar é seguro; reduzir causa bloqueio.
- `timeout: tuple[int, int] = (10, 30)` — `(connect, read)` em segundos.
- `max_retries: int = 3`.

Não modifique esses atributos sem motivo claro (ex.: rede muito lenta justifica `timeout=(30, 120)`).

## Exemplo mininal

```python
import raspe

# Busca simples
df = raspe.presidencia().raspar(pesquisa="meio ambiente", paginas=range(1, 3))
print(df.shape, df.columns.tolist())

# Múltiplos termos
df = raspe.senado().raspar(pesquisa=["educação", "saúde"], ano=2024)

# Com datas
df = raspe.folha().raspar(
    pesquisa="reforma tributária",
    site="online",
    data_inicio="2024-01-01",
    data_fim="2024-06-30",
    paginas=range(1, 5),
)
```
