# juscraper-builder

Skill para Claude Code que leva um tribunal brasileiro do formulário de busca até um PR na biblioteca [juscraper](https://github.com/jtrecenti/juscraper). As convenções de código, testes e documentação não estão copiadas aqui: a skill aponta para o `CLAUDE.md`, o `CONTRIBUTING.md` e o `docs/api-conventions.qmd` do juscraper, que são a fonte única e vencem a skill quando divergirem.

## Instalação

Pelo marketplace `labdados-skills`:

```
/plugin install juscraper-builder@labdados-skills
```

O plugin traz também a skill `juscraper-builder-captcha`, para formulários com captcha.

## Uso

```bash
cd /caminho/para/juscraper
claude
```

```
> Crie um raspador de jurisprudência para o TJXX.
> A página é: https://www.tjxx.jus.br/jurisprudencia/
```

## O que a skill faz

1. Verifica captcha e família de sistema (eSAJ, PJe) antes de tudo; com captcha, passa para `juscraper-builder-captcha`.
2. Mapeia todos os campos do formulário, inclusive ocultos e o que o JavaScript faz antes do envio, e pede confirmação do mapeamento antes de escrever código.
3. Captura as requisições da busca com o navegador automatizado que a sessão tiver, ou com `curl`/`requests` lendo o HTML e o JavaScript do formulário, e mede quais cabeçalhos o portal exige.
4. Gera o raspador sobre `HTTPScraper`, com schemas pydantic e wiring pelo pipeline canônico, usando só `requests` no código final.
5. Gera o script de captura de samples, os contratos offline com `responses`, o contrato de filtros e aliases deprecados e, se pedido, integração com marker `integration`.
6. Valida com a suíte, o pre-commit e `scripts/validate_scraper.py`, e atualiza notebook, site e CHANGELOG.

## Estrutura

```
juscraper-builder/
├── SKILL.md                           # Fluxo de trabalho
├── README.md                          # Este arquivo
├── references/
│   ├── juscraper-conventions.md       # Onde está cada convenção no juscraper e que código ler
│   ├── tribunal-checklist.md          # Checklist do fluxo
│   ├── tribunal-patterns.md           # Sistemas e padrões comuns de sites de tribunais
│   └── test-patterns.md               # Ordem dos testes e esqueletos de código
├── scripts/
│   ├── analyze_requests.py            # Pontua requisições capturadas e sugere o endpoint
│   └── validate_scraper.py            # Checagem mecânica do raspador gerado
└── assets/
    └── template_tribunal/             # Módulos base: __init__, client, download, parse, schemas
```

## Requisitos

- Clone do juscraper com ambiente de desenvolvimento (`uv sync --extra dev`).
- Para a engenharia reversa, qualquer navegador automatizado disponível na sessão (Playwright MCP, Claude in Chrome, navegador embutido do app) ou só `curl`/`requests`. Nenhum é obrigatório.
- Python e demais dependências conforme o `pyproject.toml` do juscraper.
