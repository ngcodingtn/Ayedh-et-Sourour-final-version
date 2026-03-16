"""Tests pour la décision du type de section (MEd_max vs MTu)."""
from __future__ import annotations

import pytest

from app.models.material_models import DonneesBeton, DonneesAcier
from app.core.section_decision import (
    compute_moment_reference_t_section,
    decide_section_type,
    validate_geometry,
    DecisionSection,
    SectionDecisionResult,
)
from app.core.units import MNm_to_Nmm, Nmm_to_kNm, m_to_mm


# Matériaux par défaut : fck=25, alpha_cc=1.0, gamma_c=1.5, eta=1.0
# → fcd = 25/1.5 = 16.667 MPa, fcu = 1.0 * 16.667 = 16.667 MPa
BETON = DonneesBeton(fck=25.0)
ACIER = DonneesAcier(fyk=500.0)
FCU = BETON.fcu  # 16.667 MPa


class TestComputeMTu:
    """Tests du calcul de MTu."""

    def test_mtu_exemple_1(self):
        """Exemple 1 du cours : beff=2660, hf=150, d=800, fcu≈16.667."""
        MTu = compute_moment_reference_t_section(
            b_eff=2660.0, h_f=150.0, fcu=FCU, d=800.0,
        )
        MTu_kNm = MTu / 1e6
        # MTu = 2660 * 150 * 16.667 * (800 - 75) = 4 823 478 750 N·mm ≈ 4823.5 kN·m
        assert MTu_kNm == pytest.approx(4823.5, rel=0.01)

    def test_mtu_positif(self):
        """MTu doit être positif pour des valeurs positives."""
        MTu = compute_moment_reference_t_section(
            b_eff=1000.0, h_f=100.0, fcu=20.0, d=500.0,
        )
        assert MTu > 0

    def test_mtu_formule(self):
        """Vérifie la formule directement : MTu = b_eff * hf * fcu * (d - hf/2)."""
        b, hf, fcu, d = 1500.0, 120.0, 15.0, 600.0
        attendu = b * hf * fcu * (d - hf / 2)
        MTu = compute_moment_reference_t_section(b, hf, fcu, d)
        assert MTu == pytest.approx(attendu)


class TestDecisionSection:
    """Tests de la décision rectangulaire vs section T."""

    def test_exemple_1_rectangulaire_equivalente(self):
        """Exemple 1 : MEd_max = 0.777 MN·m, MTu ≈ 4.82 MN·m → rectangulaire beff."""
        MEd_max = MNm_to_Nmm(0.777)
        dec = decide_section_type(
            MEd_max=MEd_max, b_eff=2660.0, b_w=220.0,
            h_f=150.0, h=850.0, d=800.0, fcu=FCU,
            moment_positif=True,
        )
        assert dec.decision == DecisionSection.RECTANGULAIRE_EQUIVALENTE_BEFF
        assert dec.design_width == 2660.0
        assert dec.MTu > MEd_max

    def test_exemple_2_section_T(self):
        """Exemple 2 : MEd_max = 3.04 MN·m, MTu ≈ 2.87 MN·m → section T."""
        # Diminuer beff pour que MTu < MEd_max
        # MTu = 1200 * 150 * 16.667 * (800 - 75) = 2 175 037 500 ≈ 2175 kN·m
        MEd_max = MNm_to_Nmm(3.04)  # 3040 kN·m
        dec = decide_section_type(
            MEd_max=MEd_max, b_eff=1200.0, b_w=220.0,
            h_f=150.0, h=850.0, d=800.0, fcu=FCU,
            moment_positif=True,
        )
        assert dec.decision == DecisionSection.SECTION_T
        assert dec.design_width == 220.0
        assert dec.MTu < MEd_max

    def test_exemple_3_moment_negatif(self):
        """Exemple 3 : moment négatif → toujours rectangulaire bw."""
        MEd_max = MNm_to_Nmm(0.5)
        dec = decide_section_type(
            MEd_max=MEd_max, b_eff=2660.0, b_w=220.0,
            h_f=150.0, h=850.0, d=800.0, fcu=FCU,
            moment_positif=False,
        )
        assert dec.decision == DecisionSection.RECTANGULAIRE_BW_NEGATIF
        assert dec.design_width == 220.0
        assert dec.moment_sign == "négatif"

    def test_moment_sign_positif(self):
        """Vérifie que le signe est bien retourné."""
        dec = decide_section_type(
            MEd_max=MNm_to_Nmm(0.1), b_eff=2000.0, b_w=200.0,
            h_f=100.0, h=500.0, d=450.0, fcu=FCU,
            moment_positif=True,
        )
        assert dec.moment_sign == "positif"

    def test_limite_exacte_MEd_egal_MTu(self):
        """Si MEd_max == MTu exactement, décision rectangulaire (≤)."""
        MTu = compute_moment_reference_t_section(2000.0, 100.0, FCU, 500.0)
        dec = decide_section_type(
            MEd_max=MTu, b_eff=2000.0, b_w=200.0,
            h_f=100.0, h=600.0, d=500.0, fcu=FCU,
            moment_positif=True,
        )
        assert dec.decision == DecisionSection.RECTANGULAIRE_EQUIVALENTE_BEFF

    def test_decision_result_fields(self):
        """Vérifie que tous les champs du SectionDecisionResult sont remplis."""
        MEd_max = MNm_to_Nmm(0.5)
        dec = decide_section_type(
            MEd_max=MEd_max, b_eff=2660.0, b_w=220.0,
            h_f=150.0, h=850.0, d=800.0, fcu=FCU,
            moment_positif=True,
        )
        assert dec.MEd_max == MEd_max
        assert dec.MTu > 0
        assert dec.design_width > 0
        assert len(dec.explanation) > 0


class TestValidateGeometry:
    """Tests de validation géométrique."""

    def test_valide(self):
        """Pas d'erreur pour des dimensions correctes."""
        erreurs = validate_geometry(
            b_eff=2660.0, b_w=220.0, h_f=150.0,
            h=850.0, d=800.0, MEd_max=1e6,
        )
        assert erreurs == []

    def test_beff_inferieur_bw(self):
        """Erreur si beff < bw."""
        erreurs = validate_geometry(
            b_eff=200.0, b_w=220.0, h_f=150.0,
            h=850.0, d=800.0, MEd_max=1e6,
        )
        assert any("b_eff" in e and "b_w" in e for e in erreurs)

    def test_hf_superieur_h(self):
        """Erreur si hf >= h."""
        erreurs = validate_geometry(
            b_eff=2660.0, b_w=220.0, h_f=900.0,
            h=850.0, d=800.0, MEd_max=1e6,
        )
        assert any("h_f" in e for e in erreurs)

    def test_d_superieur_h(self):
        """Erreur si d > h."""
        erreurs = validate_geometry(
            b_eff=2660.0, b_w=220.0, h_f=150.0,
            h=850.0, d=900.0, MEd_max=1e6,
        )
        assert any("d" in e and "h" in e for e in erreurs)

    def test_bw_negatif(self):
        """Erreur si bw ≤ 0."""
        erreurs = validate_geometry(
            b_eff=2660.0, b_w=0.0, h_f=150.0,
            h=850.0, d=800.0, MEd_max=1e6,
        )
        assert any("b_w" in e for e in erreurs)

    def test_MEd_negatif(self):
        """Erreur si MEd_max < 0."""
        erreurs = validate_geometry(
            b_eff=2660.0, b_w=220.0, h_f=150.0,
            h=850.0, d=800.0, MEd_max=-1e6,
        )
        assert any("MEd_max" in e for e in erreurs)


class TestDAutoCalcul:
    """Tests du calcul automatique de d = 0.9*h."""

    def test_d_auto_si_non_fourni(self):
        """Si d=0 et d_auto=True, d doit être 0.9*h."""
        from app.models.section_models import DonneesGeometrie, TypeSection
        geo = DonneesGeometrie(
            type_section=TypeSection.T,
            b_eff=2660.0, b_w=220.0, h_f=150.0,
            h=850.0, d=0.0, d_auto=True,
        )
        assert geo.hauteur_utile_effective() == pytest.approx(0.9 * 850.0)

    def test_d_fourni_non_ecrase(self):
        """Si d est fourni, on ne le remplace pas."""
        from app.models.section_models import DonneesGeometrie, TypeSection
        geo = DonneesGeometrie(
            type_section=TypeSection.T,
            b_eff=2660.0, b_w=220.0, h_f=150.0,
            h=850.0, d=800.0, d_auto=True,
        )
        assert geo.hauteur_utile_effective() == 800.0


class TestIntegrationDecision:
    """Tests d'intégration : la décision est correctement transmise au résultat ELU."""

    def test_calcul_T_rectangulaire_equiv_a_decision(self):
        """calcul_flexion_T avec MEd_max < MTu → decision RECTANGULAIRE_EQUIVALENTE_BEFF."""
        from app.core.flexion_t_beam import calcul_flexion_T
        MEd_max = MNm_to_Nmm(0.777)
        res = calcul_flexion_T(
            MEd_max, b_eff=2660.0, b_w=220.0, h_f=150.0,
            h=850.0, d=800.0, d_prime=50.0,
            beton=BETON, acier=ACIER, moment_positif=True,
        )
        assert res.calcul_valide
        assert res.decision is not None
        assert res.decision.decision == DecisionSection.RECTANGULAIRE_EQUIVALENTE_BEFF

    def test_calcul_T_section_T_a_decision(self):
        """calcul_flexion_T avec MEd_max > MTu → decision SECTION_T."""
        from app.core.flexion_t_beam import calcul_flexion_T
        MEd_max = MNm_to_Nmm(3.04)
        res = calcul_flexion_T(
            MEd_max, b_eff=1200.0, b_w=220.0, h_f=150.0,
            h=850.0, d=800.0, d_prime=50.0,
            beton=BETON, acier=ACIER, moment_positif=True,
        )
        assert res.calcul_valide
        assert res.decision is not None
        assert res.decision.decision == DecisionSection.SECTION_T

    def test_calcul_T_moment_negatif_a_decision(self):
        """calcul_flexion_T avec moment négatif → decision RECTANGULAIRE_BW_NEGATIF."""
        from app.core.flexion_t_beam import calcul_flexion_T
        MEd_max = MNm_to_Nmm(0.5)
        res = calcul_flexion_T(
            MEd_max, b_eff=2660.0, b_w=220.0, h_f=150.0,
            h=850.0, d=800.0, d_prime=50.0,
            beton=BETON, acier=ACIER, moment_positif=False,
        )
        assert res.calcul_valide
        assert res.decision is not None
        assert res.decision.decision == DecisionSection.RECTANGULAIRE_BW_NEGATIF
