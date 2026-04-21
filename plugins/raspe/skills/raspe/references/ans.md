# raspe.ans

## Fonte e escopo

Portal ANSLegis da Agencia Nacional de Saude Suplementar — `https://anslegis.datalegis.net/`. Indexa atos normativos da ANS: Resolucoes Normativas (RN), Instrucoes Normativas, Sumulas, Portarias e outros. Infra Datalegis compartilhada com ANVISA.

## Requisitos

**Extra `[browser]` obrigatorio**, mesma instalacao de `anvisa` e `saudelegis`:

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
    termo: str | list[str],
    paginas: range | None = None,
) -> pd.DataFrame
```

## Colunas retornadas

| Coluna | Conteudo |
|---|---|
| `url` | URL absoluta para o ato. |
| `titulo` | Tipo + numero + ano (ex.: "Resolucao Normativa Nº 465/2021"). |
| `descricao` | Ementa/descricao do ato. |
| `situacao` | Status (ex.: "Revogado", "Revogado Tacitamente", etc.). **Vem como `None` quando o ato esta vigente** — filtre com `df[df["situacao"].isna()]`. |
| `termo_busca` | Adicionada automaticamente. |

## Parametros especificos

- **`termo`** (nao `pesquisa` ou `assunto`): texto no campo de busca do portal.
- `headless=False` para ver o navegador (debug).
- `debug=True` mantem HTMLs brutos.

## Gotchas

- **Cloudflare**: o dominio `datalegis.net` tem bot detection. `playwright-stealth` e aplicado automaticamente pela classe base `ScraperDatalegis`. Se a stealth falhar (IP bloqueado, padrao de comportamento detectado), aparece `BrowserError: Timeout`. Veja `references/playwright.md` para diagnostico.
- **Paginacao via SELECT dropdown**: a navegacao usa um `<select id="fieldPage">` com `onchange="openPage()"`. Voce nao interage com isso — so saiba que aparece em logs.
- **Limite de 100 paginas** (`_max_pages=100`). Coleta completa de um termo generico pode atingir esse teto.
- **Situacao vigente = `None`**: nao e um bug, e como a biblioteca reconhece a ausencia de rotulo. Filtre explicitamente:

  ```python
  vigentes = df[df["situacao"].isna()]
  revogados = df[df["situacao"].notna()]
  ```

- Tempo tipico: ~15-30s por pagina. 100 paginas = ~30-60 min.

## Exemplo

```python
import raspe

df = raspe.ans().raspar(termo="doenca rara", paginas=range(1, 4))
print(df.columns.tolist())
# ['url', 'titulo', 'descricao', 'situacao', 'termo_busca']

# Vigentes
vigentes = df[df["situacao"].isna()]
```
