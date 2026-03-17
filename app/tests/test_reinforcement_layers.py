"""Tests pour la gestion des lits d'armatures avec positions verticales."""
from __future__ import annotations

import pytest

from app.core.reinforcement_layers import (
    ReinforcementLayer, TypeLit,
    compute_auto_first_distance_cm,
    recompute_layer_levels,
    add_layer, update_layer, delete_layer,
    move_layer_up, move_layer_down,
    compute_real_effective_depth,
    compute_layer_details,
    validate_layer_spacing,
)
from app.models.reinforcement_models import LitArmature, DonneesFerraillage


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Auto distance premier lit
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestAutoFirstDistance:
    """Vérifie le calcul automatique du premier lit."""

    def test_auto_distance_ha25(self):
        """c_nom=30mm, étrier=8mm, barre=25mm → (30+8+12.5)/10 = 5.05 cm."""
        d = compute_auto_first_distance_cm(30.0, 8.0, 25.0)
        assert d == pytest.approx(5.05, abs=0.01)

    def test_auto_distance_ha16(self):
        """c_nom=30mm, étrier=8mm, barre=16mm → (30+8+8)/10 = 4.6 cm."""
        d = compute_auto_first_distance_cm(30.0, 8.0, 16.0)
        assert d == pytest.approx(4.6, abs=0.01)

    def test_auto_distance_ha14(self):
        """c_nom=30mm, étrier=8mm, barre=14mm → (30+8+7)/10 = 4.5 cm."""
        d = compute_auto_first_distance_cm(30.0, 8.0, 14.0)
        assert d == pytest.approx(4.5, abs=0.01)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Ajout du premier lit
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestAddFirstLayer:
    """Ajout du premier lit avec distance à la fibre tendue."""

    def test_first_layer_manual(self):
        """Premier lit posé manuellement à 5 cm de la fibre tendue."""
        layers = []
        layer = ReinforcementLayer(
            n_bars=5, diameter_mm=25.0,
            spacing_from_previous_cm=5.0,
        )
        add_layer(layers, layer)
        assert len(layers) == 1
        assert layers[0].distance_from_tension_face_cm == 5.0
        assert layers[0].id == 1

    def test_first_layer_auto(self):
        """Premier lit en mode auto."""
        layers = []
        layer = ReinforcementLayer(
            n_bars=5, diameter_mm=25.0,
            auto_first=True,
        )
        add_layer(layers, layer, c_nom_mm=30.0, diam_etrier_mm=8.0)
        assert layers[0].distance_from_tension_face_cm == pytest.approx(5.05, abs=0.01)

    def test_first_layer_position_is_spacing(self):
        """La position absolue du 1er lit = sa distance à la fibre tendue."""
        layers = []
        layer = ReinforcementLayer(
            n_bars=5, diameter_mm=25.0,
            spacing_from_previous_cm=6.0,
        )
        add_layer(layers, layer)
        assert layers[0].distance_from_tension_face_cm == 6.0
        assert layers[0].spacing_from_previous_cm == 6.0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Ajout du deuxième lit et suivants
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestAddSubsequentLayers:
    """Ajout du 2e lit avec distance au lit précédent."""

    def test_second_layer_position(self):
        """Lit 2 à 6 cm du lit 1 (à 5 cm) → position absolue = 11 cm."""
        layers = []
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=25.0, spacing_from_previous_cm=5.0))
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=25.0, spacing_from_previous_cm=6.0))
        assert layers[1].distance_from_tension_face_cm == pytest.approx(11.0)
        assert layers[1].spacing_from_previous_cm == 6.0

    def test_third_layer_position(self):
        """Lit 3 à 3 cm du lit 2 → position absolue = 14 cm."""
        layers = []
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=25.0, spacing_from_previous_cm=5.0))
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=25.0, spacing_from_previous_cm=6.0))
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=16.0, spacing_from_previous_cm=3.0))
        assert layers[2].distance_from_tension_face_cm == pytest.approx(14.0)

    def test_fourth_layer_position(self):
        """Lit 4 à 5 cm du lit 3 → position absolue = 19 cm."""
        layers = []
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=25.0, spacing_from_previous_cm=5.0))
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=25.0, spacing_from_previous_cm=6.0))
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=16.0, spacing_from_previous_cm=3.0))
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=14.0, spacing_from_previous_cm=5.0))
        assert layers[3].distance_from_tension_face_cm == pytest.approx(19.0)

    def test_all_positions_example(self):
        """Vérifie toutes les positions de l'exemple du user :
        lit 1 à 5 cm, lit 2 à +6=11 cm, lit 3 à +3=14 cm, lit 4 à +5=19 cm."""
        layers = []
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=25.0, spacing_from_previous_cm=5.0))
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=25.0, spacing_from_previous_cm=6.0))
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=16.0, spacing_from_previous_cm=3.0))
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=14.0, spacing_from_previous_cm=5.0))

        assert [l.distance_from_tension_face_cm for l in layers] == pytest.approx([5, 11, 14, 19])

    def test_ids_are_sequential(self):
        """Les IDs doivent être 1, 2, 3, 4."""
        layers = []
        for _ in range(4):
            add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=25.0, spacing_from_previous_cm=5.0))
        assert [l.id for l in layers] == [1, 2, 3, 4]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Calcul de d réel
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestRealEffectiveDepth:
    """Vérifie le calcul de d réel à partir des positions explicites."""

    def test_single_layer(self):
        """Un seul lit à 5 cm, h=60 cm → d_réel = 600 - 50 = 550 mm."""
        layers = [ReinforcementLayer(n_bars=5, diameter_mm=25.0,
                                     distance_from_tension_face_cm=5.0)]
        d = compute_real_effective_depth(layers, h_mm=600.0)
        assert d == pytest.approx(550.0)

    def test_two_equal_layers(self):
        """Deux lits identiques : d_réel = moyenne pondérée."""
        layers = [
            ReinforcementLayer(n_bars=5, diameter_mm=25.0,
                               distance_from_tension_face_cm=5.0),
            ReinforcementLayer(n_bars=5, diameter_mm=25.0,
                               distance_from_tension_face_cm=11.0),
        ]
        d = compute_real_effective_depth(layers, h_mm=600.0)
        # d1=550, d2=490, même aire → d_reel = (550+490)/2 = 520
        assert d == pytest.approx(520.0)

    def test_four_layers_weighted(self):
        """4 lits avec diamètres différents → moyenne pondérée par aire."""
        import math
        layers = [
            ReinforcementLayer(n_bars=5, diameter_mm=25.0, distance_from_tension_face_cm=5.0),
            ReinforcementLayer(n_bars=5, diameter_mm=25.0, distance_from_tension_face_cm=11.0),
            ReinforcementLayer(n_bars=5, diameter_mm=16.0, distance_from_tension_face_cm=14.0),
            ReinforcementLayer(n_bars=5, diameter_mm=14.0, distance_from_tension_face_cm=19.0),
        ]
        d = compute_real_effective_depth(layers, h_mm=600.0)
        # Calcul manuel :
        a25 = 5 * math.pi * 25**2 / 4  # 2454.37
        a16 = 5 * math.pi * 16**2 / 4  # 1005.31
        a14 = 5 * math.pi * 14**2 / 4  # 769.69
        d1 = 600 - 50    # 550
        d2 = 600 - 110   # 490
        d3 = 600 - 140   # 460
        d4 = 600 - 190   # 410
        sum_ai_di = a25*d1 + a25*d2 + a16*d3 + a14*d4
        sum_ai = 2*a25 + a16 + a14
        expected = sum_ai_di / sum_ai
        assert d == pytest.approx(expected, rel=0.001)

    def test_compressed_layers_excluded(self):
        """Les lits comprimés ne participent pas au calcul de d_réel."""
        layers = [
            ReinforcementLayer(n_bars=5, diameter_mm=25.0,
                               distance_from_tension_face_cm=5.0),
            ReinforcementLayer(n_bars=5, diameter_mm=25.0,
                               distance_from_tension_face_cm=55.0,
                               layer_type=TypeLit.COMPRIME),
        ]
        d = compute_real_effective_depth(layers, h_mm=600.0)
        # Seul le lit tendu à 5 cm → d=550
        assert d == pytest.approx(550.0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Validation géométrique
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestValidateLayerSpacing:
    """Vérifie les contrôles géométriques des lits."""

    def test_valid_disposition(self):
        """Disposition correcte → valide."""
        layers = [
            ReinforcementLayer(id=1, n_bars=5, diameter_mm=25.0,
                               spacing_from_previous_cm=5.0,
                               distance_from_tension_face_cm=5.0),
            ReinforcementLayer(id=2, n_bars=5, diameter_mm=25.0,
                               spacing_from_previous_cm=6.0,
                               distance_from_tension_face_cm=11.0),
        ]
        r = validate_layer_spacing(layers, h_mm=600.0, d_mm=510.0)
        assert r.valid is True

    def test_negative_spacing(self):
        """Distance négative entre lits → erreur."""
        layers = [
            ReinforcementLayer(id=1, n_bars=5, diameter_mm=25.0,
                               spacing_from_previous_cm=5.0,
                               distance_from_tension_face_cm=5.0),
            ReinforcementLayer(id=2, n_bars=5, diameter_mm=25.0,
                               spacing_from_previous_cm=-2.0,
                               distance_from_tension_face_cm=3.0),
        ]
        r = validate_layer_spacing(layers, h_mm=600.0, d_mm=510.0)
        assert r.valid is False
        assert any("invalide" in m["message"].lower() for m in r.messages)

    def test_layer_outside_section(self):
        """Un lit qui dépasse la hauteur h → erreur."""
        layers = [
            ReinforcementLayer(id=1, n_bars=5, diameter_mm=25.0,
                               spacing_from_previous_cm=65.0,
                               distance_from_tension_face_cm=65.0),
        ]
        r = validate_layer_spacing(layers, h_mm=600.0, d_mm=510.0)
        assert r.valid is False
        assert any("dépasse" in m["message"].lower() for m in r.messages)

    def test_layer_beyond_effective_depth(self):
        """Un lit au-delà de d → avertissement (pas erreur)."""
        layers = [
            ReinforcementLayer(id=1, n_bars=5, diameter_mm=25.0,
                               spacing_from_previous_cm=52.0,
                               distance_from_tension_face_cm=52.0),
        ]
        r = validate_layer_spacing(layers, h_mm=600.0, d_mm=510.0)
        # 52 cm = 520 mm > d=510 mm but < h=600 mm → avertissement
        assert any(m["type"] == "avertissement" for m in r.messages)

    def test_first_layer_zero_distance(self):
        """Premier lit à 0 cm → erreur."""
        layers = [
            ReinforcementLayer(id=1, n_bars=5, diameter_mm=25.0,
                               spacing_from_previous_cm=0.0,
                               distance_from_tension_face_cm=0.0),
        ]
        r = validate_layer_spacing(layers, h_mm=600.0, d_mm=510.0)
        assert r.valid is False

    def test_insufficient_spacing_warning(self):
        """Espacement trop faible entre lits → avertissement."""
        layers = [
            ReinforcementLayer(id=1, n_bars=5, diameter_mm=25.0,
                               spacing_from_previous_cm=5.0,
                               distance_from_tension_face_cm=5.0),
            ReinforcementLayer(id=2, n_bars=5, diameter_mm=25.0,
                               spacing_from_previous_cm=1.0,
                               distance_from_tension_face_cm=6.0),
        ]
        r = validate_layer_spacing(layers, h_mm=600.0, d_mm=510.0)
        # 1.0 cm < max(25,25)/10 = 2.5 cm → avertissement
        assert any(m["type"] == "avertissement" for m in r.messages)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Suppression d'un lit
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestDeleteLayer:
    """Mise à jour correcte après suppression d'un lit."""

    def test_delete_middle_layer(self):
        """Supprimer le lit 2 de 3 → les positions se recalculent."""
        layers = []
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=25.0, spacing_from_previous_cm=5.0))
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=25.0, spacing_from_previous_cm=6.0))
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=16.0, spacing_from_previous_cm=3.0))
        # Positions : 5, 11, 14
        assert len(layers) == 3
        assert layers[2].distance_from_tension_face_cm == pytest.approx(14.0)

        delete_layer(layers, 1)  # Supprimer le lit 2 (index 1)
        assert len(layers) == 2
        assert layers[0].distance_from_tension_face_cm == pytest.approx(5.0)
        # Le lit 3 (devenu lit 2) garde son ancienne position absolue 14 cm
        # car son spacing hérite de la distance absolute qu'il avait
        assert layers[1].distance_from_tension_face_cm == pytest.approx(14.0)

    def test_delete_first_layer(self):
        """Supprimer le 1er lit → le 2e hérite de sa position absolue."""
        layers = []
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=25.0, spacing_from_previous_cm=5.0))
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=25.0, spacing_from_previous_cm=6.0))
        # Positions : 5, 11
        delete_layer(layers, 0)
        assert len(layers) == 1
        assert layers[0].distance_from_tension_face_cm == pytest.approx(11.0)
        assert layers[0].id == 1

    def test_ids_renumbered_after_delete(self):
        """Les IDs doivent être renumérotés après suppression."""
        layers = []
        for _ in range(4):
            add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=25.0, spacing_from_previous_cm=5.0))
        delete_layer(layers, 1)
        assert [l.id for l in layers] == [1, 2, 3]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Déplacement d'un lit
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestMoveLayer:
    """Mise à jour correcte après déplacement d'un lit."""

    def test_move_up(self):
        """Monter le lit 2 → échange avec lit 1."""
        layers = []
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=25.0, spacing_from_previous_cm=5.0))
        add_layer(layers, ReinforcementLayer(n_bars=3, diameter_mm=16.0, spacing_from_previous_cm=6.0))
        # Avant: [25mm, 16mm] aux positions [5, 11]
        move_layer_up(layers, 1)
        # Après: [16mm, 25mm]
        assert layers[0].diameter_mm == 16.0
        assert layers[1].diameter_mm == 25.0

    def test_move_down(self):
        """Descendre le lit 1 → échange avec lit 2."""
        layers = []
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=25.0, spacing_from_previous_cm=5.0))
        add_layer(layers, ReinforcementLayer(n_bars=3, diameter_mm=16.0, spacing_from_previous_cm=6.0))
        move_layer_down(layers, 0)
        assert layers[0].diameter_mm == 16.0
        assert layers[1].diameter_mm == 25.0

    def test_move_up_first_noop(self):
        """Monter le premier lit ne fait rien."""
        layers = []
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=25.0, spacing_from_previous_cm=5.0))
        add_layer(layers, ReinforcementLayer(n_bars=3, diameter_mm=16.0, spacing_from_previous_cm=6.0))
        move_layer_up(layers, 0)
        assert layers[0].diameter_mm == 25.0

    def test_move_down_last_noop(self):
        """Descendre le dernier lit ne fait rien."""
        layers = []
        add_layer(layers, ReinforcementLayer(n_bars=5, diameter_mm=25.0, spacing_from_previous_cm=5.0))
        add_layer(layers, ReinforcementLayer(n_bars=3, diameter_mm=16.0, spacing_from_previous_cm=6.0))
        move_layer_down(layers, 1)
        assert layers[1].diameter_mm == 16.0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Sérialisation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestSerialization:
    """Vérifie to_dict / from_dict."""

    def test_roundtrip(self):
        layer = ReinforcementLayer(
            id=2, n_bars=5, diameter_mm=25.0,
            layer_type=TypeLit.TENDU,
            spacing_from_previous_cm=6.0,
            distance_from_tension_face_cm=11.0,
            label="Lit principal",
        )
        d = layer.to_dict()
        restored = ReinforcementLayer.from_dict(d)
        assert restored.id == 2
        assert restored.n_bars == 5
        assert restored.diameter_mm == 25.0
        assert restored.layer_type == TypeLit.TENDU
        assert restored.spacing_from_previous_cm == 6.0
        assert restored.distance_from_tension_face_cm == 11.0
        assert restored.label == "Lit principal"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  LitArmature updated model
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestLitArmatureUpdated:
    """Vérifie les nouveaux champs de LitArmature."""

    def test_new_fields_default(self):
        lit = LitArmature(numero=1, nombre_barres=5, diametre_mm=25.0)
        assert lit.type_lit == "tendu"
        assert lit.espacement_precedent_cm == 5.0
        assert lit.distance_fibre_tendue_cm == 0.0
        assert lit.auto_first is False
        assert lit.label == ""

    def test_to_dict_includes_new_fields(self):
        lit = LitArmature(
            numero=1, nombre_barres=5, diametre_mm=25.0,
            type_lit="comprimé", espacement_precedent_cm=3.5,
            distance_fibre_tendue_cm=8.0, label="Test",
        )
        d = lit.to_dict()
        assert d["type_lit"] == "comprimé"
        assert d["espacement_precedent_cm"] == 3.5
        assert d["distance_fibre_tendue_cm"] == 8.0
        assert d["label"] == "Test"

    def test_from_dict_with_new_fields(self):
        d = {
            "numero": 2, "nombre_barres": 3, "diametre_mm": 16.0,
            "est_comprime": False,
            "type_lit": "tendu", "espacement_precedent_cm": 6.0,
            "distance_fibre_tendue_cm": 11.0,
        }
        lit = LitArmature.from_dict(d)
        assert lit.espacement_precedent_cm == 6.0
        assert lit.distance_fibre_tendue_cm == 11.0

    def test_from_dict_backward_compat(self):
        """Les anciens dicts sans les nouveaux champs doivent toujours charger."""
        d = {"numero": 1, "nombre_barres": 6, "diametre_mm": 16.0, "est_comprime": False}
        lit = LitArmature.from_dict(d)
        assert lit.nombre_barres == 6
        assert lit.type_lit == "tendu"  # default


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Layer details
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestLayerDetails:
    """Vérifie compute_layer_details."""

    def test_details_format(self):
        layers = [
            ReinforcementLayer(id=1, n_bars=5, diameter_mm=25.0,
                               distance_from_tension_face_cm=5.0),
        ]
        details = compute_layer_details(layers, h_mm=600.0)
        assert len(details) == 1
        d = details[0]
        assert d["lit_numero"] == 1
        assert d["nombre_barres"] == 5
        assert d["diametre_mm"] == 25.0
        assert d["distance_bord_tendu_mm"] == pytest.approx(50.0)
        assert d["d_i_mm"] == pytest.approx(550.0)
        assert d["type"] == "tendu"
        assert d["spacing_cm"] == 5.0
        assert d["absolute_cm"] == 5.0
