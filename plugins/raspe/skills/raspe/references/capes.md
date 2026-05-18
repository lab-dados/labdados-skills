# raspe.capes

## Fonte e escopo

Buscador publico do Portal de Periodicos da CAPES — `https://www.periodicos.capes.gov.br/index.php/acervo/buscador.html`. Indexa metadados de artigos, livros e capitulos via integracao com o OpenAlex, cobrindo tanto producao nacional quanto internacional (29+ milhoes de itens). O raspador coleta apenas metadados da pagina publica; acesso ao texto completo geralmente exige login institucional via CAFe.

## Assinatura

```python
raspe.capes().raspar(
    pesquisa: str | list[str],
    paginas: range | None = None,
) -> pd.DataFrame
```

## Colunas retornadas

| Coluna | Conteudo |
|---|---|
| `id` | Work ID do OpenAlex (ex.: `W4387465478`). Util para cruzar com a `openalex-skill`. |
| `tipo` | `Artigo`, `Editorial`, `Capitulo`, `Livro`, etc. |
| `titulo` | Titulo do trabalho. |
| `link` | URL absoluta da pagina de detalhamento no portal CAPES. |
| `autores` | String com autores separados por `; `. |
| `ano` | Ano de publicacao (string com 4 digitos quando disponivel). |
| `revista` | Nome do periodico/journal (vazio para livros e capitulos). |
| `instituicao` | Instituicao editora/publicadora. |
| `topicos` | Topico tematico atribuido pelo OpenAlex (em ingles). |
| `resumo` | Snippet do abstract destacando o termo buscado (curto, nao e o abstract completo). |
| `doi` | DOI sem prefixo `https://doi.org/`. |
| `link_editor` | URL externa com prefixo `https://doi.org/...` (mesma origem do DOI). |
| `acesso_aberto` | `True` se marcado como acesso aberto. |
| `producao_nacional` | `True` se o trabalho e classificado como producao brasileira. |
| `revisado_por_pares` | `True` se passou por peer review. |
| `termo_busca` | Adicionada automaticamente. |

## Gotchas

- **Sintaxe `all:contains(termo)`**. O parametro `q` da API espera essa sintaxe Solr-like. O raspador encapsula isso automaticamente — basta passar `pesquisa="termo"` e ele monta `q=all:contains(termo)`. Para termos compostos com espacos, passe a string inteira (`pesquisa="acesso a medicamentos"`).
- **Paginacao 1-based** via parametro `page`. 30 resultados por pagina.
- **Volume gigante**. Buscas genericas (ex.: "saude") retornam ~29 milhoes de resultados, ou seja, ~980 mil paginas. **Sempre use `paginas=range(1, N)` com N pequeno** (10-100 normalmente cobre). O scraper nao limita por default.
- **Resumo curto**. O campo `resumo` traz apenas o snippet com o termo destacado, nao o abstract completo. Para o abstract, voce precisaria abrir cada `link` ou cruzar pelo `id` (OpenAlex) com a `openalex-skill`.
- **Proxy CAFe institucional**. Se voce estiver atras de uma rede com sessao CAFe, o servidor pode redirecionar para uma URL com subdominio `ez{NN}.periodicos.capes.gov.br`. Isso nao afeta o conteudo da busca publica — o `requests` segue redirect automaticamente.
- **Acesso a textos completos**. O raspador nao coleta PDFs ou full-texts. Para o conteudo, use o `link_editor` (DOI), `id` OpenAlex via `openalex-skill`, ou abra o link de detalhamento manualmente.

## Exemplo

```python
import raspe

# Busca simples
df = raspe.capes().raspar(pesquisa="natjus", paginas=range(1, 2))
print(df[["tipo", "ano", "titulo", "revista"]].head())

# Multiplos termos
df = raspe.capes().raspar(
    pesquisa=["judicializacao saude", "medicamento alto custo"],
    paginas=range(1, 4),
)
print(df.groupby("termo_busca").size())

# Filtrar so producao nacional revisada por pares
df_pn = df[df["producao_nacional"] & df["revisado_por_pares"]]
```

## Cross com openalex-skill

Como o `id` retornado e um Work ID do OpenAlex, voce pode enriquecer o DataFrame com dados detalhados (abstract completo, citacoes, referencias, conceitos) usando a `openalex-skill`:

```python
ids = df["id"].tolist()  # ['W4387465478', 'W3032714479', ...]
# usar openalex-skill para baixar metadados completos de cada ID
```
