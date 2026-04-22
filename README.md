# labdados-skills

Marketplace de skills do [Claude Code](https://claude.com/claude-code) mantido
pelo [lab-dados](https://github.com/lab-dados), voltado a pesquisa empirica
em direito no Brasil. Agrupa ferramentas para **coleta de dados judiciais**,
**enriquecimento de DataFrames com LLMs**, **busca de literatura academica**,
**construcao de scrapers** e **gestao do projeto LabDados**.

## Instalacao

Dentro do Claude Code, rode:

```
/plugin marketplace add lab-dados/labdados-skills
/plugin install juscraper@labdados-skills
/plugin install dataframeit@labdados-skills
/plugin install openalex@labdados-skills
/plugin install raspe@labdados-skills
/plugin install juscraper-builder@labdados-skills
/plugin install scrum-master@labdados-skills
```

Atualizacoes sao distribuidas ao subir a versao em `marketplace.json` — rode
`/plugin marketplace update` para puxar.

## Skills disponiveis

| Skill | O que faz | Trigger tipico |
|-------|-----------|----------------|
| [juscraper](plugins/juscraper/skills/juscraper/SKILL.md) | Raspa dados judiciais brasileiros (22 tribunais estaduais + Datajud + JusBR) | Tribunal brasileiro, numero CNJ, acordao, jurisprudencia |
| [dataframeit](plugins/dataframeit/skills/dataframeit/SKILL.md) | Enriquece DataFrames com LLMs — extracao estruturada via Pydantic | LLM, enriquecer dados, extrair informacao estruturada, DataFrame |
| [openalex](plugins/openalex/skills/openalex/SKILL.md) | Busca e baixa artigos academicos do OpenAlex | Revisao sistematica, literatura academica, artigos, DOI |
| [raspe](plugins/raspe/skills/raspe/SKILL.md) | Raspa dados de fontes oficiais brasileiras (Presidencia, Camara, Senado, CNJ, IPEA, CFM, ANS, ANVISA, SaudeLegis) e imprensa (Folha, NYT) | Legislacao federal, portarias ANVISA/ANS, normas sanitarias, materias de jornal |
| [juscraper-builder](plugins/juscraper-builder/skills/juscraper-builder/SKILL.md) | Gera scraper Python para tribunal brasileiro (sem captcha) via engenharia reversa | Criar scraper de tribunal, implementar cjsg/cjpg/cpopg/cposg |
| [juscraper-builder-captcha](plugins/juscraper-builder/skills/juscraper-builder-captcha/SKILL.md) | Gera scraper Python para tribunal com captcha (text-based via `txtcaptcha`) | Tribunal com captcha, reCAPTCHA detectado na pagina |
| [scrum-master](plugins/scrum-master/skills/scrum-master/SKILL.md) | Relatorio executivo semanal do LabDados | Resumo semanal, weekly plan, fechamento da semana |

## Pre-requisitos por skill

### juscraper

- Python >= 3.11
- `pip install juscraper` (ou `uv add juscraper`)
- Para Datajud: API key do CNJ (opcional — existe chave publica default)
- Para JusBR: token JWT via login gov.br

### dataframeit

- Python >= 3.10
- `pip install dataframeit[google]` (ou outro extra do provedor)
- API key do provedor LLM escolhido (Google, OpenAI, Anthropic, Cohere, Mistral)
- Para busca web: `pip install dataframeit[search]` + `TAVILY_API_KEY` ou `EXA_API_KEY`

### openalex

- API key do OpenAlex (gratis, https://openalex.org/settings/api)
- CLI `openalex-official` (apenas para downloads em massa)

### raspe

- Python >= 3.11
- `pip install git+https://github.com/bdcdo/raspe.git`
- Para ANS/ANVISA/SaudeLegis (Playwright): `pip install "raspe[browser] @ git+https://github.com/bdcdo/raspe.git"` + `python -m playwright install chromium`
- Para NYT: API key gratuita em <https://developer.nytimes.com/get-started> (variavel `NYT_API_KEY`)

### juscraper-builder

- Playwright MCP configurado no Claude Code (para navegacao e captura de
  requisicoes de rede durante a engenharia reversa)
- Python >= 3.11
- Para paginas com captcha text-based: `pip install txtcaptcha`

### scrum-master

- Acesso ao Kanban do GitHub do projeto LabDados (via `gh` CLI autenticado)
- MCPs do Google Drive, Gmail e Google Calendar (para documentos e reunioes)
- Exportacao de mensagens do WhatsApp em `.txt` quando aplicavel

## Atualizacoes

Este marketplace usa [semantic versioning](https://semver.org/). O numero
`version` em `.claude-plugin/marketplace.json` e incrementado a cada mudanca
publicada. O Claude Code detecta o novo numero e re-clona o plugin localmente.

Para forcar atualizacao manual:

```
/plugin marketplace update labdados-skills
```

## Contribuir

Issues e pull requests bem-vindos em
<https://github.com/lab-dados/labdados-skills/issues>.

## Licenca

MIT — ver [LICENSE](LICENSE).
