"""Calculs communs pour la flexion simple."""
from __future__ import annotations

import math

from app.models.material_models import DonneesBeton, DonneesAcier
from app.constants import EPSILON_CU3


def calculer_As_min(
    beton: DonneesBeton,
    acier: DonneesAcier,
    b: float,
    d: float,
) -> float:
    """Section minimale d'armatures tendues (mm²) – EC2 §9.2.1.1.

    As,min = max(0.26 * fctm/fyk * b * d,  0.0013 * b * d)
    """
    fctm = beton.fctm
    fyk = acier.fyk
    val1 = 0.26 * fctm / fyk * b * d
    val2 = 0.0013 * b * d
    return max(val1, val2)


def calculer_As_max(b: float, h: float) -> float:
    """Section maximale d'armatures (mm²) – EC2 §9.2.1.1.

    As,max = 0.04 * Ac
    """
    return 0.04 * b * h


def calculer_mu_cu(M_Ed: float, b: float, d: float, fcu: float) -> float:
    """Moment réduit mu_cu = MEd / (b * d² * fcu)."""
    if b <= 0 or d <= 0 or fcu <= 0:
        return 0.0
    return M_Ed / (b * d ** 2 * fcu)


def calculer_alpha_u(mu_cu: float, lambda_coeff: float) -> float:
    """Position relative de l'axe neutre.

    alpha_u = (1/lambda) * (1 - sqrt(1 - 2 * mu_cu))
    """
    disc = 1 - 2 * mu_cu
    if disc < 0:
        return float('nan')
    return (1 / lambda_coeff) * (1 - math.sqrt(disc))


def calculer_Zc(d: float, alpha_u: float, lambda_coeff: float) -> float:
    """Bras de levier du couple interne (mm).

    Zc = d * (1 - lambda * alpha_u / 2)
    """
    return d * (1 - lambda_coeff * alpha_u / 2)


def calculer_As_requise(M_Ed: float, Zc: float, sigma_s1: float) -> float:
    """Section d'acier requise (mm²).

    As = MEd / (Zc * sigma_s1)
    """
    if Zc <= 0 or sigma_s1 <= 0:
        return 0.0
    return M_Ed / (Zc * sigma_s1)
