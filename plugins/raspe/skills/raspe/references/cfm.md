# raspe.cfm

## Fonte e escopo

Portal de busca de normas do Conselho Federal de Medicina e dos Conselhos Regionais de Medicina (CRMs) — `https://portal.cfm.org.br/buscar-normas-cfm-e-crm`. Cobre resoluções, pareceres, emendas, normas e decisões emitidas em âmbito federal e regional.

## Assinatura

```python
raspe.cfm().raspar(
    pesquisa: str | list[str] = "",
    uf: str = "",
    revogada: str = "",
    numero: str = "",
    ano: int | None = None,
    paginas: range | None = None,
) -> pd.DataFrame
```

O nome antigo do parâmetro de busca, `texto`, ainda é aceito com `DeprecationWarning`. `pesquisa` vazia busca só pelos demais filtros.

## Colunas retornadas

<!-- colunas-raspe:tabela:inicio (gerado por scripts/colunas_raspe.py do docs/colunas.md do raspe; nao editar a mao) -->

| Coluna | Tipo | Descrição | Exemplo |
| --- | --- | --- | --- |
| `tipo` | texto | Tipo da norma (Resolução, Parecer, Emenda, Norma ou Decisão). | Resolução |
| `uf` | texto | UF do conselho que emitiu a norma. | DF |
| `numero_ano` | texto | Número e ano da norma, como `número/ano`. | 2350/2023 |
| `situacao` | texto | Situação da norma. | Em vigor |
| `ementa` | texto | Ementa da norma. | Define diretrizes para atendimento de doenças raras no SUS. |
| `link` | texto | Endereço do texto da norma, como o portal o devolve. | /normas/2350-2023.pdf |
| `termo_busca` | texto | Termo de busca que gerou a linha: o valor de `pesquisa` ou, numa busca com lista, o item da lista. | natjus |

<!-- colunas-raspe:tabela:fim -->

## Parâmetros específicos

- `uf`: sigla da UF para filtrar CRMs (ex.: `uf="SP"`). Vazio = todos (CFM + todos os CRMs).
- `revogada`: `"1"` para incluir apenas revogadas, vazio para todas.
- `numero`: número exato da norma.
- `ano`: ano da norma, com quatro dígitos.

Por default, a busca inclui todos os 5 tipos (Resolução, Parecer, Emenda, Norma, Decisão).

## Gotchas

- **Paginação com 15 itens por página**, 1-based.
- O portal às vezes reporta "0 registros encontrados" — o scraper trata esse caso e retorna DataFrame vazio sem erro.

## Exemplo

```python
import raspe

# Todas as normas sobre "telemedicina"
df = raspe.cfm().raspar(pesquisa="telemedicina", paginas=range(1, 3))

# Só as do CRM de São Paulo
df_sp = raspe.cfm().raspar(pesquisa="telemedicina", uf="SP", paginas=range(1, 3))

# Os rótulos de situação vêm do portal: confira-os antes de filtrar
print(df["situacao"].value_counts())
```
