# raspe.presidencia

## Fonte e escopo

Portal da Legislação da Presidência da República — `https://legislacao.presidencia.gov.br/`. Cobre leis ordinárias, leis complementares, decretos, medidas provisórias e outros atos da chefia do executivo federal.

## Assinatura

```python
raspe.presidencia().raspar(
    pesquisa: str | list[str],
    paginas: range | None = None,
) -> pd.DataFrame
```

## Colunas retornadas

| Coluna | Conteúdo |
|---|---|
| `nome` | Tipo e número do ato (ex.: "Lei nº 14.437, de 2022"). |
| `link` | URL do ato completo. |
| `ficha` | URL da ficha de tramitação. |
| `revogacao` | Texto com informação de revogação (ou vazio). |
| `descricao` | Ementa/descrição do ato. |
| `termo_busca` | Adicionada automaticamente pela biblioteca. |

## Gotchas

- **Certificado SSL incompleto**: o servidor da Presidência tem cadeia SSL quebrada. A biblioteca desabilita verificação SSL **apenas para esta sessão** (`session.verify = False`) e suprime o warning do urllib3. Não altere esse comportamento — é workaround necessário. Não afeta outras fontes.
- **Método HTTP é POST**: diferente das outras fontes HTTP, que usam GET.
- **10 resultados por página**: paginação interna usa parâmetro `posicao` em múltiplos de 10.

## Exemplo

```python
import raspe

df = raspe.presidencia().raspar(pesquisa="meio ambiente", paginas=range(1, 4))
print(df.columns.tolist())
# ['nome', 'link', 'ficha', 'revogacao', 'descricao', 'termo_busca']

# Múltiplos temas
df = raspe.presidencia().raspar(pesquisa=["saúde", "educação"])
```
