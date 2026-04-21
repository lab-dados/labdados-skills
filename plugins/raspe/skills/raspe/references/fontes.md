# Matriz de fontes — raspe

Visao comparada das 11 fontes cobertas pela biblioteca. Use este arquivo quando precisar escolher entre fontes, estimar volume/limites, ou verificar se uma tarefa cabe na skill.

## Matriz geral

| Fonte | Factory | URL oficial | Tecnologia | Auth | Parametro-chave |
|---|---|---|---|---|---|
| Presidencia da Republica | `raspe.presidencia()` | legislacao.presidencia.gov.br | HTTP POST | nenhuma | `pesquisa` |
| Camara dos Deputados | `raspe.camara()` | camara.leg.br/legislacao/busca | HTTP GET | nenhuma | `pesquisa` |
| Senado Federal | `raspe.senado()` | www6g.senado.leg.br/busca | HTTP GET | nenhuma | `pesquisa` |
| CNJ (Comunica) | `raspe.cnj()` | comunicaapi.pje.jus.br | HTTP GET (JSON) | nenhuma | `pesquisa` |
| IPEA | `raspe.ipea()` | ipea.gov.br/portal/.../busca-publicacoes | HTTP GET | nenhuma | `pesquisa` |
| CFM | `raspe.cfm()` | portal.cfm.org.br/buscar-normas-cfm-e-crm | HTTP GET | nenhuma | `texto` |
| Folha de Sao Paulo | `raspe.folha()` | search.folha.uol.com.br | HTTP GET | nenhuma | `pesquisa` |
| New York Times | `raspe.nyt(api_key=...)` | api.nytimes.com (Article Search API) | HTTP GET (JSON) | API key | `texto` |
| SaudeLegis (Min. Saude) | `raspe.saudelegis()` | saudelegis.saude.gov.br | Playwright | nenhuma | `assunto` |
| ANS (ANSLegis) | `raspe.ans()` | anslegis.datalegis.net | Playwright + stealth | nenhuma | `termo` |
| ANVISA (ANVISALegis) | `raspe.anvisa()` | anvisalegis.datalegis.net | Playwright + stealth | nenhuma | `termo` |

## Colunas retornadas

| Fonte | Colunas (alem de `termo_busca`) |
|---|---|
| `presidencia` | `nome`, `link`, `ficha`, `revogacao`, `descricao` |
| `camara` | `link`, `titulo`, `descricao`, `ementa` |
| `senado` | `titulo`, `link_norma`, `link_detalhes`, `descricao`, `trecho_descricao` |
| `cnj` | Campos do JSON oficial (`texto`, `numero_processo`, `siglaTribunal`, `dataDisponibilizacao`, etc.) |
| `ipea` | `titulo`, `link`, `autores`, `data`, `assuntos` |
| `cfm` | `Tipo`, `UF`, `Nº/Ano`, `Situação`, `Ementa`, `Link` |
| `folha` | `link`, `titulo`, `resumo`, `data` |
| `nyt` | `titulo`, `url`, `data_publicacao`, `secao`, `desk`, `tipo`, `resumo`, `autor`, `palavras`, `imagem_url` |
| `saudelegis` | `tipo_norma`, `numero`, `data_pub`, `origem`, `ementa`, `link_url` |
| `ans` | `url`, `titulo`, `descricao`, `situacao` |
| `anvisa` | `url`, `titulo`, `descricao`, `situacao` |

## Limites de coleta

| Fonte | Limite | Observacao |
|---|---|---|
| `presidencia` | nenhum explicito | Sitio tem workaround SSL interno por certificado incompleto |
| `camara` | nenhum explicito | Sessao estabelecida automaticamente via pagina inicial |
| `senado` | nenhum explicito | — |
| `cnj` | 5 itens/pagina | API de comunicacoes processuais. Paginacao implicita |
| `ipea` | nenhum explicito | — |
| `cfm` | 15 itens/pagina, 1-based | — |
| `folha` | **10.000 resultados (400 paginas)** | Biblioteca emite warning ao atingir o teto; divida por `data_inicio`/`data_fim` |
| `nyt` | **1000 resultados (100 paginas), 5 req/min, 500 req/dia** | Scraper ja aplica `sleep_time=12s`. Divida por `ano` ou datas |
| `saudelegis` | 50 paginas (limite do `_max_pages`) | Paginacao por links numerados |
| `ans` | 100 paginas (limite do `_max_pages`) | Paginacao via SELECT dropdown |
| `anvisa` | 100 paginas (limite do `_max_pages`) | Paginacao via SELECT dropdown |

## Cobertura e volume tipico

- **Legislacao federal**: Presidencia (atos da chefia do executivo), Camara (proposicoes PLs, PECs), Senado (proposicoes do Senado). Buscas genericas como "saude" retornam >10.000 resultados por fonte. Use filtros.
- **Atos regulatorios**: ANS (saude suplementar), ANVISA (vigilancia sanitaria), SaudeLegis (Ministerio da Saude em geral), CFM (etica medica). Juntos cobrem quase todo o universo normativo de saude publica no Brasil.
- **CNJ Comunica**: intimacoes e comunicados processuais — nao e o mesmo que jurisprudencia. Para acordaos e julgados, use `juscraper-skill`.
- **Imprensa**: Folha cobre desde 1994 para jornal impresso, online varia por periodo. NYT tem cobertura desde 1851 na API.

## Nomes de coluna em dataframeit / analise textual

Ao aplicar `dataframeit-skill` sobre um DataFrame coletado, identifique o campo com texto significativo:

| Fonte | `text_column` recomendada |
|---|---|
| `presidencia` | `descricao` |
| `camara` | `ementa` (fallback: `titulo`) |
| `senado` | `descricao` |
| `cnj` | `texto` |
| `ipea` | `titulo` (nao ha abstract) |
| `cfm` | `Ementa` |
| `folha` | `resumo` (fallback: `titulo`) |
| `nyt` | `resumo` (`snippet` em ingles) |
| `saudelegis` | `ementa` |
| `ans` | `descricao` |
| `anvisa` | `descricao` |

## Quando combinar fontes

Pedidos comuns e estrategia:

- **"Legislacao federal sobre X"**: rode `presidencia` + `camara` + `senado`, concatene, deduplique por `link`/`titulo`. A Presidencia cobre o que foi sancionado; Camara/Senado cobrem o que tramita ou tramitou.
- **"Tudo o que ANS, ANVISA e Ministerio da Saude publicaram sobre X"**: rode `ans` + `anvisa` + `saudelegis`. Cada um retorna ementas proprias.
- **"Como a imprensa cobriu X"**: rode `folha` + `nyt`. Atencao: NYT retorna em ingles, Folha em portugues — ao usar `dataframeit` para classificar, rode em batches separados ou peca ao LLM que seja lingua-agnostico.
- **Cross-referencia legislacao <-> noticia**: colete a legislacao e, em seguida, use a data de publicacao como `data_inicio` em `folha`/`nyt` para ver a cobertura midiatica.
