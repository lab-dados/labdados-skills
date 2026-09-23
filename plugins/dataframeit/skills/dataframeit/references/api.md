# DataFrameIt — Referencia core da API

Este arquivo cobre apenas o **core da API**: instalacao, assinatura da
`dataframeit()`, entrada/retorno, funcoes utilitarias, tratamento de
erros e gotchas criticos.

Para topicos especializados, consulte as demais references:

| Topico | Arquivo |
|---|---|
| Desenho do modelo Pydantic, `json_schema_extra`, campos condicionais, self-reflection | `pydantic-patterns.md` |
| Busca web (Tavily/Exa), `search_per_field`, `search_groups`, custos de busca | `busca-web.md` |
| Paralelismo, `rate_limit_delay`, tokens/custo, resume, `batch_size`/`checkpoint_path`, truncamento, trace | `runs-longos.md` |
| Workflows de ponta a ponta | `exemplos.md` |
| Hiperparametros por modelo, modo Claude Code, §Groq | `modelos-parametros.md` |

## Indice

1. [Instalacao](#instalacao)
2. [Funcao principal — dataframeit()](#funcao-principal--dataframeit)
3. [Parametros em detalhe](#parametros-em-detalhe)
4. [Modelo e temperature](#modelo-e-temperature)
5. [Tipos de entrada aceitos](#tipos-de-entrada-aceitos)
6. [Retorno — estrutura do DataFrame](#retorno--estrutura-do-dataframe)
7. [Funcoes utilitarias](#funcoes-utilitarias)
8. [Tratamento de erros](#tratamento-de-erros)
9. [Gotchas criticos](#gotchas-criticos)

---

## Instalacao

```bash
pip install dataframeit[google]         # Google Gemini (padrao, recomendado)
pip install dataframeit[openai]         # OpenAI
pip install dataframeit[anthropic]      # Anthropic
pip install dataframeit[groq]           # Groq
pip install dataframeit[claude-code]    # provider='claude_code' (claude-agent-sdk)
pip install dataframeit[all]            # extras acima + Tavily, Exa, polars e excel
pip install dataframeit[google,search]      # Gemini + busca web com Tavily
pip install dataframeit[google,search-exa]  # Gemini + busca web com Exa
pip install dataframeit[google,search-all]  # Gemini + Tavily e Exa
pip install dataframeit[google,polars]  # Gemini + suporte Polars
pip install dataframeit[google,excel]   # Gemini + leitura/escrita .xlsx via openpyxl

# Outros provedores do LangChain: instalar o pacote de integracao a parte
pip install dataframeit langchain-mistralai   # provider='mistralai'
pip install dataframeit langchain-cohere      # provider='cohere'
```

Nao existem extras `[mistral]` nem `[cohere]`. O pip ignora extra
inexistente com um aviso e instala o dataframeit sem o pacote de
integracao, e a falha so aparece na primeira chamada.

Python >= 3.10 obrigatorio.

---

## Funcao principal — `dataframeit()`

```python
from dataframeit import dataframeit

resultado = dataframeit(
    data,                                # DataFrame | Series | list | dict
    questions,                           # type[BaseModel] — classe Pydantic (nao instancia)
    prompt,                              # str — instrucao com placeholder {texto}
    perguntas=None,                      # alias portugues para questions
    resume=True,                         # bool — pular linhas ja processadas
    reprocess_columns=None,              # list[str] | None — reprocessar apenas colunas especificas
    model='gemini-3-flash-preview',      # str — identificador do modelo LLM
    provider='google_genai',             # str — provedor LLM
    status_column=None,                  # str | None — nome customizado da coluna de status
    text_column=None,                    # str | None — coluna de texto (inferida se None)
    api_key=None,                        # str | None — None=le da variavel de ambiente
    max_retries=3,                       # int — tentativas por linha em caso de erro
    base_delay=1.0,                      # float — delay inicial (segundos) para backoff exponencial
    max_delay=30.0,                      # float — delay maximo (segundos) para backoff
    rate_limit_delay=0.0,                # float — delay entre requisicoes (controle de rate limit)
    track_tokens=True,                   # bool — adicionar _input_tokens/_output_tokens/_reasoning_tokens
    model_kwargs=None,                   # dict | None — kwargs extras repassados ao LLM
    parallel_requests=1,                 # int — workers paralelos (1=sequencial)
    use_search=False,                    # bool — habilitar busca web
    search_provider="tavily",            # str — "tavily" | "exa"
    search_per_field=False,              # bool — busca separada por campo
    max_results=5,                       # int — max resultados de busca (1-20)
    search_depth="basic",                # str — "basic" | "advanced"
    search_groups=None,                  # dict[str, dict] | None — agrupar campos para busca
    save_trace=None,                     # bool | "full" | "minimal" | None — capturar raciocinio
    batch_size=None,                     # int | None — tamanho do lote para checkpointing
    checkpoint_path=None,                # str | Path | None — .csv, .xlsx ou .parquet persistido a cada batch
)
```

---

## Parametros em detalhe

| Parametro | Tipo | Default | Descricao |
|---|---|---|---|
| `data` | DataFrame, Series, list, dict | — | Dados de entrada contendo texto |
| `questions` | type[BaseModel] | — | Classe Pydantic definindo os campos de saida |
| `prompt` | str | — | Instrucao para o LLM. Use `{texto}` para referenciar o conteudo da linha |
| `perguntas` | type[BaseModel] | None | Alias portugues para `questions` |
| `resume` | bool | **True** | Pula linhas com `_dataframeit_status == "processed"` |
| `reprocess_columns` | list[str] | None | Reprocessa apenas as colunas listadas |
| `model` | str | `'gemini-3-flash-preview'` | Identificador do modelo LLM |
| `provider` | str | `'google_genai'` | Nome de provedor do `init_chat_model` do LangChain (`'google_genai'`, `'openai'`, `'anthropic'`, `'groq'`, `'mistralai'`, `'cohere'`, ...) ou `'claude_code'` |
| `status_column` | str | None | Nome customizado para a coluna de status (padrao: `_dataframeit_status`) |
| `text_column` | str | None | Coluna do DataFrame a usar como texto. Se None, a biblioteca tenta inferir entre `texto`, `text`, `decisao`, `content`, `content_text`; DataFrames de uma unica coluna usam-na direto; se nao bater, levanta `ValueError` |
| `api_key` | str | None | API key. Se None, le da variavel de ambiente do provedor |
| `max_retries` | int | 3 | Maximo de tentativas com backoff exponencial |
| `base_delay` | float | 1.0 | Delay inicial em segundos (dobra a cada tentativa) |
| `max_delay` | float | 30.0 | Delay maximo em segundos (teto do backoff) |
| `rate_limit_delay` | float | 0.0 | Delay adicional entre requisicoes em segundos |
| `track_tokens` | bool | **True** | Adiciona `_input_tokens`, `_output_tokens` e `_reasoning_tokens` ao resultado |
| `model_kwargs` | dict | None | Kwargs extras repassados ao cliente LangChain do provedor. O dataframeit ja injeta `temperature=0`; o que vier aqui sobrescreve (ver §Modelo e temperature) |
| `parallel_requests` | int | 1 | Numero de workers paralelos |
| `use_search` | bool | False | Habilita busca web (Tavily ou Exa) |
| `search_provider` | str | `"tavily"` | `"tavily"` ou `"exa"` |
| `search_per_field` | bool | False | Executa uma busca separada para cada campo habilitado |
| `max_results` | int | 5 | Maximo de resultados de busca por consulta (1-20) |
| `search_depth` | str | `"basic"` | `"basic"` (1 credito) ou `"advanced"` (2 creditos) |
| `search_groups` | dict[str, dict] | None | Agrupa campos para compartilhar busca (ver `busca-web.md`) |
| `save_trace` | bool, str, None | None | `None`=desligado, `True` ou `"full"`=completo, `"minimal"`=resumido |
| `batch_size` | int | None | Tamanho do lote processado antes de cada checkpoint. Requer `checkpoint_path` |
| `checkpoint_path` | str \| Path | None | Arquivo onde o progresso parcial e persistido a cada `batch_size` linhas. Formato pela extensao: `.csv`, `.xlsx` (requer `[excel]`) ou `.parquet` (requer `pyarrow`). Usar junto com `batch_size`, senao `ValueError` |

Para orientacoes de `model_kwargs` por modelo (quais parametros aceita,
quais nao), veja `modelos-parametros.md`.

---

## Modelo e temperature

Nao ha modelo padrao por provedor. O unico default e
`model='gemini-3-flash-preview'`, pensado para `provider='google_genai'`.
Ao trocar de `provider`, passe `model=` junto; sem isso, o nome do
Gemini vai para o outro provedor e a chamada falha.

```python
resultado = dataframeit(df, Modelo, prompt, provider='openai', model='gpt-4.1-mini')
resultado = dataframeit(df, Modelo, prompt, provider='anthropic', model='claude-haiku-4-5')
resultado = dataframeit(df, Modelo, prompt, provider='groq', model='openai/gpt-oss-120b')
```

O mesmo vale para `provider='claude_code'`: o dataframeit repassa
`model` ao `claude-agent-sdk`, entao passe um alias (`'haiku'`,
`'sonnet'`, `'opus'`) ou um ID Claude.

Nos provedores via LangChain, o dataframeit cria o cliente com
`temperature=0` e depois aplica `model_kwargs`. Duas consequencias:

- Modelo que nao aceita `temperature` (ex.: Claude Sonnet 5, Opus 4.7
  ou mais novo, OpenAI GPT-6 com raciocinio ligado, que e o padrao,
  OpenAI o1/o3) recebe `temperature=0` e responde com erro 400. Passe `model_kwargs={'temperature': None}` para nao enviar
  o parametro. No Claude Fable o erro aparece antes da chamada, como
  `ValueError` do `langchain-anthropic`, e a saida e a mesma. Na
  familia GPT-5 o `langchain-openai` ja tira o parametro sozinho, mas
  na GPT-6 nao (conferido com `langchain-openai` 1.6.5 e
  `langchain-anthropic` 1.7.4).
- Recomendacao de temperatura diferente de 0 (ex.: Gemini 3 com 1.0)
  so vale se for passada explicitamente em `model_kwargs`.

Nomes de modelo e parametros aceitos por familia estao em
`modelos-parametros.md`.

---

## Tipos de entrada aceitos

```python
import pandas as pd
from dataframeit import dataframeit

# DataFrame (mais comum)
df = pd.DataFrame({"texto": ["texto 1", "texto 2"]})
resultado = dataframeit(df, Modelo, "Analise: {texto}")

# Series
s = pd.Series(["texto 1", "texto 2"], name="texto")
resultado = dataframeit(s, Modelo, "Analise: {texto}")

# Lista de strings
resultado = dataframeit(["texto 1", "texto 2"], Modelo, "Analise: {texto}")

# Lista de dicts
resultado = dataframeit(
    [{"texto": "t1", "autor": "a1"}],
    Modelo,
    "Analise: {texto}"
)

# Dict unico
resultado = dataframeit({"texto": "meu texto"}, Modelo, "Analise: {texto}")
```

**`text_column`**: Se `text_column=None` (padrao), o `dataframeit`
infere automaticamente:

1. DataFrames de uma unica coluna usam-na direto.
2. DataFrames com multiplas colunas procuram, nessa ordem: `texto`,
   `text`, `decisao`, `content`, `content_text`.
3. Se nenhum candidato bater, a chamada levanta `ValueError` — nao
   ha risco de a biblioteca usar silenciosamente uma coluna arbitraria.

Mesmo com inferencia, passe `text_column='nome_da_coluna'` em pipelines
de producao sempre que a coluna nao estiver entre os candidatos default
(ex: `ementa`, `acordao`, `mensagem`) — torna o contrato do pipeline
explicito.

---

## Retorno — estrutura do DataFrame

A funcao retorna os dados no mesmo formato da entrada (DataFrame,
Series, list ou dict) com as colunas originais + campos extraidos +
colunas de controle:

| Coluna | Tipo | Quando aparece | Descricao |
|---|---|---|---|
| `<campos do modelo>` | conforme Pydantic | sempre | Valores extraidos pelo LLM |
| `_dataframeit_status` | str | **apenas se houver erros** | `"processed"` ou `"error"`. **IMPORTANTE**: quando todas as linhas processam com sucesso, a biblioteca remove essa coluna (e `_error_details`) do DataFrame retornado. Use `df.get("_dataframeit_status", pd.Series(dtype=str))` para checar com seguranca. |
| `_error_details` | str \| None | **apenas se houver erros** | Mensagem de erro — removida junto com `_dataframeit_status` quando nao ha erros. |
| `_input_tokens` | int | `track_tokens=True` (padrao) | Tokens de entrada consumidos |
| `_output_tokens` | int | `track_tokens=True` (padrao) | Tokens de saida consumidos |
| `_reasoning_tokens` | int | `track_tokens=True` (padrao) | Tokens de raciocinio "invisiveis" consumidos por reasoning models (o1/o3, GPT-5 raciocinio, Claude adaptive thinking). Ja contidos em `_output_tokens`. Vale `0` para modelos nao-raciocinio. |
| `_search_credits` | int | `use_search=True` | Creditos do provedor de busca consumidos na linha (ver `busca-web.md`) |

Nao existe uma coluna `_total_tokens` agregada. Para o total, some
`_input_tokens + _output_tokens`; `_reasoning_tokens` ja esta contido em `_output_tokens` (o resumo impresso pelo dataframeit mostra "incluido no Output").
O contador interno de buscas (`_search_count`) tambem nao aparece no
DataFrame; roda por tras para alimentar os warnings de rate limit do
provedor de busca.

Para calculo de custo por provedor a partir dessas colunas, veja
`runs-longos.md`.

---

## Funcoes utilitarias

### read_df

Carrega DataFrames de diversos formatos com normalizacao automatica de
JSON:

```python
from dataframeit import read_df

df = read_df('dados.csv')
df = read_df('dados.xlsx')         # requer pip install dataframeit[excel]
df = read_df('dados.parquet')
df = read_df('dados.json')

# Com modelo Pydantic para guiar normalizacao de campos complexos
df = read_df('dados.json', model=MeuModelo)

# Sem normalizacao automatica
df = read_df('dados.csv', normalize=False)

# Kwargs extras sao repassados ao pandas
df = read_df('dados.csv', encoding='latin1', sep=';')
```

**Assinatura**:
```python
def read_df(path: str, model=None, normalize: bool = True, **kwargs) -> pd.DataFrame
```

### normalize_value

Converte strings JSON de volta para objetos Python:

```python
from dataframeit import normalize_value

normalize_value('["a", "b"]')       # → ['a', 'b']
normalize_value('{"k": "v"}')       # → {'k': 'v'}
normalize_value('texto simples')    # → 'texto simples' (sem alteracao)
```

### normalize_complex_columns

Normaliza colunas com tipos complexos (listas, dicts) em um DataFrame
inteiro:

```python
from dataframeit import normalize_complex_columns, get_complex_fields

campos_complexos = get_complex_fields(MeuModelo)
normalize_complex_columns(df, campos_complexos)  # modifica in-place
```

### get_complex_fields

Identifica campos com tipos complexos em um modelo Pydantic:

```python
from dataframeit import get_complex_fields

class MeuModelo(BaseModel):
    nome: str
    tags: list[str]
    endereco: dict

campos = get_complex_fields(MeuModelo)
# → {'tags', 'endereco'}
```

---

## Tratamento de erros

### Erros recuperaveis (retentados automaticamente)

| Erro | Causa | Acao do dataframeit |
|---|---|---|
| Rate limit (429) | Muitas requisicoes | Retry com backoff exponencial |
| Timeout | Provedor lento | Retry com backoff |
| Erro de servidor (502, 503) | Instabilidade do provedor | Retry com backoff |
| Erro de conexao / SSL | Rede instavel | Retry com backoff |

### Erros nao recuperaveis (falha imediata)

| Erro | Causa | Remedio |
|---|---|---|
| `AuthenticationError` (401) | API key incorreta ou ausente | Verificar variavel de ambiente |
| `PermissionDenied` (403) | Key sem permissao | Verificar permissoes da key no painel do provedor |
| `InvalidArgument` | Parametro invalido | Corrigir parametros |

### Backoff exponencial

A sequencia de retries segue: `base_delay * (2 ^ tentativa)` com jitter
aleatorio, limitada por `max_delay`.

Com defaults (`base_delay=1.0`, `max_delay=30.0`, `max_retries=3`):
- Tentativa 1: ~1s
- Tentativa 2: ~2s
- Tentativa 3: ~4s

Para ajustar o comportamento em runs longos, veja `runs-longos.md §Rate
limiting`.

---

## Gotchas criticos

1. **Passe a classe Pydantic, nao uma instancia** — `dataframeit(df, Modelo, ...)`
   nao `dataframeit(df, Modelo(), ...)`. Passar instancia levanta erro.

2. **`Optional[str]` vs `str`** — Use `Optional` para campos que podem
   nao existir no texto. Campos obrigatorios (`str`) forcam o LLM a
   inventar um valor se nao encontrar.

3. **`Field(description=...)` e o investimento mais barato** — Uma boa
   descricao reduz erros de extracao mais do que trocar de provedor ou
   aumentar o modelo. Ver `pydantic-patterns.md`.

4. **`resume=True` e o padrao** — Na primeira execucao funciona
   normalmente (nao ha `_dataframeit_status` para pular). Em execucoes
   subsequentes, pula linhas ja processadas.

5. **`reprocess_columns` nao reprocessa a linha inteira** — Apenas os
   campos especificados. Os demais campos extraidos anteriormente sao
   mantidos.

6. **`search_groups` reduz chamadas de busca** — Sem grupos, cada campo
   `search_enabled` dispara uma busca separada por linha. Com grupos,
   campos do mesmo grupo compartilham uma unica busca. Configure sempre
   que tiver 2+ campos com busca. Ver `busca-web.md`.

7. **`save_trace=True` gera dados volumosos** — Para datasets grandes,
   use primeiro com uma amostra pequena (`df.head(5)`) para validar a
   extracao.

8. **`parallel_requests` nao escala ilimitado** — Acima de ~10 workers,
   a maioria dos provedores retorna 429. Comece com `parallel_requests=1`
   (padrao) e aumente conforme necessario. Ver `runs-longos.md`.

9. **Campos condicionais so valem com busca por campo** — `depends_on`
   e `condition` so sao avaliados com `use_search=True,
   search_per_field=True` e sem `search_groups`. Nesse modo a ordem de
   declaracao no modelo nao importa: a biblioteca ordena os campos
   pelas dependencias. Fora desse modo, a condicao e ignorada e todos
   os campos sao extraidos. Ver `pydantic-patterns.md §Padrao 4`.

10. **`provider=` e case-sensitive** — `'Google'` falha. Use minusculas:
    `'google_genai'`, `'openai'`, `'anthropic'`, `'groq'`, `'mistralai'`
    (nao `'mistral'`), `'cohere'`, `'claude_code'`.

11. **`model=` e o LLM, nao o Pydantic** — O parametro `model` define
    qual modelo de linguagem usar (ex: `'gemini-3-flash-preview'`). O
    modelo Pydantic e passado como `questions` (segundo argumento
    posicional).

12. **`{texto}` no prompt e obrigatorio** — O placeholder `{texto}` no
    prompt e substituido pelo conteudo da linha. Sem ele, o LLM nao
    recebe o texto a analisar.

13. **Polars requer extra** — `pip install dataframeit[polars]`. Sem o
    extra, passar um Polars DataFrame levanta `ImportError`.

14. **`perguntas` e alias de `questions`** — Ambos aceitam a classe
    Pydantic. Use o que preferir, mas nao passe os dois simultaneamente.

15. **`track_tokens=True` e o padrao** — As colunas `_input_tokens`,
    `_output_tokens` e `_reasoning_tokens` ja aparecem sem configuracao
    adicional. Para desabilitar, passe
    `track_tokens=False` explicitamente.
