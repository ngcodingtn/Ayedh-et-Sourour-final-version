"""Catalogue complet des armatures longitudinales."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from app.constants import AVAILABLE_DIAMETERS_MM, STEEL_TABLE_CM2


# ──────────────────────────────────────────────
# Fonctions utilitaires
# ──────────────────────────────────────────────

def get_unit_area_mm2(diameter_mm: float) -> float:
    """Aire exacte d'une barre (mm²)."""
    return math.pi * diameter_mm ** 2 / 4.0


def get_unit_area_cm2(diameter_mm: float) -> float:
    """Aire exacte d'une barre (cm²)."""
    return get_unit_area_mm2(diameter_mm) / 100.0


def get_total_area_mm2(diameter_mm: float, n_bars: int) -> float:
    """Section totale de n barres de même diamètre (mm²)."""
    return n_bars * get_unit_area_mm2(diameter_mm)


def get_total_area_cm2(diameter_mm: float, n_bars: int) -> float:
    """Section totale de n barres de même diamètre (cm²)."""
    return get_total_area_mm2(diameter_mm, n_bars) / 100.0


def get_table_area_cm2(diameter_mm: int, n_bars: int) -> Optional[float]:
    """Retourne la section du tableau d'affichage en cm² (1 à 10 barres), ou None."""
    diam_table = STEEL_TABLE_CM2.get(diameter_mm)
    if diam_table is None:
        return None
    return diam_table.get(n_bars)


def compute_layers_area_mm2(layers: list[dict]) -> float:
    """Calcule la section totale à partir d'une liste de lits.

    Chaque lit : {"diametre": float, "nombre": int}
    """
    total = 0.0
    for layer in layers:
        d = layer["diametre"]
        n = layer["nombre"]
        total += get_total_area_mm2(d, n)
    return total


def compute_layers_area_cm2(layers: list[dict]) -> float:
    """Section totale en cm²."""
    return compute_layers_area_mm2(layers) / 100.0


def format_rebar_design(layers: list[dict]) -> str:
    """Formate un ferraillage pour affichage. Ex : '4 HA16 + 3 HA14'."""
    parts: list[str] = []
    for layer in layers:
        d = int(layer["diametre"])
        n = layer["nombre"]
        parts.append(f"{n} HA{d}")
    return " + ".join(parts)


def find_rebar_solutions(
    required_area_mm2: float,
    allowed_diameters: list[int] | None = None,
    max_bars: int = 10,
    max_layers: int = 3,
) -> list[dict]:
    """Recherche de solutions de ferraillage satisfaisant la section requise.

    Retourne une liste de solutions triées par score de pertinence.
    Chaque solution : {
        "lits": [{"diametre": int, "nombre": int}, ...],
        "As_totale_mm2": float,
        "As_totale_cm2": float,
        "ecart_mm2": float,
        "ecart_pourcent": float,
        "nb_lits": int,
        "description": str,
        "score": float,
    }
    """
    if allowed_diameters is None:
        allowed_diameters = AVAILABLE_DIAMETERS_MM

    solutions: list[dict] = []

    # ── Solutions mono-diamètre (1 lit) ────────────────────
    for d in allowed_diameters:
        unit_area = get_unit_area_mm2(d)
        n_min = math.ceil(required_area_mm2 / unit_area)
        for n in range(max(1, n_min), min(n_min + 3, max_bars + 1)):
            area = get_total_area_mm2(d, n)
            if area >= required_area_mm2:
                sol = _make_solution([{"diametre": d, "nombre": n}], required_area_mm2)
                solutions.append(sol)

    # ── Solutions 2 diamètres (2 lits) ─────────────────────
    if max_layers >= 2:
        for i, d1 in enumerate(allowed_diameters):
            for d2 in allowed_diameters[i:]:
                for n1 in range(1, max_bars + 1):
                    area1 = get_total_area_mm2(d1, n1)
                    if area1 >= required_area_mm2:
                        break
                    remaining = required_area_mm2 - area1
                    unit2 = get_unit_area_mm2(d2)
                    n2_min = math.ceil(remaining / unit2)
                    if n2_min > max_bars:
                        continue
                    for n2 in range(n2_min, min(n2_min + 2, max_bars + 1)):
                        area_total = area1 + get_total_area_mm2(d2, n2)
                        if area_total >= required_area_mm2:
                            lits = [{"diametre": d1, "nombre": n1}]
                            if d1 == d2:
                                lits = [{"diametre": d1, "nombre": n1 + n2}]
                            else:
                                lits.append({"diametre": d2, "nombre": n2})
                            sol = _make_solution(lits, required_area_mm2)
                            solutions.append(sol)
                            break

    # Supprimer les doublons par description
    seen = set()
    unique: list[dict] = []
    for s in solutions:
        key = s["description"]
        if key not in seen:
            seen.add(key)
            unique.append(s)
    solutions = unique

    # Trier par score
    solutions.sort(key=lambda s: s["score"])

    return solutions[:30]  # limiter


def _make_solution(lits: list[dict], required_area_mm2: float) -> dict:
    area = compute_layers_area_mm2(lits)
    ecart = area - required_area_mm2
    ecart_pct = (ecart / required_area_mm2 * 100) if required_area_mm2 > 0 else 0.0

    # Score : pénaliser la surarmature et le nombre de lits
    score = abs(ecart_pct) + len(lits) * 2.0
    nb_total_barres = sum(l["nombre"] for l in lits)
    score += nb_total_barres * 0.5

    return {
        "lits": lits,
        "As_totale_mm2": area,
        "As_totale_cm2": area / 100.0,
        "ecart_mm2": ecart,
        "ecart_pourcent": ecart_pct,
        "nb_lits": len(lits),
        "description": format_rebar_design(lits),
        "score": score,
    }


def check_spacing_and_constructability(
    b_w: float,
    c_nom: float,
    diam_etrier: float,
    lits: list[dict],
    espacement_horizontal: float = 25.0,
    d_g: float = 20.0,
) -> dict:
    """Vérifie la faisabilité géométrique du ferraillage.

    Args:
        b_w: largeur de l'âme (mm)
        c_nom: enrobage nominal (mm)
        diam_etrier: diamètre de l'étrier (mm)
        lits: liste de lits [{"diametre": float, "nombre": int}, ...]
        espacement_horizontal: espacement horizontal libre minimal (mm)
        d_g: grosseur maximale du granulat (mm)

    Returns:
        Dictionnaire de résultat avec les contrôles.
    """
    largeur_utile = b_w - 2 * c_nom - 2 * diam_etrier
    espacement_min_requis = max(espacement_horizontal, diam_etrier, d_g + 5)

    messages: list[dict] = []
    verifie = True

    for lit in lits:
        d = lit["diametre"]
        n = lit["nombre"]
        # Largeur occupée : n barres + (n-1) espacements
        largeur_occupee = n * d + (n - 1) * espacement_min_requis

        if largeur_occupee > largeur_utile:
            nb_max = _nb_max_barres(largeur_utile, d, espacement_min_requis)
            messages.append({
                "type": "erreur",
                "message": (
                    f"Lit HA{int(d)} : {n} barres occupent {largeur_occupee:.0f} mm "
                    f"mais la largeur utile est {largeur_utile:.0f} mm. "
                    f"Maximum possible : {nb_max} barres."
                ),
            })
            verifie = False
        else:
            messages.append({
                "type": "ok",
                "message": (
                    f"Lit HA{int(d)} : {n} barres → {largeur_occupee:.0f} mm "
                    f"/ {largeur_utile:.0f} mm disponibles. OK."
                ),
            })

    # Calculer nb max par diamètre
    nb_max_par_diam: dict[float, int] = {}
    for d in AVAILABLE_DIAMETERS_MM:
        nb_max_par_diam[d] = _nb_max_barres(largeur_utile, d, espacement_min_requis)

    return {
        "verifie": verifie,
        "messages": messages,
        "largeur_utile_mm": largeur_utile,
        "nb_max_barres_par_lit": nb_max_par_diam,
    }


def _nb_max_barres(largeur_utile: float, diam: float, espacement: float) -> int:
    """Nombre maximal de barres d'un diamètre dans la largeur utile."""
    if diam <= 0 or espacement < 0:
        return 0
    if largeur_utile < diam:
        return 0
    return int((largeur_utile + espacement) / (diam + espacement))


def compute_real_effective_depth_from_layers(
    h: float,
    c_nom: float,
    diam_etrier: float,
    lits: list[dict],
    espacement_vertical: float = 25.0,
) -> tuple[float, list[dict]]:
    """Calcule la hauteur utile réelle à partir du ferraillage proposé.

    Le premier lit est le plus bas (le plus proche du bord tendu).

    Returns:
        (d_reel, details_lits)
        details_lits : liste de dicts avec les infos par lit.
    """
    details: list[dict] = []
    somme_Ai_di = 0.0
    somme_Ai = 0.0

    y_courant = c_nom + diam_etrier  # distance du bord tendu au centre du 1er lit

    for idx, lit in enumerate(lits):
        d_barre = lit["diametre"]
        n_barres = lit["nombre"]
        section_mm2 = get_total_area_mm2(d_barre, n_barres)

        if idx == 0:
            y_centre = y_courant + d_barre / 2.0
        else:
            y_centre = y_courant + d_barre / 2.0

        d_i = h - y_centre  # hauteur utile de ce lit

        somme_Ai_di += section_mm2 * d_i
        somme_Ai += section_mm2

        details.append({
            "lit_numero": idx + 1,
            "nombre_barres": n_barres,
            "diametre_mm": d_barre,
            "section_unitaire_mm2": get_unit_area_mm2(d_barre),
            "section_totale_mm2": section_mm2,
            "section_totale_cm2": section_mm2 / 100.0,
            "distance_bord_tendu_mm": y_centre,
            "d_i_mm": d_i,
        })

        # Avancer pour le prochain lit
        y_courant = y_centre + d_barre / 2.0 + espacement_vertical

    d_reel = somme_Ai_di / somme_Ai if somme_Ai > 0 else 0.0

    return d_reel, details
