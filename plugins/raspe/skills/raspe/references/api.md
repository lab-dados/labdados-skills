# Referência de API — raspe

Assinaturas públicas exportadas em `raspe/__init__.py`. Todas as factories retornam instâncias prontas; todas as instâncias expõem `.raspar(**kwargs) -> pandas.DataFrame`. `.scrape(**kwargs)` existe como alias de `.raspar()`, mantido por retrocompatibilidade; em código novo, use `.raspar()`. A versão instalada fica em `raspe.__version__`.

## Factories

### Fontes HTTP (não precisam de `[browser]`)

| Factory | Construtor | Parâmetros de `.raspar()` |
|---|---|---|
| `raspe.presidencia()` | sem args | `pesquisa: str \| list[str]`, `paginas: range = None` |
| `raspe.camara()` | sem args | `pesquisa: str \| list[str] = ''`, `ano: int = None`, `tipo_materia: str = ''`, `paginas: range = None` |
| `raspe.senado()` | sem args | `pesquisa: str \| list[str] = ''`, `ano: int = None`, `tipo_materia: str = ''`, `paginas: range = None` |
| `raspe.ipea()` | sem args | `pesquisa: str \| list[str]`, `paginas: range = None` |
| `raspe.capes()` | sem args | `pesquisa: str \| list[str]`, `paginas: range = None` |
| `raspe.cfm()` | sem args | `pesquisa: str \| list[str] = ''`, `uf: str = ''`, `revogada: str = ''`, `numero: str = ''`, `ano: int = None`, `paginas: range = None` |
| `raspe.folha()` | sem args | `pesquisa: str \| list[str]`, `site: Literal['todos','online','jornal'] = 'todos'`, `data_inicio: str = None`, `data_fim: str = None`, `paginas: range = None` |
| `raspe.nyt(api_key=...)` | `api_key: str \| None = None` (fallback: env `NYT_API_KEY`) | `pesquisa: str \| list[str] = ''`, `ano: int = None`, `data_inicio: str = None`, `data_fim: str = None`, `sort: Literal['best','newest','oldest','relevance'] = 'newest'`, `filtro: str = ''`, `paginas: range = None` |

### Fontes Playwright (requerem `raspe[browser]`)

| Factory | Construtor | Parâmetros de `.raspar()` |
|---|---|---|
| `raspe.saudelegis()` | `debug: bool = True`, `headless: bool = True` | `pesquisa: str` |
| `raspe.ans()` | `debug: bool = True`, `headless: bool = True` | `pesquisa: str` |
| `raspe.anvisa()` | `debug: bool = True`, `headless: bool = True` | `pesquisa: str` |

Essas três fontes não aceitam `paginas`: passá-lo levanta `ValidationError` antes de abrir o navegador. A coleta percorre todas as páginas que o site informa na primeira tela de resultados, até o teto `_max_pages` (50 no SaudeLegis, 100 em ANS e ANVISA). Se o site informar mais páginas que o teto, a coleta para nele e emite `UserWarning`. O teto é atributo interno da instância, sem parâmetro público, e é o único controle de volume. Para uma coleta de teste curta:

```python
s = raspe.anvisa()
s._max_pages = 3  # atributo interno; pode mudar em versões futuras
df = s.raspar(pesquisa="dispositivo médico")
```

## Parâmetros comuns

### `paginas: range | None`

Controla quantas páginas baixar, **só nas fontes HTTP** (nas Playwright, levanta `ValidationError`; ver acima). `range(1, 4)` baixa páginas 1, 2, 3 (1-based). Default `None` = todas as páginas disponíveis até o limite da fonte.

**Sempre passe um range pequeno em buscas novas** para checar o volume antes de expandir.

### Listas em parâmetros de busca

Todas as fontes buscam por `pesquisa`. Os nomes antigos (`texto` em `cfm` e `nyt`, `assunto` em `saudelegis`, `termo` em `ans` e `anvisa`) ainda são aceitos, com `DeprecationWarning`. Nas fontes HTTP, `pesquisa` aceita `str` ou `list[str]`. Com lista, o scraper roda a raspagem em sequência para cada valor e concatena, adicionando uma coluna `termo_busca` para rastreabilidade. As fontes Playwright (`saudelegis`, `ans`, `anvisa`) recusam lista com `ValidationError`: passe uma string por chamada.

```python
df = raspe.senado().raspar(pesquisa=["educação", "saúde"])
# df['termo_busca'].unique() -> ['educação', 'saúde']
```

Só `pesquisa` aceita lista. Lista em outro parâmetro, ou parâmetro desconhecido, levanta `ValidationError`, em todas as fontes.

### Datas

`data_inicio` e `data_fim` aceitam três formatos, normalizados internamente para `YYYY-MM-DD`:

- `"2024-03-15"` (ISO)
- `"15/03/2024"` (brasileiro)
- `"20240315"` (sem separadores)

## Retorno de `.raspar()`

Sempre `pandas.DataFrame`. As colunas variam por fonte — veja `references/fontes.md` para a matriz completa.

Nas fontes com schema de saída, o DataFrame sempre termina na coluna `termo_busca`, com o valor de `pesquisa` ou, numa busca com lista, o item de cada linha; as colunas saem na ordem do schema, e uma busca sem resultado devolve DataFrame vazio com essas mesmas colunas. As fontes ainda sem schema de saída (veja a matriz de colunas da `references/fontes.md`) também terminam em `termo_busca`, vazia quando a busca foi sem `pesquisa`.

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

Em `raspe.exceptions` (todas também disponíveis em `raspe.*`). O que fazer com cada uma e os avisos de resultado incompleto (`UserWarning`) estão em "Tratamento de erros" na `SKILL.md`.

| Classe | Quando sobe | Atributos |
|---|---|---|
| `ScraperError` | Base de todas. Sozinha: resposta inicial que não é página de resultados (manutenção, acesso recusado, verificação anti-robô, layout novo); nenhuma página baixada rendeu linhas (a mensagem traz o erro de cada página, e o primeiro fica em `__cause__`; página em que nenhum item pôde ser lido conta como sem linhas, com esse erro); nas fontes Playwright, página da contagem que não abre | — |
| `APIKeyError` | NYT sem API key (no construtor) ou com key inválida (401) | — |
| `RateLimitError` | 429 persistente após `max_retries`, em qualquer página | `retry_after: int \| None` (o `Retry-After` do servidor, em segundos) |
| `APIError` | 5xx persistente após `max_retries`, em qualquer página; no NYT, também outro 4xx na página 1 ou resposta sem a contagem de resultados | `status_code: int`, `response_text: str` (truncado em 500 chars) |
| `ValidationError` | Parâmetro inválido ou desconhecido (data mal formatada, valor fora de enum, `pesquisa` vazia onde é obrigatória), antes de qualquer requisição | — |
| `BrowserError` | Falha em Playwright (elemento não encontrado, timeout, bypass de Cloudflare) | — |
| `DriverNotInstalledError` | Fonte Playwright sem o extra `[browser]`, no `.raspar()`; subclasse de `BrowserError` | — |

Fora da hierarquia, sobem os erros do `requests` descritos em "Retry automático". `SeleniumError` existe como alias de `BrowserError` para retrocompatibilidade com código antigo. Não use em código novo.

## Retry automático

Nas fontes HTTP, toda requisição, da página 1 (que também dá a contagem de páginas) às seguintes, passa por `_request_with_retry`, com até `max_retries=3` tentativas:

- **429 (rate limit)**: espera o header `Retry-After`, limitado a `max_retry_after=300` segundos, ou `2^tentativa` segundos sem ele. Esgotadas as tentativas, `RateLimitError`.
- **5xx (erro de servidor)**: espera `2^tentativa` segundos. Esgotadas as tentativas, `APIError`.
- **Falha de conexão** (inclusive `ConnectTimeout`): mesmo esquema. Esgotadas as tentativas, sobe o `requests.ConnectionError`.
- **`ReadTimeout`** (o servidor recebeu o pedido e não respondeu dentro de `timeout`): sobe na hora, sem nova tentativa.
- **Outro 4xx**: sem nova tentativa; sobe como `requests.HTTPError` (no NYT, na página 1, como `APIKeyError` ou `APIError`).

Qualquer um desses erros interrompe a coleta e sobe para quem chamou `.raspar()`: nenhuma página é pulada. Numa busca com lista, interrompe só a coleta daquele valor, que fica de fora com `UserWarning`.

## Seleção por nome (`scraper_manager`)

Além das factories, `raspe.scraper_manager.scraper(nome, **kwargs)` devolve o scraper pelo nome, sem diferenciar maiúsculas. Hoje cobre só `PRESIDENCIA`, `IPEA`, `SENADO`, `CAMARA` e `CAPES`; outro nome levanta `ValueError`. Os `kwargs` vão para o construtor, não para `.raspar()`. O módulo não é importado por `import raspe`, então importe-o explicitamente:

```python
from raspe.scraper_manager import scraper

df = scraper("capes").raspar(pesquisa="natjus", paginas=range(1, 2))
```

## Configurações sensíveis

Em instâncias de `BaseScraper`, os seguintes atributos controlam comportamento:

- `sleep_time: int = 2` (NYT: 12, por causa do rate limit). Aumentar é seguro; reduzir causa bloqueio.
- `timeout: tuple[int, int] = (10, 30)` — `(connect, read)` em segundos.
- `max_retries: int = 3`.
- `max_retry_after: int = 300` — espera máxima, em segundos, pedida pelo `Retry-After` de um 429.

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
