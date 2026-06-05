// =====================================================================
//  Template Typst (FGV Direito SP / LabDados) para o Quarto.
//  Fonte única: o mesmo .qmd gera Word (reference-doc) e PDF (este template).
//  Tipografia de marca FGV: Frutiger (primária, licenciada) -> Source Sans 3
//  (livre, em fonts/) como aproximação. Compilar com TYPST_FONT_PATHS=fonts.
// =====================================================================

#let navy  = rgb("#13294b")
#let azul  = rgb("#1b3a6b")
#let azulc = rgb("#4f7cc0")
#let coral = rgb("#e0556a")
#let lime  = rgb("#a6ce39")
#let cinza = rgb("#5b6470")
#let cinzac = rgb("#e7eaee")
#let texto = rgb("#1f2733")

#let losango-band(n: 8, cell: 34pt, cores: (coral, lime, azul, navy)) = {
  box(height: cell)[
    #grid(columns: (cell,) * n,
      ..range(n).map(i => {
        let a = cores.at(calc.rem(i, cores.len()))
        let b = cores.at(calc.rem(i + 2, cores.len()))
        box(width: cell, height: cell)[
          #place(top + left, polygon(fill: a, (0pt, 0pt), (cell, 0pt), (0pt, cell)))
          #place(top + left, polygon(fill: b, (cell, 0pt), (cell, cell), (0pt, cell)))
        ]
      }))
  ]
}

// ---- caixa de destaque (redefine o callout do Quarto p/ funcionar nos 2 formatos) ----
#let callout(body: [], title: none, background_color: none, icon: none,
             icon_color: none, body_background_color: none) = {
  block(above: 18pt, below: 18pt, fill: rgb("#eef3f9"), inset: 13pt, radius: 4pt,
        width: 100%, stroke: (left: 3pt + azul), breakable: false)[
    #set par(first-line-indent: 0pt)
    #set text(size: 9.5pt, fill: texto)
    #body
  ]
}

// ---- chips das cinco frentes (uso em bloco raw {=typst}, só no PDF) ----
#let frente_chip(nome, cor, desc) = block(
  fill: cor.lighten(94%), stroke: (left: 3pt + cor), radius: 3pt, inset: 8pt,
  width: 100%, height: 2.6cm, breakable: false)[
  #set par(justify: false, spacing: 0pt, leading: 0.5em, first-line-indent: 0pt)
  #text(font: ("Source Sans 3",), weight: "bold", size: 9.5pt, fill: cor.darken(6%))[#nome]
  #v(5pt)
  #text(size: 7.5pt, fill: cinza)[#desc]
]
#let frentes_grid() = grid(columns: (1fr,) * 5, gutter: 7pt,
  frente_chip("Institucional", rgb("#1c3d5e"), "Eventos, parcerias e diagnóstico de demandas."),
  frente_chip("Formação", rgb("#2e7d64"), "Workshops e curso de programação para pesquisa."),
  frente_chip("Pesquisa", rgb("#6a51a3"), "Saúde, eleições e revisão de literatura com IA."),
  frente_chip("Escritório de apoio", rgb("#8c5a2b"), "Serviços de dados sob demanda para a Escola."),
  frente_chip("Tecnologias", rgb("#2a7d91"), "Pacotes próprios, marketplace e aplicações."),
)

// ---- agenda visual: cartões data + título + status + detalhe (uso em {=typst}) ----
#let agenda(itens) = {
  for it in itens {
    let cor = if it.status == "Realizado" { azul } else if it.status == "Em curso" { lime } else { coral }
    block(below: 8pt, breakable: false, width: 100%)[
      #grid(columns: (62pt, 1fr), gutter: 11pt, align: (horizon, horizon),
        block(fill: navy, radius: 4pt, inset: (y: 8pt), width: 100%)[
          #set par(first-line-indent: 0pt)
          #align(center, text(weight: "bold", size: 10.5pt, fill: white)[#it.data])
        ],
        block(inset: (y: 2pt))[
          #set par(first-line-indent: 0pt, spacing: 0.4em)
          #text(weight: "bold", size: 11pt, fill: navy)[#it.titulo]
          #h(6pt)
          #box(baseline: 1pt, fill: cor.lighten(72%), inset: (x: 5pt, y: 1.5pt), radius: 2pt)[
            #text(size: 7pt, fill: cor.darken(8%), weight: "bold")[#upper(it.status)]
          ]
          #linebreak()
          #text(size: 9pt, fill: cinza)[#it.detalhe]
        ],
      )
    ]
  }
}

// ---- cartões de skills coloridos por categoria (uso em {=typst}) ----
#let skill_card(nome, desc, cor) = block(
  fill: white, stroke: (left: 3pt + cor, rest: 0.7pt + cinzac), radius: 3pt, inset: 9pt,
  width: 100%, height: 2.5cm, breakable: false)[
  #set par(spacing: 0pt, leading: 0.5em, first-line-indent: 0pt)
  #text(weight: "bold", size: 10pt, fill: cor.darken(8%))[#nome]
  #v(3pt)
  #text(size: 7.3pt, fill: cinza)[#desc]
]
#let skills_grid(cards, legenda) = {
  block(below: 10pt)[
    #set par(first-line-indent: 0pt)
    #for l in legenda {
      box(baseline: 1.5pt, width: 8pt, height: 8pt, radius: 1.5pt, fill: l.cor)
      h(4pt)
      text(size: 8pt, fill: cinza)[#l.cat]
      h(16pt)
    }
  ]
  grid(columns: (1fr, 1fr, 1fr), gutter: 8pt, align: (top, top, top),
    ..cards.map(c => skill_card(c.nome, c.desc, c.cor)))
}

#let article(
  title: none,
  subtitle: none,
  lang: "pt",
  region: "BR",
  font: ("Source Sans 3",),
  fontsize: 10.5pt,
  toc: false,
  toc_title: none,
  toc_depth: 3,
  toc_indent: 1.5em,
  doc,
) = {
  let report-label = "RELATÓRIO DE ATIVIDADES E PRESTAÇÃO DE CONTAS"

  set document(title: if title != none { title } else { "LabDados" })
  set text(font: font, size: fontsize, lang: lang, region: region, fill: texto)
  set par(
    justify: true,
    leading: 0.78em,
    spacing: 1.25em,
    first-line-indent: (amount: 1.5em, all: false),
  )

  show link: set text(fill: coral)

  // ---- títulos ----
  show heading: set text(hyphenate: false)
  show heading.where(level: 1): it => block(above: 30pt, below: 18pt, sticky: true)[
    #set par(first-line-indent: 0pt)
    #text(font: font, weight: "bold", size: 21pt, fill: navy)[#it.body]
    #v(5pt)
    #line(length: 46pt, stroke: 2.4pt + lime)
  ]
  show heading.where(level: 2): it => block(above: 22pt, below: 11pt, sticky: true)[
    #set par(first-line-indent: 0pt)
    #text(font: font, weight: "bold", size: 13pt, fill: azul)[#it.body]
  ]
  show heading.where(level: 3): it => block(above: 16pt, below: 7pt, sticky: true)[
    #set par(first-line-indent: 0pt)
    #text(font: font, weight: "bold", size: 10.5pt, fill: navy)[#it.body]
  ]

  // ---- molduras nos screenshots da plataforma/ferramentas (pelo caminho) ----
  show image: it => {
    let p = it.source
    if ("servico-" in p) or ("juscraper-app" in p) or ("escritorio" in p) {
      block(stroke: 0.6pt + cinzac, radius: 3pt, clip: true, it)
    } else { it }
  }

  // ---- figuras ----
  show figure: set block(above: 18pt, below: 18pt)
  show figure.caption: it => {
    set text(size: 8.5pt, fill: cinza)
    set par(first-line-indent: 0pt)
    it
  }

  // ---- tabelas ----
  set table(stroke: none, inset: 7pt,
    fill: (_, y) => if y == 0 { navy } else if calc.even(y) { rgb("#f3f5f8") } else { white })
  show table.cell.where(y: 0): set text(fill: white, weight: "bold")
  show table: set text(size: 9.5pt)

  // ---- citações de destaque (pull quotes) a partir de blockquotes ----
  show quote: it => block(above: 20pt, below: 20pt, width: 100%, inset: (x: 14pt), breakable: false)[
    #set par(first-line-indent: 0pt, justify: false, leading: 0.6em)
    #grid(columns: (auto, 1fr), column-gutter: 12pt, align: (top + left, horizon),
      text(font: font, size: 46pt, fill: lime.darken(4%), weight: "bold", baseline: 14pt)[\u{201C}],
      text(size: 15pt, fill: navy, style: "italic")[#it.body])
  ]

  // =================================================================
  //  CAPA
  // =================================================================
  set page(width: 210mm, height: 297mm, margin: 0pt, fill: navy)
  block(width: 100%, height: 100%, inset: (x: 34pt, top: 42pt, bottom: 40pt))[
    #set par(first-line-indent: 0pt)
    #align(right)[
      #text(font: font, weight: "bold", size: 17pt, fill: white, tracking: 1pt)[FGV DIREITO SP]
      #v(-5pt)
      #text(font: font, size: 7.5pt, fill: azulc, tracking: 1pt)[
        LABORATÓRIO DE DADOS E PESQUISA EMPÍRICA EM DIREITO]
    ]
    #v(34pt)
    #losango-band(n: 8, cell: 34pt)
    #v(150pt)
    #text(font: font, weight: "bold", size: 40pt, fill: white)[
      RELATÓRIO DE\ ATIVIDADES E\ PRESTAÇÃO DE CONTAS]
    #v(8pt)
    #text(font: font, size: 18pt, fill: rgb("#cdd8ea"))[
      Laboratório de Dados e Pesquisa Empírica em Direito]
    #v(1fr)
    #line(length: 36pt, stroke: 2.4pt + lime)
    #v(4pt)
    #text(font: font, weight: "bold", size: 11pt, fill: white, tracking: 1.5pt)[
      RELATÓRIO INSTITUCIONAL  ·  DO INÍCIO ATÉ MAIO DE 2026]
  ]

  // =================================================================
  //  CORPO
  // =================================================================
  set page(
    width: 210mm, height: 297mm, fill: white,
    margin: (x: 2.2cm, top: 2.3cm, bottom: 1.8cm),
    header: context {
      if counter(page).get().first() > 1 [
        #set text(size: 7.5pt, fill: cinza)
        #grid(columns: (1fr, auto),
          align(left)[#text(fill: navy, weight: "bold")[LabDados] · #report-label],
          align(right)[FGV Direito SP])
        #v(4pt)
        #line(length: 100%, stroke: 0.6pt + cinzac)
      ]
    },
    footer: context {
      set text(size: 8pt, fill: cinza)
      line(length: 100%, stroke: 0.6pt + cinzac)
      v(4pt)
      grid(columns: (1fr, auto),
        align(left)[Laboratório de Dados e Pesquisa Empírica em Direito · FGV Direito SP],
        align(right)[#counter(page).display()])
    },
  )
  counter(page).update(1)

  if toc {
    block(above: 0pt, below: 20pt)[
      #text(font: font, weight: "bold", size: 21pt, fill: navy)[#if toc_title != none { toc_title } else { "Sumário" }]
      #v(4pt)
      #line(length: 46pt, stroke: 2.4pt + lime)
      #v(12pt)
      #outline(title: none, depth: toc_depth, indent: toc_indent)
    ]
    pagebreak(weak: true)
  }

  doc
}
