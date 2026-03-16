"""Tests unitaires – Flexion section rectangulaire."""
import math
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.models.material_models import DonneesBeton, DonneesAcier
from app.core.flexion_rectangular import calcul_flexion_rectangulaire
from app.core.flexion_common import calculer_mu_cu, calculer_alpha_u, calculer_Zc
from app.core.units import MNm_to_Nmm, m_to_mm, mm2_to_cm2


class TestFlexionRectangulaire:
    """Tests pour le cas rectangulaire de validation.

    bw = 350 mm, h = 600 mm, d = 540 mm
    fck = 25 MPa, fyk = 500 MPa
    MEd = 0.3414 MN·m = 341.4 kN·m
    Résultat attendu : As ≈ 16.12 cm², alpha_u ≈ 0.282
    """

    def setup_method(self):
        self.beton = DonneesBeton(fck=25.0)
        self.acier = DonneesAcier(fyk=500.0)
        self.b = 350.0   # mm
        self.h = 600.0    # mm
        self.d = 540.0    # mm
        self.d_prime = 50.0
        self.M_Ed = MNm_to_Nmm(0.3414)  # N·mm

    def test_fcd(self):
        """Vérifie fcd = alpha_cc * fck / gamma_c."""
        assert self.beton.fcd == pytest.approx(25.0 / 1.5, rel=1e-3)

    def test_fcu(self):
        """Vérifie fcu = eta * fcd."""
        assert self.beton.fcu == pytest.approx(25.0 / 1.5, rel=1e-3)

    def test_moment_reduit(self):
        """Vérifie mu_cu."""
        mu = calculer_mu_cu(self.M_Ed, self.b, self.d, self.beton.fcu)
        # mu_cu = 341400000 / (350 * 540² * 16.667) ≈ 0.200
        assert 0.10 < mu < 0.40

    def test_alpha_u(self):
        """Vérifie alpha_u ≈ 0.282."""
        mu = calculer_mu_cu(self.M_Ed, self.b, self.d, self.beton.fcu)
        alpha = calculer_alpha_u(mu, self.beton.lambda_coeff)
        assert alpha == pytest.approx(0.282, abs=0.02)

    def test_bras_levier(self):
        """Vérifie Zc ≈ 480 mm."""
        mu = calculer_mu_cu(self.M_Ed, self.b, self.d, self.beton.fcu)
        alpha = calculer_alpha_u(mu, self.beton.lambda_coeff)
        Zc = calculer_Zc(self.d, alpha, self.beton.lambda_coeff)
        assert Zc == pytest.approx(480.0, abs=10.0)

    def test_section_acier_requise(self):
        """Vérifie As ≈ 16.12 cm²."""
        res = calcul_flexion_rectangulaire(
            self.M_Ed, self.b, self.d, self.d_prime, self.h,
            self.beton, self.acier,
        )
        assert res.calcul_valide
        As_cm2 = res.As_requise / 100.0
        assert As_cm2 == pytest.approx(16.12, abs=1.0)

    def test_pas_aciers_comprimes(self):
        """Vérifie qu'il n'y a pas besoin d'aciers comprimés."""
        res = calcul_flexion_rectangulaire(
            self.M_Ed, self.b, self.d, self.d_prime, self.h,
            self.beton, self.acier,
        )
        assert not res.necessite_aciers_comprimes

    def test_pivot_B(self):
        """Vérifie que c'est le pivot B."""
        res = calcul_flexion_rectangulaire(
            self.M_Ed, self.b, self.d, self.d_prime, self.h,
            self.beton, self.acier,
        )
        assert res.pivot.pivot == "B"

    def test_sigma_s1_egale_fyd(self):
        """En pivot B avec palier horizontal, sigma_s1 = fyd."""
        res = calcul_flexion_rectangulaire(
            self.M_Ed, self.b, self.d, self.d_prime, self.h,
            self.beton, self.acier,
        )
        assert res.pivot.sigma_s1 == pytest.approx(self.acier.fyd, rel=1e-3)

    def test_section_minimale(self):
        """Vérifie qu'As,min est calculé."""
        res = calcul_flexion_rectangulaire(
            self.M_Ed, self.b, self.d, self.d_prime, self.h,
            self.beton, self.acier,
        )
        assert res.As_min > 0

    def test_moment_faible_pas_erreur(self):
        """Un moment très faible ne doit pas provoquer d'erreur."""
        res = calcul_flexion_rectangulaire(
            1e6, self.b, self.d, self.d_prime, self.h,
            self.beton, self.acier,
        )
        assert res.calcul_valide

    def test_moment_nul(self):
        """Moment nul."""
        res = calcul_flexion_rectangulaire(
            0.0, self.b, self.d, self.d_prime, self.h,
            self.beton, self.acier,
        )
        assert res.calcul_valide
        assert res.As_requise >= 0
