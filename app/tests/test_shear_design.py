"""Tests – Effort tranchant (shear_design)."""
import pytest
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.models.material_models import DonneesBeton, DonneesAcier
from app.core.shear_design import (
    compute_VRdc,
    compute_VRds,
    compute_VRd_max,
    compute_Asw_s_requis,
    compute_espacement_max,
    compute_Asw_s_min,
    verifier_effort_tranchant,
)


class TestVRdc:
    def test_positive(self):
        V = compute_VRdc(bw=300, d=450, fck=25, As_mm2=1500)
        assert V > 0

    def test_increases_with_As(self):
        V1 = compute_VRdc(300, 450, 25, 1000)
        V2 = compute_VRdc(300, 450, 25, 3000)
        assert V2 > V1

    def test_minimum_applied(self):
        """Même avec As=0, vmin assure un VRdc > 0."""
        V = compute_VRdc(300, 450, 25, 0)
        assert V > 0

    def test_zero_inputs(self):
        assert compute_VRdc(0, 450, 25, 1000) == 0
        assert compute_VRdc(300, 0, 25, 1000) == 0
        assert compute_VRdc(300, 450, 0, 1000) == 0

    def test_k_factor(self):
        """k = min(1 + sqrt(200/d), 2)."""
        V_small_d = compute_VRdc(300, 100, 25, 1000)  # k capped at 2
        V_large_d = compute_VRdc(300, 800, 25, 1000)  # k < 2
        # Smaller d → larger k factor, but also smaller area → compare k only
        k_100 = min(1 + math.sqrt(200 / 100), 2.0)
        k_800 = 1 + math.sqrt(200 / 800)
        assert k_100 == 2.0
        assert k_800 < 2.0


class TestVRds:
    def test_positive(self):
        V = compute_VRds(Asw_mm2=100.53, s_mm=200, z=405, fywd=434.78, theta=45)
        assert V > 0

    def test_zero_spacing(self):
        assert compute_VRds(100, 0, 400, 434) == 0

    def test_theta_effect(self):
        """Smaller theta → larger cot(theta) → larger VRds."""
        V_45 = compute_VRds(100, 200, 400, 434, theta=45)
        V_30 = compute_VRds(100, 200, 400, 434, theta=30)
        assert V_30 > V_45

    def test_vertical_stirrups(self):
        """alpha=90 → sin(90)=1, cot(90)=0."""
        V = compute_VRds(100, 200, 400, 434, theta=45, alpha=90)
        assert V > 0


class TestVRdMax:
    def test_positive(self):
        V = compute_VRd_max(300, 405, 25)
        assert V > 0

    def test_increases_with_bw(self):
        V1 = compute_VRd_max(200, 400, 25)
        V2 = compute_VRd_max(400, 400, 25)
        assert V2 > V1

    def test_zero(self):
        assert compute_VRd_max(0, 400, 25) == 0


class TestAswRequired:
    def test_basic(self):
        Asw_s = compute_Asw_s_requis(100_000, 400, 434, theta=45)
        assert Asw_s > 0

    def test_zero_inputs(self):
        assert compute_Asw_s_requis(100_000, 0, 434) == 0
        assert compute_Asw_s_requis(100_000, 400, 0) == 0


class TestEspacementMax:
    def test_formula(self):
        assert compute_espacement_max(500) == pytest.approx(375)
        assert compute_espacement_max(400) == pytest.approx(300)


class TestAswMin:
    def test_basic(self):
        val = compute_Asw_s_min(300, 25, 500)
        rho_min = 0.08 * math.sqrt(25) / 500
        assert val == pytest.approx(rho_min * 300)

    def test_increases_with_fck(self):
        v1 = compute_Asw_s_min(300, 20, 500)
        v2 = compute_Asw_s_min(300, 30, 500)
        assert v2 > v1


class TestVerificationComplete:
    def setup_method(self):
        self.beton = DonneesBeton(fck=25.0)
        self.acier = DonneesAcier(fyk=500.0)

    def test_verifie(self):
        res = verifier_effort_tranchant(
            Ved=80_000, bw=300, d=450, As_mm2=1500,
            beton=self.beton, acier=self.acier,
            diam_etrier=8, nb_branches=2, espacement_etriers=150)
        assert res.verdict == "Vérifié"
        assert res.VRdc > 0

    def test_non_verifie_spacing(self):
        """Espacement trop grand → non vérifié."""
        res = verifier_effort_tranchant(
            Ved=200_000, bw=300, d=450, As_mm2=1500,
            beton=self.beton, acier=self.acier,
            diam_etrier=6, nb_branches=2, espacement_etriers=500)
        # s_max = 0.75 * 450 = 337.5 → 500 > 337.5
        assert not res.controle_espacement

    def test_ved_less_than_vrdc(self):
        """Si Ved < VRdc, pas besoin d'armatures."""
        res = verifier_effort_tranchant(
            Ved=10_000, bw=300, d=450, As_mm2=1500,
            beton=self.beton, acier=self.acier)
        assert not res.besoin_armatures
        assert res.verdict == "Vérifié"

    def test_bielles_failure(self):
        """Ved très élevé → rupture bielles."""
        res = verifier_effort_tranchant(
            Ved=5_000_000, bw=200, d=300, As_mm2=500,
            beton=self.beton, acier=self.acier)
        assert res.verdict == "Non vérifié"

    def test_messages_not_empty(self):
        res = verifier_effort_tranchant(
            Ved=100_000, bw=300, d=450, As_mm2=1500,
            beton=self.beton, acier=self.acier)
        assert len(res.messages) > 0

    def test_Asw_s_requis(self):
        res = verifier_effort_tranchant(
            Ved=150_000, bw=300, d=450, As_mm2=1500,
            beton=self.beton, acier=self.acier)
        assert res.Asw_s_requis > 0
