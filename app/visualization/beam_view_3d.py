"""Visualisation 3D de la poutre et des sollicitations – matplotlib 3D.

Vue 3D de la poutre avec :
  - géométrie extrudée
  - appuis
  - charges réparties et ponctuelles
  - réactions
  - position x sélectionnée
  - modes : structure, charges, sollicitations, vue complète
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from app.models.load_models import DonneesPoutre
from app.models.result_models import ResultatSollicitations


def build_beam_3d(
    ax,
    poutre: DonneesPoutre,
    section_width: float = 300.0,
    section_height: float = 500.0,
):
    """Dessine la poutre 3D (parallélépipède)."""
    L = poutre.longueur_totale_mm
    w = section_width
    h = section_height

    # Sommets du parallélépipède
    vertices = np.array([
        [0, -w/2, 0], [L, -w/2, 0], [L, w/2, 0], [0, w/2, 0],
        [0, -w/2, h], [L, -w/2, h], [L, w/2, h], [0, w/2, h],
    ])

    faces = [
        [vertices[0], vertices[1], vertices[5], vertices[4]],  # face avant
        [vertices[2], vertices[3], vertices[7], vertices[6]],  # face arrière
        [vertices[0], vertices[3], vertices[7], vertices[4]],  # face gauche
        [vertices[1], vertices[2], vertices[6], vertices[5]],  # face droite
        [vertices[0], vertices[1], vertices[2], vertices[3]],  # face inférieure
        [vertices[4], vertices[5], vertices[6], vertices[7]],  # face supérieure
    ]

    collection = Poly3DCollection(faces, alpha=0.3, facecolor="#4299E1",
                                   edgecolor="#2B6CB0", linewidth=0.5)
    ax.add_collection3d(collection)


def build_supports_3d(ax, poutre: DonneesPoutre, section_width: float = 300.0):
    """Dessine les appuis en 3D (pyramides)."""
    xA = poutre.position_appui_A_mm
    xB = poutre.position_appui_B_mm
    w = section_width
    s = w * 0.4  # taille de la base du triangle
    sh = w * 0.3  # hauteur du support

    for x_sup in [xA, xB]:
        # Pyramide inversée
        apex = np.array([x_sup, 0, -sh])
        base = np.array([
            [x_sup - s, -s, 0],
            [x_sup + s, -s, 0],
            [x_sup + s, s, 0],
            [x_sup - s, s, 0],
        ])

        faces_support = []
        for i in range(4):
            j = (i + 1) % 4
            faces_support.append([base[i], base[j], apex])

        # Base
        faces_support.append(base.tolist())

        coll = Poly3DCollection(faces_support, alpha=0.6, facecolor="#48BB78",
                                 edgecolor="#276749", linewidth=0.5)
        ax.add_collection3d(coll)


def build_distributed_loads_3d(
    ax, poutre: DonneesPoutre, section_height: float = 500.0,
    combinaison: str = "ELU",
):
    """Dessine les charges réparties en 3D."""
    from app.core.beam_loads import _combine_factor
    gamma_G, gamma_Q = _combine_factor(combinaison, poutre.psi_1, poutre.psi_2)
    w = gamma_G * poutre.g_N_mm + gamma_Q * poutre.q_N_mm

    if w <= 0:
        return

    L = poutre.longueur_totale_mm
    n_arrows = 15
    arrow_len = section_height * 0.4

    for i in range(n_arrows + 1):
        x_pos = i * L / n_arrows
        z_top = section_height + arrow_len
        ax.plot([x_pos, x_pos], [0, 0], [section_height, z_top],
                color="#E53E3E", linewidth=1.0)
        # Pointe de flèche (petite ligne)
        ax.plot([x_pos, x_pos], [0, 0], [section_height, section_height + arrow_len * 0.15],
                color="#E53E3E", linewidth=2.0)


def build_point_loads_3d(
    ax, poutre: DonneesPoutre, section_height: float = 500.0,
    combinaison: str = "ELU",
):
    """Dessine les charges ponctuelles en 3D."""
    from app.core.beam_loads import _combine_factor
    gamma_G, gamma_Q = _combine_factor(combinaison, poutre.psi_1, poutre.psi_2)

    arrow_len = section_height * 0.6

    for cc in poutre.charges_concentrees:
        F = gamma_G * cc.G_N + gamma_Q * cc.Q_N
        if F == 0:
            continue

        z_top = section_height + arrow_len
        ax.plot([cc.position_mm, cc.position_mm], [0, 0], [section_height, z_top],
                color="#C05621", linewidth=2.5)
        ax.text(cc.position_mm, 0, z_top + 20, f"{F/1000:.1f} kN",
                fontsize=8, color="#C05621", ha="center")


def build_reactions_3d(
    ax, poutre: DonneesPoutre,
    RA: float, RB: float,
    section_width: float = 300.0,
):
    """Dessine les réactions d'appui en 3D."""
    arrow_len = section_width * 0.5
    xA = poutre.position_appui_A_mm
    xB = poutre.position_appui_B_mm

    for x_pos, R, label in [(xA, RA, "RA"), (xB, RB, "RB")]:
        ax.plot([x_pos, x_pos], [0, 0], [-arrow_len, 0],
                color="#276749", linewidth=2.5)
        ax.text(x_pos, 0, -arrow_len - 30, f"{label}={R/1000:.1f} kN",
                fontsize=8, color="#276749", ha="center")


def build_selected_x_marker_3d(
    ax, x_sel: float,
    section_width: float = 300.0,
    section_height: float = 500.0,
):
    """Dessine le marqueur de la position x en 3D."""
    w = section_width * 0.8
    h = section_height * 1.2

    ax.plot([x_sel, x_sel], [-w/2, w/2], [0, 0], color="#E53E3E",
            linewidth=2, linestyle="--")
    ax.plot([x_sel, x_sel], [0, 0], [0, h], color="#E53E3E",
            linewidth=2, linestyle="--")


def render_beam_scene_3d(
    fig: Figure,
    poutre: DonneesPoutre,
    resultats: Optional[ResultatSollicitations] = None,
    x_selected: Optional[float] = None,
    section_width: float = 300.0,
    section_height: float = 500.0,
    mode: str = "vue_complete",
    combinaison: str = "ELU",
):
    """Construit la scène 3D complète dans une figure matplotlib.

    Args:
        mode: "vue_structure", "vue_charges", "vue_sollicitations", "vue_complete"
    """
    fig.clear()
    ax = fig.add_subplot(111, projection="3d")

    L = poutre.longueur_totale_mm

    # Structure
    if mode in ("vue_structure", "vue_complete"):
        build_beam_3d(ax, poutre, section_width, section_height)
        build_supports_3d(ax, poutre, section_width)

    # Charges
    if mode in ("vue_charges", "vue_complete"):
        build_distributed_loads_3d(ax, poutre, section_height, combinaison)
        build_point_loads_3d(ax, poutre, section_height, combinaison)

    # Réactions
    if resultats is not None and mode in ("vue_sollicitations", "vue_complete"):
        build_reactions_3d(ax, poutre, resultats.RA, resultats.RB, section_width)

    # Position x
    if x_selected is not None:
        build_selected_x_marker_3d(ax, x_selected, section_width, section_height)

    # Informations texte
    if resultats is not None and mode in ("vue_sollicitations", "vue_complete"):
        info = f"Combinaison : {resultats.combinaison}\n"
        info += f"M_max = {resultats.M_max/1e6:.2f} kN·m\n"
        info += f"V_max = {resultats.V_max/1000:.1f} kN"
        ax.text2D(0.02, 0.95, info, transform=ax.transAxes,
                  fontsize=9, verticalalignment="top",
                  bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8))

    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")
    ax.set_title(f"Vue 3D de la poutre – {combinaison}", fontsize=11, fontweight="bold")

    # Ajuster la vue
    ax.set_xlim(-L * 0.1, L * 1.1)
    ax.set_ylim(-section_width, section_width)
    ax.set_zlim(-section_width, section_height * 1.5)
    ax.view_init(elev=25, azim=-60)


def export_beam_3d_image(
    poutre: DonneesPoutre,
    resultats: Optional[ResultatSollicitations],
    filepath: str,
    x_selected: Optional[float] = None,
    section_width: float = 300.0,
    section_height: float = 500.0,
    mode: str = "vue_complete",
    combinaison: str = "ELU",
    dpi: int = 150,
):
    """Exporte la vue 3D en fichier image."""
    fig = Figure(figsize=(12, 8), dpi=dpi)
    render_beam_scene_3d(fig, poutre, resultats, x_selected,
                          section_width, section_height, mode, combinaison)
    fig.savefig(filepath, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
