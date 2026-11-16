# raspe.senado

## Fonte e escopo

Busca no portal do Senado Federal — `https://www6g.senado.leg.br/busca`. Retorna resultados filtrados pela coleção "Legislação Federal" (proposições e atos).

## Assinatura

```python
raspe.senado().raspar(
    pesquisa: str | list[str] = "",
    ano: int | None = None,
    tipo_materia: str = "",
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

- `pesquisa`: opcional; vazia, a busca fica só com `ano` e `tipo_materia`. É o único parâmetro que aceita lista, e a coluna `termo_busca` sai sempre, com o valor dela (vazio se não veio). Sem `pesquisa`, `ano` nem `tipo_materia`, a busca cobre toda a coleção: limite com `paginas`.
- `ano`: ano do ato, com quatro dígitos (ex.: `ano=2024`). Fora disso (`ano=0`, `ano=23`), `ValidationError` antes da busca.
- `tipo_materia`: tipo de norma no formato `"SIGLA - Nome"` do filtro da busca do Senado, como `"LEI - Lei"`. A sigla sozinha (`"LEI"`) dá zero resultados, sem erro. O formato não é o da Câmara (`"Lei Ordinária"`). Vazio, não filtra.

## Gotchas

- A página de resultados tem **duas estruturas possíveis** dependendo do tipo de busca: quando o primeiro parágrafo diz "Legislação", a descrição real está no segundo parágrafo. O parser já trata isso. Item com layout atípico é pulado, e o erro dele chega a quem chamou (veja "Tratamento de erros" na `SKILL.md`).

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
