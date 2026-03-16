"""Tests unitaires – Flexion section en T."""
import math
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.models.material_models import DonneesBeton, DonneesAcier
from app.core.flexion_t_beam import calcul_flexion_T
from app.core.units import MNm_to_Nmm, m_to_mm, mm2_to_cm2


class TestFlexionT:
    """Tests pour la section en T.

    Exemple 1 (MEd <= MTu) :
      beff=2660, bw=220, hf=150, h=850, d=800
      fck=25, MEd=0.777 MN·m
      → traitement rectangulaire beff, As ≈ 22.64 cm²

    Exemple 2 (MEd > MTu) :
      On crée un cas fictif avec MEd très élevé.
    """

    def setup_method(self):
        self.beton = DonneesBeton(fck=25.0)
        self.acier = DonneesAcier(fyk=500.0)

    def test_T_MEd_inferieur_MTu(self):
        """MEd <= MTu → calcul rectangulaire avec beff."""
        M_Ed = MNm_to_Nmm(0.777)
        res = calcul_flexion_T(
            M_Ed,
            b_eff=2660.0, b_w=220.0, h_f=150.0,
            h=850.0, d=800.0, d_prime=50.0,
            beton=self.beton, acier=self.acier,
            moment_positif=True,
        )
        assert res.calcul_valide
        assert "rectangulaire" in res.type_section_retenu.lower() or "table" in res.type_section_retenu.lower()
        As_cm2 = res.As_requise / 100.0
        assert As_cm2 == pytest.approx(22.64, abs=2.0)

    def test_T_MTu_positif(self):
        """MTu doit être positif et de l'ordre de 4.59 MN·m."""
        M_Ed = MNm_to_Nmm(0.777)
        res = calcul_flexion_T(
            M_Ed,
            b_eff=2660.0, b_w=220.0, h_f=150.0,
            h=850.0, d=800.0, d_prime=50.0,
            beton=self.beton, acier=self.acier,
            moment_positif=True,
        )
        MTu_MNm = res.MTu / 1e9
        assert MTu_MNm == pytest.approx(4.82, abs=0.3)

    def test_T_MEd_superieur_MTu(self):
        """MEd > MTu → décomposition table + âme."""
        # Utiliser un moment très élevé pour forcer MEd > MTu
        # Avec beff=500, bw=200, hf=100, h=500, d=450
        # MTu sera plus petit → plus facile de le dépasser
        beton = DonneesBeton(fck=30.0)
        acier = DonneesAcier(fyk=500.0)
        fcu = beton.fcu
        b_eff = 500.0
        b_w = 200.0
        h_f = 80.0
        d = 450.0
        h = 500.0

        MTu = b_eff * h_f * fcu * (d - h_f / 2.0)
        M_Ed = MTu * 1.5  # 50% au-dessus de MTu

        res = calcul_flexion_T(
            M_Ed,
            b_eff=b_eff, b_w=b_w, h_f=h_f,
            h=h, d=d, d_prime=50.0,
            beton=beton, acier=acier,
            moment_positif=True,
        )
        assert res.calcul_valide
        assert "âme" in res.type_section_retenu.lower() or "décomposition" in res.type_section_retenu.lower()
        assert res.As1 > 0  # contribution âme
        assert res.As2 > 0  # contribution table
        assert res.As_requise == pytest.approx(res.As1 + res.As2, rel=1e-6)

    def test_T_moment_negatif(self):
        """Moment négatif → section rectangulaire bw."""
        M_Ed = MNm_to_Nmm(0.200)
        res = calcul_flexion_T(
            M_Ed,
            b_eff=2660.0, b_w=220.0, h_f=150.0,
            h=850.0, d=800.0, d_prime=50.0,
            beton=self.beton, acier=self.acier,
            moment_positif=False,
        )
        assert res.calcul_valide
        assert "négatif" in res.type_section_retenu.lower() or "bw" in res.type_section_retenu.lower()
        # La largeur de calcul doit être bw
        assert res.b_calcul == pytest.approx(220.0, rel=1e-3)

    def test_T_moment_negatif_As_positive(self):
        """Moment négatif doit quand même donner As > 0."""
        M_Ed = MNm_to_Nmm(0.100)
        res = calcul_flexion_T(
            M_Ed,
            b_eff=2660.0, b_w=220.0, h_f=150.0,
            h=850.0, d=800.0, d_prime=50.0,
            beton=self.beton, acier=self.acier,
            moment_positif=False,
        )
        assert res.calcul_valide
        assert res.As_requise > 0
