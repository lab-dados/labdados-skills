# Coleta de dados do Google Drive

**Pasta do projeto:** https://drive.google.com/drive/u/0/folders/1cGN2Mv2GLmmWEt-fFBrI5PKAhmgcgMWq

**Folder ID:** `1cGN2Mv2GLmmWEt-fFBrI5PKAhmgcgMWq`

## MCP do Google Drive

Procure tools com prefixo como `mcp__gdrive__` ou `mcp__google-drive__`. Ferramentas típicas disponíveis:

- `search_files` — busca por nome/conteúdo.
- `list_recent_files` — arquivos modificados recentemente.
- `read_file_content` — lê conteúdo (txt, docx, pdf, sheets).
- `get_file_metadata` — datas, donos, última modificação.

Se o MCP não estiver conectado, chame `mcp__mcp-registry__search_mcp_registry` com termos `["google drive", "gdrive"]` e sugira ao usuário conectar. Enquanto isso, registre "Google Drive indisponível" no relatório e siga.

## Estratégia de coleta

1. Liste arquivos na pasta raiz + subpastas com `modifiedTime >= (hoje - 7 dias)`.
2. Para cada arquivo modificado, capture: nome, tipo, última modificação, última pessoa que editou, link.
3. Para docs relevantes (docx, gdoc, pdf com texto), leia conteúdo e resuma em 1-2 frases.
4. Se houver muitos arquivos (>15) com atividade, só resuma os 5-10 mais relevantes — priorize pelos que têm relação clara com as frentes do projeto.

## Filtros úteis

- Ignore arquivos de sistema do Drive (`.tmp`, rascunhos automáticos).
- Arquivos muito grandes (>5 MB) não leia inteiros — peça só metadata e resumo por nome.
- Se houver pastas chamadas "Arquivados", "Lixo", "Old" — pule.

## O que reportar

Para a seção "O que foi feito" do relatório, gere bullets como:

- `[D] Atualização no doc "Plano do piloto quantitativo" por Maria (editado 3x na semana)` + link.
- `[D] Novo arquivo "Notas workshop Atlas.ti" criado em 17/04` + link.

Se a pasta tem estrutura (subpastas por frente, por pessoa), use a estrutura para classificar. Ex.: mudanças em `Drive/Capacitacao/` viram evidência da entrega E2.

## Nomes e links

Sempre cite link do arquivo no Drive no relatório, para o Julio poder abrir direto. Use a URL canônica `https://drive.google.com/file/d/<fileId>/view` ou `https://docs.google.com/document/d/<id>/edit`.
