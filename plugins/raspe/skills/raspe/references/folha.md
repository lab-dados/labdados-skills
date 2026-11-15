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

<!-- colunas-raspe:tabela:inicio (gerado por scripts/colunas_raspe.py do docs/colunas.md do raspe; nao editar a mao) -->

| Coluna | Tipo | Descrição | Exemplo |
| --- | --- | --- | --- |
| `link` | texto | Endereço da notícia. | https://www1.folha.uol.com.br/equilibrioesaude/2026/08/anvisa-aprova-novo-remedio-para-distrofia-muscular-de-duchenne.shtml |
| `titulo` | texto | Título da notícia. | Anvisa aprova novo remédio para distrofia muscular de Duchenne |
| `resumo` | texto | Resumo que a busca mostra abaixo do título. | Em 2024, a Anvisa também aprovou o Elevidys, uma terapia gênica para o tratamento da distrofia muscular de Duchenne. ... |
| `data` | texto | Data e hora de publicação, como a busca as mostra. | 13.ago.2026 às 14h20 |
| `termo_busca` | texto | Termo de busca que gerou a linha: o valor de `pesquisa` ou, numa busca com lista, o item da lista. | natjus |

<!-- colunas-raspe:tabela:fim -->

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
