"""Calculs de contrainte-déformation et détermination du pivot."""
from __future__ import annotations

import math

from app.models.material_models import DonneesAcier, DonneesBeton, DiagrammeAcier
from app.models.result_models import ResultatPivot
from app.constants import EPSILON_CU3


def calculer_alpha_AB(acier: DonneesAcier, lambda_coeff: float) -> float:
    """Position relative de l'axe neutre à la frontière pivot A / pivot B.

    alpha_AB = epsilon_cu3 / (epsilon_cu3 + epsilon_ud)
    """
    return EPSILON_CU3 / (EPSILON_CU3 + acier.epsilon_ud)


def calculer_mu_AB(acier: DonneesAcier, beton: DonneesBeton) -> float:
    """Moment réduit limite entre pivot A et pivot B (mu_AB)."""
    lam = beton.lambda_coeff
    alpha_AB = calculer_alpha_AB(acier, lam)
    return lam * alpha_AB * (1 - lam * alpha_AB / 2)


def calculer_mu_ulim(acier: DonneesAcier, beton: DonneesBeton) -> float:
    """Moment réduit ultime (limite sans aciers comprimés).

    Par convention, on prend mu_ulim = mu correspondant à alpha_u
    tel que epsilon_s = epsilon_yd (fin du domaine pivot B classique).
    """
    lam = beton.lambda_coeff
    alpha_lim = EPSILON_CU3 / (EPSILON_CU3 + acier.epsilon_yd)
    return lam * alpha_lim * (1 - lam * alpha_lim / 2)


def determiner_pivot(
    mu_cu: float,
    acier: DonneesAcier,
    beton: DonneesBeton,
) -> ResultatPivot:
    """Détermine le pivot et calcule epsilon_s1 et sigma_s1.

    Args:
        mu_cu: moment réduit.
        acier: données acier.
        beton: données béton.

    Returns:
        ResultatPivot avec pivot, epsilon_s1, sigma_s1, commentaire.
    """
    lam = beton.lambda_coeff
    mu_AB = calculer_mu_AB(acier, beton)

    # Calcul de alpha_u
    discriminant = 1 - 2 * mu_cu
    if discriminant < 0:
        return ResultatPivot(
            pivot="Impossible",
            epsilon_s1=0.0,
            epsilon_c=EPSILON_CU3,
            sigma_s1=0.0,
            commentaire="Le moment réduit dépasse la capacité maximale de la section.",
        )

    alpha_u = (1 / lam) * (1 - math.sqrt(discriminant))

    # Déterminer le pivot
    alpha_AB = calculer_alpha_AB(acier, lam)

    if alpha_u <= alpha_AB:
        # Pivot A : l'acier atteint epsilon_ud
        pivot = "A"
        epsilon_s1 = acier.epsilon_ud
        epsilon_c = EPSILON_CU3 * alpha_u / (1 - alpha_u) if alpha_u < 1 else EPSILON_CU3
        commentaire = (
            f"Pivot A : la déformation de l'acier atteint ε_ud = {acier.epsilon_ud*1000:.2f} ‰. "
            f"Section sous-armée – ductile."
        )
    else:
        # Pivot B : le béton atteint epsilon_cu3
        pivot = "B"
        epsilon_c = EPSILON_CU3
        if alpha_u < 1:
            epsilon_s1 = EPSILON_CU3 * (1 - alpha_u) / alpha_u
        else:
            epsilon_s1 = 0.0
        commentaire = (
            f"Pivot B : la déformation du béton atteint ε_cu3 = {EPSILON_CU3*1000:.1f} ‰. "
            f"ε_s1 = {epsilon_s1*1000:.2f} ‰."
        )

    # Calcul de sigma_s1
    from app.core.steel import calculer_sigma_s
    sigma_s1 = calculer_sigma_s(epsilon_s1, acier)

    return ResultatPivot(
        pivot=pivot,
        epsilon_s1=epsilon_s1,
        epsilon_c=epsilon_c,
        sigma_s1=sigma_s1,
        commentaire=commentaire,
    )
