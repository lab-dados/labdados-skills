# raspe.cfm

## Fonte e escopo

Portal de busca de normas do Conselho Federal de Medicina e dos Conselhos Regionais de Medicina (CRMs) — `https://portal.cfm.org.br/buscar-normas-cfm-e-crm`. Cobre resolucoes, pareceres, emendas, normas e decisoes emitidas em ambito federal e regional.

## Assinatura

```python
raspe.cfm().raspar(
    texto: str | list[str],
    uf: str = "",
    revogada: str = "",
    numero: str = "",
    ano: str = "",
    paginas: range | None = None,
) -> pd.DataFrame
```

**Atencao ao nome do parametro**: e `texto` (nao `pesquisa`, como na maioria das outras fontes).

## Colunas retornadas

| Coluna | Conteudo |
|---|---|
| `Tipo` | Tipo da norma (Resolucao, Parecer, Emenda, Norma, Decisao). |
| `UF` | UF do CRM emissor (vazio se for CFM). |
| `Nº/Ano` | Numero e ano (ex.: "2217/2018"). |
| `Situação` | "Vigente", "Revogada", etc. |
| `Ementa` | Ementa da norma. |
| `Link` | URL da norma no portal. |
| `termo_busca` | Adicionada automaticamente. |

**Atencao**: nomes de coluna preservam maiusculas/acentos (`Nº/Ano`, `Situação`) — use-os literalmente.

## Parametros especificos

- `uf`: sigla da UF para filtrar CRMs (ex.: `uf="SP"`). Vazio = todos (CFM + todos os CRMs).
- `revogada`: `"1"` para incluir apenas revogadas, vazio para todas.
- `numero`: numero exato da norma.
- `ano`: ano da norma.

Por default, a busca inclui todos os 5 tipos (Resolucao, Parecer, Emenda, Norma, Decisao).

## Gotchas

- **Nome `texto` em vez de `pesquisa`**: facil esquecer. Se passar `pesquisa=`, o scraper nao filtra nada e retorna a base inteira.
- **Paginacao com 15 itens por pagina**, 1-based.
- O portal as vezes reporta "0 registros encontrados" — o scraper trata esse caso e retorna DataFrame vazio sem erro.

## Exemplo

```python
import raspe

# Todas as normas sobre "telemedicina"
df = raspe.cfm().raspar(texto="telemedicina", paginas=range(1, 3))

# So CFM federal (uf vazio) e so vigentes (nao passar revogada)
df_federal = df[df["UF"] == ""]
df_vigentes = df_federal[df_federal["Situação"] == "Vigente"]
```
