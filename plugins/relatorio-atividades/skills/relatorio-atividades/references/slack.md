# Coleta no Slack da equipe

O Slack do laboratório guarda decisões, combinações sobre eventos e parcerias,
andamento do processo seletivo e discussões de pesquisa. É uma fonte importante para
os blocos de atividades (Luiz) e de pesquisa (Julio e Bruno).

## Tools MCP disponíveis

Procure tools com prefixo `mcp__claude_ai_Slack__`. As principais são:

- `slack_search_channels`, encontra canais por nome ou descrição.
- `slack_read_channel`, lê o histórico de um canal (mais recentes primeiro; aceita
  `oldest` e `latest` em timestamp, e `cursor` para paginar).
- `slack_read_thread`, lê uma thread inteira (mensagem pai mais respostas).
- `slack_search_public`, busca conteúdo de mensagens em todos os canais públicos.
- `slack_search_public_and_private`, igual, incluindo canais privados.
- `slack_search_users` e `slack_read_user_profile`, para mapear quem é quem.

Se o MCP do Slack não estiver conectado, registre "Slack indisponível nesta execução"
e siga com as outras fontes.

## Estratégia de coleta (história completa)

1. **Descubra os canais** do laboratório com `slack_search_channels` (termos como
   "labdados", "lab", "dados", "pesquisa", "geral", "eventos"). Liste os canais
   relevantes e os IDs.
2. **Leia cada canal relevante** com `slack_read_channel`, paginando com `cursor` para
   cobrir o histórico. Se o histórico for grande, vá do mais antigo para o mais
   recente em blocos, consolidando marcos.
3. **Use `slack_search_public`** para buscar temas específicos dos blocos da issue
   #45: `evento`, `parceria`, `processo seletivo`, `vaga`, `oficina`, `curso`,
   `letramento`, `juscraper`, `survey`, `natjus`.
4. **Abra threads** com `slack_read_thread` quando uma mensagem importante tiver
   discussão relevante.

## Sinais a extrair

- **Eventos e parcerias** combinados, com data e instituição envolvida.
- **Processo seletivo:** etapas, prazos e resultados, sempre de forma agregada e
  neutra, nunca nominal (ver privacidade abaixo).
- **Decisões de pesquisa:** rumos dos pilotos, do app NatJus, do survey, das
  ferramentas.
- **Cursos e formação:** turmas, datas, público.

## Privacidade

Conteúdo sobre processo seletivo, remuneração e avaliação de pessoas deve ser tratado
de forma neutra e agregada. Não cite candidatos por nome nem reproduza mensagens
sensíveis. Em dúvida, resuma sem detalhe e siga.

## Como registrar

Use a tag `[S]` para Slack. Exemplo de evidência:
`[S] Parceria com [instituição] combinada no canal #geral` mais a data. Mensagens do
Slack não viram link público no relatório, ficam como texto com a tag `[S]`.
