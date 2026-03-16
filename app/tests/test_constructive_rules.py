"""Tests unitaires – Règles constructives."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.constructive_rules import verifier_regles_constructives


class TestReglesConstructives:
    """Tests des vérifications constructives."""

    def test_ferraillage_normal(self):
        """Ferraillage normal dans les limites."""
        res = verifier_regles_constructives(
            b_w=350.0, h=600.0, c_nom=30.0, diam_etrier=8.0,
            lits=[{"diametre": 16, "nombre": 4}],
            espacement_horizontal=25.0,
            espacement_vertical=25.0,
            d_g=20.0,
            nb_max_lits=4,
        )
        assert res.verifie is True

    def test_trop_de_lits(self):
        """Plus de lits que le maximum → erreur."""
        lits = [{"diametre": 12, "nombre": 3} for _ in range(5)]
        res = verifier_regles_constructives(
            b_w=350.0, h=600.0, c_nom=30.0, diam_etrier=8.0,
            lits=lits,
            nb_max_lits=4,
        )
        assert res.verifie is False

    def test_barres_ne_rentrent_pas(self):
        """Trop de barres dans la largeur → erreur."""
        res = verifier_regles_constructives(
            b_w=200.0, h=400.0, c_nom=30.0, diam_etrier=8.0,
            lits=[{"diametre": 32, "nombre": 6}],
        )
        assert res.verifie is False

    def test_avertissement_enrobage_faible(self):
        """Enrobage < 20 mm → avertissement."""
        res = verifier_regles_constructives(
            b_w=350.0, h=600.0, c_nom=15.0, diam_etrier=8.0,
            lits=[{"diametre": 16, "nombre": 4}],
        )
        # Doit contenir un avertissement sur l'enrobage
        msgs_avert = [m for m in res.messages if m["type"] == "avertissement"]
        assert len(msgs_avert) > 0

    def test_messages_contiennent_type(self):
        """Chaque message doit avoir un type et un message."""
        res = verifier_regles_constructives(
            b_w=350.0, h=600.0, c_nom=30.0, diam_etrier=8.0,
            lits=[{"diametre": 16, "nombre": 4}],
        )
        for msg in res.messages:
            assert "type" in msg
            assert "message" in msg
            assert msg["type"] in ("ok", "erreur", "avertissement")
