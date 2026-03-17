"""Tests pour l'exemple de la figure avec 4 lits d'armatures."""
from __future__ import annotations

import pytest

from app.core.examples import exemple_figure
from app.core.units import MNm_to_Nmm, Nmm_to_MNm, cm_to_mm, mm_to_cm
from app.core.section_decision import (
    compute_moment_reference_t_section,
    decide_section_type,
    DecisionSection,
)
from app.models.material_models import DonneesBeton
from app.models.reinforcement_models import LitArmature, DonneesFerraillage
from app.services.calculation_service import calcul_complet


# ── Données de l'exemple de la figure ──
# beff=120cm=1200mm, bw=50cm=500mm, h=60cm=600mm, hf=12cm=120mm, d=51cm=510mm
# Mu,max = 1.1940 MN.m
# 4 lits : 5HA25 + 5HA25 + 5HA16 + 5HA14


class TestExempleFigureData:
    """Vérifie que les données de exemple_figure() sont correctes."""

    def test_geometrie_values(self):
        ex = exemple_figure()
        geo = ex["geometrie"]
        assert geo.b_eff == 1200.0
        assert geo.b_w == 500.0
        assert geo.h == 600.0
        assert geo.h_f == 120.0
        assert geo.d == 510.0

    def test_moment_ultime(self):
        ex = exemple_figure()
        sol = ex["sollicitations"]
        # M_Ed doit être 1.1940 MN.m converti en N.mm
        assert Nmm_to_MNm(sol.M_Ed) == pytest.approx(1.1940, abs=0.0001)

    def test_quatre_lits(self):
        ex = exemple_figure()
        fer = ex["ferraillage"]
        assert len(fer.lits_tendus) == 4

    def test_lit_1(self):
        ex = exemple_figure()
        lit = ex["ferraillage"].lits_tendus[0]
        assert lit.nombre_barres == 5
        assert lit.diametre_mm == 25.0

    def test_lit_2(self):
        ex = exemple_figure()
        lit = ex["ferraillage"].lits_tendus[1]
        assert lit.nombre_barres == 5
        assert lit.diametre_mm == 25.0

    def test_lit_3(self):
        ex = exemple_figure()
        lit = ex["ferraillage"].lits_tendus[2]
        assert lit.nombre_barres == 5
        assert lit.diametre_mm == 16.0

    def test_lit_4(self):
        ex = exemple_figure()
        lit = ex["ferraillage"].lits_tendus[3]
        assert lit.nombre_barres == 5
        assert lit.diametre_mm == 14.0

    def test_materiaux(self):
        ex = exemple_figure()
        mat = ex["materiaux"]
        assert mat.beton.fck == 25.0
        assert mat.acier.fyk == 500.0

    def test_nom(self):
        ex = exemple_figure()
        assert "figure" in ex["nom"].lower()


class TestExempleFigureSectionDecision:
    """Vérifie la décision du type de section pour l'exemple de la figure."""

    def test_mtu_calculation(self):
        """Calcul de MTu pour la section de la figure."""
        fcu = 1.0 * 25.0 / 1.5  # alpha_cc * fck / gamma_c = 16.667 MPa
        MTu = compute_moment_reference_t_section(
            b_eff=1200.0, h_f=120.0, fcu=fcu, d=510.0,
        )
        MTu_MNm = Nmm_to_MNm(MTu)
        # MTu = 1200 * 120 * 16.667 * (510 - 60) = 1 080 000 000 N.mm = 1.0800 MN.m
        assert MTu_MNm == pytest.approx(1.0800, rel=0.01)

    def test_decide_section_type(self):
        """Mu,max=1.1940 > MTu → Section en T."""
        fcu = 1.0 * 25.0 / 1.5  # 16.667 MPa
        result = decide_section_type(
            MEd_max=MNm_to_Nmm(1.1940),
            b_eff=1200.0, b_w=500.0, h_f=120.0, h=600.0, d=510.0,
            fcu=fcu,
            moment_positif=True,
        )
        assert result.decision == DecisionSection.SECTION_T

    def test_decision_rect_equiv_small_moment(self):
        """Petit moment → section rectangulaire équivalente."""
        fcu = 1.0 * 25.0 / 1.5  # 16.667 MPa
        result = decide_section_type(
            MEd_max=MNm_to_Nmm(0.5),
            b_eff=1200.0, b_w=500.0, h_f=120.0, h=600.0, d=510.0,
            fcu=fcu,
            moment_positif=True,
        )
        assert result.decision == DecisionSection.RECTANGULAIRE_EQUIVALENTE_BEFF


class TestExempleFigureCalcul:
    """Teste le calcul complet avec l'exemple de la figure."""

    def test_calcul_complet_valide(self):
        """Le calcul complet doit être valide."""
        ex = exemple_figure()
        resultats = calcul_complet(
            ex["geometrie"], ex["materiaux"], ex["sollicitations"],
            ex["ferraillage"], ex["environnement"],
        )
        assert resultats.elu.calcul_valide

    def test_as_requise_positive(self):
        """La section d'acier requise doit être positive."""
        ex = exemple_figure()
        resultats = calcul_complet(
            ex["geometrie"], ex["materiaux"], ex["sollicitations"],
            ex["ferraillage"], ex["environnement"],
        )
        assert resultats.elu.As_requise > 0

    def test_as_reelle_4_lits(self):
        """Vérifie la section réelle des 4 lits."""
        ex = exemple_figure()
        fer = ex["ferraillage"]
        # 5×HA25: 5 × π/4 × 25² = 5 × 490.87 = 2454.37 mm²
        # 5×HA25: 2454.37 mm²
        # 5×HA16: 5 × π/4 × 16² = 5 × 201.06 = 1005.31 mm²
        # 5×HA14: 5 × π/4 × 14² = 5 × 153.94 = 769.69 mm²
        # Total ≈ 6683.7 mm² ≈ 66.84 cm²
        As_reelle = fer.As_reelle_mm2
        assert As_reelle == pytest.approx(6683.7, rel=0.01)

    def test_verification_ferraillage(self):
        """La vérification du ferraillage doit fonctionner."""
        ex = exemple_figure()
        resultats = calcul_complet(
            ex["geometrie"], ex["materiaux"], ex["sollicitations"],
            ex["ferraillage"], ex["environnement"],
        )
        assert resultats.verification is not None


class TestUnitConversions:
    """Vérifie les conversions d'unités utilisées dans l'interface."""

    def test_cm_to_mm_beff(self):
        assert cm_to_mm(120.0) == 1200.0

    def test_cm_to_mm_bw(self):
        assert cm_to_mm(50.0) == 500.0

    def test_cm_to_mm_h(self):
        assert cm_to_mm(60.0) == 600.0

    def test_cm_to_mm_hf(self):
        assert cm_to_mm(12.0) == 120.0

    def test_cm_to_mm_d(self):
        assert cm_to_mm(51.0) == 510.0

    def test_mm_to_cm_roundtrip(self):
        assert mm_to_cm(cm_to_mm(120.0)) == 120.0

    def test_MNm_conversion(self):
        val_Nmm = MNm_to_Nmm(1.1940)
        assert Nmm_to_MNm(val_Nmm) == pytest.approx(1.1940)

    def test_MNm_to_Nmm_value(self):
        # 1.1940 MN.m = 1.1940 * 10^9 N.mm
        assert MNm_to_Nmm(1.1940) == pytest.approx(1.1940e9)
