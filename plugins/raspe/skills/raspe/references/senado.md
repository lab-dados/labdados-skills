# raspe.senado

## Fonte e escopo

Busca no portal do Senado Federal — `https://www6g.senado.leg.br/busca`. Retorna resultados filtrados pela coleção "Legislação Federal" (proposições e atos).

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

| Coluna | Conteúdo |
|---|---|
| `titulo` | Título do ato/proposição. |
| `link_norma` | URL direto da norma. |
| `link_detalhes` | URL com metadados de tramitação (pode ser `"NA"` se ausente). |
| `descricao` | Descrição principal (tipicamente a ementa). |
| `trecho_descricao` | Trecho adicional com contexto de busca. |
| `termo_busca` | Adicionada automaticamente. |

## Parâmetros específicos

- `ano`: filtra por ano do ato (ex.: `ano=2024`).
- `tipo_materia`: filtra por tipo — valores aceitos pelo portal (`"LEI"`, `"DEC"`, `"PLS"`, etc.). Se em dúvida, omita.

## Gotchas

- A página de resultados tem **duas estruturas possíveis** dependendo do tipo de busca: quando o primeiro parágrafo diz "Legislação", a descrição real está no segundo parágrafo. O parser já trata isso, mas explica warnings do tipo "Erro ao processar item" em casos raros de páginas com layout atípico — os itens problemáticos são pulados e o warning vai ao log.

## Exemplo

```python
import raspe

df = raspe.senado().raspar(
    pesquisa=["educação", "saúde"],
    ano=2024,
    paginas=range(1, 3),
)
print(df["termo_busca"].value_counts())
```
