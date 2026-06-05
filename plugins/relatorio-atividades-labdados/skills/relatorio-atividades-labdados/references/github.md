# Coleta no GitHub: board, issues e repositórios (história completa)

> Funde `github-kanban.md` + `tools-repos.md` da skill `scrum-master`, removendo os
> filtros de janela de 7 dias. Aqui o relatório é macro: queremos totais, marcos e a
> evolução desde o início, não o delta da semana.

## Board do projeto

**URL:** https://github.com/orgs/lab-dados/projects/1

GitHub Projects v2 (só GraphQL, REST não acessa).

### Ordem de tentativa

1. **MCP do GitHub**, se disponível (tools com prefixo `mcp__github` ou similar):
   `list_project_items`, `get_project_fields`, `list_issues`.
2. **`gh` CLI com GraphQL** (após `gh auth status`):
   ```bash
   gh api graphql -f query='
     query {
       organization(login: "lab-dados") {
         projectV2(number: 1) {
           items(first: 100) {
             nodes {
               id
               fieldValues(first: 20) { nodes { __typename } }
               content { ... on Issue { number title state assignees(first:5){nodes{login}} labels(first:10){nodes{name}} createdAt closedAt url } ... on PullRequest { number title state merged url } }
             }
           }
         }
       }
     }'
   ```
   Pagine com `after:` se houver mais de 100 itens.
3. **Se nada funcionar**, registre "board indisponível nesta execução" e siga.

### O que extrair (visão de história, não de semana)

- Total de itens por status (Backlog, Doing, Done, etc.).
- Itens concluídos ao longo do tempo, agrupados por fase do projeto e por frente.
- Distribuição por frente ou label, mapeando para as entregas E1 a E9 quando possível.
- Marcos relevantes (itens que representam entregas importantes), para a linha do tempo.

Não calcule "movidos nos últimos 7 dias". O foco é o acumulado e a trajetória.

## Repositórios

O trabalho do laboratório acontece muito em código. Cubra a **organização inteira**
mais os repositórios pessoais que pertencem ao laboratório.

**Organização `lab-dados` (todos os repos):**
```bash
gh repo list lab-dados --limit 100 --json name,pushedAt,isArchived,description \
  --jq '.[] | select(.isArchived==false) | {name, pushedAt, description}'
```
Inclui o repositório `adm`, que guarda as atas em `reunioes/` (ver `reunioes.md`).

**Pessoais (autoria de membros do time, relevantes ao laboratório):**
- `jtrecenti/juscraper`, ferramenta que baixa dados de processos dos tribunais.
- `bdcdo/dataframeit`, ferramenta que aplica modelos de linguagem linha a linha em
  tabelas de dados.
- `bdcdo/dataframeitgui`, interface gráfica do dataframeit.
- `bdcdo/raspe`, ferramenta de raspagem estruturada de fontes oficiais.

Esses são os repos pessoais conhecidos hoje; a autoria/composição muda com o tempo. Se
o usuário apontar outros repos (ou outras contas), adicione à lista.

### O que extrair, por repositório (toda a história)

Sem filtro de data. Para cada repo, levante os totais e os marcos:

```bash
# Total de commits (todos os branches)
gh api "repos/<owner>/<repo>/commits?per_page=1" --jq 'length'   # use paginação p/ contar
# Primeiro e último commit (idade do projeto)
gh api "repos/<owner>/<repo>/commits?per_page=1" --jq '.[0].commit.author.date'

# PRs (todos os estados), para contar e listar os mais relevantes
gh pr list --repo <owner>/<repo> --state all --limit 200 \
  --json number,title,state,mergedAt,author

# Issues (todas), exclui PRs
gh issue list --repo <owner>/<repo> --state all --limit 200 \
  --json number,title,state,createdAt,closedAt,author,labels

# Releases publicados (marcos de versão)
gh release list --repo <owner>/<repo> --limit 50 --json tagName,name,publishedAt
```

Para contagem de commits ao longo da história, prefira a API de estatísticas ou
pagine: `gh api --paginate "repos/<owner>/<repo>/commits?per_page=100"`. Se for caro
demais, registre uma estimativa e diga que é estimativa.

### Execução em paralelo

Chame os repos em paralelo (várias tool calls numa só mensagem). Use `pushedAt` e a
data do primeiro commit para situar cada ferramenta na linha do tempo.

## Como registrar no relatório

- **Releases** viram marcos na linha do tempo e no texto, por exemplo "o juscraper
  chegou à versão 0.3.0 em [mês], passando a cobrir 28 tribunais".
- **Tabela de ferramentas** (no bloco de pesquisa e ferramentas): nome, o que faz,
  status, repositório, número de versões publicadas.
- **Issues e PRs** dão a dimensão do esforço acumulado por ferramenta. Não liste
  todas, destaque as que representam entregas.
- Sempre transforme referências em links: `#N` para a issue, `owner/repo#N` para PRs
  de outros repos, `vX.Y.Z` para o release.

## Limites

- Se a autenticação `gh` falhar ou o rate limit for atingido, registre "fonte de
  código parcialmente indisponível" e siga.
- Não leia diffs nem código, só metadata. O relatório é institucional, não revisão
  técnica.
- Ignore bots (dependabot, renovate, github-actions[bot]), salvo PRs merged que sejam
  marcos.
- Não abra issues nem crie cards automaticamente.
