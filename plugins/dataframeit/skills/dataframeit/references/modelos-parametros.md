# Parâmetros aceitos por modelo: referência consultável

Matriz dos hiperparâmetros aceitos por cada família de modelo, com recomendação para **extração estruturada e classificação de campos finitos** (o caso central do dataframeit).

Atualizado em setembro de 2026 a partir das páginas de modelos e de deprecação de cada provedor. Confirme na documentação oficial antes de executar: provedores aposentam modelos e mudam parâmetros com frequência. Os modelos atuais, os preços e o padrão de cada provider no dataframeit estão em https://brunodcdo.com.br/dataframeit/guides/providers/; o padrão da versão instalada sai de `from dataframeit.core import DEFAULT_MODELS`.

**Lembrete do dataframeit**: nos provedores via LangChain, a biblioteca não envia parâmetro de amostragem, e o cliente recebe só o que vier em `model_kwargs`. Para modelo que não aceita `temperature`, não passe o parâmetro; para determinismo nos que aceitam, passe o valor explicitamente, senão vale o default do provedor. Ver `api.md §Modelo e temperature`.

---

## Tabela-resumo

| Modelo (`model=`) | Provider | `temperature` | `seed` | Config recomendada (extração) |
|---|---|---|---|---|
| `gemini-3.8-flash`, `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash-lite` | `google_genai` | **Deprecada** | Não confirmado | `{}`: não passar `temperature` |
| `gemini-3-flash-preview` (deprecado) | `google_genai` | Aceita, **manter 1.0** | Sim | Migrar para um Flash estável |
| `gemini-3.1-pro-preview` | `google_genai` | Aceita, manter 1.0 | Sim | Não é default; só escalação justificada |
| `gpt-4.1-mini`, `gpt-4o-mini` (sem raciocínio) | `openai` | Aceita 0.0-2.0 | Deprecado no Chat Completions | `{'temperature': 0}` |
| GPT-6 Luna / Sol (`gpt-6-luna`, `gpt-6-sol`) | `openai` | Só com `reasoning_effort='none'` | Deprecado | `{'reasoning_effort': 'none', 'temperature': 0}` |
| GPT-6 Astra (`gpt-6-astra`) | `openai` | **Não aceita** (sem nível `none`) | Deprecado | `{}`: não passar `temperature`. Não é default para extração |
| GPT-5 (`gpt-5`, `gpt-5-mini`, `gpt-5-nano`) | `openai` | Só com raciocínio `none` | Deprecado | Snapshots saem em 11/12/2026; migrar |
| **o1, o3, o3-mini** | `openai` | **Não aceita** | Não | o1 e o3-mini saem em 23/10/2026, o3 em 11/12/2026 |
| `claude-haiku-4-5` | `anthropic` | Aceita 0.0-1.0 | Não | `{'temperature': 0}` |
| `claude-sonnet-4-6` | `anthropic` | Aceita 0.0-1.0 | Não | `{'temperature': 0}` |
| `claude-sonnet-5`, `claude-opus-5`, `claude-opus-5-5`, Opus 4.7/4.8 | `anthropic` | **Não aceita** (erro 400) | Não | `{}`: não passar `temperature`. Não é default para extração |
| `mistral-small-latest` (hoje Mistral Small 4) | `mistralai` | Aceita, 0-0.7 recomendado | `random_seed` | `{'temperature': 0, 'random_seed': 42}` |
| `mistral-large-latest` (hoje Mistral Large 3) | `mistralai` | Aceita | `random_seed` | `{'temperature': 0, 'random_seed': 42}` |
| `command-a-03-2025` | `cohere` | Aceita | Sim | `{'temperature': 0, 'seed': 42}` |
| `openai/gpt-oss-120b`, `openai/gpt-oss-20b` | `groq` | Aceita 0.0-2.0 | Sim | `{'temperature': 0, 'seed': 42}` |

**Aposentados ou restritos que ainda aparecem em código antigo**: Gemini 1.5 (desligado em 29/09/2025); Gemini 2.5 Pro/Flash (acesso restrito a quem já usava; para projeto novo o Google indica 3.5 Flash-Lite ou 3.8 Flash); aliases `command-r`/`command-r-plus` da Cohere (deprecados desde 15/09/2025); `llama-3.3-70b-versatile` e `llama-3.1-8b-instant` na Groq (desligados em 16/08/2026 nos planos free e developer).

**Regra geral**:

1. Para extração e classificação, **modelo pequeno** sempre (ver roteamento em `SKILL.md §Passo 1`).
2. Determinismo por `temperature=0`, passado em `model_kwargs`, quando o modelo aceita. Nos Gemini 3.x o parâmetro está deprecado ou deve ficar em 1.0 (§Google).
3. `seed` fixo sempre que disponível, cumulativo com `temperature=0`.
4. **Modelos de raciocínio** (série o, GPT-5/GPT-6 com raciocínio ligado, Claude Sonnet 5/Opus) não aceitam `temperature`. Para extração, prefira modelo sem raciocínio ou desligue o raciocínio quando o provedor permite (GPT-6 Luna/Sol com `reasoning_effort='none'`).
5. Parâmetro recusado pelo provedor (erro 400) não ganha nova tentativa: todas as linhas terminam `'error'`. Rode uma amostra antes.

---

## Como passar via `dataframeit`

O dicionário `model_kwargs` é repassado ao cliente do provedor:

```python
from dataframeit import dataframeit

# Claude Haiku 4.5
resultado = dataframeit(
    df, CodificacaoDecisao, "...",
    provider='anthropic',
    model='claude-haiku-4-5',
    model_kwargs={'temperature': 0},
)

# Gemini 3.8 Flash: sem temperature
resultado = dataframeit(
    df, CodificacaoDecisao, "...",
    provider='google_genai',
    model='gemini-3.8-flash',
)

# GPT-6 Luna sem raciocínio
resultado = dataframeit(
    df, CodificacaoDecisao, "...",
    provider='openai',
    model='gpt-6-luna',
    model_kwargs={'reasoning_effort': 'none', 'temperature': 0},
)
```

Quando o nome do parâmetro varia entre providers (ex.: `max_tokens` vs. `max_output_tokens` vs. `max_completion_tokens`), passe conforme o cliente do provedor espera: o dataframeit não normaliza esses nomes.

---

## §Google (`provider='google_genai'`)

### Gemini 3 Flash preview (deprecado)

O Google o chama de modelo Flash legado: a página de deprecações indica `gemini-3.6-flash` como substituto e, para projeto novo, 3.5 Flash-Lite ou 3.8 Flash. Não existe `gemini-3-flash` GA. Só use para reproduzir pipeline antigo.

| Parâmetro | Aceita | Default | Recomendação para extração |
|---|---|---|---|
| `temperature` | 0.0-2.0 | **1.0** | **Manter 1.0** |
| `seed` | int | aleatório | Fixar (ex.: 42) |
| `top_p` | 0.0-1.0 | | Não alterar |
| `top_k` | int | | Não alterar |
| `max_output_tokens` | int | ~8192 | Dimensionar conforme o Pydantic |

**Cuidado, não reduzir `temperature`**: o Google recomenda manter `temperature=1.0` nos Gemini 3. Reduzir pode causar looping ou degradação. Sem `temperature` em `model_kwargs`, vale o default do provedor, que já é 1.0. Para reprodutibilidade, fixe `seed`, não `temperature`.

### Gemini 3.5 Flash-Lite, 3.6 Flash, 3.7 Flash, 3.8 Flash (estáveis)

`temperature`, `top_p` e `top_k` estão deprecados a partir do Gemini 3.6 Flash e do 3.5 Flash-Lite (changelog de 21/07/2026), e o guia de migração para o 3.8 manda removê-los. Não passe esses parâmetros em `model_kwargs`. Não foi confirmado se `seed` continua valendo nesses modelos. O raciocínio se ajusta com `thinking_level` (ex.: `{'thinking_level': 'low'}`).

### Gemini 3.1 Pro preview

Único Pro de texto disponível (`gemini-3-pro-preview` foi desligado em 09/03/2026). Mesma recomendação de `temperature=1.0`. Reservar para escalação justificada.

---

## §OpenAI (`provider='openai'`)

### gpt-4.1-mini, gpt-4o-mini (sem raciocínio)

Continuam disponíveis como aliases (só alguns snapshots antigos saem em 23/10/2026).

| Parâmetro | Aceita | Default | Recomendação para extração |
|---|---|---|---|
| `temperature` | 0.0-2.0 | 1.0 | **0** |
| `seed` | int | | Marcado como deprecado no Chat Completions |
| `top_p` | 0.0-1.0 | 1.0 | Não alterar |
| `max_completion_tokens` | int | varia | Dimensionar |

### GPT-6 (`gpt-6-luna`, `gpt-6-sol`, `gpt-6-astra`)

Família corrente; `gpt-6-luna` é o modelo mais barato. O raciocínio vem ligado (`medium`) por padrão, e nesse modo `temperature` e `top_p` são rejeitados. Luna e Sol aceitam `reasoning_effort='none'`; o Astra não (níveis `low` a `max`). Duas saídas:

- Extração determinística (Luna/Sol): `{'reasoning_effort': 'none', 'temperature': 0}`.
- Manter o raciocínio (inclusive Astra): não passe `temperature`. É o que acontece com `provider='openai'` sem `model_kwargs`. Com `use_search=True`, o agente do dataframeit usa tools, e a OpenAI documenta function calling em Chat Completions para Luna/Sol só com `reasoning_effort='none'` (não testado aqui).

### GPT-5, o1, o3, o3-mini (em aposentadoria)

o1 e o3-mini desligam em 23/10/2026; o3 e os snapshots `-2025-08-07` de `gpt-5`, `gpt-5-mini` e `gpt-5-nano` em 11/12/2026. A OpenAI indica os `gpt-5.6-*` como substitutos. Não aceitam `temperature` (GPT-5 só com raciocínio `none`). Parâmetros próprios dos modelos de raciocínio:

| Parâmetro | Valores | O que faz |
|---|---|---|
| `reasoning_effort` | `'none'` (GPT-5/6), `'low'`, `'medium'`, `'high'` | Quanto raciocínio o modelo gera |
| `max_completion_tokens` | int | Total da saída, inclui os tokens de raciocínio |

**Recomendação para extração estruturada**: raciocínio desligado ou modelo sem raciocínio. Raciocínio só para tarefas de raciocínio livre (ex.: sumarizar divergências doutrinárias extensas).

---

## §Anthropic (`provider='anthropic'`)

IDs sem sufixo de data: `claude-haiku-4-5`, `claude-sonnet-4-6`, `claude-sonnet-5`, `claude-opus-5`, `claude-opus-5-5`, `claude-fable-5-1`. A Anthropic anuncia a aposentadoria do Haiku 4.5 para não antes de 15/10/2026: confira a página de deprecações antes de fixá-lo num pipeline longo.

### Claude Haiku 4.5 e Sonnet 4.6

| Parâmetro | Aceita | Default | Recomendação para extração |
|---|---|---|---|
| `temperature` | 0.0-1.0 | 1.0 | **0** |
| `top_p` | 0.0-1.0 | | Não alterar |
| `top_k` | int | | Não alterar |
| `max_tokens` | int | obrigatório | Dimensionar conforme o Pydantic |

Não há parâmetro `seed`: a Anthropic não expõe controle de seed. Para reprodutibilidade, `temperature=0` basta na maioria dos casos.

### Claude Sonnet 5, Opus 4.7/4.8, Opus 5, Opus 5.5 e Fable

**Não aceitam `temperature`, `top_p` nem `top_k`**: qualquer valor diferente do padrão volta com erro 400, então não passe esses parâmetros em `model_kwargs`. No Fable, o `langchain-anthropic` recusa antes da chamada, com `ValueError`.

O thinking desses modelos é adaptativo e controlado por `effort`; no Opus 5.5 e no Fable ele não pode ser desligado. Para extração, esses modelos não são default: use Haiku 4.5 e escale só com justificativa. O padrão de `provider='anthropic'` sem `model` é um deles (confira `DEFAULT_MODELS`), então passe `model='claude-haiku-4-5'` explicitamente.

Fonte: Claude API Docs (Models overview, Adaptive thinking, Migration guide).

---

## §Mistral (`provider='mistralai'`)

Nome do provider no LangChain: `'mistralai'`, não `'mistral'`. Instalar com `pip install dataframeit langchain-mistralai` (não há extra `[mistral]`). A chave é `MISTRAL_API_KEY`. Sem modelo padrão: passe `model=`.

### Mistral Small / Mistral Large

`mistral-small-latest` aponta hoje para o Small 4 (`mistral-small-2603`) e `mistral-large-latest` para o Large 3 (`mistral-large-2512`). Para reprodutibilidade, registre o ID datado.

| Parâmetro | Aceita | Default | Recomendação para extração |
|---|---|---|---|
| `temperature` | 0.0-1.5 (0-0.7 recomendado) | 0.7 | **0** |
| `random_seed` | int | | Fixar |
| `top_p` | 0.0-1.0 | 1.0 | Não alterar |
| `max_tokens` | int | | Dimensionar |

O parâmetro se chama `random_seed`, não `seed`.

---

## §Cohere (`provider='cohere'`)

Instalar com `pip install dataframeit langchain-cohere` (não há extra `[cohere]`). A chave é `COHERE_API_KEY`. Sem modelo padrão: passe `model=`.

### Command A

Os aliases `command-r` e `command-r-plus` estão deprecados desde 15/09/2025; o substituto indicado é `command-a-03-2025`. As versões `command-r-08-2024` e `command-r-plus-08-2024` ainda estão no ar.

| Parâmetro | Aceita | Default | Recomendação para extração |
|---|---|---|---|
| `temperature` | float | 0.3 | **0** |
| `seed` | int | | Fixar |
| `p` | 0.01-0.99 | | Não alterar (análogo a top_p) |
| `k` | int | | Não alterar (análogo a top_k) |
| `max_tokens` | int | | Dimensionar |

---

## §Claude Code (`provider='claude_code'`)

Delega as chamadas ao Claude Agent SDK (`claude-agent-sdk`), que executa o Claude Code CLI. Referência oficial: https://brunodcdo.com.br/dataframeit/guides/providers/#claude-code.

### Quando (não) usar

**Não assumir como default.** Antes de configurar `provider='claude_code'`, pergunte:

> "Para a codificação via LLM, você prefere (a) usar a autenticação do seu Claude Code via `provider='claude_code'`, ou (b) pagar pela API tradicional de um provedor específico (OpenAI, Gemini, Anthropic)?"

Alguns usuários preferem (b) para separar custos de desenvolvimento dos de pipelines de dados; outros preferem (a) para aproveitar o plano.

### Requisitos e comportamento

- `pip install dataframeit[claude-code]` (instala o `claude-agent-sdk`, que traz o CLI).
- Autenticação do próprio Claude Code: as credenciais de um login feito numa instalação do Claude Code na máquina (o CLI que o extra traz não fica no `PATH`), ou `ANTHROPIC_API_KEY`, que cobra pela API. O parâmetro `api_key` é ignorado.
- Não suporta `use_search=True`; para busca web, use um provider via LangChain.
- Funciona com event loop já ativo, como no Jupyter.
- O texto das linhas é tratado como conteúdo não confiável: a execução roda sem ferramentas, sem os settings de usuário e de projeto e com `--strict-mcp-config`, de modo que servidores MCP e regras `permissions.allow` do Claude Code do usuário não chegam a ela.
- As colunas de tokens trazem o uso que o SDK informa, com leitura de cache em `_cached_input_tokens`, e ficam nulas quando o SDK não informa.
- Com `track_tokens=True`, o resumo ao fim da execução mostra o custo em USD informado pelo SDK, somando as tentativas re-tentadas e as linhas que falharam.

### Modelo

Com `model=None` (padrão), o runtime do Claude Code escolhe. Para fixar, passe um alias (`'haiku'`, `'sonnet'`, `'opus'`, que o SDK resolve para a versão atual da família) ou o ID completo (ex.: `'claude-haiku-4-5'`). Em pesquisa, fixe e registre o ID.

### `model_kwargs`

Só três chaves são lidas; as outras, inclusive `temperature` e `top_p`, são ignoradas.

| Parâmetro | Padrão | O que faz |
|---|---|---|
| `effort` | do runtime | Profundidade do raciocínio (ex.: `'low'`, `'medium'`, `'high'`). `'low'` serve à extração direta |
| `max_turns` | `1` | Iterações do agente por tentativa. Sem ferramentas, `1` basta |
| `max_budget_usd` | `0.50` | Teto de gasto **por tentativa**, em USD. Como uma resposta vazia ou fora do schema é tentada de novo, uma linha pode gastar até `max_retries` vezes esse valor |

Estourar `max_budget_usd` ou `max_turns` encerra a linha com erro definitivo, sem nova tentativa.

```python
resultado = dataframeit(
    df, Codificacao, "Codifique: {texto}",
    provider='claude_code',
    model='haiku',                 # alias; ou 'claude-haiku-4-5' para fixar a versão
    model_kwargs={
        'max_budget_usd': 0.25,    # teto por tentativa
        'effort': 'low',           # extração direta
    },
)
```

---

## §Codex (`provider='codex'`)

Experimental: usa o SDK Python oficial do Codex (`openai-codex`) e a credencial local do Codex CLI, em vez de API key. As versões do SDK e do runtime fixadas pelo extra ainda são de pré-lançamento.

### Quando (não) usar

Mesma regra do Claude Code: **não assumir como default**. Pergunte se o usuário quer usar a conta do Codex ou pagar por API.

### Requisitos

- `pip install dataframeit[codex]`. O extra fica fora do `[all]` e traz o runtime empacotado; um `codex` instalado à parte não participa da execução.
- `auth.json` do Codex criado uma vez pelo Codex CLI oficial: `codex --config cli_auth_credentials_store='"file"' login`. Ver https://brunodcdo.com.br/dataframeit/getting-started/installation/.
- Não passe `api_key`: a chamada levanta erro de configuração.
- Não suporta `use_search=True`.
- O schema Pydantic precisa caber no Structured Outputs, com campos no nível raiz: o preflight rejeita `RootModel`, `Any`, `dict` com chaves dinâmicas, tupla de tamanho fixo e `set` antes de processar qualquer linha (`ProviderConfigurationError`).
- Enquanto uma execução usa a credencial, outra execução do dataframeit com o mesmo `auth.json` falha antes de iniciar. `parallel_requests` dentro da mesma execução funciona. Não use o Codex CLI com a mesma credencial até o processamento terminar.
- O modelo não recebe busca web, shell nem MCP; aprovações são negadas e o sandbox é somente leitura.

### Modelo e `model_kwargs`

Com `model=None` (padrão), o runtime escolhe; para fixar, passe o ID aceito pelo runtime. Em `model_kwargs`, **só `effort`** é aceito (padrão `'medium'`); valor inválido levanta erro com a lista dos aceitos, e qualquer outra chave levanta `ProviderConfigurationError` antes de começar, em vez de ser ignorada.

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

`llama-3.3-70b-versatile` e `llama-3.1-8b-instant` foram desligados em 16/08/2026 nos planos free e developer (seguem só no Enterprise). Os substitutos indicados pela Groq são `openai/gpt-oss-120b` e `openai/gpt-oss-20b`.

| Parâmetro | Aceita | Default | Recomendação para extração |
|---|---|---|---|
| `temperature` | 0.0-2.0 | 1.0 | **0** |
| `seed` | int | | Fixar |
| `top_p` | 0.0-1.0 | 1.0 | Não alterar |
| `max_tokens` | int | varia | Dimensionar conforme o Pydantic |

A Groq roda modelos open-weight em hardware próprio otimizado para latência, com free tier limitado por requisições por minuto em cada modelo. Bom default para classificação em alto volume quando a qualidade de um modelo aberto basta. A Groq troca modelos com frequência (sobretudo os `preview`): confira https://console.groq.com/docs/models antes de um run longo.

---

## Provedores hospedados no Brasil

O dataframeit documenta receitas para rodar em São Paulo via Vertex AI (`southamerica-east1`, com `provider='google_genai'` e `model_kwargs={'vertexai': True, ...}` ou `provider='google_vertexai'`), AWS Bedrock (`provider='bedrock_converse'`, `sa-east-1`) e Azure OpenAI (`provider='azure_openai'`, Brazil South), com os pacotes `langchain-google-vertexai`, `langchain-aws` e `langchain-openai`. Esses providers não têm modelo padrão: passe `model=` sempre. No Bedrock, o Claude Sonnet 5 em `sa-east-1` só existe pelo perfil global (`global.`), que pode processar fora do Brasil. Receitas completas em https://brunodcdo.com.br/dataframeit/guides/providers/#servidor-no-brasil-sao-paulo.

---

## Registrar no protocolo (obrigatório)

Para reprodutibilidade, registre no protocolo de pesquisa:

- `provider` (ex.: `google_genai`, `anthropic`, `openai`);
- `model` exato, de preferência o ID datado quando o provedor usa alias móvel (ex.: `mistral-small-2603` em vez de `mistral-small-latest`);
- `temperature` (ou "não suportado");
- `seed` / `random_seed` (ou "não suportado");
- `reasoning_effort` / `effort`, se usado;
- `top_p`, `top_k` (se alterados do default);
- `max_output_tokens` / `max_tokens` / `max_completion_tokens`;
- versão do dataframeit (`dataframeit.__version__`) e data da execução.

Sem esse registro, o estudo não é reprodutível mesmo com o código-fonte disponível, porque modelos mudam em silêncio atrás do mesmo nome.
