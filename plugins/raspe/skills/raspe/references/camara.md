# raspe.camara

## Fonte e escopo

Busca de legislação federal no portal da Câmara dos Deputados — `https://www.camara.leg.br/legislacao/busca`. Retorna proposições, projetos de lei e atos com âmbito "Legislação Federal" indexados pela Câmara.

## Assinatura

```python
raspe.camara().raspar(
    pesquisa: str | list[str],
    ano: int | None = None,
    tipo_materia: str | None = None,
    paginas: range | None = None,
) -> pd.DataFrame
```

## Colunas retornadas

| Coluna | Conteúdo |
|---|---|
| `link` | URL para a proposição/ato. |
| `titulo` | Título exibido no resultado de busca. |
| `descricao` | Descrição curta da proposição. |
| `ementa` | Situação ou ementa resumida. |
| `termo_busca` | Adicionada automaticamente. |

## Parâmetros específicos

- `ano`: filtra por ano (ex.: `ano=2024`).
- `tipo_materia`: filtra por tipo. Valores aceitos pelo portal incluem `"LEI"`, `"DEC"`, `"MPV"`, `"PLP"`, `"PL"`. Quando em dúvida, omita — o filtro é aplicado apenas se fornecido.

## Gotchas

- **Pré-estabelecimento de sessão**: o scraper acessa a página inicial (`camara.leg.br/`) antes de ir para a busca para não ser tratado como bot. Isso já é automático — apenas não instancie e descarte `raspe.camara()` repetidamente em loop.
- **10 resultados por página**: paginação via `pagina` 1-based.

## Exemplo

```python
import raspe

df = raspe.camara().raspar(
    pesquisa="educação",
    ano=2024,
    paginas=range(1, 4),
)
print(df.shape, df.columns.tolist())
# (..., 5) ['link', 'titulo', 'descricao', 'ementa', 'termo_busca']
```
