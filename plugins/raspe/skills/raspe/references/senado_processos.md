# raspe.senado_processos

## Fonte e escopo

Processos legislativos do Senado Federal pela API oficial de Dados Abertos — `https://legis.senado.leg.br/dadosabertos/processo`. Lista projetos de lei, PECs, requerimentos e demais processos do Senado e do Congresso Nacional, tenham virado norma ou não. Para a legislação já publicada, a fonte é outra: `raspe.senado()` (veja `references/senado.md`).

## Assinatura

```python
raspe.senado_processos().raspar(
    pesquisa: str | list[str] = "",
    ano: int | None = None,
    sigla_tipo: str = "",
    data_inicio: str | None = None,
    data_fim: str | None = None,
    paginas: range | None = None,
) -> pd.DataFrame
```

A busca precisa de `ano` ou de `data_inicio`.

## Colunas retornadas

<!-- colunas-raspe:tabela:inicio (gerado por scripts/colunas_raspe.py do docs/colunas.md do raspe; nao editar a mao) -->

| Coluna | Tipo | Descrição | Exemplo |
| --- | --- | --- | --- |
| `id` | inteiro | Identificador do processo no Senado. | 7879650 |
| `codigo_materia` | inteiro | Código da matéria no sistema anterior do Senado (MATE). | 141263 |
| `identificacao` | texto | Sigla, número e ano do processo. | PL 696/2020 |
| `apelido` | texto ou nulo | Nome pelo qual o processo ficou conhecido, ou nulo. | Marco Legal da Inteligência Artificial |
| `ementa` | texto | Ementa do processo. | Dispõe sobre o uso da telemedicina durante a crise causada pelo coronavírus |
| `tipo_documento` | texto | Tipo do documento que iniciou o processo. | Projeto de Lei Ordinária |
| `tipo_conteudo` | texto | Tipo de conteúdo do documento inicial. | Norma Geral |
| `autoria` | texto | Autor ou autores do processo. | Câmara dos Deputados |
| `objetivo` | texto ou nulo | Papel do Senado no processo (como iniciadora ou revisora), ou nulo. | Revisora |
| `casa_identificadora` | texto | Casa que identifica o processo: `SF` (Senado Federal) ou `CN` (Congresso Nacional). | SF |
| `ente_identificador` | texto | Sigla do ente (casa, comissão ou colegiado) que identifica o processo. | SF |
| `data_apresentacao` | texto | Data de apresentação, em AAAA-MM-DD. | 2020-03-26 |
| `tramitando` | texto | Se o processo ainda tramita: `Sim` ou `Não`, como a API devolve. | Não |
| `situacao_atual` | texto ou nulo | Situação atual do processo, ou nulo. | TRANSFORMADA EM NORMA JURÍDICA COM VETO PARCIAL |
| `data_situacao_atual` | texto ou nulo | Data da situação atual, em AAAA-MM-DD, ou nulo. | 2020-04-16 |
| `data_deliberacao` | texto ou nulo | Data da deliberação, em AAAA-MM-DD, ou nulo quando ainda não houve. | 2020-03-31 |
| `sigla_tipo_deliberacao` | texto ou nulo | Sigla do tipo de deliberação, ou nulo quando ainda não houve. | APROVADA_NO_PLENARIO |
| `norma_gerada` | texto ou nulo | Norma em que o processo se transformou, ou nulo. | Lei nº 13.989 de 15/04/2020 |
| `ultima_informacao_atualizada` | texto ou nulo | Tipo da última informação atualizada no processo, ou nulo. | EVENTO_LEGISLATIVO |
| `data_ultima_atualizacao` | texto ou nulo | Data e hora da última atualização, em ISO 8601 sem fuso, ou nulo. | 2026-07-01T09:07:06.075 |
| `url_documento` | texto ou nulo | Endereço do documento inicial do processo, ou nulo. | https://legis.senado.gov.br/sdleg-getter/dadosabertos/documento/aeb2ac05-c25d-40bb-ba82-710cef32ae5c |
| `termo_busca` | texto | Termo de busca que gerou a linha: o valor de `pesquisa` ou, numa busca com lista, o item da lista. | natjus |

<!-- colunas-raspe:tabela:fim -->

## Parâmetros específicos

- `pesquisa`: termo procurado nas palavras-chave do processo. É o único parâmetro que aceita lista. Vazia, a busca fica só com os demais filtros.
- `ano`: ano da identificação do processo (o 2020 de PL 696/2020), com quatro dígitos. Pode não ser o ano de apresentação, que se filtra com `data_inicio` e `data_fim`.
- `sigla_tipo`: sigla da identificação do processo, como o Senado a escreve (`"PL"`, `"PEC"`). Vazio, não filtra. O filtro não é o `tipo_materia` de `raspe.senado()`, que aqui levanta `ValidationError`.
- `data_inicio`, `data_fim`: período da data de apresentação, em `YYYY-MM-DD`, `DD/MM/YYYY` ou `YYYYMMDD`.
- `paginas`: só existe por paridade com as outras fontes. A API devolve cada consulta inteira, sem paginação: `range(1, 2)` ou nenhum valor baixam tudo.

## Gotchas

- **Sem `ano` e sem `data_inicio`, `ValidationError` antes da busca.** Só com `pesquisa`, a API devolveria apenas os processos que ainda tramitam, e só com `data_fim`, apenas os do ano anterior a ela. `data_inicio` no futuro, sem `data_fim`, também é recusada.
- **Sem `ano`, o período é dividido em janelas de até um ano**, de `data_inicio` até `data_fim` ou, sem ela, até hoje. O raspe faz uma consulta por janela e junta os processos sem repetir. Com `ano`, a busca sai numa consulta só.
- **Não há como limitar o volume por `paginas`.** Um ano inteiro sem `pesquisa` traz uns 5.500 processos numa resposta de quase 5 MB. Para uma coleta de teste, use `pesquisa`, `sigla_tipo` ou um período curto.
- **Colunas "ou nulo" vêm vazias em parte dos processos** (`apelido`, `objetivo`, `situacao_atual`, `norma_gerada`, `url_documento` e as de deliberação e atualização): a API só manda esses campos quando existem. Use `df["norma_gerada"].notna()` para achar os que viraram norma.
- `tramitando` é texto (`"Sim"` ou `"Não"`), não booleano.

## Exemplo

```python
import raspe

# Processos de 2020 sobre telemedicina
df = raspe.senado_processos().raspar(pesquisa="telemedicina", ano=2020)
print(df[["identificacao", "ementa", "situacao_atual"]].head())

# Tudo o que foi apresentado sobre o tema em dois anos (duas consultas, uma por ano)
df = raspe.senado_processos().raspar(
    pesquisa="inteligência artificial",
    data_inicio="2023-01-01",
    data_fim="2024-12-31",
)
print(df["tramitando"].value_counts())
```

## Recomendação para dataframeit

`text_column = "ementa"`
