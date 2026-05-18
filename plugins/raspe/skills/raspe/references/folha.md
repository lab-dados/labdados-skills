# raspe.folha

## Fonte e escopo

Busca de notícias da Folha de São Paulo — `https://search.folha.uol.com.br/search`. Cobre matérias online e do jornal impresso.

## Assinatura

```python
raspe.folha().raspar(
    pesquisa: str | list[str],
    site: Literal["todos", "online", "jornal"] = "todos",
    data_inicio: str | None = None,
    data_fim: str | None = None,
    paginas: range | None = None,
) -> pd.DataFrame
```

## Colunas retornadas

| Coluna | Conteúdo |
|---|---|
| `link` | URL da matéria. |
| `titulo` | Título da reportagem. |
| `resumo` | Lead/resumo. |
| `data` | Data de publicação (formato amigável — varia por matéria). |
| `termo_busca` | Adicionada automaticamente. |

## Parâmetros específicos

- `site`:
  - `"todos"` (default) — online + jornal impresso.
  - `"online"` — só o site Folha.com.
  - `"jornal"` — só matérias do jornal impresso. Útil para retrospectiva histórica.
- `data_inicio`/`data_fim`: `YYYY-MM-DD`, `DD/MM/YYYY` ou `YYYYMMDD`. A biblioteca converte internamente para o formato `DD/MM/YYYY` que a API da Folha exige.

## Gotchas

- **Teto de 10.000 resultados (400 páginas)** — limitação do motor de busca da Folha. Se a coleta atingir esse número, a biblioteca emite warning e **existem mais matérias além do que foi coletado**. Para corpus completo, divida em `data_inicio`/`data_fim` menores (ex.: um ano por vez).
- **25 itens por página** — paginação usa parâmetro `sr` com incrementos de 25 (internamente: `sr=1, 26, 51, ...`).
- Valores de `site` fora de `{todos, online, jornal}` levantam `ValidationError`.

## Exemplo

```python
import raspe

df = raspe.folha().raspar(
    pesquisa="reforma tributária",
    site="online",
    data_inicio="2024-01-01",
    data_fim="2024-06-30",
    paginas=range(1, 6),
)
print(f"{len(df)} matérias")
print(df[["data", "titulo"]].head())
```
