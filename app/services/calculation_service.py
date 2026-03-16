"""Service de calcul principal – orchestre la logique métier."""
from __future__ import annotations

from app.models.section_models import DonneesGeometrie, TypeSection
from app.models.material_models import DonneesMateriaux
from app.models.load_models import DonneesSollicitations
from app.models.reinforcement_models import DonneesFerraillage, DonneesEnvironnement
from app.models.result_models import (
    ResultatFlexionELU, ResultatVerificationFerraillage,
    ResultatConstructif, ResultatFissuration, ResultatsComplets,
)
from app.core.section_decision import (
    decide_section_type, validate_geometry, DecisionSection,
)
from app.core.flexion_rectangular import calcul_flexion_rectangulaire
from app.core.flexion_t_beam import calcul_flexion_T
from app.core.reinforcement_check import verifier_ferraillage
from app.core.constructive_rules import verifier_regles_constructives
from app.core.cracking import controle_fissuration


def calculer_elu(
    geometrie: DonneesGeometrie,
    materiaux: DonneesMateriaux,
    sollicitations: DonneesSollicitations,
) -> ResultatFlexionELU:
    """Effectue le calcul ELU complet.

    La logique de décision est :
      - Si le type choisi est RECTANGULAIRE → calcul rectangulaire classique.
      - Si le type est T ou AUTO → on utilise la décision MEd_max vs MTu.
    """
    # Validation des données
    erreurs = geometrie.valider()
    erreurs.extend(sollicitations.valider())
    if erreurs:
        res = ResultatFlexionELU()
        res.erreurs = erreurs
        res.calcul_valide = False
        return res

    # Hauteur utile effective
    d = geometrie.hauteur_utile_effective()
    h = geometrie.h
    d_prime = geometrie.d_prime if geometrie.d_prime > 0 else 0.1 * h
    MEd_max = sollicitations.M_Ed

    # Section rectangulaire pure → pas besoin de décision T
    if geometrie.type_section == TypeSection.RECTANGULAIRE:
        return calcul_flexion_rectangulaire(
            MEd_max, geometrie.b_w, d, d_prime, h,
            materiaux.beton, materiaux.acier,
        )

    # Section T ou AUTO → validation géométrique et décision
    err_geo = validate_geometry(
        b_eff=geometrie.b_eff, b_w=geometrie.b_w,
        h_f=geometrie.h_f, h=h, d=d, MEd_max=MEd_max,
    )
    if err_geo:
        res = ResultatFlexionELU()
        res.erreurs = err_geo
        res.calcul_valide = False
        return res

    return calcul_flexion_T(
        MEd_max,
        geometrie.b_eff, geometrie.b_w, geometrie.h_f,
        h, d, d_prime,
        materiaux.beton, materiaux.acier,
        sollicitations.moment_positif,
    )


def verifier_ferraillage_propose(
    geometrie: DonneesGeometrie,
    ferraillage: DonneesFerraillage,
    resultat_elu: ResultatFlexionELU,
) -> ResultatVerificationFerraillage:
    """Vérifie le ferraillage proposé."""
    if not ferraillage.lits_tendus:
        res = ResultatVerificationFerraillage()
        res.message_verdict = "Aucun ferraillage proposé."
        return res

    # Inclure les positions explicites si disponibles
    has_positions = any(
        lit.distance_fibre_tendue_cm > 0 for lit in ferraillage.lits_tendus
    )
    lits = []
    for lit in ferraillage.lits_tendus:
        d = {"diametre": lit.diametre_mm, "nombre": lit.nombre_barres}
        if has_positions:
            d["distance_fibre_mm"] = lit.distance_fibre_tendue_cm * 10.0
        lits.append(d)

    return verifier_ferraillage(
        lits=lits,
        As_requise_mm2=resultat_elu.As_requise,
        d_calcul=resultat_elu.d_calcul,
        h=geometrie.h,
        c_nom=geometrie.c_nom,
        diam_etrier=geometrie.diam_etrier,
        espacement_vertical=geometrie.espacement_vertical,
        positions_explicites=has_positions,
    )


def verifier_constructif(
    geometrie: DonneesGeometrie,
    ferraillage: DonneesFerraillage,
) -> ResultatConstructif:
    """Vérifie les règles constructives."""
    if not ferraillage.lits_tendus:
        return ResultatConstructif()

    lits = [
        {"diametre": lit.diametre_mm, "nombre": lit.nombre_barres}
        for lit in ferraillage.lits_tendus
    ]

    return verifier_regles_constructives(
        b_w=geometrie.b_w,
        h=geometrie.h,
        c_nom=geometrie.c_nom,
        diam_etrier=geometrie.diam_etrier,
        lits=lits,
        espacement_horizontal=geometrie.espacement_horizontal,
        espacement_vertical=geometrie.espacement_vertical,
        d_g=geometrie.d_g,
        nb_max_lits=geometrie.nb_max_lits,
    )


def verifier_fissuration(
    geometrie: DonneesGeometrie,
    materiaux: DonneesMateriaux,
    sollicitations: DonneesSollicitations,
    ferraillage: DonneesFerraillage,
    environnement: DonneesEnvironnement,
    resultat_elu: ResultatFlexionELU,
) -> ResultatFissuration:
    """Vérifie la fissuration."""
    As_reelle = ferraillage.As_reelle_mm2
    b = resultat_elu.b_calcul if resultat_elu.b_calcul > 0 else geometrie.b_w
    d = resultat_elu.d_calcul if resultat_elu.d_calcul > 0 else geometrie.hauteur_utile_effective()

    # Diamètre max des barres proposées
    diam_max = max((lit.diametre_mm for lit in ferraillage.lits_tendus), default=16.0)

    return controle_fissuration(
        classe_exposition=environnement.classe_exposition,
        As_reelle_mm2=As_reelle,
        b=b,
        d=d,
        h=geometrie.h,
        M_ser=sollicitations.M_ser,
        beton=materiaux.beton,
        acier=materiaux.acier,
        wmax_impose=environnement.wmax_impose,
        diam_max_propose=diam_max,
    )


def calcul_complet(
    geometrie: DonneesGeometrie,
    materiaux: DonneesMateriaux,
    sollicitations: DonneesSollicitations,
    ferraillage: DonneesFerraillage,
    environnement: DonneesEnvironnement,
) -> ResultatsComplets:
    """Effectue tous les calculs et vérifications."""
    resultats = ResultatsComplets()

    # 1. ELU
    resultats.elu = calculer_elu(geometrie, materiaux, sollicitations)

    if not resultats.elu.calcul_valide:
        return resultats

    # 2. Vérification du ferraillage
    if ferraillage.lits_tendus:
        resultats.verification = verifier_ferraillage_propose(
            geometrie, ferraillage, resultats.elu,
        )

        # 3. Constructif
        resultats.constructif = verifier_constructif(geometrie, ferraillage)

        # 4. Fissuration
        resultats.fissuration = verifier_fissuration(
            geometrie, materiaux, sollicitations,
            ferraillage, environnement, resultats.elu,
        )

    return resultats
