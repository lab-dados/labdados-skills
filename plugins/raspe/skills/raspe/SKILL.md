---
name: raspe
description: Raspar dados de fontes oficiais brasileiras, bases acadêmicas e imprensa com a biblioteca raspe. Cobre legislação federal (Presidência, Câmara, Senado), agências reguladoras (ANS, ANVISA, SaudeLegis, CFM), órgão de pesquisa (IPEA), base bibliográfica acadêmica (CAPES Periódicos), e imprensa (Folha de São Paulo, New York Times). Use esta skill sempre que o usuário mencionar coleta/raspagem de leis, decretos, portarias, resoluções, projetos de lei, atos normativos, comunicados, diário oficial, agenda regulatória, normas sanitárias, normas médicas, publicações do IPEA, artigos acadêmicos, revisão de literatura via CAPES, periódicos científicos, notícias de jornal, "coletar dados do governo federal", "baixar legislação", "atos da ANVISA", "resoluções da ANS", "portarias do Ministério da Saúde", "buscador da CAPES", "Portal de Periódicos", "matérias da Folha", "artigos do NYT sobre Brasil", ou qualquer tarefa que envolva DataFrame a partir de sites oficiais brasileiros, da CAPES e do NYT — mesmo que não mencione explicitamente "raspe".
---

# Raspe Skill

`raspe` é uma biblioteca Python para coleta automatizada de dados de **fontes oficiais brasileiras** e de duas fontes de imprensa (Folha de São Paulo e New York Times). Todos os scrapers expõem a mesma fachada `raspe.<fonte>().raspar(...)` e retornam `pandas.DataFrame` — sem parsing manual, sem autenticação na maioria dos casos.

- Repositório: <https://github.com/bdcdo/raspe>
- Licença: MIT
- Autor: Bruno da Cunha de Oliveira

## Escopo desta skill

Esta skill cobre **uso** da biblioteca — escolher a fonte certa, chamar o scraper, interpretar resultados e erros. **Não cobre** criação de novos scrapers (estender `BaseScraper`/`PlaywrightScraper` para adicionar uma fonte nova) — para isso, use a skill `raspe-builder`.

## Antes de começar

Complete este checklist antes de qualquer chamada. Fonte a fonte, a instalação muda.

### 1. Instalação básica (8 fontes HTTP)

```bash
pip install git+https://github.com/bdcdo/raspe.git
```

Python >= 3.10. Verifique com `python -c "import raspe; print(raspe.__version__)"`.

Cobre: `presidencia`, `camara`, `senado`, `ipea`, `cfm`, `folha`, `nyt`, `capes`.

### 2. Instalação com navegador (3 fontes Playwright)

Para ANS, ANVISA e SaudeLegis (sites dinâmicos com JavaScript e/ou Cloudflare):

```bash
pip install "raspe[browser] @ git+https://github.com/bdcdo/raspe.git"
python -m playwright install chromium
```

Se o agente tentar usar esses scrapers sem o extra `[browser]`, a própria biblioteca levanta `DriverNotInstalledError` com a mensagem de instalação — não tente contornar, instale e tente novamente.

### 3. Autenticação (apenas NYT)

Apenas o scraper do NYT pede credencial:

- Cadastre um app gratuito em <https://developer.nytimes.com/get-started>, ative "Article Search API", copie a key.
- Passe via parâmetro (`raspe.nyt(api_key="...")`) ou exporte `NYT_API_KEY` no ambiente. A biblioteca tenta a variável automaticamente se o argumento for omitido.
- Sem chave, o construtor levanta `APIKeyError` com o passo a passo no texto da mensagem.

As demais 10 fontes são totalmente públicas e não exigem cadastro.

## Roteamento de decisão — qual fonte usar?

Comece identificando a **natureza do dado** que o usuário quer, depois confirme com a tabela.

| Quero... | Factory | Tecnologia | Parâmetro-chave | Autenticação |
|---|---|---|---|---|
| Leis, decretos, MPs publicadas pela Presidência | `raspe.presidencia()` | HTTP | `pesquisa` | nenhuma |
| Projetos de lei, proposições da Câmara | `raspe.camara()` | HTTP | `pesquisa`, `ano`, `tipo_materia` | nenhuma |
| Projetos e legislação federal indexada pelo Senado | `raspe.senado()` | HTTP | `pesquisa`, `ano`, `tipo_materia` | nenhuma |
| Estudos e publicações do IPEA | `raspe.ipea()` | HTTP | `pesquisa` | nenhuma |
| Artigos acadêmicos no buscador do Portal de Periódicos da CAPES | `raspe.capes()` | HTTP | `pesquisa` | nenhuma |
| Normas do CFM e conselhos regionais de medicina | `raspe.cfm()` | HTTP | `texto`, `uf`, `ano`, `numero` | nenhuma |
| Notícias da Folha de São Paulo (online/jornal) | `raspe.folha()` | HTTP | `pesquisa`, `site`, `data_inicio`, `data_fim` | nenhuma |
| Artigos do New York Times por termo/ano/seção | `raspe.nyt(api_key=...)` | HTTP (API) | `texto`, `ano`, `data_inicio`, `data_fim`, `filtro` | API key |
| Normas sanitárias do Ministério da Saúde (SaudeLegis) | `raspe.saudelegis()` | Playwright | `assunto` (sem `paginas`) | nenhuma, requer `[browser]` |
| Atos normativos da ANS (plano de saúde) | `raspe.ans()` | Playwright + stealth | `termo` (sem `paginas`) | nenhuma, requer `[browser]` |
| Atos normativos da ANVISA (vigilância sanitária) | `raspe.anvisa()` | Playwright + stealth | `termo` (sem `paginas`) | nenhuma, requer `[browser]` |

Para detalhes de cobertura, limites e quirks de cada fonte, leia a reference correspondente em `references/<fonte>.md` **antes** de gerar código. A matriz completa de colunas retornadas e limites está em `references/fontes.md`.

## Vocabulário do pesquisador → factory

O usuário raramente diz "presidência" ou "câmara" diretamente. Traduza termos informais:

| O usuário disse... | Factory mais provável |
|---|---|
| "legislação federal", "leis publicadas", "decretos", "medidas provisórias", "diário oficial" | `presidencia` (primeira opção) + `camara`/`senado` (fonte original) |
| "projetos de lei", "proposições em tramitação" | `camara` ou `senado` — pergunte a casa legislativa se não disser |
| "portarias do Ministério da Saúde", "normas sanitárias federais" | `saudelegis` |
| "resoluções da ANS", "RN da ANS", "normativo de plano de saúde" | `ans` |
| "RDC", "resoluções da ANVISA", "portarias ANVISA", "registro sanitário" | `anvisa` |
| "código de ética médica", "resolução CFM", "parecer CFM" | `cfm` |
| "estudo do IPEA", "texto para discussão", "publicação do IPEA" | `ipea` |
| "artigo acadêmico", "paper", "revisão de literatura", "Portal de Periódicos da CAPES", "buscador da CAPES", "periódicos científicos" | `capes` |
| "intimação processual", "comunicado oficial do tribunal", "comunicações do CNJ" | não é raspe: a fonte CNJ saiu da biblioteca. Use `juscraper-skill` (ComunicaCNJ, `juscraper.scraper("comunica_cnj")`) |
| "matéria da Folha", "Folha de São Paulo escreveu sobre" | `folha` |
| "NYT sobre Brasil", "matéria do New York Times" | `nyt` |

Se o tema é **jurisprudência, acórdão, número CNJ de processo**: **não é raspe**, é `juscraper-skill`. Avise o usuário e redirecione.

## Conceitos-chave

**Factory + `.raspar(...)`.** Toda fonte segue o padrão:

```python
import raspe
df = raspe.presidencia().raspar(pesquisa="meio ambiente", paginas=range(1, 4))
```

O método `.raspar()` sempre retorna `pandas.DataFrame`.

**Coluna `termo_busca`.** Numa busca por string única, a biblioteca só adiciona `termo_busca` quando o parâmetro de busca se chama `pesquisa`, `termo`, `q` ou `query` (nas fontes Playwright, também `assunto`). `cfm` e `nyt`, que usam `texto`, voltam **sem** a coluna. Nas fontes HTTP, se você passar uma lista (`pesquisa=["a", "b"]`, `texto=["a", "b"]`), o scraper roda cada valor, concatena e preenche `termo_busca` com o valor de cada linha, inclusive em `cfm` e `nyt`. As fontes Playwright não aceitam lista.

**Paginação 1-based via `paginas=range(...)`.** `paginas=range(1, 4)` baixa páginas 1, 2, 3. `paginas=None` (default) baixa todas — **use com cautela**: buscas genéricas podem ter centenas ou milhares de páginas. **Só nas fontes HTTP.** `saudelegis`, `ans` e `anvisa` ignoram `paginas` sem erro e percorrem todas as páginas que o site informa, até o teto interno `_max_pages` (50 no SaudeLegis, 100 em ANS e ANVISA). Detalhes em `references/api.md`.

**Nome do parâmetro de busca varia.** A maioria usa `pesquisa`, mas:

- `cfm` usa `texto`
- `nyt` usa `texto` (e aceita `ano`, `data_inicio`, `data_fim`, `filtro`)
- `saudelegis` usa `assunto`
- `ans` e `anvisa` usam `termo`

A reference por fonte tem a assinatura exata.

**Filtros de data.** `folha` e `nyt` aceitam `data_inicio` e `data_fim`. Formatos aceitos: `YYYY-MM-DD`, `DD/MM/YYYY`, `YYYYMMDD`. A biblioteca normaliza internamente.

**Filtro por ano.** `camara`, `senado` e `nyt` aceitam `ano=2024`.

## Rate limiting, ética e boas práticas de coleta

Sites governamentais são infraestrutura pública — raspagem agressiva derruba serviço para outros pesquisadores. Regras operacionais:

- **Comece pequeno.** Para qualquer busca nova numa fonte HTTP, rode primeiro com `paginas=range(1, 4)`, confira o volume de resultados (há logs indicando "X páginas" após a primeira requisição) e **pergunte ao usuário** se faz sentido expandir. Termos genéricos ("saúde", "educação") podem render dezenas de milhares de registros.
- **Não toque em `sleep_time`.** O default (2s entre requisições HTTP) já é conservador. Reduzir leva a bloqueio de IP do lado do servidor — o usuário vai ficar horas sem acesso. Se precisar **aumentar** por causa de 429, faça; nunca diminuir.
- **NYT tem hard limit.** 5 requisições por minuto, 500 por dia, máximo de 1000 resultados por busca (100 páginas). O scraper já aplica `sleep_time=12` automaticamente. Para coletar mais de 1000 resultados, divida por intervalos de datas (`data_inicio`/`data_fim`).
- **Folha tem teto de 10.000 resultados.** Se uma busca atingir esse número, a própria biblioteca emite warning. Divida em períodos menores.
- **Snapshot da data da coleta.** Para reprodutibilidade, registre quando você coletou. Sugira salvar junto com os dados: `df.assign(data_coleta=pd.Timestamp.today().isoformat()).to_parquet(...)`.
- **Republicar dados brutos.** Dados públicos coletados de sites oficiais são livres para pesquisa — mas republicar em datasets abertos merece atenção a direito autoral (conteúdo editorial de Folha/NYT, por exemplo). Em dúvida, publique apenas links e metadados, não o texto integral.

## Tratamento de erros

Hierarquia de exceções (em `raspe.exceptions`). Nem todas chegam a quem chama `.raspar()`:

- `ScraperError` — base de tudo.
  - `APIKeyError` — NYT sem API key (no construtor) ou com key inválida (401 na requisição inicial). Propaga. Mostre ao usuário como cadastrar.
  - `RateLimitError` — 429 persistente após os retries da requisição inicial. **Não propaga**: a biblioteca registra o erro no log e `.raspar()` devolve DataFrame vazio. O atributo `retry_after` existe, mas não chega ao usuário.
  - `APIError` — erro HTTP. Atributos: `status_code`, `response_text` (500 chars). Só propaga no NYT, para 4xx diferente de 401 e 429 (401 vira `APIKeyError`) ou resposta com status inválido. 5xx persistente na requisição inicial tem o destino do `RateLimitError`: log e DataFrame vazio.
  - `ValidationError` — parâmetro inválido (data mal formatada, `site` fora de `{todos, online, jornal}`, `pesquisa` vazia na CAPES etc.). Propaga.
  - `BrowserError` — falha em Playwright (elemento não encontrado, timeout, bypass de Cloudflare falhou). Propaga.
    - `DriverNotInstalledError` — sintoma clássico: usuário chamou `raspe.ans().raspar(...)` sem `[browser]`. O construtor funciona sem Playwright, porque o import é preguiçoso; o erro só sai no `.raspar()`. Solução: `pip install "raspe[browser]"` + `playwright install chromium`.

Fora dessa hierarquia também propagam: `ValueError` (mais de um parâmetro passado como lista), `requests.HTTPError` (4xx diferente de 429 na requisição inicial das demais fontes HTTP) e erros de conexão ou timeout do `requests` na requisição inicial.

**Como detectar a falha silenciosa.** O logger de cada scraper escreve no stderr por padrão. Sinais no log:

- DataFrame vazio (`df.empty`) com `ERROR - Erro na requisição inicial`: 429 ou 5xx esgotados na requisição que conta as páginas, não ausência de resultados. Reduzir `paginas` não ajuda, porque foi essa primeira requisição que falhou. Espere alguns minutos ou tente em outro horário e rode a mesma busca de novo.
- `WARNING - Server error ... ignorando página N`: 5xx numa página seguinte, que foi pulada.
- `ERROR - Erro ao baixar página N`: erro de rede ou timeout numa página seguinte, que foi pulada.

Nos dois últimos casos o DataFrame veio incompleto. Um 4xx ou 429 numa página seguinte não deixa rastro: o corpo da resposta de erro é tratado como página e, no NYT, vira zero linhas. Esse é o risco típico do NYT, com limite de 5 requisições por minuto; confira se o número de linhas bate com o esperado (10 por página no NYT).

Padrão geral: se uma fonte falhar com timeout ou 5xx, aumente `paginas` para um range menor, tente em outro horário (sites governamentais ficam lentos em horário comercial), e confirme com o usuário antes de repetir.

## O que fazer com os dados coletados

- **Exploração rápida**: `df.head()`, `df.shape` e, se a coluna existir (`if "termo_busca" in df`), `df["termo_busca"].value_counts()`.
- **Salvar para análise**: `df.to_parquet("coleta.parquet")` (melhor para volumes grandes) ou `df.to_excel("coleta.xlsx", index=False)` (compatível com o fluxo Excel da maioria dos pesquisadores).
- **Múltiplas fontes**: colete em DataFrames separados e concatene com `pd.concat([df1, df2], ignore_index=True)`; as colunas variam entre scrapers, então o concat fica com `NaN` nos campos específicos.
- **Deduplicação**: `raspe` exporta `raspe.remove_duplicates(df)` para casos comuns.

## Workflow típico do agente

1. Já leu este SKILL.md (feito).
2. Rode o checklist "Antes de começar" — confira instalação, extras `[browser]` se aplicável, `NYT_API_KEY` se for NYT.
3. Traduza o pedido do usuário via "Vocabulário do pesquisador → factory" e confirme a fonte.
4. Para cada fonte envolvida, leia `references/<fonte>.md` **antes** de gerar código — assinaturas e colunas mudam por scraper.
5. Se há dúvida sobre limites/cobertura, leia `references/fontes.md`.
6. Se for Playwright (ANS/ANVISA/SaudeLegis), leia `references/playwright.md`.
7. Gere código com `paginas=range(1, 4)` por default e confirme com o usuário se ele quer expandir. Nas fontes Playwright, `paginas` não tem efeito: veja `references/api.md` para limitar o volume.
8. Execute. Se der erro, consulte "Tratamento de erros" acima.
9. Sugira `to_parquet` ou `to_excel` para persistir.

## Arquivos de referência

Leia a referência apropriada **antes** de gerar código. A tabela abaixo indica quando ler cada uma.

| Arquivo | Quando ler |
|---|---|
| `references/api.md` | Sempre antes de gerar código. Assinaturas exatas de todas as factories, parâmetros comuns, utilitários, exceções. |
| `references/fontes.md` | Quando precisar escolher entre fontes, comparar cobertura ou checar limites (NYT rate limit, teto da Folha, SELECT de ANS/ANVISA). |
| `references/playwright.md` | Quando for usar `ans`, `anvisa` ou `saudelegis`. Cobre instalação, Cloudflare, `headless`/`debug`, sintomas de falha. |
| `references/exemplos.md` | Quando quiser um workflow ponta a ponta (coleta → filtro → export). 3 casos reais. |
| `references/presidencia.md` | Antes de chamar `raspe.presidencia()`. |
| `references/camara.md` | Antes de chamar `raspe.camara()`. |
| `references/senado.md` | Antes de chamar `raspe.senado()`. |
| `references/ipea.md` | Antes de chamar `raspe.ipea()`. |
| `references/capes.md` | Antes de chamar `raspe.capes()` — cobre sintaxe `all:contains(...)` e colunas. |
| `references/cfm.md` | Antes de chamar `raspe.cfm()`. |
| `references/folha.md` | Antes de chamar `raspe.folha()`. |
| `references/nyt.md` | Antes de chamar `raspe.nyt()` — cobre API key, rate limit, sintaxe Lucene do `filtro`. |
| `references/saudelegis.md` | Antes de chamar `raspe.saudelegis()`. |
| `references/ans.md` | Antes de chamar `raspe.ans()` — cobre Cloudflare. |
| `references/anvisa.md` | Antes de chamar `raspe.anvisa()` — cobre Cloudflare. |

## Integração com outras skills

`raspe` entrega **dados brutos** (DataFrames). O fluxo típico de uma pesquisa empírica usando esta skill combina:

| Etapa | Skill | Produto |
|---|---|---|
| Coleta em fontes oficiais brasileiras/imprensa | **raspe-skill** (esta) | DataFrame pandas com colunas específicas da fonte |
| Codificação via LLM (classificar, extrair campos) | **dataframeit-skill** | DataFrame enriquecido com colunas estruturadas + `_input_tokens`, `_output_tokens`, `_reasoning_tokens` (não há `_total_tokens`; para o custo total, some `_input_tokens` e `_output_tokens`) |
| Revisão de literatura que motiva/dialoga com os dados | **openalex-skill** | Lista de artigos relevantes |
| Se o pedido for sobre **tribunais, jurisprudência, acórdãos** | **juscraper-skill** | `raspe` não cobre isso — redirecione |

Se o usuário vai codificar/classificar o que foi coletado com LLM, lembre-o da **dataframeit-skill**. A `text_column` recomendada varia por fonte — consulte a tabela em `references/fontes.md` (seção "Nomes de coluna em dataframeit / análise textual"), que cobre as 11 fontes. Sempre passe `text_column=` explicitamente ao chamar `dataframeit`.
