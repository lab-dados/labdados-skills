# Busca web em dataframeit

Enriquecimento com dados da internet via `use_search=True`. Este arquivo cobre a configuração de busca, os dois provedores (Tavily e Exa), o limite de buscas por agente, como agrupar campos para economizar, custos e rate limit. A referência oficial é https://brunodcdo.com.br/dataframeit/guides/web-search/.

Para configuração de campo individual em `json_schema_extra` (prompt por campo, `search_depth` por campo, condicionais), veja também `pydantic-patterns.md`.

## Índice

1. [Instalação e API keys](#instalação-e-api-keys)
2. [Como a busca funciona](#como-a-busca-funciona)
3. [Configuração básica](#configuração-básica)
4. [Limite de buscas (max_search_calls)](#limite-de-buscas-max_search_calls)
5. [Busca por campo (search_per_field)](#busca-por-campo-search_per_field)
6. [Search groups: agrupar campos](#search-groups-agrupar-campos)
7. [Custos de busca](#custos-de-busca)
8. [Rate limit e paralelismo](#rate-limit-e-paralelismo)

---

## Instalação e API keys

```bash
pip install dataframeit[openai,search]      # Tavily
pip install dataframeit[openai,search-exa]  # Exa
pip install dataframeit[openai,search-all]  # os dois
```

- **Tavily** (padrão): `TAVILY_API_KEY`, https://tavily.com (1000 buscas/mês grátis)
- **Exa**: `EXA_API_KEY`, https://exa.ai

Chave ausente levanta `ValueError` antes de processar. A busca só funciona com providers via LangChain: `provider='claude_code'` e `'codex'` não aceitam `use_search=True`.

---

## Como a busca funciona

Com `use_search=True`, cada linha é resolvida por um **agente** que decide se e quando buscar, faz até `max_search_calls` buscas e depois responde no formato do modelo Pydantic. Não é uma busca fixa por linha: um modelo pode buscar uma vez, várias ou nenhuma.

| Configuração | Agentes por linha | Buscas por linha, no máximo |
|---|---|---|
| `search_per_field=False` (padrão) | 1 | `max_search_calls` |
| `search_per_field=True` | 1 por campo, ou por grupo | `max_search_calls` por agente |

Um erro do Tavily ou do Exa (quota, chave inválida, falha de rede) interrompe o agente, e a linha volta ao ciclo de novas tentativas; esgotadas as tentativas, fica `'error'`. "Sem resultados" e erro de argumento do Tavily (400, 422, como consulta longa demais) voltam ao modelo como mensagem, e ele pode tentar outra consulta.

---

## Configuração básica

```python
resultado = dataframeit(
    df, Modelo,
    "Analise e busque informações complementares: {texto}",
    use_search=True,              # habilita busca
    search_provider="tavily",     # "tavily" (padrão) ou "exa"
    search_depth="basic",         # "basic" (1 crédito) ou "advanced" (2 créditos); só Tavily
    max_results=5,                # resultados por busca (1-20)
    max_search_calls=10,          # buscas por execução do agente (padrão 10)
)
```

Com `search_provider="exa"`, `search_depth` é ignorado; `max_results` e o corte de 1000 caracteres por resultado valem.

---

## Limite de buscas (max_search_calls)

`max_search_calls` (padrão 10, int >= 1) limita as buscas de cada execução do agente. Ao atingi-lo, as buscas seguintes são bloqueadas e o agente responde com o que encontrou. As buscas bloqueadas não entram em `_search_credits`, e o limite de passos do agente acompanha o teto, para que um modelo que ignore o bloqueio pare em poucas chamadas.

Vale em três níveis, e o mais específico vence:

| Nível | Onde |
|---|---|
| Global | `dataframeit(..., max_search_calls=3)` |
| Por grupo | `search_groups={"g": {"fields": [...], "max_search_calls": 2}}` |
| Por campo | `Field(json_schema_extra={"max_search_calls": 1})`, com `search_per_field=True` |

Nos overrides por grupo e por campo, só a ausência (`None`) cai no valor global. Quando uma ou duas buscas bastam, reduzir o limite é a forma mais direta de cortar custo.

---

## Busca por campo (search_per_field)

Com `search_per_field=True`, **cada campo do modelo** ganha um agente próprio por linha, com as próprias buscas. Serve quando cada campo precisa de fontes diferentes, e é o modo exigido por configuração por campo em `json_schema_extra`, por campos condicionais e por `search_groups`.

```python
resultado = dataframeit(
    df, MedicamentoInfo,
    "Analise o medicamento: {texto}",
    use_search=True,
    search_per_field=True,        # um agente por campo
)
```

**Custo**: um modelo de 5 campos cria 5 agentes por linha, cada um com até `max_search_calls` buscas. Para reduzir, agrupe campos com `search_groups` e baixe `max_search_calls`.

Chaves por campo em `json_schema_extra`: `prompt` (ou `prompt_replace`), `prompt_append`, `search_depth`, `max_results`, `max_search_calls`, `condition`, `depends_on`. Qualquer uma delas sem `use_search=True` e `search_per_field=True` levanta `ValueError`, e a mensagem diz o que falta. Ver `pydantic-patterns.md`.

---

## Search groups: agrupar campos

Campos relacionados compartilham **um agente** por linha:

```python
resultado = dataframeit(
    df, Modelo, prompt,
    use_search=True,
    search_per_field=True,   # obrigatório com search_groups (senão ValueError)
    search_groups={
        "localizacao": {
            "fields": ["cidade", "estado", "pais"],
            "max_results": 5,
        },
        "contato": {
            "fields": ["email", "telefone"],
            "prompt": "Busque informações de contato de: {texto}",
            "search_depth": "advanced",
            "max_search_calls": 3,
        },
    },
)
```

Aqui são 2 agentes por linha, mais um para cada campo fora dos grupos, em vez de 5.

| Chave do grupo | Tipo | Descrição |
|---|---|---|
| `fields` | list[str] | Campos do modelo que compartilham o agente (obrigatório) |
| `prompt` | str | Prompt do grupo; use `{texto}` (ou o sinônimo `{query}`) para o texto |
| `search_depth` | str | `"basic"` ou `"advanced"` (herda do global) |
| `max_results` | int | Resultados por busca, 1-20 (herda do global) |
| `max_search_calls` | int | Buscas do agente do grupo (herda do global) |

**Regras de validação**: exige `use_search=True` e `search_per_field=True`; os campos precisam existir no modelo; um campo não pode estar em dois grupos; e campo agrupado não pode ter configuração de busca própria em `json_schema_extra` (escolha entre configurar o campo ou o grupo).

**Regra prática**: use `search_groups` sempre que tiver 2+ campos que dependem da mesma pesquisa.

Campos condicionais continuam valendo com grupos: campo com condição falsa fica `None` e não é pedido ao agente, e grupos e campos isolados rodam na ordem das dependências. Ver `pydantic-patterns.md §Padrão 4`.

---

## Custos de busca

| Provedor | Tipo | Custo | Free tier |
|---|---|---|---|
| Tavily | basic | 1 crédito/busca | 1000 buscas/mês |
| Tavily | advanced | 2 créditos/busca | 1000 buscas/mês |
| Exa | até 20 resultados (o máximo de `max_results`) | 1 crédito, ~US$ 0,005/busca | não |

Os preços mudam; confira em https://tavily.com/pricing e https://exa.ai/pricing.

`_search_credits` traz os créditos gastos na linha e conta só as chamadas da ferramenta de busca, sem a resposta estruturada nem as buscas bloqueadas por `max_search_calls`. O resumo ao fim da execução mostra o total.

**Para economizar**: `max_results` entre 3 e 5; `search_depth='basic'`; filtrar o DataFrame antes; `search_per_field=False` quando possível, ou `search_groups`; `max_search_calls` baixo quando uma ou duas buscas bastam.

---

## Rate limit e paralelismo

Com `parallel_requests`, é fácil passar do limite do provedor de busca, que costuma ser mais apertado que o do LLM:

| Provedor | Rate limit aproximado |
|---|---|
| Tavily | ~100 req/min |
| Exa | ~300 req/min |

Com `parallel_requests=20` e `search_per_field=True` num modelo de 4 campos, rodam 80 agentes ao mesmo tempo.

| Cenário | Tavily: `parallel_requests` / `rate_limit_delay` | Exa: `parallel_requests` / `rate_limit_delay` |
|---|---|---|
| `search_per_field=False` | 5-10 / 0.5 | 10-15 / 0.3 |
| `search_per_field=True`, 2-3 campos | 3-5 / 0.5 | 5-8 / 0.3 |
| `search_per_field=True`, 4+ campos | 2-3 / 1.0 | 3-5 / 0.5 |

O `dataframeit` emite um `UserWarning` quando a configuração parece arriscada (muitas consultas concorrentes ou taxa estimada perto do limite), com recomendação de `parallel_requests` e `rate_limit_delay`. O aviso também dispara em execução sequencial quando `search_per_field=True` produz mais de 100 consultas no total. Ele não interrompe a execução.
