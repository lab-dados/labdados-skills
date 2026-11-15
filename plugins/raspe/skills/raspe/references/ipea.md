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

<!-- colunas-raspe:tabela:inicio (gerado por scripts/colunas_raspe.py do docs/colunas.md do raspe; nao editar a mao) -->

| Coluna | Tipo | Descrição | Exemplo |
| --- | --- | --- | --- |
| `titulo` | texto | Título da publicação. | Regras do governo brasileiro sobre serviços de telessaúde : revisão integrativa |
| `link` | texto | Endereço da publicação no portal do IPEA. | https://www.ipea.gov.br/portal/publicacao-item?id=61d484f0-c674-4e16-a421-3e7a22e842d7 |
| `autores` | texto | Autores, como o portal os lista; vazio quando o portal deixa o campo em branco. |  |
| `data` | texto | Data de publicação, como o portal a mostra: mês abreviado e ano, ou só o ano. | Jun-2015 |
| `assuntos` | texto | Assuntos, cada um uma vez, separados por vírgula. | Economia da Saúde |
| `termo_busca` | texto | Termo de busca que gerou a linha: o valor de `pesquisa` ou, numa busca com lista, o item da lista. | natjus |

<!-- colunas-raspe:tabela:fim -->

## Gotchas

- **Não há abstract na listagem** — para o texto real da publicação, acesse o `link`. Se o usuário precisar processar o conteúdo com LLM, use `titulo` + `assuntos` como proxy, ou baixe separadamente os PDFs (fora do escopo da biblioteca).
- **Paginação 1-based**, parâmetro `pagina`, 10 resultados por página.

## Exemplo

```python
import raspe

df = raspe.ipea().raspar(pesquisa="renda básica", paginas=range(1, 4))
print(df[["titulo", "data", "autores"]].head())
```
