"""Vue 3D de la section avec pyvista intégré dans PySide6."""
from __future__ import annotations

import math
import numpy as np

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

from app.models.section_models import DonneesGeometrie, TypeSection
from app.models.reinforcement_models import DonneesFerraillage
from app.core.steel_catalog import compute_real_effective_depth_from_layers


def creer_vue_3d(
    geometrie: DonneesGeometrie,
    ferraillage: DonneesFerraillage,
) -> QWidget:
    """Crée un widget PySide6 contenant la vue 3D pyvista."""
    try:
        import pyvista as pv
        from pyvistaqt import QtInteractor
    except ImportError:
        # Fallback si pyvista pas disponible
        widget = QWidget()
        layout = QVBoxLayout(widget)
        lbl = QLabel(
            "La vue 3D nécessite les packages 'pyvista' et 'pyvistaqt'.\n"
            "Installez-les avec : pip install pyvista pyvistaqt"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 14px; color: #C62828; padding: 40px;")
        layout.addWidget(lbl)
        return widget

    h = geometrie.h
    b_w = geometrie.b_w
    b_eff = geometrie.b_eff if geometrie.b_eff > 0 else b_w
    h_f = geometrie.h_f if geometrie.h_f > 0 else 0
    c_nom = geometrie.c_nom
    diam_etrier = geometrie.diam_etrier
    longueur = geometrie.longueur_extrusion

    est_T = (geometrie.type_section in (TypeSection.T, TypeSection.AUTO)) and b_eff > b_w and h_f > 0

    # Créer le widget Qt
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)

    plotter = QtInteractor(widget)
    layout.addWidget(plotter.interactor)

    plotter.set_background("#F5F5F5")

    # ── Béton ──
    if est_T:
        # Âme
        ame = pv.Box(bounds=[
            -b_w / 2, b_w / 2,
            0, h - h_f,
            0, longueur,
        ])
        plotter.add_mesh(ame, color="#BDBDBD", opacity=0.4, label="Âme")

        # Table
        table = pv.Box(bounds=[
            -b_eff / 2, b_eff / 2,
            h - h_f, h,
            0, longueur,
        ])
        plotter.add_mesh(table, color="#9E9E9E", opacity=0.4, label="Table")
    else:
        beton = pv.Box(bounds=[
            -b_w / 2, b_w / 2,
            0, h,
            0, longueur,
        ])
        plotter.add_mesh(beton, color="#BDBDBD", opacity=0.4, label="Béton")

    # ── Armatures longitudinales tendues ──
    if ferraillage.lits_tendus:
        # Utiliser les positions explicites si disponibles
        has_positions = any(
            lit.distance_fibre_tendue_cm > 0 for lit in ferraillage.lits_tendus
        )

        if has_positions:
            details = []
            for lit in ferraillage.lits_tendus:
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

        for det in details:
            nb = det["nombre_barres"]
            diam = det["diametre_mm"]
            y_centre = det["distance_bord_tendu_mm"]
            rayon = diam / 2

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
                barre = pv.Cylinder(
                    center=[x, y_centre, longueur / 2],
                    direction=[0, 0, 1],
                    radius=rayon,
                    height=longueur,
                    resolution=16,
                )
                plotter.add_mesh(barre, color="#1565C0", label="")

    # ── Étriers (simplifiés – quelques étriers le long de la longueur) ──
    nb_etriers = max(3, int(longueur / 200))
    espacement_etriers = longueur / (nb_etriers + 1)

    x_int = b_w / 2 - c_nom - diam_etrier / 2
    y_int_bas = c_nom + diam_etrier / 2
    y_int_haut = h - c_nom - diam_etrier / 2
    rayon_etrier = diam_etrier / 2

    for i in range(1, nb_etriers + 1):
        z_pos = i * espacement_etriers
        # Quatre segments de l'étrier
        # Bas
        barre_b = pv.Cylinder(
            center=[0, y_int_bas, z_pos], direction=[1, 0, 0],
            radius=rayon_etrier, height=2 * x_int, resolution=8,
        )
        plotter.add_mesh(barre_b, color="#FF6F00")
        # Haut
        barre_h = pv.Cylinder(
            center=[0, y_int_haut, z_pos], direction=[1, 0, 0],
            radius=rayon_etrier, height=2 * x_int, resolution=8,
        )
        plotter.add_mesh(barre_h, color="#FF6F00")
        # Gauche
        barre_g = pv.Cylinder(
            center=[-x_int, (y_int_bas + y_int_haut) / 2, z_pos],
            direction=[0, 1, 0],
            radius=rayon_etrier, height=y_int_haut - y_int_bas, resolution=8,
        )
        plotter.add_mesh(barre_g, color="#FF6F00")
        # Droite
        barre_d = pv.Cylinder(
            center=[x_int, (y_int_bas + y_int_haut) / 2, z_pos],
            direction=[0, 1, 0],
            radius=rayon_etrier, height=y_int_haut - y_int_bas, resolution=8,
        )
        plotter.add_mesh(barre_d, color="#FF6F00")

    # Axes et configuration
    plotter.add_axes()
    plotter.reset_camera()
    plotter.camera_position = "iso"

    return widget
