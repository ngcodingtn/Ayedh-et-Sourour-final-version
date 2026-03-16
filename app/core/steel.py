"""Calculs relatifs à l'acier – Eurocode 2."""
from __future__ import annotations

from app.models.material_models import DonneesAcier, DiagrammeAcier
from app.constants import EPSILON_CU3


def calculer_fyd(acier: DonneesAcier) -> float:
    """Résistance de calcul fyd = fyk / gamma_s (MPa)."""
    return acier.fyd


def calculer_epsilon_yd(acier: DonneesAcier) -> float:
    """Déformation élastique limite."""
    return acier.epsilon_yd


def calculer_sigma_s(
    epsilon_s: float,
    acier: DonneesAcier,
) -> float:
    """Contrainte dans l'acier selon le diagramme choisi.

    Args:
        epsilon_s: déformation de l'acier (valeur positive en traction).
        acier: données acier.

    Returns:
        Contrainte sigma_s (MPa).
    """
    fyd = acier.fyd
    Es = acier.Es
    eps_yd = acier.epsilon_yd
    eps_ud = acier.epsilon_ud

    if acier.diagramme == DiagrammeAcier.PALIER_HORIZONTAL:
        # Palier horizontal : sigma_s = min(Es * eps_s, fyd)
        return min(Es * abs(epsilon_s), fyd)
    else:
        # Palier incliné
        eps = abs(epsilon_s)
        if eps <= eps_yd:
            return Es * eps
        elif eps <= eps_ud:
            k = acier.k
            # interpolation linéaire entre fyd et k*fyd
            sigma = fyd + (k * fyd - fyd) * (eps - eps_yd) / (eps_ud - eps_yd)
            return sigma
        else:
            return acier.k * fyd


def calculer_sigma_s_compression(
    epsilon_s_prime: float,
    acier: DonneesAcier,
) -> float:
    """Contrainte dans l'acier comprimé."""
    return min(acier.Es * abs(epsilon_s_prime), acier.fyd)
