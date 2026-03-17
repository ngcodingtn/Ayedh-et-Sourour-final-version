"""Tests – Visualisation poutre 2D et 3D (smoke tests)."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import matplotlib
matplotlib.use("Agg")  # backend non-interactif
import matplotlib.pyplot as plt

from app.models.load_models import DonneesPoutre, ChargeConcentree
from app.models.result_models import ResultatSollicitations
from app.core.beam_loads import calculer_sollicitations

from app.visualization.beam_plot_2d import (
    draw_beam_2d,
    draw_supports_2d,
    draw_shear_diagram_2d,
    draw_moment_diagram_2d,
    export_beam_2d_png,
)
from app.visualization.beam_view_3d import (
    render_beam_scene_3d,
    export_beam_3d_image,
)


def _make_poutre():
    return DonneesPoutre(
        longueur_totale_mm=5000,
        position_appui_A_mm=0,
        position_appui_B_mm=5000,
        g_N_mm=10,
        q_N_mm=5,
        charges_concentrees=[
            ChargeConcentree(position_mm=2500, G_N=5000, Q_N=2000),
        ],
    )


def _make_resultats(poutre=None):
    p = poutre or _make_poutre()
    return calculer_sollicitations(p, 2500, "ELU")


class TestDrawBeam2D:
    def test_schema_poutre(self):
        fig, ax = plt.subplots()
        p = _make_poutre()
        r = _make_resultats(p)
        draw_beam_2d(fig, p, r, mode="schema_poutre", x_selected=2500)
        plt.close(fig)

    def test_diagrammes(self):
        fig, axes = plt.subplots(2, 1)
        p = _make_poutre()
        r = _make_resultats(p)
        draw_beam_2d(fig, p, r, mode="diagrammes", x_selected=2500)
        plt.close(fig)

    def test_vue_complete(self):
        fig, axes = plt.subplots(3, 1)
        p = _make_poutre()
        r = _make_resultats(p)
        draw_beam_2d(fig, p, r, mode="vue_complete", x_selected=2500)
        plt.close(fig)


class TestDrawSupports:
    def test_no_error(self):
        fig, ax = plt.subplots()
        draw_supports_2d(ax, 0, 5000, 0, 5000)
        plt.close(fig)


class TestDiagrams2D:
    def test_shear_diagram(self):
        fig, ax = plt.subplots()
        r = _make_resultats()
        draw_shear_diagram_2d(ax, r, x_selected=2500)
        plt.close(fig)

    def test_moment_diagram(self):
        fig, ax = plt.subplots()
        r = _make_resultats()
        draw_moment_diagram_2d(ax, r, x_selected=2500)
        plt.close(fig)


class TestExport2D:
    def test_export_png(self, tmp_path):
        p = _make_poutre()
        r = _make_resultats(p)
        path = str(tmp_path / "beam_2d.png")
        export_beam_2d_png(p, r, path, x_selected=2500)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 100


class TestRender3D:
    def test_vue_structure(self):
        fig = plt.figure()
        p = _make_poutre()
        r = _make_resultats(p)
        render_beam_scene_3d(fig, p, r, mode="vue_structure")
        plt.close(fig)

    def test_vue_complete(self):
        fig = plt.figure()
        p = _make_poutre()
        r = _make_resultats(p)
        render_beam_scene_3d(fig, p, r, mode="vue_complete")
        plt.close(fig)


class TestExport3D:
    def test_export_image(self, tmp_path):
        p = _make_poutre()
        r = _make_resultats(p)
        path = str(tmp_path / "beam_3d.png")
        export_beam_3d_image(p, r, path)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 100
