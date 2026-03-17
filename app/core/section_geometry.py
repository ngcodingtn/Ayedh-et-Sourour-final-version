"""Géométrie de la section – utilitaires."""
from __future__ import annotations

from app.models.section_models import DonneesGeometrie, TypeSection


def determiner_type_effectif(
    geometrie: DonneesGeometrie,
    moment_positif: bool = True,
) -> TypeSection:
    """Détermine le type de section effectif en mode AUTO."""
    if geometrie.type_section == TypeSection.RECTANGULAIRE:
        return TypeSection.RECTANGULAIRE
    elif geometrie.type_section == TypeSection.T:
        return TypeSection.T
    else:
        # AUTO
        if geometrie.b_eff > 0 and geometrie.h_f > 0 and moment_positif:
            return TypeSection.T
        return TypeSection.RECTANGULAIRE


def calculer_section_beton(geometrie: DonneesGeometrie) -> float:
    """Aire de la section brute de béton (mm²)."""
    t = geometrie.type_section
    if t == TypeSection.RECTANGULAIRE:
        return geometrie.b_w * geometrie.h
    else:
        # Section en T
        aire_table = geometrie.b_eff * geometrie.h_f
        aire_ame = geometrie.b_w * (geometrie.h - geometrie.h_f)
        return aire_table + aire_ame
