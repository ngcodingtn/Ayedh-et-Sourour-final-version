"""Modèles de données pour les matériaux."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.constants import (
    ALPHA_CC_DEFAULT, GAMMA_C_DEFAULT, GAMMA_S_DEFAULT,
    ETA_DEFAULT, LAMBDA_DEFAULT, ES_DEFAULT,
    FCK_DEFAULT, FYK_DEFAULT,
    EPSILON_UK, K_DUCT, EPSILON_UD_FACTOR,
)


class ClasseDuctilite(Enum):
    A = "A"
    B = "B"
    C = "C"


class DiagrammeAcier(Enum):
    PALIER_HORIZONTAL = "Palier horizontal"
    PALIER_INCLINE = "Palier incliné"


@dataclass
class DonneesBeton:
    """Propriétés du béton."""
    fck: float = FCK_DEFAULT          # MPa
    alpha_cc: float = ALPHA_CC_DEFAULT
    gamma_c: float = GAMMA_C_DEFAULT
    eta: float = ETA_DEFAULT
    lambda_coeff: float = LAMBDA_DEFAULT

    @property
    def fcd(self) -> float:
        """Résistance de calcul en compression."""
        return self.alpha_cc * self.fck / self.gamma_c

    @property
    def fcu(self) -> float:
        """Contrainte du bloc rectangulaire simplifié."""
        return self.eta * self.fcd

    @property
    def fctm(self) -> float:
        """Résistance moyenne en traction (EC2 tableau 3.1)."""
        if self.fck <= 50:
            return 0.30 * self.fck ** (2.0 / 3.0)
        return 2.12 * (1 + self.fck / 10) ** 0.1  # simplifié

    @property
    def Ecm(self) -> float:
        """Module d'élasticité sécant (MPa)."""
        return 22_000 * (self.fck / 10 + 8) ** 0.3  # EC2 approx (fcm = fck+8)

    def to_dict(self) -> dict:
        return {
            "fck": self.fck,
            "alpha_cc": self.alpha_cc,
            "gamma_c": self.gamma_c,
            "eta": self.eta,
            "lambda_coeff": self.lambda_coeff,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DonneesBeton":
        return cls(**data)


@dataclass
class DonneesAcier:
    """Propriétés de l'acier."""
    fyk: float = FYK_DEFAULT       # MPa
    Es: float = ES_DEFAULT         # MPa
    gamma_s: float = GAMMA_S_DEFAULT
    classe_ductilite: ClasseDuctilite = ClasseDuctilite.B
    diagramme: DiagrammeAcier = DiagrammeAcier.PALIER_HORIZONTAL

    @property
    def fyd(self) -> float:
        """Résistance de calcul en traction."""
        return self.fyk / self.gamma_s

    @property
    def epsilon_yd(self) -> float:
        """Déformation élastique limite."""
        return self.fyd / self.Es

    @property
    def epsilon_uk(self) -> float:
        """Déformation caractéristique ultime."""
        return EPSILON_UK[self.classe_ductilite.value]

    @property
    def epsilon_ud(self) -> float:
        """Déformation de calcul ultime."""
        return EPSILON_UD_FACTOR * self.epsilon_uk

    @property
    def k(self) -> float:
        """Rapport ft/fy pour palier incliné."""
        return K_DUCT[self.classe_ductilite.value]

    def to_dict(self) -> dict:
        return {
            "fyk": self.fyk,
            "Es": self.Es,
            "gamma_s": self.gamma_s,
            "classe_ductilite": self.classe_ductilite.value,
            "diagramme": self.diagramme.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DonneesAcier":
        data = dict(data)
        data["classe_ductilite"] = ClasseDuctilite(data.get("classe_ductilite", "B"))
        data["diagramme"] = DiagrammeAcier(data.get("diagramme", "Palier horizontal"))
        return cls(**data)


@dataclass
class DonneesMateriaux:
    """Regroupe béton et acier."""
    beton: DonneesBeton = None  # type: ignore
    acier: DonneesAcier = None  # type: ignore

    def __post_init__(self):
        if self.beton is None:
            self.beton = DonneesBeton()
        if self.acier is None:
            self.acier = DonneesAcier()

    @property
    def alpha_e(self) -> float:
        """Coefficient d'équivalence acier/béton."""
        Ec_eff = self.beton.Ecm
        if Ec_eff <= 0:
            return 15.0
        return self.acier.Es / Ec_eff

    def to_dict(self) -> dict:
        return {
            "beton": self.beton.to_dict(),
            "acier": self.acier.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DonneesMateriaux":
        return cls(
            beton=DonneesBeton.from_dict(data["beton"]),
            acier=DonneesAcier.from_dict(data["acier"]),
        )
