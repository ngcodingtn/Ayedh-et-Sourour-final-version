"""Tests unitaires – Aciers comprimés, persistance JSON, rapport."""
import math
import json
import tempfile
import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.models.material_models import DonneesBeton, DonneesAcier, DonneesMateriaux
from app.models.section_models import DonneesGeometrie, TypeSection
from app.models.load_models import DonneesSollicitations
from app.models.reinforcement_models import DonneesFerraillage, LitArmature, DonneesEnvironnement
from app.core.flexion_rectangular import calcul_flexion_rectangulaire
from app.core.units import MNm_to_Nmm, Nmm_to_kNm
from app.services.calculation_service import calcul_complet
from app.services.persistence_service import sauvegarder_projet, charger_projet
from app.core.examples import exemple_rectangulaire, exemple_section_T, exemple_aciers_comprimes


class TestAciersComprimes:
    """Tests pour le cas avec aciers comprimés.

    Section rectangulaire fortement sollicitée :
    bw=250, h=400, d=360, d'=40
    fck=25, fyk=500
    MEd élevé → mu_cu > mu_ulim
    """

    def setup_method(self):
        self.beton = DonneesBeton(fck=25.0)
        self.acier = DonneesAcier(fyk=500.0)

    def test_aciers_comprimes_necessaires(self):
        """Un moment suffisamment élevé requiert des aciers comprimés."""
        M_Ed = MNm_to_Nmm(0.220)
        res = calcul_flexion_rectangulaire(
            M_Ed, b=250.0, d=360.0, d_prime=40.0, h=400.0,
            beton=self.beton, acier=self.acier,
        )
        assert res.calcul_valide
        assert res.necessite_aciers_comprimes is True
        assert res.As_comp_requise > 0
        assert res.As_requise > 0

    def test_Mlu_positif(self):
        """Le moment limite Mlu doit être positif."""
        M_Ed = MNm_to_Nmm(0.220)
        res = calcul_flexion_rectangulaire(
            M_Ed, b=250.0, d=360.0, d_prime=40.0, h=400.0,
            beton=self.beton, acier=self.acier,
        )
        assert res.Mlu > 0

    def test_commentaire_compression(self):
        """Un commentaire doit expliquer le cas comprimé."""
        M_Ed = MNm_to_Nmm(0.220)
        res = calcul_flexion_rectangulaire(
            M_Ed, b=250.0, d=360.0, d_prime=40.0, h=400.0,
            beton=self.beton, acier=self.acier,
        )
        assert len(res.commentaire_compression) > 0
        assert "comprimé" in res.commentaire_compression.lower() or "μcu" in res.commentaire_compression

    def test_moment_limite_pas_aciers_comprimes(self):
        """Un moment faible ne nécessite pas d'aciers comprimés."""
        M_Ed = MNm_to_Nmm(0.050)
        res = calcul_flexion_rectangulaire(
            M_Ed, b=250.0, d=360.0, d_prime=40.0, h=400.0,
            beton=self.beton, acier=self.acier,
        )
        assert res.calcul_valide
        assert res.necessite_aciers_comprimes is False


class TestPersistanceJSON:
    """Tests de sauvegarde et chargement JSON."""

    def test_sauvegarder_et_charger(self):
        """Round-trip : sauvegarder puis recharger."""
        ex = exemple_rectangulaire()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            chemin = f.name

        try:
            sauvegarder_projet(
                chemin,
                ex["geometrie"], ex["materiaux"],
                ex["sollicitations"], ex["ferraillage"],
                ex["environnement"],
            )

            # Vérifier que le fichier existe et est du JSON valide
            with open(chemin, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert "geometrie" in data
            assert "materiaux" in data
            assert "sollicitations" in data

            # Recharger
            loaded = charger_projet(chemin)
            assert loaded["geometrie"].b_w == ex["geometrie"].b_w
            assert loaded["geometrie"].h == ex["geometrie"].h
            assert loaded["materiaux"].beton.fck == ex["materiaux"].beton.fck
            assert loaded["sollicitations"].M_Ed == pytest.approx(ex["sollicitations"].M_Ed, rel=1e-6)

        finally:
            os.unlink(chemin)

    def test_json_structure(self):
        """Le JSON doit avoir la bonne structure."""
        ex = exemple_rectangulaire()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            chemin = f.name

        try:
            sauvegarder_projet(
                chemin,
                ex["geometrie"], ex["materiaux"],
                ex["sollicitations"], ex["ferraillage"],
                ex["environnement"],
            )

            with open(chemin, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert data["version"] == "1.0"
            assert data["geometrie"]["type_section"] == "Rectangulaire"
            assert data["materiaux"]["beton"]["fck"] == 25.0
            assert data["materiaux"]["acier"]["fyk"] == 500.0

        finally:
            os.unlink(chemin)

    def test_type_section_roundtrip(self):
        """Le type de section doit survivre au round-trip."""
        ex = exemple_section_T()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            chemin = f.name

        try:
            sauvegarder_projet(
                chemin,
                ex["geometrie"], ex["materiaux"],
                ex["sollicitations"], ex["ferraillage"],
                ex["environnement"],
            )
            loaded = charger_projet(chemin)
            assert loaded["geometrie"].type_section == TypeSection.T
        finally:
            os.unlink(chemin)


class TestRapportPDF:
    """Tests de génération du rapport PDF."""

    def test_generer_rapport(self):
        """Le rapport PDF doit être généré sans erreur."""
        ex = exemple_rectangulaire()
        geo = ex["geometrie"]
        mat = ex["materiaux"]
        sol = ex["sollicitations"]
        fer = ex["ferraillage"]
        env = ex["environnement"]

        resultats = calcul_complet(geo, mat, sol, fer, env)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            chemin = f.name

        try:
            from app.reports.pdf_report import generer_pdf
            generer_pdf(chemin, geo, mat, sol, fer, env, resultats)

            # Vérifier que le fichier existe et n'est pas vide
            assert os.path.exists(chemin)
            assert os.path.getsize(chemin) > 1000  # au moins 1 Ko

        finally:
            os.unlink(chemin)


class TestCalculComplet:
    """Tests du service de calcul complet."""

    def test_exemple_rectangulaire_complet(self):
        """Le calcul complet sur l'exemple rectangulaire doit fonctionner."""
        ex = exemple_rectangulaire()
        res = calcul_complet(
            ex["geometrie"], ex["materiaux"], ex["sollicitations"],
            ex["ferraillage"], ex["environnement"],
        )
        assert res.elu.calcul_valide
        assert res.verification is not None
        assert res.verification.verdict_global is True
        assert res.constructif is not None
        assert res.fissuration is not None

    def test_exemple_section_T_complet(self):
        """Le calcul complet sur l'exemple T doit fonctionner."""
        ex = exemple_section_T()
        res = calcul_complet(
            ex["geometrie"], ex["materiaux"], ex["sollicitations"],
            ex["ferraillage"], ex["environnement"],
        )
        assert res.elu.calcul_valide

    def test_donnees_invalides(self):
        """Données invalides → erreurs retournées."""
        geo = DonneesGeometrie(b_w=0, h=0, d=0)
        mat = DonneesMateriaux()
        sol = DonneesSollicitations(M_Ed=100e6)
        fer = DonneesFerraillage()
        env = DonneesEnvironnement()

        res = calcul_complet(geo, mat, sol, fer, env)
        assert not res.elu.calcul_valide
        assert len(res.elu.erreurs) > 0
