"""Fissuration et contrôle complet – EC2 §7.3.

Module de contrôle de la fissuration :
  1. compute_as_min : section minimale
  2. check_crack_control_without_direct_calculation : contrôle simplifié
  3. prepare_direct_crack_calculation : calcul direct wk (architecture extensible)
  4. controle_fissuration_complet : orchestration complète
"""
from __future__ import annotations

import math
from typing import Optional

from app.models.material_models import DonneesBeton, DonneesAcier
from app.models.result_models import ResultatFissuration
from app.constants import (
    WMAX_PAR_CLASSE, TABLEAU_DIAMETRE_MAX, TABLEAU_ESPACEMENT_MAX,
)
from app.core.flexion_common import calculer_As_min
from app.core.serviceability import (
    compute_mcr, is_cracked_section,
    compute_service_stresses_uncracked,
    compute_service_stresses_cracked,
    check_service_stresses,
)


# ──────────────────────────────────────────────────────────────────────────
#  Section minimale de fissuration
# ──────────────────────────────────────────────────────────────────────────
def compute_as_min(
    beton: DonneesBeton,
    acier: DonneesAcier,
    b: float,
    d: float,
) -> float:
    """Section minimale d'armatures tendues (mm²) – EC2 §9.2.1.1."""
    return calculer_As_min(beton, acier, b, d)


# ──────────────────────────────────────────────────────────────────────────
#  Contrôle simplifié sans calcul direct – tables 7.2N / 7.3N
# ──────────────────────────────────────────────────────────────────────────
def check_crack_control_without_direct_calculation(
    sigma_s: float,
    wmax: float,
    diam_max_propose: float = 16.0,
    espacement_propose: float = 150.0,
) -> dict:
    """Vérification simplifiée de la fissuration (sans calcul direct de wk).

    Returns:
        {"phi_max_adm": float|None, "esp_max_adm": float|None,
         "controle_diametre": bool, "controle_espacement": bool,
         "verdict": bool, "messages": list[str]}
    """
    messages: list[str] = []
    sigma_arrondi = _arrondir_sigma(sigma_s)

    # Diamètre max (tableau 7.2N)
    phi_max_adm = None
    controle_diametre = True
    if sigma_arrondi in TABLEAU_DIAMETRE_MAX:
        phi_max_adm = TABLEAU_DIAMETRE_MAX[sigma_arrondi].get(wmax)
        if phi_max_adm is not None:
            controle_diametre = diam_max_propose <= phi_max_adm
            if controle_diametre:
                messages.append(
                    f"Diamètre HA{diam_max_propose:.0f} ≤ HA{phi_max_adm:.0f} admissible → OK."
                )
            else:
                messages.append(
                    f"Diamètre HA{diam_max_propose:.0f} > HA{phi_max_adm:.0f} admissible → NON VÉRIFIÉ."
                )
    else:
        messages.append(
            f"σ_s = {sigma_s:.0f} MPa : hors tableau 7.2N. Contrôle diamètre non applicable."
        )

    # Espacement max (tableau 7.3N)
    esp_max_adm = None
    controle_espacement = True
    if sigma_arrondi in TABLEAU_ESPACEMENT_MAX:
        esp_max_adm = TABLEAU_ESPACEMENT_MAX[sigma_arrondi].get(wmax)
        if esp_max_adm is not None:
            controle_espacement = espacement_propose <= esp_max_adm
            if controle_espacement:
                messages.append(
                    f"Espacement {espacement_propose:.0f} mm ≤ {esp_max_adm:.0f} mm admissible → OK."
                )
            else:
                messages.append(
                    f"Espacement {espacement_propose:.0f} mm > {esp_max_adm:.0f} mm admissible → NON VÉRIFIÉ."
                )
    else:
        messages.append(
            f"σ_s = {sigma_s:.0f} MPa : hors tableau 7.3N. Contrôle espacement non applicable."
        )

    return {
        "phi_max_adm": phi_max_adm,
        "esp_max_adm": esp_max_adm,
        "controle_diametre": controle_diametre,
        "controle_espacement": controle_espacement,
        "verdict": controle_diametre and controle_espacement,
        "messages": messages,
    }


# ──────────────────────────────────────────────────────────────────────────
#  Calcul direct de fissuration — architecture extensible
# ──────────────────────────────────────────────────────────────────────────
def prepare_direct_crack_calculation(
    sigma_s: float,
    Es: float,
    fctm: float,
    rho_p_eff: float,
    phi: float,
    c_nom: float,
    k1: float = 0.8,
    k2: float = 0.5,
    k3: float = 3.4,
    k4: float = 0.425,
    kt: float = 0.6,
) -> dict:
    """Calcul direct de l'ouverture de fissure wk — EC2 §7.3.4.

    wk = sr_max * (epsilon_sm - epsilon_cm)

    Returns:
        {"sr_max": float, "epsilon_sm_minus_cm": float, "wk": float}
    """
    if Es <= 0 or rho_p_eff <= 0 or phi <= 0:
        return {"sr_max": 0.0, "epsilon_sm_minus_cm": 0.0, "wk": 0.0}

    # Longueur de transfert maximale
    sr_max = k3 * c_nom + k1 * k2 * k4 * phi / rho_p_eff

    # Déformation relative
    epsilon_sm_minus_cm = (sigma_s - kt * fctm / rho_p_eff * (1 + alpha_e_ratio(Es, fctm) * rho_p_eff)) / Es
    epsilon_min = 0.6 * sigma_s / Es
    epsilon_sm_minus_cm = max(epsilon_sm_minus_cm, epsilon_min)

    wk = sr_max * epsilon_sm_minus_cm

    return {
        "sr_max": sr_max,
        "epsilon_sm_minus_cm": epsilon_sm_minus_cm,
        "wk": max(wk, 0.0),
    }


def alpha_e_ratio(Es: float, fctm: float) -> float:
    """Rapport alpha_e approximatif pour le calcul direct."""
    # Ecm approx à partir de fctm (inverse de fctm = 0.3 * fck^(2/3))
    # On utilise une valeur standard
    return Es / 30000.0 if Es > 0 else 15.0


# ──────────────────────────────────────────────────────────────────────────
#  Contrôle complet de fissuration
# ──────────────────────────────────────────────────────────────────────────
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
    type_section: str = "rectangulaire",
    beff: float = 0.0,
    bw: float = 0.0,
    hf: float = 0.0,
    d_prime: float = 0.0,
    As_prime_mm2: float = 0.0,
) -> ResultatFissuration:
    """Contrôle complet de la fissuration – logique ELS réelle.

    Étapes :
      1. Calcul de Mcr
      2. Comparaison Mser / Mcr
      3. Calcul des contraintes (section brute ou fissurée)
      4. Vérification des limites de contraintes
      5. Vérification simplifiée (tables 7.2N / 7.3N)
      6. Verdict global
    """
    res = ResultatFissuration()
    messages: list[str] = []

    # Déterminer wmax
    wmax = wmax_impose if wmax_impose is not None else WMAX_PAR_CLASSE.get(classe_exposition)
    res.wmax_recommande = wmax

    if wmax is None:
        messages.append(
            f"Classe {classe_exposition} : dispositions particulières requises. "
            "Contrôle simplifié non applicable."
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
        messages.append(f"As,réelle = {As_reelle_mm2/100:.2f} cm² < As,min = {As_min/100:.2f} cm² → NON VÉRIFIÉ.")
    else:
        messages.append(f"As,réelle = {As_reelle_mm2/100:.2f} cm² ≥ As,min = {As_min/100:.2f} cm² → OK.")

    # Calcul de Mcr
    b_mcr = b if b > 0 else bw
    Mcr = compute_mcr(beton.fctm, b_mcr, h, type_section, beff, bw, hf)
    res.Mcr = Mcr

    # État de fissuration
    fissure = is_cracked_section(M_ser, Mcr)
    res.section_fissuree = fissure

    if fissure:
        messages.append(f"Mser = {M_ser/1e6:.2f} kN·m > Mcr = {Mcr/1e6:.2f} kN·m → Section fissurée.")
    else:
        messages.append(f"Mser = {M_ser/1e6:.2f} kN·m ≤ Mcr = {Mcr/1e6:.2f} kN·m → Section non fissurée.")

    # Calcul alpha_e
    alpha_e = acier.Es / beton.Ecm if beton.Ecm > 0 else 15.0

    # Contraintes en service
    if fissure and As_reelle_mm2 > 0:
        stresses = compute_service_stresses_cracked(
            M_ser, b, d, As_reelle_mm2, alpha_e,
            As_prime_mm2, d_prime, type_section, beff, bw, hf,
        )
        messages.append(f"Axe neutre fissurée : x = {stresses['x_ser']:.1f} mm")
        messages.append(f"Inertie fissurée : I = {stresses['I_fiss']:.0f} mm⁴")
    else:
        stresses = compute_service_stresses_uncracked(
            M_ser, b, h, As_reelle_mm2, alpha_e,
            type_section, beff, bw, hf, d,
        )

    sigma_c = stresses.get("sigma_c", 0.0)
    sigma_s = stresses.get("sigma_s", 0.0)
    res.sigma_s_service = sigma_s
    res.sigma_c_service = sigma_c
    res.x_ser = stresses.get("x_ser", 0.0)
    res.I_fiss = stresses.get("I_fiss", 0.0)

    # Vérification des limites de contraintes
    stress_check = check_service_stresses(sigma_c, sigma_s, beton.fck, acier.fyk)
    res.sigma_c_lim = stress_check["sigma_c_lim"]
    res.sigma_s_lim = stress_check["sigma_s_lim"]
    res.controle_sigma_c = stress_check["sigma_c_ok"]
    res.controle_sigma_s = stress_check["sigma_s_ok"]

    if stress_check["sigma_c_ok"]:
        messages.append(f"σ_c = {sigma_c:.1f} MPa ≤ 0.6·fck = {stress_check['sigma_c_lim']:.1f} MPa → OK.")
    else:
        messages.append(f"σ_c = {sigma_c:.1f} MPa > 0.6·fck = {stress_check['sigma_c_lim']:.1f} MPa → NON VÉRIFIÉ.")

    if stress_check["sigma_s_ok"]:
        messages.append(f"σ_s = {sigma_s:.1f} MPa ≤ 0.8·fyk = {stress_check['sigma_s_lim']:.1f} MPa → OK.")
    else:
        messages.append(f"σ_s = {sigma_s:.1f} MPa > 0.8·fyk = {stress_check['sigma_s_lim']:.1f} MPa → NON VÉRIFIÉ.")

    # Contrôle simplifié (diamètre + espacement)
    if fissure:
        crack_ctrl = check_crack_control_without_direct_calculation(
            sigma_s, wmax, diam_max_propose, espacement_propose,
        )
        res.diametre_max_admissible = crack_ctrl["phi_max_adm"]
        res.espacement_max_admissible = crack_ctrl["esp_max_adm"]
        res.controle_diametre = crack_ctrl["controle_diametre"]
        res.controle_espacement = crack_ctrl["controle_espacement"]
        res.diam_propose = diam_max_propose
        res.espacement_propose = espacement_propose
        messages.extend(crack_ctrl["messages"])
    else:
        res.controle_diametre = True
        res.controle_espacement = True
        messages.append("Section non fissurée → contrôle simplifié non nécessaire.")

    # Verdict global
    checks = [
        res.controle_As_min,
        stress_check["global_ok"],
        res.controle_diametre,
        res.controle_espacement,
    ]
    if all(checks):
        res.verdict = "Vérifié"
    else:
        res.verdict = "Non vérifié"

    res.messages = messages
    return res


# ──────────────────────────────────────────────────────────────────────────
#  Rétro-compatibilité : l'ancienne API reste fonctionnelle
# ──────────────────────────────────────────────────────────────────────────
# controle_fissuration a la même signature de base (paramètres supplémentaires
# ont des valeurs par défaut), donc tout code existant continue de fonctionner.


def _arrondir_sigma(sigma: float) -> int:
    """Arrondit sigma_s vers la valeur du tableau la plus proche (par excès)."""
    paliers = sorted(TABLEAU_DIAMETRE_MAX.keys())
    for p in paliers:
        if sigma <= p:
            return p
    return paliers[-1] if paliers else 0
