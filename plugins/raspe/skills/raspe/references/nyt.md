# raspe.nyt

## Fonte e escopo

Article Search API oficial do New York Times — `https://api.nytimes.com/svc/search/v2/articlesearch.json`. Retorna metadados de artigos (título, URL, seção, autor, resumo, imagem). **Não retorna texto integral** — para o texto, siga o `url` retornado.

## Assinatura

```python
raspe.nyt(api_key: str | None = None).raspar(
    texto: str | list[str],
    ano: int | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    sort: Literal["best", "newest", "oldest", "relevance"] = "newest",
    filtro: str = "",
    paginas: range | None = None,
) -> pd.DataFrame
```

## API key

Obrigatória. Obtenção gratuita:

1. Cadastre em <https://developer.nytimes.com/get-started>.
2. Crie um app e **ative "Article Search API"**.
3. Copie a key.

Passe de duas formas:

```python
# Explícita no construtor
nyt = raspe.nyt(api_key="sua-chave")

# Ou via env (mais seguro — não vaza em logs/notebooks commitados)
import os
os.environ["NYT_API_KEY"] = "sua-chave"
nyt = raspe.nyt()  # lê NYT_API_KEY automaticamente
```

Sem chave: `APIKeyError` com o passo a passo no corpo da mensagem.

Se a chave for inválida/expirada, a primeira requisição devolve 401 e a biblioteca levanta `APIKeyError` apontando para `https://developer.nytimes.com/my-apps`.

## Colunas retornadas

| Coluna | Conteúdo |
|---|---|
| `titulo` | Título principal do artigo. |
| `url` | URL canônica no NYT. |
| `data_publicacao` | ISO timestamp (`pub_date`). |
| `secao` | Nome da seção (`section_name`). |
| `desk` | "Desk" editorial. |
| `tipo` | Tipo de material (`News`, `Op-Ed`, etc.). |
| `resumo` | Snippet curto. |
| `autor` | Byline completo. |
| `palavras` | Word count do artigo. |
| `imagem_url` | URL de imagem (prioriza tamanhos maiores). |
| `termo_busca` | Adicionada automaticamente. |

## Parâmetros específicos

- **`texto`** (não `pesquisa`): termo de busca. Aceita operadores simples ("Brazil election").
- **`ano`**: atalho que seta `data_inicio=YYYY-01-01` e `data_fim=YYYY-12-31` automaticamente.
- **`data_inicio`/`data_fim`**: aceitam `YYYY-MM-DD` etc. A API interna usa `YYYYMMDD` — a biblioteca converte.
- **`sort`**:
  - `"newest"` (default).
  - `"oldest"`.
  - `"best"` / `"relevance"`.
- **`filtro`**: sintaxe Lucene para `fq`. Exemplos:
  - `filtro='section.name:"Politics"'` — só seção Politics.
  - `filtro='glocations:"Brazil"'` — matérias geotagueadas com Brasil.
  - `filtro='type_of_material:"Op-Ed"'` — só Op-Eds.
  - Combinações: `filtro='section.name:"Business" AND glocations:"Brazil"'`.

## Rate limits — **ATENÇÃO**

A API tem limites rigorosos:

- **5 requisições por minuto**.
- **500 requisições por dia**.
- **10 resultados por página**.
- **Máximo 100 páginas (1000 resultados) por busca**.

A biblioteca **já aplica `sleep_time=12s`** automaticamente entre requisições para respeitar o limite de 5/min. Não reduza.

Se um termo retornar >1000 resultados potenciais, o scraper coleta até 1000 e para. Para pegar mais, **divida por intervalos de datas**:

```python
# Para coletar "Brazil" em 2024 inteiro, divida em trimestres
for q in [("2024-01-01","2024-03-31"), ("2024-04-01","2024-06-30"),
          ("2024-07-01","2024-09-30"), ("2024-10-01","2024-12-31")]:
    df_q = raspe.nyt().raspar(texto="Brazil", data_inicio=q[0], data_fim=q[1])
    ...
```

## Gotchas

- **A chave `texto` é em inglês** — a API é em inglês. Para assuntos brasileiros, use termos como "Brazil", "Bolsonaro", "Lula", "Amazon rainforest".
- **Página 0-based internamente** — a biblioteca normaliza para 1-based, então você passa `paginas=range(1, 6)` normalmente.
- **`multimedia` mudou de formato**: versões antigas do NYT retornavam estrutura diferente. A biblioteca trata o formato atual (objetos com `url`, `subtype`); se o NYT mudar de novo, o campo `imagem_url` pode vir vazio sem erro.

## Exemplo

```python
import os, raspe
os.environ["NYT_API_KEY"] = "..."

df = raspe.nyt().raspar(
    texto="Brazil tax reform",
    data_inicio="2024-01-01",
    data_fim="2024-06-30",
    filtro='section.name:"Business"',
    paginas=range(1, 4),
)
print(df[["data_publicacao", "titulo", "secao"]].head())
```
