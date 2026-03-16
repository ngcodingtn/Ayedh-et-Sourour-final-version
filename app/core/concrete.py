"""Calculs relatifs au béton – Eurocode 2."""
from __future__ import annotations

from app.models.material_models import DonneesBeton


def calculer_fcd(beton: DonneesBeton) -> float:
    """Résistance de calcul fcd = alpha_cc * fck / gamma_c (MPa)."""
    return beton.fcd


def calculer_fcu(beton: DonneesBeton) -> float:
    """Contrainte du bloc rectangulaire fcu = eta * fcd (MPa)."""
    return beton.fcu


def calculer_fctm(beton: DonneesBeton) -> float:
    """Résistance moyenne en traction (MPa)."""
    return beton.fctm


def calculer_Ecm(beton: DonneesBeton) -> float:
    """Module d'élasticité sécant (MPa)."""
    return beton.Ecm


def parametres_diagramme(fck: float) -> dict:
    """Retourne eta et lambda selon fck (EC2 §3.1.7)."""
    if fck <= 50:
        return {"eta": 1.0, "lambda": 0.8}
    else:
        eta = 1.0 - (fck - 50) / 200
        lam = 0.8 - (fck - 50) / 400
        return {"eta": eta, "lambda": lam}
