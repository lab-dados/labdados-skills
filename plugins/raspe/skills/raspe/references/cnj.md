# raspe.cnj

## Fonte e escopo

API de **Comunicações Processuais** do CNJ — `https://comunicaapi.pje.jus.br/api/v1/comunicacao`. Retorna intimações, citações e comunicados publicados nos portais do PJe. **Não é jurisprudência** — para acórdãos/julgados use `juscraper-skill`.

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

| Coluna | Conteúdo |
|---|---|
| `texto` | Texto integral da comunicação processual. |
| `numero_processo` | Número CNJ do processo. |
| `siglaTribunal` | Tribunal emissor (ex.: "TJSP", "TRF1"). |
| `dataDisponibilizacao` | Data em que a comunicação foi publicada. |
| `link` | URL para detalhes. |
| (outras) | Campos variados da API oficial. |
| `termo_busca` | Adicionada automaticamente. |

A resposta da API pode incluir campos adicionais. Rode `df.columns.tolist()` após a primeira coleta para ver tudo.

## Parâmetros específicos

- `data_inicio`/`data_fim`: filtram por data de disponibilização. Aceitam `YYYY-MM-DD`, `DD/MM/YYYY` ou `YYYYMMDD`.
- **5 itens por página** — a paginação é mais granular que outras fontes.

## Gotchas

- **Distinção conceitual**: o CNJ Comunica é diferente do DataJud e de qualquer sistema de jurisprudência. É apenas o *mural público* de intimações. Se o usuário pede "quero acórdãos do TJ" ou "jurisprudência sobre dano moral", **redirecione para juscraper-skill**.
- O endpoint é uma API JSON oficial — não há parsing HTML, então o DataFrame vem direto com a estrutura do JSON (pode ter colunas aninhadas como dicts).

## Exemplo

```python
import raspe

df = raspe.cnj().raspar(
    pesquisa="resolução",
    data_inicio="2024-01-01",
    data_fim="2024-03-31",
    paginas=range(1, 3),
)
print(df.head(3))
```
