"""Service de suggestion de ferraillage."""
from __future__ import annotations

from app.models.section_models import DonneesGeometrie
from app.models.result_models import ResultatFlexionELU, SolutionArmature
from app.core.steel_catalog import (
    find_rebar_solutions, check_spacing_and_constructability,
    compute_layers_area_mm2, compute_real_effective_depth_from_layers,
    format_rebar_design,
)
from app.constants import AVAILABLE_DIAMETERS_MM


def proposer_solutions(
    resultat_elu: ResultatFlexionELU,
    geometrie: DonneesGeometrie,
    diametres_autorises: list[int] | None = None,
    max_barres: int = 10,
    max_lits: int = 3,
) -> list[SolutionArmature]:
    """Propose des solutions de ferraillage classées par pertinence."""
    if not resultat_elu.calcul_valide or resultat_elu.As_requise <= 0:
        return []

    As_req = resultat_elu.As_requise

    if diametres_autorises is None:
        diametres_autorises = AVAILABLE_DIAMETERS_MM

    # Recherche de solutions
    raw_solutions = find_rebar_solutions(
        As_req, diametres_autorises, max_barres, max_lits,
    )

    solutions: list[SolutionArmature] = []

    for raw in raw_solutions:
        # Vérification constructive
        check = check_spacing_and_constructability(
            geometrie.b_w,
            geometrie.c_nom,
            geometrie.diam_etrier,
            raw["lits"],
            geometrie.espacement_horizontal,
            geometrie.d_g,
        )

        sol = SolutionArmature(
            lits=raw["lits"],
            As_totale_mm2=raw["As_totale_mm2"],
            As_totale_cm2=raw["As_totale_cm2"],
            ecart_mm2=raw["ecart_mm2"],
            ecart_pourcent=raw["ecart_pourcent"],
            nb_lits=raw["nb_lits"],
            faisable=check["verifie"],
            score=raw["score"] + (0 if check["verifie"] else 100),
            description=raw["description"],
        )
        solutions.append(sol)

    # Trier par faisabilité puis par score
    solutions.sort(key=lambda s: (not s.faisable, s.score))

    return solutions
