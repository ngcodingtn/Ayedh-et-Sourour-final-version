"""Modèles de données pour les sollicitations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


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


@dataclass
class ChargeConcentree:
    """Charge concentrée ponctuelle."""
    position_mm: float = 0.0   # position sur la poutre (mm)
    G_N: float = 0.0           # charge permanente (N)
    Q_N: float = 0.0           # charge d'exploitation (N)
    label: str = ""

    def to_dict(self) -> dict:
        return {"position_mm": self.position_mm, "G_N": self.G_N,
                "Q_N": self.Q_N, "label": self.label}

    @classmethod
    def from_dict(cls, data: dict) -> "ChargeConcentree":
        return cls(**data)


@dataclass
class DonneesPoutre:
    """Données de la poutre pour le calcul de sollicitations."""
    # Type de poutre
    type_poutre: str = "simple"  # "simple", "console_gauche", "console_droite", "deux_consoles"

    # Géométrie
    longueur_totale_mm: float = 5000.0  # longueur totale (mm)
    position_appui_A_mm: float = 0.0    # position appui gauche (mm)
    position_appui_B_mm: float = 5000.0  # position appui droit (mm)

    # Charges uniformément réparties
    g_N_mm: float = 0.0   # charge permanente (N/mm)
    q_N_mm: float = 0.0   # charge d'exploitation (N/mm)

    # Charges concentrées
    charges_concentrees: list[ChargeConcentree] = field(default_factory=list)

    # Coefficients psi
    psi_1: float = 0.5    # coefficient fréquent
    psi_2: float = 0.3    # coefficient quasi-permanent

    def portee(self) -> float:
        """Portée entre appuis (mm)."""
        return abs(self.position_appui_B_mm - self.position_appui_A_mm)

    def console_gauche(self) -> float:
        """Longueur console gauche (mm)."""
        return max(self.position_appui_A_mm, 0.0)

    def console_droite(self) -> float:
        """Longueur console droite (mm)."""
        return max(self.longueur_totale_mm - self.position_appui_B_mm, 0.0)

    def valider(self) -> list[str]:
        erreurs: list[str] = []
        if self.longueur_totale_mm <= 0:
            erreurs.append("La longueur totale doit être positive.")
        if self.position_appui_A_mm < 0:
            erreurs.append("La position de l'appui A ne peut pas être négative.")
        if self.position_appui_B_mm <= self.position_appui_A_mm:
            erreurs.append("L'appui B doit être après l'appui A.")
        if self.position_appui_B_mm > self.longueur_totale_mm:
            erreurs.append("L'appui B doit être ≤ longueur totale.")
        for i, cc in enumerate(self.charges_concentrees):
            if cc.position_mm < 0 or cc.position_mm > self.longueur_totale_mm:
                erreurs.append(f"Charge concentrée {i+1} : position hors de la poutre.")
        return erreurs

    def to_dict(self) -> dict:
        return {
            "type_poutre": self.type_poutre,
            "longueur_totale_mm": self.longueur_totale_mm,
            "position_appui_A_mm": self.position_appui_A_mm,
            "position_appui_B_mm": self.position_appui_B_mm,
            "g_N_mm": self.g_N_mm,
            "q_N_mm": self.q_N_mm,
            "charges_concentrees": [c.to_dict() for c in self.charges_concentrees],
            "psi_1": self.psi_1,
            "psi_2": self.psi_2,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DonneesPoutre":
        d = dict(data)
        ccs = d.pop("charges_concentrees", [])
        obj = cls(**d)
        obj.charges_concentrees = [ChargeConcentree.from_dict(c) for c in ccs]
        return obj
