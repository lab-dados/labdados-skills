# Diagramas que estruturam as atividades

O relatório traz três diagramas. Eles existem para a diretoria enxergar a
estrutura do laboratório de relance: como o trabalho se organiza, o que já foi
entregue e a evolução no tempo.

1. **Estrutura de frentes e projetos:** as seis frentes, cada uma com seus projetos.
2. **Mapa de entregas E1 a E9:** as entregas do ciclo agrupadas por fase.
3. **Linha do tempo:** marcos do projeto, do início aos próximos previstos.

> **Código canônico no template.** A versão que funciona dos três diagramas vive em
> `assets/relatorio_template.qmd`, já testada. Use-a como ponto de partida. Dois cuidados
> aprendidos na prática, que o template já incorpora:
>
> - **Estrutura de frentes:** monte cada frente como uma **caixa única** (título +
>   lista de projetos, via rótulo HTML do Graphviz) e arrume as seis caixas numa **grade
>   2 x 3** (com `rank="same"` por linha e arestas invisíveis). Não use um nó por projeto
>   solto nem encadeie clusters com arestas invisíveis: a primeira opção vira uma faixa
>   larguíssima e ilegível, a segunda distorce os clusters.
> - **Linha do tempo:** faça **vertical** (marcos empilhados de cima para baixo, rótulo
>   "mês · descrição" à direita de cada ponto, cor por status realizado/previsto). A
>   versão horizontal sobrepõe os rótulos quando os marcos se concentram nos primeiros
>   meses. O texto abaixo descreve a ideia geral; o código atual está no template.

## Método primário: Graphviz pelo pacote Python (sem browser)

Os dois primeiros diagramas são estruturais e saem melhor em Graphviz. O bloco
nativo ```{dot}``` do Quarto funciona, mas para gerar PNG no docx ele depende do
Chrome ou Edge. Para não depender de browser e ter um PNG nítido, **renderize com o
pacote Python `graphviz`** (que chama o binário `dot` direto) dentro de um chunk
`{python}`, e embuta a imagem com `IPython.display.Image`. Isso embute um PNG raster
no docx, igual a um gráfico do plotnine.

Pré-requisitos: `pip install graphviz` mais o binário do Graphviz instalado (o
comando `dot` no PATH). Em Windows: instalar o Graphviz e garantir o `dot`.

### Diagrama 1: estrutura por frentes

```{python}
#| label: fig-frentes
#| fig-cap: "Estrutura do LabDados e suas seis frentes de atuação."
import graphviz
from IPython.display import Image
from fgv_theme import FGV_AZUL, FGV_AZUL_CLARO

g = graphviz.Digraph(format="png")
g.attr(rankdir="LR", bgcolor="white", dpi="300")
g.attr("node", shape="box", style="filled,rounded", fontname="Century Gothic",
       color=FGV_AZUL, fillcolor=FGV_AZUL, fontcolor="white")
g.node("hub", "LabDados")
g.attr("node", fillcolor=FGV_AZUL_CLARO, fontcolor="#003a79", color=FGV_AZUL_CLARO)
frentes = [
    "Mapeamento e demandas",
    "Levantamento de literatura",
    "Capacitação",
    "Escritório de apoio",
    "Projetos piloto",
    "Tecnologia e métodos",
]
for i, f in enumerate(frentes):
    g.node(f"f{i}", f)
    g.edge("hub", f"f{i}", color=FGV_AZUL)
Image(g.pipe(format="png"), format="png")
```

### Diagrama 3: mapa de entregas E1 a E9 por fase

```{python}
#| label: fig-entregas
#| fig-cap: "Entregas do ciclo (E1 a E9) agrupadas pelas três fases do projeto."
import graphviz
from IPython.display import Image
from fgv_theme import FGV_AZUL, FGV_AMARELO, FGV_AZUL_CLARO

g = graphviz.Digraph(format="png")
g.attr(rankdir="LR", bgcolor="white", dpi="300", compound="true")
g.attr("node", shape="box", style="filled,rounded", fontname="Century Gothic",
       fontcolor="#003a79", color=FGV_AZUL_CLARO, fillcolor=FGV_AZUL_CLARO)

fases = {
    "Fase 1 (M1 a M3)": ["E1 Mapeamento e literatura"],
    "Fase 2 (M4 a M7)": ["E2 Capacitação", "E3 Escritório de pesquisa",
                          "E6 Tecnologias e difusão", "E7 Discussão metodológica"],
    "Fase 3 (M8 a M10)": ["E4 Piloto qualitativo", "E5 Piloto quantitativo",
                          "E8 Mobilização", "E9 Relatório consolidado"],
}
for fase, entregas in fases.items():
    with g.subgraph(name=f"cluster_{fase}") as c:
        c.attr(label=fase, style="filled", color=FGV_AMARELO, fillcolor="white",
               fontname="Century Gothic", fontcolor="#003a79")
        for e in entregas:
            c.node(e, e)
Image(g.pipe(format="png"), format="png")
```

Marque cada entrega já concluída mudando `fillcolor` para `FGV_AZUL` e
`fontcolor="white"` no node correspondente. Assim o diagrama mostra, de relance, o
que já foi feito e o que está por vir.

## Diagrama 2: linha do tempo (plotnine)

A linha do tempo sai melhor em plotnine, consistente com o template. Use
`geom_segment` para as fases e `geom_point` para os marcos.

```{python}
#| label: fig-timeline
#| fig-cap: "Linha do tempo do LabDados: fases e principais marcos."
#| fig-width: 8
#| fig-height: 3.5
import pandas as pd
from plotnine import (ggplot, aes, geom_segment, geom_point, geom_text,
                      scale_x_continuous, labs)
from fgv_theme import FGV_AZUL, FGV_AMARELO, fgv_theme

fases = pd.DataFrame({
    "fase": ["Estruturação", "Ativação", "Consolidação"],
    "ini":  [1, 4, 8],
    "fim":  [3, 7, 10],
    "y":    [1, 1, 1],
})
# Preencha os marcos com base nas fontes (releases, eventos, atas):
marcos = pd.DataFrame({
    "mes":   [3, 5, 9],
    "y":     [1, 1, 1],
    "label": ["marco A", "marco B", "marco C"],
})
(
    ggplot()
    + geom_segment(fases, aes(x="ini", xend="fim", y="y", yend="y"),
                   color=FGV_AZUL, size=6)
    + geom_point(marcos, aes(x="mes", y="y"), color=FGV_AMARELO, size=4)
    + geom_text(marcos, aes(x="mes", y="y", label="label"),
                va="bottom", nudge_y=0.05, size=8)
    + scale_x_continuous(breaks=range(1, 11), limits=(0.5, 10.5))
    + labs(x="Mês do projeto", y="")
    + fgv_theme(legend_position="none")
)
```

## Fallback sem Graphviz

Se o binário `dot` não estiver disponível e não der para instalar, não pare. Troque os
dois diagramas estruturais por **tabelas estruturadas** em Markdown:

- Estrutura por frentes: tabela frente, responsável, foco.
- Mapa de entregas: tabela fase, entrega, situação (concluída, em andamento, planejada).

A linha do tempo em plotnine não depende de Graphviz e continua funcionando. Registre
no relatório, com honestidade, que os diagramas estruturais saíram como tabela por
falta do Graphviz nesta execução.

## Observações

- `fgv_theme.py` precisa estar ao lado do `.qmd` para os `import` funcionarem (a skill
  copia o arquivo para a pasta de trabalho).
- As cores `FGV_AZUL`, `FGV_AZUL_CLARO`, `FGV_AMARELO` vêm de `fgv_theme.py` e mantêm os
  diagramas dentro da identidade visual da FGV.
