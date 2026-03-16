"""Modèles de données pour les sections de béton."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TypeSection(Enum):
    RECTANGULAIRE = "Rectangulaire"
    T = "T"
    AUTO = "Auto"


@dataclass
class DonneesGeometrie:
    """Données géométriques de la section (toutes en mm)."""
    type_section: TypeSection = TypeSection.RECTANGULAIRE
    b_eff: float = 0.0       # largeur efficace de la table (mm)
    b_w: float = 0.0         # largeur de l'âme (mm)
    h_f: float = 0.0         # hauteur de la table (mm)
    h: float = 0.0           # hauteur totale (mm)
    d: float = 0.0           # hauteur utile (mm)
    d_prime: float = 0.0     # distance aciers comprimés au bord (mm)
    c_nom: float = 30.0      # enrobage nominal (mm)
    diam_etrier: float = 8.0 # diamètre de l'étrier (mm)
    espacement_vertical: float = 25.0   # espacement vertical entre lits (mm)
    espacement_horizontal: float = 25.0 # espacement horizontal libre (mm)
    d_g: float = 20.0        # grosseur max granulat (mm)
    nb_max_lits: int = 4     # nombre maximal de lits autorisés
    longueur_extrusion: float = 1000.0  # pour la vue 3D (mm)
    d_auto: bool = True       # calculer d = 0.9 * h si non fourni

    def calculer_d_auto(self) -> float:
        """Retourne d calculé automatiquement si non fourni."""
        if self.d <= 0 and self.d_auto and self.h > 0:
            return 0.9 * self.h
        return self.d

    def hauteur_utile_effective(self) -> float:
        """Retourne la hauteur utile effective."""
        d_val = self.d if self.d > 0 else self.calculer_d_auto()
        return d_val

    def largeur_calcul(self, moment_positif: bool = True) -> float:
        """Retourne la largeur de calcul selon le type de section et le signe du moment."""
        if self.type_section == TypeSection.RECTANGULAIRE:
            return self.b_w
        elif self.type_section == TypeSection.T:
            if moment_positif:
                return self.b_eff
            else:
                return self.b_w
        else:  # AUTO
            if moment_positif and self.b_eff > 0 and self.h_f > 0:
                return self.b_eff
            return self.b_w

    def valider(self) -> list[str]:
        """Valide la cohérence géométrique. Retourne une liste d'erreurs."""
        erreurs: list[str] = []
        if self.h <= 0:
            erreurs.append("La hauteur h doit être strictement positive.")
        if self.b_w <= 0:
            erreurs.append("La largeur bw doit être strictement positive.")
        d_eff = self.hauteur_utile_effective()
        if d_eff <= 0:
            erreurs.append("La hauteur utile d doit être strictement positive.")
        if d_eff >= self.h:
            erreurs.append("La hauteur utile d doit être inférieure à h.")
        if self.type_section in (TypeSection.T, TypeSection.AUTO):
            if self.b_eff > 0 and self.b_eff < self.b_w:
                erreurs.append("La largeur efficace beff doit être ≥ bw.")
            if self.h_f > 0 and self.h_f >= self.h:
                erreurs.append("La hauteur de table hf doit être < h.")
        if self.c_nom < 0:
            erreurs.append("L'enrobage cnom ne peut pas être négatif.")
        return erreurs

    def to_dict(self) -> dict:
        return {
            "type_section": self.type_section.value,
            "b_eff": self.b_eff,
            "b_w": self.b_w,
            "h_f": self.h_f,
            "h": self.h,
            "d": self.d,
            "d_prime": self.d_prime,
            "c_nom": self.c_nom,
            "diam_etrier": self.diam_etrier,
            "espacement_vertical": self.espacement_vertical,
            "espacement_horizontal": self.espacement_horizontal,
            "d_g": self.d_g,
            "nb_max_lits": self.nb_max_lits,
            "longueur_extrusion": self.longueur_extrusion,
            "d_auto": self.d_auto,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DonneesGeometrie":
        data = dict(data)
        data["type_section"] = TypeSection(data.get("type_section", "Rectangulaire"))
        return cls(**data)
