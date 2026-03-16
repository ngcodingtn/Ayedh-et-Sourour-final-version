"""Tests unitaires – Vérification du ferraillage et catalogue acier."""
import math
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.steel_catalog import (
    get_unit_area_mm2, get_unit_area_cm2,
    get_total_area_mm2, get_total_area_cm2,
    get_table_area_cm2, compute_layers_area_mm2,
    compute_layers_area_cm2, format_rebar_design,
    find_rebar_solutions, check_spacing_and_constructability,
    compute_real_effective_depth_from_layers,
)
from app.core.reinforcement_check import verifier_ferraillage


class TestCatalogueAcier:
    """Tests sur le catalogue des armatures."""

    def test_1_HA12(self):
        """1 HA12 → environ 1.13 cm²."""
        assert get_total_area_cm2(12, 1) == pytest.approx(1.13, abs=0.01)

    def test_8_HA12(self):
        """8 HA12 → environ 9.05 cm²."""
        assert get_total_area_cm2(12, 8) == pytest.approx(9.05, abs=0.02)

    def test_6_HA16(self):
        """6 HA16 → environ 12.06 cm²."""
        assert get_total_area_cm2(16, 6) == pytest.approx(12.06, abs=0.02)

    def test_10_HA20(self):
        """10 HA20 → environ 31.42 cm²."""
        assert get_total_area_cm2(20, 10) == pytest.approx(31.42, abs=0.05)

    def test_combo_6HA16_3HA14(self):
        """6 HA16 + 3 HA14 → environ 16.68 cm²."""
        layers = [{"diametre": 16, "nombre": 6}, {"diametre": 14, "nombre": 3}]
        total = compute_layers_area_cm2(layers)
        assert total == pytest.approx(16.68, abs=0.05)

    def test_table_area_match(self):
        """Vérification que le tableau correspond aux valeurs exactes."""
        area_exact = get_total_area_cm2(12, 1)
        area_table = get_table_area_cm2(12, 1)
        assert area_table is not None
        assert abs(area_exact - area_table) < 0.01

    def test_table_area_beyond_10(self):
        """Pour n > 10, le tableau retourne None."""
        assert get_table_area_cm2(12, 11) is None

    def test_table_area_invalid_diameter(self):
        """Diamètre non disponible retourne None."""
        assert get_table_area_cm2(15, 1) is None

    def test_unit_area_exact(self):
        """Aire unitaire exacte = pi * d² / 4."""
        for d in [6, 8, 10, 12, 14, 16, 20, 25, 32, 40]:
            expected = math.pi * d**2 / 4.0
            assert get_unit_area_mm2(d) == pytest.approx(expected, rel=1e-10)

    def test_format_rebar(self):
        """Format lisible."""
        layers = [{"diametre": 16, "nombre": 4}, {"diametre": 14, "nombre": 3}]
        txt = format_rebar_design(layers)
        assert "4 HA16" in txt
        assert "3 HA14" in txt


class TestVerificationFerraillage:
    """Tests de vérification du ferraillage proposé."""

    def test_ferraillage_verifie(self):
        """Ferraillage suffisant → vérifié."""
        # As_requise ≈ 16.12 cm² = 1612 mm²
        lits = [
            {"diametre": 16, "nombre": 6},
            {"diametre": 14, "nombre": 3},
        ]
        res = verifier_ferraillage(
            lits=lits,
            As_requise_mm2=1612.0,
            d_calcul=540.0,
            h=600.0,
            c_nom=30.0,
            diam_etrier=8.0,
        )
        assert res.controle_section is True
        assert res.verdict_global is True

    def test_ferraillage_non_verifie(self):
        """Ferraillage insuffisant → non vérifié."""
        lits = [{"diametre": 10, "nombre": 2}]
        res = verifier_ferraillage(
            lits=lits,
            As_requise_mm2=1612.0,
            d_calcul=540.0,
            h=600.0,
            c_nom=30.0,
            diam_etrier=8.0,
        )
        assert res.controle_section is False
        assert res.verdict_global is False

    def test_d_reel_calcule(self):
        """d_réel doit être calculé correctement."""
        lits = [
            {"diametre": 16, "nombre": 6},
            {"diametre": 14, "nombre": 3},
        ]
        res = verifier_ferraillage(
            lits=lits,
            As_requise_mm2=1612.0,
            d_calcul=540.0,
            h=600.0,
            c_nom=30.0,
            diam_etrier=8.0,
        )
        # d_reel doit être positif et inférieur à h
        assert 0 < res.d_reel < 600.0

    def test_details_lits_complets(self):
        """Chaque lit doit avoir les détails complets."""
        lits = [
            {"diametre": 16, "nombre": 4},
            {"diametre": 16, "nombre": 4},
        ]
        res = verifier_ferraillage(
            lits=lits,
            As_requise_mm2=1600.0,
            d_calcul=540.0,
            h=600.0,
            c_nom=30.0,
            diam_etrier=8.0,
        )
        assert len(res.details_lits) == 2
        for det in res.details_lits:
            assert "lit_numero" in det
            assert "nombre_barres" in det
            assert "diametre_mm" in det
            assert "section_totale_mm2" in det
            assert "d_i_mm" in det


class TestConstructibilite:
    """Tests de faisabilité géométrique."""

    def test_solution_possible(self):
        """4 HA16 dans bw=350 → faisable."""
        result = check_spacing_and_constructability(
            b_w=350.0, c_nom=30.0, diam_etrier=8.0,
            lits=[{"diametre": 16, "nombre": 4}],
            espacement_horizontal=25.0, d_g=20.0,
        )
        assert result["verifie"] is True

    def test_solution_impossible(self):
        """10 HA40 dans bw=200 → impossible."""
        result = check_spacing_and_constructability(
            b_w=200.0, c_nom=30.0, diam_etrier=8.0,
            lits=[{"diametre": 40, "nombre": 10}],
            espacement_horizontal=25.0, d_g=20.0,
        )
        assert result["verifie"] is False

    def test_largeur_utile(self):
        """Largeur utile = bw - 2*cnom - 2*diam_etrier."""
        result = check_spacing_and_constructability(
            b_w=350.0, c_nom=30.0, diam_etrier=8.0,
            lits=[{"diametre": 16, "nombre": 4}],
        )
        assert result["largeur_utile_mm"] == pytest.approx(274.0, abs=1.0)

    def test_nb_max_barres(self):
        """Nombre max de barres par diamètre."""
        result = check_spacing_and_constructability(
            b_w=350.0, c_nom=30.0, diam_etrier=8.0,
            lits=[{"diametre": 16, "nombre": 1}],
        )
        assert 16 in result["nb_max_barres_par_lit"] or 16.0 in result["nb_max_barres_par_lit"]


class TestPropositions:
    """Tests du moteur de proposition."""

    def test_solutions_trouvees(self):
        """Le moteur doit trouver des solutions."""
        solutions = find_rebar_solutions(1612.0)
        assert len(solutions) > 0

    def test_solutions_suffisantes(self):
        """Chaque solution doit avoir As >= As_requise."""
        solutions = find_rebar_solutions(1612.0)
        for sol in solutions:
            assert sol["As_totale_mm2"] >= 1612.0

    def test_solutions_triees(self):
        """Les solutions doivent être triées par score."""
        solutions = find_rebar_solutions(1612.0)
        if len(solutions) > 1:
            scores = [s["score"] for s in solutions]
            assert scores == sorted(scores)

    def test_description_formatee(self):
        """Chaque solution a une description."""
        solutions = find_rebar_solutions(1000.0)
        for sol in solutions:
            assert len(sol["description"]) > 0
            assert "HA" in sol["description"]


class TestHauteurUtileReelle:
    """Tests du calcul de d_réel."""

    def test_un_lit(self):
        """Un seul lit : d_reel simple."""
        lits = [{"diametre": 16, "nombre": 4}]
        d_reel, details = compute_real_effective_depth_from_layers(
            h=600.0, c_nom=30.0, diam_etrier=8.0,
            lits=lits, espacement_vertical=25.0,
        )
        # d_reel = h - (c_nom + diam_etrier + phi/2) = 600 - (30 + 8 + 8) = 554
        assert d_reel == pytest.approx(554.0, abs=1.0)

    def test_deux_lits_identiques(self):
        """Deux lits identiques : d_reel entre les deux niveaux."""
        lits = [
            {"diametre": 16, "nombre": 4},
            {"diametre": 16, "nombre": 4},
        ]
        d_reel, details = compute_real_effective_depth_from_layers(
            h=600.0, c_nom=30.0, diam_etrier=8.0,
            lits=lits, espacement_vertical=25.0,
        )
        assert len(details) == 2
        assert details[0]["d_i_mm"] > details[1]["d_i_mm"]
        # d_reel doit être la moyenne pondérée
        d1 = details[0]["d_i_mm"]
        d2 = details[1]["d_i_mm"]
        assert d_reel == pytest.approx((d1 + d2) / 2, abs=1.0)
