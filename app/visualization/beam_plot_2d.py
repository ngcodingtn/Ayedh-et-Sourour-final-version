"""Visualisation 2D de la poutre et des sollicitations – matplotlib.

Dessine :
  - la poutre avec appuis et consoles
  - les charges réparties et ponctuelles
  - les réactions d'appui
  - les diagrammes V(x) et M(x)
  - la position x sélectionnée
  - export PNG
"""
from __future__ import annotations

import os
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.figure import Figure

from app.models.load_models import DonneesPoutre
from app.models.result_models import ResultatSollicitations


def draw_beam_2d(
    fig: Figure,
    poutre: DonneesPoutre,
    resultats: Optional[ResultatSollicitations] = None,
    x_selected: Optional[float] = None,
    mode: str = "vue_complete",
    combinaison: str = "ELU",
):
    """Dessine la vue 2D complète dans une figure matplotlib.

    Args:
        fig: figure matplotlib.
        poutre: données de la poutre.
        resultats: résultats de calcul (optionnel).
        x_selected: position x sélectionnée (mm).
        mode: "schema_poutre", "diagrammes", "vue_complete".
        combinaison: combinaison utilisée.
    """
    fig.clear()

    L = poutre.longueur_totale_mm
    xA = poutre.position_appui_A_mm
    xB = poutre.position_appui_B_mm

    if mode == "diagrammes" and resultats is not None:
        axes = fig.subplots(2, 1, gridspec_kw={"hspace": 0.35})
        draw_shear_diagram_2d(axes[0], resultats, x_selected)
        draw_moment_diagram_2d(axes[1], resultats, x_selected)
        return

    if mode == "schema_poutre":
        ax = fig.add_subplot(111)
        _draw_beam_schema(ax, poutre, resultats, x_selected, combinaison)
        return

    # Vue complète : poutre + diagrammes
    axes = fig.subplots(3, 1, gridspec_kw={"height_ratios": [2, 1.5, 1.5], "hspace": 0.35})
    _draw_beam_schema(axes[0], poutre, resultats, x_selected, combinaison)

    if resultats is not None:
        draw_shear_diagram_2d(axes[1], resultats, x_selected)
        draw_moment_diagram_2d(axes[2], resultats, x_selected)
    else:
        axes[1].set_visible(False)
        axes[2].set_visible(False)


def _draw_beam_schema(ax, poutre, resultats, x_selected, combinaison):
    """Dessine le schéma de la poutre avec charges et réactions."""
    L = poutre.longueur_totale_mm
    xA = poutre.position_appui_A_mm
    xB = poutre.position_appui_B_mm
    y_beam = 0.0
    beam_h = L * 0.015  # épaisseur visuelle

    # Marges
    margin = L * 0.05
    ax.set_xlim(-margin, L + margin)
    ax.set_ylim(-L * 0.3, L * 0.3)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("Position (mm)")
    ax.set_title(f"Schéma de la poutre – {combinaison}", fontsize=11, fontweight="bold")

    # Poutre
    rect = patches.Rectangle((0, y_beam - beam_h / 2), L, beam_h,
                               linewidth=2, edgecolor="#2B6CB0", facecolor="#EBF8FF")
    ax.add_patch(rect)

    # Appuis
    draw_supports_2d(ax, xA, xB, y_beam, L)

    # Charges réparties
    draw_distributed_loads_2d(ax, poutre, y_beam, L, combinaison)

    # Charges ponctuelles
    draw_point_loads_2d(ax, poutre, y_beam, L, combinaison)

    # Réactions
    if resultats is not None:
        draw_reactions_2d(ax, xA, xB, resultats.RA, resultats.RB, y_beam, L)

    # Position x sélectionnée
    if x_selected is not None:
        draw_selected_x_marker(ax, x_selected, y_beam, L, resultats)

    # Annotations de positions
    ax.annotate("0", (0, y_beam - L * 0.06), ha="center", fontsize=8, color="gray")
    ax.annotate(f"{L:.0f}", (L, y_beam - L * 0.06), ha="center", fontsize=8, color="gray")
    if xA > 0:
        ax.annotate(f"A={xA:.0f}", (xA, y_beam - L * 0.06), ha="center", fontsize=8, color="#2B6CB0")
    if xB < L:
        ax.annotate(f"B={xB:.0f}", (xB, y_beam - L * 0.06), ha="center", fontsize=8, color="#2B6CB0")

    ax.axhline(y=y_beam, color="lightgray", linewidth=0.5, zorder=0)
    ax.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def draw_supports_2d(ax, xA, xB, y_beam, L):
    """Dessine les appuis (triangles)."""
    support_h = L * 0.04
    support_w = L * 0.03

    for x_sup in [xA, xB]:
        triangle = plt.Polygon([
            (x_sup, y_beam - L * 0.015),
            (x_sup - support_w, y_beam - support_h),
            (x_sup + support_w, y_beam - support_h),
        ], closed=True, facecolor="#276749", edgecolor="#276749", zorder=5)
        ax.add_patch(triangle)


def draw_distributed_loads_2d(ax, poutre, y_beam, L, combinaison):
    """Dessine les charges réparties (flèches vers le bas)."""
    from app.core.beam_loads import _combine_factor
    gamma_G, gamma_Q = _combine_factor(combinaison, poutre.psi_1, poutre.psi_2)
    w = gamma_G * poutre.g_N_mm + gamma_Q * poutre.q_N_mm

    if w <= 0:
        return

    arrow_spacing = L / 20
    arrow_len = L * 0.06
    y_top = y_beam + arrow_len + L * 0.02

    for i in range(21):
        x_pos = i * arrow_spacing
        if x_pos <= L:
            ax.annotate("", xy=(x_pos, y_beam + L * 0.015),
                        xytext=(x_pos, y_top),
                        arrowprops=dict(arrowstyle="->", color="#C53030", lw=1.2))

    # Ligne horizontale en haut
    ax.plot([0, L], [y_top, y_top], color="#C53030", linewidth=1.5)

    # Label
    ax.text(L / 2, y_top + L * 0.015, f"w = {w:.2f} N/mm",
            ha="center", fontsize=9, color="#C53030", fontweight="bold")


def draw_point_loads_2d(ax, poutre, y_beam, L, combinaison):
    """Dessine les charges ponctuelles."""
    from app.core.beam_loads import _combine_factor
    gamma_G, gamma_Q = _combine_factor(combinaison, poutre.psi_1, poutre.psi_2)

    arrow_len = L * 0.1

    for cc in poutre.charges_concentrees:
        F = gamma_G * cc.G_N + gamma_Q * cc.Q_N
        if F == 0:
            continue

        y_top = y_beam + arrow_len + L * 0.04
        ax.annotate("", xy=(cc.position_mm, y_beam + L * 0.015),
                    xytext=(cc.position_mm, y_top),
                    arrowprops=dict(arrowstyle="-|>", color="#C05621", lw=2))
        ax.text(cc.position_mm, y_top + L * 0.01, f"{F/1000:.1f} kN",
                ha="center", fontsize=9, color="#C05621", fontweight="bold")


def draw_reactions_2d(ax, xA, xB, RA, RB, y_beam, L):
    """Dessine les réactions d'appui (flèches vers le haut)."""
    arrow_len = L * 0.08

    for x_pos, R, label in [(xA, RA, "RA"), (xB, RB, "RB")]:
        ax.annotate("", xy=(x_pos, y_beam - L * 0.015),
                    xytext=(x_pos, y_beam - arrow_len),
                    arrowprops=dict(arrowstyle="-|>", color="#276749", lw=2))
        ax.text(x_pos, y_beam - arrow_len - L * 0.02, f"{label} = {R/1000:.1f} kN",
                ha="center", fontsize=9, color="#276749", fontweight="bold")


def draw_selected_x_marker(ax, x_sel, y_beam, L, resultats=None):
    """Dessine le marqueur de la position x sélectionnée."""
    ax.axvline(x=x_sel, color="#E53E3E", linestyle="--", linewidth=1.5, zorder=3)

    txt = f"x = {x_sel:.0f} mm"
    if resultats is not None:
        from app.core.beam_loads import compute_shear_at_x, compute_moment_at_x
        txt += f"\nV = {resultats.Vx/1000:.1f} kN"
        txt += f"\nM = {resultats.Mx/1e6:.2f} kN·m"

    ax.text(x_sel + L * 0.01, y_beam + L * 0.15, txt,
            fontsize=8, color="#E53E3E", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#E53E3E", alpha=0.9))


def draw_shear_diagram_2d(ax, resultats: ResultatSollicitations, x_selected=None):
    """Dessine le diagramme de l'effort tranchant."""
    if not resultats.x_values or not resultats.V_values:
        return

    x_vals = resultats.x_values
    V_vals = [v / 1000 for v in resultats.V_values]  # en kN

    ax.fill_between(x_vals, V_vals, 0, alpha=0.3, color="#2B6CB0")
    ax.plot(x_vals, V_vals, color="#2B6CB0", linewidth=1.5)
    ax.axhline(y=0, color="gray", linewidth=0.5)
    ax.set_ylabel("V (kN)")
    ax.set_xlabel("Position (mm)")
    ax.set_title(f"Effort tranchant – {resultats.combinaison}", fontsize=10, fontweight="bold")
    ax.grid(True, alpha=0.3)

    if x_selected is not None:
        vx = resultats.Vx / 1000
        ax.axvline(x=x_selected, color="#E53E3E", linestyle="--", linewidth=1.0)
        ax.plot(x_selected, vx, "ro", markersize=6)
        ax.annotate(f"{vx:.1f} kN", (x_selected, vx),
                    textcoords="offset points", xytext=(10, 5), fontsize=8, color="#E53E3E")


def draw_moment_diagram_2d(ax, resultats: ResultatSollicitations, x_selected=None):
    """Dessine le diagramme du moment fléchissant."""
    if not resultats.x_values or not resultats.M_values:
        return

    x_vals = resultats.x_values
    M_vals = [m / 1e6 for m in resultats.M_values]  # en kN·m

    ax.fill_between(x_vals, M_vals, 0, alpha=0.3, color="#C05621")
    ax.plot(x_vals, M_vals, color="#C05621", linewidth=1.5)
    ax.axhline(y=0, color="gray", linewidth=0.5)
    ax.set_ylabel("M (kN·m)")
    ax.set_xlabel("Position (mm)")
    ax.set_title(f"Moment fléchissant – {resultats.combinaison}", fontsize=10, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.invert_yaxis()  # Convention : moments positifs vers le bas

    if x_selected is not None:
        mx = resultats.Mx / 1e6
        ax.axvline(x=x_selected, color="#E53E3E", linestyle="--", linewidth=1.0)
        ax.plot(x_selected, mx, "ro", markersize=6)
        ax.annotate(f"{mx:.2f} kN·m", (x_selected, mx),
                    textcoords="offset points", xytext=(10, 5), fontsize=8, color="#E53E3E")


def export_beam_2d_png(
    poutre: DonneesPoutre,
    resultats: Optional[ResultatSollicitations],
    filepath: str,
    x_selected: Optional[float] = None,
    mode: str = "vue_complete",
    combinaison: str = "ELU",
    dpi: int = 150,
):
    """Exporte la vue 2D en fichier PNG."""
    fig = Figure(figsize=(14, 10), dpi=dpi)
    draw_beam_2d(fig, poutre, resultats, x_selected, mode, combinaison)
    fig.savefig(filepath, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
