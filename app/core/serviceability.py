"""Vérifications ELS – structure extensible."""
from __future__ import annotations

from app.models.material_models import DonneesBeton, DonneesAcier
import math


def calculer_moment_fissuration(
    beton: DonneesBeton,
    b: float,
    h: float,
) -> float:
    """Moment de fissuration Mcr (N·mm).

    Mcr = fctm * I / v  avec v = h/2, I = b*h³/12
    """
    fctm = beton.fctm
    I = b * h ** 3 / 12.0
    v = h / 2.0
    if v == 0:
        return 0.0
    return fctm * I / v


def section_fissuree(M_ser: float, Mcr: float) -> bool:
    """Indique si la section est fissurée sous le moment de service."""
    return abs(M_ser) > abs(Mcr)


def calculer_contraintes_service(
    M_ser: float,
    b: float,
    d: float,
    As_mm2: float,
    alpha_e: float,
) -> dict:
    """Calcule les contraintes en service (section fissurée).

    Retourne {"sigma_c": float, "sigma_s": float, "x_ser": float, "z_ser": float}.
    """
    if b <= 0 or d <= 0 or As_mm2 <= 0:
        return {"sigma_c": 0.0, "sigma_s": 0.0, "x_ser": 0.0, "z_ser": 0.0}

    rho = As_mm2 / (b * d)
    k = alpha_e * rho
    alpha_ser = -k + math.sqrt(k ** 2 + 2 * k)
    x_ser = alpha_ser * d
    z_ser = d - x_ser / 3.0

    if z_ser <= 0:
        return {"sigma_c": 0.0, "sigma_s": 0.0, "x_ser": x_ser, "z_ser": 0.0}

    sigma_s = M_ser / (As_mm2 * z_ser) if As_mm2 > 0 else 0.0
    sigma_c = 2 * M_ser / (b * x_ser * z_ser) if x_ser > 0 else 0.0

    return {
        "sigma_c": abs(sigma_c),
        "sigma_s": abs(sigma_s),
        "x_ser": x_ser,
        "z_ser": z_ser,
    }
