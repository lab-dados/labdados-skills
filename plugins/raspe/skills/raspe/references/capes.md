# raspe.capes

## Fonte e escopo

Buscador público do Portal de Periódicos da CAPES — `https://www.periodicos.capes.gov.br/index.php/acervo/buscador.html`. Indexa metadados de artigos, livros e capítulos via integração com o OpenAlex, cobrindo tanto produção nacional quanto internacional (29+ milhões de itens). O raspador coleta apenas metadados da página pública; acesso ao texto completo geralmente exige login institucional via CAFe.

## Assinatura

```python
raspe.capes().raspar(
    pesquisa: str | list[str],
    paginas: range | None = None,
) -> pd.DataFrame
```

## Colunas retornadas

| Coluna | Conteúdo |
|---|---|
| `id` | Work ID do OpenAlex (ex.: `W4387465478`). Útil para cruzar com a `openalex-skill`. |
| `tipo` | `Artigo`, `Editorial`, `Capítulo`, `Livro`, etc. |
| `titulo` | Título do trabalho. |
| `link` | URL absoluta da página de detalhamento no portal CAPES. |
| `autores` | String com autores separados por `; `. |
| `ano` | Ano de publicação (string com 4 dígitos quando disponível). |
| `revista` | Nome do periódico/journal (vazio para livros e capítulos). |
| `instituicao` | Instituição editora/publicadora. |
| `topicos` | Tópico temático atribuído pelo OpenAlex (em inglês). |
| `resumo` | Snippet do abstract destacando o termo buscado (curto, não é o abstract completo). |
| `doi` | DOI sem prefixo `https://doi.org/`. |
| `link_editor` | URL externa com prefixo `https://doi.org/...` (mesma origem do DOI). |
| `acesso_aberto` | `True` se marcado como acesso aberto. |
| `producao_nacional` | `True` se o trabalho é classificado como produção brasileira. |
| `revisado_por_pares` | `True` se passou por peer review. |
| `termo_busca` | Adicionada automaticamente. |

## Gotchas

- **Sintaxe `all:contains(termo)`**. O parâmetro `q` da API espera essa sintaxe Solr-like. O raspador encapsula isso automaticamente — basta passar `pesquisa="termo"` e ele monta `q=all:contains(termo)`. Para termos compostos com espaços, passe a string inteira (`pesquisa="acesso a medicamentos"`).
- **Paginação 1-based** via parâmetro `page`. 30 resultados por página.
- **Volume gigante**. Buscas genéricas (ex.: "saúde") retornam ~29 milhões de resultados, ou seja, ~980 mil páginas. **Sempre use `paginas=range(1, N)` com N pequeno** (10-100 normalmente cobre). O scraper não limita por default.
- **Resumo curto**. O campo `resumo` traz apenas o snippet com o termo destacado, não o abstract completo. Para o abstract, você precisaria abrir cada `link` ou cruzar pelo `id` (OpenAlex) com a `openalex-skill`.
- **Proxy CAFe institucional**. Se você estiver atrás de uma rede com sessão CAFe, o servidor pode redirecionar para uma URL com subdomínio `ez{NN}.periodicos.capes.gov.br`. Isso não afeta o conteúdo da busca pública — o `requests` segue redirect automaticamente.
- **Acesso a textos completos**. O raspador não coleta PDFs ou full-texts. Para o conteúdo, use o `link_editor` (DOI), `id` OpenAlex via `openalex-skill`, ou abra o link de detalhamento manualmente.

## Exemplo

```python
import raspe

# Busca simples
df = raspe.capes().raspar(pesquisa="natjus", paginas=range(1, 2))
print(df[["tipo", "ano", "titulo", "revista"]].head())

# Múltiplos termos
df = raspe.capes().raspar(
    pesquisa=["judicialização saúde", "medicamento alto custo"],
    paginas=range(1, 4),
)
print(df.groupby("termo_busca").size())

# Filtrar só produção nacional revisada por pares
df_pn = df[df["producao_nacional"] & df["revisado_por_pares"]]
```

## Cross com openalex-skill

Como o `id` retornado é um Work ID do OpenAlex, você pode enriquecer o DataFrame com dados detalhados (abstract completo, citações, referências, conceitos) usando a `openalex-skill`:

```python
ids = df["id"].tolist()  # ['W4387465478', 'W3032714479', ...]
# usar openalex-skill para baixar metadados completos de cada ID
```
