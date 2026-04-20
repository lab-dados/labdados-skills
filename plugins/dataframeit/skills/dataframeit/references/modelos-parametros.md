# Parametros aceitos por modelo — referencia consultavel

Matriz dos hiperparametros aceitos por cada familia de modelo, com
recomendacao para **extracao estruturada e classificacao de campos
finitos** (caso de uso central do dataframeit).

Atualizado em abril/2026. Confirme na documentacao oficial do provedor
antes de executar — provedores ajustam parametros silenciosamente.

---

## Tabela-resumo por modelo default

| Modelo | Provider | `temperature` | `seed` | `max_output_tokens` | Config recomendada (extracao) |
|---|---|---|---|---|---|
| **Gemini 3 Flash** (default global) | `google_genai` | Aceita 0.0-2.0, **manter 1.0** | Sim | Sim | `{'temperature': 1.0, 'seed': 42}` |
| Gemini 2.5 Pro | `google_genai` | Aceita 0.0-2.0 | Sim | Sim | `{'temperature': 0, 'seed': 42}` |
| Gemini 2.5 Flash | `google_genai` | Aceita 0.0-2.0 | Sim | Sim | `{'temperature': 0, 'seed': 42}` |
| gpt-4o-mini | `openai` | Aceita 0.0-2.0 | Sim | Sim | `{'temperature': 0, 'seed': 42}` |
| gpt-4.1-mini | `openai` | Aceita 0.0-2.0 | Sim | Sim | `{'temperature': 0, 'seed': 42}` |
| gpt-4o | `openai` | Aceita 0.0-2.0 | Sim | Sim | `{'temperature': 0, 'seed': 42}` |
| **o1 / o1-mini** | `openai` | **Nao aceita** | Nao | `max_completion_tokens` | Nao se aplica a extracao |
| **o3 / o3-mini** | `openai` | **Nao aceita** | Nao | `max_completion_tokens` | Nao se aplica a extracao |
| **GPT-5 (raciocinio)** | `openai` | **Nao aceita** | Nao | `max_completion_tokens` | Nao se aplica a extracao |
| Claude Haiku 4.5 | `anthropic` | Aceita 0.0-1.0 | Nao | `max_tokens` | `{'temperature': 0}` |
| Claude Sonnet 4.6 | `anthropic` | Aceita 0.0-1.0 | Nao | `max_tokens` | `{'temperature': 0}` — desligar adaptive thinking |
| Claude Opus 4.7 | `anthropic` | Aceita 0.0-1.0, interage com adaptive thinking | Nao | `max_tokens` | Nao e default — apenas escalacao para raciocinio livre justificada |
| Mistral Small | `mistral` | Aceita 0.0-1.5 | `random_seed` | Sim | `{'temperature': 0, 'random_seed': 42}` |
| Mistral Large | `mistral` | Aceita 0.0-1.5 | `random_seed` | Sim | `{'temperature': 0, 'random_seed': 42}` |
| Cohere Command R | `cohere` | Aceita 0.0-5.0 | Sim | Sim | `{'temperature': 0, 'seed': 42}` |
| Cohere Command R+ | `cohere` | Aceita 0.0-5.0 | Sim | Sim | `{'temperature': 0, 'seed': 42}` |

**Regra geral**:

1. Para extracao/classificacao, **modelo pequeno** sempre — ver
   roteamento em `dataframeit-skill/SKILL.md` §Roteamento Passo 1.
2. Determinismo por `temperature=0` quando o modelo aceita, **exceto**
   Gemini 3 Flash (ver §Google abaixo).
3. `seed` fixo sempre que disponivel — cumulativo com `temperature=0`.
4. **Reasoning models** (o1/o3/GPT-5 raciocinio) nao aceitam
   `temperature`, usam `reasoning_effort` e `verbosity`, e nao se
   aplicam a extracao estruturada — ver §OpenAI abaixo.

---

## Como passar via `dataframeit`

O dicionario `model_kwargs` e repassado ao cliente do provedor:

```python
from dataframeit import dataframeit

# Claude Haiku 4.5
resultado = dataframeit(
    df, CodificacaoDecisao, "...",
    provider='anthropic',
    model='claude-haiku-4-5-20251001',
    model_kwargs={'temperature': 0},
)

# Gemini 3 Flash
resultado = dataframeit(
    df, CodificacaoDecisao, "...",
    provider='google_genai',
    model='gemini-3.0-flash',
    model_kwargs={'temperature': 1.0, 'seed': 42},
)

# gpt-4o-mini
resultado = dataframeit(
    df, CodificacaoDecisao, "...",
    provider='openai',
    model='gpt-4o-mini',
    model_kwargs={'temperature': 0, 'seed': 42},
)
```

Quando o nome do parametro varia entre providers (ex: `max_tokens`
vs. `max_output_tokens` vs. `max_completion_tokens`), passar conforme
o cliente do provedor espera — o dataframeit nao normaliza esses
nomes.

---

## §Google (`provider='google_genai'`)

### Gemini 3 Flash (default)

| Parametro | Aceita | Default | Recomendacao extracao |
|---|---|---|---|
| `temperature` | 0.0 – 2.0 | **1.0** | **Manter 1.0** |
| `seed` | int | aleatorio | Fixar (ex: 42) |
| `top_p` | 0.0 – 1.0 | — | Nao alterar |
| `top_k` | int | — | Nao alterar |
| `max_output_tokens` | int | ~8192 | Dimensionar conforme tamanho Pydantic |
| `response_mime_type` | str | — | `'application/json'` quando extracao via JSON |

**Cuidado — nao reduzir `temperature`**: Google recomenda manter
`temperature=1.0` (default) para Gemini 3 Flash. Reduzir abaixo de
1.0 pode causar looping ou degradacao, especialmente em tarefas
envolvendo raciocinio matematico/logico. Para reprodutibilidade,
fixe `seed` — nao `temperature`.

Fonte: Gemini 3 Developer Guide (Google AI for Developers, 2026).

### Gemini 2.5 Pro / 2.5 Flash / 1.5 Pro / 1.5 Flash (legados)

| Parametro | Aceita | Default | Recomendacao extracao |
|---|---|---|---|
| `temperature` | 0.0 – 2.0 | 1.0 | **0** |
| `seed` | int | aleatorio | Fixar |
| `top_p` | 0.0 – 1.0 | — | Nao alterar |
| `top_k` | int | — | Nao alterar |
| `max_output_tokens` | int | varia | Dimensionar |

Nos modelos legados, `temperature=0` ainda e o caminho tradicional.

---

## §OpenAI (`provider='openai'`)

### gpt-4o-mini, gpt-4o, gpt-4.1-mini, gpt-4.1 (nao-raciocinio)

| Parametro | Aceita | Default | Recomendacao extracao |
|---|---|---|---|
| `temperature` | 0.0 – 2.0 | 1.0 | **0** |
| `seed` | int | — | Fixar |
| `top_p` | 0.0 – 1.0 | 1.0 | Nao alterar |
| `max_completion_tokens` | int | varia | Dimensionar |
| `response_format` | dict | — | `{'type': 'json_schema', ...}` quando aplicavel |

`temperature=0` + `seed=42` e a combinacao tradicional de reprodutibilidade
em modelos nao-raciocinio da OpenAI.

### o1, o1-mini, o3, o3-mini, GPT-5 (modo raciocinio)

**Nao aceitam `temperature`** — a tentativa retorna erro 400:

```
Error: Unsupported parameter: 'temperature' is not supported with this model.
```

Tambem nao aceitam: `top_p`, `presence_penalty`, `frequency_penalty`,
`logit_bias`, `seed` (na pratica, desconsiderado).

Parametros proprios:

| Parametro | Valores | O que faz |
|---|---|---|
| `reasoning_effort` | `'low'`, `'medium'`, `'high'` | Quanta "cadeia de raciocinio" o modelo gera |
| `verbosity` | `'low'`, `'medium'`, `'high'` | Verbosidade da resposta final |
| `max_completion_tokens` | int | Total (inclui tokens de raciocinio invisiveis) |

**Recomendacao para extracao estruturada**: nao usar. Esses modelos
sao apropriados para tarefas de raciocinio livre (ex: sumarizar
divergencias doutrinarias extensas, classificar tipos de argumentacao
em texto juridico complexo). Para campos `Literal[...]` e extracao
direta, use gpt-4o-mini / gpt-4.1-mini ou equivalente pequeno de outro
provider.

Fonte: OpenAI Developer Community threads sobre unsupported parameter
error; documentacao de reasoning models.

---

## §Anthropic (`provider='anthropic'`)

### Claude Haiku 4.5

| Parametro | Aceita | Default | Recomendacao extracao |
|---|---|---|---|
| `temperature` | 0.0 – 1.0 | 1.0 | **0** |
| `top_p` | 0.0 – 1.0 | — | Nao alterar |
| `top_k` | int | — | Nao alterar |
| `max_tokens` | int | obrigatorio | Dimensionar conforme Pydantic |
| `system` | str | — | Prompt-sistema |

Nao ha parametro `seed` oficial — a Anthropic nao expoe controle de
seed via API publica. Para reprodutibilidade, `temperature=0` +
`top_p` default basta na maioria dos casos.

### Claude Sonnet 4.6 e Opus 4.6 / 4.7 com adaptive thinking

| Parametro | Observacao |
|---|---|
| `temperature` | Aceita, mas **interage com adaptive thinking** em Claude 4.x |
| `thinking` | Objeto com `effort` e configuracao de adaptive thinking |

**Nota sobre adaptive thinking**: extended thinking foi deprecado em
Claude 4.6+. Adaptive thinking e o substituto e, em Claude Opus 4.7, e
o **unico modo de thinking** suportado — nao aceita mais
`thinking: {type: "enabled", budget_tokens: N}`. Em adaptive thinking,
o modelo calibra automaticamente conforme `effort` + complexidade da
query.

Para extracao estruturada com Sonnet/Opus (quando ja justificou
escalacao), **desligue adaptive thinking** (nao passe `thinking={...}`)
e use `temperature=0` — comporta-se como modelo nao-pensante para
extracao reprodutivel.

Fonte: Claude API Docs — Models overview, Adaptive thinking, Migration
guide.

---

## §Mistral (`provider='mistral'`)

### Mistral Small / Mistral Large

| Parametro | Aceita | Default | Recomendacao extracao |
|---|---|---|---|
| `temperature` | 0.0 – 1.5 | 0.7 | **0** |
| `random_seed` | int | — | Fixar |
| `top_p` | 0.0 – 1.0 | 1.0 | Nao alterar |
| `max_tokens` | int | — | Dimensionar |
| `response_format` | dict | — | `{'type': 'json_object'}` quando aplicavel |

Note: o parametro se chama `random_seed`, nao `seed`.

---

## §Cohere (`provider='cohere'`)

### Command R / Command R+

| Parametro | Aceita | Default | Recomendacao extracao |
|---|---|---|---|
| `temperature` | 0.0 – 5.0 | 0.3 | **0** |
| `seed` | int | — | Fixar |
| `p` | 0.01 – 0.99 | — | Nao alterar (analogo a top_p) |
| `k` | int | — | Nao alterar (analogo a top_k) |
| `max_tokens` | int | — | Dimensionar |

Range de temperatura vai ate 5.0 (mais amplo que outros providers),
mas para extracao estruturada isso e irrelevante — use 0.

---

## §Claude Code (`provider='claude_code'`)

Modo especial — delega as chamadas ao `claude-agent-sdk` e consome
tokens do plano Claude Code do usuario. Modelos disponiveis seguem o
plano: Haiku 4.5, Sonnet 4.6, Opus 4.7 (conforme tier). Hiperparametros
seguem a regra da familia Anthropic acima.

Nao suporta `use_search=True` — para busca web, usar
`provider='google_genai'` ou `'openai'`.

Defaults de protecao de custo: `max_turns=1`, `max_budget_usd=0.50`
por linha.

---

## Registrar no protocolo (obrigatorio)

Para reprodutibilidade (registre no protocolo de pesquisa):

- `provider` (ex: `google_genai`, `anthropic`, `openai`)
- `model` exato (ex: `gemini-3.0-flash`, `claude-haiku-4-5-20251001`)
- `temperature` (ou "nao suportado" em reasoning models)
- `seed` / `random_seed` (ou "nao suportado")
- `top_p`, `top_k` (se alterados do default)
- `max_output_tokens` / `max_tokens` / `max_completion_tokens`
- Data da execucao

Sem esse registro completo, o estudo nao e reprodutivel mesmo com o
codigo-fonte disponivel — modelos mudam silenciosamente atras do mesmo
nome.
