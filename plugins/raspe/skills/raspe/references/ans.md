# raspe.ans

## Fonte e escopo

Portal ANSLegis da Agência Nacional de Saúde Suplementar — `https://anslegis.datalegis.net/`. Indexa atos normativos da ANS: Resoluções Normativas (RN), Instruções Normativas, Súmulas, Portarias e outros. Infra Datalegis compartilhada com ANVISA.

## Requisitos

**Extra `[browser]` obrigatório**, mesma instalação de `anvisa` e `saudelegis`:

```bash
pip install "raspe[browser] @ git+https://github.com/bdcdo/raspe.git"
python -m playwright install chromium
```

## Assinatura

```python
raspe.ans(
    debug: bool = True,
    headless: bool = True,
).raspar(
    pesquisa: str,
) -> pd.DataFrame
```

Sem `paginas` e sem lista em `pesquisa`. O que acontece se passá-los, o volume da coleta, a coleta de teste curta e o nome antigo do parâmetro de busca estão em `references/api.md`.

## Colunas retornadas

<!-- colunas-raspe:tabela:inicio (gerado por scripts/colunas_raspe.py do docs/colunas.md do raspe; nao editar a mao) -->

| Coluna | Tipo | Descrição | Exemplo |
| --- | --- | --- | --- |
| `url` | texto | Endereço do texto do ato, no domínio do portal do órgão. | https://anslegis.datalegis.net/acao/abrirTextoAto.php?id=12345 |
| `titulo` | texto | Tipo e número do ato. | RESOLUÇÃO NORMATIVA Nº 500/2024 |
| `descricao` | texto ou nulo | Ementa do ato, ou nulo quando o portal não a traz. | Define diretrizes para cobertura de doenças raras. |
| `situacao` | texto ou nulo | Situação do ato (vigente, revogado etc.), ou nulo quando o portal não a traz. | Em vigor |
| `termo_busca` | texto | Termo de busca que gerou a linha: o valor de `pesquisa` ou, numa busca com lista, o item da lista. | natjus |

<!-- colunas-raspe:tabela:fim -->

## Parâmetros específicos

- **`pesquisa`**: texto no campo de busca do portal. Vazia, levanta `ValidationError`.
- `headless=False` para ver o navegador (debug).
- `debug=True` mantém HTMLs brutos.

## Gotchas

- **Cloudflare**: o domínio `datalegis.net` tem bot detection. `playwright-stealth` é aplicado automaticamente pela classe base `ScraperDatalegis`. Se a stealth falhar (IP bloqueado, padrão de comportamento detectado), aparece `BrowserError: Timeout`. Veja `references/playwright.md` para diagnóstico.
- **Paginação via SELECT dropdown**: a navegação usa um `<select id="fieldPage">` com `onchange="openPage()"`. Você não interage com isso — só saiba que aparece em logs.
- **Limite de 100 páginas** (`_max_pages=100`). Coleta completa de um termo genérico pode atingir esse teto; nesse caso sai um `UserWarning`.
- **`situacao` traz o rótulo do portal** (por exemplo, `Vigente`, `Vigente com Alterações`, `Alterador` ou `Revogado`) e só vem nula quando o ato não tem rótulo. Os rótulos variam: confira os valores antes de filtrar, em vez de comparar com um rótulo só:

  ```python
  print(df["situacao"].value_counts(dropna=False))
  revogados = df[df["situacao"].str.startswith("Revogado", na=False)]
  ```

- Tempo típico: ~15-30s por página. 100 páginas = ~30-60 min.

## Exemplo

```python
import raspe

df = raspe.ans().raspar(pesquisa="doença rara")
print(df[["titulo", "situacao"]].head())
```
