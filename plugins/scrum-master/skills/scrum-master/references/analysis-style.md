# Estilo de análise — bons vs. maus exemplos

O valor do relatório está na qualidade da análise, não no volume. Use estes exemplos como guia ao escrever cada seção.

## Sumário executivo

**Ruim (genérico, sem substância):**
> - O time trabalhou em várias frentes.
> - Houve boa comunicação.
> - Alguns cards foram movidos.

**Bom (concreto, informativo):**
> - 12 cards movidos, 4 fechados, 0 abandonados.
> - Piloto quantitativo entrou na fase de coleta (Pedro lidera).
> - Workshop de Atlas.ti realizado em 17/04 com 14 participantes.
> - Dúvida sobre schema de jurimetria sem resposta há 5 dias — trava o piloto.

## O que foi feito

**Ruim (sem fonte, sem pessoa):**
> - Trabalho no pipeline de dados.
> - Discussões sobre metodologia.

**Bom (rastreável):**
> - `[K]` #42 "Pipeline de coleta STF" movido de "Doing" para "Review" por Pedro em 16/04.
> - `[W]` Maria anunciou no grupo (15/04) envio do primeiro draft da revisão de literatura.
> - `[D]` Doc "Protocolo piloto qualitativo" editado 4 vezes por Maria na semana; último commit em 18/04.

## Análise crítica — elogios

**Ruim (vago, parece puxa-saco):**
> - O time está motivado.
> - Todos estão contribuindo bem.

**Bom (específico, baseado em evidência):**
> - **Cadência de entrega do Pedro:** 3 PRs merged em 4 dias, todos com testes. Está puxando o piloto quantitativo de forma consistente.
> - **Resposta rápida no WhatsApp:** dúvidas do Pedro sobre schema respondidas em menos de 2h pela Maria em 3 ocasiões esta semana.

## Análise crítica — dificuldades

**Ruim (difuso, reclamão):**
> - As coisas estão andando devagar.
> - Falta clareza em algumas partes.

**Bom (específico, acionável):**
> - **Card "Definir categorias analíticas do piloto quali" parado desde 08/04** (>2 semanas). Sem comentário no card nem menção no WhatsApp — risco de bloqueio silencioso na entrega E4.
> - **Ausência de João na semana:** sem mensagens no grupo, sem movimentação no Kanban. Pode ser férias (não anunciadas) ou sinal a investigar.
> - **Dúvida de Pedro sobre licença do dataset** mandada no grupo em 13/04 sem resposta até 19/04. Enquanto isso, ele está bloqueado no passo de aquisição.

## Pauta sugerida para reunião

**Ruim (genérico):**
> - Alinhar sobre o projeto.
> - Discutir próximos passos.

**Bom (cada item tem razão de estar ali):**
> 1. **Schema de jurimetria** — Pedro precisa de decisão; bloqueia o piloto há 5 dias.
> 2. **Categorias do piloto quali** — card parado há 2 semanas; definir responsável ou fechar.
> 3. **Check-in com João** — ausente na semana; confirmar status.
> 4. **Calendário de workshops Q3** — proposta da Maria no WhatsApp (16/04) ainda não discutida.

## Tarefas por pessoa

**Ruim (não usa contexto):**
> - Julio: acompanhar o projeto.
> - Maria: continuar seu trabalho.

**Bom (baseada no que ficou pendente):**
> ### Maria (maria-xyz)
> - [ ] Responder dúvida do Pedro sobre licença do dataset (#43) *(pendente desde 13/04)*
> - [ ] Finalizar draft da revisão de literatura (E1) — combinado no WhatsApp de 15/04
> - [ ] Agendar workshop seguinte de Atlas.ti (proposta do dia 16/04)

## Cards propostos

**Ruim (vago, impossível de triar):**
> - Card sobre IA.
> - Melhorar documentação.

**Bom (título acionável, escopo claro):**
> **[ ] Aprovar**
> - **Título:** Definir política de uso de LLMs em pesquisas do LabDados
> - **Descrição:** Workshop de 16/04 levantou dúvidas sobre uso de modelos proprietários em dados sensíveis. Documento curto com diretrizes, aprovado por coordenação.
> - **Assignee sugerido:** Julio (coord. acadêmica)
> - **Coluna:** Ready
> - **Origem:** `[R]` reunião 16/04 + `[W]` discussão 17/04

## Princípios gerais

1. **Evidência > afirmação.** Sempre que possível, aponte a fonte (issue, data, mensagem, documento).
2. **Quantidade quando possível.** "3 PRs merged" > "vários PRs". "Parado há 14 dias" > "parado há tempos".
3. **Pessoa por nome, não por papel** — "Pedro" não "o pesquisador quantitativo". Papel vai em parênteses se ajudar.
4. **Não invente contexto.** Se não tem evidência, não afirme.
5. **Neutralidade.** Em dificuldades, descreva o fato; evite adjetivar pessoas ("lento", "desengajado"). Descreva o comportamento observável ("sem mensagens na semana").
