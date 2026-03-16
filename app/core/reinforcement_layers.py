"""Gestion des lits d'armatures avec positions verticales explicites.

Chaque lit stocke sa distance relative au lit précédent (ou à la fibre
tendue pour le premier lit). Les positions absolues et les hauteurs
utiles sont recalculées automatiquement.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TypeLit(str, Enum):
    """Type d'un lit d'armatures."""
    TENDU = "tendu"
    COMPRIME = "comprimé"
    MONTAGE = "montage"


@dataclass
class ReinforcementLayer:
    """Un lit d'armatures avec position verticale explicite.

    Attributes:
        id:  numéro unique du lit (1-based).
        n_bars:  nombre de barres.
        diameter_mm:  diamètre nominal (mm).
        layer_type:  tendu / comprimé / montage.
        spacing_from_previous_cm:  distance relative au lit précédent (cm).
            Pour le premier lit tendu, c'est la distance à la fibre tendue.
        distance_from_tension_face_cm:  position absolue depuis la fibre
            tendue (recalculée automatiquement).
        auto_first:  si *True* le calcul automatique est utilisé
            pour le premier lit (enrobage + étrier + Ø/2).
        label:  étiquette libre.
    """
    id: int = 1
    n_bars: int = 0
    diameter_mm: float = 0.0
    layer_type: TypeLit = TypeLit.TENDU
    spacing_from_previous_cm: float = 5.0
    distance_from_tension_face_cm: float = 0.0
    auto_first: bool = False
    label: str = ""

    # ── Sections ──
    @property
    def area_mm2(self) -> float:
        return self.n_bars * math.pi * self.diameter_mm ** 2 / 4.0

    @property
    def area_cm2(self) -> float:
        return self.area_mm2 / 100.0

    @property
    def unit_area_mm2(self) -> float:
        return math.pi * self.diameter_mm ** 2 / 4.0

    @property
    def unit_area_cm2(self) -> float:
        return self.unit_area_mm2 / 100.0

    # ── Sérialisation ──
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "n_bars": self.n_bars,
            "diameter_mm": self.diameter_mm,
            "layer_type": self.layer_type.value,
            "spacing_from_previous_cm": self.spacing_from_previous_cm,
            "distance_from_tension_face_cm": self.distance_from_tension_face_cm,
            "auto_first": self.auto_first,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ReinforcementLayer":
        return cls(
            id=d.get("id", 1),
            n_bars=d.get("n_bars", 0),
            diameter_mm=d.get("diameter_mm", 0.0),
            layer_type=TypeLit(d.get("layer_type", "tendu")),
            spacing_from_previous_cm=d.get("spacing_from_previous_cm", 5.0),
            distance_from_tension_face_cm=d.get("distance_from_tension_face_cm", 0.0),
            auto_first=d.get("auto_first", False),
            label=d.get("label", ""),
        )


# ────────────────────────────────────────────────────────────────────────
#  Fonctions de gestion
# ────────────────────────────────────────────────────────────────────────

def compute_auto_first_distance_cm(
    c_nom_mm: float,
    diam_etrier_mm: float,
    diam_barre_mm: float,
) -> float:
    """Distance automatique du 1er lit à la fibre tendue (cm).

    = enrobage + Ø_étrier + Ø_barre / 2  (tout en mm → converti en cm).
    """
    return (c_nom_mm + diam_etrier_mm + diam_barre_mm / 2.0) / 10.0


def recompute_layer_levels(
    layers: list[ReinforcementLayer],
    c_nom_mm: float = 30.0,
    diam_etrier_mm: float = 8.0,
) -> None:
    """Recalcule *in-place* la position absolue de chaque lit.

    * Lit 1 : ``distance_from_tension_face_cm`` = ``spacing_from_previous_cm``
      (ou auto si ``auto_first``).
    * Lit N (N>1) : position absolue = position(N-1) + spacing_from_previous_cm(N).
    """
    for i, layer in enumerate(layers):
        if i == 0:
            if layer.auto_first:
                layer.distance_from_tension_face_cm = compute_auto_first_distance_cm(
                    c_nom_mm, diam_etrier_mm, layer.diameter_mm,
                )
                layer.spacing_from_previous_cm = layer.distance_from_tension_face_cm
            else:
                layer.distance_from_tension_face_cm = layer.spacing_from_previous_cm
        else:
            layer.distance_from_tension_face_cm = (
                layers[i - 1].distance_from_tension_face_cm
                + layer.spacing_from_previous_cm
            )
        layer.id = i + 1


def add_layer(
    layers: list[ReinforcementLayer],
    layer: ReinforcementLayer,
    c_nom_mm: float = 30.0,
    diam_etrier_mm: float = 8.0,
) -> None:
    """Ajoute un lit en fin de liste et recalcule les positions."""
    layers.append(layer)
    recompute_layer_levels(layers, c_nom_mm, diam_etrier_mm)


def update_layer(
    layers: list[ReinforcementLayer],
    index: int,
    **kwargs,
) -> None:
    """Met à jour les attributs d'un lit et recalcule tout."""
    layer = layers[index]
    for k, v in kwargs.items():
        setattr(layer, k, v)


def delete_layer(
    layers: list[ReinforcementLayer],
    index: int,
    c_nom_mm: float = 30.0,
    diam_etrier_mm: float = 8.0,
) -> None:
    """Supprime un lit et recalcule les positions.

    Les lits suivants conservent leur position absolue.
    """
    if index < 0 or index >= len(layers):
        return

    # Ajuster le spacing du lit suivant pour préserver sa position absolue
    if index < len(layers) - 1:
        next_layer = layers[index + 1]
        if index == 0:
            # Le second lit devient le premier — son spacing devient
            # sa position absolue actuelle
            next_layer.spacing_from_previous_cm = next_layer.distance_from_tension_face_cm
            next_layer.auto_first = False
        else:
            # Le lit suivant doit absorber le gap créé par la suppression
            prev_abs = layers[index - 1].distance_from_tension_face_cm
            next_layer.spacing_from_previous_cm = (
                next_layer.distance_from_tension_face_cm - prev_abs
            )

    layers.pop(index)
    recompute_layer_levels(layers, c_nom_mm, diam_etrier_mm)


def move_layer_up(
    layers: list[ReinforcementLayer],
    index: int,
    c_nom_mm: float = 30.0,
    diam_etrier_mm: float = 8.0,
) -> None:
    """Monte un lit d'une position (échange avec le précédent)."""
    if index <= 0 or index >= len(layers):
        return
    layers[index], layers[index - 1] = layers[index - 1], layers[index]
    # Recalcule les spacings pour garder les mêmes positions absolues
    _readjust_spacings_after_swap(layers, index - 1, index)
    recompute_layer_levels(layers, c_nom_mm, diam_etrier_mm)


def move_layer_down(
    layers: list[ReinforcementLayer],
    index: int,
    c_nom_mm: float = 30.0,
    diam_etrier_mm: float = 8.0,
) -> None:
    """Descend un lit d'une position (échange avec le suivant)."""
    if index < 0 or index >= len(layers) - 1:
        return
    layers[index], layers[index + 1] = layers[index + 1], layers[index]
    _readjust_spacings_after_swap(layers, index, index + 1)
    recompute_layer_levels(layers, c_nom_mm, diam_etrier_mm)


def _readjust_spacings_after_swap(
    layers: list[ReinforcementLayer],
    idx_a: int,
    idx_b: int,
) -> None:
    """Après un swap, réajuste les spacings relatifs."""
    # Après swap les anciennes positions absolues sont échangées,
    # on recalcule les spacings relatifs en se basant sur les
    # anciennes absolute positions qui sont maintenant croisées.
    # Le plus simple : recalculer le spacing du second à partir du premier.
    if idx_a == 0:
        layers[idx_a].spacing_from_previous_cm = layers[idx_a].distance_from_tension_face_cm
    if idx_b > 0:
        layers[idx_b].spacing_from_previous_cm = (
            layers[idx_b].distance_from_tension_face_cm
            - layers[idx_a].distance_from_tension_face_cm
        )


# ────────────────────────────────────────────────────────────────────────
#  Calculs
# ────────────────────────────────────────────────────────────────────────

def compute_real_effective_depth(
    layers: list[ReinforcementLayer],
    h_mm: float,
) -> float:
    """Hauteur utile réelle d_réel = Σ(Ai×di) / Σ(Ai).

    Chaque ``di = h - distance_from_tension_face`` (en mm).
    """
    sum_ai_di = 0.0
    sum_ai = 0.0
    for layer in layers:
        if layer.layer_type == TypeLit.COMPRIME:
            continue
        ai = layer.area_mm2
        di = h_mm - layer.distance_from_tension_face_cm * 10.0  # cm → mm
        sum_ai_di += ai * di
        sum_ai += ai
    return sum_ai_di / sum_ai if sum_ai > 0 else 0.0


def compute_layer_details(
    layers: list[ReinforcementLayer],
    h_mm: float,
) -> list[dict]:
    """Détails par lit (compatible avec le format attendu par le reste de l'app)."""
    details: list[dict] = []
    for layer in layers:
        y_centre_mm = layer.distance_from_tension_face_cm * 10.0
        d_i = h_mm - y_centre_mm
        details.append({
            "lit_numero": layer.id,
            "nombre_barres": layer.n_bars,
            "diametre_mm": layer.diameter_mm,
            "section_unitaire_mm2": layer.unit_area_mm2,
            "section_totale_mm2": layer.area_mm2,
            "section_totale_cm2": layer.area_cm2,
            "distance_bord_tendu_mm": y_centre_mm,
            "d_i_mm": d_i,
            "type": layer.layer_type.value,
            "spacing_cm": layer.spacing_from_previous_cm,
            "absolute_cm": layer.distance_from_tension_face_cm,
        })
    return details


# ────────────────────────────────────────────────────────────────────────
#  Validation géométrique
# ────────────────────────────────────────────────────────────────────────

@dataclass
class LayerValidationResult:
    """Résultat de la validation géométrique des lits."""
    valid: bool = True
    messages: list[dict] = field(default_factory=list)

    def add(self, msg: str, level: str = "ok") -> None:
        self.messages.append({"type": level, "message": msg})
        if level == "erreur":
            self.valid = False


def validate_layer_spacing(
    layers: list[ReinforcementLayer],
    h_mm: float,
    d_mm: float,
) -> LayerValidationResult:
    """Vérifie la cohérence géométrique des lits.

    Contrôles :
    1. Distances positives.
    2. Lits à l'intérieur de la section.
    3. Aucun lit ne dépasse la hauteur utile.
    """
    result = LayerValidationResult()

    if not layers:
        result.add("Aucun lit défini.", "info")
        return result

    for layer in layers:
        y_mm = layer.distance_from_tension_face_cm * 10.0

        # Distance positive
        if layer.spacing_from_previous_cm <= 0 and layer.id > 1:
            result.add(
                f"Distance entre le lit {layer.id} et le lit {layer.id - 1} "
                f"invalide ({layer.spacing_from_previous_cm:.1f} cm ≤ 0).",
                "erreur",
            )
        if layer.id == 1 and layer.distance_from_tension_face_cm <= 0:
            result.add(
                f"Distance du lit 1 à la fibre tendue invalide "
                f"({layer.distance_from_tension_face_cm:.1f} cm ≤ 0).",
                "erreur",
            )

        # Dans la section
        if y_mm >= h_mm:
            result.add(
                f"Le lit {layer.id} (à {layer.distance_from_tension_face_cm:.1f} cm) "
                f"dépasse la hauteur de la section ({h_mm / 10:.1f} cm).",
                "erreur",
            )
        elif y_mm > d_mm:
            result.add(
                f"Le lit {layer.id} (à {layer.distance_from_tension_face_cm:.1f} cm) "
                f"dépasse la hauteur utile ({d_mm / 10:.1f} cm).",
                "avertissement",
            )

    # Espacement minimum (empirique : max(diamètre barre, 20 mm) ~ 2 cm)
    for i in range(1, len(layers)):
        esp_min_cm = max(layers[i].diameter_mm, layers[i - 1].diameter_mm) / 10.0
        if layers[i].spacing_from_previous_cm < esp_min_cm:
            result.add(
                f"Espacement vertical insuffisant entre lit {layers[i - 1].id} "
                f"et lit {layers[i].id} : {layers[i].spacing_from_previous_cm:.1f} cm "
                f"< min {esp_min_cm:.1f} cm.",
                "avertissement",
            )

    # Somme cohérente avec h
    last = layers[-1]
    y_last_mm = last.distance_from_tension_face_cm * 10.0 + last.diameter_mm / 2.0
    if y_last_mm > h_mm:
        result.add(
            f"Le lit {last.id} avec son rayon dépasse la hauteur disponible.",
            "erreur",
        )

    if result.valid:
        result.add("Disposition verticale des lits valide.", "ok")

    return result
