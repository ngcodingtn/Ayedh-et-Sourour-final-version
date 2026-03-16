"""Schéma 2D de la section avec matplotlib."""
from __future__ import annotations

import math
import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
import matplotlib.patches as mpatches

from app.models.section_models import DonneesGeometrie, TypeSection
from app.models.reinforcement_models import DonneesFerraillage
from app.core.steel_catalog import compute_real_effective_depth_from_layers
from app.core.units import mm_to_cm


def dessiner_section_2d(
    fig: Figure,
    geometrie: DonneesGeometrie,
    ferraillage: DonneesFerraillage,
) -> None:
    """Dessine la section 2D sur la figure matplotlib."""
    fig.clear()
    ax = fig.add_subplot(111)
    ax.set_aspect("equal")
    ax.set_title("Section transversale", fontsize=14, fontweight="bold", color="#1565C0")

    h = geometrie.h
    b_w = geometrie.b_w
    b_eff = geometrie.b_eff if geometrie.b_eff > 0 else b_w
    h_f = geometrie.h_f if geometrie.h_f > 0 else 0
    c_nom = geometrie.c_nom
    diam_etrier = geometrie.diam_etrier
    d = geometrie.hauteur_utile_effective()

    est_T = (geometrie.type_section in (TypeSection.T, TypeSection.AUTO)) and b_eff > b_w and h_f > 0

    # ── Contour béton ──
    if est_T:
        # Section en T
        # Table (en haut)
        x_table = -b_eff / 2
        y_table = h - h_f
        ax.add_patch(Rectangle(
            (x_table, y_table), b_eff, h_f,
            linewidth=2, edgecolor="#424242", facecolor="#E0E0E0",
            label="Béton",
        ))
        # Âme
        x_ame = -b_w / 2
        ax.add_patch(Rectangle(
            (x_ame, 0), b_w, h - h_f,
            linewidth=2, edgecolor="#424242", facecolor="#E0E0E0",
        ))
    else:
        # Section rectangulaire
        x_rect = -b_w / 2
        ax.add_patch(Rectangle(
            (x_rect, 0), b_w, h,
            linewidth=2, edgecolor="#424242", facecolor="#E0E0E0",
            label="Béton",
        ))

    # ── Étrier ──
    etrier_offset = c_nom
    x_et = -b_w / 2 + etrier_offset
    y_et = etrier_offset
    w_et = b_w - 2 * etrier_offset
    h_et = h - 2 * etrier_offset
    ax.add_patch(Rectangle(
        (x_et, y_et), w_et, h_et,
        linewidth=1.5, edgecolor="#FF6F00", facecolor="none",
        linestyle="--", label=f"Étrier Ø{diam_etrier:.0f}",
    ))

    # ── Armatures tendues ──
    if ferraillage.lits_tendus:
        # Utiliser les positions explicites si disponibles
        has_positions = any(
            lit.distance_fibre_tendue_cm > 0 for lit in ferraillage.lits_tendus
        )

        if has_positions:
            details = []
            for i, lit in enumerate(ferraillage.lits_tendus):
                details.append({
                    "nombre_barres": lit.nombre_barres,
                    "diametre_mm": lit.diametre_mm,
                    "distance_bord_tendu_mm": lit.distance_fibre_tendue_cm * 10.0,
                })
        else:
            lits_data = [
                {"diametre": lit.diametre_mm, "nombre": lit.nombre_barres}
                for lit in ferraillage.lits_tendus
            ]
            _, details = compute_real_effective_depth_from_layers(
                h, c_nom, diam_etrier, lits_data, geometrie.espacement_vertical,
            )

        for lit_idx, det in enumerate(details):
            nb = det["nombre_barres"]
            diam = det["diametre_mm"]
            y_centre = det["distance_bord_tendu_mm"]

            # Largeur utile pour placer les barres
            largeur_utile = b_w - 2 * c_nom - 2 * diam_etrier
            if nb == 1:
                positions_x = [0.0]
            else:
                espacement = largeur_utile / (nb + 1)
                positions_x = [
                    -largeur_utile / 2 + espacement * (i + 1)
                    for i in range(nb)
                ]

            for x in positions_x:
                circle = Circle(
                    (x, y_centre), diam / 2,
                    facecolor="#1565C0", edgecolor="#0D47A1", linewidth=1,
                )
                ax.add_patch(circle)

            # Étiquette du lit (à droite des barres)
            x_label = b_w / 2 - c_nom
            dist_label = f" {mm_to_cm(y_centre):.1f}cm" if has_positions else ""
            ax.text(x_label, y_centre,
                    f" Lit {lit_idx+1}: {nb}HA{diam:.0f}{dist_label}",
                    fontsize=7, va="center", color="#0D47A1")

        # Marquer le premier lit
        ax.plot([], [], "o", color="#1565C0", markersize=8, label="Acier tendu")

    # ── Armatures comprimées ──
    if ferraillage.lits_comprimes:
        for lit in ferraillage.lits_comprimes:
            nb = lit.nombre_barres
            diam = lit.diametre_mm
            y_centre = h - c_nom - diam_etrier - diam / 2

            largeur_utile = b_w - 2 * c_nom - 2 * diam_etrier
            if nb == 1:
                positions_x = [0.0]
            else:
                espacement = largeur_utile / (nb + 1)
                positions_x = [
                    -largeur_utile / 2 + espacement * (i + 1)
                    for i in range(nb)
                ]

            for x in positions_x:
                circle = Circle(
                    (x, y_centre), diam / 2,
                    facecolor="#C62828", edgecolor="#B71C1C", linewidth=1,
                )
                ax.add_patch(circle)
        ax.plot([], [], "o", color="#C62828", markersize=8, label="Acier comprimé")

    # ── Cotations ──
    marge = max(b_w, b_eff) * 0.15

    # Hauteur h
    ax.annotate("", xy=(b_w / 2 + marge, 0), xytext=(b_w / 2 + marge, h),
                arrowprops=dict(arrowstyle="<->", color="#424242", lw=1.5))
    ax.text(b_w / 2 + marge + 10, h / 2, f"h = {mm_to_cm(h):.1f} cm",
            fontsize=9, va="center", color="#424242")

    # Largeur bw
    ax.annotate("", xy=(-b_w / 2, -marge), xytext=(b_w / 2, -marge),
                arrowprops=dict(arrowstyle="<->", color="#424242", lw=1.5))
    ax.text(0, -marge - 15, f"bw = {mm_to_cm(b_w):.1f} cm", fontsize=9, ha="center", color="#424242")

    # Hauteur utile d
    if d > 0:
        ax.axhline(y=h - d, color="#2E7D32", linestyle=":", linewidth=1, alpha=0.7)
        ax.text(-b_w / 2 - 10, h - d, f"d = {mm_to_cm(d):.1f} cm", fontsize=8, ha="right",
                va="center", color="#2E7D32")

    if est_T:
        # beff
        ax.annotate("", xy=(-b_eff / 2, h + marge), xytext=(b_eff / 2, h + marge),
                    arrowprops=dict(arrowstyle="<->", color="#1565C0", lw=1.5))
        ax.text(0, h + marge + 10, f"beff = {mm_to_cm(b_eff):.1f} cm", fontsize=9,
                ha="center", color="#1565C0")

        # hf
        ax.annotate("", xy=(b_eff / 2 + marge + 40, h - h_f), xytext=(b_eff / 2 + marge + 40, h),
                    arrowprops=dict(arrowstyle="<->", color="#1565C0", lw=1.5))
        ax.text(b_eff / 2 + marge + 50, h - h_f / 2, f"hf = {mm_to_cm(h_f):.1f} cm",
                fontsize=9, va="center", color="#1565C0")

    # Enrobage
    ax.text(-b_w / 2 + c_nom / 2, 5, f"c={mm_to_cm(c_nom):.1f} cm", fontsize=7, ha="center",
            color="#FF6F00", alpha=0.8)

    # Légende
    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)

    # Limites et grille
    x_max = max(b_w, b_eff) / 2 + marge + 80
    ax.set_xlim(-x_max, x_max)
    ax.set_ylim(-marge - 40, h + marge + 40)
    ax.set_xlabel("(mm)", fontsize=10)
    ax.set_ylabel("(mm)", fontsize=10)
    ax.grid(True, alpha=0.2)

    fig.tight_layout()
