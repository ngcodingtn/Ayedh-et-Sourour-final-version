"""Service de calcul principal – orchestre la logique métier."""
from __future__ import annotations

from app.models.section_models import DonneesGeometrie, TypeSection
from app.models.material_models import DonneesMateriaux
from app.models.load_models import DonneesSollicitations, DonneesPoutre
from app.models.reinforcement_models import DonneesFerraillage, DonneesEnvironnement
from app.models.result_models import (
    ResultatFlexionELU, ResultatVerificationFerraillage,
    ResultatConstructif, ResultatFissuration, ResultatsComplets,
    ResultatSollicitations, ResultatEffortTranchant,
)
from app.core.section_decision import (
    decide_section_type, validate_geometry, DecisionSection,
)
from app.core.flexion_rectangular import calcul_flexion_rectangulaire
from app.core.flexion_t_beam import calcul_flexion_T
from app.core.reinforcement_check import verifier_ferraillage
from app.core.constructive_rules import verifier_regles_constructives
from app.core.cracking import controle_fissuration
from app.core.beam_loads import calculer_sollicitations
from app.core.shear_design import verifier_effort_tranchant


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
    """Vérifie la fissuration avec la logique ELS complète."""
    As_reelle = ferraillage.As_reelle_mm2
    b = resultat_elu.b_calcul if resultat_elu.b_calcul > 0 else geometrie.b_w
    d = resultat_elu.d_calcul if resultat_elu.d_calcul > 0 else geometrie.hauteur_utile_effective()

    # Diamètre max des barres proposées
    diam_max = max((lit.diametre_mm for lit in ferraillage.lits_tendus), default=16.0)

    # Type de section pour le calcul ELS
    type_section = "rectangulaire"
    if geometrie.type_section in (TypeSection.T, TypeSection.AUTO):
        if geometrie.b_eff > 0 and geometrie.h_f > 0:
            type_section = "t"

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
        type_section=type_section,
        beff=geometrie.b_eff,
        bw=geometrie.b_w,
        hf=geometrie.h_f,
        d_prime=geometrie.d_prime,
        As_prime_mm2=ferraillage.As_prime_mm2,
    )


def calculer_sollicitations_poutre(
    poutre: DonneesPoutre,
    x_choisi: float,
    combinaison: str = "ELU",
) -> ResultatSollicitations:
    """Calcul des sollicitations sur la poutre."""
    return calculer_sollicitations(poutre, x_choisi, combinaison)


def calculer_effort_tranchant(
    Ved: float,
    geometrie: DonneesGeometrie,
    materiaux: DonneesMateriaux,
    As_mm2: float,
    diam_etrier: float = 8.0,
    nb_branches: int = 2,
    espacement_etriers: float = 200.0,
    theta: float = 45.0,
) -> ResultatEffortTranchant:
    """Calcul et vérification de l'effort tranchant."""
    d = geometrie.hauteur_utile_effective()
    return verifier_effort_tranchant(
        Ved=Ved,
        bw=geometrie.b_w,
        d=d,
        As_mm2=As_mm2,
        beton=materiaux.beton,
        acier=materiaux.acier,
        diam_etrier=diam_etrier,
        nb_branches=nb_branches,
        espacement_etriers=espacement_etriers,
        theta=theta,
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


def calcul_complet_avec_poutre(
    geometrie: DonneesGeometrie,
    materiaux: DonneesMateriaux,
    sollicitations: DonneesSollicitations,
    ferraillage: DonneesFerraillage,
    environnement: DonneesEnvironnement,
    poutre: DonneesPoutre = None,
    x_choisi: float = 0.0,
    combinaison: str = "ELU",
    diam_etrier: float = 8.0,
    nb_branches: int = 2,
    espacement_etriers: float = 200.0,
) -> ResultatsComplets:
    """Calcul complet intégré : charges → moments → flexion → fissuration → effort tranchant."""
    resultats = ResultatsComplets()

    # 1. Sollicitations (si poutre fournie)
    if poutre is not None:
        res_sol = calculer_sollicitations_poutre(poutre, x_choisi, combinaison)
        resultats.sollicitations = res_sol

        if res_sol.calcul_valide:
            # Mettre à jour les sollicitations avec les valeurs calculées
            sollicitations = DonneesSollicitations(
                M_Ed=res_sol.MEd,
                M_ser=res_sol.Mser,
                moment_positif=res_sol.Mx >= 0,
            )

    # 2. ELU
    resultats.elu = calculer_elu(geometrie, materiaux, sollicitations)

    if not resultats.elu.calcul_valide:
        return resultats

    # 3. Vérification du ferraillage
    if ferraillage.lits_tendus:
        resultats.verification = verifier_ferraillage_propose(
            geometrie, ferraillage, resultats.elu,
        )

        # 4. Constructif
        resultats.constructif = verifier_constructif(geometrie, ferraillage)

        # 5. Fissuration
        resultats.fissuration = verifier_fissuration(
            geometrie, materiaux, sollicitations,
            ferraillage, environnement, resultats.elu,
        )

    # 6. Effort tranchant (si poutre fournie)
    if poutre is not None and resultats.sollicitations is not None:
        Ved = resultats.sollicitations.Ved
        As_mm2 = ferraillage.As_reelle_mm2 if ferraillage.lits_tendus else resultats.elu.As_requise
        resultats.effort_tranchant = calculer_effort_tranchant(
            Ved=Ved,
            geometrie=geometrie,
            materiaux=materiaux,
            As_mm2=As_mm2,
            diam_etrier=diam_etrier,
            nb_branches=nb_branches,
            espacement_etriers=espacement_etriers,
        )

    return resultats
