# raspe.folha

## Fonte e escopo

Busca de noticias da Folha de Sao Paulo — `https://search.folha.uol.com.br/search`. Cobre materias online e do jornal impresso.

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

| Coluna | Conteudo |
|---|---|
| `link` | URL da materia. |
| `titulo` | Titulo da reportagem. |
| `resumo` | Lead/resumo. |
| `data` | Data de publicacao (formato amigavel — varia por materia). |
| `termo_busca` | Adicionada automaticamente. |

## Parametros especificos

- `site`:
  - `"todos"` (default) — online + jornal impresso.
  - `"online"` — so o site Folha.com.
  - `"jornal"` — so materias do jornal impresso. Util para retrospectiva historica.
- `data_inicio`/`data_fim`: `YYYY-MM-DD`, `DD/MM/YYYY` ou `YYYYMMDD`. A biblioteca converte internamente para o formato `DD/MM/YYYY` que a API da Folha exige.

## Gotchas

- **Teto de 10.000 resultados (400 paginas)** — limitacao do motor de busca da Folha. Se a coleta atingir esse numero, a biblioteca emite warning e **existem mais materias alem do que foi coletado**. Para corpus completo, divida em `data_inicio`/`data_fim` menores (ex.: um ano por vez).
- **25 itens por pagina** — paginacao usa parametro `sr` com incrementos de 25 (internamente: `sr=1, 26, 51, ...`).
- Valores de `site` fora de `{todos, online, jornal}` levantam `ValidationError`.

## Exemplo

```python
import raspe

df = raspe.folha().raspar(
    pesquisa="reforma tributaria",
    site="online",
    data_inicio="2024-01-01",
    data_fim="2024-06-30",
    paginas=range(1, 6),
)
print(f"{len(df)} materias")
print(df[["data", "titulo"]].head())
```
