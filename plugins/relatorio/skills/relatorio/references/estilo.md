# Estilo dos relatórios LabDados

Guia de escrita e formatação. O objetivo é um documento que um leitor técnico
(pesquisador, coordenador, parceiro institucional) leia rápido e confie.

## Escrita

- **Português, formal, direto.** Sem floreio, sem "neste relatório iremos".
  Frases curtas. Voz ativa.
- **Resumo autossuficiente.** O primeiro parágrafo entrega o essencial: o que
  foi feito, os números-chave, a conclusão. Quem ler só ele não fica perdido.
- **Número sempre com referência.** Toda afirmação quantitativa aponta para uma
  tabela (`@tbl-...`) ou figura (`@fig-...`). Não solte número órfão no texto.
- **Não narre a tabela.** Em vez de repetir as células em prosa, comente o que
  elas mostram e por que importa.
- **Honestidade sobre limitações.** Vieses conhecidos, lacunas de cobertura e
  ressalvas vão no texto, não escondidos. É o que dá credibilidade.
- **Números em português:** milhar com ponto (`3.357.449`), decimal com vírgula
  (`98,9%`). Datas por extenso ou ISO conforme o contexto, consistentes.

## Estrutura típica

Resumo → Contexto/objetivo → Métodos/dados → Resultados → Conclusões →
Próximas etapas. Para relatórios mais longos, agrupe resultados em subseções
temáticas. Use `number-sections: false` (o padrão do template) — os títulos já
orientam.

## Tabelas

- Escreva em **pipe tables** Markdown ou gere com
  `Markdown(df.to_markdown(index=False))` num chunk `{python}`.
- Alinhe números à direita (`---:` na linha separadora).
- **Legenda** abaixo, com `{#tbl-rotulo}` para cross-reference.
- **Não desenhe bordas manualmente.** O stroke da última linha é aplicado pelo
  pós-processamento (`scripts/fix_docx_tables.py`), que iguala a borda inferior
  da última linha à do cabeçalho. Se você pular esse passo, a última linha fica
  sem fechamento — é o erro mais comum.

## Figuras

- **plotnine + `fgv_theme()`.** Importe a paleta de `fgv_theme.py`.
- **Sem título embutido** no gráfico: a legenda da figura (`#| fig-cap`) é o
  título. Título dentro do gráfico só em apresentação.
- Paleta: `FGV_AZUL` como primário, `FGV_AMARELO` para o segundo grupo,
  `FGV_VERMELHO` para "negativo/sem dados". Use `PALETA_PRINCIPAL` para muitas
  categorias.
- `fig-dpi: 300`, fundo branco, grade só horizontal e discreta (já no tema).
- Barras horizontais com legenda curta → `fgv_theme(legend_position="bottom")`.

## Identidade visual

- **Fonte:** Century Gothic (substituto geométrico do Gotham institucional). Já
  configurada no `_reference-fgv.docx` (texto) e no `fgv_theme.py` (gráficos).
- **Cor primária:** azul FGV `#003a79`.
- O `_reference-fgv.docx` carrega os estilos de parágrafo, título e tabela.
  **Nunca** estilize manualmente o que o reference-doc já cobre.
