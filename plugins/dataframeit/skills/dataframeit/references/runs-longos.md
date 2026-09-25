# Runs longos: paralelismo, custo, tolerância a falha

Este arquivo reúne o que é preciso para rodar `dataframeit` em datasets grandes com segurança: paralelismo e rate limit, rastreamento de custo, retomada depois de interrupção, checkpointing periódico, detecção de truncamento de saída e trace. A referência oficial é https://brunodcdo.com.br/dataframeit/guides/performance/.

## Índice

1. [Processamento paralelo (`parallel_requests`)](#processamento-paralelo-parallel_requests)
2. [Rate limiting (`rate_limit_delay`)](#rate-limiting-rate_limit_delay)
3. [Perfis de configuração](#perfis-de-configuração)
4. [Rastreamento de tokens](#rastreamento-de-tokens)
5. [Cálculo de custo](#cálculo-de-custo)
6. [Resume e reprocessamento](#resume-e-reprocessamento)
7. [Checkpointing por lotes](#checkpointing-por-lotes)
8. [Truncamento de saída: detecção e retry](#truncamento-de-saída-detecção-e-retry)
9. [Trace](#trace)

---

## Processamento paralelo (`parallel_requests`)

```python
resultado = dataframeit(df, Modelo, prompt)                       # sequencial (padrão, mais fácil de depurar)
resultado = dataframeit(df, Modelo, prompt, parallel_requests=5)  # 5 workers
```

| Volume | `parallel_requests` |
|---|---|
| < 50 linhas | 1 (padrão) |
| 50-500 linhas | 3 a 5 |
| > 500 linhas | 5 a 10, monitorando rate limit |

A cada 429, o dataframeit reduz os workers pela metade (10, 5, 2, 1) e tenta de novo com backoff. Os workers só diminuem, nunca aumentam sozinhos. A solução estável para 429 frequente é baixar `parallel_requests` ou aumentar `rate_limit_delay`.

---

## Rate limiting (`rate_limit_delay`)

`rate_limit_delay` é a pausa de **cada worker** depois de **cada linha concluída com sucesso**. Com vários workers, as pausas correm em paralelo, e a taxa máxima de requisições é:

```
taxa máxima (req/min) = parallel_requests × 60 / rate_limit_delay
delay = 60 × parallel_requests / limite_de_req_por_minuto
```

| Limite da conta | Workers | `rate_limit_delay` |
|---|---|---|
| 60 req/min | 1 | 1.0 |
| 60 req/min | 5 | 5.0 |
| 500 req/min | 5 | 0.6 |

A taxa real fica abaixo desse teto, porque cada chamada também leva tempo. O limite depende do modelo e do nível da conta e muda com frequência; confira o valor na página de rate limits do provedor antes de aplicar a fórmula. Com busca web, o limite do provedor de busca costuma ser o mais apertado (ver `busca-web.md`).

**Retry.** Erros transitórios (429, 408, 409, 5xx, timeout, conexão, SSL) e respostas que não passam na validação Pydantic ganham novas tentativas, com o mesmo prompt, com backoff exponencial: a espera antes da tentativa `n + 1` é `min(base_delay × 2^(n-1), max_delay)`, com até 10% de variação. `max_retries` conta as tentativas totais, incluindo a primeira: com os defaults (`base_delay=1.0`, `max_delay=30.0`, `max_retries=3`), são três tentativas, com esperas de ~1s e ~2s. Os demais 4xx (400, 401, 403, 404, 422) e o estouro de contexto falham na hora. Detalhes em `api.md §Tratamento de erros e retry`.

---

## Perfis de configuração

| Perfil | `parallel_requests` | `rate_limit_delay` | `max_retries` | Quando usar |
|---|---|---|---|---|
| Econômico | 1 | 1.5 | 3 | Free tier, datasets pequenos |
| Estável | 3 | 1.0 | 3 (com `base_delay=2.0`) | Uso geral |
| Rápido | 10 | 0.0 | 5 | Tier pago, datasets grandes |

Confira o perfil contra a fórmula acima: o rápido, com 10 workers e sem pausa, só serve em conta com limite alto.

---

## Rastreamento de tokens

`track_tokens=True` é o **padrão**. As colunas são as mesmas em todos os providers: `_input_tokens`, `_cached_input_tokens`, `_output_tokens`, `_reasoning_tokens`. Ficam nulas quando o provider não informa uso; quando informa o total mas não cache ou raciocínio, a parcela fica em zero.

```python
resultado = dataframeit(df, Modelo, prompt)

total_input = resultado['_input_tokens'].sum()
total_output = resultado['_output_tokens'].sum()
total_reasoning = resultado['_reasoning_tokens'].sum()
total_cache = resultado['_cached_input_tokens'].sum()
total = total_input + total_output  # raciocínio está dentro da saída; cache, dentro da entrada
print(f"Tokens: {total:,} "
      f"(entrada: {total_input:,}, dos quais cache: {total_cache:,}, "
      f"saída: {total_output:,}, raciocínio: {total_reasoning:,})")
```

Não existe coluna `_total_tokens`. Somar as três colunas conta o raciocínio duas vezes, e `_cached_input_tokens` também é parcela de `_input_tokens`.

Ao fim da execução, o dataframeit imprime um resumo com modelo, tokens de entrada e saída (e de cache e raciocínio, quando o provider informa), tempo, workers, requisições, RPM e TPM efetivos. Com busca, o resumo ganha buscas e créditos; com `claude_code`, o custo em USD informado pelo SDK, somando as tentativas re-tentadas e as linhas que falharam. Use RPM e TPM para calibrar `parallel_requests` e `rate_limit_delay`.

---

## Cálculo de custo

Os preços por modelo estão na página de provedores da documentação (https://brunodcdo.com.br/dataframeit/guides/providers/) e mudam com frequência; confira no site do provedor antes de estimar.

```python
preco_entrada = 0.10   # USD por 1M tokens (preencher com o preço atual do modelo)
preco_saida = 0.50
custo = (total_input * preco_entrada + total_output * preco_saida) / 1_000_000
print(f"Custo estimado: ${custo:.4f}")
```

Em modelos de raciocínio, os tokens de raciocínio são cobrados como saída e já estão em `total_output`. Tokens lidos de cache costumam custar menos que a entrada comum; a fórmula acima os cobra pelo preço cheio e superestima o custo quando `total_cache` é alto.

**Estimativa prévia**: o melhor caminho é rodar uma amostra (`df.sample(30)`) e escalar pelo tamanho do dataset. Sem amostra, `len(df) × ~500 tokens/linha × preço` é uma aproximação conservadora. Para datasets com mais de 1000 linhas, mostre a estimativa ao usuário e peça confirmação.

---

## Resume e reprocessamento

### resume=True (padrão)

Processa só as linhas sem `_dataframeit_status`: as `'processed'` e as `'error'` ficam como estão. A escolha depende só do status de cada linha, então funciona com índice fora de ordem (depois de `sort_values`, `sample` ou filtro) e com índice textual. Se todas as linhas já têm status, a chamada devolve o DataFrame sem contatar o provedor.

**Armadilha**: uma saída sem erros não tem coluna de status. Rodar `dataframeit` de novo sobre ela processa **todas** as linhas outra vez, e paga por isso; o dataframeit emite um aviso quando as colunas do modelo já estão preenchidas e falta a de status. Se a saída já está pronta, não rode de novo; para refazer só algumas colunas, use `reprocess_columns`.

```python
resultado = dataframeit(df, Modelo, prompt)
resultado.to_parquet('saida.parquet')
```

### resume=False

Processa toda linha que não esteja `'processed'`. Se as colunas do modelo já existem e `reprocess_columns` não veio, emite aviso e devolve os dados sem processar, para não sobrescrever resultados.

### reprocess_columns

Refaz só as colunas listadas, mantendo as demais, inclusive em linhas já processadas. No modo por campo ou por grupo, só as colunas escolhidas são pedidas ao agente, e as condições usam os valores já gravados na linha:

```python
resultado_corrigido = dataframeit(
    resultado, Modelo, prompt,
    reprocess_columns=["campo_problematico"],
)
```

Ao retomar com o modelo Pydantic alterado, as linhas já processadas são validadas contra o modelo atual; um campo incompatível levanta `ValueError` até entrar em `reprocess_columns`.

### Reprocessar linhas com erro

Com `resume=True`, linha `'error'` não é refeita sozinha: limpe o status e o detalhe dela antes de rodar de novo.

```python
if '_dataframeit_status' in resultado.columns:
    mascara = resultado['_dataframeit_status'] == 'error'
    print(f"{mascara.sum()} linhas com erro")
    print(resultado.loc[mascara, '_error_details'].value_counts())
    resultado.loc[mascara, ['_dataframeit_status', '_error_details']] = None
    resultado = dataframeit(resultado, Modelo, prompt)
```

Erros de autenticação, de parâmetro ou de texto ausente voltam iguais se nada mudar; corrija a causa antes de refazer.

---

## Checkpointing por lotes

`batch_size` + `checkpoint_path` gravam o DataFrame parcial a cada `batch_size` linhas. Sem checkpoint, uma queda de rede ou `Ctrl+C` perde tudo o que está em memória.

```python
resultado = dataframeit(
    df, Modelo, "Classifique: {texto}",
    parallel_requests=5,
    batch_size=50,                                 # grava a cada 50 linhas
    checkpoint_path='checkpoints/run-01.parquet',  # formato pela extensão
)
```

**Retomada depois de queda**: recarregue com `read_df` passando o modelo, que devolve listas, dicts e textos com os tipos do modelo, e rode de novo com `resume=True` (padrão):

```python
from dataframeit import read_df

df_parcial = read_df('checkpoints/run-01.parquet', Modelo)
resultado = dataframeit(
    df_parcial, Modelo, "Classifique: {texto}",
    batch_size=50,
    checkpoint_path='checkpoints/run-01.parquet',
)
```

| Cenário | Usar checkpoint? |
|---|---|
| < 100 linhas | Não, o run termina em minutos |
| 100-1000 linhas | Opcional; gravar a saída no fim basta |
| > 1000 linhas ou > 10 min estimados | **Sim**, para tolerar quedas |
| Run em notebook que pode ser interrompido | **Sim** |

`batch_size` e `checkpoint_path` vão juntos: um sem o outro levanta `ValueError`. Formatos: `.csv`, `.xlsx` (extra `[excel]`) e `.parquet` (`pyarrow`, que vem no extra `[polars]`). Prefira `.parquet`: CSV e XLSX gravam `""` e ausência do mesmo jeito, e um campo obrigatório de texto que era `""` volta ausente e é acusado para reprocessar. Uma falha ao gravar o checkpoint (disco cheio, arquivo aberto no Excel) vira aviso, sem mudar o status da linha, e a gravação seguinte grava o estado completo.

---

## Truncamento de saída: detecção e retry

Distinto do limite de contexto de **entrada**, a saída pode ser cortada ao atingir o limite de saída. O nome do parâmetro varia por provedor: `max_completion_tokens` na OpenAI, `max_output_tokens` no Gemini, `max_tokens` na Anthropic, Groq e Mistral; o dataframeit não normaliza. Sinais: campos finais em branco, strings cortadas, listas com contagem suspeita (sempre exatamente 5 itens). A validação Pydantic pode passar se os campos obrigatórios foram preenchidos, e o truncamento fica invisível.

```python
LIMITE_OUTPUT = 2000   # o limite de saída passado em model_kwargs
suspeito = resultado['_output_tokens'] >= int(LIMITE_OUTPUT * 0.95)
if '_error_details' in resultado.columns:
    suspeito |= resultado['_error_details'].fillna('').str.contains(
        'max_tokens|length_limit|stop_reason.*length', case=False, regex=True
    )

if suspeito.any():
    resultado_fix = dataframeit(
        resultado[suspeito], Modelo, "...",
        reprocess_columns=[...],                           # só os campos afetados
        provider='openai', model='gpt-6-luna',
        model_kwargs={'max_completion_tokens': 4000},      # dobrar o limite (nome da OpenAI)
    )
```

**Prevenção**: dimensione o limite de saída com folga de 2× antes da rodada. Para Pydantic com ~8 campos e justificativa, ~800 tokens bastam; para `List[Pedido]` com ~3 pedidos médios, ~1500; com folga, 3000 a 4000.

---

## Trace

Captura o que o agente de busca fez em cada linha. Serve para depurar extrações inesperadas. Exige `use_search=True`; sem busca, `save_trace` levanta `ValueError`.

```python
resultado = dataframeit(df, Modelo, prompt, use_search=True, save_trace="full")     # completo
resultado = dataframeit(df, Modelo, prompt, use_search=True, save_trace="minimal")  # resumido
resultado = dataframeit(df, Modelo, prompt, use_search=True, save_trace=True)       # igual a "full"
```

| Valor | Conteúdo |
|---|---|
| `None` (padrão) | Desligado |
| `True` ou `"full"` | Mensagens completas, inclusive o conteúdo dos resultados de busca |
| `"minimal"` | Só as consultas e as contagens, sem o conteúdo das buscas |

O trace vai, em JSON, para `_trace` ou, com `search_per_field=True`, para `_trace_{campo}` (e `_trace_{grupo}` com `search_groups`). Chaves: `messages`, `search_queries`, `total_tool_calls` (todas as chamadas, inclusive a resposta estruturada), `duration_seconds`, `model`.

```python
import json
trace = json.loads(resultado['_trace'].iloc[0])
print(trace['search_queries'], trace['duration_seconds'])
```

Trace completo em dataset grande gera muito dado: valide primeiro numa amostra (`df.head(5)`).
