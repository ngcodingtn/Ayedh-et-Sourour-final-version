"""Vérifications ELS complètes – EC2 §7.

Module complet de calcul en service :
  - Moment de fissuration Mcr
  - État fissuré / non fissuré
  - Contraintes en service (section brute et fissurée)
  - Sections rectangulaires et en T
"""
from __future__ import annotations

import math

from app.models.material_models import DonneesBeton, DonneesAcier


# ──────────────────────────────────────────────────────────────────────────
#  Rétro-compatibilité : anciens noms
# ──────────────────────────────────────────────────────────────────────────
def calculer_moment_fissuration(beton: DonneesBeton, b: float, h: float) -> float:
    """Alias rétro-compatible → compute_mcr."""
    return compute_mcr(beton.fctm, b, h)


def section_fissuree(M_ser: float, Mcr: float) -> bool:
    """Alias rétro-compatible → is_cracked_section."""
    return is_cracked_section(M_ser, Mcr)


def calculer_contraintes_service(
    M_ser: float, b: float, d: float, As_mm2: float, alpha_e: float,
) -> dict:
    """Alias rétro-compatible → compute_service_stresses_cracked."""
    r = compute_service_stresses_cracked(M_ser, b, d, As_mm2, alpha_e)
    return {"sigma_c": r["sigma_c"], "sigma_s": r["sigma_s"],
            "x_ser": r["x_ser"], "z_ser": r["z_ser"]}


# ──────────────────────────────────────────────────────────────────────────
#  Moment de fissuration
# ──────────────────────────────────────────────────────────────────────────
def compute_mcr(
    fctm: float,
    b: float,
    h: float,
    type_section: str = "rectangulaire",
    beff: float = 0.0,
    bw: float = 0.0,
    hf: float = 0.0,
) -> float:
    """Moment de fissuration Mcr (N·mm).

    Pour section rectangulaire : Mcr = fctm * b * h² / 6
    Pour section T : utilise le centre de gravité et l'inertie de la section brute.
    """
    if h <= 0:
        return 0.0

    if type_section.lower() == "t" and beff > 0 and bw > 0 and hf > 0:
        A_table = beff * hf
        A_ame = bw * (h - hf)
        A_total = A_table + A_ame
        if A_total <= 0:
            return 0.0
        y_table = hf / 2.0
        y_ame = hf + (h - hf) / 2.0
        yG = (A_table * y_table + A_ame * y_ame) / A_total
        I_table = beff * hf ** 3 / 12.0 + A_table * (yG - y_table) ** 2
        I_ame = bw * (h - hf) ** 3 / 12.0 + A_ame * (yG - y_ame) ** 2
        I_total = I_table + I_ame
        v = h - yG
        if v <= 0:
            return 0.0
        return fctm * I_total / v
    else:
        if b <= 0:
            return 0.0
        I = b * h ** 3 / 12.0
        v = h / 2.0
        return fctm * I / v


def is_cracked_section(M_ser: float, Mcr: float) -> bool:
    """Indique si la section est fissurée sous le moment de service."""
    return abs(M_ser) > abs(Mcr)


# ──────────────────────────────────────────────────────────────────────────
#  Contraintes en service — section non fissurée (section brute)
# ──────────────────────────────────────────────────────────────────────────
def compute_service_stresses_uncracked(
    M_ser: float,
    b: float,
    h: float,
    As_mm2: float,
    alpha_e: float,
    type_section: str = "rectangulaire",
    beff: float = 0.0,
    bw: float = 0.0,
    hf: float = 0.0,
    d: float = 0.0,
) -> dict:
    """Contraintes en service pour une section non fissurée (section brute).

    Returns:
        {"sigma_c": float, "sigma_s": float, "yG": float, "I_brut": float}
    """
    if h <= 0 or M_ser == 0:
        return {"sigma_c": 0.0, "sigma_s": 0.0, "yG": 0.0, "I_brut": 0.0}

    if type_section.lower() == "t" and beff > 0 and bw > 0 and hf > 0:
        A_table = beff * hf
        A_ame = bw * (h - hf)
        A_total = A_table + A_ame
        if A_total <= 0:
            return {"sigma_c": 0.0, "sigma_s": 0.0, "yG": 0.0, "I_brut": 0.0}
        y_table = hf / 2.0
        y_ame = hf + (h - hf) / 2.0
        yG = (A_table * y_table + A_ame * y_ame) / A_total
        I_table = beff * hf ** 3 / 12.0 + A_table * (yG - y_table) ** 2
        I_ame = bw * (h - hf) ** 3 / 12.0 + A_ame * (yG - y_ame) ** 2
        I_brut = I_table + I_ame
    else:
        if b <= 0:
            return {"sigma_c": 0.0, "sigma_s": 0.0, "yG": 0.0, "I_brut": 0.0}
        yG = h / 2.0
        I_brut = b * h ** 3 / 12.0

    sigma_c = abs(M_ser) * yG / I_brut if I_brut > 0 else 0.0
    d_eff = d if d > 0 else 0.9 * h
    sigma_s = alpha_e * abs(M_ser) * (d_eff - yG) / I_brut if I_brut > 0 else 0.0

    return {
        "sigma_c": abs(sigma_c),
        "sigma_s": abs(sigma_s),
        "yG": yG,
        "I_brut": I_brut,
    }


# ──────────────────────────────────────────────────────────────────────────
#  Contraintes en service — section fissurée
# ──────────────────────────────────────────────────────────────────────────
def compute_service_stresses_cracked(
    M_ser: float,
    b: float,
    d: float,
    As_mm2: float,
    alpha_e: float,
    As_prime_mm2: float = 0.0,
    d_prime: float = 0.0,
    type_section: str = "rectangulaire",
    beff: float = 0.0,
    bw: float = 0.0,
    hf: float = 0.0,
) -> dict:
    """Contraintes en service pour une section fissurée (section homogénéisée).

    Returns:
        {"sigma_c": float, "sigma_s": float, "x_ser": float, "I_fiss": float, "z_ser": float}
    """
    if d <= 0 or As_mm2 <= 0:
        return {"sigma_c": 0.0, "sigma_s": 0.0, "x_ser": 0.0, "I_fiss": 0.0, "z_ser": 0.0}

    if type_section.lower() == "t" and beff > 0 and bw > 0 and hf > 0:
        x_ser = _solve_neutral_axis_rect(beff, d, As_mm2, alpha_e, As_prime_mm2, d_prime)
        if x_ser <= hf:
            return _stresses_rect(M_ser, beff, d, As_mm2, alpha_e, x_ser, As_prime_mm2, d_prime)
        else:
            x_ser = _solve_neutral_axis_T(beff, bw, hf, d, As_mm2, alpha_e, As_prime_mm2, d_prime)
            return _stresses_T(M_ser, beff, bw, hf, d, As_mm2, alpha_e, x_ser, As_prime_mm2, d_prime)
    else:
        b_calc = b if b > 0 else bw
        if b_calc <= 0:
            return {"sigma_c": 0.0, "sigma_s": 0.0, "x_ser": 0.0, "I_fiss": 0.0, "z_ser": 0.0}
        x_ser = _solve_neutral_axis_rect(b_calc, d, As_mm2, alpha_e, As_prime_mm2, d_prime)
        return _stresses_rect(M_ser, b_calc, d, As_mm2, alpha_e, x_ser, As_prime_mm2, d_prime)


def _solve_neutral_axis_rect(
    b: float, d: float, As: float, alpha_e: float,
    As_prime: float = 0.0, d_prime: float = 0.0,
) -> float:
    """Position de l'axe neutre section fissurée rectangulaire."""
    a = b / 2.0
    b_coeff = alpha_e * (As + As_prime)
    c = -(alpha_e * (As * d + As_prime * d_prime))
    disc = b_coeff ** 2 - 4 * a * c
    if disc < 0:
        return 0.0
    x = (-b_coeff + math.sqrt(disc)) / (2 * a)
    return max(x, 0.0)


def _solve_neutral_axis_T(
    beff: float, bw: float, hf: float, d: float,
    As: float, alpha_e: float,
    As_prime: float = 0.0, d_prime: float = 0.0,
) -> float:
    """Position de l'axe neutre, section T fissurée (x > hf)."""
    a = bw / 2.0
    b_coeff = (beff - bw) * hf + alpha_e * (As + As_prime)
    c = -((beff - bw) * hf ** 2 / 2.0 + alpha_e * (As * d + As_prime * d_prime))
    disc = b_coeff ** 2 - 4 * a * c
    if disc < 0:
        return hf
    x = (-b_coeff + math.sqrt(disc)) / (2 * a)
    return max(x, 0.0)


def _stresses_rect(
    M_ser: float, b: float, d: float, As: float, alpha_e: float,
    x_ser: float, As_prime: float = 0.0, d_prime: float = 0.0,
) -> dict:
    """Contraintes section rectangulaire fissurée."""
    I_fiss = (b * x_ser ** 3 / 3.0
              + alpha_e * As * (d - x_ser) ** 2
              + alpha_e * As_prime * (x_ser - d_prime) ** 2)
    z_ser = d - x_ser / 3.0
    sigma_c = abs(M_ser) * x_ser / I_fiss if I_fiss > 0 else 0.0
    sigma_s = alpha_e * abs(M_ser) * (d - x_ser) / I_fiss if I_fiss > 0 else 0.0
    return {
        "sigma_c": abs(sigma_c),
        "sigma_s": abs(sigma_s),
        "x_ser": x_ser,
        "I_fiss": I_fiss,
        "z_ser": z_ser,
    }


def _stresses_T(
    M_ser: float, beff: float, bw: float, hf: float,
    d: float, As: float, alpha_e: float, x_ser: float,
    As_prime: float = 0.0, d_prime: float = 0.0,
) -> dict:
    """Contraintes section T fissurée."""
    I_fiss = (bw * x_ser ** 3 / 3.0
              + (beff - bw) * hf ** 3 / 12.0
              + (beff - bw) * hf * (x_ser - hf / 2.0) ** 2
              + alpha_e * As * (d - x_ser) ** 2
              + alpha_e * As_prime * (x_ser - d_prime) ** 2)
    z_ser = d - x_ser / 3.0
    sigma_c = abs(M_ser) * x_ser / I_fiss if I_fiss > 0 else 0.0
    sigma_s = alpha_e * abs(M_ser) * (d - x_ser) / I_fiss if I_fiss > 0 else 0.0
    return {
        "sigma_c": abs(sigma_c),
        "sigma_s": abs(sigma_s),
        "x_ser": x_ser,
        "I_fiss": I_fiss,
        "z_ser": z_ser,
    }


# ──────────────────────────────────────────────────────────────────────────
#  Vérification des limites de contraintes
# ──────────────────────────────────────────────────────────────────────────
def check_service_stresses(
    sigma_c: float,
    sigma_s: float,
    fck: float,
    fyk: float,
) -> dict:
    """Vérifie les limites de contraintes en service EC2 §7.2.

    Returns:
        {"sigma_c_lim": float, "sigma_s_lim": float,
         "sigma_c_ok": bool, "sigma_s_ok": bool, "global_ok": bool}
    """
    sigma_c_lim = 0.6 * fck
    sigma_s_lim = 0.8 * fyk
    sigma_c_ok = sigma_c <= sigma_c_lim
    sigma_s_ok = sigma_s <= sigma_s_lim
    return {
        "sigma_c_lim": sigma_c_lim,
        "sigma_s_lim": sigma_s_lim,
        "sigma_c_ok": sigma_c_ok,
        "sigma_s_ok": sigma_s_ok,
        "global_ok": sigma_c_ok and sigma_s_ok,
    }
