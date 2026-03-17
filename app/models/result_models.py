"""Modèles de résultats de calcul."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.section_decision import SectionDecisionResult


@dataclass
class ResultatPivot:
    """Informations sur le pivot de calcul."""
    pivot: str = ""          # "A", "B" ou "Compression"
    epsilon_s1: float = 0.0
    epsilon_c: float = 0.0
    sigma_s1: float = 0.0
    commentaire: str = ""


@dataclass
class ResultatFlexionELU:
    """Résultats du calcul en flexion simple ELU."""
    # Type de section retenu
    type_section_retenu: str = ""
    commentaire_section: str = ""

    # Paramètres béton
    fcd: float = 0.0
    fcu: float = 0.0

    # Moment réduit
    mu_cu: float = 0.0
    mu_ulim: float = 0.0

    # Position de l'axe neutre
    alpha_u: float = 0.0
    x_u: float = 0.0         # profondeur axe neutre (mm)

    # Bras de levier
    Zc: float = 0.0           # mm

    # Pivot
    pivot: ResultatPivot = field(default_factory=ResultatPivot)

    # Sections d'acier (mm²)
    As_requise: float = 0.0
    As_min: float = 0.0

    # Pour section T
    MTu: float = 0.0         # moment de référence (N·mm)
    As1: float = 0.0         # contribution âme (mm²)
    As2: float = 0.0         # contribution table (mm²)
    MEd1: float = 0.0        # moment repris par l'âme (N·mm)
    MEd2: float = 0.0        # moment repris par la table (N·mm)

    # Aciers comprimés
    necessite_aciers_comprimes: bool = False
    As_comp_requise: float = 0.0  # mm²
    As_tendue_totale: float = 0.0  # mm²
    Mlu: float = 0.0              # N·mm
    commentaire_compression: str = ""

    # Largeur de calcul utilisée
    b_calcul: float = 0.0    # mm
    d_calcul: float = 0.0    # mm

    # Décision de section (T vs rectangulaire)
    decision: Optional[SectionDecisionResult] = None

    # Statut
    calcul_valide: bool = False
    erreurs: list[str] = field(default_factory=list)
    avertissements: list[str] = field(default_factory=list)


@dataclass
class ResultatVerificationFerraillage:
    """Résultats de la vérification du ferraillage proposé."""
    As_requise_mm2: float = 0.0
    As_reelle_mm2: float = 0.0
    d_calcul: float = 0.0
    d_reel: float = 0.0
    ecart_absolu_mm2: float = 0.0
    taux_pourcentage: float = 0.0  # positif = surarmé, négatif = sous-armé

    # Contrôle mécanique
    controle_section: bool = False
    controle_bras_levier: bool = False
    verdict_global: bool = False

    # Détails par lit
    details_lits: list[dict] = field(default_factory=list)

    # Messages
    message_section: str = ""
    message_bras_levier: str = ""
    message_verdict: str = ""


@dataclass
class ResultatConstructif:
    """Résultats des vérifications constructives."""
    verifie: bool = True
    messages: list[dict] = field(default_factory=list)  # {"type": "ok"|"erreur"|"avertissement", "message": str}
    largeur_utile_mm: float = 0.0
    nb_max_barres_par_lit: dict[float, int] = field(default_factory=dict)


@dataclass
class ResultatFissuration:
    """Résultats du contrôle de fissuration."""
    wmax_recommande: Optional[float] = None
    sigma_s_service: float = 0.0
    sigma_c_service: float = 0.0
    As_min_mm2: float = 0.0
    As_reelle_mm2: float = 0.0

    # Moment de fissuration
    Mcr: float = 0.0
    section_fissuree: bool = False
    x_ser: float = 0.0
    I_fiss: float = 0.0

    # Limites de contraintes
    sigma_c_lim: float = 0.0
    sigma_s_lim: float = 0.0
    controle_sigma_c: bool = True
    controle_sigma_s: bool = True

    # Contrôle simplifié
    diametre_max_admissible: Optional[float] = None
    espacement_max_admissible: Optional[float] = None
    diam_propose: float = 16.0
    espacement_propose: float = 150.0

    # Calcul direct (wk)
    wk: float = 0.0
    wk_lim: float = 0.0
    controle_wk: bool = True

    # Verdicts
    controle_As_min: bool = False
    controle_diametre: bool = False
    controle_espacement: bool = False
    verdict: str = ""  # "Vérifié", "Non vérifié", "Vérifié sous réserve"
    messages: list[str] = field(default_factory=list)


@dataclass
class ResultatSollicitations:
    """Résultats du calcul des sollicitations sur poutre."""
    # Réactions d'appui
    RA: float = 0.0  # N
    RB: float = 0.0  # N
    # Valeurs au point x choisi
    x_choisi: float = 0.0  # mm
    Vx: float = 0.0   # N
    Mx: float = 0.0   # N·mm
    zone: str = ""     # "travée", "appui", "console gauche", "console droite"
    # Extrema
    M_max: float = 0.0  # N·mm
    M_min: float = 0.0  # N·mm
    V_max: float = 0.0  # N
    V_min: float = 0.0  # N
    x_M_max: float = 0.0  # mm
    x_V_max: float = 0.0  # mm
    # Diagrammes (listes de points)
    x_values: list[float] = field(default_factory=list)
    V_values: list[float] = field(default_factory=list)
    M_values: list[float] = field(default_factory=list)
    # Combinaison utilisée
    combinaison: str = "ELU"
    # Moments ELU / ELS de calcul
    MEd: float = 0.0   # N·mm – moment ELU au point de calcul
    Mser: float = 0.0  # N·mm – moment ELS au point de calcul
    Ved: float = 0.0   # N – effort tranchant ELU au point de calcul
    calcul_valide: bool = False
    erreurs: list[str] = field(default_factory=list)


@dataclass
class ResultatEffortTranchant:
    """Résultats du calcul d'effort tranchant."""
    Ved: float = 0.0       # N – effort tranchant de calcul
    VRdc: float = 0.0      # N – résistance béton seul
    VRds: float = 0.0      # N – résistance armatures transversales
    VRd_max: float = 0.0   # N – résistance maximale bielles comprimées
    besoin_armatures: bool = False
    Asw_s_requis: float = 0.0    # mm²/mm
    Asw_s_reel: float = 0.0     # mm²/mm
    espacement_reel: float = 0.0  # mm
    espacement_max: float = 0.0   # mm
    controle_espacement: bool = False
    controle_section: bool = False
    verdict: str = ""
    messages: list[str] = field(default_factory=list)


@dataclass
class SolutionArmature:
    """Une proposition de ferraillage."""
    lits: list[dict] = field(default_factory=list)  # [{"diametre": 16, "nombre": 4}, ...]
    As_totale_mm2: float = 0.0
    As_totale_cm2: float = 0.0
    ecart_mm2: float = 0.0
    ecart_pourcent: float = 0.0
    nb_lits: int = 0
    faisable: bool = True
    score: float = 0.0
    description: str = ""


@dataclass
class ResultatsComplets:
    """Regroupe tous les résultats."""
    elu: ResultatFlexionELU = field(default_factory=ResultatFlexionELU)
    verification: Optional[ResultatVerificationFerraillage] = None
    constructif: Optional[ResultatConstructif] = None
    fissuration: Optional[ResultatFissuration] = None
    sollicitations: Optional[ResultatSollicitations] = None
    effort_tranchant: Optional[ResultatEffortTranchant] = None
    propositions: list[SolutionArmature] = field(default_factory=list)
