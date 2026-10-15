# Checklist do fluxo

Marca o avanço pelas etapas da skill. O que o PR precisa conter está no `CONTRIBUTING.md` do juscraper, seção "Adding a new tribunal", e é lá que se confere a parte de código e testes; esta lista não a repete.

## Antes de começar
- [ ] Worktree e branch de feature no clone do juscraper; `uv sync --extra dev`
- [ ] Lidos o `CLAUDE.md`, as seções do `CONTRIBUTING.md` citadas no `SKILL.md` e `docs/api-conventions.qmd`
- [ ] Lidos dois raspadores de referência (ver `juscraper-conventions.md`)

## Reconhecimento
- [ ] Captcha verificado (tipo: ________________); se houver, fluxo passado à skill `juscraper-builder-captcha`
- [ ] Família verificada (eSAJ, PJe consulta pública, nenhuma)
- [ ] Todos os campos do formulário mapeados, inclusive ocultos, abas e o que o JavaScript faz antes do envio
- [ ] Mapeamento apresentado ao usuário e confirmado, com os campos deixados de fora e o motivo
- [ ] `robots.txt` lido

## Captura
- [ ] Requisição principal registrada (URL, método, Content-Type, corpo)
- [ ] Paginação entendida comparando páginas 1 e 2; fonte do total de resultados encontrada
- [ ] Sequência mínima de requisições (sessão, CSRF, estado no servidor) reproduzida com `requests`
- [ ] Cabeçalhos medidos: UA padrão do `HTTPScraper` testado primeiro; cabeçalhos de navegador só com evidência anotada
- [ ] Cada filtro testado uma vez no site

## Código, testes e PR
- [ ] Itens de "Adding a new tribunal" do `CONTRIBUTING.md` conferidos um a um
- [ ] Checklist de "Schemas pydantic" > "Checklist ao adicionar um tribunal novo" conferida
- [ ] Registro em `_SCRAPERS` de `src/juscraper/__init__.py`
- [ ] `uv run pytest tests/<xx> tests/schemas` passa
- [ ] `uv run pre-commit run --files <arquivos alterados>` passa
- [ ] `scripts/validate_scraper.py <xx>` sem problemas
- [ ] Notebook, `docs/_quarto.yml`, `docs/index.qmd` e CHANGELOG (Etapa 6 do `SKILL.md`)
- [ ] PR aberto pela branch de feature
