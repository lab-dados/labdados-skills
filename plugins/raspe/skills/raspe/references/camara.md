# raspe.camara

## Fonte e escopo

Busca de legislacao federal no portal da Camara dos Deputados — `https://www.camara.leg.br/legislacao/busca`. Retorna proposicoes, projetos de lei e atos com ambito "Legislacao Federal" indexados pela Camara.

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

| Coluna | Conteudo |
|---|---|
| `link` | URL para a proposicao/ato. |
| `titulo` | Titulo exibido no resultado de busca. |
| `descricao` | Descricao curta da proposicao. |
| `ementa` | Situacao ou ementa resumida. |
| `termo_busca` | Adicionada automaticamente. |

## Parametros especificos

- `ano`: filtra por ano (ex.: `ano=2024`).
- `tipo_materia`: filtra por tipo. Valores aceitos pelo portal incluem `"LEI"`, `"DEC"`, `"MPV"`, `"PLP"`, `"PL"`. Quando em duvida, omita — o filtro e aplicado apenas se fornecido.

## Gotchas

- **Pre-estabelecimento de sessao**: o scraper acessa a pagina inicial (`camara.leg.br/`) antes de ir para a busca para nao ser tratado como bot. Isso ja e automatico — apenas nao instancie e descarte `raspe.camara()` repetidamente em loop.
- **10 resultados por pagina**: paginacao via `pagina` 1-based.

## Exemplo

```python
import raspe

df = raspe.camara().raspar(
    pesquisa="educacao",
    ano=2024,
    paginas=range(1, 4),
)
print(df.shape, df.columns.tolist())
# (..., 5) ['link', 'titulo', 'descricao', 'ementa', 'termo_busca']
```
