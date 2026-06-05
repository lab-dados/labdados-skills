# Estilo dos relatórios de atividades do LabDados

Guia de escrita e formatação. O objetivo é um documento que a diretoria e as
coordenações da FGV Direito SP leiam rápido, entendam de primeira e confiem.
Adaptado do guia da skill `relatorio`, com regras de linguagem mais simples.

## Regras de linguagem (pedido do usuário, valem para todo o texto)

- **Não use travessões.** Nada de "—". Quando precisar separar uma ideia, use
  vírgula, ponto, parênteses, ou quebre a frase em duas. Isso vale para o texto
  corrido, para as legendas de tabela e figura e para os títulos.
- **Linguagem simples e natural**, como um relatório de pesquisa de verdade.
  Frases curtas, voz ativa, sem rebuscamento. Escreva para informar, não para
  impressionar.
- **Pouco jargão técnico.** Use só o termo necessário para o entendimento. Quando
  um termo técnico for inevitável (por exemplo o nome de uma ferramenta), explique
  em uma linha o que ela faz. Exemplo: "o juscraper, uma ferramenta que baixa
  dados de processos dos tribunais".
- Evite siglas soltas. Na primeira aparição, escreva o nome por extenso e a sigla
  entre parênteses.
- **Sem rótulos de fonte no corpo do texto.** As tags `[R]`, `[K]`, `[C]`, `[D]`, `[W]`
  servem para você rastrear a origem durante a coleta e a síntese, mas **não aparecem**
  no relatório final. O documento é para a diretoria, não um aparato de citação.
- **Sem números de issue no texto.** Nada de `#45`, `#32` e afins. Referência a issue não
  faz sentido para a diretoria. Links para ferramentas, releases e documentos podem
  aparecer; números de issue, não.

## Escrita

- **Português, claro e direto.** Sem floreio, sem "neste relatório iremos".
- **Resumo autossuficiente.** O primeiro parágrafo entrega o essencial: o que o
  laboratório fez, os números principais e onde está hoje. Quem ler só ele entende
  o panorama.
- **Número sempre com referência.** Toda afirmação quantitativa aponta para uma
  tabela (`@tbl-...`) ou figura (`@fig-...`). Não solte número solto no texto.
- **Não narre a tabela.** Em vez de repetir as células em prosa, comente o que
  elas mostram e por que importa.
- **Honestidade sobre limitações.** Lacunas de cobertura, fontes que não foram
  consultadas e ressalvas vão no texto, não escondidas. É o que dá credibilidade.
- **Números em português:** milhar com ponto (`3.357.449`), decimal com vírgula
  (`98,9%`). Datas em formato consistente.

## Tom para a diretoria

Este relatório é institucional e macro. Mostre progresso concreto e o rumo do
laboratório. Foque no que foi entregue, no que está em andamento e nos próximos
passos. Não é um relatório técnico nem uma revisão de código. A pessoa que lê quer
entender o valor do trabalho e a direção, não os detalhes de implementação.

## Tabelas

- Escreva em **pipe tables** Markdown ou gere com
  `Markdown(df.to_markdown(index=False))` num chunk `{python}`.
- Alinhe números à direita (`---:` na linha separadora).
- **Legenda** abaixo, com `{#tbl-rotulo}` para cross-reference.
- **Não desenhe bordas manualmente.** O stroke da última linha é aplicado pelo
  pós-processamento (`scripts/fix_docx_tables.py`), que iguala a borda inferior da
  última linha à do cabeçalho. Se você pular esse passo, a última linha fica sem
  fechamento. É o erro mais comum.

## Figuras e diagramas

- **Gráficos:** plotnine + `fgv_theme()`. Importe a paleta de `fgv_theme.py`. Sem
  título embutido no gráfico, a legenda da figura (`#| fig-cap`) cumpre esse papel.
- **Diagramas estruturais:** Graphviz via bloco `{dot}` (ver `diagramas.md`). Use
  a paleta FGV nas cores.
- Paleta: `FGV_AZUL` como primário, `FGV_AMARELO` para o segundo grupo,
  `FGV_VERMELHO` para algo negativo ou ausente. Use `PALETA_PRINCIPAL` para muitas
  categorias.
- `fig-dpi: 300`, fundo branco, grade só horizontal e discreta (já no tema).

## Identidade visual

- **Fonte:** Century Gothic, já configurada no `_reference-fgv.docx` (texto) e no
  `fgv_theme.py` (gráficos).
- **Cor primária:** azul FGV `#003a79`.
- O `_reference-fgv.docx` carrega os estilos de parágrafo, título e tabela. **Nunca**
  estilize manualmente o que o reference-doc já cobre.
