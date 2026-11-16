# Matriz de fontes — raspe

Visão comparada das 11 fontes cobertas pela biblioteca. Use este arquivo quando precisar escolher entre fontes, estimar volume/limites, ou verificar se uma tarefa cabe na skill.

## Matriz geral

| Fonte | Factory | URL oficial | Tecnologia | Auth | Parâmetro-chave |
|---|---|---|---|---|---|
| Presidência da República | `raspe.presidencia()` | legislacao.presidencia.gov.br | HTTP POST | nenhuma | `pesquisa` |
| Câmara dos Deputados | `raspe.camara()` | camara.leg.br/legislacao/busca | HTTP GET | nenhuma | `pesquisa` |
| Senado Federal | `raspe.senado()` | www6g.senado.leg.br/busca | HTTP GET | nenhuma | `pesquisa` |
| IPEA | `raspe.ipea()` | ipea.gov.br/portal/.../busca-publicacoes | HTTP GET | nenhuma | `pesquisa` |
| CAPES Periódicos | `raspe.capes()` | www.periodicos.capes.gov.br/.../buscador.html | HTTP GET | nenhuma | `pesquisa` |
| CFM | `raspe.cfm()` | portal.cfm.org.br/buscar-normas-cfm-e-crm | HTTP GET | nenhuma | `pesquisa` |
| Folha de São Paulo | `raspe.folha()` | search.folha.uol.com.br | HTTP GET | nenhuma | `pesquisa` |
| New York Times | `raspe.nyt(api_key=...)` | api.nytimes.com (Article Search API) | HTTP GET (JSON) | API key | `pesquisa` |
| SaudeLegis (Min. Saúde) | `raspe.saudelegis()` | saudelegis.saude.gov.br | Playwright | nenhuma | `pesquisa` |
| ANS (ANSLegis) | `raspe.ans()` | anslegis.datalegis.net | Playwright + stealth | nenhuma | `pesquisa` |
| ANVISA (ANVISALegis) | `raspe.anvisa()` | anvisalegis.datalegis.net | Playwright + stealth | nenhuma | `pesquisa` |

## Colunas retornadas

Nas fontes com schema de saída, uma busca sem resultado devolve DataFrame vazio com estas mesmas colunas. A descrição de cada coluna está na reference da fonte.

<!-- colunas-raspe:matriz:inicio (gerado por scripts/colunas_raspe.py do docs/colunas.md do raspe; nao editar a mao) -->

| Fonte | Colunas, na ordem do DataFrame |
|---|---|
| `ans` | `url`, `titulo`, `descricao`, `situacao`, `termo_busca` |
| `anvisa` | `url`, `titulo`, `descricao`, `situacao`, `termo_busca` |
| `capes` | `id`, `tipo`, `titulo`, `link`, `autores`, `ano`, `revista`, `instituicao`, `topicos`, `resumo`, `doi`, `link_editor`, `acesso_aberto`, `producao_nacional`, `revisado_por_pares`, `termo_busca` |
| `cfm` | `tipo`, `uf`, `numero_ano`, `situacao`, `ementa`, `link`, `termo_busca` |
| `folha` | `link`, `titulo`, `resumo`, `data`, `termo_busca` |
| `ipea` | `titulo`, `link`, `autores`, `data`, `assuntos`, `termo_busca` |
| `nyt` | `titulo`, `url`, `data_publicacao`, `secao`, `desk`, `tipo`, `resumo`, `autor`, `palavras`, `imagem_url`, `termo_busca` |
| `presidencia` | `nome`, `link`, `ficha`, `revogacao`, `descricao`, `rotulo`, `termo_busca` |
| `saudelegis` | `tipo_norma`, `numero`, `data_pub`, `origem`, `ementa`, `link_url`, `termo_busca` |
| `camara` | sem schema de saída; veja `references/camara.md` |
| `senado` | sem schema de saída; veja `references/senado.md` |

<!-- colunas-raspe:matriz:fim -->

## Limites de coleta

| Fonte | Limite | Observação |
|---|---|---|
| `presidencia` | nenhum explícito | Sítio tem workaround SSL interno por certificado incompleto |
| `camara` | **10.000 resultados (500 páginas de 20)** | Acima disso, `UserWarning`; divida por `ano` ou `tipo_materia`. Sessão estabelecida automaticamente via página inicial |
| `senado` | nenhum explícito | — |
| `ipea` | nenhum explícito | — |
| `capes` | nenhum explícito; o tamanho da página vem dos itens da página 1 (30 hoje) | Buscas genéricas passam de 1 milhão de páginas: sempre use `paginas=range(1, N)` com N pequeno |
| `cfm` | 15 itens/página, 1-based | — |
| `folha` | **10.000 resultados (400 páginas)** | Biblioteca emite `UserWarning` ao atingir o teto; divida por `data_inicio`/`data_fim` |
| `nyt` | **1000 resultados (100 páginas), 5 req/min, 500 req/dia** | Scraper já aplica `sleep_time=12s`. Acima de 1000 resultados, `UserWarning`; divida por `ano` ou datas |
| `saudelegis` | 50 páginas (limite do `_max_pages`) | Paginação por links numerados |
| `ans` | 100 páginas (limite do `_max_pages`) | Paginação via SELECT dropdown |
| `anvisa` | 100 páginas (limite do `_max_pages`) | Paginação via SELECT dropdown |

## Cobertura e volume típico

- **Legislação federal**: Presidência (atos da chefia do executivo), Câmara (proposições PLs, PECs), Senado (proposições do Senado). Buscas genéricas como "saúde" retornam >10.000 resultados por fonte. Use filtros.
- **Atos regulatórios**: ANS (saúde suplementar), ANVISA (vigilância sanitária), SaudeLegis (Ministério da Saúde em geral), CFM (ética médica). Juntos cobrem quase todo o universo normativo de saúde pública no Brasil.
- **CAPES Periódicos**: base bibliográfica acadêmica indexada via OpenAlex, com 29+ milhões de itens (artigos, livros, capítulos). Cobre tanto produção nacional quanto internacional, com flags para acesso aberto e revisão por pares. Acesso ao **texto completo** dos artigos geralmente exige login institucional via CAFe — o raspador coleta apenas metadados da página pública de busca.
- **Imprensa**: Folha cobre desde 1994 para jornal impresso, online varia por período. NYT tem cobertura desde 1851 na API.

## Nomes de coluna em dataframeit / análise textual

Ao aplicar `dataframeit-skill` sobre um DataFrame coletado, identifique o campo com texto significativo:

| Fonte | `text_column` recomendada |
|---|---|
| `presidencia` | `descricao` |
| `camara` | `ementa` (fallback: `titulo`) |
| `senado` | `descricao` |
| `ipea` | `titulo` (não há abstract) |
| `capes` | `resumo` (fallback: `titulo` + `topicos`) |
| `cfm` | `ementa` |
| `folha` | `resumo` (fallback: `titulo`) |
| `nyt` | `resumo` (em inglês) |
| `saudelegis` | `ementa` |
| `ans` | `descricao` |
| `anvisa` | `descricao` |

## Quando combinar fontes

Pedidos comuns e estratégia:

- **"Legislação federal sobre X"**: rode `presidencia` + `camara` + `senado`, concatene, deduplique por `link`/`titulo`. A Presidência cobre o que foi sancionado; Câmara/Senado cobrem o que tramita ou tramitou.
- **"Tudo o que ANS, ANVISA e Ministério da Saúde publicaram sobre X"**: rode `ans` + `anvisa` + `saudelegis`. Cada um retorna ementas próprias.
- **"Como a imprensa cobriu X"**: rode `folha` + `nyt`. Atenção: NYT retorna em inglês, Folha em português — ao usar `dataframeit` para classificar, rode em batches separados ou peça ao LLM que seja língua-agnóstico.
- **Cross-referência legislação <-> notícia**: colete a legislação e, em seguida, use a data de publicação como `data_inicio` em `folha`/`nyt` para ver a cobertura midiática.
