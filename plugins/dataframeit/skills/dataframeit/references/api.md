# DataFrameIt — Referencia da API

## Indice

1. [Instalacao](#instalacao)
2. [Funcao principal — dataframeit()](#funcao-principal--dataframeit)
3. [Retorno — estrutura do DataFrame](#retorno--estrutura-do-dataframe)
4. [Tipos de entrada aceitos](#tipos-de-entrada-aceitos)
5. [Modelos Pydantic — padroes](#modelos-pydantic--padroes)
6. [json_schema_extra — referencia completa](#json_schema_extra--referencia-completa)
7. [Busca web](#busca-web)
8. [Processamento paralelo e rate limiting](#processamento-paralelo-e-rate-limiting)
9. [Rastreamento de tokens e calculo de custo](#rastreamento-de-tokens-e-calculo-de-custo)
10. [Resume e reprocessamento](#resume-e-reprocessamento)
11. [Trace logging](#trace-logging)
12. [Funcoes utilitarias](#funcoes-utilitarias)
13. [Tratamento de erros](#tratamento-de-erros)
14. [Exemplos de workflow completo](#exemplos-de-workflow-completo)
15. [Gotchas criticos](#gotchas-criticos)

---

## Instalacao

```bash
pip install dataframeit[google]         # Google Gemini (padrao, recomendado)
pip install dataframeit[openai]         # OpenAI
pip install dataframeit[anthropic]      # Anthropic
pip install dataframeit[cohere]         # Cohere
pip install dataframeit[mistral]        # Mistral
pip install dataframeit[all]            # todos os provedores
pip install dataframeit[google,search]  # Gemini + busca web (Tavily/Exa)
pip install dataframeit[all,search]     # todos + busca web
pip install dataframeit[google,polars]  # Gemini + suporte Polars
```

Python >= 3.10 obrigatorio.

## Funcao principal — `dataframeit()`

```python
from dataframeit import dataframeit

resultado = dataframeit(
    data,                          # DataFrame | Series | list | dict
    questions,                     # type[BaseModel] — classe Pydantic (nao instancia)
    prompt,                        # str — instrucao com placeholder {texto}
    perguntas=None,                # alias portugues para questions
    resume=True,                   # bool — pular linhas ja processadas
    reprocess_columns=None,        # list[str] | None — reprocessar apenas colunas especificas
    model='gemini-3.0-flash',      # str — identificador do modelo LLM
    provider='google_genai',       # str — provedor LLM
    status_column=None,            # str | None — nome customizado da coluna de status
    text_column=None,              # str | None — coluna do DataFrame a usar como texto
    api_key=None,                  # str | None — None=le da variavel de ambiente
    max_retries=3,                 # int — tentativas por linha em caso de erro
    base_delay=1.0,                # float — delay inicial (segundos) para backoff exponencial
    max_delay=30.0,                # float — delay maximo (segundos) para backoff
    rate_limit_delay=0.0,          # float — delay entre requisicoes (controle de rate limit)
    track_tokens=True,             # bool — adicionar colunas _tokens_* ao resultado
    model_kwargs=None,             # dict | None — kwargs extras repassados ao LLM
    parallel_requests=1,           # int — workers paralelos (1=sequencial)
    use_search=False,              # bool — habilitar busca web
    search_provider="tavily",      # str — "tavily" | "exa"
    search_per_field=False,        # bool — busca separada por campo
    max_results=5,                 # int — max resultados de busca (1-20)
    search_depth="basic",          # str — "basic" | "advanced"
    search_groups=None,            # dict[str, dict] | None — agrupar campos para busca
    save_trace=None,               # bool | "full" | "minimal" | None — capturar raciocinio
)
```

### Parametros em detalhe

| Parametro | Tipo | Default | Descricao |
|---|---|---|---|
| `data` | DataFrame, Series, list, dict | — | Dados de entrada contendo texto |
| `questions` | type[BaseModel] | — | Classe Pydantic definindo os campos de saida |
| `prompt` | str | — | Instrucao para o LLM. Use `{texto}` para referenciar o conteudo da linha |
| `perguntas` | type[BaseModel] | None | Alias portugues para `questions` |
| `resume` | bool | **True** | Pula linhas com `_dataframeit_status == "processed"` |
| `reprocess_columns` | list[str] | None | Reprocessa apenas as colunas listadas |
| `model` | str | `'gemini-3.0-flash'` | Identificador do modelo LLM |
| `provider` | str | `'google_genai'` | Provedor: `'google_genai'`, `'openai'`, `'anthropic'`, `'cohere'`, `'mistral'` |
| `status_column` | str | None | Nome customizado para a coluna de status (padrao: `_dataframeit_status`) |
| `text_column` | str | None | Coluna do DataFrame a usar como texto. Se None, usa a primeira coluna |
| `api_key` | str | None | API key. Se None, le da variavel de ambiente do provedor |
| `max_retries` | int | 3 | Maximo de tentativas com backoff exponencial |
| `base_delay` | float | 1.0 | Delay inicial em segundos (dobra a cada tentativa) |
| `max_delay` | float | 30.0 | Delay maximo em segundos (teto do backoff) |
| `rate_limit_delay` | float | 0.0 | Delay adicional entre requisicoes em segundos |
| `track_tokens` | bool | **True** | Adiciona `_input_tokens`, `_output_tokens`, `_total_tokens` |
| `model_kwargs` | dict | None | Kwargs extras repassados ao cliente LangChain do provedor |
| `parallel_requests` | int | 1 | Numero de workers paralelos |
| `use_search` | bool | False | Habilita busca web (Tavily ou Exa) |
| `search_provider` | str | `"tavily"` | `"tavily"` ou `"exa"` |
| `search_per_field` | bool | False | Executa uma busca separada para cada campo habilitado |
| `max_results` | int | 5 | Maximo de resultados de busca por consulta (1-20) |
| `search_depth` | str | `"basic"` | `"basic"` (1 credito) ou `"advanced"` (2 creditos) |
| `search_groups` | dict[str, dict] | None | Agrupa campos para compartilhar busca (ver secao dedicada) |
| `save_trace` | bool, str, None | None | `None`=desligado, `True` ou `"full"`=completo, `"minimal"`=resumido |

### Modelos padrao por provedor

| Provedor | `provider=` | Modelo padrao (`model=`) |
|---|---|---|
| Google Gemini | `'google_genai'` | `'gemini-3.0-flash'` |
| OpenAI | `'openai'` | `'gpt-4o-mini'` |
| Anthropic | `'anthropic'` | `'claude-3-haiku-20240307'` |
| Cohere | `'cohere'` | `'command-r'` |
| Mistral | `'mistral'` | `'mistral-small-latest'` |

Para usar outro modelo, especifique `model=` explicitamente:
```python
resultado = dataframeit(df, Modelo, prompt, provider='openai', model='gpt-4o')
resultado = dataframeit(df, Modelo, prompt, provider='anthropic', model='claude-sonnet-4-20250514')
```

---

## Retorno — estrutura do DataFrame

A funcao retorna os dados no mesmo formato da entrada (DataFrame, Series, list ou dict)
com as colunas originais + campos extraidos + colunas de controle:

| Coluna | Tipo | Quando aparece | Descricao |
|---|---|---|---|
| `<campos do modelo>` | conforme Pydantic | sempre | Valores extraidos pelo LLM |
| `_dataframeit_status` | str | **apenas se houver erros** | `"processed"` ou `"error"`. **IMPORTANTE**: quando todas as linhas processam com sucesso, a biblioteca remove essa coluna (e `_error_details`) do DataFrame retornado. Use `df.get("_dataframeit_status", pd.Series(dtype=str))` para checar com seguranca. |
| `_error_details` | str \| None | **apenas se houver erros** | Mensagem de erro — removida junto com `_dataframeit_status` quando nao ha erros. |
| `_input_tokens` | int | `track_tokens=True` (padrao) | Tokens de entrada consumidos |
| `_output_tokens` | int | `track_tokens=True` (padrao) | Tokens de saida consumidos |
| `_total_tokens` | int | `track_tokens=True` (padrao) | Total de tokens |

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

**`text_column`**: Se o DataFrame tiver multiplas colunas e a coluna de texto nao for
a primeira, especifique `text_column='nome_da_coluna'`.

---

## Modelos Pydantic — padroes

### Padrao 1 — Basico

```python
from pydantic import BaseModel
from typing import Literal

class Sentimento(BaseModel):
    sentimento: Literal['positivo', 'negativo', 'neutro']
    confianca: Literal['alta', 'media', 'baixa']

resultado = dataframeit(df, Sentimento, "Analise o sentimento do texto: {texto}")
```

Use `Literal` para restringir valores — reduz alucinacoes do LLM.
Use `Optional[str]` para campos que podem nao existir no texto.

### Padrao 2 — Com Field(description=)

```python
from pydantic import BaseModel, Field
from typing import Optional

class Processo(BaseModel):
    numero_cnj: str = Field(description="Numero do processo no formato CNJ")
    tribunal: str = Field(description="Sigla do tribunal (ex: TJSP, TJRS)")
    classe: str = Field(description="Classe processual (ex: Apelacao Civel)")
    valor_causa: Optional[float] = Field(
        description="Valor da causa em reais. None se nao informado"
    )
```

`Field(description=...)` e o investimento mais barato para melhorar a qualidade da extracao.

### Padrao 3 — Com json_schema_extra

```python
from pydantic import BaseModel, Field

class MedicamentoInfo(BaseModel):
    principio_ativo: str = Field(description="Principio ativo do medicamento")

    doenca_rara: str = Field(
        description="Classificacao de doenca rara",
        json_schema_extra={
            "prompt": "Busque em Orphanet (orpha.net). Analise: {texto}"
        }
    )

    avaliacao_conitec: str = Field(
        description="Avaliacao da CONITEC",
        json_schema_extra={
            "prompt_append": "Busque APENAS no site da CONITEC (gov.br/conitec)."
        }
    )

    estudos_clinicos: str = Field(
        description="Estudos clinicos relevantes",
        json_schema_extra={
            "prompt_append": "Busque estudos clinicos recentes.",
            "search_depth": "advanced",
            "max_results": 10
        }
    )
```

### Padrao 4 — Campos condicionais (depends_on)

```python
from pydantic import BaseModel, Field
from typing import Optional

class AnaliseMulta(BaseModel):
    tem_multa: bool = Field(description="O texto menciona aplicacao de multa?")

    valor_multa: Optional[float] = Field(
        description="Valor da multa em reais",
        json_schema_extra={
            "depends_on": ["tem_multa"],
            "condition": {"field": "tem_multa", "equals": True}
        }
    )

    fundamentacao: Optional[str] = Field(
        description="Fundamentacao legal da multa",
        json_schema_extra={
            "depends_on": ["tem_multa"],
            "condition": {"field": "tem_multa", "equals": True}
        }
    )
```

O campo-pai (`tem_multa`) deve ser definido **antes** dos campos-filhos no modelo.

---

## json_schema_extra — referencia completa

Chaves suportadas dentro de `json_schema_extra={}` no `Field()`:

| Chave | Tipo | Descricao |
|---|---|---|
| `prompt` | str | Substitui o prompt principal para este campo. Usa `{texto}` como placeholder |
| `prompt_append` | str | Adiciona texto ao final do prompt principal para este campo |
| `search_depth` | `"basic"` \| `"advanced"` | Profundidade de busca web para este campo |
| `max_results` | int (1-20) | Max resultados de busca para este campo |
| `depends_on` | list[str] \| str | Campo(s) que devem ser extraidos antes deste |
| `condition` | dict | Condicao para extrair este campo (ver operadores abaixo) |

### Formato da `condition`

```python
"condition": {
    "field": "nome_do_campo",    # campo a avaliar (suporta dot notation: "endereco.cidade")
    "equals": valor              # OU um dos operadores abaixo
}
```

### Operadores condicionais

| Operador | Descricao | Exemplo |
|---|---|---|
| `equals` | Valor e igual | `{"field": "tipo", "equals": "criminal"}` |
| `not_equals` | Valor e diferente | `{"field": "tipo", "not_equals": "civil"}` |
| `in` | Valor esta na lista | `{"field": "uf", "in": ["SP", "RJ", "MG"]}` |
| `not_in` | Valor nao esta na lista | `{"field": "uf", "not_in": ["AC", "RR"]}` |
| `exists` | Campo tem valor (nao None) | `{"field": "email", "exists": True}` |

---

## Busca web

### Configuracao basica

```python
resultado = dataframeit(
    df, Modelo,
    "Analise e busque informacoes complementares: {texto}",
    use_search=True,              # habilita busca
    search_provider="tavily",     # "tavily" (padrao) ou "exa"
    search_depth="basic",         # "basic" (1 credito) ou "advanced" (2 creditos)
    max_results=5,                # resultados por busca (1-20)
)
```

### Busca por campo (search_per_field)

Cada campo com configuracao de busca no `json_schema_extra` recebe sua propria busca:

```python
resultado = dataframeit(
    df, MedicamentoInfo,
    "Analise o medicamento: {texto}",
    use_search=True,
    search_per_field=True,        # busca separada por campo
)
```

### Search groups — agrupar campos

Campos relacionados compartilham uma unica busca para economizar:

```python
resultado = dataframeit(
    df, Modelo, prompt,
    use_search=True,
    search_groups={
        "localizacao": {
            "fields": ["cidade", "estado", "pais"],
            "search_depth": "basic",
            "max_results": 5
        },
        "contato": {
            "fields": ["email", "telefone"],
            "prompt": "Busque informacoes de contato de: {texto}",
            "search_depth": "advanced"
        }
    }
)
```

Cada grupo cria **uma** chamada de busca. Sem grupos, seriam 5 chamadas separadas.

| Chave do grupo | Tipo | Descricao |
|---|---|---|
| `fields` | list[str] | Campos do modelo que compartilham esta busca (obrigatorio) |
| `prompt` | str | Prompt customizado para a busca deste grupo (opcional) |
| `search_depth` | str | `"basic"` ou `"advanced"` (opcional, herda do global) |
| `max_results` | int | Max resultados (opcional, herda do global) |

### Custos de busca

| Provedor | Tipo | Custo | Free tier |
|---|---|---|---|
| Tavily | basic | 1 credito/busca | 1000 buscas/mes |
| Tavily | advanced | 2 creditos/busca | 1000 buscas/mes |
| Exa | 1-25 resultados | ~$0.005/busca | — |
| Exa | 26-100 resultados | ~$0.025/busca | — |

**Recomendacao**: Tavily para volume baixo/medio (< 2667 buscas/mes).
Exa para volume alto com busca semantica.

---

## Processamento paralelo e rate limiting

### parallel_requests

```python
# Sequencial (padrao — mais facil de depurar)
resultado = dataframeit(df, Modelo, prompt, parallel_requests=1)

# 5 workers paralelos
resultado = dataframeit(df, Modelo, prompt, parallel_requests=5)

# 10 workers para datasets grandes
resultado = dataframeit(df, Modelo, prompt, parallel_requests=10)
```

Recomendacoes:
- **< 50 linhas**: `parallel_requests=1` (sequencial)
- **50-500 linhas**: `parallel_requests=5`
- **> 500 linhas**: `parallel_requests=10` (monitorar rate limit)

### rate_limit_delay

Delay adicional entre requisicoes para evitar erro 429:

```python
# Sem delay (padrao)
resultado = dataframeit(df, Modelo, prompt, rate_limit_delay=0.0)

# 0.5s entre requisicoes (conservador)
resultado = dataframeit(df, Modelo, prompt, rate_limit_delay=0.5)

# Calculo: 60 / requests_per_minute do provedor
# Ex: Anthropic free tier (50 req/min) → rate_limit_delay=1.2
```

### Perfis de configuracao

| Perfil | parallel_requests | rate_limit_delay | max_retries | Quando usar |
|---|---|---|---|---|
| Economico | 1 | 1.5 | 10 | Free tier, datasets pequenos |
| Equilibrado | 5 | 0.5 | 5 | Uso geral |
| Rapido | 10 | 0.0 | 3 | Tier pago, datasets grandes |

---

## Rastreamento de tokens e calculo de custo

`track_tokens=True` e o **padrao**. Colunas adicionadas automaticamente:

```python
resultado = dataframeit(df, Modelo, prompt)  # track_tokens=True por padrao

# Verificar uso total
total_input = resultado['_input_tokens'].sum()
total_output = resultado['_output_tokens'].sum()
total = resultado['_total_tokens'].sum()
print(f"Tokens: {total:,} (entrada: {total_input:,}, saida: {total_output:,})")
```

### Calculo de custo por provedor

```python
# Google Gemini (gemini-3.0-flash)
custo = (total_input * 0.10 + total_output * 0.40) / 1_000_000

# OpenAI (gpt-4o-mini)
custo = (total_input * 0.15 + total_output * 0.60) / 1_000_000

# Anthropic (claude-3-haiku)
custo = (total_input * 0.25 + total_output * 1.25) / 1_000_000

print(f"Custo estimado: ${custo:.4f}")
```

---

## Resume e reprocessamento

### resume=True (padrao)

Pula linhas onde `_dataframeit_status == "processed"`. Util para retomar apos interrupcao:

```python
# Primeira execucao (pode ser interrompida)
resultado = dataframeit(df, Modelo, prompt)

# Salvar progresso parcial
resultado.to_parquet('progresso.parquet')

# Retomar de onde parou (linhas ja processadas sao puladas)
df_parcial = pd.read_parquet('progresso.parquet')
resultado_final = dataframeit(df_parcial, Modelo, prompt)
```

### reprocess_columns

Reprocessa apenas colunas especificas, mantendo as demais:

```python
# Reprocessar apenas 'campo_problematico'
resultado_corrigido = dataframeit(
    resultado_com_erros, Modelo, prompt,
    reprocess_columns=["campo_problematico"]
)
```

### Reprocessar linhas com erro

```python
# Verificar erros
erros = resultado[resultado['_dataframeit_status'] == 'error']
print(f"{len(erros)} linhas com erro")
print(erros['_error_details'].value_counts())

# Resetar status das linhas com erro para reprocessar
resultado.loc[resultado['_dataframeit_status'] == 'error', '_dataframeit_status'] = None
resultado_corrigido = dataframeit(resultado, Modelo, prompt)
```

---

## Trace logging

Captura o raciocinio do agente LLM para cada linha. Util para depurar extracoes inesperadas.

```python
# Trace completo
resultado = dataframeit(df, Modelo, prompt, save_trace="full")

# Trace resumido
resultado = dataframeit(df, Modelo, prompt, save_trace="minimal")

# True equivale a "full"
resultado = dataframeit(df, Modelo, prompt, save_trace=True)
```

Modos:
- `None` (padrao) — desligado
- `True` ou `"full"` — captura completa (tool calls, raciocinio, passos intermediarios)
- `"minimal"` — apenas decisoes-chave e extracao final

**Aviso**: trace completo em datasets grandes gera muito dado. Use com amostras pequenas primeiro.

---

## Funcoes utilitarias

### read_df

Carrega DataFrames de diversos formatos com normalizacao automatica de JSON:

```python
from dataframeit import read_df

df = read_df('dados.csv')
df = read_df('dados.xlsx')
df = read_df('dados.parquet')
df = read_df('dados.json')

# Com modelo Pydantic para guiar normalizacao de campos complexos
df = read_df('dados.json', model=MeuModelo)

# Sem normalizacao automatica
df = read_df('dados.csv', normalize=False)

# Kwargs extras sao repassados ao pandas
df = read_df('dados.csv', encoding='latin1', sep=';')
```

**Assinatura:**
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

Normaliza colunas com tipos complexos (listas, dicts) em um DataFrame inteiro:

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

A sequencia de retries segue: `base_delay * (2 ^ tentativa)` com jitter aleatorio,
limitada por `max_delay`:

Com defaults (`base_delay=1.0`, `max_delay=30.0`, `max_retries=3`):
- Tentativa 1: ~1s
- Tentativa 2: ~2s
- Tentativa 3: ~4s

---

## Exemplos de workflow completo

### Exemplo 1 — Classificacao de sentimento

```python
import pandas as pd
from pydantic import BaseModel, Field
from typing import Literal
from dataframeit import dataframeit

# 1. Definir esquema de saida
class Sentimento(BaseModel):
    sentimento: Literal['positivo', 'negativo', 'neutro']
    confianca: Literal['alta', 'media', 'baixa']

# 2. Carregar dados
df = pd.DataFrame({
    'texto': [
        'Produto excelente! Superou expectativas.',
        'Pessimo atendimento, nunca mais compro.',
        'Entrega ok, produto mediano.'
    ]
})

# 3. Executar
resultado = dataframeit(df, Sentimento, "Analise o sentimento do texto: {texto}")

# 4. Verificar
print(resultado[['texto', 'sentimento', 'confianca', '_dataframeit_status']])
print(f"Tokens totais: {resultado['_total_tokens'].sum():,}")
```

### Exemplo 2 — Extracao com busca web e campos condicionais

```python
import pandas as pd
from pydantic import BaseModel, Field
from typing import Optional
from dataframeit import dataframeit

# 1. Esquema com busca web e campos condicionais
class EmpresaInfo(BaseModel):
    nome_empresa: str = Field(description="Nome da empresa mencionada")
    setor: str = Field(description="Setor de atuacao da empresa")

    tem_dado_financeiro: bool = Field(
        description="O texto menciona dados financeiros?"
    )
    receita_anual: Optional[str] = Field(
        description="Receita anual (se disponivel)",
        json_schema_extra={
            "depends_on": ["tem_dado_financeiro"],
            "condition": {"field": "tem_dado_financeiro", "equals": True},
            "prompt_append": "Busque a receita mais recente.",
            "search_depth": "advanced"
        }
    )
    sede: Optional[str] = Field(
        description="Localizacao da sede",
        json_schema_extra={
            "prompt_append": "Busque a localizacao da sede."
        }
    )

# 2. Carregar dados
df = pd.DataFrame({
    'texto': [
        'A empresa XYZ reportou crescimento de 30% no ultimo trimestre.',
        'Startup ABC recebeu investimento serie A de R$ 50 milhoes.',
    ]
})

# 3. Executar com busca web e search groups
resultado = dataframeit(
    df, EmpresaInfo,
    "Analise a empresa mencionada: {texto}",
    use_search=True,
    search_groups={
        "financeiro": {
            "fields": ["receita_anual"],
            "search_depth": "advanced",
            "max_results": 5
        },
        "localizacao": {
            "fields": ["sede"],
            "search_depth": "basic"
        }
    }
)

# 4. Verificar
print(resultado[['nome_empresa', 'setor', 'receita_anual', 'sede', '_dataframeit_status']])
```

### Exemplo 3 — Pipeline de producao (grande volume)

```python
import pandas as pd
from pydantic import BaseModel, Field
from typing import Literal, Optional
from dataframeit import dataframeit, read_df

# 1. Carregar dataset grande
df = read_df('ementas_tjsp.parquet')
print(f"Total de linhas: {len(df):,}")

# 2. Definir esquema
class ClassificacaoEmenta(BaseModel):
    area: Literal['civel', 'criminal', 'trabalhista', 'tributario', 'outro']
    tema_principal: str = Field(description="Tema juridico principal da ementa")
    houve_reforma: Optional[bool] = Field(
        description="A decisao reformou a sentenca de 1o grau?"
    )

# 3. Estimar custo ANTES de executar
tokens_estimados = len(df) * 500  # ~500 tokens por ementa (estimativa)
custo_gemini = tokens_estimados / 1_000_000 * 0.50  # entrada + saida
print(f"Custo estimado (Gemini): ~${custo_gemini:.2f}")
# → Confirmar com o usuario antes de prosseguir

# 4. Executar com resume (retomavel) e paralelismo
resultado = dataframeit(
    df,
    ClassificacaoEmenta,
    "Classifique esta ementa judicial: {texto}",
    parallel_requests=5,
    rate_limit_delay=0.5,
)

# 5. Salvar progresso (resume=True permite retomar)
resultado.to_parquet('classificacao_progresso.parquet')

# 6. Verificar erros
erros = resultado[resultado['_dataframeit_status'] == 'error']
print(f"Processados: {len(resultado) - len(erros):,} | Erros: {len(erros):,}")
print(f"Tokens totais: {resultado['_total_tokens'].sum():,}")

# 7. Reprocessar erros se necessario
if len(erros) > 0:
    resultado.loc[resultado['_dataframeit_status'] == 'error', '_dataframeit_status'] = None
    resultado_final = dataframeit(
        resultado, ClassificacaoEmenta,
        "Classifique esta ementa judicial: {texto}",
        parallel_requests=3,
        rate_limit_delay=1.0,  # mais conservador na segunda tentativa
    )
    resultado_final.to_parquet('classificacao_final.parquet')
```

---

## Gotchas criticos

1. **Passe a classe Pydantic, nao uma instancia** — `dataframeit(df, Modelo, ...)` nao
   `dataframeit(df, Modelo(), ...)`. Passar instancia levanta erro.

2. **`Optional[str]` vs `str`** — Use `Optional` para campos que podem nao existir no texto.
   Campos obrigatorios (`str`) forcam o LLM a inventar um valor se nao encontrar.

3. **`Field(description=...)` e o investimento mais barato** — Uma boa descricao reduz
   erros de extracao mais do que trocar de provedor ou aumentar o modelo.

4. **`resume=True` e o padrao** — Na primeira execucao funciona normalmente (nao ha
   `_dataframeit_status` para pular). Em execucoes subsequentes, pula linhas ja processadas.

5. **`reprocess_columns` nao reprocessa a linha inteira** — Apenas os campos especificados.
   Os demais campos extraidos anteriormente sao mantidos.

6. **`search_groups` reduz chamadas de busca** — Sem grupos, cada campo `search_enabled`
   dispara uma busca separada por linha. Com grupos, campos do mesmo grupo compartilham
   uma unica busca. Configure sempre que tiver 2+ campos com busca.

7. **`save_trace=True` gera dados volumosos** — Para datasets grandes, use primeiro com
   uma amostra pequena (`df.head(5)`) para validar a extracao.

8. **`parallel_requests` nao escala ilimitado** — Acima de ~10 workers, a maioria dos
   provedores retorna 429. Comece com `parallel_requests=1` (padrao) e aumente conforme
   necessario.

9. **Campos condicionais exigem ordem** — O campo-pai (`depends_on`) deve ser definido
   **antes** do campo-filho no modelo Pydantic. Se invertido, a condicao pode nao funcionar.

10. **`provider=` e case-sensitive** — `'Google'` falha. Use minusculas:
    `'google_genai'`, `'openai'`, `'anthropic'`, `'cohere'`, `'mistral'`.

11. **`model=` e o LLM, nao o Pydantic** — O parametro `model` define qual modelo de
    linguagem usar (ex: `'gemini-3.0-flash'`). O modelo Pydantic e passado como `questions`
    (segundo argumento posicional).

12. **`{texto}` no prompt e obrigatorio** — O placeholder `{texto}` no prompt e substituido
    pelo conteudo da linha. Sem ele, o LLM nao recebe o texto a analisar.

13. **Polars requer extra** — `pip install dataframeit[polars]`. Sem o extra, passar um
    Polars DataFrame levanta `ImportError`.

14. **`perguntas` e alias de `questions`** — Ambos aceitam a classe Pydantic. Use o que
    preferir, mas nao passe os dois simultaneamente.

15. **`track_tokens=True` e o padrao** — As colunas `_tokens_*` ja aparecem sem configuracao
    adicional. Para desabilitar, passe `track_tokens=False` explicitamente.
