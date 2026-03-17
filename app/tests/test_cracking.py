"""Tests complets – Fissuration et ELS."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.models.material_models import DonneesBeton, DonneesAcier
from app.core.cracking import (
    controle_fissuration, compute_as_min,
    check_crack_control_without_direct_calculation,
    prepare_direct_crack_calculation,
)
from app.core.serviceability import (
    compute_mcr, is_cracked_section,
    compute_service_stresses_uncracked,
    compute_service_stresses_cracked,
    check_service_stresses,
    calculer_moment_fissuration, section_fissuree,
    calculer_contraintes_service,
)
from app.core.units import MNm_to_Nmm


class TestMcr:
    def setup_method(self):
        self.beton = DonneesBeton(fck=25.0)

    def test_mcr_rect(self):
        fctm = self.beton.fctm
        mcr = compute_mcr(fctm, 300, 500)
        expected = fctm * 300 * 500**2 / 6.0
        assert mcr == pytest.approx(expected, rel=1e-6)

    def test_mcr_zero_height(self):
        assert compute_mcr(self.beton.fctm, 300, 0) == 0.0

    def test_mcr_section_T(self):
        fctm = self.beton.fctm
        mcr_rect = compute_mcr(fctm, 200, 500)
        mcr_T = compute_mcr(fctm, 200, 500, "t", 600, 200, 100)
        assert mcr_T > mcr_rect

    def test_retro_compat(self):
        old = calculer_moment_fissuration(self.beton, 300, 500)
        new = compute_mcr(self.beton.fctm, 300, 500)
        assert old == pytest.approx(new, rel=1e-6)


class TestCrackedState:
    def test_non_fissuree(self):
        beton = DonneesBeton(fck=25.0)
        mcr = compute_mcr(beton.fctm, 300, 500)
        assert not is_cracked_section(mcr * 0.5, mcr)

    def test_fissuree(self):
        beton = DonneesBeton(fck=25.0)
        mcr = compute_mcr(beton.fctm, 300, 500)
        assert is_cracked_section(mcr * 1.5, mcr)

    def test_section_fissuree_sous_moment_eleve(self):
        beton = DonneesBeton(fck=25.0)
        Mcr = calculer_moment_fissuration(beton, 350.0, 600.0)
        assert section_fissuree(MNm_to_Nmm(0.300), Mcr) is True

    def test_section_non_fissuree_moment_faible(self):
        beton = DonneesBeton(fck=25.0)
        Mcr = calculer_moment_fissuration(beton, 350.0, 600.0)
        assert section_fissuree(MNm_to_Nmm(0.001), Mcr) is False


class TestStressesUncracked:
    def test_basic(self):
        result = compute_service_stresses_uncracked(
            M_ser=100e6, b=300, h=500, As_mm2=1500, alpha_e=15, d=450)
        assert result["sigma_c"] > 0
        assert result["sigma_s"] > 0
        assert result["yG"] == pytest.approx(250, rel=1e-6)

    def test_zero_moment(self):
        result = compute_service_stresses_uncracked(
            M_ser=0, b=300, h=500, As_mm2=1500, alpha_e=15)
        assert result["sigma_c"] == 0
        assert result["sigma_s"] == 0


class TestStressesCracked:
    def test_basic(self):
        result = compute_service_stresses_cracked(
            M_ser=100e6, b=300, d=450, As_mm2=1500, alpha_e=15)
        assert result["sigma_c"] > 0
        assert result["sigma_s"] > 0
        assert 0 < result["x_ser"] < 450
        assert result["I_fiss"] > 0

    def test_section_T(self):
        result = compute_service_stresses_cracked(
            M_ser=100e6, b=200, d=450, As_mm2=1500, alpha_e=15,
            type_section="t", beff=600, bw=200, hf=100)
        assert result["sigma_c"] > 0
        assert result["sigma_s"] > 0

    def test_retro_compat(self):
        old = calculer_contraintes_service(100e6, 300, 450, 1500, 15)
        new = compute_service_stresses_cracked(100e6, 300, 450, 1500, 15)
        assert old["sigma_c"] == pytest.approx(new["sigma_c"], rel=1e-6)


class TestStressLimits:
    def test_ok(self):
        r = check_service_stresses(10, 200, 25, 500)
        assert r["global_ok"]

    def test_sigma_c_fail(self):
        r = check_service_stresses(20, 200, 25, 500)
        assert not r["sigma_c_ok"]

    def test_sigma_s_fail(self):
        r = check_service_stresses(10, 450, 25, 500)
        assert not r["sigma_s_ok"]


class TestAsMin:
    def test_basic(self):
        beton = DonneesBeton(fck=25.0)
        acier = DonneesAcier(fyk=500.0)
        As_min = compute_as_min(beton, acier, 300, 450)
        assert As_min > 0
        val1 = 0.26 * beton.fctm / 500 * 300 * 450
        val2 = 0.0013 * 300 * 450
        assert As_min == pytest.approx(max(val1, val2), rel=1e-6)


class TestCrackControlSimplified:
    def test_ok(self):
        r = check_crack_control_without_direct_calculation(200, 0.3, 16, 150)
        assert r["verdict"]

    def test_diameter_fail(self):
        r = check_crack_control_without_direct_calculation(300, 0.3, 20, 80)
        assert not r["controle_diametre"]

    def test_spacing_fail(self):
        r = check_crack_control_without_direct_calculation(300, 0.3, 8, 250)
        assert not r["controle_espacement"]


class TestDirectCrack:
    def test_prepare(self):
        r = prepare_direct_crack_calculation(250, 200_000, 2.6, 0.01, 16, 30)
        assert r["sr_max"] > 0
        assert r["wk"] >= 0


class TestControleComplet:
    def setup_method(self):
        self.beton = DonneesBeton(fck=25.0)
        self.acier = DonneesAcier(fyk=500.0)

    def test_verifiee(self):
        res = controle_fissuration(
            classe_exposition="XC1", As_reelle_mm2=2500,
            b=350, d=540, h=600, M_ser=MNm_to_Nmm(0.120),
            beton=self.beton, acier=self.acier,
            diam_max_propose=10, espacement_propose=60)
        assert res.verdict in ("Vérifié", "Vérifié sous réserve")
        assert res.Mcr > 0

    def test_As_min_ok(self):
        res = controle_fissuration(
            classe_exposition="XC1", As_reelle_mm2=1700,
            b=350, d=540, h=600, M_ser=MNm_to_Nmm(0.2376),
            beton=self.beton, acier=self.acier)
        assert res.controle_As_min

    def test_As_insuffisante(self):
        res = controle_fissuration(
            classe_exposition="XC1", As_reelle_mm2=50,
            b=350, d=540, h=600, M_ser=MNm_to_Nmm(0.2376),
            beton=self.beton, acier=self.acier)
        assert not res.controle_As_min
        assert res.verdict == "Non vérifié"

    def test_XD3(self):
        res = controle_fissuration(
            classe_exposition="XD3", As_reelle_mm2=1700,
            b=350, d=540, h=600, M_ser=MNm_to_Nmm(0.2376),
            beton=self.beton, acier=self.acier)
        assert res.verdict == "Vérifié sous réserve"

    def test_wmax_XC1(self):
        res = controle_fissuration(
            classe_exposition="XC1", As_reelle_mm2=1700,
            b=350, d=540, h=600, M_ser=MNm_to_Nmm(0.100),
            beton=self.beton, acier=self.acier)
        assert res.wmax_recommande == 0.30

    def test_section_T(self):
        res = controle_fissuration(
            classe_exposition="XC1", As_reelle_mm2=2000,
            b=200, d=450, h=500, M_ser=150e6,
            beton=self.beton, acier=self.acier,
            type_section="t", beff=600, bw=200, hf=100)
        assert res.Mcr > 0
        assert res.sigma_s_service > 0

    def test_section_non_fissuree(self):
        mcr = compute_mcr(self.beton.fctm, 300, 500)
        res = controle_fissuration(
            classe_exposition="XC1", As_reelle_mm2=1500,
            b=300, d=450, h=500, M_ser=mcr * 0.3,
            beton=self.beton, acier=self.acier)
        assert not res.section_fissuree

    def test_section_fissuree(self):
        res = controle_fissuration(
            classe_exposition="XC1", As_reelle_mm2=1500,
            b=300, d=450, h=500, M_ser=200e6,
            beton=self.beton, acier=self.acier)
        assert res.section_fissuree
        assert res.sigma_s_service > 0
        assert res.sigma_c_service > 0
