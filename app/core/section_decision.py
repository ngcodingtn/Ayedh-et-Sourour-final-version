"""Décision du type de section – logique métier EC2.

Ce module implémente la règle de décision pour déterminer si le calcul
doit se faire en section rectangulaire équivalente ou en vraie section en T,
en comparant le moment sollicitant MEd_max au moment de référence MTu.

Unités internes : mm, MPa, N·mm.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DecisionSection(Enum):
    """Type de décision retenu pour le calcul."""
    RECTANGULAIRE_EQUIVALENTE_BEFF = "RECTANGULAIRE_EQUIVALENTE_BEFF"
    SECTION_T = "SECTION_T"
    RECTANGULAIRE_BW_NEGATIF = "RECTANGULAIRE_BW_NEGATIF"


@dataclass
class SectionDecisionResult:
    """Résultat de la décision du type de section."""
    MEd_max: float = 0.0           # moment sollicitant (N·mm)
    MTu: float = 0.0               # moment de référence (N·mm)
    moment_sign: str = "positif"   # "positif" ou "négatif"
    decision: DecisionSection = DecisionSection.RECTANGULAIRE_EQUIVALENTE_BEFF
    design_width: float = 0.0      # largeur de calcul retenue (mm)
    explanation: str = ""


def compute_moment_reference_t_section(
    b_eff: float,
    h_f: float,
    fcu: float,
    d: float,
) -> float:
    """Calcule le moment de référence MTu d'une section en T.

    MTu = b_eff × h_f × fcu × (d − h_f / 2)

    Args:
        b_eff: largeur efficace de la table (mm).
        h_f: hauteur de la table (mm).
        fcu: contrainte du bloc rectangulaire simplifié (MPa).
        d: hauteur utile (mm).

    Returns:
        MTu en N·mm.
    """
    return b_eff * h_f * fcu * (d - h_f / 2.0)


def validate_geometry(
    b_eff: float,
    b_w: float,
    h_f: float,
    h: float,
    d: float,
    MEd_max: float,
) -> list[str]:
    """Valide les données géométriques pour la décision de section.

    Returns:
        Liste d'erreurs (vide si tout est correct).
    """
    erreurs: list[str] = []
    if b_eff <= 0:
        erreurs.append("b_eff doit être strictement positif.")
    if b_w <= 0:
        erreurs.append("b_w doit être strictement positif.")
    if h_f <= 0:
        erreurs.append("h_f doit être strictement positif.")
    if h <= 0:
        erreurs.append("h doit être strictement positif.")
    if d <= 0:
        erreurs.append("d doit être strictement positif.")
    if d > h and h > 0 and d > 0:
        erreurs.append("d doit être ≤ h.")
    if b_eff > 0 and b_w > 0 and b_eff < b_w:
        erreurs.append("b_eff doit être ≥ b_w.")
    if h_f > 0 and h > 0 and h_f >= h:
        erreurs.append("h_f doit être < h.")
    if MEd_max < 0:
        erreurs.append("MEd_max doit être ≥ 0 (le signe est géré séparément).")
    return erreurs


def decide_section_type(
    MEd_max: float,
    b_eff: float,
    b_w: float,
    h_f: float,
    h: float,
    d: float,
    fcu: float,
    moment_positif: bool = True,
) -> SectionDecisionResult:
    """Détermine le type de section à utiliser pour le calcul ELU.

    Logique :
      - CAS A : moment négatif → rectangulaire de largeur bw
      - CAS B : moment positif, MEd_max ≤ MTu → rectangulaire équivalente beff
      - CAS C : moment positif, MEd_max > MTu → vraie section en T

    Args:
        MEd_max: moment maximal sollicitant à l'ELU (N·mm), valeur absolue.
        b_eff: largeur efficace de la table (mm).
        b_w: largeur de l'âme (mm).
        h_f: hauteur de la table (mm).
        h: hauteur totale (mm).
        d: hauteur utile (mm).
        fcu: contrainte du bloc rectangulaire simplifié (MPa).
        moment_positif: True si moment positif.

    Returns:
        SectionDecisionResult avec la décision, MTu, largeur de calcul et explication.
    """
    result = SectionDecisionResult()
    result.MEd_max = MEd_max
    result.moment_sign = "positif" if moment_positif else "négatif"

    # CAS A : moment négatif
    if not moment_positif:
        result.decision = DecisionSection.RECTANGULAIRE_BW_NEGATIF
        result.design_width = b_w
        result.MTu = 0.0
        result.explanation = (
            f"Moment négatif : le béton tendu est négligé.\n"
            f"Calcul en section rectangulaire de largeur bw = {b_w:.0f} mm."
        )
        return result

    # CAS B et C : moment positif → calcul de MTu
    MTu = compute_moment_reference_t_section(b_eff, h_f, fcu, d)
    result.MTu = MTu

    if MEd_max <= MTu:
        # CAS B : la zone comprimée reste dans la table
        result.decision = DecisionSection.RECTANGULAIRE_EQUIVALENTE_BEFF
        result.design_width = b_eff
        result.explanation = (
            f"Mu,max = {MEd_max / 1e9:.4f} MN\u00b7m \u2264 MTu = {MTu / 1e9:.4f} MN\u00b7m\n"
            f"La zone comprim\u00e9e est dans la table.\n"
            f"La section en T se comporte comme une section rectangulaire "
            f"\u00e9quivalente de largeur b_eff = {b_eff / 10:.1f} cm."
        )
    else:
        # CAS C : la table ne suffit pas
        result.decision = DecisionSection.SECTION_T
        result.design_width = b_w
        result.explanation = (
            f"Mu,max = {MEd_max / 1e9:.4f} MN\u00b7m > MTu = {MTu / 1e9:.4f} MN\u00b7m\n"
            f"La table seule ne suffit pas.\n"
            f"Calcul en vraie section en T (décomposition table + âme)."
        )

    return result
