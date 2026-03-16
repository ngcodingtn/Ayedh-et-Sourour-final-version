"""Vérification du ferraillage proposé."""
from __future__ import annotations

from app.models.result_models import ResultatVerificationFerraillage
from app.core.steel_catalog import (
    compute_real_effective_depth_from_layers, compute_layers_area_mm2,
)


def verifier_ferraillage(
    lits: list[dict],
    As_requise_mm2: float,
    d_calcul: float,
    h: float,
    c_nom: float,
    diam_etrier: float,
    espacement_vertical: float = 25.0,
    positions_explicites: bool = False,
) -> ResultatVerificationFerraillage:
    """Vérifie le ferraillage proposé par l'utilisateur.

    Args:
        lits: liste de lits [{"diametre": float, "nombre": int,
              optionnel "distance_fibre_mm": float}, ...]
        As_requise_mm2: section requise par le calcul (mm²).
        d_calcul: hauteur utile utilisée dans le calcul (mm).
        h: hauteur totale de la section (mm).
        c_nom: enrobage nominal (mm).
        diam_etrier: diamètre de l'étrier (mm).
        espacement_vertical: espacement vertical entre lits (mm).
        positions_explicites: si True, utilise "distance_fibre_mm" de chaque lit.

    Returns:
        ResultatVerificationFerraillage.
    """
    res = ResultatVerificationFerraillage()
    res.As_requise_mm2 = As_requise_mm2
    res.d_calcul = d_calcul

    # Section réelle
    As_reelle = compute_layers_area_mm2(lits)
    res.As_reelle_mm2 = As_reelle

    # Hauteur utile réelle
    if positions_explicites and all("distance_fibre_mm" in l for l in lits):
        # Utiliser les positions explicites stockées sur les lits
        d_reel, details_lits = _compute_from_explicit_positions(lits, h)
    else:
        d_reel, details_lits = compute_real_effective_depth_from_layers(
            h, c_nom, diam_etrier, lits, espacement_vertical,
        )
    res.d_reel = d_reel
    res.details_lits = details_lits

    # Écart
    ecart = As_reelle - As_requise_mm2
    res.ecart_absolu_mm2 = ecart
    if As_requise_mm2 > 0:
        res.taux_pourcentage = ecart / As_requise_mm2 * 100.0
    else:
        res.taux_pourcentage = 0.0

    # ── Contrôle 1 : section ──
    if As_reelle >= As_requise_mm2:
        res.controle_section = True
        res.message_section = (
            f"As,réelle = {As_reelle/100:.2f} cm² ≥ As,requise = {As_requise_mm2/100:.2f} cm² → OK"
        )
    else:
        res.controle_section = False
        res.message_section = (
            f"As,réelle = {As_reelle/100:.2f} cm² < As,requise = {As_requise_mm2/100:.2f} cm² → NON VÉRIFIÉ"
        )

    # ── Contrôle 2 : bras de levier réel ──
    produit_reel = As_reelle * d_reel
    produit_calcul = As_requise_mm2 * d_calcul

    if produit_reel >= produit_calcul:
        res.controle_bras_levier = True
        res.message_bras_levier = (
            f"As×d réel = {produit_reel/100:.2f} mm·cm² ≥ "
            f"As×d calcul = {produit_calcul/100:.2f} mm·cm² → OK"
        )
    else:
        res.controle_bras_levier = False
        res.message_bras_levier = (
            f"As×d réel = {produit_reel/100:.2f} mm·cm² < "
            f"As×d calcul = {produit_calcul/100:.2f} mm·cm² → NON VÉRIFIÉ"
        )

    # ── Verdict global ──
    res.verdict_global = res.controle_section and res.controle_bras_levier
    if res.verdict_global:
        res.message_verdict = "✓ Ferraillage vérifié."
    else:
        raisons: list[str] = []
        if not res.controle_section:
            raisons.append("section insuffisante")
        if not res.controle_bras_levier:
            raisons.append("bras de levier réel insuffisant")
        res.message_verdict = f"✗ Ferraillage non vérifié : {', '.join(raisons)}."

    return res


def _compute_from_explicit_positions(
    lits: list[dict], h: float,
) -> tuple[float, list[dict]]:
    """Calcule d_reel à partir des positions explicites des lits."""
    import math
    details: list[dict] = []
    sum_ai_di = 0.0
    sum_ai = 0.0

    for idx, lit in enumerate(lits):
        d_barre = lit["diametre"]
        n = lit["nombre"]
        y_centre = lit["distance_fibre_mm"]
        area = n * math.pi * d_barre ** 2 / 4.0
        d_i = h - y_centre

        sum_ai_di += area * d_i
        sum_ai += area

        details.append({
            "lit_numero": idx + 1,
            "nombre_barres": n,
            "diametre_mm": d_barre,
            "section_unitaire_mm2": math.pi * d_barre ** 2 / 4.0,
            "section_totale_mm2": area,
            "section_totale_cm2": area / 100.0,
            "distance_bord_tendu_mm": y_centre,
            "d_i_mm": d_i,
        })

    d_reel = sum_ai_di / sum_ai if sum_ai > 0 else 0.0
    return d_reel, details
