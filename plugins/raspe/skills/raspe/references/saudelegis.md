# raspe.saudelegis

## Fonte e escopo

Portal SaudeLegis do Ministerio da Saude — `https://saudelegis.saude.gov.br/saudelegis/secure/norma/listPublic.xhtml`. Indexa portarias, resolucoes e demais normas sanitarias do MS e orgaos vinculados.

## Requisitos

**Extra `[browser]` obrigatorio**. Sem ele, o construtor levanta `DriverNotInstalledError`:

```bash
pip install "raspe[browser] @ git+https://github.com/bdcdo/raspe.git"
python -m playwright install chromium
```

## Assinatura

```python
raspe.saudelegis(
    debug: bool = True,
    headless: bool = True,
).raspar(
    assunto: str | list[str],
    paginas: range | None = None,
) -> pd.DataFrame
```

## Colunas retornadas

| Coluna | Conteudo |
|---|---|
| `tipo_norma` | Tipo (Portaria, Resolucao, Instrucao Normativa, etc.). |
| `numero` | Numero da norma. |
| `data_pub` | Data de publicacao. |
| `origem` | Orgao emissor. |
| `ementa` | Ementa da norma. |
| `link_url` | URL para o texto completo. |
| `termo_busca` | Adicionada automaticamente. |

## Parametros especificos

- **`assunto`** (nao `pesquisa` ou `termo`): texto digitado no campo de busca do portal.
- `headless=False` para ver o navegador durante a coleta (debug).
- `debug=True` mantem HTMLs brutos baixados — util se precisar inspecionar o conteudo.

## Gotchas

- **JavaScript obrigatorio**: o portal usa PrimeFaces (`form:...`), impossivel raspar com `requests`. Por isso Playwright.
- **Sem Cloudflare**: diferente de ANS/ANVISA. Playwright basico (sem stealth) ja funciona.
- **Limite de 50 paginas** (`_max_pages=50`). Suficiente para a maioria das buscas tematicas.
- **Paginacao por links numerados** — estrategia `NUMBERED_LINKS`.
- Tempo de execucao tipico: ~10-20s por pagina. Planeje accordingly.

## Exemplo

```python
import raspe

df = raspe.saudelegis().raspar(assunto="doenca rara", paginas=range(1, 4))
print(df[["tipo_norma", "numero", "data_pub", "ementa"]].head())
```

Para debug visual:

```python
df = raspe.saudelegis(headless=False).raspar(assunto="doenca rara", paginas=range(1, 2))
```
