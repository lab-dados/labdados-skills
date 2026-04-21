# raspe.ipea

## Fonte e escopo

Central de Conteudo do IPEA (Instituto de Pesquisa Economica Aplicada) — `https://www.ipea.gov.br/portal/coluna-5/central-de-conteudo/busca-publicacoes`. Indexa textos para discussao, livros, boletins e demais publicacoes do instituto.

## Assinatura

```python
raspe.ipea().raspar(
    pesquisa: str | list[str],
    paginas: range | None = None,
) -> pd.DataFrame
```

## Colunas retornadas

| Coluna | Conteudo |
|---|---|
| `titulo` | Titulo da publicacao. |
| `link` | URL absoluta (ja prefixada com `https://www.ipea.gov.br`). |
| `autores` | String com autores. |
| `data` | Data ou periodo de publicacao. |
| `assuntos` | Assuntos/tags classificadas pelo IPEA. |
| `termo_busca` | Adicionada automaticamente. |

## Gotchas

- **Nao ha abstract na listagem** — para o texto real da publicacao, acesse o `link`. Se o usuario precisar processar o conteudo com LLM, use `titulo` + `assuntos` como proxy, ou baixe separadamente os PDFs (fora do escopo da biblioteca).
- **Paginacao 1-based**, parametro `pagina`, 10 resultados por pagina.

## Exemplo

```python
import raspe

df = raspe.ipea().raspar(pesquisa="renda basica", paginas=range(1, 4))
print(df[["titulo", "data", "autores"]].head())
```
