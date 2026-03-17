"""Constantes de l'application – paramètres par défaut Eurocode 2."""
from __future__ import annotations

import math

# ──────────────────────────────────────────────
# Coefficients partiels par défaut EC2
# ──────────────────────────────────────────────
ALPHA_CC_DEFAULT = 1.0
GAMMA_C_DEFAULT = 1.5
GAMMA_S_DEFAULT = 1.15

# Paramètres du diagramme rectangulaire simplifié (fck ≤ 50 MPa)
ETA_DEFAULT = 1.0
LAMBDA_DEFAULT = 0.8

# Déformations limites (‰ converties en valeur absolue)
EPSILON_CU3 = 3.5e-3   # déformation ultime béton
EPSILON_C3 = 1.75e-3    # déformation au pic béton

# Acier
ES_DEFAULT = 200_000.0  # MPa – module de Young acier
FYK_DEFAULT = 500.0     # MPa
FCK_DEFAULT = 25.0      # MPa

# Ductilité – déformations caractéristiques ultimes (epsilon_uk)
EPSILON_UK = {"A": 25e-3, "B": 50e-3, "C": 75e-3}
K_DUCT = {"A": 1.05, "B": 1.08, "C": 1.15}

# Déformation de calcul pour palier horizontal
EPSILON_UD_FACTOR = 0.9  # epsilon_ud = 0.9 * epsilon_uk

# ──────────────────────────────────────────────
# Sections d'armatures – catalogue
# ──────────────────────────────────────────────
AVAILABLE_DIAMETERS_MM: list[int] = [6, 8, 10, 12, 14, 16, 20, 25, 32, 40]

STEEL_TABLE_CM2: dict[int, dict[int, float]] = {
    6:  {1: 0.28, 2: 0.57, 3: 0.85, 4: 1.13, 5: 1.41, 6: 1.70, 7: 1.98, 8: 2.26, 9: 2.54, 10: 2.83},
    8:  {1: 0.50, 2: 1.01, 3: 1.51, 4: 2.01, 5: 2.51, 6: 3.02, 7: 3.52, 8: 4.02, 9: 4.52, 10: 5.03},
    10: {1: 0.79, 2: 1.57, 3: 2.36, 4: 3.14, 5: 3.93, 6: 4.71, 7: 5.50, 8: 6.28, 9: 7.07, 10: 7.85},
    12: {1: 1.13, 2: 2.26, 3: 3.39, 4: 4.52, 5: 5.65, 6: 6.79, 7: 7.92, 8: 9.05, 9: 10.18, 10: 11.31},
    14: {1: 1.54, 2: 3.08, 3: 4.62, 4: 6.16, 5: 7.70, 6: 9.24, 7: 10.78, 8: 12.32, 9: 13.85, 10: 15.39},
    16: {1: 2.01, 2: 4.02, 3: 6.03, 4: 8.04, 5: 10.05, 6: 12.06, 7: 14.07, 8: 16.08, 9: 18.10, 10: 20.11},
    20: {1: 3.14, 2: 6.28, 3: 9.42, 4: 12.57, 5: 15.71, 6: 18.85, 7: 21.99, 8: 25.13, 9: 28.27, 10: 31.42},
    25: {1: 4.91, 2: 9.82, 3: 14.73, 4: 19.64, 5: 24.54, 6: 29.45, 7: 34.36, 8: 39.27, 9: 44.18, 10: 49.09},
    32: {1: 8.04, 2: 16.08, 3: 24.13, 4: 32.17, 5: 40.21, 6: 48.25, 7: 56.30, 8: 64.34, 9: 72.38, 10: 80.42},
    40: {1: 12.57, 2: 25.13, 3: 37.70, 4: 50.27, 5: 62.83, 6: 75.40, 7: 87.96, 8: 100.53, 9: 113.10, 10: 125.66},
}

# ──────────────────────────────────────────────
# Classes d'exposition et wmax (tableau 7.1N EC2)
# ──────────────────────────────────────────────
CLASSES_EXPOSITION = [
    "X0", "XC1", "XC2", "XC3", "XC4",
    "XD1", "XD2", "XD3",
    "XS1", "XS2", "XS3",
    "XF1", "XF2", "XF3", "XF4",
    "XA1", "XA2", "XA3",
]

WMAX_PAR_CLASSE: dict[str, float | None] = {
    "X0":  0.40,
    "XC1": 0.30,
    "XC2": 0.30,
    "XC3": 0.30,
    "XC4": 0.30,
    "XD1": 0.30,
    "XD2": 0.30,
    "XD3": None,   # dispositions particulières requises
    "XS1": 0.30,
    "XS2": 0.30,
    "XS3": None,
    "XF1": 0.30,
    "XF2": 0.30,
    "XF3": 0.30,
    "XF4": 0.30,
    "XA1": 0.30,
    "XA2": 0.30,
    "XA3": None,
}

# Diamètre maximal et espacement maximal pour contrôle simplifié (table 7.2N / 7.3N)
# Clés = sigma_s arrondi (MPa), Valeurs = {wmax: phi_max_mm}
TABLEAU_DIAMETRE_MAX: dict[int, dict[float, float]] = {
    160: {0.40: 40, 0.30: 32, 0.20: 25},
    200: {0.40: 32, 0.30: 25, 0.20: 16},
    240: {0.40: 20, 0.30: 16, 0.20: 12},
    280: {0.40: 16, 0.30: 12, 0.20: 8},
    320: {0.40: 12, 0.30: 10, 0.20: 6},
    360: {0.40: 10, 0.30: 8, 0.20: 5},
    400: {0.40: 8, 0.30: 6, 0.20: 4},
    450: {0.40: 6, 0.30: 5, 0.20: 0},
}

TABLEAU_ESPACEMENT_MAX: dict[int, dict[float, float]] = {
    160: {0.40: 300, 0.30: 300, 0.20: 200},
    200: {0.40: 300, 0.30: 250, 0.20: 150},
    240: {0.40: 250, 0.30: 200, 0.20: 100},
    280: {0.40: 200, 0.30: 150, 0.20: 50},
    320: {0.40: 150, 0.30: 100, 0.20: 0},
    360: {0.40: 100, 0.30: 50, 0.20: 0},
}
