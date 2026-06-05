"""Gera as figuras do relatório institucional do LabDados (PNG 300 dpi) em fig/.

Paleta alinhada à identidade visual da FGV Direito SP / CEPI: azul-marinho como
base, com coral e verde-limão de apoio. Roda com o .venv do projeto (uv).

    python build_figs.py
"""
from __future__ import annotations
import os
from pathlib import Path

import pandas as pd
import graphviz
from plotnine import *
import matplotlib
matplotlib.rcParams["font.family"] = "sans-serif"
matplotlib.rcParams["font.sans-serif"] = ["Arial", "Segoe UI", "DejaVu Sans"]

# ---------------------------------------------------------------- paleta FGV/CEPI
NAVY = "#13294b"      # azul-marinho (base, capa, bandas)
AZUL = "#1b3a6b"      # azul institucional (títulos, barras)
AZUL_CLARO = "#4f7cc0"
CORAL = "#e0556a"     # vermelho coral (destaque)
LIME = "#a6ce39"      # verde-limão (acento)
CINZA = "#5b6470"
CINZA_CLARO = "#d8dde3"
TEXTO = "#1f2733"

FIG = Path(__file__).parent / "fig"
FIG.mkdir(exist_ok=True)


def _tema(base=12):
    return theme_minimal(base_size=base) + theme(
        text=element_text(family="Arial", color=TEXTO),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="white", color="white"),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color="#e7eaee", size=0.4),
        axis_ticks=element_blank(),
        axis_text=element_text(color=CINZA, size=base - 1),
        axis_title=element_blank(),
        legend_position="none",
        plot_margin=0.01,
    )


def salvar(p, nome, w, h):
    p.save(FIG / nome, width=w, height=h, dpi=300, verbose=False)
    print("ok", nome)


# ============================================================ 1. esforço por ferramenta
def fig_esforco():
    df = pd.DataFrame({
        "ferramenta": ["juscraper", "dataframeit", "dataframeitgui", "raspe",
                        "escritório de serviços", "LabDados SDK", "núcleo compartilhado",
                        "marketplace de skills"],
        "commits": [538, 195, 187, 95, 51, 24, 19, 10],
    })
    df["destaque"] = df["ferramenta"].eq("juscraper")
    df["ferramenta"] = pd.Categorical(df["ferramenta"],
                                      categories=df.sort_values("commits")["ferramenta"], ordered=True)
    p = (
        ggplot(df, aes("ferramenta", "commits", fill="destaque"))
        + geom_col(width=0.72)
        + geom_text(aes(label="commits"), ha="left", nudge_y=8, size=10,
                    color=TEXTO, format_string="{}")
        + scale_fill_manual({True: CORAL, False: AZUL})
        + coord_flip()
        + scale_y_continuous(expand=(0, 0, 0.12, 0))
        + _tema()
        + theme(panel_grid_major_x=element_blank(),
                axis_text_x=element_blank())
    )
    salvar(p, "esforco.png", 7.2, 3.4)


# ============================================================ 2. andamento do quadro
def fig_quadro():
    df = pd.DataFrame({
        "status": ["Concluído", "A fazer (backlog)", "Em andamento", "Em revisão", "Pronto"],
        "n": [45, 32, 6, 4, 4],
    })
    cores = {"Concluído": AZUL, "A fazer (backlog)": CINZA_CLARO, "Em andamento": LIME,
             "Em revisão": CORAL, "Pronto": AZUL_CLARO}
    df["status"] = pd.Categorical(df["status"], categories=df["status"][::-1], ordered=True)
    df["y"] = "itens"
    p = (
        ggplot(df, aes("y", "n", fill="status"))
        + geom_col(width=0.5, position=position_stack(reverse=True))
        + geom_text(aes(label="n"), position=position_stack(vjust=0.5, reverse=True),
                    size=11, color="white", fontweight="bold")
        + scale_fill_manual(cores)
        + coord_flip()
        + scale_y_continuous(expand=(0, 0))
        + labs(fill="")
        + _tema()
        + theme(legend_position="bottom", legend_title=element_blank(),
                panel_grid_major_x=element_blank(), axis_text=element_blank(),
                legend_text=element_text(size=10, color=CINZA))
    )
    salvar(p, "quadro.png", 7.2, 1.9)


# ============================================================ 3. evolução do juscraper
def fig_juscraper():
    rel = pd.DataFrame({
        "data": pd.to_datetime([
            "2025-07-19", "2025-07-20", "2025-11-29", "2025-12-28",
            "2026-03-31", "2026-03-31", "2026-04-09", "2026-04-13", "2026-05-03"]),
        "versao": ["0.1.0", "0.1.3", "0.1.4", "0.1.5", "0.1.6", "0.1.7",
                   "0.2.0", "0.2.1", "0.3.0"],
    }).reset_index(drop=True)
    rel["acum"] = range(1, len(rel) + 1)
    marcos = rel[rel["versao"].isin(["0.1.0", "0.2.0", "0.3.0"])]
    _mes_pt = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    brks = pd.to_datetime(["2025-09-01", "2025-11-01", "2026-01-01", "2026-03-01", "2026-05-01"])
    labs_pt = [f"{_mes_pt[d.month - 1]}/{str(d.year)[2:]}" for d in brks]
    p = (
        ggplot(rel, aes("data", "acum"))
        + geom_step(color=AZUL, size=1.1)
        + geom_point(color=AZUL, size=2.2)
        + geom_point(marcos, aes("data", "acum"), color=CORAL, size=3.6)
        + geom_text(marcos, aes("data", "acum", label="'v'+versao"),
                    va="bottom", ha="right", nudge_y=0.35, size=9, color=CORAL)
        + scale_y_continuous(breaks=range(0, 10, 2), expand=(0.02, 0, 0.12, 0))
        + scale_x_datetime(breaks=brks, labels=labs_pt)
        + _tema()
        + theme(panel_grid_major_y=element_line(color="#e7eaee", size=0.4))
    )
    salvar(p, "juscraper.png", 7.2, 2.8)


# ============================================================ 4. linha do tempo (vertical)
def fig_timeline():
    tl = pd.DataFrame({
        "ord": list(range(11, 0, -1)),
        "mes": ["abr/26", "abr/26", "abr/26", "mai/26", "mai/26", "mai/26",
                "mai/26", "mai/26", "jun/26", "jul/26", "ago/26"],
        "desc": [
            "Plano de trabalho e prioridades definidos",
            "Repositório de dados na Biblioteca da FGV (Dataverse)",
            "Palestra do Ministro Barroso, primeiro evento do laboratório",
            "juscraper na versão 0.3.0",
            "SDK e escritório de apoio em construção",
            "Parceria com o InternetLab aprovada pela Direção",
            "Workshop de Letramento em IA com turma lotada",
            "Contratação de nova pesquisadora",
            "Lançamento do escritório de apoio (previsto)",
            "Lançamento público do juscraper 1.0 (previsto)",
            "Semana de abertura e app do CAJU (previsto)",
        ],
        "status": ["Realizado"] * 8 + ["Previsto"] * 3,
    })
    tl["rotulo"] = tl["mes"] + "   ·   " + tl["desc"]
    spine = pd.DataFrame({"x": [0], "xe": [0], "y": [1], "ye": [11]})
    p = (
        ggplot()
        + geom_segment(spine, aes(x="x", xend="xe", y="y", yend="ye"), color=AZUL_CLARO, size=1)
        + geom_point(tl, aes(0, "ord", color="status"), size=4.5)
        + geom_text(tl, aes(0.18, "ord", label="rotulo"), ha="left", size=10, color=TEXTO)
        + scale_color_manual({"Realizado": AZUL, "Previsto": CORAL})
        + scale_x_continuous(limits=(-0.2, 9))
        + scale_y_continuous(limits=(0.5, 11.5))
        + labs(color="")
        + _tema()
        + theme(legend_position="top", legend_title=element_blank(),
                panel_grid_major_x=element_blank(), axis_text=element_blank(),
                legend_text=element_text(size=11, color=CINZA))
    )
    salvar(p, "timeline.png", 8.6, 5.4)


# ============================================================ 5/6. diagramas Graphviz
def fig_estrutura():
    """Árvore de iniciativas: LabDados -> frentes (proposta) -> projetos."""
    frentes = {
        "Mapeamento e\ncaptação de demandas": ["Diagnóstico\ninstitucional", "Dados abertos"],
        "Levantamento\nde literatura": ["Scoping review\nde IA"],
        "Capacitação": ["Letramento em IA", "Curso de\nprogramação", "Oficina Atlas.ti"],
        "Escritório de\napoio à pesquisa": ["Plataforma do\nescritório", "LabDados SDK"],
        "Projetos piloto": ["CCD Saúde", "Parceria\nInternetLab"],
        "Tecnologias\ne métodos": ["juscraper", "dataframeit", "raspe", "Marketplace\nde skills",
                                   "App do CAJU", "Revista\nDireito GV", "Eventos"],
    }
    g = graphviz.Digraph(format="png")
    g.attr(bgcolor="white", dpi="300", rankdir="LR", ranksep="0.9", nodesep="0.14",
           splines="ortho")
    g.node("root", "LabDados", shape="box", style="filled,rounded", fillcolor=NAVY,
           fontcolor="white", color=NAVY, fontname="Arial", fontsize="16",
           width="1.4", height="0.7")
    g.attr("edge", color=AZUL_CLARO, penwidth="1.1")
    for i, (fr, projs) in enumerate(frentes.items()):
        fn = f"F{i}"
        g.node(fn, fr, shape="box", style="filled,rounded", fillcolor=AZUL,
               fontcolor="white", color=AZUL, fontname="Arial", fontsize="12")
        g.edge("root", fn)
        for j, p in enumerate(projs):
            pn = f"F{i}_{j}"
            g.node(pn, p, shape="box", style="filled,rounded", fillcolor="#eef3f9",
                   fontcolor="#13294b", color="#9fb6d6", fontname="Arial", fontsize="11")
            g.edge(fn, pn)
    (FIG / "estrutura.png").write_bytes(g.pipe(format="png"))
    print("ok estrutura.png (árvore)")


def fig_entregas():
    fases = {
        "Fase 1 · Estruturação (M1 a M3)": [("E1 Mapeamento e literatura", True)],
        "Fase 2 · Ativação (M4 a M7)": [("E2 Capacitação", True), ("E3 Escritório de apoio", True),
                                        ("E6 Tecnologias e difusão", True),
                                        ("E7 Discussão metodológica", False)],
        "Fase 3 · Consolidação (M8 a M10)": [("E4 Pesquisa qualitativa", False),
                                             ("E5 Pesquisa quantitativa", False),
                                             ("E8 Mobilização", False),
                                             ("E9 Relatório consolidado", False)],
    }

    def caixa(titulo, ents):
        linhas = ""
        for e, feito in ents:
            if feito:
                linhas += (f'<tr><td align="left"><font point-size="11" color="#13294b">'
                           f'<b>&#9632; {e}</b></font></td></tr>')
            else:
                linhas += (f'<tr><td align="left"><font point-size="11" color="#8a94a3">'
                           f'&#9633; {e}</font></td></tr>')
        return ('<<table border="0" cellborder="0" cellspacing="3">'
                f'<tr><td align="center"><b><font point-size="12" color="#13294b">{titulo}</font></b></td></tr>'
                f'{linhas}</table>>')

    g = graphviz.Digraph(format="png")
    g.attr(bgcolor="white", dpi="300", rankdir="TB", nodesep="0.5", ranksep="0.4")
    g.attr("node", shape="box", style="filled,rounded", color=AZUL, fillcolor="#eef3f9",
           fontname="Arial")
    nomes = ["P1", "P2", "P3"]
    for n, (fase, ents) in zip(nomes, fases.items()):
        g.node(n, caixa(fase, ents))
    with g.subgraph() as s:
        s.attr(rank="same")
        for n in nomes:
            s.node(n)
    for a, b in zip(nomes, nomes[1:]):
        g.edge(a, b, style="invis")
    (FIG / "entregas.png").write_bytes(g.pipe(format="png"))
    print("ok entregas.png")


def fig_fluxo():
    """Fluxo de dados que liga os pacotes do laboratório, das fontes à entrega."""
    def caixa(titulo, itens, cor_titulo="#13294b"):
        linhas = "".join(
            f'<tr><td align="left"><font point-size="11" color="#1f2733">'
            f'{i.replace(chr(10), "<br/>")}</font></td></tr>'
            for i in itens)
        return ('<<table border="0" cellborder="0" cellspacing="3">'
                f'<tr><td align="center"><b><font point-size="12" color="{cor_titulo}">{titulo}</font></b></td></tr>'
                f'{linhas}</table>>')

    g = graphviz.Digraph(format="png")
    g.attr(bgcolor="white", dpi="300", rankdir="LR", nodesep="0.3", ranksep="0.55")
    g.attr("node", shape="box", style="filled,rounded", fontname="Arial",
           color=AZUL, fillcolor="#eef3f9")
    estagios = [
        ("Fontes de dados", ["Tribunais e\nPoder Judiciário", "Periódicos\ncientíficos",
                             "Documentos\ne áudios"]),
        ("Coleta", ["juscraper", "raspe"]),
        ("Estruturação com IA", ["LabDados SDK", "dataframeit"]),
        ("Análise e entrega", ["Pesquisas do lab", "Escritório de apoio"]),
    ]
    nomes = []
    for i, (tit, itens) in enumerate(estagios):
        n = f"S{i}"
        g.node(n, caixa(tit, itens))
        nomes.append(n)
    g.attr("edge", color=CORAL, penwidth="1.6", arrowsize="0.8")
    for a, b in zip(nomes, nomes[1:]):
        g.edge(a, b)
    # difusão: empacota e leva para fora do laboratório
    g.node("dif", caixa("Difusão", ["Marketplace\nde skills", "Revista\nDireito GV"],
                        cor_titulo="#13294b"),
           fillcolor="#f3f7ec", color=LIME)
    g.attr("edge", color=LIME, penwidth="1.4", style="dashed")
    g.edge("S2", "dif")
    (FIG / "fluxo.png").write_bytes(g.pipe(format="png"))
    print("ok fluxo.png")


if __name__ == "__main__":
    fig_timeline()
    fig_estrutura()
    fig_entregas()
    fig_fluxo()
    print("figuras em", FIG)
