# cópia de plugins/relatorio/skills/relatorio/assets/fgv_theme.py — manter em sync
"""Paleta de cores e tema gráfico para relatórios LabDados, alinhados à FGV.

Cores extraídas da identidade visual institucional da FGV: azul `#003a79`
como primário, azul escuro e azul claro como apoio, amarelo discreto para
destaque e cinza neutro para texto. A tipografia usa Century Gothic, o
substituto geométrico mais próximo da fonte institucional (Gotham) e
disponível tanto no sistema quanto no matplotlib.

Gráficos não levam título embutido: a legenda da figura no relatório
cumpre esse papel. Títulos só fazem sentido em apresentações.
"""

from __future__ import annotations

import matplotlib

from plotnine import (
    element_blank,
    element_line,
    element_rect,
    element_text,
    theme,
    theme_minimal,
)

FGV_AZUL = "#003a79"
FGV_AZUL_ESCURO = "#002e61"
FGV_AZUL_CLARO = "#008bc9"
FGV_CIANO = "#0dcaf0"
FGV_AMARELO = "#ffc107"
FGV_CINZA = "#495057"
FGV_CINZA_CLARO = "#adb5bd"
FGV_VERMELHO = "#dc3545"
FGV_TEXTO = "#212529"

FONT_FAMILY = "Century Gothic"

PALETA_PRINCIPAL = [
    FGV_AZUL,
    FGV_AMARELO,
    FGV_AZUL_CLARO,
    FGV_CINZA,
    FGV_AZUL_ESCURO,
    FGV_CIANO,
    FGV_VERMELHO,
]

PALETA_DUPLA = {
    "Justiça Comum": FGV_AZUL,
    "Juizado Especial": FGV_AMARELO,
    "Com dados": FGV_AZUL,
    "Sem dados": FGV_VERMELHO,
    "TJSP": FGV_AZUL,
    "TRF3": FGV_AMARELO,
}

# Garante a fonte no backend do matplotlib usado pelo plotnine.
matplotlib.rcParams["font.family"] = "sans-serif"
matplotlib.rcParams["font.sans-serif"] = [FONT_FAMILY, "Segoe UI", "Arial", "DejaVu Sans"]
matplotlib.rcParams["figure.dpi"] = 300
matplotlib.rcParams["savefig.dpi"] = 300


def fgv_theme(base_size: int = 12, legend_position: str = "right"):
    """Tema plotnine alinhado à identidade visual da FGV.

    Sem título embutido, fundo branco, somente linhas de grade
    horizontais discretas, eixos em cinza, tipografia sem serifa.
    A posição da legenda é parametrizável; o padrão ``"right"`` funciona
    bem para a maioria dos gráficos, e ``"bottom"`` para os de barras
    horizontais com legenda curta.
    """
    return theme_minimal(base_size=base_size) + theme(
        text=element_text(family=FONT_FAMILY, color=FGV_TEXTO),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="white", color="white"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#e3e6ea", size=0.4),
        axis_line_x=element_line(color=FGV_CINZA, size=0.5),
        axis_line_y=element_blank(),
        axis_ticks=element_line(color=FGV_CINZA, size=0.3),
        axis_text=element_text(color=FGV_CINZA, size=base_size - 2),
        axis_title=element_text(color=FGV_TEXTO, size=base_size - 1),
        axis_title_x=element_text(margin={"t": 8}),
        axis_title_y=element_text(margin={"r": 8}),
        legend_position=legend_position,
        legend_title=element_text(color=FGV_TEXTO, size=base_size - 1),
        legend_text=element_text(color=FGV_CINZA, size=base_size - 2),
        legend_background=element_rect(fill="white", color="white"),
        legend_key=element_rect(fill="white", color="white"),
        legend_key_size=14,
        plot_caption=element_text(color=FGV_CINZA, size=base_size - 3, ha="right"),
        plot_margin=0.06,
    )


__all__ = [
    "FGV_AZUL",
    "FGV_AZUL_ESCURO",
    "FGV_AZUL_CLARO",
    "FGV_CIANO",
    "FGV_AMARELO",
    "FGV_CINZA",
    "FGV_CINZA_CLARO",
    "FGV_VERMELHO",
    "FGV_TEXTO",
    "FONT_FAMILY",
    "PALETA_PRINCIPAL",
    "PALETA_DUPLA",
    "fgv_theme",
]
