"""Calcul des sollicitations sur poutre – réactions, V(x), M(x).

Poutre sur deux appuis avec possibilité de consoles.
Charges uniformes et concentrées.
Combinaisons ELU et ELS (caractéristique, fréquente, quasi-permanente).
"""
from __future__ import annotations

import math
from typing import Optional

from app.models.load_models import DonneesPoutre, ChargeConcentree
from app.models.result_models import ResultatSollicitations


# ──────────────────────────────────────────────────────────────────────────
#  Combinaisons de charges
# ──────────────────────────────────────────────────────────────────────────
def combine_loads_elu(g: float, q: float) -> float:
    """Combinaison ELU = 1.35 G + 1.5 Q."""
    return 1.35 * g + 1.5 * q


def combine_loads_els_characteristic(g: float, q: float) -> float:
    """ELS caractéristique = G + Q."""
    return g + q


def combine_loads_els_frequent(g: float, q: float, psi_1: float = 0.5) -> float:
    """ELS fréquente = G + ψ₁ Q."""
    return g + psi_1 * q


def combine_loads_els_quasi_permanent(g: float, q: float, psi_2: float = 0.3) -> float:
    """ELS quasi-permanente = G + ψ₂ Q."""
    return g + psi_2 * q


def _combine_factor(combinaison: str, psi_1: float = 0.5, psi_2: float = 0.3):
    """Retourne (gamma_G, gamma_Q) pour la combinaison donnée."""
    if combinaison == "ELU":
        return 1.35, 1.5
    elif combinaison == "ELS caractéristique":
        return 1.0, 1.0
    elif combinaison == "ELS fréquente":
        return 1.0, psi_1
    elif combinaison == "ELS quasi-permanente":
        return 1.0, psi_2
    else:
        return 1.35, 1.5


# ──────────────────────────────────────────────────────────────────────────
#  Réactions d'appui
# ──────────────────────────────────────────────────────────────────────────
def compute_support_reactions(
    poutre: DonneesPoutre,
    combinaison: str = "ELU",
) -> tuple[float, float]:
    """Calcule les réactions d'appui RA et RB (N).

    Poutre isostatique sur deux appuis.
    """
    gamma_G, gamma_Q = _combine_factor(combinaison, poutre.psi_1, poutre.psi_2)

    L_total = poutre.longueur_totale_mm
    xA = poutre.position_appui_A_mm
    xB = poutre.position_appui_B_mm
    portee = xB - xA

    if portee <= 0:
        return 0.0, 0.0

    # Charge répartie combinée
    w = gamma_G * poutre.g_N_mm + gamma_Q * poutre.q_N_mm

    # Moment des charges réparties par rapport à A
    # Charge répartie sur toute la longueur
    # Moment par rapport à A de la charge uniformément répartie
    # Force totale = w * L_total, appliquée à L_total/2 depuis x=0
    F_repartie = w * L_total
    M_repartie_A = w * L_total * (L_total / 2.0 - xA)

    # Charges concentrées
    M_concentrees_A = 0.0
    F_concentrees = 0.0
    for cc in poutre.charges_concentrees:
        F_cc = gamma_G * cc.G_N + gamma_Q * cc.Q_N
        M_concentrees_A += F_cc * (cc.position_mm - xA)
        F_concentrees += F_cc

    # RB par moments en A : RB * portee = M_repartie_A + M_concentrees_A
    RB = (M_repartie_A + M_concentrees_A) / portee

    # RA par équilibre : RA + RB = F_repartie + F_concentrees
    RA = F_repartie + F_concentrees - RB

    return RA, RB


# ──────────────────────────────────────────────────────────────────────────
#  Effort tranchant V(x)
# ──────────────────────────────────────────────────────────────────────────
def compute_shear_at_x(
    poutre: DonneesPoutre,
    x: float,
    combinaison: str = "ELU",
) -> float:
    """Effort tranchant V(x) en N à la position x (mm)."""
    gamma_G, gamma_Q = _combine_factor(combinaison, poutre.psi_1, poutre.psi_2)
    xA = poutre.position_appui_A_mm
    xB = poutre.position_appui_B_mm

    RA, RB = compute_support_reactions(poutre, combinaison)

    w = gamma_G * poutre.g_N_mm + gamma_Q * poutre.q_N_mm

    # V(x) = -w*x + RA*(x >= xA) + RB*(x >= xB) - charges concentrées accumulées
    V = -w * x

    if x >= xA:
        V += RA
    if x >= xB:
        V += RB

    for cc in poutre.charges_concentrees:
        F_cc = gamma_G * cc.G_N + gamma_Q * cc.Q_N
        if x >= cc.position_mm:
            V -= F_cc

    return V


def compute_shear_diagram(
    poutre: DonneesPoutre,
    combinaison: str = "ELU",
    n_points: int = 200,
) -> tuple[list[float], list[float]]:
    """Diagramme de l'effort tranchant.

    Returns:
        (x_values, V_values) en mm et N.
    """
    L = poutre.longueur_totale_mm
    dx = L / n_points
    x_vals = [i * dx for i in range(n_points + 1)]
    V_vals = [compute_shear_at_x(poutre, x, combinaison) for x in x_vals]
    return x_vals, V_vals


# ──────────────────────────────────────────────────────────────────────────
#  Moment fléchissant M(x)
# ──────────────────────────────────────────────────────────────────────────
def compute_moment_at_x(
    poutre: DonneesPoutre,
    x: float,
    combinaison: str = "ELU",
) -> float:
    """Moment fléchissant M(x) en N·mm à la position x (mm)."""
    gamma_G, gamma_Q = _combine_factor(combinaison, poutre.psi_1, poutre.psi_2)
    xA = poutre.position_appui_A_mm
    xB = poutre.position_appui_B_mm

    RA, RB = compute_support_reactions(poutre, combinaison)

    w = gamma_G * poutre.g_N_mm + gamma_Q * poutre.q_N_mm

    # M(x) = -w*x²/2 + RA*(x-xA) si x>=xA + RB*(x-xB) si x>=xB - Σ F*(x-xi) si x>=xi
    M = -w * x ** 2 / 2.0

    if x >= xA:
        M += RA * (x - xA)
    if x >= xB:
        M += RB * (x - xB)

    for cc in poutre.charges_concentrees:
        F_cc = gamma_G * cc.G_N + gamma_Q * cc.Q_N
        if x >= cc.position_mm:
            M -= F_cc * (x - cc.position_mm)

    return M


def compute_moment_diagram(
    poutre: DonneesPoutre,
    combinaison: str = "ELU",
    n_points: int = 200,
) -> tuple[list[float], list[float]]:
    """Diagramme du moment fléchissant.

    Returns:
        (x_values, M_values) en mm et N·mm.
    """
    L = poutre.longueur_totale_mm
    dx = L / n_points
    x_vals = [i * dx for i in range(n_points + 1)]
    M_vals = [compute_moment_at_x(poutre, x, combinaison) for x in x_vals]
    return x_vals, M_vals


# ──────────────────────────────────────────────────────────────────────────
#  Extrema
# ──────────────────────────────────────────────────────────────────────────
def find_moment_extrema(
    poutre: DonneesPoutre,
    combinaison: str = "ELU",
    n_points: int = 500,
) -> dict:
    """Trouve le moment max et min et leurs positions.

    Returns:
        {"M_max": float, "x_M_max": float, "M_min": float, "x_M_min": float}
    """
    x_vals, M_vals = compute_moment_diagram(poutre, combinaison, n_points)
    M_max = max(M_vals)
    M_min = min(M_vals)
    x_M_max = x_vals[M_vals.index(M_max)]
    x_M_min = x_vals[M_vals.index(M_min)]
    return {"M_max": M_max, "x_M_max": x_M_max, "M_min": M_min, "x_M_min": x_M_min}


def find_shear_extrema(
    poutre: DonneesPoutre,
    combinaison: str = "ELU",
    n_points: int = 500,
) -> dict:
    """Trouve l'effort tranchant max et min.

    Returns:
        {"V_max": float, "x_V_max": float, "V_min": float, "x_V_min": float}
    """
    x_vals, V_vals = compute_shear_diagram(poutre, combinaison, n_points)
    V_max = max(V_vals)
    V_min = min(V_vals)
    x_V_max = x_vals[V_vals.index(V_max)]
    x_V_min = x_vals[V_vals.index(V_min)]
    return {"V_max": V_max, "x_V_max": x_V_max, "V_min": V_min, "x_V_min": x_V_min}


# ──────────────────────────────────────────────────────────────────────────
#  Zone de la position x
# ──────────────────────────────────────────────────────────────────────────
def determine_zone(poutre: DonneesPoutre, x: float) -> str:
    """Détermine la zone de la position x."""
    xA = poutre.position_appui_A_mm
    xB = poutre.position_appui_B_mm
    tol = 1.0  # mm

    if abs(x - xA) < tol:
        return "appui A"
    if abs(x - xB) < tol:
        return "appui B"
    if x < xA:
        return "console gauche"
    if x > xB:
        return "console droite"
    return "travée"


# ──────────────────────────────────────────────────────────────────────────
#  Calcul complet des sollicitations
# ──────────────────────────────────────────────────────────────────────────
def calculer_sollicitations(
    poutre: DonneesPoutre,
    x_choisi: float,
    combinaison: str = "ELU",
) -> ResultatSollicitations:
    """Calcul complet des sollicitations à une position x.

    Returns:
        ResultatSollicitations avec diagrammes et valeurs au point choisi.
    """
    res = ResultatSollicitations()

    erreurs = poutre.valider()
    if erreurs:
        res.erreurs = erreurs
        return res

    RA, RB = compute_support_reactions(poutre, combinaison)
    res.RA = RA
    res.RB = RB

    res.x_choisi = x_choisi
    res.Vx = compute_shear_at_x(poutre, x_choisi, combinaison)
    res.Mx = compute_moment_at_x(poutre, x_choisi, combinaison)
    res.zone = determine_zone(poutre, x_choisi)
    res.combinaison = combinaison

    # Diagrammes
    x_vals, V_vals = compute_shear_diagram(poutre, combinaison)
    x_vals_m, M_vals = compute_moment_diagram(poutre, combinaison)
    res.x_values = x_vals
    res.V_values = V_vals
    res.M_values = M_vals

    # Extrema
    m_ext = find_moment_extrema(poutre, combinaison)
    res.M_max = m_ext["M_max"]
    res.M_min = m_ext["M_min"]
    res.x_M_max = m_ext["x_M_max"]

    v_ext = find_shear_extrema(poutre, combinaison)
    res.V_max = v_ext["V_max"]
    res.V_min = v_ext["V_min"]
    res.x_V_max = v_ext["x_V_max"]

    # Moments ELU et ELS au point x pour liaison avec les autres modules
    res.MEd = abs(compute_moment_at_x(poutre, x_choisi, "ELU"))
    res.Mser = abs(compute_moment_at_x(poutre, x_choisi, "ELS caractéristique"))
    res.Ved = abs(compute_shear_at_x(poutre, x_choisi, "ELU"))

    res.calcul_valide = True
    return res
