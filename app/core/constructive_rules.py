"""Vérifications des règles constructives – EC2 §8 et §9."""
from __future__ import annotations

from app.models.result_models import ResultatConstructif
from app.core.steel_catalog import check_spacing_and_constructability


def verifier_regles_constructives(
    b_w: float,
    h: float,
    c_nom: float,
    diam_etrier: float,
    lits: list[dict],
    espacement_horizontal: float = 25.0,
    espacement_vertical: float = 25.0,
    d_g: float = 20.0,
    nb_max_lits: int = 4,
) -> ResultatConstructif:
    """Vérifie les règles constructives du ferraillage.

    Returns:
        ResultatConstructif.
    """
    res = ResultatConstructif()

    # Vérification de la faisabilité géométrique par lit
    check = check_spacing_and_constructability(
        b_w, c_nom, diam_etrier, lits, espacement_horizontal, d_g,
    )
    res.verifie = check["verifie"]
    res.messages = check["messages"]
    res.largeur_utile_mm = check["largeur_utile_mm"]
    res.nb_max_barres_par_lit = check["nb_max_barres_par_lit"]

    # Contrôle du nombre de lits
    if len(lits) > nb_max_lits:
        res.verifie = False
        res.messages.append({
            "type": "erreur",
            "message": (
                f"Nombre de lits ({len(lits)}) > maximum autorisé ({nb_max_lits})."
            ),
        })

    # Contrôle enrobage
    if c_nom < 20:
        res.messages.append({
            "type": "avertissement",
            "message": f"Enrobage nominal cnom = {c_nom:.0f} mm < 20 mm. Vérifiez la classe d'exposition.",
        })

    # Contrôle diamètre étrier
    if diam_etrier < 6:
        res.messages.append({
            "type": "avertissement",
            "message": f"Diamètre d'étrier = {diam_etrier:.0f} mm < 6 mm. Minimum recommandé : 6 mm.",
        })

    # Contrôle espacement vertical
    for i, lit in enumerate(lits):
        d_barre = lit["diametre"]
        esp_v_min = max(espacement_vertical, d_barre, d_g + 5)
        if espacement_vertical < esp_v_min and espacement_vertical < d_barre:
            res.messages.append({
                "type": "avertissement",
                "message": (
                    f"Lit {i+1} : espacement vertical ({espacement_vertical:.0f} mm) "
                    f"< diamètre de la barre ({d_barre:.0f} mm). "
                    f"Minimum recommandé : {esp_v_min:.0f} mm."
                ),
            })

    # Contrôle passage du béton entre barres
    for i, lit in enumerate(lits):
        d_barre = lit["diametre"]
        esp_libre_min = max(d_barre, d_g + 5, 20)
        if espacement_horizontal < esp_libre_min:
            res.messages.append({
                "type": "avertissement",
                "message": (
                    f"Lit {i+1} : espacement horizontal libre ({espacement_horizontal:.0f} mm) "
                    f"< minimum requis ({esp_libre_min:.0f} mm) pour le passage du béton."
                ),
            })

    return res
