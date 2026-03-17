"""Flexion simple – Section en T."""
from __future__ import annotations

import math

from app.models.section_models import DonneesGeometrie
from app.models.material_models import DonneesBeton, DonneesAcier
from app.models.result_models import ResultatFlexionELU
from app.core.flexion_common import (
    calculer_mu_cu, calculer_alpha_u, calculer_Zc,
    calculer_As_requise, calculer_As_min,
)
from app.core.flexion_rectangular import calcul_flexion_rectangulaire
from app.core.stress_strain import determiner_pivot, calculer_mu_ulim
from app.core.section_decision import (
    decide_section_type, DecisionSection, SectionDecisionResult,
)


def calcul_flexion_T(
    MEd_max: float,
    b_eff: float,
    b_w: float,
    h_f: float,
    h: float,
    d: float,
    d_prime: float,
    beton: DonneesBeton,
    acier: DonneesAcier,
    moment_positif: bool = True,
) -> ResultatFlexionELU:
    """Calcul en flexion simple pour une section en T.

    Toutes les unités en mm et N·mm.

    La fonction utilise la décision automatique :
      - moment négatif → rectangulaire bw
      - MEd_max ≤ MTu → rectangulaire équivalente beff
      - MEd_max > MTu → vraie section en T (décomposition)
    """
    fcu = beton.fcu

    # ── Décision du type de section ──
    decision = decide_section_type(
        MEd_max=MEd_max,
        b_eff=b_eff, b_w=b_w, h_f=h_f, h=h, d=d,
        fcu=fcu,
        moment_positif=moment_positif,
    )

    # ── CAS A : moment négatif → rectangulaire bw ──
    if decision.decision == DecisionSection.RECTANGULAIRE_BW_NEGATIF:
        res = calcul_flexion_rectangulaire(MEd_max, b_w, d, d_prime, h, beton, acier)
        res.type_section_retenu = "T (moment négatif → rectangulaire bw)"
        res.decision = decision
        res.commentaire_section = decision.explanation
        return res

    # ── CAS B : MEd_max ≤ MTu → rectangulaire équivalente beff ──
    if decision.decision == DecisionSection.RECTANGULAIRE_EQUIVALENTE_BEFF:
        res = calcul_flexion_rectangulaire(MEd_max, b_eff, d, d_prime, h, beton, acier)
        res.type_section_retenu = "T (axe neutre dans la table → rectangulaire beff)"
        res.MTu = decision.MTu
        res.decision = decision

        # EC2 §9.2.1.1(3) : pour une section en T, bt = bw
        As_min_bw = calculer_As_min(beton, acier, b_w, d)
        As_calc = calculer_As_requise(MEd_max, res.Zc, res.pivot.sigma_s1)
        res.As_min = As_min_bw
        res.As_requise = max(As_calc, As_min_bw)

        res.commentaire_section = decision.explanation
        return res

    # ── CAS C : MEd_max > MTu → vraie section en T (décomposition) ──
    lam = beton.lambda_coeff
    res = ResultatFlexionELU()
    res.type_section_retenu = "T (axe neutre dans l'âme → décomposition)"
    res.MTu = decision.MTu
    res.decision = decision
    res.fcd = beton.fcd
    res.fcu = fcu
    res.b_calcul = b_w
    res.d_calcul = d

    # Contribution de la table (débords)
    MEd2 = (b_eff - b_w) * h_f * fcu * (d - h_f / 2.0)
    z2 = d - h_f / 2.0
    res.MEd2 = MEd2

    # Contribution de l'âme
    MEd1 = MEd_max - MEd2
    res.MEd1 = MEd1

    # Moment réduit sur l'âme
    mu_cu = calculer_mu_cu(MEd1, b_w, d, fcu)
    res.mu_cu = mu_cu

    mu_ulim = calculer_mu_ulim(acier, beton)
    res.mu_ulim = mu_ulim

    if mu_cu > mu_ulim:
        res.necessite_aciers_comprimes = True
        res.avertissements.append(
            "La contribution de l'âme nécessite des aciers comprimés. "
            "Envisagez d'augmenter les dimensions de la section."
        )
        alpha_u_lim = calculer_alpha_u(mu_ulim, lam)
        Zc = calculer_Zc(d, alpha_u_lim, lam)
        pivot = determiner_pivot(mu_ulim, acier, beton)

        Mlu = mu_ulim * b_w * d ** 2 * fcu
        res.Mlu = Mlu

        As1_ame = Mlu / (Zc * pivot.sigma_s1)
        res.alpha_u = alpha_u_lim
        res.x_u = alpha_u_lim * d
        res.Zc = Zc
        res.pivot = pivot
    else:
        alpha_u = calculer_alpha_u(mu_cu, lam)
        Zc = calculer_Zc(d, alpha_u, lam)
        pivot = determiner_pivot(mu_cu, acier, beton)

        res.alpha_u = alpha_u
        res.x_u = alpha_u * d
        res.Zc = Zc
        res.pivot = pivot

        As1_ame = calculer_As_requise(MEd1, Zc, pivot.sigma_s1)

    # Acier pour la table
    As2_table = MEd2 / (z2 * pivot.sigma_s1) if (z2 > 0 and pivot.sigma_s1 > 0) else 0.0

    res.As1 = As1_ame
    res.As2 = As2_table
    res.As_requise = As1_ame + As2_table

    # Section minimale
    As_min = calculer_As_min(beton, acier, b_w, d)
    res.As_min = As_min

    if res.As_requise < As_min:
        res.As_requise = As_min
        res.avertissements.append(
            f"As calculée < As,min ({As_min/100:.2f} cm²). Section minimale retenue."
        )

    res.commentaire_section = (
        f"{decision.explanation}\n"
        f"Contribution table : MEd2 = {MEd2/1e6:.2f} kN·m → As2 = {As2_table/100:.2f} cm²\n"
        f"Contribution âme  : MEd1 = {MEd1/1e6:.2f} kN·m → As1 = {As1_ame/100:.2f} cm²\n"
        f"As totale requise = {res.As_requise/100:.2f} cm²"
    )
    res.calcul_valide = True

    return res
