"""Fissuration et contrôle simplifié – EC2 §7.3."""
from __future__ import annotations

from typing import Optional

from app.models.material_models import DonneesBeton, DonneesAcier
from app.models.result_models import ResultatFissuration
from app.constants import (
    WMAX_PAR_CLASSE, TABLEAU_DIAMETRE_MAX, TABLEAU_ESPACEMENT_MAX,
)
from app.core.flexion_common import calculer_As_min


def controle_fissuration(
    classe_exposition: str,
    As_reelle_mm2: float,
    b: float,
    d: float,
    h: float,
    M_ser: float,
    beton: DonneesBeton,
    acier: DonneesAcier,
    wmax_impose: Optional[float] = None,
    diam_max_propose: float = 16.0,
    espacement_propose: float = 150.0,
) -> ResultatFissuration:
    """Contrôle simplifié de la fissuration.

    Args:
        classe_exposition: classe d'exposition (ex: "XC1").
        As_reelle_mm2: section réelle d'acier tendu (mm²).
        b: largeur (mm).
        d: hauteur utile (mm).
        h: hauteur totale (mm).
        M_ser: moment de service (N·mm).
        beton: données béton.
        acier: données acier.
        wmax_impose: wmax imposé par l'utilisateur (mm) ou None.
        diam_max_propose: diamètre maximal des barres proposées (mm).
        espacement_propose: espacement entre barres (mm).

    Returns:
        ResultatFissuration.
    """
    res = ResultatFissuration()
    messages: list[str] = []

    # wmax recommandé
    wmax = wmax_impose if wmax_impose is not None else WMAX_PAR_CLASSE.get(classe_exposition)
    res.wmax_recommande = wmax

    if wmax is None:
        messages.append(
            f"Classe d'exposition {classe_exposition} : dispositions particulières requises. "
            "Le contrôle simplifié n'est pas applicable directement."
        )
        res.verdict = "Vérifié sous réserve"
        res.messages = messages
        return res

    # Section minimale
    As_min = calculer_As_min(beton, acier, b, d)
    res.As_min_mm2 = As_min
    res.As_reelle_mm2 = As_reelle_mm2
    res.controle_As_min = As_reelle_mm2 >= As_min

    if not res.controle_As_min:
        messages.append(
            f"As,réelle = {As_reelle_mm2/100:.2f} cm² < As,min = {As_min/100:.2f} cm² → NON VÉRIFIÉ."
        )
    else:
        messages.append(
            f"As,réelle = {As_reelle_mm2/100:.2f} cm² ≥ As,min = {As_min/100:.2f} cm² → OK."
        )

    # Estimation contrainte acier en service (simplifiée)
    if As_reelle_mm2 > 0 and d > 0:
        # Approximation z ≈ 0.9 * d
        z_approx = 0.9 * d
        sigma_s_ser = M_ser / (As_reelle_mm2 * z_approx) if M_ser > 0 else 0.0
    else:
        sigma_s_ser = 0.0
    res.sigma_s_service = sigma_s_ser

    # Estimation contrainte béton en service
    if b > 0 and d > 0 and As_reelle_mm2 > 0:
        alpha_e = acier.Es / beton.Ecm if beton.Ecm > 0 else 15.0
        rho = As_reelle_mm2 / (b * d)
        # Position axe neutre fissurée (simplifié)
        k = alpha_e * rho
        alpha_ser = -k + (k**2 + 2*k)**0.5
        z_ser = d * (1 - alpha_ser / 3)
        if z_ser > 0 and M_ser > 0:
            sigma_c_ser = M_ser / (0.5 * b * alpha_ser * d * z_ser) if alpha_ser > 0 else 0.0
        else:
            sigma_c_ser = 0.0
    else:
        sigma_c_ser = 0.0
    res.sigma_c_service = sigma_c_ser

    # Contrôle contrainte béton ≤ 0.6 * fck
    sigma_c_lim = 0.6 * beton.fck
    if sigma_c_ser > sigma_c_lim:
        messages.append(
            f"σ_c,ser = {sigma_c_ser:.1f} MPa > 0.6·fck = {sigma_c_lim:.1f} MPa → NON VÉRIFIÉ."
        )
    else:
        messages.append(
            f"σ_c,ser = {sigma_c_ser:.1f} MPa ≤ 0.6·fck = {sigma_c_lim:.1f} MPa → OK."
        )

    # Contrôle contrainte acier ≤ 0.8 * fyk
    sigma_s_lim = 0.8 * acier.fyk
    if sigma_s_ser > sigma_s_lim:
        messages.append(
            f"σ_s,ser = {sigma_s_ser:.1f} MPa > 0.8·fyk = {sigma_s_lim:.1f} MPa → NON VÉRIFIÉ."
        )
    else:
        messages.append(
            f"σ_s,ser = {sigma_s_ser:.1f} MPa ≤ 0.8·fyk = {sigma_s_lim:.1f} MPa → OK."
        )

    # Contrôle par diamètre maximal (tableau 7.2N)
    sigma_s_arrondi = _arrondir_sigma(sigma_s_ser)
    if sigma_s_arrondi in TABLEAU_DIAMETRE_MAX:
        phi_max_adm = TABLEAU_DIAMETRE_MAX[sigma_s_arrondi].get(wmax)
        res.diametre_max_admissible = phi_max_adm
        if phi_max_adm is not None:
            res.controle_diametre = diam_max_propose <= phi_max_adm
            if res.controle_diametre:
                messages.append(
                    f"Diamètre max proposé HA{diam_max_propose:.0f} ≤ "
                    f"HA{phi_max_adm:.0f} admissible → OK."
                )
            else:
                messages.append(
                    f"Diamètre max proposé HA{diam_max_propose:.0f} > "
                    f"HA{phi_max_adm:.0f} admissible → NON VÉRIFIÉ."
                )
    else:
        res.controle_diametre = True
        messages.append(
            f"σ_s,ser = {sigma_s_ser:.0f} MPa : hors tableau 7.2N. "
            "Contrôle diamètre non applicable."
        )

    # Contrôle par espacement maximal (tableau 7.3N)
    if sigma_s_arrondi in TABLEAU_ESPACEMENT_MAX:
        esp_max_adm = TABLEAU_ESPACEMENT_MAX[sigma_s_arrondi].get(wmax)
        res.espacement_max_admissible = esp_max_adm
        if esp_max_adm is not None:
            res.controle_espacement = espacement_propose <= esp_max_adm
            if res.controle_espacement:
                messages.append(
                    f"Espacement proposé {espacement_propose:.0f} mm ≤ "
                    f"{esp_max_adm:.0f} mm admissible → OK."
                )
            else:
                messages.append(
                    f"Espacement proposé {espacement_propose:.0f} mm > "
                    f"{esp_max_adm:.0f} mm admissible → NON VÉRIFIÉ."
                )
    else:
        res.controle_espacement = True
        messages.append(
            f"σ_s,ser = {sigma_s_ser:.0f} MPa : hors tableau 7.3N. "
            "Contrôle espacement non applicable."
        )

    # Verdict global
    checks = [res.controle_As_min, res.controle_diametre, res.controle_espacement]
    if all(checks):
        res.verdict = "Vérifié"
    elif any(not c for c in checks):
        res.verdict = "Non vérifié"
    else:
        res.verdict = "Vérifié sous réserve"

    res.messages = messages
    return res


def _arrondir_sigma(sigma: float) -> int:
    """Arrondit sigma_s vers la valeur du tableau la plus proche (par excès)."""
    paliers = sorted(TABLEAU_DIAMETRE_MAX.keys())
    for p in paliers:
        if sigma <= p:
            return p
    return paliers[-1] if paliers else 0
