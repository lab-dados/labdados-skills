# Matriz de fontes — raspe

Visão comparada das 12 fontes cobertas pela biblioteca. Use este arquivo quando precisar escolher entre fontes, estimar volume/limites, ou verificar se uma tarefa cabe na skill.

## Matriz geral

| Fonte | Factory | URL oficial | Tecnologia | Auth | Parâmetro-chave |
|---|---|---|---|---|---|
| Presidência da República | `raspe.presidencia()` | legislacao.presidencia.gov.br | HTTP POST | nenhuma | `pesquisa` |
| Câmara dos Deputados | `raspe.camara()` | camara.leg.br/legislacao/busca | HTTP GET | nenhuma | `pesquisa` |
| Senado Federal | `raspe.senado()` | www6g.senado.leg.br/busca | HTTP GET | nenhuma | `pesquisa` |
| CNJ (Comunica) | `raspe.cnj()` | comunicaapi.pje.jus.br | HTTP GET (JSON) | nenhuma | `pesquisa` |
| IPEA | `raspe.ipea()` | ipea.gov.br/portal/.../busca-publicacoes | HTTP GET | nenhuma | `pesquisa` |
| CAPES Periódicos | `raspe.capes()` | www.periodicos.capes.gov.br/.../buscador.html | HTTP GET | nenhuma | `pesquisa` |
| CFM | `raspe.cfm()` | portal.cfm.org.br/buscar-normas-cfm-e-crm | HTTP GET | nenhuma | `texto` |
| Folha de São Paulo | `raspe.folha()` | search.folha.uol.com.br | HTTP GET | nenhuma | `pesquisa` |
| New York Times | `raspe.nyt(api_key=...)` | api.nytimes.com (Article Search API) | HTTP GET (JSON) | API key | `texto` |
| SaudeLegis (Min. Saúde) | `raspe.saudelegis()` | saudelegis.saude.gov.br | Playwright | nenhuma | `assunto` |
| ANS (ANSLegis) | `raspe.ans()` | anslegis.datalegis.net | Playwright + stealth | nenhuma | `termo` |
| ANVISA (ANVISALegis) | `raspe.anvisa()` | anvisalegis.datalegis.net | Playwright + stealth | nenhuma | `termo` |

## Colunas retornadas

| Fonte | Colunas (além de `termo_busca`) |
|---|---|
| `presidencia` | `nome`, `link`, `ficha`, `revogacao`, `descricao` |
| `camara` | `link`, `titulo`, `descricao`, `ementa` |
| `senado` | `titulo`, `link_norma`, `link_detalhes`, `descricao`, `trecho_descricao` |
| `cnj` | Campos do JSON oficial (`texto`, `numero_processo`, `siglaTribunal`, `dataDisponibilizacao`, etc.) |
| `ipea` | `titulo`, `link`, `autores`, `data`, `assuntos` |
| `capes` | `id` (OpenAlex Work ID), `tipo`, `titulo`, `link`, `autores`, `ano`, `revista`, `instituicao`, `topicos`, `resumo`, `doi`, `link_editor`, `acesso_aberto`, `producao_nacional`, `revisado_por_pares` |
| `cfm` | `Tipo`, `UF`, `Nº/Ano`, `Situação`, `Ementa`, `Link` |
| `folha` | `link`, `titulo`, `resumo`, `data` |
| `nyt` | `titulo`, `url`, `data_publicacao`, `secao`, `desk`, `tipo`, `resumo`, `autor`, `palavras`, `imagem_url` |
| `saudelegis` | `tipo_norma`, `numero`, `data_pub`, `origem`, `ementa`, `link_url` |
| `ans` | `url`, `titulo`, `descricao`, `situacao` |
| `anvisa` | `url`, `titulo`, `descricao`, `situacao` |

## Limites de coleta

| Fonte | Limite | Observação |
|---|---|---|
| `presidencia` | nenhum explícito | Sítio tem workaround SSL interno por certificado incompleto |
| `camara` | nenhum explícito | Sessão estabelecida automaticamente via página inicial |
| `senado` | nenhum explícito | — |
| `cnj` | 5 itens/página | API de comunicações processuais. Paginação implícita |
| `ipea` | nenhum explícito | — |
| `capes` | nenhum explícito; **default `_find_n_pags` calcula `total // 30`** | Buscas genéricas retornam dezenas de milhões de páginas — sempre use `paginas=range(1, N)` com N pequeno |
| `cfm` | 15 itens/página, 1-based | — |
| `folha` | **10.000 resultados (400 páginas)** | Biblioteca emite warning ao atingir o teto; divida por `data_inicio`/`data_fim` |
| `nyt` | **1000 resultados (100 páginas), 5 req/min, 500 req/dia** | Scraper já aplica `sleep_time=12s`. Divida por `ano` ou datas |
| `saudelegis` | 50 páginas (limite do `_max_pages`) | Paginação por links numerados |
| `ans` | 100 páginas (limite do `_max_pages`) | Paginação via SELECT dropdown |
| `anvisa` | 100 páginas (limite do `_max_pages`) | Paginação via SELECT dropdown |

## Cobertura e volume típico

- **Legislação federal**: Presidência (atos da chefia do executivo), Câmara (proposições PLs, PECs), Senado (proposições do Senado). Buscas genéricas como "saúde" retornam >10.000 resultados por fonte. Use filtros.
- **Atos regulatórios**: ANS (saúde suplementar), ANVISA (vigilância sanitária), SaudeLegis (Ministério da Saúde em geral), CFM (ética médica). Juntos cobrem quase todo o universo normativo de saúde pública no Brasil.
- **CNJ Comunica**: intimações e comunicados processuais — não é o mesmo que jurisprudência. Para acórdãos e julgados, use `juscraper-skill`.
- **CAPES Periódicos**: base bibliográfica acadêmica indexada via OpenAlex, com 29+ milhões de itens (artigos, livros, capítulos). Cobre tanto produção nacional quanto internacional, com flags para acesso aberto e revisão por pares. Acesso ao **texto completo** dos artigos geralmente exige login institucional via CAFe — o raspador coleta apenas metadados da página pública de busca.
- **Imprensa**: Folha cobre desde 1994 para jornal impresso, online varia por período. NYT tem cobertura desde 1851 na API.

## Nomes de coluna em dataframeit / análise textual

Ao aplicar `dataframeit-skill` sobre um DataFrame coletado, identifique o campo com texto significativo:

| Fonte | `text_column` recomendada |
|---|---|
| `presidencia` | `descricao` |
| `camara` | `ementa` (fallback: `titulo`) |
| `senado` | `descricao` |
| `cnj` | `texto` |
| `ipea` | `titulo` (não há abstract) |
| `capes` | `resumo` (fallback: `titulo` + `topicos`) |
| `cfm` | `Ementa` |
| `folha` | `resumo` (fallback: `titulo`) |
| `nyt` | `resumo` (`snippet` em inglês) |
| `saudelegis` | `ementa` |
| `ans` | `descricao` |
| `anvisa` | `descricao` |

## Quando combinar fontes

Pedidos comuns e estratégia:

- **"Legislação federal sobre X"**: rode `presidencia` + `camara` + `senado`, concatene, deduplique por `link`/`titulo`. A Presidência cobre o que foi sancionado; Câmara/Senado cobrem o que tramita ou tramitou.
- **"Tudo o que ANS, ANVISA e Ministério da Saúde publicaram sobre X"**: rode `ans` + `anvisa` + `saudelegis`. Cada um retorna ementas próprias.
- **"Como a imprensa cobriu X"**: rode `folha` + `nyt`. Atenção: NYT retorna em inglês, Folha em português — ao usar `dataframeit` para classificar, rode em batches separados ou peça ao LLM que seja língua-agnóstico.
- **Cross-referência legislação <-> notícia**: colete a legislação e, em seguida, use a data de publicação como `data_inicio` em `folha`/`nyt` para ver a cobertura midiática.
