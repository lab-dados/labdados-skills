# juscraper-builder

Skill para Claude Code que gera automaticamente scrapers de tribunais
brasileiros para o pacote [juscraper](https://github.com/jtrecenti/juscraper).

## Instalação

### 1. Copie a pasta para o diretório de skills do Claude Code

```bash
# Nível de usuário (disponível em qualquer projeto)
cp -r juscraper-builder ~/.claude/skills/

# OU nível de projeto (apenas no juscraper)
cp -r juscraper-builder /caminho/para/juscraper/.claude/skills/
```

### 2. Instale o Playwright MCP

```bash
# A skill precisa do Playwright MCP para navegar nos sites
claude mcp add playwright -- npx @playwright/mcp@latest
```

Requer Node.js 18+. Se não tiver:
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS
brew install node
```

### 3. Pronto!

```bash
cd /caminho/para/juscraper
claude

# Diga algo como:
> Crie um scraper de jurisprudência para o TJMG.
> A página é: https://www5.tjmg.jus.br/jurisprudencia/
```

## O que a skill faz

1. Navega até o site do tribunal usando Playwright (browser real)
2. Mapeia os campos do formulário de busca
3. Submete uma busca de teste e captura as requisições HTTP
4. Identifica a API/endpoint por baixo do site
5. Gera código Python usando `requests` (sem Playwright no código final)
6. Cria testes de integração reais
7. Valida que tudo funciona

## Estrutura

```
juscraper-builder/
├── SKILL.md                           # Instruções principais
├── README.md                          # Este arquivo
├── references/
│   ├── juscraper-conventions.md       # Convenções do projeto
│   ├── tribunal-checklist.md          # Checklist de novo tribunal
│   ├── tribunal-patterns.md           # Padrões de sites de tribunais
│   └── test-patterns.md               # Padrões de testes
├── scripts/
│   ├── analyze_requests.py            # Analisa requisições capturadas
│   └── validate_scraper.py            # Valida scraper gerado
└── assets/
    └── template_tribunal.py           # Template base de scraper
```

## Requisitos

- Claude Code com Playwright MCP configurado
- Node.js 18+ (para o Playwright MCP)
- Python 3.11+ (para o juscraper)
- Repositório juscraper clonado e instalado em modo editável
