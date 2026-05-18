# raspe.cfm

## Fonte e escopo

Portal de busca de normas do Conselho Federal de Medicina e dos Conselhos Regionais de Medicina (CRMs) — `https://portal.cfm.org.br/buscar-normas-cfm-e-crm`. Cobre resoluções, pareceres, emendas, normas e decisões emitidas em âmbito federal e regional.

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

**Atenção ao nome do parâmetro**: é `texto` (não `pesquisa`, como na maioria das outras fontes).

## Colunas retornadas

| Coluna | Conteúdo |
|---|---|
| `Tipo` | Tipo da norma (Resolução, Parecer, Emenda, Norma, Decisão). |
| `UF` | UF do CRM emissor (vazio se for CFM). |
| `Nº/Ano` | Número e ano (ex.: "2217/2018"). |
| `Situação` | "Vigente", "Revogada", etc. |
| `Ementa` | Ementa da norma. |
| `Link` | URL da norma no portal. |
| `termo_busca` | Adicionada automaticamente. |

**Atenção**: nomes de coluna preservam maiúsculas/acentos (`Nº/Ano`, `Situação`) — use-os literalmente.

## Parâmetros específicos

- `uf`: sigla da UF para filtrar CRMs (ex.: `uf="SP"`). Vazio = todos (CFM + todos os CRMs).
- `revogada`: `"1"` para incluir apenas revogadas, vazio para todas.
- `numero`: número exato da norma.
- `ano`: ano da norma.

Por default, a busca inclui todos os 5 tipos (Resolução, Parecer, Emenda, Norma, Decisão).

## Gotchas

- **Nome `texto` em vez de `pesquisa`**: fácil esquecer. Se passar `pesquisa=`, o scraper não filtra nada e retorna a base inteira.
- **Paginação com 15 itens por página**, 1-based.
- O portal às vezes reporta "0 registros encontrados" — o scraper trata esse caso e retorna DataFrame vazio sem erro.

## Exemplo

```python
import raspe

# Todas as normas sobre "telemedicina"
df = raspe.cfm().raspar(texto="telemedicina", paginas=range(1, 3))

# Só CFM federal (uf vazio) e só vigentes (não passar revogada)
df_federal = df[df["UF"] == ""]
df_vigentes = df_federal[df_federal["Situação"] == "Vigente"]
```
