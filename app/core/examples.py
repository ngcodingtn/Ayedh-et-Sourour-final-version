"""Exemples de validation prédéfinis."""
from __future__ import annotations

from app.models.section_models import DonneesGeometrie, TypeSection
from app.models.material_models import DonneesBeton, DonneesAcier, DonneesMateriaux
from app.models.load_models import DonneesSollicitations
from app.models.reinforcement_models import DonneesFerraillage, LitArmature, DonneesEnvironnement
from app.core.units import m_to_mm, cm_to_mm, MNm_to_Nmm


def exemple_rectangulaire() -> dict:
    """Exemple rectangulaire de validation.

    bw = 0.35 m, h = 0.60 m, d = 0.54 m
    fck = 25 MPa, fyk = 500 MPa
    MEd = 0.3414 MN·m, Mser = 0.2376 MN·m
    """
    geometrie = DonneesGeometrie(
        type_section=TypeSection.RECTANGULAIRE,
        b_w=m_to_mm(0.35),     # 350 mm
        h=m_to_mm(0.60),       # 600 mm
        d=m_to_mm(0.54),       # 540 mm
        d_prime=m_to_mm(0.05), # 50 mm
        c_nom=30.0,
        diam_etrier=8.0,
        d_auto=False,
    )

    materiaux = DonneesMateriaux(
        beton=DonneesBeton(fck=25.0),
        acier=DonneesAcier(fyk=500.0),
    )

    sollicitations = DonneesSollicitations(
        M_Ed=MNm_to_Nmm(0.3414),
        M_ser=MNm_to_Nmm(0.2376),
        moment_positif=True,
    )

    ferraillage = DonneesFerraillage(
        lits_tendus=[
            LitArmature(numero=1, nombre_barres=6, diametre_mm=16.0),
            LitArmature(numero=2, nombre_barres=3, diametre_mm=14.0),
        ],
    )

    environnement = DonneesEnvironnement(
        classe_exposition="XC1",
        maitrise_fissuration=True,
    )

    return {
        "geometrie": geometrie,
        "materiaux": materiaux,
        "sollicitations": sollicitations,
        "ferraillage": ferraillage,
        "environnement": environnement,
        "nom": "Exemple rectangulaire – Validation",
    }


def exemple_section_T() -> dict:
    """Exemple section en T.

    beff = 2.66 m, bw = 0.22 m, hf = 0.15 m, h = 0.85 m, d = 0.80 m
    fck = 25 MPa, MEd = 0.777 MN·m
    """
    geometrie = DonneesGeometrie(
        type_section=TypeSection.T,
        b_eff=m_to_mm(2.66),   # 2660 mm
        b_w=m_to_mm(0.22),     # 220 mm
        h_f=m_to_mm(0.15),     # 150 mm
        h=m_to_mm(0.85),       # 850 mm
        d=m_to_mm(0.80),       # 800 mm
        d_prime=m_to_mm(0.05),
        c_nom=30.0,
        diam_etrier=8.0,
        d_auto=False,
    )

    materiaux = DonneesMateriaux(
        beton=DonneesBeton(fck=25.0),
        acier=DonneesAcier(fyk=500.0),
    )

    sollicitations = DonneesSollicitations(
        M_Ed=MNm_to_Nmm(0.777),
        M_ser=MNm_to_Nmm(0.55),
        moment_positif=True,
    )

    environnement = DonneesEnvironnement(
        classe_exposition="XC3",
        maitrise_fissuration=True,
    )

    return {
        "geometrie": geometrie,
        "materiaux": materiaux,
        "sollicitations": sollicitations,
        "ferraillage": DonneesFerraillage(),
        "environnement": environnement,
        "nom": "Exemple section en T – Validation",
    }


def exemple_aciers_comprimes() -> dict:
    """Exemple avec aciers comprimés nécessaires.

    Section rectangulaire fortement sollicitée.
    """
    geometrie = DonneesGeometrie(
        type_section=TypeSection.RECTANGULAIRE,
        b_w=250.0,
        h=400.0,
        d=360.0,
        d_prime=40.0,
        c_nom=30.0,
        diam_etrier=8.0,
        d_auto=False,
    )

    materiaux = DonneesMateriaux(
        beton=DonneesBeton(fck=25.0),
        acier=DonneesAcier(fyk=500.0),
    )

    # Moment élevé pour forcer les aciers comprimés
    sollicitations = DonneesSollicitations(
        M_Ed=MNm_to_Nmm(0.220),
        M_ser=MNm_to_Nmm(0.155),
        moment_positif=True,
    )

    environnement = DonneesEnvironnement(
        classe_exposition="XC3",
        maitrise_fissuration=True,
    )

    return {
        "geometrie": geometrie,
        "materiaux": materiaux,
        "sollicitations": sollicitations,
        "ferraillage": DonneesFerraillage(),
        "environnement": environnement,
        "nom": "Exemple avec aciers comprimés",
    }


def exemple_figure() -> dict:
    """Exemple de la figure du cours.

    beff = 120 cm, bw = 50 cm, h = 60 cm, hf = 12 cm, d = 51 cm
    Mu,max = 1.1940 MN·m
    4 lits : 5HA25 + 5HA25 + 5HA16 + 5HA14
    """
    geometrie = DonneesGeometrie(
        type_section=TypeSection.T,
        b_eff=cm_to_mm(120),   # 1200 mm
        b_w=cm_to_mm(50),      # 500 mm
        h_f=cm_to_mm(12),      # 120 mm
        h=cm_to_mm(60),        # 600 mm
        d=cm_to_mm(51),        # 510 mm
        d_prime=cm_to_mm(5),   # 50 mm
        c_nom=30.0,
        diam_etrier=8.0,
        d_auto=False,
    )

    materiaux = DonneesMateriaux(
        beton=DonneesBeton(fck=25.0),
        acier=DonneesAcier(fyk=500.0),
    )

    sollicitations = DonneesSollicitations(
        M_Ed=MNm_to_Nmm(1.1940),
        M_ser=0.0,
        moment_positif=True,
    )

    ferraillage = DonneesFerraillage(
        lits_tendus=[
            LitArmature(numero=1, nombre_barres=5, diametre_mm=25.0),
            LitArmature(numero=2, nombre_barres=5, diametre_mm=25.0),
            LitArmature(numero=3, nombre_barres=5, diametre_mm=16.0),
            LitArmature(numero=4, nombre_barres=5, diametre_mm=14.0),
        ],
    )

    environnement = DonneesEnvironnement(
        classe_exposition="XC1",
        maitrise_fissuration=True,
    )

    return {
        "geometrie": geometrie,
        "materiaux": materiaux,
        "sollicitations": sollicitations,
        "ferraillage": ferraillage,
        "environnement": environnement,
        "nom": "Exemple de la figure – 4 lits",
    }
