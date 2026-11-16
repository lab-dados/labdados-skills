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

<!-- colunas-raspe:tabela:inicio (gerado por scripts/colunas_raspe.py do docs/colunas.md do raspe; nao editar a mao) -->

| Coluna | Tipo | Descrição | Exemplo |
| --- | --- | --- | --- |
| `id` | texto | Identificador do registro, o mesmo do OpenAlex. | W4387465478 |
| `tipo` | texto | Tipo do registro. | Artigo |
| `titulo` | texto | Título do registro. | Judicialização de produtos à base de canabidiol no Brasil: uma análise de 2019 a 2022 |
| `link` | texto | Endereço da página de detalhes no portal da CAPES. | https://www.periodicos.capes.gov.br/index.php/acervo/buscador.html?task=detalhes&source=digital&id=W4387465478 |
| `autores` | texto | Autores separados por `; `. | Ronaldo Portela; Daniel Marques Mota; Paulo José Gonçalves Ferreira |
| `ano` | texto | Ano de publicação, com quatro dígitos, ou vazio. | 2023 |
| `revista` | texto | Periódico em que o registro saiu. | Cadernos de Saúde Pública |
| `instituicao` | texto | Instituição informada no card, ou vazio quando o card não traz instituição. | Escola Nacional de Saúde Pública, Fundação Oswaldo Cruz |
| `topicos` | texto | Tópico de pesquisa atribuído ao registro. | Cannabis and Cannabinoid Research |
| `resumo` | texto | Trechos do resumo que o buscador destaca, não o resumo inteiro. | ... the Center for Technical Support of the Judiciary |
| `doi` | texto | DOI, sem o prefixo `https://doi.org/`. | 10.1590/0102-311xpt024723 |
| `link_editor` | texto | Endereço do DOI na editora. | https://doi.org/10.1590/0102-311xpt024723 |
| `acesso_aberto` | booleano | O card traz o selo de acesso aberto. | True |
| `producao_nacional` | booleano | O card traz o selo de produção nacional. | True |
| `revisado_por_pares` | booleano | O card traz o selo de revisão por pares. | True |
| `termo_busca` | texto | Termo de busca que gerou a linha: o valor de `pesquisa` ou, numa busca com lista, o item da lista. | natjus |

<!-- colunas-raspe:tabela:fim -->

## Gotchas

- **Sintaxe `all:contains(termo)`**. O parâmetro `q` da API espera essa sintaxe Solr-like. O raspador encapsula isso automaticamente — basta passar `pesquisa="termo"` e ele monta `q=all:contains(termo)`. Para termos compostos com espaços, passe a string inteira (`pesquisa="acesso a medicamentos"`).
- **Paginação 1-based** via parâmetro `page`. O tamanho da página vem do número de itens da página 1 (30 em novembro de 2026; o atributo `data-per-page` do `<nav>`, que diz 20, fica só de reserva).
- **`pesquisa` é obrigatória.** String vazia ou só com espaços levanta `ValidationError` antes de qualquer requisição.
- **Volume gigante**. Buscas genéricas (ex.: "saúde") retornam ~29 milhões de resultados, ou seja, ~1 milhão de páginas com 30 itens cada. **Sempre use `paginas=range(1, N)` com N pequeno** (10-100 normalmente cobre). O scraper não limita por default.
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
