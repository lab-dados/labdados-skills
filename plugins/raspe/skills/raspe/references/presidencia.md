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

<!-- colunas-raspe:tabela:inicio (gerado por scripts/colunas_raspe.py do docs/colunas.md do raspe; nao editar a mao) -->

| Coluna | Tipo | Descrição | Exemplo |
| --- | --- | --- | --- |
| `nome` | texto | Nome do ato, com tipo, número e ano. | Decreto nº 12.725 de 18 de novembro de 2025 |
| `link` | texto | Endereço do texto do ato, como o portal o devolve. | https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/decreto/d12725.htm |
| `ficha` | texto | Endereço da ficha do ato, do botão "Ficha"; vazio, com `UserWarning`, se o card não o traz. | https://legislacao.presidencia.gov.br/atos?tipo=DEC&numero=12725&ano=2025&data=18/11/2025&ato=499cXVU9UNZpWT45a |
| `revogacao` | texto | Situação de revogação informada pelo portal. | Não consta revogação expressa |
| `descricao` | texto | Ementa do ato. | Aprova a Política Nacional de Defesa, a Estratégia Nacional de Defesa e o Livro Branco de Defesa Nacional. |
| `rotulo` | texto | Selo que o portal põe ao lado do nome, como "Veto Parcial"; vazio quando não há. | Veto Parcial |
| `termo_busca` | texto | Termo de busca que gerou a linha: o valor de `pesquisa` ou, numa busca com lista, o item da lista. | natjus |

<!-- colunas-raspe:tabela:fim -->

## Gotchas

- **Certificado SSL incompleto**: o servidor da Presidência tem cadeia SSL quebrada. A biblioteca desabilita verificação SSL **apenas para esta sessão** (`session.verify = False`) e suprime o warning do urllib3. Não altere esse comportamento — é workaround necessário. Não afeta outras fontes.
- **Método HTTP é POST**: diferente das outras fontes HTTP, que usam GET.
- **10 resultados por página**: paginação interna usa parâmetro `posicao` em múltiplos de 10.

## Exemplo

```python
import raspe

df = raspe.presidencia().raspar(pesquisa="meio ambiente", paginas=range(1, 4))
print(df.columns.tolist())
# ['nome', 'link', 'ficha', 'revogacao', 'descricao', 'rotulo', 'termo_busca']

# Múltiplos temas
df = raspe.presidencia().raspar(pesquisa=["saúde", "educação"])
```
