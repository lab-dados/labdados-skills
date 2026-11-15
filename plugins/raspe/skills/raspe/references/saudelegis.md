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
    pesquisa: str,
) -> pd.DataFrame
```

Não aceita lista nem `paginas`: os dois levantam `ValidationError` antes de abrir o navegador. O nome antigo do parâmetro de busca, `assunto`, ainda é aceito com `DeprecationWarning`. O volume é todas as páginas que o site informa, até `_max_pages`; para uma coleta de teste curta, veja `references/api.md`.

## Colunas retornadas

<!-- colunas-raspe:tabela:inicio (gerado por scripts/colunas_raspe.py do docs/colunas.md do raspe; nao editar a mao) -->

| Coluna | Tipo | Descrição | Exemplo |
| --- | --- | --- | --- |
| `tipo_norma` | texto | Tipo da norma. | PORTARIA |
| `numero` | texto | Número e ano da norma. | 123/2024 |
| `data_pub` | texto | Data de publicação, em DD/MM/AAAA. | 15/01/2024 |
| `origem` | texto | Órgão de origem. | MS/GM |
| `ementa` | texto | Ementa da norma. | Define diretrizes para atendimento de doenças raras. |
| `link_url` | texto | Endereço do texto completo, ou vazio quando o portal não o traz. | /doc/portaria-123-2024.pdf |
| `termo_busca` | texto | Termo de busca que gerou a linha: o valor de `pesquisa` ou, numa busca com lista, o item da lista. | natjus |

<!-- colunas-raspe:tabela:fim -->

## Parâmetros específicos

- **`pesquisa`**: texto digitado no campo de busca do portal. Vazia, levanta `ValidationError`.
- `headless=False` para ver o navegador durante a coleta (debug).
- `debug=True` mantém HTMLs brutos baixados — útil se precisar inspecionar o conteúdo.

## Gotchas

- **JavaScript obrigatório**: o portal usa PrimeFaces (`form:...`), impossível raspar com `requests`. Por isso Playwright.
- **Sem Cloudflare**: diferente de ANS/ANVISA. Playwright básico (sem stealth) já funciona.
- **Limite de 50 páginas** (`_max_pages=50`). Suficiente para a maioria das buscas temáticas; se o site informar mais, a coleta para no teto com `UserWarning`.
- **Paginação por links numerados** — estratégia `NUMBERED_LINKS`.
- Tempo de execução típico: ~10-20s por página. Planeje accordingly.

## Exemplo

```python
import raspe

df = raspe.saudelegis().raspar(pesquisa="doença rara")
print(df[["tipo_norma", "numero", "data_pub", "ementa"]].head())
```

Para debug visual:

```python
df = raspe.saudelegis(headless=False).raspar(pesquisa="doença rara")
```
