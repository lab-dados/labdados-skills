# Parametros aceitos por modelo — referencia consultavel

Matriz dos hiperparametros aceitos por cada familia de modelo, com
recomendacao para **extracao estruturada e classificacao de campos
finitos** (caso de uso central do dataframeit).

Atualizado em setembro/2026 a partir das paginas de modelos e de
deprecacao de cada provedor. Confirme na documentacao oficial antes de
executar: provedores aposentam modelos e mudam parametros com
frequencia.

**Lembrete do dataframeit**: nos provedores via LangChain, a biblioteca
cria o cliente com `temperature=0` e depois aplica `model_kwargs`. Para
modelo que nao aceita `temperature`, passe `{'temperature': None}`; para
recomendacao diferente de 0, passe o valor explicitamente. Ver
`api.md §Modelo e temperature`.

---

## Tabela-resumo

| Modelo (`model=`) | Provider | `temperature` | `seed` | Config recomendada (extracao) |
|---|---|---|---|---|
| **`gemini-3-flash-preview`** (default do dataframeit, ainda em preview) | `google_genai` | Aceita, **manter 1.0** | Sim | `{'temperature': 1.0, 'seed': 42}` |
| `gemini-3.5-flash-lite`, `gemini-3.6-flash` a `gemini-3.8-flash` | `google_genai` | **Deprecada** | Nao confirmado | `{'temperature': None}` |
| `gemini-3.1-pro-preview` | `google_genai` | Aceita, manter 1.0 | Sim | Nao e default, so escalacao justificada |
| `gpt-4.1-mini`, `gpt-4o-mini` (nao-raciocinio) | `openai` | Aceita 0.0-2.0 | Deprecado no Chat Completions | `{'temperature': 0}` |
| **GPT-6** (`gpt-6-luna`, `gpt-6-sol`, `gpt-6-astra`) | `openai` | So com `reasoning_effort='none'` | Deprecado | `{'reasoning_effort': 'none', 'temperature': 0}` |
| GPT-5 (`gpt-5`, `gpt-5-mini`, `gpt-5-nano`) | `openai` | So com raciocinio `none` | Deprecado | Snapshots saem em 11/12/2026, migrar |
| **o1, o3, o3-mini** | `openai` | **Nao aceita** | Nao | o1 e o3-mini saem em 23/10/2026, o3 em 11/12/2026 |
| `claude-haiku-4-5` | `anthropic` | Aceita 0.0-1.0 | Nao | `{'temperature': 0}` |
| `claude-sonnet-4-6` | `anthropic` | Aceita 0.0-1.0 | Nao | `{'temperature': 0}` |
| `claude-sonnet-5`, `claude-opus-5`, `claude-opus-5-5`, Opus 4.7/4.8 | `anthropic` | **Nao aceita** (erro 400) | Nao | `{'temperature': None}`. Nao e default para extracao |
| `mistral-small-latest` (hoje Mistral Small 4) | `mistralai` | Aceita, 0-0.7 recomendado | `random_seed` | `{'temperature': 0, 'random_seed': 42}` |
| `mistral-large-latest` (hoje Mistral Large 3) | `mistralai` | Aceita | `random_seed` | `{'temperature': 0, 'random_seed': 42}` |
| `command-a-03-2025` | `cohere` | Aceita | Sim | `{'temperature': 0, 'seed': 42}` |
| `openai/gpt-oss-120b`, `openai/gpt-oss-20b` | `groq` | Aceita 0.0-2.0 | Sim | `{'temperature': 0, 'seed': 42}` |

**Aposentados que ainda aparecem em codigo antigo**: Gemini 1.5 (desligado
em 29/09/2025); Gemini 2.5 Pro/Flash (acesso restrito a quem ja usava);
aliases `command-r`/`command-r-plus` da Cohere (deprecados desde
15/09/2025); `llama-3.3-70b-versatile` e `llama-3.1-8b-instant` na Groq
(desligados em 16/08/2026 nos planos free e developer).

**Regra geral**:

1. Para extracao/classificacao, **modelo pequeno** sempre — ver
   roteamento em `SKILL.md §Roteamento Passo 1`.
2. Determinismo por `temperature=0` quando o modelo aceita, **exceto**
   Gemini 3 (ver §Google abaixo).
3. `seed` fixo sempre que disponivel — cumulativo com `temperature=0`.
4. **Modelos de raciocinio** (OpenAI o-series, GPT-5/GPT-6 com
   raciocinio ligado, Claude Sonnet 5/Opus) nao aceitam `temperature`.
   Para extracao, prefira modelo nao-raciocinio ou desligue o raciocinio
   quando o provedor permite (GPT-6 com `reasoning_effort='none'`).

---

## Como passar via `dataframeit`

O dicionario `model_kwargs` e repassado ao cliente do provedor:

```python
from dataframeit import dataframeit

# Claude Haiku 4.5
resultado = dataframeit(
    df, CodificacaoDecisao, "...",
    provider='anthropic',
    model='claude-haiku-4-5',
    model_kwargs={'temperature': 0},
)

# Gemini 3 Flash (default)
resultado = dataframeit(
    df, CodificacaoDecisao, "...",
    provider='google_genai',
    model='gemini-3-flash-preview',
    model_kwargs={'temperature': 1.0, 'seed': 42},
)

# GPT-6 Luna sem raciocinio
resultado = dataframeit(
    df, CodificacaoDecisao, "...",
    provider='openai',
    model='gpt-6-luna',
    model_kwargs={'reasoning_effort': 'none', 'temperature': 0},
)
```

Quando o nome do parametro varia entre providers (ex: `max_tokens`
vs. `max_output_tokens` vs. `max_completion_tokens`), passar conforme
o cliente do provedor espera — o dataframeit nao normaliza esses
nomes.

---

## §Google (`provider='google_genai'`)

### Gemini 3 Flash preview (default do dataframeit)

`gemini-3-flash-preview` continua em preview, sem data de desligamento
anunciada. Nao existe `gemini-3-flash` GA: as versoes estaveis sao as
numeradas abaixo.

| Parametro | Aceita | Default | Recomendacao extracao |
|---|---|---|---|
| `temperature` | 0.0 – 2.0 | **1.0** | **Manter 1.0** |
| `seed` | int | aleatorio | Fixar (ex: 42) |
| `top_p` | 0.0 – 1.0 | — | Nao alterar |
| `top_k` | int | — | Nao alterar |
| `max_output_tokens` | int | ~8192 | Dimensionar conforme tamanho Pydantic |

**Cuidado — nao reduzir `temperature`**: o Google recomenda manter
`temperature=1.0` nos Gemini 3. Reduzir pode causar looping ou
degradacao. Como o dataframeit injeta `temperature=0`, passe 1.0
explicitamente. Para reprodutibilidade, fixe `seed`, nao `temperature`.

### Gemini 3.5 Flash-Lite, 3.6 Flash, 3.7 Flash, 3.8 Flash (estaveis)

`temperature`, `top_p` e `top_k` estao deprecados a partir do
Gemini 3.6 Flash e do 3.5 Flash-Lite (changelog de 21/07/2026), e o
guia de migracao para o 3.8 manda remove-los. O `langchain-google-genai`
4.4 so descarta `temperature` sozinho para `gemini-3.5-flash-lite` e
`gemini-3.6-flash`; nos demais, passe `{'temperature': None}`. Nao foi
confirmado se `seed` continua valendo nesses modelos.

### Gemini 3.1 Pro preview

Unico Pro de texto disponivel (`gemini-3-pro-preview` foi desligado em
09/03/2026). Mesma recomendacao de `temperature=1.0`. Reservar para
escalacao justificada.

---

## §OpenAI (`provider='openai'`)

### gpt-4.1-mini, gpt-4o-mini (nao-raciocinio)

Continuam disponiveis como aliases (so alguns snapshots antigos saem
em 23/10/2026).

| Parametro | Aceita | Default | Recomendacao extracao |
|---|---|---|---|
| `temperature` | 0.0 – 2.0 | 1.0 | **0** |
| `seed` | int | — | Marcado como deprecado no Chat Completions |
| `top_p` | 0.0 – 1.0 | 1.0 | Nao alterar |
| `max_completion_tokens` | int | varia | Dimensionar |

### GPT-6 (`gpt-6-luna`, `gpt-6-sol`, `gpt-6-astra`)

Familia corrente. `gpt-6-luna` e o modelo mais barato. O raciocinio vem
ligado (`medium`) por padrao, e nesse modo `temperature` e `top_p` sao
rejeitados. Duas saidas:

- Extracao deterministica: `{'reasoning_effort': 'none', 'temperature': 0}`.
- Manter o raciocinio: `{'temperature': None}`, porque o
  `langchain-openai` 1.6.5 envia o `temperature=0` do dataframeit para
  a GPT-6 (na GPT-5 ele ja tirava sozinho).

### GPT-5, o1, o3, o3-mini (em aposentadoria)

o1 e o3-mini desligam em 23/10/2026; o3 e os snapshots `-2025-08-07`
de `gpt-5`, `gpt-5-mini` e `gpt-5-nano` em 11/12/2026. A OpenAI indica
os `gpt-5.6-*` como substitutos. Nao aceitam `temperature` (GPT-5 so com
raciocinio `none`). Parametros proprios dos modelos de raciocinio:

| Parametro | Valores | O que faz |
|---|---|---|
| `reasoning_effort` | `'none'` (GPT-5/6), `'low'`, `'medium'`, `'high'` | Quanta "cadeia de raciocinio" o modelo gera |
| `max_completion_tokens` | int | Total (inclui tokens de raciocinio invisiveis) |

**Recomendacao para extracao estruturada**: raciocinio desligado ou
modelo nao-raciocinio. Raciocinio so para tarefas de raciocinio livre
(ex: sumarizar divergencias doutrinarias extensas).

---

## §Anthropic (`provider='anthropic'`)

IDs sem sufixo de data: `claude-haiku-4-5`, `claude-sonnet-4-6`,
`claude-sonnet-5`, `claude-opus-5`, `claude-opus-5-5`.

### Claude Haiku 4.5 e Sonnet 4.6

| Parametro | Aceita | Default | Recomendacao extracao |
|---|---|---|---|
| `temperature` | 0.0 – 1.0 | 1.0 | **0** |
| `top_p` | 0.0 – 1.0 | — | Nao alterar |
| `top_k` | int | — | Nao alterar |
| `max_tokens` | int | obrigatorio | Dimensionar conforme Pydantic |

Nao ha parametro `seed`: a Anthropic nao expoe controle de seed. Para
reprodutibilidade, `temperature=0` basta na maioria dos casos.

### Claude Sonnet 5, Opus 4.7/4.8, Opus 5, Opus 5.5 e Fable

**Nao aceitam `temperature`, `top_p` nem `top_k`**: qualquer valor
diferente do padrao volta com erro 400. Como o dataframeit injeta
`temperature=0`, passe `model_kwargs={'temperature': None}`. No Fable,
o `langchain-anthropic` recusa antes da chamada, com `ValueError`, e a
saida e a mesma.

O thinking desses modelos e adaptativo e controlado por `effort`; no
Opus 5.5 ele nao pode ser desligado. Para extracao, esses modelos nao
sao default: use Haiku 4.5 e escale so com justificativa.

Fonte: Claude API Docs — Models overview, Adaptive thinking, Migration
guide.

---

## §Mistral (`provider='mistralai'`)

Nome do provider no LangChain: `'mistralai'`, nao `'mistral'`. Instalar
com `pip install dataframeit langchain-mistralai` (nao ha extra
`[mistral]`).

### Mistral Small / Mistral Large

`mistral-small-latest` aponta hoje para o Small 4 (`mistral-small-2603`)
e `mistral-large-latest` para o Large 3 (`mistral-large-2512`). Para
reprodutibilidade, registre o ID datado.

| Parametro | Aceita | Default | Recomendacao extracao |
|---|---|---|---|
| `temperature` | 0.0 – 1.5 (0-0.7 recomendado) | 0.7 | **0** |
| `random_seed` | int | — | Fixar |
| `top_p` | 0.0 – 1.0 | 1.0 | Nao alterar |
| `max_tokens` | int | — | Dimensionar |

Note: o parametro se chama `random_seed`, nao `seed`.

---

## §Cohere (`provider='cohere'`)

Instalar com `pip install dataframeit langchain-cohere` (nao ha extra
`[cohere]`).

### Command A

Os aliases `command-r` e `command-r-plus` estao deprecados desde
15/09/2025; o substituto indicado e `command-a-03-2025`. As versoes
`command-r-08-2024` e `command-r-plus-08-2024` ainda estao no ar.

| Parametro | Aceita | Default | Recomendacao extracao |
|---|---|---|---|
| `temperature` | float | 0.3 | **0** |
| `seed` | int | — | Fixar |
| `p` | 0.01 – 0.99 | — | Nao alterar (analogo a top_p) |
| `k` | int | — | Nao alterar (analogo a top_k) |
| `max_tokens` | int | — | Dimensionar |

---

## §Claude Code (`provider='claude_code'`)

Modo especial — delega as chamadas ao `claude-agent-sdk` e consome
tokens do plano Claude Code do usuario. Modelos disponiveis seguem o
plano. Zero custo incremental de API, mas consome quota do plano.

### Quando (nao) usar

**NAO assumir como default.** Antes de configurar `provider='claude_code'`,
faca a pergunta:

> "Para a codificacao via LLM, voce prefere: (a) usar tokens do seu plano
> Claude Code via `provider='claude_code'` (zero custo de API, consome
> quota do plano), ou (b) pagar via API tradicional com um provedor
> especifico (Gemini/OpenAI/Anthropic)?"

Alguns usuarios preferem (b) por razoes de billing (separar custos de
desenvolvimento de custos de pipelines de dados). Outros preferem (a)
por aproveitar melhor o plano.

### Requisitos

- `pip install dataframeit[claude-code]` (instala o `claude-agent-sdk`)
- Rodar dentro de um ambiente Claude Code com subscription ativa
- Nao suporta `use_search=True` (levanta `ValueError`) — para busca web,
  use `provider='google_genai'` ou `'openai'`
- As colunas `_input_tokens` e `_output_tokens` saem zeradas neste modo:
  o SDK devolve custo em USD, nao contagem de tokens

### Modelo (obrigatorio passar)

O dataframeit repassa `model` ao SDK. Como o default da funcao e
`'gemini-3-flash-preview'`, **passe sempre `model=`**. Aliases aceitos:
`'haiku'`, `'sonnet'`, `'opus'` (o SDK resolve para a versao atual da
familia no plano). Alternativa: o ID completo (ex: `'claude-haiku-4-5'`)
quando for preciso fixar a versao.

### Hiperparametros (via `model_kwargs`)

| Parametro | Valores | O que faz |
|---|---|---|
| `effort` | `'low'`, `'medium'`, `'high'`, `'xhigh'`, `'max'` | Profundidade do raciocinio no agente SDK. `'low'` adequado para extracao direta; niveis mais altos consomem mais tokens do plano |
| `max_turns` | int | Numero maximo de iteracoes do agente por linha (padrao: `1`). Subir so quando a codificacao exige ferramentas/raciocinio encadeado |
| `max_budget_usd` | float | Teto de gasto por linha em USD (padrao: `0.50`). Linha ultrapassando o teto e marcada como erro |

Outras chaves de `model_kwargs` (inclusive `temperature` e `top_p`) sao
ignoradas neste modo: o dataframeit so repassa as tres acima.

### Exemplo

```python
resultado = dataframeit(
    df, Codificacao, "Codifique: {texto}",
    provider='claude_code',
    model='haiku',                 # alias; ou 'claude-haiku-4-5' para fixar versao
    model_kwargs={
        'max_turns': 3,            # mais iteracoes de ferramenta/raciocinio
        'max_budget_usd': 1.00,    # teto de gasto por linha
        'effort': 'medium',        # profundidade do raciocinio
    },
)
```

---

## §Groq (`provider='groq'`)

### GPT-OSS 120B / 20B

`llama-3.3-70b-versatile` e `llama-3.1-8b-instant` foram desligados em
16/08/2026 nos planos free e developer (seguem so no Enterprise). Os
substitutos indicados pela Groq sao `openai/gpt-oss-120b` e
`openai/gpt-oss-20b`.

| Parametro | Aceita | Default | Recomendacao extracao |
|---|---|---|---|
| `temperature` | 0.0 – 2.0 | 1.0 | **0** |
| `seed` | int | — | Fixar |
| `top_p` | 0.0 – 1.0 | 1.0 | Nao alterar |
| `max_tokens` | int | varia | Dimensionar conforme Pydantic |

Groq roda modelos open-weight em hardware proprio otimizado para
latencia; tokens/s ficam bem acima dos provedores proprietarios, com
custo competitivo. Bom default para classificacao em alto volume quando
a qualidade de um modelo aberto basta. A Groq troca modelos com
frequencia: confira a pagina de deprecacoes antes de um run longo.

---

## Provedores hospedados no Brasil `[unreleased]`

A main do dataframeit (0.7.1, ainda nao no PyPI) documenta receitas
para rodar em Sao Paulo via Vertex AI (`southamerica-east1`), AWS
Bedrock (`sa-east-1`) e Azure OpenAI (Brazil South), com mensagens de
erro que indicam o pacote certo (`langchain-google-vertexai`,
`langchain-aws`, `langchain-openai`). Os providers do LangChain
(`google_vertexai`, `bedrock_converse`, `azure_openai`) ja funcionam na
0.6.0 com o pacote de integracao instalado; o que a 0.7.1 acrescenta e
a documentacao e as mensagens de erro. Ver `docs/guides/providers.md`
no repositorio do dataframeit.

---

## Registrar no protocolo (obrigatorio)

Para reprodutibilidade (registre no protocolo de pesquisa):

- `provider` (ex: `google_genai`, `anthropic`, `openai`)
- `model` exato, de preferencia o ID datado quando o provedor usa alias
  movel (ex: `mistral-small-2603` em vez de `mistral-small-latest`)
- `temperature` (ou "nao suportado")
- `seed` / `random_seed` (ou "nao suportado")
- `reasoning_effort` / `effort`, se usado
- `top_p`, `top_k` (se alterados do default)
- `max_output_tokens` / `max_tokens` / `max_completion_tokens`
- Data da execucao

Sem esse registro completo, o estudo nao e reprodutivel mesmo com o
codigo-fonte disponivel — modelos mudam silenciosamente atras do mesmo
nome.
