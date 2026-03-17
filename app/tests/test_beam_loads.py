"""Tests – Sollicitations poutre (beam_loads)."""
import pytest
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.models.load_models import DonneesPoutre, ChargeConcentree
from app.core.beam_loads import (
    combine_loads_elu,
    combine_loads_els_characteristic,
    combine_loads_els_frequent,
    combine_loads_els_quasi_permanent,
    compute_support_reactions,
    compute_shear_at_x,
    compute_moment_at_x,
    compute_shear_diagram,
    compute_moment_diagram,
    find_moment_extrema,
    find_shear_extrema,
    determine_zone,
    calculer_sollicitations,
)


# ── Fixtures ──────────────────────────────────────────────────────────────

def _simple_beam(L=5000, g=10.0, q=5.0):
    """Poutre sur deux appuis, charge répartie seule."""
    return DonneesPoutre(
        longueur_totale_mm=L,
        position_appui_A_mm=0.0,
        position_appui_B_mm=L,
        g_N_mm=g, q_N_mm=q,
    )


def _beam_with_point_load():
    """Poutre 6 m avec charge concentrée à mi-portée."""
    return DonneesPoutre(
        longueur_totale_mm=6000,
        position_appui_A_mm=0.0,
        position_appui_B_mm=6000,
        g_N_mm=5.0, q_N_mm=3.0,
        charges_concentrees=[
            ChargeConcentree(position_mm=3000, G_N=10_000, Q_N=5_000),
        ],
    )


# ── Combinaisons ─────────────────────────────────────────────────────────

class TestCombinations:
    def test_elu(self):
        assert combine_loads_elu(10, 5) == pytest.approx(1.35 * 10 + 1.5 * 5)

    def test_els_char(self):
        assert combine_loads_els_characteristic(10, 5) == pytest.approx(15)

    def test_els_frequent(self):
        assert combine_loads_els_frequent(10, 5, 0.5) == pytest.approx(12.5)

    def test_els_qp(self):
        assert combine_loads_els_quasi_permanent(10, 5, 0.3) == pytest.approx(11.5)


# ── Réactions d'appui ────────────────────────────────────────────────────

class TestSupportReactions:
    def test_simple_beam_symmetry(self):
        """Charge symétrique → RA == RB."""
        p = _simple_beam()
        RA, RB = compute_support_reactions(p, "ELU")
        assert RA == pytest.approx(RB, rel=1e-6)

    def test_simple_beam_equilibrium(self):
        """RA + RB = charge totale."""
        p = _simple_beam(L=4000, g=8.0, q=4.0)
        RA, RB = compute_support_reactions(p, "ELU")
        w = 1.35 * 8 + 1.5 * 4
        total = w * 4000
        assert RA + RB == pytest.approx(total, rel=1e-6)

    def test_with_point_load(self):
        """Charge concentrée au milieu → contributions symétriques."""
        p = _beam_with_point_load()
        RA, RB = compute_support_reactions(p, "ELU")
        # Charge concentrée au milieu : contribution symétrique
        F_cc = 1.35 * 10_000 + 1.5 * 5_000
        w = 1.35 * 5.0 + 1.5 * 3.0
        total = w * 6000 + F_cc
        assert RA + RB == pytest.approx(total, rel=1e-6)
        # Symétrie
        assert RA == pytest.approx(RB, rel=1e-3)

    def test_zero_span(self):
        p = DonneesPoutre(longueur_totale_mm=0, position_appui_A_mm=0, position_appui_B_mm=0)
        RA, RB = compute_support_reactions(p, "ELU")
        assert RA == 0 and RB == 0


# ── Effort tranchant V(x) ───────────────────────────────────────────────

class TestShearAtX:
    def test_zero_at_midspan(self):
        """Pour poutre symétrique, V à mi-portée ≈ 0."""
        p = _simple_beam()
        V_mid = compute_shear_at_x(p, 2500, "ELU")
        assert abs(V_mid) < 1.0  # quasi zéro

    def test_sign_change(self):
        """V change de signe entre 0 et L."""
        p = _simple_beam()
        V_start = compute_shear_at_x(p, 0.01, "ELU")
        V_end = compute_shear_at_x(p, 4999.99, "ELU")
        # V start positif, V end négatif (convention)
        assert V_start > 0
        assert V_end < 0

    def test_diagram_length(self):
        p = _simple_beam()
        xs, Vs = compute_shear_diagram(p, "ELU", n_points=100)
        assert len(xs) == 101
        assert len(Vs) == 101


# ── Moment fléchissant M(x) ─────────────────────────────────────────────

class TestMomentAtX:
    def test_zero_at_supports(self):
        """M(0) = M(L) = 0 pour poutre sur deux appuis sans consoles."""
        p = _simple_beam()
        assert abs(compute_moment_at_x(p, 0, "ELU")) < 1.0
        assert abs(compute_moment_at_x(p, 5000, "ELU")) < 1.0

    def test_max_at_midspan(self):
        """Moment max à mi-portée pour charge symétrique."""
        p = _simple_beam()
        M_mid = compute_moment_at_x(p, 2500, "ELU")
        M_quarter = compute_moment_at_x(p, 1250, "ELU")
        assert M_mid > M_quarter

    def test_positive_in_span(self):
        """Moment positif en travée (hogging convention)."""
        p = _simple_beam()
        M = compute_moment_at_x(p, 2500, "ELU")
        assert M > 0

    def test_diagram_returns_lists(self):
        p = _simple_beam()
        xs, Ms = compute_moment_diagram(p, "ELU", 50)
        assert len(xs) == 51
        assert isinstance(Ms[0], float)


# ── Extrema ──────────────────────────────────────────────────────────────

class TestExtrema:
    def test_moment_extrema(self):
        p = _simple_beam()
        ext = find_moment_extrema(p, "ELU")
        assert ext["M_max"] > 0
        assert ext["x_M_max"] == pytest.approx(2500, abs=50)

    def test_shear_extrema(self):
        p = _simple_beam()
        ext = find_shear_extrema(p, "ELU")
        assert ext["V_max"] > 0
        assert ext["V_min"] < 0


# ── Zone ─────────────────────────────────────────────────────────────────

class TestZone:
    def test_travee(self):
        p = _simple_beam()
        assert determine_zone(p, 2500) == "travée"

    def test_appui_A(self):
        p = _simple_beam()
        assert determine_zone(p, 0.0) == "appui A"

    def test_appui_B(self):
        p = _simple_beam()
        assert determine_zone(p, 5000.0) == "appui B"

    def test_console_gauche(self):
        p = DonneesPoutre(
            longueur_totale_mm=6000,
            position_appui_A_mm=500,
            position_appui_B_mm=5500,
        )
        assert determine_zone(p, 100) == "console gauche"

    def test_console_droite(self):
        p = DonneesPoutre(
            longueur_totale_mm=6000,
            position_appui_A_mm=500,
            position_appui_B_mm=5500,
        )
        assert determine_zone(p, 5800) == "console droite"


# ── Calcul complet ───────────────────────────────────────────────────────

class TestCalculerSollicitations:
    def test_basic(self):
        p = _simple_beam()
        res = calculer_sollicitations(p, 2500, "ELU")
        assert res.calcul_valide
        assert res.RA > 0
        assert res.RB > 0
        assert res.Mx > 0
        assert len(res.x_values) > 0

    def test_invalid_beam(self):
        p = DonneesPoutre(longueur_totale_mm=-1)
        res = calculer_sollicitations(p, 0, "ELU")
        assert not res.calcul_valide
        assert len(res.erreurs) > 0

    def test_med_mser_ved(self):
        p = _simple_beam()
        res = calculer_sollicitations(p, 2500, "ELU")
        assert res.MEd > 0
        assert res.Mser > 0
        assert abs(res.Ved) < 1.0  # à mi-portée

    def test_els_combination(self):
        p = _simple_beam()
        r_elu = calculer_sollicitations(p, 2500, "ELU")
        r_els = calculer_sollicitations(p, 2500, "ELS caractéristique")
        # ELU moment > ELS moment
        assert abs(r_elu.Mx) > abs(r_els.Mx)
