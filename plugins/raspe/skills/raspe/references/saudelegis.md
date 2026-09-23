# raspe.saudelegis

## Fonte e escopo

Portal SaudeLegis do Ministério da Saúde — `https://saudelegis.saude.gov.br/saudelegis/secure/norma/listPublic.xhtml`. Indexa portarias, resoluções e demais normas sanitárias do MS e órgãos vinculados.

## Requisitos

**Extra `[browser]` obrigatório**. Sem ele, `.raspar()` levanta `DriverNotInstalledError` (o construtor funciona, porque o import do Playwright é preguiçoso):

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
    assunto: str,
) -> pd.DataFrame
```

Não aceita lista nem `paginas` (ignorado sem erro). O volume é todas as páginas que o site informa, até `_max_pages`; para uma coleta de teste curta, veja `references/api.md`.

## Colunas retornadas

| Coluna | Conteúdo |
|---|---|
| `tipo_norma` | Tipo (Portaria, Resolução, Instrução Normativa, etc.). |
| `numero` | Número da norma. |
| `data_pub` | Data de publicação. |
| `origem` | Órgão emissor. |
| `ementa` | Ementa da norma. |
| `link_url` | URL para o texto completo. |
| `termo_busca` | Adicionada quando há resultado. Busca sem resultado devolve DataFrame vazio sem nenhuma coluna. |

## Parâmetros específicos

- **`assunto`** (não `pesquisa` ou `termo`): texto digitado no campo de busca do portal.
- `headless=False` para ver o navegador durante a coleta (debug).
- `debug=True` mantém HTMLs brutos baixados — útil se precisar inspecionar o conteúdo.

## Gotchas

- **JavaScript obrigatório**: o portal usa PrimeFaces (`form:...`), impossível raspar com `requests`. Por isso Playwright.
- **Sem Cloudflare**: diferente de ANS/ANVISA. Playwright básico (sem stealth) já funciona.
- **Limite de 50 páginas** (`_max_pages=50`). Suficiente para a maioria das buscas temáticas.
- **Paginação por links numerados** — estratégia `NUMBERED_LINKS`.
- Tempo de execução típico: ~10-20s por página. Planeje accordingly.

## Exemplo

```python
import raspe

df = raspe.saudelegis().raspar(assunto="doença rara")
print(df[["tipo_norma", "numero", "data_pub", "ementa"]].head())
```

Para debug visual:

```python
df = raspe.saudelegis(headless=False).raspar(assunto="doença rara")
```
