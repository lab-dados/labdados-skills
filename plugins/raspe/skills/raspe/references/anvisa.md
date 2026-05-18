# raspe.anvisa

## Fonte e escopo

Portal ANVISALegis da Agência Nacional de Vigilância Sanitária — `https://anvisalegis.datalegis.net/`. Indexa atos normativos da ANVISA: Resoluções da Diretoria Colegiada (RDC), Instruções Normativas, Portarias, Resoluções, e outros tipos. Infra Datalegis compartilhada com ANS.

## Requisitos

**Extra `[browser]` obrigatório**:

```bash
pip install "raspe[browser] @ git+https://github.com/bdcdo/raspe.git"
python -m playwright install chromium
```

## Assinatura

```python
raspe.anvisa(
    debug: bool = True,
    headless: bool = True,
).raspar(
    termo: str | list[str],
    paginas: range | None = None,
) -> pd.DataFrame
```

A assinatura é **idêntica** à de `raspe.ans()` — ambos herdam de `ScraperDatalegis`.

## Colunas retornadas

| Coluna | Conteúdo |
|---|---|
| `url` | URL absoluta para o ato. |
| `titulo` | Tipo + número + ano (ex.: "Resolução Nº 34, de 25/02/2021"). |
| `descricao` | Ementa do ato. |
| `situacao` | Status. **`None` = vigente**, caso contrário mostra "Revogado", "Revogado Tacitamente", etc. |
| `termo_busca` | Adicionada automaticamente. |

## Parâmetros específicos

Iguais aos de `raspe.ans()`:

- **`termo`**: texto do campo de busca.
- `headless=False` e `debug=True` para diagnósticos.

## Gotchas

- **Cloudflare + stealth**: igual à ANS. Sintomas de bloqueio: timeout em cima do campo de busca, página travada em challenge. Veja `references/playwright.md`.
- **Paginação via SELECT dropdown** (estratégia `SELECT_DROPDOWN`, `_max_pages=100`).
- **Situação vigente = `None`**: filtre explicitamente com `df[df["situacao"].isna()]`.
- Tempo típico: 15-30s por página.

## Exemplo

```python
import raspe

df = raspe.anvisa().raspar(termo="dispositivo médico", paginas=range(1, 4))
print(df.columns.tolist())

# Concentrar em vigentes
vigentes = df[df["situacao"].isna()]
print(f"{len(vigentes)} atos vigentes")

# Exportar
df.to_parquet("anvisa_dispositivo_medico.parquet")
```

## Diferença técnica vs ANS

Sob o capô, `anvisa` e `ans` compartilham 100% da lógica em `ScraperDatalegis`. Mudam apenas os **códigos internos do portal** (`_dominio`, `_cod_modulo`, `_cod_menu`, `_sgl_tipos`), que a biblioteca já tem hardcoded. Você não precisa conhecer esses detalhes — só use a factory certa para o órgão que o usuário quer.
