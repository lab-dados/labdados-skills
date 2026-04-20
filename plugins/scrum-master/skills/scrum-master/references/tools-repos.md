# Repositórios de ferramentas — como coletar atividade da semana

Muito do trabalho do LabDados acontece em código, e nem tudo vira card no Kanban. Esta fonte existe para que o relatório capture entregas reais: commits, PRs, issues e releases em ferramentas que o time desenvolve.

## Repositórios monitorados

**Organização `lab-dados` (todos):** use `gh repo list lab-dados --limit 100` para descobrir repos vivos e iterar em cada um.

**Externos (relevantes ao LabDados por dependência ou por autoria do time):**
- `jtrecenti/juscraper` — raspador de tribunais brasileiros (Julio).
- `bdcdo/dataframeit` — utilitário de dataframes (Bruno).
- `bdcdo/raspe` — raspagem estruturada (Bruno).
- `bdcdo/cluster-facil` — agrupamento aplicado (Bruno).

Se o Julio apontar novos repos ("olha esse também"), adicione à lista e persista em `weekly-plan/.tools-repos.json` para runs futuros.

## O que extrair, por repositório

Para cada repo, cubra os **últimos 7 dias** (`--since=2026-04-13` ou o equivalente à janela analisada):

1. **Commits** — autor, mensagem curta, data. Agregue por autor + dia quando houver rajada.
2. **Pull requests** abertos, fechados, merged na janela — título, autor, estado.
3. **Issues** abertas ou fechadas — título, autor, labels se houver.
4. **Releases** publicados — tag, nome, data.

Comandos `gh` úteis (rodam com o PAT já autenticado):

```bash
# Commits na janela, todos os branches
gh api "repos/<owner>/<repo>/commits?since=2026-04-13T00:00:00Z&until=2026-04-20T00:00:00Z&per_page=100" \
  --jq '.[] | {sha: .sha[0:7], author: .commit.author.name, date: .commit.author.date, msg: .commit.message | split("\n")[0]}'

# PRs atualizados na janela
gh pr list --repo <owner>/<repo> --state all --search "updated:>=2026-04-13" \
  --json number,title,state,author,updatedAt

# Issues atualizadas na janela (exclui PRs)
gh issue list --repo <owner>/<repo> --state all --search "updated:>=2026-04-13" \
  --json number,title,state,author,updatedAt

# Releases recentes
gh release list --repo <owner>/<repo> --limit 5 --json tagName,name,publishedAt
```

Descobrir a org toda:
```bash
gh repo list lab-dados --limit 100 --json name,pushedAt,isArchived \
  --jq '.[] | select(.isArchived==false) | .name'
```

## Execução em paralelo

Chame os repos em paralelo (múltiplas tool calls numa só mensagem). Para um primeiro filtro rápido antes de iterar: `pushedAt >= janela` já elimina repos dormentes.

## Como registrar no relatório

- **Sumário executivo e métrica topo (HTML):** considere adicionar uma métrica "commits na semana" (soma entre repos) ou "repos ativos" quando fizer sentido.
- **O que foi feito:** cada atividade relevante vira 1 linha com tag `[C]`. Exemplos:
  - `[C] Bruno publicou v0.3.1 de cluster-facil (17/04) com suporte a HDBSCAN.`
  - `[C] Julio mergeou 4 PRs em juscraper (TJRS/TJMG/TJPR/TJPE) — 210 commits.`
  - `[C] lab-dados/portal-servicos: 12 commits da POC (Julio, 13–16/04).`
- **Cards propostos:** se aparecer issue relevante aberta e não atendida, vale propor card no Kanban central do LabDados (mesmo que a issue já esteja no repo).

## Limites

- Se autenticação `gh` falhar ou limite de rate for atingido, registre "fonte de código parcialmente indisponível" e siga com o resto.
- Não abra diffs ou leia código: só metadata. O relatório é gerencial, não revisão técnica.
- Ignore bots (dependabot, renovate, github-actions[bot]) salvo se virarem PRs merged que valem destaque.
- Respeite o fluxo de cards: **não abra issues nem crie cards no Kanban automaticamente** a partir do que achar nos repos. Tudo vira "Cards propostos" no `.md` para o Julio aprovar.
