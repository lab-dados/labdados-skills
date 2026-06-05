# Contexto dos projetos do LabDados (fatos para o relatório)

Este arquivo guarda o que já foi apurado sobre cada projeto, para o relatório ter
**estofo**. Atualize com novas conversas. As datas são absolutas; converta "semana que
vem" etc. ao registrar. Nada de tags de fonte nem números de issue no texto final.

## Identidade do laboratório

- **Missão (texto oficial do site):** o LabDados é uma instância da FGV Direito SP que
  promove a interação entre as reflexões metodológicas em pesquisa empírica em Direito (que
  a Escola desenvolve há mais de uma década) e os avanços de análise de dados e IA. Objetivo:
  firmar a FGV Direito SP como centro de referência em pesquisa que combina ciência de dados
  e IA aplicadas ao Direito.
- **Site oficial:** https://direitosp.fgv.br/nucleos-de-pesquisa/laboratorio-dados-pesquisa-empirica-direito-labdados
- **Cinco eixos** (do site): pesquisa própria; apoio metodológico; formação; fórum
  permanente de debate metodológico; parcerias estratégicas.
- **O laboratório não é de ferramentas.** As ferramentas são meio; o fim é qualificar a
  pesquisa empírica da Escola. Esse enquadramento deve aparecer no relatório (use uma caixa
  de destaque). Evite dar peso excessivo ao juscraper: é um projeto entre vários.

## Equipe

> **Snapshot — muda com o tempo.** Esta é a composição conhecida na última execução,
> não uma premissa fixa da skill. **Confirme e atualize a cada relatório** (board, Slack,
> repos). Não acople pessoas a frentes na lógica da skill; trate quem está em cada frente
> como dado de runtime.

- **Coordenação:** Daniel Wang (Daniel Wei Liang Wang).
- **Equipe (ordem alfabética, sem papéis no texto):** Beatriz Varejão, Bruno Oliveira,
  Cláudia Hiromi, Helena Funari, Julio Trecenti, Luiz Pimenta.
- **Apoio:** João Pedro Salvador.
- Capacidades complementares: pós-doc em métodos, coordenação executiva, infraestrutura RTI
  FAPESP. (Handles GitHub: wangdanielwl, jtrecenti, bdcdo, LuizPF42, HelenaHime, claudia
  hiromi, biabrajal/Beatriz.)

## Frentes (proposta, seção 4) x Entregas (proposta, seção 2)

São **dois recortes diferentes** do mesmo trabalho, não listas concorrentes. O relatório usa
as 6 frentes como seções e marca em cada uma as entregas E1–E9 que cobre.

| Frente | Entrega(s) |
|---|---|
| Mapeamento institucional e captação de demandas | E1 |
| Levantamento de literatura | E1 |
| Capacitação | E2 |
| Escritório de apoio | E3 |
| Projetos de pesquisa (não chamar de "piloto") | E4 + E5 |
| Tecnologias e discussão metodológica | E6 + E7 + E8 |
| (relatório final) | E9 |

## Projetos, por frente

### Mapeamento institucional
- **Diagnóstico institucional:** formulário de demanda circulado na Escola; relatório de
  interesse e familiaridade com **67 respondentes**. Achado central: "a coleta de dados
  costuma vir antes da análise" (orienta formação e serviços). Segue rodada de conversas
  individuais com professores/coordenações. Espaço de documentos compartilhados (SharePoint/
  Teams).
- **Dados abertos:** Dataverse FGV (acertado com a Biblioteca) resolve armazenamento e
  publicação; ferramentas em código aberto; terreno comum com OKBR e afins.

### Levantamento de literatura
- **Scoping review IA na pesquisa jurídica:** revisão de escopo publicável (não sistemática
  fechada). Universo: periódicos de ciências sociais na Scopus, desde nov/2023, que usam LLM
  como **método** (não como objeto). Raspador da CAPES (no `raspe`). Primeiro teste de revisão
  automatizada feito; triagem em curso com validação humana da classificação por LLM. Desenho
  amadureceu em conversas com equipe canadense (sem parceria). Alimenta um grupo de estudos
  LLM no 2º semestre.

### Capacitação
- **Letramento em IA:** workshop de 4h, material próprio (espaço vetorial, alucinação,
  verificação de referências geradas por IA). 1ª turma 25/05/2026 **lotou e foi sucesso**;
  2ª turma 01/06; 3ª em avaliação. Turmas ≤ 30.
- **Curso de programação para pesquisa em direito:** um curso robusto (~6 encontros noturnos,
  2º sem), seguido de workshops. Busca reconhecimento como crédito nas 3 coordenações;
  diálogo com curso parecido no Insper. **Usará os pacotes do laboratório como material**
  (juscraper, dataframeit, raspe, SDK) sobre dados jurídicos reais.
- **Oficina Atlas.ti:** com profissional externa (Moniz); mini-workshop introdutório pelo lab.

### Escritório de apoio
- **Plataforma:** cardápio de serviços + fluxo de atendimento + POC **no ar para testes**.
  URL: https://labdados-frontend.livelydesert-3e3e3dd8.brazilsouth.azurecontainerapps.io/
  Serviços reais (do print): OCR de PDFs; transcrição e diarização de áudio (Whisper +
  pyannote); estruturação de textos com LLMs; anonimização de dados (NER, openai/privacy-filter
  e LeNER-Br); pedidos de consultoria; chave de API (SDK `labdados`). **Há vídeo explicativo:**
  https://www.youtube.com/watch?v=xYEflAD_Ls0
  Decisão 19/05: abandonar site próprio, hospedar via iFrame no domínio FGV (precedente: mapa
  do Núcleo de Direito Racial). Lançamento ~fim de junho/2026.
- **LabDados SDK:** pacote que reúne os serviços (OCR, transcrição, estruturação LLM, análise
  de viabilidade). Modos nuvem (chave) e local (dados sensíveis). Núcleo comum (`labdados-core`)
  com regras de viabilidade/veredito.

### Projetos de pesquisa
- **CCD Saúde (quantitativa):** com o Centro de Cidadania e Direitos; FAPESP + PGE-SP + SES-SP.
  Pergunta: o que mudou/permaneceu na judicialização da saúde após decisões do STF (Temas 6 e
  1234). Base do Datajud: **~3,3 milhões de processos** (33 tribunais, ~70 assuntos).
  Comparação MS x Datajud: **~40% de divergência** de cobertura (vira possível nota técnica
  sobre qualidade dos dados públicos). Recorte: 1ª instância, SP, só sentenças, estadual+
  federal. Acesso ao PDPJ pendente de autorização. Beatriz Varejão integrada (GitHub biabrajal,
  29/05). Repo com gráficos: `lab-dados/ccd-saude-data` (notebooks/1-explore-datajud: por ano,
  por tribunal, por assunto, por grau). O gráfico de processos por ano (crescimento) é o mais
  expressivo.
- **Parceria InternetLab (eleições):** vieses de LLMs em conteúdo político. Firmada em
  14/05/2026, aprovada pela Direção no mesmo dia ("agregar pessoas, não dividir o tempo").
  Escopo: revisão de literatura de técnicas de avaliação de viés; lista de contas/licenças do
  ambiente de testes; proposta técnica. Bibliografia: de **21 para 76 referências**. Quatro
  questões metodológicas: interface vs API; localização; memórias; conversas curtas vs longas.
  Base: paper da Maritaca (llm-bias-bench) + paper do IESP. Lidera Helena Funari, apoio JP
  Salvador. Overhead 20% aprovado; início pleno em julho. (O doc detalhado de objetivos do
  InternetLab estava pendente de envio pelo parceiro até o fim de maio.)

### Tecnologias e métodos (pacotes)
- **Pipeline (diagrama de fluxo):** fontes → coleta (juscraper, raspe) → estruturação com IA
  (SDK, dataframeit) → análise e entrega (pesquisas, escritório); difusão = marketplace de
  skills + Revista Direito GV.
- **juscraper:** baixa dados de processos. Cobre **28 tribunais** (estaduais e federais) + **4
  agregadores nacionais** (Datajud, JusBR, ComunicaCNJ, PDPJ). Alimenta o CCD. 1º lançamento
  público ~fim jul/2026.
- **dataframeit:** aplica LLM linha a linha em tabelas (classificação/extração). Tem GUI em
  desenvolvimento. Usado na revisão de literatura.
- **raspe:** raspagem estruturada de fontes oficiais (Presidência, Câmara, Senado, CNJ, ANS,
  ANVISA) e imprensa. Base do raspador da CAPES.
- **Marketplace de skills (10 habilidades):** explicar o que é uma skill (extensão para
  assistentes de IA que empacota uma tarefa de ponta a ponta; instala e usa sem programar).
  Grupos e habilidades (ver `marketplace.json` em `lab-dados/labdados-skills`):
  - Coleta: juscraper, raspe, openalex (460M+ obras).
  - Análise com IA: dataframeit.
  - Geração de raspadores: juscraper-builder, raspe-builder.
  - Operação/difusão: ata-reuniao, scrum-master, relatorio, explainer-video.
- **App do CAJU:** interface web para o escritório modelo da FGV (assistência jurídica);
  inaugurar na semana de abertura (agosto), junto com o juscraper.
- **Revista Direito GV:** robô revisor para acelerar publicação pós-aceite; entra na **difusão**
  do diagrama. Conversa em andamento.

### Eventos
- **Palestra de Luís Roberto Barroso** — "Novas Tecnologias e Direito", **28/04/2026**, 11h–
  12h30, auditório FGV Direito SP. Mesa: Oscar Vilhena (diretor, abertura), Daniel Wang
  (LabDados), Marina Feferbaum (CEPI). Barroso relatou usar IA para resumir processos no STF.
  **Lotou; foi sucesso.** Página: https://direitosp.fgv.br/eventos/novas-tecnologias-direito-palestra-luis-roberto-barroso
  Foto: https://static.poder360.com.br/2026/04/Barroso-na-FGV-1-848x477.png (crédito Gabriella
  Santos / Poder360; uso interno com crédito; para externo, confirmar autorização).
- **Agenda futura:** lançamento do escritório (~fim jun); lançamento público do juscraper
  (~fim jul, mesa com OKBR, Beatriz Milz, Ricardo Feliz); semana de abertura + app CAJU (ago);
  professor visitante Marco Biasi, Università di Milano (ago, IA e direito do trabalho);
  mapeamento de congressos (Helena).

## Em números (use métricas verificáveis, NÃO o quadro interno)

O Kanban é interno; não mostre estatísticas dele. Prefira: frentes (6), projetos (~17),
processos coletados (3,3 mi), tribunais+bases do juscraper (32), referências da literatura
(76), respondentes da demanda (67), habilidades no marketplace (10), turmas de formação (2),
parcerias (1), eventos realizados (1). As estatísticas de uso da plataforma do escritório
entram quando ela lançar.
