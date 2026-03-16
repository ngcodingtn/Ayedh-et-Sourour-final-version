"""Modèles de données pour le ferraillage."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import math


@dataclass
class LitArmature:
    """Un lit d'armatures avec position verticale explicite."""
    numero: int = 1
    nombre_barres: int = 0
    diametre_mm: float = 0.0
    est_comprime: bool = False
    type_lit: str = "tendu"          # tendu / comprimé / montage
    espacement_precedent_cm: float = 5.0   # distance relative au lit précédent (cm)
    distance_fibre_tendue_cm: float = 0.0  # position absolue (cm) — recalculée
    auto_first: bool = False               # calcul auto pour le 1er lit
    label: str = ""

    @property
    def section_unitaire_mm2(self) -> float:
        return math.pi * self.diametre_mm ** 2 / 4.0

    @property
    def section_totale_mm2(self) -> float:
        return self.nombre_barres * self.section_unitaire_mm2

    @property
    def section_unitaire_cm2(self) -> float:
        return self.section_unitaire_mm2 / 100.0

    @property
    def section_totale_cm2(self) -> float:
        return self.section_totale_mm2 / 100.0

    def to_dict(self) -> dict:
        return {
            "numero": self.numero,
            "nombre_barres": self.nombre_barres,
            "diametre_mm": self.diametre_mm,
            "est_comprime": self.est_comprime,
            "type_lit": self.type_lit,
            "espacement_precedent_cm": self.espacement_precedent_cm,
            "distance_fibre_tendue_cm": self.distance_fibre_tendue_cm,
            "auto_first": self.auto_first,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LitArmature":
        known = {
            "numero", "nombre_barres", "diametre_mm", "est_comprime",
            "type_lit", "espacement_precedent_cm", "distance_fibre_tendue_cm",
            "auto_first", "label",
        }
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


@dataclass
class DonneesFerraillage:
    """Ferraillage proposé par l'utilisateur."""
    lits_tendus: list[LitArmature] = field(default_factory=list)
    lits_comprimes: list[LitArmature] = field(default_factory=list)

    @property
    def As_reelle_mm2(self) -> float:
        return sum(lit.section_totale_mm2 for lit in self.lits_tendus)

    @property
    def As_reelle_cm2(self) -> float:
        return self.As_reelle_mm2 / 100.0

    @property
    def As_prime_mm2(self) -> float:
        return sum(lit.section_totale_mm2 for lit in self.lits_comprimes)

    def to_dict(self) -> dict:
        return {
            "lits_tendus": [lit.to_dict() for lit in self.lits_tendus],
            "lits_comprimes": [lit.to_dict() for lit in self.lits_comprimes],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DonneesFerraillage":
        return cls(
            lits_tendus=[LitArmature.from_dict(d) for d in data.get("lits_tendus", [])],
            lits_comprimes=[LitArmature.from_dict(d) for d in data.get("lits_comprimes", [])],
        )


@dataclass
class DonneesEnvironnement:
    """Paramètres ELS / fissuration."""
    classe_exposition: str = "XC1"
    maitrise_fissuration: bool = True
    wmax_impose: Optional[float] = None
    calcul_direct_fissuration: bool = False

    def wmax_recommande(self) -> Optional[float]:
        from app.constants import WMAX_PAR_CLASSE
        return WMAX_PAR_CLASSE.get(self.classe_exposition)

    def to_dict(self) -> dict:
        return {
            "classe_exposition": self.classe_exposition,
            "maitrise_fissuration": self.maitrise_fissuration,
            "wmax_impose": self.wmax_impose,
            "calcul_direct_fissuration": self.calcul_direct_fissuration,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DonneesEnvironnement":
        return cls(**data)
