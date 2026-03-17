"""Flexion simple – Section rectangulaire."""
from __future__ import annotations

import math

from app.models.section_models import DonneesGeometrie
from app.models.material_models import DonneesBeton, DonneesAcier
from app.models.result_models import ResultatFlexionELU
from app.core.flexion_common import (
    calculer_mu_cu, calculer_alpha_u, calculer_Zc,
    calculer_As_requise, calculer_As_min, calculer_As_max,
)
from app.core.stress_strain import (
    determiner_pivot, calculer_mu_ulim,
)
from app.core.steel import calculer_sigma_s_compression
from app.constants import EPSILON_CU3


def calcul_flexion_rectangulaire(
    M_Ed: float,
    b: float,
    d: float,
    d_prime: float,
    h: float,
    beton: DonneesBeton,
    acier: DonneesAcier,
) -> ResultatFlexionELU:
    """Calcul complet en flexion simple pour une section rectangulaire.

    Toutes les unités en mm et N·mm.

    Args:
        M_Ed: moment ultime de calcul (N·mm).
        b: largeur de la section (mm).
        d: hauteur utile (mm).
        d_prime: distance aciers comprimés au bord comprimé (mm).
        h: hauteur totale (mm).
        beton: données béton.
        acier: données acier.

    Returns:
        ResultatFlexionELU.
    """
    res = ResultatFlexionELU()
    res.type_section_retenu = "Rectangulaire"
    res.b_calcul = b
    res.d_calcul = d

    # Paramètres matériaux
    fcu = beton.fcu
    fcd = beton.fcd
    lam = beton.lambda_coeff
    res.fcd = fcd
    res.fcu = fcu

    # Moment réduit
    mu_cu = calculer_mu_cu(M_Ed, b, d, fcu)
    res.mu_cu = mu_cu

    # Moment réduit limite
    mu_ulim = calculer_mu_ulim(acier, beton)
    res.mu_ulim = mu_ulim

    # Vérification moment réduit
    if mu_cu > 0.5:
        res.erreurs.append(
            f"Moment réduit μcu = {mu_cu:.4f} > 0.50. "
            "La section est insuffisante. Augmentez les dimensions."
        )
        res.calcul_valide = False
        return res

    if mu_cu <= mu_ulim:
        # ── Calcul sans aciers comprimés ──
        res.necessite_aciers_comprimes = False

        # Position axe neutre
        alpha_u = calculer_alpha_u(mu_cu, lam)
        res.alpha_u = alpha_u
        res.x_u = alpha_u * d

        # Bras de levier
        Zc = calculer_Zc(d, alpha_u, lam)
        res.Zc = Zc

        # Pivot et contrainte acier
        pivot = determiner_pivot(mu_cu, acier, beton)
        res.pivot = pivot

        # Section d'acier requise
        As_req = calculer_As_requise(M_Ed, Zc, pivot.sigma_s1)
        res.As_requise = As_req

        # Section minimale
        As_min = calculer_As_min(beton, acier, b, d)
        res.As_min = As_min

        if As_req < As_min:
            res.As_requise = As_min
            res.avertissements.append(
                f"As calculée ({As_req/100:.2f} cm²) < As,min ({As_min/100:.2f} cm²). "
                "La section minimale est retenue."
            )

        res.commentaire_section = (
            f"Section rectangulaire b×d = {b:.0f}×{d:.0f} mm. "
            f"μcu = {mu_cu:.4f} ≤ μulim = {mu_ulim:.4f}. "
            f"Pas d'aciers comprimés nécessaires."
        )
        res.calcul_valide = True

    else:
        # ── Calcul avec aciers comprimés ──
        res.necessite_aciers_comprimes = True

        # Moment repris par la section simple à la limite
        Mlu = mu_ulim * b * d ** 2 * fcu
        res.Mlu = Mlu

        # Alpha_u à la limite
        alpha_u_lim = calculer_alpha_u(mu_ulim, lam)
        res.alpha_u = alpha_u_lim
        res.x_u = alpha_u_lim * d

        # Bras de levier à la limite
        Zc = calculer_Zc(d, alpha_u_lim, lam)
        res.Zc = Zc

        # Pivot à la limite
        pivot = determiner_pivot(mu_ulim, acier, beton)
        res.pivot = pivot

        # Contrainte acier comprimé
        x_u = alpha_u_lim * d
        if x_u > 0:
            eps_s_prime = EPSILON_CU3 * (x_u - d_prime) / x_u
        else:
            eps_s_prime = 0.0
        sigma_s2 = calculer_sigma_s_compression(eps_s_prime, acier)

        # Moment excédentaire
        delta_M = M_Ed - Mlu

        # Section acier comprimé
        if sigma_s2 > 0 and (d - d_prime) > 0:
            As2 = delta_M / (sigma_s2 * (d - d_prime))
        else:
            As2 = 0.0
        res.As_comp_requise = As2

        # Section acier tendu totale
        As1 = Mlu / (Zc * pivot.sigma_s1) + As2 * sigma_s2 / pivot.sigma_s1
        res.As_requise = As1
        res.As_tendue_totale = As1

        # Section minimale
        As_min = calculer_As_min(beton, acier, b, d)
        res.As_min = As_min

        res.commentaire_compression = (
            f"μcu = {mu_cu:.4f} > μulim = {mu_ulim:.4f}. "
            f"Des aciers comprimés sont nécessaires.\n"
            f"Mlu = {Mlu/1e6:.2f} kN·m, ΔM = {delta_M/1e6:.2f} kN·m.\n"
            f"σ's = {sigma_s2:.1f} MPa.\n"
            f"A's requise = {As2/100:.2f} cm², As totale = {As1/100:.2f} cm²."
        )
        res.commentaire_section = (
            f"Section rectangulaire b×d = {b:.0f}×{d:.0f} mm. "
            f"Aciers comprimés requis (μcu > μulim)."
        )
        res.calcul_valide = True

    return res
