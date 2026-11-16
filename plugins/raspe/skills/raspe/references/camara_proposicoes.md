# raspe.camara_proposicoes

## Fonte e escopo

Proposições da Câmara dos Deputados pela API oficial de Dados Abertos — `https://dadosabertos.camara.leg.br/api/v2/proposicoes`. Lista projetos de lei, PECs, requerimentos e demais proposições, tenham virado norma ou não. Para a legislação já publicada, a fonte é outra: `raspe.camara()` (veja `references/camara.md`).

## Assinatura

```python
raspe.camara_proposicoes().raspar(
    pesquisa: str | list[str] = "",
    ano: int | None = None,
    sigla_tipo: str = "",
    data_inicio: str | None = None,
    data_fim: str | None = None,
    paginas: range | None = None,
) -> pd.DataFrame
```

A busca precisa de `pesquisa` ou de um filtro de tempo (`ano`, `data_inicio` ou `data_fim`).

## Colunas retornadas

<!-- colunas-raspe:tabela:inicio (gerado por scripts/colunas_raspe.py do docs/colunas.md do raspe; nao editar a mao) -->

| Coluna | Tipo | Descrição | Exemplo |
| --- | --- | --- | --- |
| `id` | inteiro | Identificador da proposição na Câmara. | 2239462 |
| `uri` | texto | Endereço da proposição na API, que devolve os detalhes dela. | https://dadosabertos.camara.leg.br/api/v2/proposicoes/2239462 |
| `sigla_tipo` | texto | Sigla do tipo de proposição. | PL |
| `cod_tipo` | inteiro | Código numérico do tipo de proposição. | 139 |
| `numero` | inteiro | Número da proposição. | 696 |
| `ano` | inteiro | Ano da identificação da proposição, que pode diferir do ano de `data_apresentacao`. | 2020 |
| `ementa` | texto | Ementa da proposição. | Dispõe sobre o uso da telemedicina durante a crise causada pelo coronavírus |
| `data_apresentacao` | texto | Data e hora de apresentação, em ISO 8601 sem fuso, como a API devolve. | 2020-03-18T10:54 |
| `termo_busca` | texto | Termo de busca que gerou a linha: o valor de `pesquisa` ou, numa busca com lista, o item da lista. | natjus |

<!-- colunas-raspe:tabela:fim -->

## Parâmetros específicos

- `pesquisa`: termo procurado nas proposições. É o único parâmetro que aceita lista. Vazia, a busca fica só com os demais filtros e exige um filtro de tempo.
- `ano`: ano da identificação da proposição (o 2020 de PL 696/2020), com quatro dígitos. Pode não ser o ano de apresentação, que se filtra com `data_inicio` e `data_fim`.
- `sigla_tipo`: sigla do tipo de proposição, como a Câmara a escreve (`"PL"`, `"PEC"`). Vazio, não filtra. O filtro não é o `tipo_materia` de `raspe.camara()`, que aqui levanta `ValidationError`.
- `data_inicio`, `data_fim`: período da data de apresentação, em `YYYY-MM-DD`, `DD/MM/YYYY` ou `YYYYMMDD`.
- `paginas`: 100 proposições por página, 1-based. Não é aceito na busca dividida por período (veja abaixo).

## Gotchas

- **Sem filtro de tempo, a busca cobre a base inteira.** A API sozinha só devolveria os últimos 30 dias; o raspe pede a base inteira quando não vêm `ano`, `data_inicio` nem `data_fim`. Isso só funciona com `pesquisa`: sem termo e sem filtro de tempo, `ValidationError` antes da busca (a API não responde a tempo).
- **Período de mais de 3 meses é dividido.** A API recusa `data_inicio` e `data_fim` a mais de 3 meses uma da outra. O raspe divide o período em janelas de até 3 meses e junta as proposições sem repetir, em ordem de `id`. Com `pesquisa`, ele tenta antes uma consulta só com `data_inicio` e tira o que foi apresentado depois de `data_fim`, o que costuma sair em 1 a 3 requisições. Sem `pesquisa`, vai uma consulta por janela: um período de anos leva dezenas de requisições.
- **`paginas` na busca dividida levanta `ValidationError`**: cada janela tem a própria paginação. Tire `paginas` ou encurte o período. Uma data só, ou `ano`, não tem o limite de 3 meses e aceita `paginas`.
- **`ementa` é o único texto.** A API de listagem não traz autor, situação nem inteiro teor; `uri` aponta para o endereço da API que devolve os detalhes da proposição.
- `data_apresentacao` vem como texto, com hora (`2020-03-18T10:54`). Converta com `pd.to_datetime` antes de ordenar ou filtrar por data.

## Exemplo

```python
import raspe

# Projetos de lei de 2020 sobre telemedicina
df = raspe.camara_proposicoes().raspar(pesquisa="telemedicina", ano=2020, sigla_tipo="PL")
print(df[["sigla_tipo", "numero", "ano", "ementa"]].head())

# Tudo o que foi apresentado sobre o tema em dois anos (busca dividida: sem `paginas`)
df = raspe.camara_proposicoes().raspar(
    pesquisa="telemedicina",
    data_inicio="2020-01-01",
    data_fim="2021-12-31",
)
print(df["sigla_tipo"].value_counts())
```

## Recomendação para dataframeit

`text_column = "ementa"`
