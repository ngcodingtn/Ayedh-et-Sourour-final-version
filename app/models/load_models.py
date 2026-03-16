"""Modèles de données pour les sollicitations."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DonneesSollicitations:
    """Moments de calcul (stockés en N·mm en interne)."""
    M_Ed: float = 0.0    # moment ultime (N·mm)
    M_ser: float = 0.0   # moment de service (N·mm)
    moment_positif: bool = True

    def valider(self) -> list[str]:
        erreurs: list[str] = []
        if self.M_Ed < 0:
            erreurs.append("Le moment ultime MEd ne peut pas être négatif (utiliser le signe du moment).")
        if self.M_ser < 0:
            erreurs.append("Le moment de service Mser ne peut pas être négatif.")
        return erreurs

    def to_dict(self) -> dict:
        return {
            "M_Ed": self.M_Ed,
            "M_ser": self.M_ser,
            "moment_positif": self.moment_positif,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DonneesSollicitations":
        return cls(**data)
