---
name: juscraper-builder
description: >
  Gera raspadores Python para tribunais brasileiros dentro da biblioteca
  juscraper, seguindo as convenções do próprio repositório (CLAUDE.md e
  CONTRIBUTING.md do juscraper, que vencem esta skill quando divergirem).
  Use sempre que o usuário pedir para criar um raspador ou scraper para um
  tribunal novo, implementar cjsg/cjpg/cpopg/cposg num tribunal, adicionar
  um tribunal ou agregador ao juscraper, mapear o formulário de busca de um
  tribunal, ou fazer engenharia reversa de uma página de consulta de
  jurisprudência ou de processos para virar código. Também acionar com
  "raspagem de tribunal", "scraping judicial", "novo tribunal no juscraper",
  "descobrir a API do TJXX", mesmo que o usuário não cite a skill. A
  engenharia reversa usa o navegador automatizado que a sessão tiver ou
  curl/requests lendo o HTML e o JavaScript do formulário; o código final
  usa só requests. Não confundir com juscraper-builder-captcha (o
  formulário tem captcha; esta skill encaminha para ela), com juscraper
  (usar a biblioteca para coletar dados, sem escrever raspador) nem com
  raspe-builder (fontes governamentais não judiciais, na biblioteca raspe).
---

# Juscraper Builder

Esta skill é o fluxo de trabalho para levar um tribunal do formulário no navegador até um PR no juscraper. As convenções em si moram no repositório do juscraper e não são copiadas aqui: cada etapa aponta a seção que é a fonte única. Onde a skill e o repositório divergirem, o repositório vence; quando isso acontecer, avise o usuário para que a skill seja corrigida.

## Princípio

O navegador serve só para entender o site. O raspador final faz requisições HTTP com `requests`, pela sessão do `HTTPScraper`, e não importa Selenium nem Playwright. A única exceção hoje é o desafio JavaScript do AWS WAF: `src/juscraper/core/waf.py` obtém o cookie `aws-waf-token` com Playwright num extra opcional (`juscraper[waf]`), com import lazy, e a raspagem segue em `requests` (STF e consulta pública do TJPE). Repetir esse desenho exige autorização do usuário depois de mostrar que não há alternativa.

## Etapa 0. Preparação

1. Confirme que está num clone do juscraper e trabalhe numa worktree com branch de feature, como manda o `CLAUDE.md` do juscraper, seção "Worktree e GitHub". Ambiente: `uv sync --extra dev`.
2. Leia, nesta ordem, antes de qualquer código:
   - `CLAUDE.md` do juscraper inteiro (é curto);
   - `CONTRIBUTING.md`, seções "Tests", "Adding a new tribunal", "Schemas pydantic" e "Docstrings de métodos públicos com kwargs" (e "Adding an eSAJ tribunal" se o site for eSAJ);
   - `docs/api-conventions.qmd`, para nomes de parâmetros, datas e paginação.
3. Leia dois raspadores recentes completos, cliente e testes. O mapa de quais ler e por quê está em `references/juscraper-conventions.md`. O código atual vence qualquer resumo, inclusive o desta skill.

## Etapa 1. Reconhecimento do site

**1.1 Captcha primeiro.** Antes de mapear campos, veja se o formulário ou a resposta da busca traz captcha (imagem, reCAPTCHA, hCaptcha, Cloudflare Turnstile) ou desafio de bot manager. Havendo captcha, interrompa este fluxo e siga a skill `juscraper-builder-captcha`, que começa testando se o backend de fato valida o captcha. Desafio JavaScript de WAF sem captcha (STF, TJPE) não é caso daquela skill: veja o Princípio acima.

**1.2 Família.** Antes de criar um raspador do zero, veja se o site pertence a uma família já implementada: eSAJ vira subclasse de `EsajSearchScraper` (`courts/_esaj/`) e PJe consulta pública vira subclasse de `TRFConsultaScraper` (`courts/_trf/`). A regra de quando generalizar está no `CLAUDE.md` do juscraper, seção "Arquitetura".

**1.3 Ferramenta.** Use o que a sessão oferecer. Qualquer navegador automatizado com acesso ao tráfego de rede serve (Playwright MCP, Claude in Chrome, navegador embutido do app): abra o formulário, submeta uma busca de reconhecimento e leia as requisições `fetch`, `xhr` e `document`, o bastante para saber o nome de cada campo no corpo. Sem navegador, baixe a página com `curl` ou `requests` e leia o `<form>`, os campos ocultos e o JavaScript que monta a requisição; em SPA, procure no bundle JS a URL da API e o formato do corpo. As duas vias podem ser combinadas, e o JavaScript costuma ser lido de qualquer jeito (ver 1.4).

**1.4 Mapear TODOS os campos do formulário.** Liste cada campo de busca, não só os óbvios. Para cada um, registre:

- rótulo na tela e nome do campo no corpo da requisição;
- tipo: texto, data, dropdown, checkbox, radio, aba ou base de pesquisa;
- valores possíveis dos dropdowns, e se o servidor recebe o ID ou o texto da opção;
- campos ocultos e o que o JavaScript faz antes do envio: copiar texto para campo oculto, reescrever valor, montar molde de campo indexado. No TRF3, o servidor ignora o ID do dropdown e pesquisa o texto que o JS copia para campos ocultos;
- campos que só existem em uma aba ou base, e combinações que o formulário recusa;
- o nome canônico que o campo vai ter no juscraper, conforme `docs/api-conventions.qmd` e as bases em `src/juscraper/schemas/`.

**1.5 Confirmação do usuário (obrigatória).** Apresente a lista completa ao usuário e espere a confirmação antes da captura da Etapa 2 (filtros testados um a um, paginação, samples) e antes de escrever código. Diga também quais campos você propõe deixar de fora e por quê. Exemplo de formato:

```
Campos de busca do {TRIBUNAL} ({URL}):

| Tela               | Campo no corpo        | Tipo     | Nome no juscraper        | Observação                    |
|--------------------|-----------------------|----------|--------------------------|-------------------------------|
| Pesquisa livre     | texto                 | texto    | pesquisa                 |                               |
| Julgamento de/até  | dtIni / dtFim         | data     | data_julgamento_inicio/fim | DD/MM/AAAA                  |
| Órgão julgador     | orgao (texto da opção)| dropdown | orgao_julgador           | 42 opções; ID ignorado        |
| Base               | aba `home/index/{n}` | aba      | base                     | acórdãos, monocráticas, ...   |

Fora do escopo proposto: {campo}, porque {motivo}.
Confirma o mapeamento?
```

Filtro que não entrar no schema fica rejeitado pelo `extra="forbid"`; filtro esquecido aqui só aparece depois que alguém precisar dele.

## Etapa 2. Captura das requisições

1. Submeta uma busca com termo genérico ("dano moral", "direito") e capture a requisição principal: URL, método, Content-Type, corpo, cookies e cabeçalhos. Ignore assets.
2. Vá para a página 2 e compare com a 1 para entender a paginação (offset, número de página, cursor, estado na sessão do servidor). Descubra de onde vem o total de resultados.
3. Descubra a sequência mínima: se é preciso um GET prévio para abrir sessão (JSESSIONID, `ASP.NET_SessionId`), token CSRF, ou um passo que grava estado no servidor. No TRF3, sem o GET da aba o POST cai em sessão expirada.
4. **Cabeçalhos: meça, não chute.** Reproduza a requisição com `requests` primeiro com o User-Agent padrão do `HTTPScraper` (`juscraper/<versão>`). Só se ele falhar (403, conexão pendurada, página de desafio, resposta diferente da do navegador), teste o conjunto mínimo de cabeçalhos de navegador que faz o portal responder. Anote o que foi medido, porque isso vira o comentário do `_configure_session` (ver Etapa 3).
5. Teste cada filtro mapeado na Etapa 1 pelo menos uma vez, para saber como ele aparece no corpo e se o servidor de fato o aplica.

Os scripts `scripts/analyze_requests.py` (pontua requisições capturadas em JSON e sugere o endpoint) e o roteiro de `references/tribunal-patterns.md` ajudam nesta etapa.

## Etapa 3. Código

O template em `assets/template_tribunal/` traz os cinco módulos (`__init__`, `client`, `download`, `parse`, `schemas`) para adaptar, com placeholders `TJXX`/`tjxx`. Quando o tribunal tiver endpoints de sistemas diferentes, a divisão por endpoint (`cjsg_download.py`, `cjsg_parse.py`, `cjsg_schemas.py`) também é praticada no repositório. Para cada parte, a fonte única:

| Parte | Onde está a regra |
|---|---|
| Classe base, sessão, retry | `CONTRIBUTING.md` > "Adding a new tribunal", item da base `HTTPScraper`; código em `src/juscraper/core/http.py` (`_request_with_retry`, `RequestPolicy`, `perfis_http`) |
| Payload builder público e constantes de URL | `CONTRIBUTING.md` > "Adding a new tribunal", item dos payload builders |
| Schemas `Input*`/`Output*` | `CONTRIBUTING.md` > "Schemas pydantic" (bases, mixins, nomes canônicos, `BACKEND_DATE_FORMAT`, checklist do tribunal novo) |
| Wiring da entrada | `CONTRIBUTING.md` > "Schemas pydantic" > "Pipeline canônico (wiring)"; implementação em `src/juscraper/utils/params.py::apply_input_pipeline_search` |
| Nomes de parâmetros, datas, paginação, aliases | `docs/api-conventions.qmd`; `CLAUDE.md` do juscraper, seções "API pública" e "Política de deprecação" |
| Docstrings | `CONTRIBUTING.md` > "Docstrings de métodos públicos com kwargs" |
| Registro na factory | dict `_SCRAPERS` em `src/juscraper/__init__.py`, formato `"módulo:Classe"` |

Pontos do fluxo que costumam escapar:

- **Retorno de `cjsg_download`.** Fora da família eSAJ, `cjsg_download` devolve a lista de respostas brutas (uma por página) e `cjsg_parse` recebe essa lista; o eSAJ ainda grava em disco e devolve o caminho. Confira num raspador recente antes de escrever, porque isso pode mudar.
- **Aliases.** `query`/`termo` e `data_inicio`/`data_fim` são aliases **deprecados**: o pipeline os resolve e emite `DeprecationWarning`. Nome antigo específico do tribunal também entra como alias deprecado (`resolve_deprecated_alias`/`pop_deprecated_alias`), resolvido antes do pydantic. Raspador novo não cria alias novo sem motivo.
- **User-Agent.** Não fixe UA no código. O `HTTPScraper` monta o identificável `juscraper/<versão>`, que é o default. Quando a medição da Etapa 2 mostrar que o portal só responde a cabeçalhos de navegador (bot manager, gating por UA), sobrescreva em `_configure_session` (ou na sessão própria do endpoint) e escreva na docstring ou no comentário o que foi medido. Quem faz isso hoje e como se acha com o comando em `references/juscraper-conventions.md`; a família eSAJ ainda fixa um UA antigo por requisição, legado que não serve de modelo.
- **Timeout e retry por endpoint.** Portal que pendura conexão ganha um perfil em `perfis_http` com `RequestPolicy` (timeout, tentativas, retry em timeout) e o download passa `perfil=` ao `request_fn`, em vez de retry manual.
- **Filtros em `**kwargs`, schema como lista única.** O template passa o `Input*` validado ao builder e ao manager, em vez de repetir os filtros em cada assinatura, e documenta cada campo do schema como bullet em `**kwargs` (a paridade de docstring confere). Raspador novo não cria alias específico: alias só existe para nome que já foi público.
- **Lint sem dispensa.** Arquivo novo entra sem dispensa em `ruff.toml` (`CONTRIBUTING.md` > "Política de lint e adoção gradual" > "Alcance das dispensas"). Raspadores antigos passam no gate graças a dispensas herdadas; copie deles a estrutura, não as assinaturas. Script de captura novo registra com `logging`, porque `print` cai na regra T201.
- **Combinações que o formulário recusa** (dois tipos de data juntos, filtro que uma base não tem) são validadas depois do pydantic e antes da primeira requisição, com `ValueError` claro.
- Paginação, pausa entre páginas e barra de progresso: siga o template e o raspador de referência; a semântica de `paginas` está no `CLAUDE.md` do juscraper, seção "API pública".

## Etapa 4. Testes

A política de testes é a do `CONTRIBUTING.md` do juscraper, seções "Tests" e "Adding a new tribunal", e o `CLAUDE.md` do juscraper diz que skills a seguem. Resumo do fluxo, sem substituir a lista de lá:

1. **Script de captura** em `tests/fixtures/capture/<xx>.py`, rodado contra o backend real, que importa o payload builder e as constantes do `download.py` e grava os samples crus em `tests/<xx>/samples/<endpoint>/`. Sample nunca é escrito à mão.
2. **Contrato offline** por método público (`test_<endpoint>_contract.py`) com `responses` servindo os samples e matcher de payload.
3. **Propagação de filtros** (`test_<endpoint>_filters_contract.py`): todos os filtros mapeados na Etapa 1 numa só chamada, conferidos contra um corpo literal com os nomes de campo do backend. Esperado montado pelo mesmo payload builder da produção não pega filtro que o builder deixou de mapear.
4. **Aliases deprecados**: um teste por alias aceito, com `pytest.warns(DeprecationWarning)` e o valor chegando ao backend como o canônico.
5. **Schema**: teste do `Input*` e registro do `Input*` e do `Output*` conforme `CONTRIBUTING.md` > "Schemas pydantic" > "Checklist ao adicionar um tribunal novo", mais os casos de `CONTRIBUTING.md` > "Docstrings de métodos públicos com kwargs" > "Cobertura de paridade".
6. **Integração**, se fizer, é camada extra em `test_<endpoint>_integration.py` com marker `integration` (e `anti_bot` se o portal bloqueia por IP), fora do `pytest` padrão. Nunca é o teste principal.

Templates e o conjunto de testes de referência estão em `references/test-patterns.md`.

## Etapa 5. Validação

```bash
uv run pytest tests/<xx> tests/schemas
uv run pre-commit run --files <arquivos alterados>   # o hook lint-policy exige origin/main local
uv run python <caminho-da-skill>/scripts/validate_scraper.py <xx>   # da raiz do juscraper
```

`validate_scraper.py` confere a parte mecânica (estrutura, base da classe, imports proibidos, UA fixo, `_request_with_retry`, registro em `_SCRAPERS`, contratos, samples, captura, registro dos schemas). Ele não substitui a suíte nem a leitura do `CONTRIBUTING.md`, e só cobre `src/juscraper/courts/`; agregador se confere pela suíte e pelo `CONTRIBUTING.md`. Antes do pre-commit, veja `CONTRIBUTING.md` > "Comandos locais e pre-commit" (`git fetch origin`).

Checagens manuais:

- [ ] Todos os campos confirmados na Etapa 1 viraram filtro do schema ou foram excluídos com motivo dito ao usuário
- [ ] Página 2 diferente da página 1
- [ ] Colunas com nomes canônicos
- [ ] Samples vieram do script de captura
- [ ] Nenhum `DeprecationWarning` disparado pelo próprio código do raspador

Diagnóstico rápido: 403 ou conexão pendurada aponta para cabeçalhos ou cookie de sessão (volte à Etapa 2.4); `ConnectionError` do `responses` no contrato quer dizer que o corpo enviado não bateu com o matcher, e a comparação se faz contra o payload builder; DataFrame vazio com resposta 200 costuma ser seletor, chave JSON ou encoding.

## Etapa 6. Documentação, changelog e PR

- **Idioma.** Pelo `CLAUDE.md` do juscraper, seção "Idiomas": docstrings em `src/`, commits e comentários de PR em português; arquivos de `docs/` em inglês, por convenção do projeto. Alguns títulos antigos de `docs/index.qmd` e `docs/_quarto.yml` estão em português; não os traduza no PR do tribunal.
- **Notebook** `docs/notebooks/<xx>.ipynb` com o fluxo público do raspador (busca simples, colunas, filtros, `*_download` e `*_parse` separados). Ele serve de documentação e de canário pós-refatoração (`CONTRIBUTING.md` > "Notebooks como sanity check").
- **Site.** Acrescente o notebook à barra lateral e a classe à seção de tribunais do quartodoc em `docs/_quarto.yml`, e o tribunal à tabela de `docs/index.qmd`. A tabela de tribunais do `README.md` hoje diverge da de `docs/index.qmd`; pergunte ao mantenedor se o PR deve atualizar as duas.
- **CHANGELOG** em `[Unreleased]` > `Added`, conforme `CLAUDE.md` do juscraper, seção "Changelog" (só efeito na API pública).
- **PR** pela branch de feature, sem push direto em `main`, conforme "Worktree e GitHub".

## Decisões de projeto

- **Encoding.** Tribunal brasileiro usa `latin-1` com frequência (eSAJ). Quando o parser trata o encoding, o contrato carrega o sample com `load_sample_bytes`.
- **Parsing de HTML.** `BeautifulSoup` com `lxml`; `pd.read_html()` basta para tabela simples. Contagem de resultados em HTML segue `CLAUDE.md` do juscraper, seção "Extração de número de páginas/resultados".
- **Site sem API acessível por `requests`** (conteúdo só via JavaScript, só WebSocket, anti-bot que nem cabeçalhos de navegador nem cookie de WAF resolvem): pare e apresente as opções ao usuário, como navegador no código final (menos estável, exige autorização), fonte alternativa (Datajud, JusBR, PDPJ) ou marcar o tribunal como não suportado.

## Conduta

- Respeite `robots.txt` e mantenha pausa de pelo menos 1 segundo entre requisições.
- Faça só as requisições necessárias para entender o site e capturar os samples.
- Rode integração fora do horário comercial quando possível.
- Não grave credenciais nem dados pessoais no código ou nos samples; o saneamento fica dentro do script de captura.
