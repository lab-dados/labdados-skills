# raspe.cnj

## Fonte e escopo

API de **Comunicacoes Processuais** do CNJ — `https://comunicaapi.pje.jus.br/api/v1/comunicacao`. Retorna intimacoes, citacoes e comunicados publicados nos portais do PJe. **Nao e jurisprudencia** — para acordaos/julgados use `juscraper-skill`.

## Assinatura

```python
raspe.cnj().raspar(
    pesquisa: str | list[str],
    data_inicio: str | None = None,
    data_fim: str | None = None,
    paginas: range | None = None,
) -> pd.DataFrame
```

## Colunas retornadas

A API retorna JSON — o DataFrame tem as colunas nativas da API. As principais:

| Coluna | Conteudo |
|---|---|
| `texto` | Texto integral da comunicacao processual. |
| `numero_processo` | Numero CNJ do processo. |
| `siglaTribunal` | Tribunal emissor (ex.: "TJSP", "TRF1"). |
| `dataDisponibilizacao` | Data em que a comunicacao foi publicada. |
| `link` | URL para detalhes. |
| (outras) | Campos variados da API oficial. |
| `termo_busca` | Adicionada automaticamente. |

A resposta da API pode incluir campos adicionais. Rode `df.columns.tolist()` apos a primeira coleta para ver tudo.

## Parametros especificos

- `data_inicio`/`data_fim`: filtram por data de disponibilizacao. Aceitam `YYYY-MM-DD`, `DD/MM/YYYY` ou `YYYYMMDD`.
- **5 itens por pagina** — a paginacao e mais granular que outras fontes.

## Gotchas

- **Distincao conceitual**: o CNJ Comunica e diferente do DataJud e de qualquer sistema de jurisprudencia. E apenas o *mural publico* de intimacoes. Se o usuario pede "quero acordaos do TJ" ou "jurisprudencia sobre dano moral", **redirecione para juscraper-skill**.
- O endpoint e uma API JSON oficial — nao ha parsing HTML, entao o DataFrame vem direto com a estrutura do JSON (pode ter colunas aninhadas como dicts).

## Exemplo

```python
import raspe

df = raspe.cnj().raspar(
    pesquisa="resolucao",
    data_inicio="2024-01-01",
    data_fim="2024-03-31",
    paginas=range(1, 3),
)
print(df.head(3))
```
