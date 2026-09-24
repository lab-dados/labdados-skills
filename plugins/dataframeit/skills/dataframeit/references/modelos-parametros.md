# Parametros aceitos por modelo — referencia consultavel

Matriz dos hiperparametros aceitos por cada familia de modelo, com
recomendacao para **extracao estruturada e classificacao de campos
finitos** (caso de uso central do dataframeit).

Atualizado em setembro/2026 a partir das paginas de modelos e de
deprecacao de cada provedor. Confirme na documentacao oficial antes de
executar: provedores aposentam modelos e mudam parametros com
frequencia.

**Lembrete do dataframeit**: nos provedores via LangChain, a biblioteca
nao envia parametro de amostragem, e o cliente recebe so o que vier em
`model_kwargs`. Para modelo que nao aceita `temperature`, nao passe o
parametro; para determinismo nos que aceitam, passe o valor
explicitamente, senao vale o default do provedor. Sem `model`, cada
provider usa o proprio modelo padrao. Ver `api.md §Modelo e temperature`.

---

## Tabela-resumo

| Modelo (`model=`) | Provider | `temperature` | `seed` | Config recomendada (extracao) |
|---|---|---|---|---|
| **`gemini-3.8-flash`** (padrao de `google_genai`), `gemini-3.5-flash-lite`, `gemini-3.6-flash`, `gemini-3.7-flash` | `google_genai` | **Deprecada** | Nao confirmado | `{}`: nao passar `temperature` |
| `gemini-3-flash-preview` (deprecado, era o default ate a 0.8.x) | `google_genai` | Aceita, **manter 1.0** | Sim | Migrar para `gemini-3.8-flash` |
| `gemini-3.1-pro-preview` | `google_genai` | Aceita, manter 1.0 | Sim | Nao e default, so escalacao justificada |
| `gpt-4.1-mini`, `gpt-4o-mini` (nao-raciocinio) | `openai` | Aceita 0.0-2.0 | Deprecado no Chat Completions | `{'temperature': 0}` |
| **GPT-6 Luna / Sol** (`gpt-6-luna` e o padrao de `openai`; `gpt-6-sol`) | `openai` | So com `reasoning_effort='none'` | Deprecado | `{'reasoning_effort': 'none', 'temperature': 0}` |
| GPT-6 Astra (`gpt-6-astra`) | `openai` | **Nao aceita** (sem nivel `none`) | Deprecado | `{}`: nao passar `temperature`. Nao e default para extracao |
| GPT-5 (`gpt-5`, `gpt-5-mini`, `gpt-5-nano`) | `openai` | So com raciocinio `none` | Deprecado | Snapshots saem em 11/12/2026, migrar |
| **o1, o3, o3-mini** | `openai` | **Nao aceita** | Nao | o1 e o3-mini saem em 23/10/2026, o3 em 11/12/2026 |
| `claude-haiku-4-5` | `anthropic` | Aceita 0.0-1.0 | Nao | `{'temperature': 0}` |
| `claude-sonnet-4-6` | `anthropic` | Aceita 0.0-1.0 | Nao | `{'temperature': 0}` |
| `claude-sonnet-5` (padrao de `anthropic`), `claude-opus-5`, `claude-opus-5-5`, Opus 4.7/4.8 | `anthropic` | **Nao aceita** (erro 400) | Nao | `{}`: nao passar `temperature`. Nao e default para extracao, apesar de ser o padrao do provider |
| `mistral-small-latest` (hoje Mistral Small 4) | `mistralai` | Aceita, 0-0.7 recomendado | `random_seed` | `{'temperature': 0, 'random_seed': 42}` |
| `mistral-large-latest` (hoje Mistral Large 3) | `mistralai` | Aceita | `random_seed` | `{'temperature': 0, 'random_seed': 42}` |
| `command-a-03-2025` | `cohere` | Aceita | Sim | `{'temperature': 0, 'seed': 42}` |
| `openai/gpt-oss-120b` (padrao de `groq`), `openai/gpt-oss-20b` | `groq` | Aceita 0.0-2.0 | Sim | `{'temperature': 0, 'seed': 42}` |

**Aposentados ou restritos que ainda aparecem em codigo antigo**: Gemini
1.5 (desligado em 29/09/2025); Gemini 2.5 Pro/Flash (nao deprecados, mas
com acesso restrito a quem ja usava; para projeto novo o Google indica
3.5 Flash-Lite ou 3.8 Flash); aliases `command-r`/`command-r-plus` da Cohere (deprecados desde
15/09/2025); `llama-3.3-70b-versatile` e `llama-3.1-8b-instant` na Groq
(desligados em 16/08/2026 nos planos free e developer).

**Regra geral**:

1. Para extracao/classificacao, **modelo pequeno** sempre — ver
   roteamento em `SKILL.md §Roteamento Passo 1`.
2. Determinismo por `temperature=0`, passado em `model_kwargs`, quando o
   modelo aceita. Nos Gemini 3.x o parametro esta deprecado ou deve
   ficar em 1.0 (ver §Google abaixo).
3. `seed` fixo sempre que disponivel, cumulativo com `temperature=0`.
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

# Gemini 3.8 Flash (padrao de google_genai): sem temperature
resultado = dataframeit(
    df, CodificacaoDecisao, "...",
    provider='google_genai',
    model='gemini-3.8-flash',
)

# GPT-6 Luna sem raciocinio (gpt-6-luna e o padrao da biblioteca)
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

### Gemini 3 Flash preview (deprecado)

Foi o default do dataframeit ate a 0.8.x; a 0.9.0 passou a usar
`gemini-3.8-flash` como padrao de `google_genai`. O Google o chama de
modelo Flash legado: a pagina de deprecacoes indica `gemini-3.6-flash`
como substituto e, para projeto novo, 3.5 Flash-Lite ou 3.8 Flash. Nao
existe `gemini-3-flash` GA. So use para reproduzir pipeline antigo.

| Parametro | Aceita | Default | Recomendacao extracao |
|---|---|---|---|
| `temperature` | 0.0 – 2.0 | **1.0** | **Manter 1.0** |
| `seed` | int | aleatorio | Fixar (ex: 42) |
| `top_p` | 0.0 – 1.0 | — | Nao alterar |
| `top_k` | int | — | Nao alterar |
| `max_output_tokens` | int | ~8192 | Dimensionar conforme tamanho Pydantic |

**Cuidado — nao reduzir `temperature`**: o Google recomenda manter
`temperature=1.0` nos Gemini 3. Reduzir pode causar looping ou
degradacao. Sem `temperature` em `model_kwargs`, vale o default do
provedor, que ja e 1.0. Para reprodutibilidade, fixe `seed`, nao
`temperature`.

### Gemini 3.5 Flash-Lite, 3.6 Flash, 3.7 Flash, 3.8 Flash (estaveis)

`temperature`, `top_p` e `top_k` estao deprecados a partir do
Gemini 3.6 Flash e do 3.5 Flash-Lite (changelog de 21/07/2026), e o
guia de migracao para o 3.8 manda remove-los. Nao passe esses
parametros em `model_kwargs`. Nao foi confirmado se `seed` continua
valendo nesses modelos.

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
rejeitados. Luna e Sol aceitam `reasoning_effort='none'`; o Astra nao
(niveis `low` a `max`). Duas saidas:

- Extracao deterministica (Luna/Sol): `{'reasoning_effort': 'none', 'temperature': 0}`.
- Manter o raciocinio (inclusive Astra): nao passe `temperature`. E o
  que acontece com `gpt-6-luna` sem `model_kwargs`, o padrao da
  biblioteca. Com `use_search=True`, o agente do dataframeit usa tools,
  e a OpenAI documenta function calling em Chat Completions para
  Luna/Sol so com `reasoning_effort='none'` (nao testado aqui).

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
`claude-sonnet-5`, `claude-opus-5`, `claude-opus-5-5`, `claude-fable-5-1`.
A Anthropic anuncia a aposentadoria do Haiku 4.5 para nao antes de
15/10/2026: confira a pagina de deprecacoes antes de fixa-lo num
pipeline longo.

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
diferente do padrao volta com erro 400, entao nao passe esses
parametros em `model_kwargs`. No Fable, o `langchain-anthropic` recusa
antes da chamada, com `ValueError`.

O thinking desses modelos e adaptativo e controlado por `effort`; no
Opus 5.5 e no Fable ele nao pode ser desligado. Para extracao, esses modelos nao
sao default: use Haiku 4.5 e escale so com justificativa. O Sonnet 5 e o
modelo padrao de `provider='anthropic'` sem `model`, entao passe
`model='claude-haiku-4-5'` explicitamente.

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
- Funciona com event loop ja ativo, como no Jupyter
- As colunas de tokens trazem o uso que o SDK informa, com leitura de
  cache em `_cached_input_tokens`; ficam nulas quando o SDK nao informa
- O modelo nao recebe ferramentas nem permissao para agir: o texto das
  linhas e conteudo nao confiavel e pode trazer instrucao injetada, e o
  dataframeit so pede a resposta estruturada

### Modelo

Com `model=None` (padrao), o runtime do Claude Code escolhe o modelo.
Para fixar, passe um alias (`'haiku'`, `'sonnet'`, `'opus'`, que o SDK
resolve para a versao atual da familia no plano) ou o ID completo (ex:
`'claude-haiku-4-5'`). Em pesquisa, fixe e registre o ID.

### Hiperparametros (via `model_kwargs`)

| Parametro | Valores | O que faz |
|---|---|---|
| `effort` | `'low'`, `'medium'`, `'high'`, `'xhigh'`, `'max'` | Profundidade do raciocinio no agente SDK. `'low'` adequado para extracao direta; niveis mais altos consomem mais tokens do plano |
| `max_turns` | int | Numero maximo de iteracoes do agente por linha (padrao: `1`). Como o modelo nao tem ferramentas, `1` basta para extracao |
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
        'max_budget_usd': 1.00,    # teto de gasto por linha
        'effort': 'low',           # extracao direta
    },
)
```

---

## §Codex (`provider='codex'`)

Modo experimental: usa o SDK Python oficial do Codex (`openai-codex`) e
a credencial local do Codex CLI, em vez de API key. As versoes do SDK e
do runtime fixadas pelo extra ainda sao de pre-lancamento.

### Quando (nao) usar

Mesma regra do Claude Code: **nao assumir como default**. Pergunte se o
usuario quer usar a conta do Codex ou pagar por API.

### Requisitos

- `pip install dataframeit[codex]`. O extra fica fora do `[all]` e traz
  o runtime empacotado; um `codex` instalado a parte nao participa da
  execucao
- `auth.json` do Codex criado uma vez pelo Codex CLI oficial:
  `codex --config cli_auth_credentials_store='"file"' login`
- Nao passe `api_key`: a chamada levanta erro de configuracao
- Nao suporta `use_search=True` (levanta `ValueError`)
- Enquanto uma execucao usa a credencial, outra execucao do dataframeit
  com o mesmo `auth.json` falha antes de iniciar. `parallel_requests`
  dentro da mesma execucao funciona. Nao use o Codex CLI com a mesma
  credencial ate o processamento terminar
- O modelo nao recebe busca web, shell nem MCP; aprovacoes sao negadas
  e o sandbox e somente leitura

### Modelo e `model_kwargs`

Com `model=None` (padrao), o runtime escolhe o modelo; para fixar,
passe o ID aceito pelo runtime. Em `model_kwargs`, so `effort` e
aceito (`'none'`, `'minimal'`, `'low'`, `'medium'`, `'high'`,
`'xhigh'`; padrao `'medium'`). Qualquer outra chave levanta erro de
configuracao, em vez de ser ignorada.

```python
resultado = dataframeit(
    df, Codificacao, "Codifique: {texto}",
    provider='codex',
    model_kwargs={'effort': 'low'},
    parallel_requests=3,
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

## Provedores hospedados no Brasil

Desde a 0.8.0, o dataframeit documenta receitas para rodar em Sao Paulo
via Vertex AI (`southamerica-east1`), AWS Bedrock (`sa-east-1`) e Azure
OpenAI (Brazil South), com mensagens de erro que indicam o pacote certo
(`langchain-google-vertexai`, `langchain-aws`, `langchain-openai`). Na
0.6.0, so `google_vertexai` passava pela validacao de dependencias; a
partir da 0.8.0, `bedrock_converse` e `azure_openai` tambem passam.
Esses providers nao tem modelo padrao: passe `model=` sempre. Ver
`docs/guides/providers.md` no repositorio do dataframeit.

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
