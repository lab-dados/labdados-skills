# raspe.camara

## Fonte e escopo

Busca de legislação federal no portal da Câmara dos Deputados — `https://www.camara.leg.br/legislacao/busca`. Retorna normas já publicadas, com âmbito "Legislação Federal", indexadas pela Câmara. Projetos de lei e demais proposições saem de `raspe.camara_proposicoes()`.

## Assinatura

```python
raspe.camara().raspar(
    pesquisa: str | list[str] = "",
    ano: int | None = None,
    tipo_materia: str = "",
    paginas: range | None = None,
) -> pd.DataFrame
```

## Colunas retornadas

| Coluna | Conteúdo |
|---|---|
| `link` | URL para a norma. |
| `titulo` | Título exibido no resultado de busca. |
| `descricao` | Descrição curta da norma. |
| `ementa` | Situação ou ementa resumida. |
| `termo_busca` | Adicionada automaticamente. |

## Parâmetros específicos

- `pesquisa`: opcional; vazia, a busca fica só com `ano` e `tipo_materia`. É o único parâmetro que aceita lista, e a coluna `termo_busca` sai sempre, com o valor dela (vazio se não veio). Sem `pesquisa`, `ano` nem `tipo_materia`, a busca cobre toda a coleção: limite com `paginas`.
- `ano`: ano da norma, com quatro dígitos (ex.: `ano=2024`). Fora disso (`ano=0`, `ano=23`), `ValidationError` antes da busca.
- `tipo_materia`: tipo de norma escrito por extenso, como no filtro da busca da Câmara: `"Lei Ordinária"`, `"Medida Provisória"`. Sigla (`"LEI"`, `"MPV"`) não casa e dá zero resultados, sem erro. Vazio, não filtra.

## Gotchas

- **Pré-estabelecimento de sessão**: o scraper acessa a página inicial (`camara.leg.br/`) antes de ir para a busca para não ser tratado como bot. Isso já é automático — apenas não instancie e descarte `raspe.camara()` repetidamente em loop.
- **20 resultados por página**: paginação via `pagina` 1-based. O portal só serve as 500 primeiras páginas (10.000 resultados): uma busca maior coleta só essas e emite `UserWarning`. Divida por `ano` ou `tipo_materia`.

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
