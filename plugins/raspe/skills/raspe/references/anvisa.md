# raspe.anvisa

## Fonte e escopo

Portal ANVISALegis da Agencia Nacional de Vigilancia Sanitaria — `https://anvisalegis.datalegis.net/`. Indexa atos normativos da ANVISA: Resolucoes da Diretoria Colegiada (RDC), Instrucoes Normativas, Portarias, Resolucoes, e outros tipos. Infra Datalegis compartilhada com ANS.

## Requisitos

**Extra `[browser]` obrigatorio**:

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

A assinatura e **identica** a `raspe.ans()` — ambos herdam de `ScraperDatalegis`.

## Colunas retornadas

| Coluna | Conteudo |
|---|---|
| `url` | URL absoluta para o ato. |
| `titulo` | Tipo + numero + ano (ex.: "Resolucao Nº 34, de 25/02/2021"). |
| `descricao` | Ementa do ato. |
| `situacao` | Status. **`None` = vigente**, caso contrario mostra "Revogado", "Revogado Tacitamente", etc. |
| `termo_busca` | Adicionada automaticamente. |

## Parametros especificos

Iguais aos de `raspe.ans()`:

- **`termo`**: texto do campo de busca.
- `headless=False` e `debug=True` para diagnosticos.

## Gotchas

- **Cloudflare + stealth**: igual a ANS. Sintomas de bloqueio: timeout em cima do campo de busca, pagina travada em challenge. Veja `references/playwright.md`.
- **Paginacao via SELECT dropdown** (estrategia `SELECT_DROPDOWN`, `_max_pages=100`).
- **Situacao vigente = `None`**: filtre explicitamente com `df[df["situacao"].isna()]`.
- Tempo tipico: 15-30s por pagina.

## Exemplo

```python
import raspe

df = raspe.anvisa().raspar(termo="dispositivo medico", paginas=range(1, 4))
print(df.columns.tolist())

# Concentrar em vigentes
vigentes = df[df["situacao"].isna()]
print(f"{len(vigentes)} atos vigentes")

# Exportar
df.to_parquet("anvisa_dispositivo_medico.parquet")
```

## Diferenca tecnica vs ANS

Sob o capo, `anvisa` e `ans` compartilham 100% da logica em `ScraperDatalegis`. Mudam apenas os **codigos internos do portal** (`_dominio`, `_cod_modulo`, `_cod_menu`, `_sgl_tipos`), que a biblioteca ja tem hardcoded. Voce nao precisa conhecer esses detalhes — so use a factory certa para o orgao que o usuario quer.
