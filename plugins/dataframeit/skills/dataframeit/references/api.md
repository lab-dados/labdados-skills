# DataFrameIt: referência core da API

Este arquivo cobre só o **core da API**: instalação, assinatura da `dataframeit()`, entrada e retorno, funções utilitárias, exceções, tratamento de erros e gotchas críticos. A referência oficial fica em https://brunodcdo.com.br/dataframeit/reference/api/, e a página de perguntas frequentes em https://brunodcdo.com.br/dataframeit/guides/faq/.

Para tópicos especializados, consulte as demais references:

| Tópico | Arquivo |
|---|---|
| Desenho do modelo Pydantic, `json_schema_extra`, campos condicionais, self-reflection | `pydantic-patterns.md` |
| Busca web (Tavily/Exa), `search_per_field`, `search_groups`, `max_search_calls`, custos de busca | `busca-web.md` |
| Paralelismo, `rate_limit_delay`, tokens/custo, resume, `batch_size`/`checkpoint_path`, truncamento, trace | `runs-longos.md` |
| Workflows de ponta a ponta | `exemplos.md` |
| Hiperparâmetros por modelo, Claude Code e Codex | `modelos-parametros.md` |

## Índice

1. [Instalação](#instalação)
2. [Função principal: dataframeit()](#função-principal-dataframeit)
3. [Parâmetros em detalhe](#parâmetros-em-detalhe)
4. [Modelo e temperature](#modelo-e-temperature)
5. [Tipos de entrada aceitos](#tipos-de-entrada-aceitos)
6. [Retorno: estrutura do DataFrame](#retorno-estrutura-do-dataframe)
7. [Funções utilitárias](#funções-utilitárias)
8. [Exceções](#exceções)
9. [Tratamento de erros e retry](#tratamento-de-erros-e-retry)
10. [Gotchas críticos](#gotchas-críticos)

---

## Instalação

```bash
pip install dataframeit[openai]         # OpenAI (provider padrão)
pip install dataframeit[google]         # Google Gemini
pip install dataframeit[anthropic]      # Anthropic
pip install dataframeit[groq]           # Groq
pip install dataframeit[claude-code]    # provider='claude_code' (claude-agent-sdk)
pip install dataframeit[codex]          # provider='codex' (experimental, fora do [all])
pip install dataframeit[all]            # openai, google, anthropic, groq, claude-code, Tavily, Exa, polars e excel
pip install dataframeit[openai,search]      # OpenAI + busca web com Tavily
pip install dataframeit[openai,search-exa]  # OpenAI + busca web com Exa
pip install dataframeit[openai,search-all]  # OpenAI + Tavily e Exa
pip install dataframeit[openai,polars]  # OpenAI + polars (traz pyarrow, para .parquet)
pip install dataframeit[openai,excel]   # OpenAI + leitura e checkpoint em .xlsx via openpyxl

# Outros provedores do LangChain: instalar o pacote de integração à parte
pip install dataframeit langchain-mistralai   # provider='mistralai'
pip install dataframeit langchain-cohere      # provider='cohere'
```

Não existem extras `[mistral]` nem `[cohere]`. O pip ignora extra inexistente com um aviso e instala o dataframeit sem o pacote de integração. Quando falta o extra de um provider que tem extra, a chamada levanta `ImportError` antes de processar, e a mensagem diz o que instalar.

Python >= 3.10 obrigatório.

---

## Função principal: `dataframeit()`

```python
from dataframeit import dataframeit

resultado = dataframeit(
    data,                                # DataFrame | Series | list | dict
    questions,                           # type[BaseModel]: classe Pydantic (não instância)
    prompt,                              # str: instrução com placeholder {texto}
    perguntas=None,                      # obsoleto: nome antigo de questions (DeprecationWarning)
    resume=True,                         # bool: processar só linhas sem status
    reprocess_columns=None,              # list[str] | None: refazer só essas colunas
    model=None,                          # str | None: None usa o modelo padrão do provider
    provider='openai',                   # str: provedor LLM
    status_column=None,                  # str | None: nome da coluna de status
    text_column=None,                    # str | None: coluna de texto (inferida se None)
    api_key=None,                        # str | None: None lê da variável de ambiente
    max_retries=3,                       # int >= 1: tentativas totais por linha, contando a primeira
    base_delay=1.0,                      # float: espera antes da primeira nova tentativa (s)
    max_delay=30.0,                      # float: teto da espera entre tentativas (s)
    rate_limit_delay=0.0,                # float: pausa de cada worker depois de cada linha bem-sucedida (s)
    track_tokens=True,                   # bool: colunas de tokens
    model_kwargs=None,                   # dict | None: kwargs repassados ao cliente do LLM
    parallel_requests=1,                 # int: workers paralelos (1 = sequencial)
    use_search=False,                    # bool: habilitar busca web
    search_provider="tavily",            # str: "tavily" | "exa"
    search_per_field=False,              # bool: um agente por campo
    max_results=5,                       # int: resultados por busca (1-20)
    search_depth="basic",                # str: "basic" | "advanced" (só Tavily)
    max_search_calls=10,                 # int >= 1: máximo de buscas por execução do agente
    search_groups=None,                  # dict[str, dict] | None: campos que compartilham um agente
    save_trace=None,                     # bool | "full" | "minimal" | None: trace do agente (exige busca)
    batch_size=None,                     # int | None: checkpoint a cada N linhas
    checkpoint_path=None,                # str | Path | None: .csv, .xlsx ou .parquet
)
```

---

## Parâmetros em detalhe

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `data` | DataFrame, Series, list, dict | obrigatório | Dados de entrada com o texto |
| `questions` | type[BaseModel] | obrigatório | Classe Pydantic que define os campos de saída |
| `prompt` | str | obrigatório | Instrução para o LLM. Use `{texto}` para posicionar o conteúdo da linha |
| `perguntas` | type[BaseModel] | None | Nome obsoleto de `questions`; emite `DeprecationWarning` |
| `resume` | bool | **True** | Com `True`, processa só as linhas sem status e preserva as `'processed'` e as `'error'`. Com `False`, processa toda linha que não esteja `'processed'`; se as colunas do modelo já existirem e `reprocess_columns` não vier, emite aviso e devolve os dados sem processar |
| `reprocess_columns` | list[str] | None | Refaz só as colunas listadas, inclusive em linhas já processadas; ao retomar com modelo alterado, deve cobrir os campos incompatíveis |
| `model` | str | None | Modelo LLM. Se None, usa o padrão do provider (ver §Modelo e temperature) |
| `provider` | str | `'openai'` | Nome de provedor do `init_chat_model` do LangChain (`'openai'`, `'google_genai'`, `'anthropic'`, `'groq'`, `'mistralai'`, `'cohere'` ...), `'claude_code'` ou `'codex'` |
| `status_column` | str | None | Nome da coluna de status (padrão `_dataframeit_status`) |
| `text_column` | str | None | Coluna de texto. Se None, infere entre `texto`, `text`, `decisao`, `content`, `content_text`; DataFrame de uma coluna usa-a direto; sem candidato, `ValueError` |
| `api_key` | str | None | API key. Se None, lê da variável de ambiente do provedor. Recusada com `'codex'`, ignorada com `'claude_code'` |
| `max_retries` | int | 3 | Tentativas totais por linha, contando a primeira. Fora de `int >= 1`, `ValueError` |
| `base_delay` | float | 1.0 | Espera antes da primeira nova tentativa, em segundos; dobra a cada tentativa |
| `max_delay` | float | 30.0 | Teto da espera entre tentativas, em segundos |
| `rate_limit_delay` | float | 0.0 | Pausa de cada worker depois de cada linha bem-sucedida, em segundos. Taxa máxima: `parallel_requests × 60 / rate_limit_delay` por minuto |
| `track_tokens` | bool | **True** | Adiciona `_input_tokens`, `_cached_input_tokens`, `_output_tokens` e `_reasoning_tokens` |
| `model_kwargs` | dict | None | Repassado ao cliente LangChain do provedor, que só recebe o que vier aqui. Com `'claude_code'`, só `effort`, `max_turns` e `max_budget_usd` são lidos, e o resto é ignorado; com `'codex'`, só `effort` é aceito, e outra chave levanta erro |
| `parallel_requests` | int | 1 | Número de workers paralelos |
| `use_search` | bool | False | Habilita busca web. Não suportado com `'claude_code'` nem `'codex'` |
| `search_provider` | str | `"tavily"` | `"tavily"` (`TAVILY_API_KEY`) ou `"exa"` (`EXA_API_KEY`) |
| `search_per_field` | bool | False | Um agente por campo; exigido por `condition`, `search_groups` e configuração por campo |
| `max_results` | int | 5 | Resultados por busca (1-20) |
| `search_depth` | str | `"basic"` | `"basic"` (1 crédito) ou `"advanced"` (2 créditos); só Tavily |
| `max_search_calls` | int | 10 | Máximo de buscas por execução do agente; as seguintes são bloqueadas e o agente responde com o que encontrou. Aceita override por grupo e por campo |
| `search_groups` | dict[str, dict] | None | Campos que compartilham um agente (ver `busca-web.md`) |
| `save_trace` | bool, str, None | None | `None` desligado, `True` ou `"full"` completo, `"minimal"` resumido. Exige `use_search=True` |
| `batch_size` | int | None | Grava o checkpoint a cada N linhas. Exige `checkpoint_path` |
| `checkpoint_path` | str \| Path | None | Arquivo do checkpoint; o formato vem da extensão: `.csv`, `.xlsx` (extra `[excel]`) ou `.parquet` (`pyarrow`). `batch_size` e `checkpoint_path` vão juntos, senão `ValueError` |

Para `model_kwargs` por modelo (o que cada um aceita), veja `modelos-parametros.md`.

---

## Modelo e temperature

Sem `model`, cada provider usa o próprio modelo padrão, definido em `DEFAULT_MODELS`. Para ver os valores da versão instalada:

```python
from dataframeit.core import DEFAULT_MODELS
print(DEFAULT_MODELS)   # ex.: {'openai': 'gpt-6-luna', 'anthropic': 'claude-sonnet-5', ...}
```

A tabela com o padrão e os modelos atuais de cada provider está em https://brunodcdo.com.br/dataframeit/guides/providers/. Provider fora de `DEFAULT_MODELS` (`'mistralai'`, `'cohere'`, `'google_vertexai'`, `'bedrock_converse'`, `'azure_openai'` etc.) exige `model=`; sem ele, a chamada levanta `ValueError` antes de processar qualquer linha. Com `'claude_code'` e `'codex'`, `model=None` deixa o runtime de cada um escolher.

```python
resultado = dataframeit(df, Modelo, prompt)                          # openai, modelo padrão
resultado = dataframeit(df, Modelo, prompt, provider='anthropic', model='claude-haiku-4-5')
resultado = dataframeit(df, Modelo, prompt, provider='mistralai', model='mistral-small-latest')
```

O modelo padrão nem sempre é o indicado para extração: o da Anthropic não é modelo pequeno, e o da OpenAI vem com raciocínio ligado. Em pipeline de pesquisa, passe `model=` explicitamente e registre-o.

Nos provedores via LangChain, o dataframeit não envia parâmetro de amostragem: o cliente recebe só `model_provider`, a `api_key` (quando houver) e o que vier em `model_kwargs`. Duas consequências:

- Modelo que não aceita `temperature` (ex.: Claude Sonnet 5 e Opus mais novos, GPT-6 com raciocínio ligado, série o, Gemini 3.5 Flash-Lite e 3.6 Flash ou mais novo) funciona sem ajuste. Não passe `temperature` a esses modelos: no Claude e na GPT-6 com raciocínio, a chamada volta com erro 400, que não ganha nova tentativa.
- Para determinismo, passe `temperature` (e `seed`, quando existir) explicitamente nos modelos que aceitam. Sem isso, vale o default do provedor, em geral maior que 0.

---

## Tipos de entrada aceitos

```python
import pandas as pd
from dataframeit import dataframeit

# DataFrame (mais comum)
df = pd.DataFrame({"texto": ["texto 1", "texto 2"]})
resultado = dataframeit(df, Modelo, "Analise: {texto}")

# Series (preserva o índice)
s = pd.Series(["texto 1", "texto 2"], index=["x", "y"])
resultado = dataframeit(s, Modelo, "Analise: {texto}")

# Lista de strings (DataFrame com índice numérico)
resultado = dataframeit(["texto 1", "texto 2"], Modelo, "Analise: {texto}")

# Dict (as chaves viram índice)
resultado = dataframeit({"id1": "texto 1", "id2": "texto 2"}, Modelo, "Analise: {texto}")
```

| Entrada | Saída |
|---|---|
| `pd.DataFrame` | `pd.DataFrame` |
| `pl.DataFrame` | `pl.DataFrame` (extra `[polars]`) |
| `pd.Series` | `pd.DataFrame` preservando o índice |
| `pl.Series` | `pl.DataFrame` |
| `list` | `pd.DataFrame` com índice numérico |
| `dict` | `pd.DataFrame` com as chaves como índice |

**`text_column`**: com `text_column=None` (padrão), a inferência segue esta ordem:

1. DataFrame de uma única coluna usa-a direto.
2. DataFrame com várias colunas procura, nessa ordem: `texto`, `text`, `decisao`, `content`, `content_text`.
3. Sem candidato, a chamada levanta `ValueError`.

Mesmo com inferência, passe `text_column='nome_da_coluna'` em pipelines de produção sempre que a coluna não estiver entre os candidatos (ex.: `ementa`, `acordao`, `mensagem`).

Validações antes do processamento, todas com `ValueError`: índice com rótulos repetidos (o resultado de uma linha seria gravado em outra) e campo do modelo com o mesmo nome da coluna de texto (a resposta sobrescreveria o texto).

---

## Retorno: estrutura do DataFrame

A função devolve os dados no formato da tabela acima, com as colunas originais, os campos extraídos e as colunas de controle:

| Coluna | Tipo | Quando aparece | Descrição |
|---|---|---|---|
| `<campos do modelo>` | conforme Pydantic | sempre | Valores extraídos pelo LLM |
| `_dataframeit_status` (ou o nome em `status_column`) | str | ver nota | `'processed'`, `'error'` ou `None` (linha ainda não processada) |
| `_error_details` | str \| None | ver nota | Mensagem do erro; numa linha que deu certo depois de novas tentativas, `"Sucesso após N retry(s)"`; numa linha com texto vazio, `"Texto ausente"` |
| `_input_tokens` | int | `track_tokens=True` (padrão) | Tokens de entrada, incluindo os lidos de cache |
| `_cached_input_tokens` | int | `track_tokens=True` (padrão) | Parcela de `_input_tokens` lida do cache |
| `_output_tokens` | int | `track_tokens=True` (padrão) | Tokens de saída |
| `_reasoning_tokens` | int | `track_tokens=True` (padrão) | Parcela de `_output_tokens` usada em raciocínio; `0` em modelos sem raciocínio |
| `_search_credits` | int | `use_search=True` | Créditos de busca gastos na linha (ver `busca-web.md`) |
| `_trace`, `_trace_{campo}`, `_trace_{grupo}` | str (JSON) | `save_trace` definido | Trace do agente |

**Nota sobre as colunas de status**: quando nenhuma linha termina com erro e nenhuma registra detalhe, `_dataframeit_status` e `_error_details` são removidas da saída. Antes de filtrar, confira se a coluna existe:

```python
if '_dataframeit_status' in resultado.columns:
    erros = resultado[resultado['_dataframeit_status'] == 'error']
```

Linhas com texto ausente (`None`, `NaN` ou só espaços) não vão ao LLM: ficam com status `'error'` e detalhe `"Texto ausente"`, e um aviso diz quantas são.

As colunas de token existem em todos os providers. Ficam nulas quando o provider não informa uso; quando ele informa o total mas não cache ou raciocínio, a parcela fica em zero. Não existe coluna `_total_tokens`: some `_input_tokens + _output_tokens`, sem somar de novo `_reasoning_tokens` nem `_cached_input_tokens`, que são parcelas. Cálculo de custo em `runs-longos.md`.

---

## Funções utilitárias

### read_df

Lê `.csv`, `.xlsx`/`.xls`, `.json` e `.parquet` e devolve às estruturas originais as listas, dicts e modelos aninhados gravados como JSON (ou como repr Python, em arquivos antigos). É a forma de recarregar um checkpoint ou uma saída salva para retomar com `resume=True`.

```python
from dataframeit import read_df

df = read_df('dados.csv')
df = read_df('dados.xlsx')              # requer o extra [excel]
df = read_df('parcial.parquet', MeuModelo)   # com o modelo: forma recomendada para retomar
df = read_df('dados.csv', normalize=False)   # sem converter nenhuma coluna
df = read_df('dados.csv', encoding='latin1', sep=';')   # kwargs vão ao pandas
```

```python
def read_df(path: str, model=None, normalize: bool = True, **kwargs) -> pd.DataFrame
```

Com `model`, só os campos de estrutura são normalizados, e em `.csv`/`.xlsx` os campos de texto são lidos como texto cru: `"2023"` não vira número e `"N/A"` não vira ausência. Passar `dtype`, `converters`, `na_values`, `keep_default_na`, `na_filter` ou `usecols` desliga essa leitura. CSV e XLSX gravam `""` e ausência do mesmo jeito; para guardar a diferença, use checkpoint `.parquet`.

### normalize_value

Converte em estrutura Python um valor gravado como texto:

```python
from dataframeit import normalize_value

normalize_value('["a", "b"]')       # ['a', 'b']
normalize_value("['a', 'b']")       # ['a', 'b'] (literal Python, sem executar código)
normalize_value('{"k": "v"}')       # {'k': 'v'}
normalize_value('texto simples')    # 'texto simples' (inalterado)
```

### normalize_complex_columns e get_complex_fields

`get_complex_fields(Modelo)` devolve o conjunto de campos cujo tipo é `list`, `dict`, `tuple` ou modelo aninhado, inclusive dentro de `Optional` e `Union`. `normalize_complex_columns(df, campos)` aplica `normalize_value` a essas colunas, no lugar, e ignora as ausentes.

```python
from dataframeit import get_complex_fields, normalize_complex_columns, read_df

df = read_df('saida.csv')
normalize_complex_columns(df, get_complex_fields(MeuModelo))
```

`read_df(path, model=MeuModelo)` faz essa normalização sozinho.

A versão instalada fica em `dataframeit.__version__`.

---

## Exceções

Referência oficial: https://brunodcdo.com.br/dataframeit/reference/exceptions/.

**Antes do processamento**, a configuração é validada e um problema interrompe a execução sem processar nenhuma linha:

| Exceção | Quando ocorre |
|---|---|
| `ImportError` | Falta o extra do provider ou do provedor de busca; a mensagem diz qual instalar |
| `ValueError` | Parâmetro inválido: `questions` ou `prompt` ausentes, `max_retries < 1`, `batch_size` sem `checkpoint_path`, `search_groups` sem `search_per_field=True`, `condition` fora do modo por campo, dependência circular ou campo inexistente em `condition`, chave de API de busca ausente, linhas já processadas incompatíveis com o modelo atual |
| `ProviderConfigurationError` | Configuração incompatível com o provider, como `model_kwargs` que o `codex` não aceita ou schema Pydantic que ele não representa. Subclasse de `ValueError` |

**Durante o processamento**, a falha de uma linha não interrompe a execução: a linha recebe status `'error'`, e `_error_details` guarda `[Falhou após N tentativa(s)] Classe: mensagem` ou `[Erro não-recuperável] Classe: mensagem`, o que permite filtrar por classe.

As classes abaixo são importáveis de `dataframeit` (e de `dataframeit.errors`):

```python
from dataframeit import (
    ProviderError, ProviderTransientError, ProviderOverloadedError,
    ProviderRejectedOutputError, ProviderConfigurationError, ProviderOutputError,
)
```

| Exceção | Base | Nova tentativa | Situação típica |
|---|---|---|---|
| `ProviderError` | `RuntimeError` | Não | Erro definitivo do provider, como autenticação recusada ou orçamento do `claude_code` esgotado |
| `ProviderTransientError` | `ProviderError` | Sim | Falha de rede ou do serviço que costuma passar sozinha |
| `ProviderOverloadedError` | `ProviderTransientError` | Sim | Sobrecarga ou HTTP 429 |
| `ProviderRejectedOutputError` | `ProviderTransientError` e `ValueError` | Sim | Resposta recusada pela validação do modelo Pydantic |
| `ProviderConfigurationError` | `ValueError` | Não (levantada antes) | Configuração local incompatível com o provider |
| `ProviderOutputError` | `ValueError` | Não | Provider terminou sem resposta utilizável, como um turno do `codex` sem conteúdo |

Erros dos providers via LangChain, em geral, não usam essas classes: são classificados pelo tipo que a LangChain declara, pelo status HTTP e pela mensagem (próxima seção).

---

## Tratamento de erros e retry

Referência oficial: https://brunodcdo.com.br/dataframeit/guides/error-handling/.

A classificação usa primeiro o tipo declarado pela LangChain (`is_retryable` do `ModelError`, com `langchain-core` recente) e o status HTTP que a exceção ou a causa dela declara (`status_code`, `code`, `http_status`, `response.status_code`). Sem status, olha o nome e a mensagem, e um código só conta como número isolado ("4015 tokens" não é 401).

### Recuperáveis (novas tentativas com backoff)

| Erro | Ação do dataframeit |
|---|---|
| Rate limit (429) | Nova tentativa; no modo paralelo, reduz os workers pela metade a cada 429 (nunca aumenta) |
| Timeout (408), conflito (409), erro de servidor (5xx) | Nova tentativa |
| Timeout, conexão ou SSL sem status HTTP | Nova tentativa |
| Resposta recusada pela validação Pydantic ou JSON inválido | Nova tentativa que leva ao modelo a resposta recusada e os erros por campo (caminho e valor), pedindo correção; nos providers do LangChain |
| Erro do Tavily ou do Exa (quota, chave, rede) | Interrompe o agente e a linha volta ao ciclo de tentativas |

Na resposta recusada, os tokens das tentativas recusadas entram em `_input_tokens` e `_output_tokens` quando uma tentativa seguinte dá certo, porque também são cobrados. Se todas falham, a linha fica `'error'` e `_error_details` diz o campo e a regra de cada erro.

### Não recuperáveis (falha imediata)

| Erro | Remédio |
|---|---|
| Autenticação (401) ou permissão (403) | Conferir a variável de ambiente no mesmo processo; todas as linhas terminam `'error'` |
| Modelo inexistente (404) | Conferir o ID na página do provedor |
| Requisição inválida (400, 422, `BadRequestError`, `InvalidArgument`) | Corrigir `model_kwargs`, ex.: `temperature` num modelo de raciocínio |
| Prompt maior que a janela de contexto (`ContextOverflowError`) | Encurtar o texto ou trocar de modelo |
| Orçamento (`max_budget_usd`) ou turnos (`max_turns`) do `claude_code` esgotados | Aumentar o teto em `model_kwargs` |

### Backoff exponencial

A espera antes da tentativa `n + 1` é `min(base_delay × 2^(n-1), max_delay)`, com até 10% de variação aleatória para que workers paralelos não repitam a chamada no mesmo instante. Com os defaults (`base_delay=1.0`, `max_delay=30.0`, `max_retries=3`), são três tentativas e duas esperas:

- depois da 1ª falha: ~1s;
- depois da 2ª falha: ~2s;
- a 3ª falha encerra a linha com status `'error'`.

Para runs longos, veja `runs-longos.md §Rate limiting`.

---

## Gotchas críticos

1. **Passe a classe Pydantic, não uma instância**: `dataframeit(df, Modelo, ...)`, não `dataframeit(df, Modelo(), ...)`.

2. **`Optional[str]` vs `str`**: use `Optional` para campos que podem não existir no texto. Campo obrigatório força o LLM a inventar um valor.

3. **`Field(description=...)` é o investimento mais barato**: uma boa descrição reduz mais erros que trocar de provedor. Ver `pydantic-patterns.md`.

4. **`resume=True` é o padrão**: processa só as linhas sem status; `'processed'` e `'error'` ficam como estão. Para refazer um erro, limpe o status da linha (ver `runs-longos.md §Reprocessar linhas com erro`). Rodar de novo sobre uma saída sem erros, que não tem coluna de status, reprocessa todas as linhas e emite aviso.

5. **`reprocess_columns` não refaz a linha inteira**: só os campos pedidos, e os demais são mantidos.

6. **Colunas de status podem não existir**: sem erro nem detalhe, a saída não tem `_dataframeit_status` nem `_error_details`. Filtrar direto dá `KeyError`; confira `'_dataframeit_status' in resultado.columns`.

7. **`search_groups` reduz agentes de busca**: sem grupos, `search_per_field=True` cria um agente por campo e por linha, cada um com até `max_search_calls` buscas. Ver `busca-web.md`.

8. **`save_trace` exige busca e gera dados volumosos**: sem `use_search=True`, `ValueError`. Valide primeiro numa amostra (`df.head(5)`).

9. **`parallel_requests` não escala sem limite**: acima de ~10 workers, a maioria dos provedores devolve 429. Comece baixo. Ver `runs-longos.md`.

10. **Campos condicionais exigem busca por campo**: `condition` e `depends_on` só funcionam com `use_search=True, search_per_field=True`, com ou sem `search_groups`; fora desse modo, `ValueError`. Em campo de modelo aninhado ou item de lista, `ValueError` em qualquer modo. Ver `pydantic-patterns.md §Padrão 4`.

11. **`provider=` diferencia maiúsculas**: `'Google'` falha. Use `'openai'`, `'google_genai'`, `'anthropic'`, `'groq'`, `'mistralai'` (não `'mistral'`), `'cohere'`, `'claude_code'`, `'codex'`.

12. **`model=` é o LLM, não o Pydantic**: o modelo Pydantic é o segundo argumento posicional (`questions`).

13. **`{texto}` marca onde entra o texto**: sem o placeholder, a biblioteca acrescenta `"Texto a analisar:\n{texto}"` ao fim do prompt. O mesmo vale para `prompt` por campo.

14. **Polars requer extra**: `pip install dataframeit[polars]`; sem ele, passar um DataFrame polars levanta `ImportError`.

15. **`perguntas` é nome obsoleto de `questions`**: emite `DeprecationWarning`; se os dois vierem, vale `questions`.

16. **`track_tokens=True` é o padrão**: as quatro colunas de tokens já aparecem; para desligar, `track_tokens=False`.
