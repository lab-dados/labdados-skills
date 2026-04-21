# raspe.senado

## Fonte e escopo

Busca no portal do Senado Federal — `https://www6g.senado.leg.br/busca`. Retorna resultados filtrados pela colecao "Legislacao Federal" (proposicoes e atos).

## Assinatura

```python
raspe.senado().raspar(
    pesquisa: str | list[str],
    ano: int | None = None,
    tipo_materia: str | None = None,
    paginas: range | None = None,
) -> pd.DataFrame
```

## Colunas retornadas

| Coluna | Conteudo |
|---|---|
| `titulo` | Titulo do ato/proposicao. |
| `link_norma` | URL direto da norma. |
| `link_detalhes` | URL com metadados de tramitacao (pode ser `"NA"` se ausente). |
| `descricao` | Descricao principal (tipicamente a ementa). |
| `trecho_descricao` | Trecho adicional com contexto de busca. |
| `termo_busca` | Adicionada automaticamente. |

## Parametros especificos

- `ano`: filtra por ano do ato (ex.: `ano=2024`).
- `tipo_materia`: filtra por tipo — valores aceitos pelo portal (`"LEI"`, `"DEC"`, `"PLS"`, etc.). Se em duvida, omita.

## Gotchas

- A pagina de resultados tem **duas estruturas possiveis** dependendo do tipo de busca: quando o primeiro paragrafo diz "Legislacao", a descricao real esta no segundo paragrafo. O parser ja trata isso, mas explica warnings do tipo "Erro ao processar item" em casos raros de paginas com layout atipico — os itens problematicos sao pulados e o warning vai ao log.

## Exemplo

```python
import raspe

df = raspe.senado().raspar(
    pesquisa=["educacao", "saude"],
    ano=2024,
    paginas=range(1, 3),
)
print(df["termo_busca"].value_counts())
```
