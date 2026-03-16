"""Tests unitaires – Fissuration et ELS."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.models.material_models import DonneesBeton, DonneesAcier
from app.core.cracking import controle_fissuration
from app.core.serviceability import (
    calculer_moment_fissuration, section_fissuree, calculer_contraintes_service,
)
from app.core.units import MNm_to_Nmm


class TestFissuration:
    """Tests du contrôle de fissuration."""

    def setup_method(self):
        self.beton = DonneesBeton(fck=25.0)
        self.acier = DonneesAcier(fyk=500.0)

    def test_fissuration_verifiee(self):
        """Ferraillage correct avec classe XC1 → vérifié."""
        res = controle_fissuration(
            classe_exposition="XC1",
            As_reelle_mm2=2500.0,
            b=350.0, d=540.0, h=600.0,
            M_ser=MNm_to_Nmm(0.2376),
            beton=self.beton, acier=self.acier,
            diam_max_propose=10.0,
            espacement_propose=60.0,
        )
        assert res.verdict in ("Vérifié", "Vérifié sous réserve")

    def test_fissuration_As_min(self):
        """As_réelle >= As_min → contrôle OK."""
        res = controle_fissuration(
            classe_exposition="XC1",
            As_reelle_mm2=1700.0,
            b=350.0, d=540.0, h=600.0,
            M_ser=MNm_to_Nmm(0.2376),
            beton=self.beton, acier=self.acier,
        )
        assert res.controle_As_min is True

    def test_fissuration_As_insuffisante(self):
        """As trop faible → contrôle As_min KO."""
        res = controle_fissuration(
            classe_exposition="XC1",
            As_reelle_mm2=50.0,  # trop faible
            b=350.0, d=540.0, h=600.0,
            M_ser=MNm_to_Nmm(0.2376),
            beton=self.beton, acier=self.acier,
        )
        assert res.controle_As_min is False

    def test_classe_XD3_avertissement(self):
        """Classe XD3 → dispositions particulières."""
        res = controle_fissuration(
            classe_exposition="XD3",
            As_reelle_mm2=1700.0,
            b=350.0, d=540.0, h=600.0,
            M_ser=MNm_to_Nmm(0.2376),
            beton=self.beton, acier=self.acier,
        )
        assert res.verdict == "Vérifié sous réserve"
        assert any("particulières" in m for m in res.messages)

    def test_wmax_recommande(self):
        """wmax doit être retourné pour XC1."""
        res = controle_fissuration(
            classe_exposition="XC1",
            As_reelle_mm2=1700.0,
            b=350.0, d=540.0, h=600.0,
            M_ser=MNm_to_Nmm(0.2376),
            beton=self.beton, acier=self.acier,
        )
        assert res.wmax_recommande == 0.30

    def test_wmax_X0(self):
        """wmax pour X0 = 0.40."""
        res = controle_fissuration(
            classe_exposition="X0",
            As_reelle_mm2=1700.0,
            b=350.0, d=540.0, h=600.0,
            M_ser=MNm_to_Nmm(0.100),
            beton=self.beton, acier=self.acier,
        )
        assert res.wmax_recommande == 0.40


class TestServiceabilite:
    """Tests des calculs ELS."""

    def test_moment_fissuration_positif(self):
        """Mcr doit être positif."""
        beton = DonneesBeton(fck=25.0)
        Mcr = calculer_moment_fissuration(beton, 350.0, 600.0)
        assert Mcr > 0

    def test_section_fissuree_sous_moment_eleve(self):
        """Un moment élevé doit fissurer la section."""
        beton = DonneesBeton(fck=25.0)
        Mcr = calculer_moment_fissuration(beton, 350.0, 600.0)
        assert section_fissuree(MNm_to_Nmm(0.300), Mcr) is True

    def test_section_non_fissuree_moment_faible(self):
        """Un moment très faible ne fissure pas."""
        beton = DonneesBeton(fck=25.0)
        Mcr = calculer_moment_fissuration(beton, 350.0, 600.0)
        assert section_fissuree(1e3, Mcr) is False

    def test_contraintes_service(self):
        """Les contraintes en service doivent être positives."""
        alpha_e = 200000 / (22000 * (25/10 + 8)**0.3)
        result = calculer_contraintes_service(
            M_ser=MNm_to_Nmm(0.2376),
            b=350.0, d=540.0,
            As_mm2=1700.0,
            alpha_e=alpha_e,
        )
        assert result["sigma_c"] > 0
        assert result["sigma_s"] > 0
        assert result["x_ser"] > 0
        assert result["z_ser"] > 0
