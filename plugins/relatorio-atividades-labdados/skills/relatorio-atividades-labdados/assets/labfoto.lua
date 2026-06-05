-- Filtro Quarto: layout "texto à esquerda + foto à direita" só no Typst (PDF),
-- sem duplicar o texto. No Word, devolve só os parágrafos (a foto entra à parte).
-- Uso no .qmd:
--   ::: {.labfoto img="fig/x.jpg" cap="Legenda."}
--   parágrafos...
--   :::
function Div(el)
  -- bloco de logo de parceiro: no Typst vira um bloco "sticky" (rótulo + logo
  -- seguem o parágrafo seguinte, evitando título órfão no fim da página).
  if el.classes:includes("parceiro") then
    if quarto.doc.is_format("typst") then
      local blocks = pandoc.List()
      blocks:insert(pandoc.RawBlock("typst",
        "#block(sticky: true, below: 14pt)[\n" ..
        "#set text(size: 7.5pt, fill: cinza, weight: \"semibold\", tracking: 0.6pt)\n" ..
        "#set par(spacing: 3pt, first-line-indent: 0pt, leading: 0.4em)\n"))
      blocks:extend(el.content)
      blocks:insert(pandoc.RawBlock("typst", "]"))
      return blocks
    else
      return el.content
    end
  end
  if el.classes:includes("labfoto") then
    if quarto.doc.is_format("typst") then
      local img = el.attributes["img"] or ""
      local cap = el.attributes["cap"] or ""
      local open = pandoc.RawBlock("typst",
        '#grid(columns: (1.04fr, 0.96fr), column-gutter: 20pt, align: (top, top), [')
      local close = pandoc.RawBlock("typst",
        '], [#box(width: 100%, height: 13.5cm, clip: true, radius: 4pt, image("' .. img ..
        '", width: 100%, height: 100%, fit: "cover"))\n' ..
        '#v(3pt)\n#block(text(size: 8pt, fill: rgb("#5b6470"), style: "italic")[' .. cap .. '])])\n')
      local blocks = pandoc.List()
      blocks:insert(open)
      blocks:extend(el.content)
      blocks:insert(close)
      return blocks
    else
      return el.content
    end
  end
end
