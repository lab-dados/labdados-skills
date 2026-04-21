# raspe.presidencia

## Fonte e escopo

Portal da Legislacao da Presidencia da Republica — `https://legislacao.presidencia.gov.br/`. Cobre leis ordinarias, leis complementares, decretos, medidas provisorias e outros atos da chefia do executivo federal.

## Assinatura

```python
raspe.presidencia().raspar(
    pesquisa: str | list[str],
    paginas: range | None = None,
) -> pd.DataFrame
```

## Colunas retornadas

| Coluna | Conteudo |
|---|---|
| `nome` | Tipo e numero do ato (ex.: "Lei nº 14.437, de 2022"). |
| `link` | URL do ato completo. |
| `ficha` | URL da ficha de tramitacao. |
| `revogacao` | Texto com informacao de revogacao (ou vazio). |
| `descricao` | Ementa/descricao do ato. |
| `termo_busca` | Adicionada automaticamente pela biblioteca. |

## Gotchas

- **Certificado SSL incompleto**: o servidor da Presidencia tem cadeia SSL quebrada. A biblioteca desabilita verificacao SSL **apenas para esta sessao** (`session.verify = False`) e suprime o warning do urllib3. Nao altere esse comportamento — e workaround necessario. Nao afeta outras fontes.
- **Metodo HTTP e POST**: diferente das outras fontes HTTP, que usam GET.
- **10 resultados por pagina**: paginacao interna usa parametro `posicao` em multiplos de 10.

## Exemplo

```python
import raspe

df = raspe.presidencia().raspar(pesquisa="meio ambiente", paginas=range(1, 4))
print(df.columns.tolist())
# ['nome', 'link', 'ficha', 'revogacao', 'descricao', 'termo_busca']

# Multiplos temas
df = raspe.presidencia().raspar(pesquisa=["saude", "educacao"])
```
