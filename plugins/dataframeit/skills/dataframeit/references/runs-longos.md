# Runs longos — paralelismo, custo, tolerancia a falha

Este arquivo consolida tudo que voce precisa para rodar `dataframeit`
em datasets grandes (centenas de milhares de linhas) com seguranca:
controle de paralelismo e rate limit, rastreamento de custo, retomada
apos interrupcao, checkpointing periodico, deteccao de truncamento de
saida e trace logging.

## Indice

1. [Processamento paralelo (`parallel_requests`)](#processamento-paralelo-parallel_requests)
2. [Rate limiting (`rate_limit_delay`)](#rate-limiting-rate_limit_delay)
3. [Perfis de configuracao](#perfis-de-configuracao)
4. [Rastreamento de tokens](#rastreamento-de-tokens)
5. [Calculo de custo por provedor](#calculo-de-custo-por-provedor)
6. [Resume e reprocessamento](#resume-e-reprocessamento)
7. [Checkpointing por lotes](#checkpointing-por-lotes)
8. [Truncamento de saida — deteccao e retry](#truncamento-de-saida--deteccao-e-retry)
9. [Trace logging](#trace-logging)

---

## Processamento paralelo (`parallel_requests`)

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

Acima de ~10 workers, a maioria dos provedores retorna 429 — comece
baixo e suba conforme o provedor aguentar.

---

## Rate limiting (`rate_limit_delay`)

Delay adicional entre requisicoes para evitar erro 429:

```python
# Sem delay (padrao)
resultado = dataframeit(df, Modelo, prompt, rate_limit_delay=0.0)

# 0.5s entre requisicoes (conservador)
resultado = dataframeit(df, Modelo, prompt, rate_limit_delay=0.5)
```

Calculo pratico: `60 / requests_per_minute_do_provedor`.
Ex: Anthropic free tier (50 req/min) → `rate_limit_delay=1.2`.

Erros transitorios (429, timeout, 502/503, SSL) sao retentados
automaticamente com backoff exponencial: `base_delay * 2^tentativa`
com jitter, limitado por `max_delay`. Com defaults (`base_delay=1.0`,
`max_delay=30.0`, `max_retries=3`): ~1s, ~2s, ~4s.

---

## Perfis de configuracao

| Perfil | parallel_requests | rate_limit_delay | max_retries | Quando usar |
|---|---|---|---|---|
| Economico | 1 | 1.5 | 10 | Free tier, datasets pequenos |
| Equilibrado | 5 | 0.5 | 5 | Uso geral |
| Rapido | 10 | 0.0 | 3 | Tier pago, datasets grandes |

---

## Rastreamento de tokens

`track_tokens=True` e o **padrao**. Colunas adicionadas automaticamente:
`_input_tokens`, `_output_tokens`, `_reasoning_tokens`.

```python
resultado = dataframeit(df, Modelo, prompt)  # track_tokens=True por padrao

total_input = resultado['_input_tokens'].sum()
total_output = resultado['_output_tokens'].sum()
total_reasoning = resultado.get('_reasoning_tokens', pd.Series([0])).sum()
total = total_input + total_output + total_reasoning
print(f"Tokens: {total:,} "
      f"(entrada: {total_input:,}, saida: {total_output:,}, raciocinio: {total_reasoning:,})")
```

Nao existe coluna `_total_tokens` agregada — some as tres. Use
`df.get(...)` para nao quebrar quando `_reasoning_tokens` estiver
ausente (ex: `track_tokens=False` ou versoes antigas).

`_reasoning_tokens` so e > 0 em modelos de raciocinio (o1/o3, GPT-5
raciocinio, Claude adaptive thinking).

---

## Calculo de custo por provedor

Precos aproximados em USD por 1M tokens — verifique no site do provedor
antes de estimar, eles mudam frequentemente.

| Provedor | Modelo default | Entrada | Saida |
|---|---|---|---|
| Google Gemini | gemini-3-flash-preview | ~$0.10 | ~$0.40 |
| OpenAI | gpt-4o-mini | ~$0.15 | ~$0.60 |
| Anthropic | claude-haiku-4-5 | ~$1.00 | ~$5.00 |
| Mistral | mistral-small-latest | ~$0.20 | ~$0.60 |
| Cohere | command-r | ~$0.15 | ~$0.60 |
| Groq | llama-3.3-70b-versatile | ~$0.59 | ~$0.79 |

```python
# Google Gemini (gemini-3-flash-preview)
custo = (total_input * 0.10 + total_output * 0.40) / 1_000_000

# OpenAI (gpt-4o-mini)
custo = (total_input * 0.15 + total_output * 0.60) / 1_000_000

# Anthropic (claude-haiku-4-5)
custo = (total_input * 1.00 + total_output * 5.00) / 1_000_000

# Groq (llama-3.3-70b-versatile)
custo = (total_input * 0.59 + total_output * 0.79) / 1_000_000

print(f"Custo estimado: ${custo:.4f}")
```

Para reasoning models, `total_reasoning` e cobrado como saida pela
maioria dos provedores — ajuste a formula somando `total_reasoning` ao
multiplicador de saida.

**Estimativa previa** (antes de rodar): `len(df) × ~500 tokens/linha ×
preco` e uma aproximacao conservadora. Para datasets > 1000 linhas,
mostre a estimativa ao usuario e peca confirmacao.

---

## Resume e reprocessamento

### resume=True (padrao)

Pula linhas onde `_dataframeit_status == "processed"`. Util para retomar
apos interrupcao:

```python
resultado = dataframeit(df, Modelo, prompt)
resultado.to_parquet('progresso.parquet')

# Retomar — linhas ja processadas sao puladas
df_parcial = pd.read_parquet('progresso.parquet')
resultado_final = dataframeit(df_parcial, Modelo, prompt)
```

### reprocess_columns

Reprocessa apenas colunas especificas, mantendo as demais:

```python
resultado_corrigido = dataframeit(
    resultado_com_erros, Modelo, prompt,
    reprocess_columns=["campo_problematico"]
)
```

### Reprocessar linhas com erro

```python
# `_dataframeit_status` so existe quando ha erros — use .get() antes de filtrar
status = resultado.get('_dataframeit_status', pd.Series(dtype=str))
erros = resultado[status == 'error']
print(f"{len(erros)} linhas com erro")
if len(erros) > 0:
    print(erros['_error_details'].value_counts())
    resultado.loc[status == 'error', '_dataframeit_status'] = None
    resultado_corrigido = dataframeit(resultado, Modelo, prompt)
```

---

## Checkpointing por lotes

`batch_size` + `checkpoint_path` persistem o DataFrame parcial a cada
`batch_size` linhas. Complementa `resume=True` em runs longos: sem
checkpoint, uma queda de rede ou `Ctrl+C` perde tudo que nao foi
gravado manualmente.

```python
resultado = dataframeit(
    df, Modelo, "Classifique: {texto}",
    parallel_requests=5,
    batch_size=50,                                 # persiste a cada 50 linhas
    checkpoint_path='checkpoints/run-01.parquet',  # arquivo de destino
)
```

**Retomada apos queda**:

```python
import pandas as pd

df_parcial = pd.read_parquet('checkpoints/run-01.parquet')
resultado = dataframeit(
    df_parcial, Modelo, "Classifique: {texto}",
    batch_size=50,
    checkpoint_path='checkpoints/run-01.parquet',
)
```

**Quando usar**:

| Cenario | Usar checkpoint? |
|---|---|
| < 100 linhas | Nao — o run todo termina em minutos |
| 100-1000 linhas | Opcional — `.to_parquet()` manual no fim basta |
| > 1000 linhas ou > 10 min estimados | **Sim** — sempre, para tolerar quedas |
| Run via notebook que pode ser interrompido | **Sim** — evita reprocessar tudo |

`batch_size` sem `checkpoint_path` e inutil (nao ha onde persistir);
`checkpoint_path` sem `batch_size` tambem — a biblioteca so grava ao
fim de cada batch.

---

## Truncamento de saida — deteccao e retry

Distinto do problema de contexto de **entrada**, o output pode ser
truncado ao atingir `max_output_tokens`. Sinais: campos finais em
branco, strings cortadas, listas aninhadas com contagem suspeita
(sempre exatamente 5 itens). O Pydantic pode passar na validacao se os
campos obrigatorios foram preenchidos — o truncamento fica invisivel.

**Deteccao e retry**:

```python
LIMITE_OUTPUT = 2000   # ajustar ao model_kwargs['max_output_tokens']
resultado['_trunc_suspeito'] = resultado['_output_tokens'] >= int(LIMITE_OUTPUT * 0.95)
mascara_erro = resultado['_error_details'].fillna('').str.contains(
    'max_tokens|length_limit|stop_reason.*length', case=False, regex=True
)

precisa_retry = resultado[resultado['_trunc_suspeito'] | mascara_erro]

if len(precisa_retry) > 0:
    resultado_fix = dataframeit(
        precisa_retry, Modelo, "...",
        reprocess_columns=[...],                           # so campos afetados
        model_kwargs={'max_output_tokens': 4000},          # dobrar limite
    )
```

**Prevencao**: dimensione `max_output_tokens` com folga de 2× antes da
rodada. Para Pydantic com ~8 campos + justificativa, ~800 tokens bastam;
para `List[Pedido]` com ~3 pedidos medios, ~1500 tokens; com folga,
3000-4000.

---

## Trace logging

Captura o raciocinio do agente LLM para cada linha. Util para depurar
extracoes inesperadas.

```python
resultado = dataframeit(df, Modelo, prompt, save_trace="full")     # completo
resultado = dataframeit(df, Modelo, prompt, save_trace="minimal")  # resumido
resultado = dataframeit(df, Modelo, prompt, save_trace=True)       # = "full"
```

Modos:
- `None` (padrao) — desligado
- `True` ou `"full"` — captura completa (tool calls, raciocinio, passos intermediarios)
- `"minimal"` — apenas decisoes-chave e extracao final

**Aviso**: trace completo em datasets grandes gera muito dado. Use
primeiro com uma amostra pequena (`df.head(5)`) para validar a
extracao.
