# raspe.ipea

## Fonte e escopo

Central de Conteúdo do IPEA (Instituto de Pesquisa Econômica Aplicada) — `https://www.ipea.gov.br/portal/coluna-5/central-de-conteudo/busca-publicacoes`. Indexa textos para discussão, livros, boletins e demais publicações do instituto.

## Assinatura

```python
raspe.ipea().raspar(
    pesquisa: str | list[str],
    paginas: range | None = None,
) -> pd.DataFrame
```

## Colunas retornadas

| Coluna | Conteúdo |
|---|---|
| `titulo` | Título da publicação. |
| `link` | URL absoluta (já prefixada com `https://www.ipea.gov.br`). |
| `autores` | String com autores. |
| `data` | Data ou período de publicação. |
| `assuntos` | Assuntos/tags classificadas pelo IPEA. |
| `termo_busca` | Adicionada automaticamente. |

## Gotchas

- **Não há abstract na listagem** — para o texto real da publicação, acesse o `link`. Se o usuário precisar processar o conteúdo com LLM, use `titulo` + `assuntos` como proxy, ou baixe separadamente os PDFs (fora do escopo da biblioteca).
- **Paginação 1-based**, parâmetro `pagina`, 10 resultados por página.

## Exemplo

```python
import raspe

df = raspe.ipea().raspar(pesquisa="renda básica", paginas=range(1, 4))
print(df[["titulo", "data", "autores"]].head())
```
