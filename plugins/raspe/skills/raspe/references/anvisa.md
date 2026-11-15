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
    pesquisa: str,
) -> pd.DataFrame
```

Não aceita lista nem `paginas`: os dois levantam `ValidationError` antes de abrir o navegador. O nome antigo do parâmetro de busca, `termo`, ainda é aceito com `DeprecationWarning`. O volume é todas as páginas que o site informa, até `_max_pages`; para uma coleta de teste curta, veja `references/api.md`.

A assinatura é **idêntica** à de `raspe.ans()` — ambos herdam de `ScraperDatalegis`.

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

Iguais aos de `raspe.ans()`:

- **`pesquisa`**: texto do campo de busca.
- `headless=False` e `debug=True` para diagnósticos.

## Gotchas

- **Cloudflare + stealth**: igual à ANS. Sintomas de bloqueio: timeout em cima do campo de busca, página travada em challenge. Veja `references/playwright.md`.
- **Paginação via SELECT dropdown** (estratégia `SELECT_DROPDOWN`, `_max_pages=100`).
- **`situacao` traz o rótulo do portal** (`Vigente`, `Vigente com Alterações`, `Alterador`, `Revogado` etc.) e só vem nula quando o ato não tem rótulo. Os rótulos variam: confira com `df["situacao"].value_counts(dropna=False)` antes de filtrar.
- Tempo típico: 15-30s por página.

## Exemplo

```python
import raspe

df = raspe.anvisa().raspar(pesquisa="dispositivo médico")
print(df.columns.tolist())

# Rótulos de situação, antes de filtrar
print(df["situacao"].value_counts(dropna=False))

# Separar os revogados ("Revogado", "Revogado Tacitamente"...) do resto
revogado = df["situacao"].str.startswith("Revogado", na=False)
vigentes = df[~revogado]
print(f"{len(vigentes)} atos vigentes")

# Exportar
df.to_parquet("anvisa_dispositivo_medico.parquet")
```

## Diferença técnica vs ANS

Sob o capô, `anvisa` e `ans` compartilham 100% da lógica em `ScraperDatalegis`. Mudam apenas os **códigos internos do portal** (`_dominio`, `_cod_modulo`, `_cod_menu`, `_sgl_tipos`), que a biblioteca já tem hardcoded. Você não precisa conhecer esses detalhes — só use a factory certa para o órgão que o usuário quer.
