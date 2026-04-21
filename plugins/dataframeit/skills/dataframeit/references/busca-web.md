# Busca web em dataframeit

Enriquecimento com dados da internet via `use_search=True`. Este arquivo
cobre a configuracao de busca, os dois provedores (Tavily e Exa), como
agrupar campos para economizar, custos e warnings de rate limit.

Para config de campo individual em `json_schema_extra` (prompt por
campo, `search_depth` por campo), veja tambem
`pydantic-patterns.md`.

## Indice

1. [Instalacao e API keys](#instalacao-e-api-keys)
2. [Configuracao basica](#configuracao-basica)
3. [Busca por campo (search_per_field)](#busca-por-campo-search_per_field)
4. [Search groups — agrupar campos](#search-groups--agrupar-campos)
5. [Custos de busca](#custos-de-busca)
6. [Warnings de rate limit](#warnings-de-rate-limit)

---

## Instalacao e API keys

```bash
pip install dataframeit[google,search]
```

- **Tavily** (padrao): `TAVILY_API_KEY` — https://tavily.com (1000 buscas/mes gratis)
- **Exa**: `EXA_API_KEY` — https://exa.ai (mais economico em alto volume)

---

## Configuracao basica

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

Quando `use_search=True` e nenhum campo tem config propria, o
`dataframeit` faz **uma** busca por linha usando o prompt principal
como query — os resultados alimentam o agente que preenche todos os
campos.

---

## Busca por campo (search_per_field)

Cada campo com configuracao de busca no `json_schema_extra` recebe sua
propria busca — util quando cada campo precisa de fontes diferentes:

```python
resultado = dataframeit(
    df, MedicamentoInfo,
    "Analise o medicamento: {texto}",
    use_search=True,
    search_per_field=True,        # busca separada por campo
)
```

**Custo**: multiplica as buscas por campo. Se o modelo tem 5 campos com
`json_schema_extra` configurado, cada linha dispara 5 buscas. Para
reduzir, use `search_groups`.

---

## Search groups — agrupar campos

Campos relacionados compartilham uma unica busca:

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

Cada grupo cria **uma** chamada de busca. Sem grupos, seriam 5 chamadas
separadas.

| Chave do grupo | Tipo | Descricao |
|---|---|---|
| `fields` | list[str] | Campos do modelo que compartilham esta busca (obrigatorio) |
| `prompt` | str | Prompt customizado para a busca deste grupo (opcional) |
| `search_depth` | str | `"basic"` ou `"advanced"` (opcional, herda do global) |
| `max_results` | int | Max resultados (opcional, herda do global) |

**Regra pratica**: use `search_groups` sempre que tiver 2+ campos com
busca — o ganho de custo e imediato.

---

## Custos de busca

| Provedor | Tipo | Custo | Free tier |
|---|---|---|---|
| Tavily | basic | 1 credito/busca | 1000 buscas/mes |
| Tavily | advanced | 2 creditos/busca | 1000 buscas/mes |
| Exa | 1-25 resultados | ~$0.005/busca | — |
| Exa | 26-100 resultados | ~$0.025/busca | — |

**Recomendacao**: Tavily para volume baixo/medio (< 2667 buscas/mes);
Exa para volume alto com busca semantica.

---

## Warnings de rate limit

O `dataframeit` emite um `UserWarning` informativo quando o volume de
consultas se aproxima do limite de rate do provedor de busca. O warning
nao interrompe a execucao — serve para voce decidir entre baixar
`parallel_requests`, subir `rate_limit_delay` ou trocar de provedor
antes de bater em 429.
