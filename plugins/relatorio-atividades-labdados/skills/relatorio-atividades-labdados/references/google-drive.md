# Coleta no Google Drive e OneDrive (história completa)

> Adaptado de `plugins/scrum-master/.../google-drive.md`. Sem filtro de 7 dias: aqui
> interessa o acervo inteiro de documentos do laboratório, não só o que mudou na semana.

## Google Drive

**Pasta do projeto:** https://drive.google.com/drive/u/0/folders/1cGN2Mv2GLmmWEt-fFBrI5PKAhmgcgMWq

**Folder ID:** `1cGN2Mv2GLmmWEt-fFBrI5PKAhmgcgMWq`

### Tools MCP

Procure tools com prefixo `mcp__claude_ai_Google_Drive__` (ou `mcp__gdrive__`).
Operações típicas:

- `search_files`, busca por nome ou conteúdo.
- `list_recent_files`, arquivos recentes.
- `read_file_content`, lê txt, docx, pdf, sheets.
- `get_file_metadata`, datas, donos, última modificação.

Se o MCP não estiver conectado, registre "Google Drive indisponível nesta execução",
sugira ao usuário conectar, e siga.

### Estratégia de coleta (acervo, não delta)

1. Liste a estrutura de pastas dentro da pasta do projeto. A organização em subpastas
   (por frente, por evento, por pesquisa) já é informação útil para classificar.
2. Para cada documento relevante, capture nome, tipo, data de criação, link.
3. Leia os documentos que descrevem entregas, eventos, parcerias, planos de pesquisa,
   materiais de curso. Resuma em uma ou duas frases o que cada um representa.
4. Priorize os documentos que viram evidência de uma entrega (E1 a E9) ou de um item
   dos blocos da issue #45.

### Filtros úteis

- Ignore arquivos de sistema e rascunhos automáticos.
- Arquivos muito grandes (acima de 5 MB) não leia inteiros, use só metadata e o nome.
- Pule pastas "Arquivados", "Lixo", "Old".

### Links

Sempre cite o link do arquivo, para a diretoria poder abrir. Use a URL canônica
`https://drive.google.com/file/d/<fileId>/view` ou
`https://docs.google.com/document/d/<id>/edit`.

## OneDrive

O usuário também guarda material no OneDrive. Não há uma pasta fixa conhecida.

- Se o usuário fornecer um link ou uma pasta do OneDrive, use-o. Se o conteúdo exigir
  acesso, **peça o acesso ou o link compartilhável** ao usuário antes de seguir.
- Se houver um MCP de OneDrive ou Microsoft Graph conectado, procure tools com prefixo
  `mcp__` correspondente e liste os arquivos da pasta indicada.
- Se nada estiver disponível, registre "OneDrive não consultado nesta execução
  (sem link ou sem acesso)" e siga. Não invente conteúdo.

## O que reportar

Para os blocos do relatório, transforme documentos em evidência:

- `[D] Documento "Plano do piloto quantitativo"` mais o link, no bloco de pesquisa.
- `[D] Material da oficina de letramento em IA`, no bloco de cursos e formação.

Use a tag `[D]` para Drive e OneDrive. Se a pasta tem estrutura por frente, use a
estrutura para classificar.
