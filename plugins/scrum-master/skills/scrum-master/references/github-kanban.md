# Coleta de dados do Kanban do GitHub

**URL do projeto:** https://github.com/orgs/lab-dados/projects/1/views/1

GitHub Projects v2 (novo, não o clássico). A API é diferente e só suporta GraphQL — REST não acessa projects v2.

## Ordem de tentativa

1. **MCP do GitHub se disponível.** Procure em tools do prefixo `mcp__github` ou similar. Se houver, use operações como `list_project_items`, `get_project_fields`, `list_issues`. É o caminho mais rápido.
2. **`gh` CLI com GraphQL.** Se a CLI `gh` estiver instalada e autenticada (`gh auth status`), use:
   ```bash
   gh api graphql -f query='
     query {
       organization(login: "lab-dados") {
         projectV2(number: 1) {
           items(first: 100) {
             nodes {
               id
               fieldValues(first: 20) { nodes { __typename } }
               content { ... on Issue { number title state assignees(first:5){nodes{login}} labels(first:10){nodes{name}} updatedAt createdAt closedAt } ... on PullRequest { number title state merged } }
             }
           }
         }
       }
     }'
   ```
3. **Fallback: scraping autenticado via Chrome MCP.** Se nada acima funcionar, avise o usuário — scraping frequente quebra e não deve ser o caminho padrão.
4. **Se nada funcionar**, registre no relatório "Kanban indisponível nesta execução" e continue.

## Campos relevantes

Para cada item colete:
- `number`, `title`, `state` (OPEN/CLOSED/MERGED)
- `assignees[].login`
- `labels[].name`
- `updatedAt`, `createdAt`, `closedAt`
- Coluna/status customizado do projeto (Fase 2 do GH projects v2 guarda isso em `fieldValues` — procure o campo "Status").
- Link para o issue/PR (`url`).

## Classificação para o relatório

Com os itens em mãos, gere estas agregações:

- **Movidos na janela:** itens cujo `updatedAt` ou mudança de status caiu nos últimos 7 dias.
- **Fechados na janela:** `state == CLOSED` e `closedAt` nos últimos 7 dias.
- **Abertos na janela:** `createdAt` nos últimos 7 dias.
- **Parados há >14 dias:** `state == OPEN` e `updatedAt` há mais de 14 dias — entram em "dificuldades".
- **Por assignee:** conte itens abertos por pessoa. Assignees com fila muito grande (>7) merecem nota de overload.
- **Por label/frente:** mapeie labels para frentes do projeto (E1–E9) quando possível. Labels livres viram "Outros".

## Cuidados

- Não exponha tokens nem URLs com credenciais no relatório.
- Links do tipo `https://github.com/orgs/lab-dados/projects/1?pane=issue&itemId=...` são longos — prefira o link canônico do issue: `https://github.com/lab-dados/<repo>/issues/<number>`.
- Se houver itens "Draft" (sem conteúdo ligado a issue), trate como "ideia não formalizada" e só cite se for relevante.
