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
    termo: str | list[str],
    paginas: range | None = None,
) -> pd.DataFrame
```

## Colunas retornadas

| Coluna | Conteúdo |
|---|---|
| `url` | URL absoluta para o ato. |
| `titulo` | Tipo + número + ano (ex.: "Resolução Normativa Nº 465/2021"). |
| `descricao` | Ementa/descrição do ato. |
| `situacao` | Status (ex.: "Revogado", "Revogado Tacitamente", etc.). **Vem como `None` quando o ato está vigente** — filtre com `df[df["situacao"].isna()]`. |
| `termo_busca` | Adicionada automaticamente. |

## Parâmetros específicos

- **`termo`** (não `pesquisa` ou `assunto`): texto no campo de busca do portal.
- `headless=False` para ver o navegador (debug).
- `debug=True` mantém HTMLs brutos.

## Gotchas

- **Cloudflare**: o domínio `datalegis.net` tem bot detection. `playwright-stealth` é aplicado automaticamente pela classe base `ScraperDatalegis`. Se a stealth falhar (IP bloqueado, padrão de comportamento detectado), aparece `BrowserError: Timeout`. Veja `references/playwright.md` para diagnóstico.
- **Paginação via SELECT dropdown**: a navegação usa um `<select id="fieldPage">` com `onchange="openPage()"`. Você não interage com isso — só saiba que aparece em logs.
- **Limite de 100 páginas** (`_max_pages=100`). Coleta completa de um termo genérico pode atingir esse teto.
- **Situação vigente = `None`**: não é um bug, é como a biblioteca reconhece a ausência de rótulo. Filtre explicitamente:

  ```python
  vigentes = df[df["situacao"].isna()]
  revogados = df[df["situacao"].notna()]
  ```

- Tempo típico: ~15-30s por página. 100 páginas = ~30-60 min.

## Exemplo

```python
import raspe

df = raspe.ans().raspar(termo="doença rara", paginas=range(1, 4))
print(df.columns.tolist())
# ['url', 'titulo', 'descricao', 'situacao', 'termo_busca']

# Vigentes
vigentes = df[df["situacao"].isna()]
```
