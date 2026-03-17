"""Dimensionnement à l'effort tranchant – EC2 §6.2.

Calcul de :
  - VRd,c (résistance béton seul)
  - VRd,s (résistance armatures transversales)
  - VRd,max (bielles comprimées)
  - Vérification Asw/s requis et espacement
"""
from __future__ import annotations

import math
from typing import Optional

from app.models.material_models import DonneesBeton, DonneesAcier
from app.models.result_models import ResultatEffortTranchant


def compute_VRdc(
    bw: float,
    d: float,
    fck: float,
    As_mm2: float,
    gamma_c: float = 1.5,
    k1: float = 0.15,
    NEd: float = 0.0,
    Ac: float = 0.0,
) -> float:
    """Résistance à l'effort tranchant du béton seul VRd,c (N) – EC2 §6.2.2.

    VRd,c = [CRd,c * k * (100 * ρ_l * fck)^(1/3) + k1 * σ_cp] * bw * d
    avec un minimum vmin.
    """
    if bw <= 0 or d <= 0 or fck <= 0:
        return 0.0

    CRdc = 0.18 / gamma_c
    k = min(1 + math.sqrt(200.0 / d), 2.0)  # d en mm
    rho_l = min(As_mm2 / (bw * d), 0.02)

    sigma_cp = min(NEd / Ac, 0.2 * fck) if Ac > 0 and NEd > 0 else 0.0

    VRdc_calc = (CRdc * k * (100 * rho_l * fck) ** (1.0 / 3.0) + k1 * sigma_cp) * bw * d

    # Valeur minimale
    vmin = 0.035 * k ** 1.5 * fck ** 0.5
    VRdc_min = (vmin + k1 * sigma_cp) * bw * d

    return max(VRdc_calc, VRdc_min)


def compute_VRds(
    Asw_mm2: float,
    s_mm: float,
    z: float,
    fywd: float,
    theta: float = 45.0,
    alpha: float = 90.0,
) -> float:
    """Résistance des armatures transversales VRd,s (N) – EC2 §6.2.3.

    VRd,s = (Asw / s) * z * fywd * (cot(θ) + cot(α)) * sin(α)
    """
    if s_mm <= 0 or z <= 0 or fywd <= 0:
        return 0.0

    theta_rad = math.radians(theta)
    alpha_rad = math.radians(alpha)

    cot_theta = 1.0 / math.tan(theta_rad) if theta_rad > 0 else 0.0
    cot_alpha = 1.0 / math.tan(alpha_rad) if alpha_rad > 0 else 0.0
    sin_alpha = math.sin(alpha_rad)

    return (Asw_mm2 / s_mm) * z * fywd * (cot_theta + cot_alpha) * sin_alpha


def compute_VRd_max(
    bw: float,
    z: float,
    fck: float,
    gamma_c: float = 1.5,
    theta: float = 45.0,
    alpha: float = 90.0,
    nu1: Optional[float] = None,
) -> float:
    """Résistance maximale des bielles comprimées VRd,max (N) – EC2 §6.2.3.

    VRd,max = α_cw * bw * z * ν₁ * fcd / (cot θ + tan θ)
    """
    if bw <= 0 or z <= 0 or fck <= 0:
        return 0.0

    fcd = fck / gamma_c
    if nu1 is None:
        nu1 = 0.6 * (1 - fck / 250.0)

    theta_rad = math.radians(theta)
    cot_theta = 1.0 / math.tan(theta_rad) if theta_rad > 0 else 0.0
    tan_theta = math.tan(theta_rad)

    alpha_cw = 1.0  # pour béton armé sans précontrainte

    return alpha_cw * bw * z * nu1 * fcd / (cot_theta + tan_theta)


def compute_Asw_s_requis(
    Ved: float,
    z: float,
    fywd: float,
    theta: float = 45.0,
) -> float:
    """Section d'armatures transversales requise Asw/s (mm²/mm).

    Asw/s = Ved / (z * fywd * cot θ)
    """
    if z <= 0 or fywd <= 0:
        return 0.0

    theta_rad = math.radians(theta)
    cot_theta = 1.0 / math.tan(theta_rad) if theta_rad > 0 else 0.0

    if cot_theta <= 0:
        return 0.0

    return Ved / (z * fywd * cot_theta)


def compute_espacement_max(
    d: float,
) -> float:
    """Espacement maximal des étriers – EC2 §9.2.2.

    s_max = 0.75 * d
    """
    return 0.75 * d


def compute_Asw_s_min(
    bw: float,
    fck: float,
    fyk: float,
) -> float:
    """Section minimale d'armatures transversales Asw,min/s (mm²/mm) – EC2 §9.2.2.

    ρ_w,min = 0.08 * √fck / fyk
    Asw,min/s = ρ_w,min * bw
    """
    rho_w_min = 0.08 * math.sqrt(fck) / fyk
    return rho_w_min * bw


# ──────────────────────────────────────────────────────────────────────────
#  Vérification complète effort tranchant
# ──────────────────────────────────────────────────────────────────────────
def verifier_effort_tranchant(
    Ved: float,
    bw: float,
    d: float,
    As_mm2: float,
    beton: DonneesBeton,
    acier: DonneesAcier,
    diam_etrier: float = 8.0,
    nb_branches: int = 2,
    espacement_etriers: float = 200.0,
    theta: float = 45.0,
) -> ResultatEffortTranchant:
    """Vérification complète de l'effort tranchant.

    Args:
        Ved: effort tranchant de calcul (N).
        bw: largeur de l'âme (mm).
        d: hauteur utile (mm).
        As_mm2: section d'armatures longitudinales tendues (mm²).
        beton: propriétés du béton.
        acier: propriétés de l'acier.
        diam_etrier: diamètre de l'étrier (mm).
        nb_branches: nombre de branches de l'étrier.
        espacement_etriers: espacement des étriers (mm).
        theta: angle des bielles comprimées (degrés).

    Returns:
        ResultatEffortTranchant
    """
    res = ResultatEffortTranchant()
    messages: list[str] = []
    res.Ved = abs(Ved)

    z = 0.9 * d  # bras de levier interne

    # VRd,c
    VRdc = compute_VRdc(bw, d, beton.fck, As_mm2, beton.gamma_c)
    res.VRdc = VRdc

    # Besoin d'armatures transversales ?
    res.besoin_armatures = abs(Ved) > VRdc

    if not res.besoin_armatures:
        messages.append(f"Ved = {abs(Ved)/1000:.1f} kN ≤ VRd,c = {VRdc/1000:.1f} kN")
        messages.append("Pas d'armatures transversales requises par le calcul.")
        messages.append("Dispositions minimales d'armatures transversales à respecter.")
    else:
        messages.append(f"Ved = {abs(Ved)/1000:.1f} kN > VRd,c = {VRdc/1000:.1f} kN")
        messages.append("Armatures transversales nécessaires.")

    # VRd,max
    VRd_max = compute_VRd_max(bw, z, beton.fck, beton.gamma_c, theta)
    res.VRd_max = VRd_max

    if abs(Ved) > VRd_max:
        messages.append(f"Ved = {abs(Ved)/1000:.1f} kN > VRd,max = {VRd_max/1000:.1f} kN → RUPTURE BIELLES")
        res.verdict = "Non vérifié"
        res.messages = messages
        return res

    # Asw/s requis
    fywd = acier.fyk / acier.gamma_s
    Asw_s_requis = compute_Asw_s_requis(abs(Ved), z, fywd, theta)
    Asw_s_min = compute_Asw_s_min(bw, beton.fck, acier.fyk)
    Asw_s_requis = max(Asw_s_requis, Asw_s_min)
    res.Asw_s_requis = Asw_s_requis

    # Asw/s réel
    Asw_unit = nb_branches * math.pi * diam_etrier ** 2 / 4.0
    Asw_s_reel = Asw_unit / espacement_etriers if espacement_etriers > 0 else 0.0
    res.Asw_s_reel = Asw_s_reel

    # VRd,s
    VRds = compute_VRds(Asw_unit, espacement_etriers, z, fywd, theta)
    res.VRds = VRds

    # Contrôle section
    res.controle_section = Asw_s_reel >= Asw_s_requis
    if res.controle_section:
        messages.append(f"Asw/s réel = {Asw_s_reel:.3f} mm²/mm ≥ requis = {Asw_s_requis:.3f} mm²/mm → OK.")
    else:
        messages.append(f"Asw/s réel = {Asw_s_reel:.3f} mm²/mm < requis = {Asw_s_requis:.3f} mm²/mm → NON VÉRIFIÉ.")

    # Espacement
    s_max = compute_espacement_max(d)
    res.espacement_reel = espacement_etriers
    res.espacement_max = s_max
    res.controle_espacement = espacement_etriers <= s_max
    if res.controle_espacement:
        messages.append(f"Espacement {espacement_etriers:.0f} mm ≤ s_max = {s_max:.0f} mm → OK.")
    else:
        messages.append(f"Espacement {espacement_etriers:.0f} mm > s_max = {s_max:.0f} mm → NON VÉRIFIÉ.")

    # Verdict
    checks = [res.controle_section, res.controle_espacement]
    if not res.besoin_armatures:
        res.verdict = "Vérifié"
    elif all(checks):
        res.verdict = "Vérifié"
    else:
        res.verdict = "Non vérifié"

    res.messages = messages
    return res
