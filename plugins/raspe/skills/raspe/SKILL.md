---
name: raspe
description: Raspar dados de fontes oficiais brasileiras e imprensa com a biblioteca raspe. Cobre legislacao federal (Presidencia, Camara, Senado), agencias reguladoras (ANS, ANVISA, SaudeLegis, CFM), orgaos de pesquisa e controle (IPEA, CNJ) e imprensa (Folha de Sao Paulo, New York Times). Use esta skill sempre que o usuario mencionar coleta/raspagem de leis, decretos, portarias, resolucoes, projetos de lei, atos normativos, comunicados, diario oficial, agenda regulatoria, normas sanitarias, normas medicas, publicacoes do IPEA, noticias de jornal, "coletar dados do governo federal", "baixar legislacao", "atos da ANVISA", "resolucoes da ANS", "portarias do Ministerio da Saude", "materias da Folha", "artigos do NYT sobre Brasil", ou qualquer tarefa que envolva DataFrame a partir de sites oficiais brasileiros e do NYT — mesmo que nao mencione explicitamente "raspe".
---

# Raspe Skill

`raspe` e uma biblioteca Python para coleta automatizada de dados de **fontes oficiais brasileiras** e de duas fontes de imprensa (Folha de Sao Paulo e New York Times). Todos os scrapers expoem a mesma fachada `raspe.<fonte>().raspar(...)` e retornam `pandas.DataFrame` — sem parsing manual, sem autenticacao na maioria dos casos.

- Repositorio: <https://github.com/bdcdo/raspe>
- Licenca: MIT
- Autor: Bruno da Cunha de Oliveira

## Escopo desta skill

Esta skill cobre **uso** da biblioteca — escolher a fonte certa, chamar o scraper, interpretar resultados e erros. **Nao cobre** criacao de novos scrapers (extender `BaseScraper`/`PlaywrightScraper` para adicionar uma fonte nova). Se o usuario pedir "adicione a Receita Federal", oriente a abrir issue no repositorio e sugira como contorno coletar a fonte existente mais proxima.

## Antes de comecar

Complete este checklist antes de qualquer chamada. Fonte a fonte, a instalacao muda.

### 1. Instalacao basica (8 fontes HTTP)

```bash
pip install git+https://github.com/bdcdo/raspe.git
```

Python >= 3.11. Verifique com `python -c "import raspe; print(raspe.__version__)"`.

Cobre: `presidencia`, `camara`, `senado`, `cnj`, `ipea`, `cfm`, `folha`, `nyt`.

### 2. Instalacao com navegador (3 fontes Playwright)

Para ANS, ANVISA e SaudeLegis (sites dinamicos com JavaScript e/ou Cloudflare):

```bash
pip install "raspe[browser] @ git+https://github.com/bdcdo/raspe.git"
python -m playwright install chromium
```

Se o agente tentar usar esses scrapers sem o extra `[browser]`, a propria biblioteca levanta `DriverNotInstalledError` com a mensagem de instalacao — nao tente contornar, instale e tente novamente.

### 3. Autenticacao (apenas NYT)

Apenas o scraper do NYT pede credencial:

- Cadastre um app gratuito em <https://developer.nytimes.com/get-started>, ative "Article Search API", copie a key.
- Passe via parametro (`raspe.nyt(api_key="...")`) ou exporte `NYT_API_KEY` no ambiente. A biblioteca tenta a variavel automaticamente se o argumento for omitido.
- Sem chave, o construtor levanta `APIKeyError` com o passo-a-passo no texto da mensagem.

As demais 10 fontes sao totalmente publicas e nao exigem cadastro.

## Roteamento de decisao — qual fonte usar?

Comece identificando a **natureza do dado** que o usuario quer, depois confirme com a tabela.

| Quero... | Factory | Tecnologia | Parametro-chave | Autenticacao |
|---|---|---|---|---|
| Leis, decretos, MPs publicadas pela Presidencia | `raspe.presidencia()` | HTTP | `pesquisa` | nenhuma |
| Projetos de lei, proposicoes da Camara | `raspe.camara()` | HTTP | `pesquisa`, `ano`, `tipo_materia` | nenhuma |
| Projetos e legislacao federal indexada pelo Senado | `raspe.senado()` | HTTP | `pesquisa`, `ano`, `tipo_materia` | nenhuma |
| Comunicados e intimacoes processuais do CNJ | `raspe.cnj()` | HTTP (JSON) | `pesquisa`, `data_inicio`, `data_fim` | nenhuma |
| Estudos e publicacoes do IPEA | `raspe.ipea()` | HTTP | `pesquisa` | nenhuma |
| Normas do CFM e conselhos regionais de medicina | `raspe.cfm()` | HTTP | `texto`, `uf`, `ano`, `numero` | nenhuma |
| Noticias da Folha de Sao Paulo (online/jornal) | `raspe.folha()` | HTTP | `pesquisa`, `site`, `data_inicio`, `data_fim` | nenhuma |
| Artigos do New York Times por termo/ano/secao | `raspe.nyt(api_key=...)` | HTTP (API) | `texto`, `ano`, `data_inicio`, `data_fim`, `filtro` | API key |
| Normas sanitarias do Ministerio da Saude (SaudeLegis) | `raspe.saudelegis()` | Playwright | `assunto` | nenhuma, requer `[browser]` |
| Atos normativos da ANS (plano de saude) | `raspe.ans()` | Playwright + stealth | `termo` | nenhuma, requer `[browser]` |
| Atos normativos da ANVISA (vigilancia sanitaria) | `raspe.anvisa()` | Playwright + stealth | `termo` | nenhuma, requer `[browser]` |

Para detalhes de cobertura, limites e quirks de cada fonte, leia a reference correspondente em `references/<fonte>.md` **antes** de gerar codigo. A matriz completa de colunas retornadas e limites esta em `references/fontes.md`.

## Vocabulario do pesquisador → factory

O usuario raramente diz "presidencia" ou "camara" diretamente. Traduza termos informais:

| O usuario disse... | Factory mais provavel |
|---|---|
| "legislacao federal", "leis publicadas", "decretos", "medidas provisorias", "diario oficial" | `presidencia` (primeira opcao) + `camara`/`senado` (fonte original) |
| "projetos de lei", "proposicoes em tramitacao" | `camara` ou `senado` — pergunte a casa legislativa se nao disser |
| "portarias do Ministerio da Saude", "normas sanitarias federais" | `saudelegis` |
| "resolucoes da ANS", "RN da ANS", "normativo de plano de saude" | `ans` |
| "RDC", "resolucoes da ANVISA", "portarias ANVISA", "registro sanitario" | `anvisa` |
| "codigo de etica medica", "resolucao CFM", "parecer CFM" | `cfm` |
| "estudo do IPEA", "texto para discussao", "publicacao do IPEA" | `ipea` |
| "intimacao processual", "comunicado oficial do tribunal" (nao jurisprudencia) | `cnj` |
| "materia da Folha", "Folha de Sao Paulo escreveu sobre" | `folha` |
| "NYT sobre Brasil", "materia do New York Times" | `nyt` |

Se o tema e **jurisprudencia, acordao, numero CNJ de processo**: **nao e raspe**, e `juscraper-skill`. Avise o usuario e redirecione.

## Conceitos-chave

**Factory + `.raspar(...)`.** Toda fonte segue o padrao:

```python
import raspe
df = raspe.presidencia().raspar(pesquisa="meio ambiente", paginas=range(1, 4))
```

O metodo `.raspar()` sempre retorna `pandas.DataFrame`.

**Coluna `termo_busca` automatica.** Ao buscar com `pesquisa="X"` (ou `termo`/`texto`), a biblioteca adiciona `termo_busca` ao DataFrame para rastreabilidade. Se voce passar uma lista (`pesquisa=["a", "b"]`), ela roda cada termo e concatena com a coluna `termo_busca` identificando cada valor — ideal para rodar varios temas de uma vez sem precisar escrever um loop.

**Paginacao 1-based via `paginas=range(...)`.** `paginas=range(1, 4)` baixa paginas 1, 2, 3. `paginas=None` (default) baixa todas — **use com cautela**: buscas genericas podem ter centenas ou milhares de paginas.

**Nome do parametro de busca varia.** A maioria usa `pesquisa`, mas:

- `cfm` usa `texto`
- `nyt` usa `texto` (e aceita `ano`, `data_inicio`, `data_fim`, `filtro`)
- `saudelegis` usa `assunto`
- `ans` e `anvisa` usam `termo`

A reference por fonte tem a assinatura exata.

**Filtros de data.** `cnj`, `folha` e `nyt` aceitam `data_inicio` e `data_fim`. Formatos aceitos: `YYYY-MM-DD`, `DD/MM/YYYY`, `YYYYMMDD`. A biblioteca normaliza internamente.

**Filtro por ano.** `camara`, `senado` e `nyt` aceitam `ano=2024`.

## Rate limiting, etica e boas praticas de coleta

Sites governamentais sao infraestrutura publica — raspagem agressiva derruba servico para outros pesquisadores. Regras operacionais:

- **Comece pequeno.** Para qualquer busca nova, rode primeiro com `paginas=range(1, 4)`, confira o volume de resultados (ha logs indicando "X paginas" apos a primeira requisicao) e **pergunte ao usuario** se faz sentido expandir. Termos genericos ("saude", "educacao") podem render dezenas de milhares de registros.
- **Nao toque em `sleep_time`.** O default (2s entre requisicoes HTTP) ja e conservador. Reduzir leva a bloqueio de IP do lado do servidor — o usuario vai ficar horas sem acesso. Se precisar **aumentar** por causa de 429, faca; nunca diminuir.
- **NYT tem hard limit.** 5 requisicoes por minuto, 500 por dia, maximo de 1000 resultados por busca (100 paginas). O scraper ja aplica `sleep_time=12` automaticamente. Para coletar mais de 1000 resultados, divida por intervalos de datas (`data_inicio`/`data_fim`).
- **Folha tem teto de 10.000 resultados.** Se uma busca atingir esse numero, a propria biblioteca emite warning. Divida em periodos menores.
- **Snapshot da data da coleta.** Para reprodutibilidade, registre quando voce coletou. Sugira salvar junto com os dados: `df.assign(data_coleta=pd.Timestamp.today().isoformat()).to_parquet(...)`.
- **Republicar dados brutos.** Dados publicos coletados de sites oficiais sao livres para pesquisa — mas republicar em datasets abertos merece atencao a direito autoral (conteudo editorial de Folha/NYT, por exemplo). Em duvida, publique apenas links e metadados, nao o texto integral.

## Tratamento de erros

Hierarquia de excecoes (em `raspe.exceptions`):

- `ScraperError` — base de tudo.
  - `APIKeyError` — NYT sem API key ou key invalida. Mostre ao usuario como cadastrar.
  - `RateLimitError` — 429 persistente apos retries. Tem atributo `retry_after` (segundos). Espere e tente menos paginas.
  - `APIError` — erro HTTP generico. Atributos: `status_code`, `response_text` (500 chars).
  - `ValidationError` — parametro invalido (data mal formatada, `site` fora de `{todos, online, jornal}`, etc.).
  - `BrowserError` — falha em Playwright (elemento nao encontrado, timeout, bypass de Cloudflare falhou).
    - `DriverNotInstalledError` — sintoma classico: usuario chamou `raspe.ans()` sem `[browser]`. Solucao: `pip install "raspe[browser]"` + `playwright install chromium`.

Padrao geral: se uma fonte falhar com timeout ou 5xx, aumente `paginas` para um range menor, tente em outro horario (sites governamentais ficam lentos em horario comercial), e confirme com o usuario antes de repetir.

## O que fazer com os dados coletados

- **Exploracao rapida**: `df.head()`, `df.shape`, `df['termo_busca'].value_counts()`.
- **Salvar para analise**: `df.to_parquet("coleta.parquet")` (melhor para volumes grandes) ou `df.to_excel("coleta.xlsx", index=False)` (compativel com o fluxo Excel da maioria dos pesquisadores).
- **Multiplas fontes**: colete em DataFrames separados e concatene com `pd.concat([df1, df2], ignore_index=True)`; as colunas variam entre scrapers, entao o concat fica com `NaN` nos campos especificos.
- **Deduplicacao**: `raspe` exporta `raspe.remove_duplicates(df)` para casos comuns.

## Workflow tipico do agente

1. Ja leu este SKILL.md (feito).
2. Rode o checklist "Antes de comecar" — confira instalacao, extras `[browser]` se aplicavel, `NYT_API_KEY` se for NYT.
3. Traduza o pedido do usuario via "Vocabulario do pesquisador → factory" e confirme a fonte.
4. Para cada fonte envolvida, leia `references/<fonte>.md` **antes** de gerar codigo — assinaturas e colunas mudam por scraper.
5. Se ha duvida sobre limites/cobertura, leia `references/fontes.md`.
6. Se for Playwright (ANS/ANVISA/SaudeLegis), leia `references/playwright.md`.
7. Gere codigo com `paginas=range(1, 4)` por default e confirme com o usuario se ele quer expandir.
8. Execute. Se der erro, consulte "Tratamento de erros" acima.
9. Sugira `to_parquet` ou `to_excel` para persistir.

## Arquivos de referencia

Leia a referencia apropriada **antes** de gerar codigo. A tabela abaixo indica quando ler cada uma.

| Arquivo | Quando ler |
|---|---|
| `references/api.md` | Sempre antes de gerar codigo. Assinaturas exatas de todas as factories, parametros comuns, utilitarios, excecoes. |
| `references/fontes.md` | Quando precisar escolher entre fontes, comparar cobertura ou checar limites (NYT rate limit, teto da Folha, SELECT de ANS/ANVISA). |
| `references/playwright.md` | Quando for usar `ans`, `anvisa` ou `saudelegis`. Cobre instalacao, Cloudflare, `headless`/`debug`, sintomas de falha. |
| `references/exemplos.md` | Quando quiser um workflow ponta a ponta (coleta → filtro → export). 3 casos reais. |
| `references/presidencia.md` | Antes de chamar `raspe.presidencia()`. |
| `references/camara.md` | Antes de chamar `raspe.camara()`. |
| `references/senado.md` | Antes de chamar `raspe.senado()`. |
| `references/cnj.md` | Antes de chamar `raspe.cnj()`. |
| `references/ipea.md` | Antes de chamar `raspe.ipea()`. |
| `references/cfm.md` | Antes de chamar `raspe.cfm()`. |
| `references/folha.md` | Antes de chamar `raspe.folha()`. |
| `references/nyt.md` | Antes de chamar `raspe.nyt()` — cobre API key, rate limit, sintaxe Lucene do `filtro`. |
| `references/saudelegis.md` | Antes de chamar `raspe.saudelegis()`. |
| `references/ans.md` | Antes de chamar `raspe.ans()` — cobre Cloudflare. |
| `references/anvisa.md` | Antes de chamar `raspe.anvisa()` — cobre Cloudflare. |

## Integracao com outras skills

`raspe` entrega **dados brutos** (DataFrames). O fluxo tipico de uma pesquisa empirica usando esta skill combina:

| Etapa | Skill | Produto |
|---|---|---|
| Coleta em fontes oficiais brasileiras/imprensa | **raspe-skill** (esta) | DataFrame pandas com colunas especificas da fonte |
| Codificacao via LLM (classificar, extrair campos) | **dataframeit-skill** | DataFrame enriquecido com colunas estruturadas + `_total_tokens` |
| Revisao de literatura que motiva/dialoga com os dados | **openalex-skill** | Lista de artigos relevantes |
| Se o pedido for sobre **tribunais, jurisprudencia, acordaos** | **juscraper-skill** | `raspe` nao cobre isso — redirecione |

Se o usuario vai codificar/classificar o que foi coletado com LLM, lembre-o da **dataframeit-skill**. A `text_column` recomendada varia por fonte — consulte a tabela em `references/fontes.md` (secao "Nomes de coluna em dataframeit / analise textual"), que cobre as 11 fontes. Sempre passe `text_column=` explicitamente ao chamar `dataframeit`.
